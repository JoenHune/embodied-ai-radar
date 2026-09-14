"""Explicit source-review ingestion; no network, name-based promotion or role inference.

The input is a reviewed, complete candidate cohort. Authority is changed only
with --apply, after all work identities and original person records validate.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from catalog_store import encode, fingerprint, load_catalog, write_if_changed
from people_radar import (_authority_reviews, _hard_identity, _observed, _prepare_reviews,
                          _url, load_people_authority, save_people_authority)

ROOT = Path(__file__).resolve().parents[1]


def capture_cohort(api, scope="all"):
    if scope not in {"all", "window"}:
        raise ValueError("candidate_review_invalid_scope")
    index = json.loads((api / "index.json").read_text())
    rows = []
    for person in index["people"]:
        detail = json.loads((api / (person["slug"] + ".json")).read_text())
        if detail["review_hash"] != index["review_hash"] or detail["dataset_version"] != index["dataset_version"]:
            raise ValueError("people_candidate_cohort_mixed_versions")
        for work in detail["candidate_works"]:
            if scope == "window" and work.get("in_complete_window") is not True:
                continue
            rows.append({"person_id": person["person_id"], "work_id": work["work_id"],
                         "matched_author_name": work["authorship_evidence"].get("matched_author_name"),
                         "in_complete_window": work["in_complete_window"]})
    rows.sort(key=lambda row: (row["person_id"], row["work_id"]))
    result = {"schema_version": "1", "authority_hash": index["review_hash"], "dataset_version": index["dataset_version"],
              "cohort_id": fingerprint(rows), "rows": rows}
    if scope == "window":
        window = index.get("window", {})
        if len(window.get("months", [])) != 12 or not window.get("cutoff"):
            raise ValueError("candidate_review_complete_twelve_month_window_required")
        result.update(scope=scope, window=copy.deepcopy(window))
    return result


def validate_cohort_scope(cohort, scope):
    if cohort.get("scope", "all") != scope:
        raise ValueError("candidate_review_saved_cohort_scope_mismatch")
    if scope == "window":
        if any(row.get("in_complete_window") is not True for row in cohort["rows"]):
            raise ValueError("candidate_review_window_contains_outside_row")
        if fingerprint(cohort["rows"]) != cohort.get("cohort_id"):
            raise ValueError("candidate_review_cohort_hash_mismatch")
    pairs = [(row["person_id"], row["work_id"]) for row in cohort["rows"]]
    if len(pairs) != len(set(pairs)):
        raise ValueError("candidate_review_duplicate_baseline_pair")


def _bridged_work_url(work_id, proof, linked):
    """Resolve a reviewed same-entry pair of hard IDs, never a fuzzy title.

    The source's actual arXiv link remains in linked_url. A separate coauthor
    publication entry must explicitly connect that exact arXiv URL and the
    DOI publisher/resolver link. No canonical work/alias table is changed.
    """
    bridge = proof.get("manifestation_identity_bridge")
    if not bridge:
        return linked
    if not isinstance(bridge, dict) or not bridge.get("locator") or not bridge.get("source_url"):
        raise ValueError("candidate_review_manifestation_bridge_entry_required")
    _url(bridge["source_url"])
    actual = _url(bridge.get("linked_url"))
    target = _hard_identity(actual)
    parts = urlsplit(actual)
    # Science's explicit /doi/<DOI> URL is a DOI-bearing publisher permalink,
    # not an arbitrary page whose title resembles a canonical work.
    if parts.hostname in {"science.org", "www.science.org"}:
        match = re.fullmatch(r"/doi/(10\.\d{4,9}/.+)", unquote(parts.path).rstrip("/"))
        target = "doi:" + match.group(1).lower() if match else None
    if (not work_id.startswith("doi:") or target != work_id.lower() or
            _hard_identity(_url(bridge.get("same_entry_arxiv"))) != _hard_identity(linked)):
        raise ValueError("candidate_review_manifestation_bridge_identifier_mismatch")
    return "https://doi.org/" + work_id[4:]


def normalize_result(row):
    if row.get("status") and row.get("result") and row["status"] != row["result"]:
        raise ValueError("candidate_review_conflicting_resolution_fields")
    status = row.get("status", row.get("result"))
    if status not in {"verified", "unresolved"}:
        raise ValueError("candidate_review_requires_explicit_resolution")
    reason = row.get("reason") or row.get("method")
    if not reason:
        raise ValueError("candidate_review_reason_required")
    # A generated canonical URL is not evidence that the source contains it.
    bases = [row.get("match_basis", ""), *[proof.get("match_basis", "") for proof in row.get("evidence", [])]]
    if any("exact_title_and_explicit_author" in basis or "official_person_author_archive_exact_title" in basis for basis in bases):
        status = "unresolved"
        reason = "官网标题与作者匹配，但尚缺可复核的作品硬标识链接；保留待核验。"
    sources = set([*(row.get("checked_source_urls") or []), *(row.get("checked_sources") or [])])
    if row.get("source_url"):
        sources.add(row["source_url"])
    evidence = []
    if status == "verified":
        proofs = row.get("evidence") or [row]
        if not isinstance(proofs, list):
            raise ValueError("candidate_review_evidence_array_required")
        for proof in proofs:
            source = proof.get("source_url") or proof.get("url") or row.get("source_url")
            work_url = proof.get("work_url") or row.get("work_url")
            linked = proof.get("linked_url") or proof.get("matched_link")
            # Preserve the link actually read on the source page. It may be an
            # arXiv version of a DOI-first canonical work; authority validation
            # below requires that exact identity to belong uniquely to it.
            if linked:
                work_url = _bridged_work_url(row["work_id"], proof, linked)
                if proof.get("manifestation_identity_bridge"):
                    bridge = proof["manifestation_identity_bridge"]
                    sources.update(bridge[key] for key in ("source_url", "linked_url", "same_entry_arxiv"))
            sources.add(source)
            # Keep the reviewed entry locator, actual links, nested identity
            # bridge and source hashes; do not flatten them into only a reason.
            item = {**copy.deepcopy(proof), "kind": proof.get("kind") or row.get("kind"), "url": source,
                    "work_url": work_url, "observed_at": proof.get("observed_at") or row["observed_at"],
                    "statement": reason, "excerpt": None}
            if linked:
                item["linked_url"] = linked
            for key in ("locator", "evidence_locator", "match_basis", "source_scope", "matched_author_name", "author_locator", "source_body_sha256", "entry_text_sha256", "author_profile_url", "identity_source_url", "identity_url", "work_identifier_source_url"):
                if proof.get(key) or row.get(key):
                    item[key] = proof.get(key) or row[key]
                    if key.endswith('_url'):
                        _url(item[key])
                        sources.add(item[key])
            chain = proof.get("source_chain") or row.get("source_chain")
            if chain:
                item["source_chain"] = []
                for step in chain:
                    clean = {key: step[key] for key in ("source_url", "linked_url", "relation", "observed_at") if step.get(key)}
                    for key in ("source_url", "linked_url"):
                        if clean.get(key):
                            _url(clean[key])
                            sources.add(clean[key])
                    item["source_chain"].append(clean)
            evidence.append(item)
    for source in sources:
        _url(source)
    _observed(row.get("observed_at"))
    return {"person_id": row["person_id"], "work_id": row["work_id"], "result": status,
            "checked_at": row["observed_at"], "reason": reason,
            "checked_sources": sorted(sources), "evidence": evidence}


def _profile_key(value):
    parts = urlsplit(_url(value))
    # Transport and conventional www aliases do not create a new person;
    # arbitrary subdomains, paths and query parameters remain distinct.
    return ((parts.hostname or "").removeprefix("www."), parts.path.rstrip("/"), parts.query)


def _validate_nested_sources(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if child and (key == "url" or key.endswith("_url") or key == "href"):
                _url(child)
            if child and key in {"observed_at", "profile_observed_at"}:
                _observed(child)
            _validate_nested_sources(child)
    elif isinstance(value, list):
        for child in value:
            _validate_nested_sources(child)


def validate_window_identity_evidence(authority, cohort, results):
    """Strict opt-in window checks, in addition to canonical work validation.

    Reviewed author/profile anchors must reach a stored verified profile, or
    an explicitly documented same-person identity bridge. A name, title,
    bibliography link, or invented canonical URL is never sufficient.
    """
    people = {person["person_id"]: person for person in authority["persons"]}
    for result in results:
        if result["result"] != "verified":
            continue
        person = people[result["person_id"]]
        if person["identity_status"] != "profile_verified":
            raise ValueError("people_candidate_identity_cannot_verify_authorship")
        known = {_profile_key(profile["url"]) for profile in person["official_profiles"]}
        for proof in result["evidence"]:
            _validate_nested_sources(proof)
            linked = proof.get("linked_url")
            if not linked or _hard_identity(_bridged_work_url(result["work_id"], proof, linked)) != _hard_identity(proof["work_url"]):
                raise ValueError("candidate_review_actual_work_link_required:" + result["work_id"])
            structure = proof.get("structure") or {}
            locator = proof.get("locator") or proof.get("evidence_locator") or structure
            if not locator:
                raise ValueError("candidate_review_specific_entry_locator_required:" + result["work_id"])
            scope = (str(proof.get("source_scope", "")) + " " + str(proof.get("match_basis", ""))).lower()
            if any(word in scope for word in ("bibliography", "whole_page", "title_only", "reference_list")):
                raise ValueError("candidate_review_non_primary_scope_rejected:" + result["work_id"])
            bridge = proof.get("identity_bridge") or {}
            profile = proof.get("author_profile_url") or bridge.get("linked_url")
            if not profile:
                raise ValueError("candidate_review_author_profile_anchor_required:" + result["work_id"])
            author_anchor = structure.get("author_link") or {}
            author_name = proof.get("matched_author_name") or bridge.get("author_name") or author_anchor.get("text")
            if not author_name:
                raise ValueError("candidate_review_explicit_author_anchor_required:" + result["work_id"])
            label = lambda value: re.sub(r"[^a-z\u3400-\u9fff]", "", value.lower())
            if label(author_name) not in {label(name) for name in [person["name"], *person.get("aliases", [])]}:
                raise ValueError("candidate_review_author_anchor_name_mismatch:" + result["work_id"])
            if author_anchor.get("linked_url", author_anchor.get("href", profile)) and _profile_key(
                    author_anchor.get("linked_url", author_anchor.get("href", profile))) != _profile_key(profile):
                raise ValueError("candidate_review_author_anchor_profile_mismatch")
            edges = [*proof.get("identity_chain", []), *proof.get("source_chain", []),
                     *[edge for edge in cohort.get("identity_bridges", []) if edge.get("person_id") == result["person_id"]]]
            reachable = set(known)
            for _ in range(len(edges) + 1):
                before = len(reachable)
                for edge in edges:
                    source = edge.get("source_url") or edge.get("url")
                    target = edge.get("linked_url")
                    if not source or not target:
                        continue  # Unlinked prose never silently invents an edge.
                    _validate_nested_sources(edge)
                    if not (edge.get("locator") or edge.get("relation")):
                        continue
                    pair = {_profile_key(source), _profile_key(target)}
                    if pair & reachable:
                        reachable.update(pair)
                if len(reachable) == before:
                    break
            if _profile_key(profile) not in reachable:
                raise ValueError("candidate_review_identity_bridge_not_verified:" + result["person_id"])
            additional = [edge for edge in cohort.get("identity_bridges", []) if edge.get("person_id") == result["person_id"]]
            if additional:
                # Keep newly checked bridge receipts with the authority proof,
                # not only in an external batch file needed to interpret it.
                receipts = [*proof.get("identity_chain", []), *additional]
                proof["identity_chain"] = list({fingerprint(edge): copy.deepcopy(edge) for edge in receipts}.values())
                for edge in additional:
                    result["checked_sources"] = sorted(set(result["checked_sources"]) | {
                        value for key, value in edge.items() if value and (key == "url" or key.endswith("_url"))})
                    if edge.get("observed_at"):
                        result["checked_at"] = max(result["checked_at"], edge["observed_at"])


def merge_results(rows):
    result = {}
    for source in rows:
        row = normalize_result(source)
        key = (row["person_id"], row["work_id"])
        old = result.get(key)
        if old:
            # Explicit additional project evidence may resolve an earlier gap.
            chosen = row if row["result"] == "verified" or old["result"] != "verified" else old
            chosen = copy.deepcopy(chosen)
            chosen["checked_at"] = max(old["checked_at"], row["checked_at"])
            chosen["checked_sources"] = sorted(set(old["checked_sources"] + row["checked_sources"]))
            if row["result"] == old["result"] == "verified":
                proofs = {fingerprint(proof): proof for proof in old["evidence"] + row["evidence"]}
                chosen["evidence"] = [proofs[key] for key in sorted(proofs)]
            result[key] = chosen
        else:
            result[key] = row
    return [result[key] for key in sorted(result)]


def apply_candidate_reviews(payload, authority, cohort, results, batch_id):
    validate_cohort_scope(cohort, cohort.get("scope", "all"))
    _prepare_reviews(payload, _authority_reviews(authority))
    results = copy.deepcopy(results)
    expected = {(row["person_id"], row["work_id"]): row for row in cohort["rows"]}
    incoming = {(row["person_id"], row["work_id"]): row for row in results}
    if len(incoming) != len(results) or set(incoming) != set(expected):
        raise ValueError("candidate_review_cohort_missing_extra_or_duplicate")
    if cohort.get("scope") == "window":
        validate_window_identity_evidence(authority, cohort, results)
    out = copy.deepcopy(authority)
    people = {row["person_id"]: row for row in out["persons"]}
    links = {(row["person_id"], row["work_id"]): row for row in out["authorship-reviews"]}
    if cohort.get("authority_hash") and cohort["authority_hash"] != fingerprint(authority):
        if not all(links.get(key, {}).get("verification_audit", {}).get("cohort_id") == cohort["cohort_id"] for key in expected):
            raise ValueError("candidate_review_stale_authority_cohort")
    for key, result in incoming.items():
        person_id, work_id = key
        old = links.get(key)
        if old and old["status"] == "verified" and not old.get("verification_audit"):
            raise ValueError("candidate_review_cannot_overwrite_prior_verified")
        if old and old["status"] == "verified" and result["result"] != "verified":
            raise ValueError("candidate_review_cannot_downgrade_verified")
        link = copy.deepcopy(old or {"authorship_id": "authorship:" + fingerprint([person_id, work_id])[:24],
                                    "person_id": person_id, "work_id": work_id, "submitted_work_id": work_id,
                                    "matched_author_name": expected[key]["matched_author_name"],
                                    "review_id": people[person_id]["review_id"], "roles": None, "evidence": []})
        link["status"] = "verified" if result["result"] == "verified" else "candidate"
        link["basis"] = "direct_official_person_work_link" if link["status"] == "verified" else "reviewed_candidate"
        if link["status"] == "verified":
            link["evidence"] = copy.deepcopy(result["evidence"])
        link["verification_audit"] = {key: copy.deepcopy(result[key]) for key in ("result", "checked_at", "reason", "checked_sources")}
        link["verification_audit"].update(batch_id=batch_id, cohort_id=cohort["cohort_id"], review_method="official_source_identifier_check", reviewer_kind="ai")
        links[key] = link
    out["authorship-reviews"] = sorted(links.values(), key=lambda row: row["authorship_id"])
    _prepare_reviews(payload, _authority_reviews(out))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--scope", choices=("all", "window"), default="all",
                        help="all candidates (legacy default) or the API's most recent complete 12-month window")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    directory = ROOT / "data/people/candidate-audits" / args.batch
    if not args.batch or Path(args.batch).name != args.batch or args.batch.startswith('.'):
        raise ValueError("unsafe_candidate_batch")
    payload, _ = load_catalog(ROOT / "data/catalog")
    authority = load_people_authority(ROOT / "data/people")
    baseline_path = directory / "baseline.json"
    cohort = json.loads(baseline_path.read_text()) if baseline_path.exists() else capture_cohort(ROOT / "docs/public/api/v1/people", args.scope)
    validate_cohort_scope(cohort, args.scope)
    raw = []
    for path in args.input:
        value = json.loads(path.read_text())
        raw.extend(value.get("results", value.get("authorship_reviews", [])))
    results = merge_results(raw)
    updated = apply_candidate_reviews(payload, authority, cohort, results, args.batch)
    counts = Counter(row["result"] for row in results)
    report = {"batch_id": args.batch, "scope": args.scope, "cohort_id": cohort["cohort_id"], "total": len(results), **dict(counts),
              "window": dict(Counter(row["result"] for row in results if next(item for item in cohort["rows"] if (item["person_id"], item["work_id"]) == (row["person_id"], row["work_id"]))["in_complete_window"])),
              "authority_before": fingerprint(authority), "authority_after": fingerprint(updated),
              "applied": args.apply, "limitations": ["Official-source checks, not complete publication histories or contribution-role validation.", "A missing or inaccessible source does not prove different identity."]}
    if args.apply:
        # The catalog may grow independently, but never overwrite concurrent
        # edits to the person authority this plan was validated against.
        if fingerprint(load_people_authority(ROOT / "data/people")) != fingerprint(authority):
            raise ValueError("candidate_review_authority_changed_before_write")
        directory.mkdir(parents=True, exist_ok=True)
        write_if_changed(baseline_path, encode(cohort) + "\n")
        write_if_changed(directory / "review-results.jsonl", ''.join(encode(row) + '\n' for row in results))
        save_people_authority(ROOT / "data/people", updated)
        write_if_changed(directory / "reconciliation.json", encode(report) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
