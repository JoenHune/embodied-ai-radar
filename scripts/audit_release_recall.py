"""Read-only recall audit of a frozen, independently sourced release sample.

Gold records never originate from the catalog. Missing, excluded, ambiguous,
and unlinked records stay in their original denominator. Release capture and
canonical-work presence are reported separately; neither proves internet-wide
recall or independent experimental validation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import posixpath
from pathlib import Path
import re
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from catalog_rules import normalized_title
from catalog_store import load_catalog
from temporal_evidence import public_day

ROOT = Path(__file__).resolve().parents[1]
TRACKING_QUERY = {"fbclid", "gclid", "ref", "referrer"}
RESEARCH_TYPES = {"paper", "technical_report", "model_report", "dataset_report", "infrastructure_report", "code_release", "benchmark"}


def normalize_url(url: str | None) -> str:
    if not isinstance(url, str):
        return ""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return ""
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        return ""
    host = parts.hostname.casefold()
    if host in {"www.arxiv.org", "export.arxiv.org"}:
        host = "arxiv.org"
    # Browser/RFC dot-segment resolution: an observed redirect to /project/.
    # is the same resource as /project/, not a title-based inferred alias.
    path = posixpath.normpath(unquote(parts.path)).rstrip("/") or "/"
    if path == ".":
        path = "/"
    if host == "arxiv.org":
        match = re.fullmatch(r"/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?", path)
        if match:
            path = "/abs/" + match[1]
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_") and k.lower() not in TRACKING_QUERY]
    return urlunsplit(("https", host, path, urlencode(sorted(query)), ""))


def url_identifiers(url: str) -> set[str]:
    parts = urlsplit(normalize_url(url))
    if parts.hostname == "arxiv.org":
        match = re.fullmatch(r"/abs/(\d{4}\.\d{4,5})", parts.path)
        return {"arxiv:" + match[1]} if match else set()
    if parts.hostname in {"doi.org", "dx.doi.org"}:
        return {"doi:" + parts.path.lstrip("/").casefold()}
    return set()


def validate_gold(records: list[dict]) -> list[str]:
    errors, seen = [], set()
    for row in records:
        gid = row.get("gold_id")
        if not gid or gid in seen:
            errors.append(f"duplicate_or_missing_gold_id:{gid}")
        seen.add(gid)
        if row.get("record_type") == "source_gap":
            if not row.get("organization_id") or not row.get("reason") or not row.get("source_url"):
                errors.append(f"incomplete_source_gap:{gid}")
            continue
        if row.get("record_type") != "release":
            errors.append(f"unknown_record_type:{gid}")
            continue
        for field in ["organization_id", "title", "url", "index_url", "frozen_at", "sampling_frame_id", "selection_basis", "release_type"]:
            if not row.get(field):
                errors.append(f"missing_{field}:{gid}")
        when = public_day(row.get("published_at"), row.get("published_at_precision"))
        window = row.get("window", {})
        if not when or not (window.get("from", "") <= when.isoformat() <= window.get("to", "")):
            errors.append(f"unknown_or_out_of_window_date:{gid}")
        if not normalize_url(row.get("url")) or not normalize_url(row.get("index_url")):
            errors.append(f"invalid_source_url:{gid}")
        provenance = row.get("provenance", [])
        captured = [p for p in provenance if p.get("status") == "captured"]
        if not captured:
            errors.append(f"no_source_hash:{gid}")
        for proof in captured:
            if not re.fullmatch(r"[0-9a-f]{64}", proof.get("sha256", "")) or not proof.get("excerpt") or proof.get("hash_scope") != "http_response_body_bytes":
                errors.append(f"invalid_source_provenance:{gid}")
        observed_redirects = {normalize_url(row["url"])} | {normalize_url(p.get("effective_url")) for p in provenance if p.get("role") == "release_page"}
        if not {normalize_url(url) for url in row.get("equivalent_urls", [])} <= observed_redirects:
            errors.append(f"unobserved_equivalent_url:{gid}")
        if any(key in row for key in ["matched_work_id", "catalog_match", "match_status"]):
            errors.append(f"catalog_state_must_not_enter_gold:{gid}")
    return errors


def build_match_index(catalog: dict) -> dict:
    works = {w["work_id"]: w for w in catalog.get("works", [])}
    source_urls = {s["source_record_id"]: s.get("url") for s in catalog.get("source-records", [])}
    urls, identifiers, titles, version_urls = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set)
    for wid, work in works.items():
        titles[normalized_title(work.get("title", ""))].add(wid)
        identifiers[wid.casefold()].add(wid)
        for key, value in work.get("identifiers", {}).items():
            if value:
                identifiers[f"{key}:{value}".casefold()].add(wid)
        for alias in work.get("aliases", []):
            identifiers[alias.casefold()].add(wid)
        for source_id in work.get("source_record_ids", []):
            url = normalize_url(source_urls.get(source_id))
            if url:
                urls[url].add(wid)
    for item in catalog.get("work-aliases", []):
        if item.get("work_id") in works:
            identifiers[item["alias"].casefold()].add(item["work_id"])
    for manifestation in catalog.get("manifestations", []):
        url = normalize_url(manifestation.get("url"))
        if url and manifestation.get("work_id") in works:
            urls[url].add(manifestation["work_id"])
            version_urls[url].add(manifestation["work_id"])
    for row in catalog.get("reconciliation", []):
        url = normalize_url(source_urls.get(row.get("source_record_id")))
        if url and row.get("work_id") in works:
            urls[url].add(row["work_id"])
    return {"works": works, "urls": urls, "version_urls": version_urls, "identifiers": identifiers, "titles": titles,
            "raw_source_urls": {normalize_url(url) for url in source_urls.values() if normalize_url(url)}}


def match_release(row: dict, index: dict) -> dict:
    release_urls = {normalize_url(url) for url in [row["url"], *row.get("equivalent_urls", [])]} - {""}
    # Only observed HTTP redirects are equivalent release URLs. Related papers,
    # citations, the group's index page and project-family links are not.
    direct = set().union(*(index["urls"].get(url, set()) for url in release_urls))
    ids = {identifier for url in release_urls for identifier in url_identifiers(url)}
    identity = set().union(*(index["identifiers"].get(value.casefold(), set()) for value in ids))
    by_title = index["titles"].get(normalized_title(row["title"]), set())
    matches, basis = (direct, "release_url") if direct else (identity, "canonical_identifier") if identity else (by_title, "exact_normalized_title")
    common = {"gold_id": row["gold_id"], "organization_id": row["organization_id"], "title": row["title"],
              "url": row["url"], "published_at": row["published_at"], "release_type": row["release_type"],
              "match_basis": basis if matches else None, "matched_work_ids": sorted(matches), "release_captured": False,
              "release_url_present": bool(direct or release_urls & index["raw_source_urls"]),
              "canonical_work_present": False, "canonical_identity_resolved": False, "catalog_relevance": None, "formal_visible": False}
    if len(matches) > 1:
        # Hard URL/identifier evidence proves receipt even when duplicate
        # canonical candidates prevent a unique identity decision.
        return {**common, "status": "ambiguous", "canonical_work_present": bool(direct or identity)}
    if not matches:
        stored = bool(release_urls & index["raw_source_urls"])
        return {**common, "status": "unlinked_source" if stored else "missing"}
    work = index["works"][next(iter(matches))]
    relevance = work.get("relevance", {}).get("status", "manual_review")
    if basis == "exact_normalized_title":
        return {**common, "status": "title_candidate", "candidate_catalog_relevance": relevance,
                "review_reason": "Title alone does not establish identity; require verified author/project/identifier evidence."}
    captured = bool(direct)
    linked_version = any(work["work_id"] in index["version_urls"].get(url, set()) for url in release_urls)
    return {**common, "status": relevance if captured else "known_work_missing_release", "catalog_relevance": relevance,
            "canonical_work_present": True, "canonical_identity_resolved": True, "release_captured": captured,
            "manifestation_linked": linked_version, "formal_visible": captured and relevance == "included"}


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    count = lambda key: sum(bool(row.get(key)) for row in rows)
    return {"denominator": n, "status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
            "catalog_relevance_counts": dict(sorted(Counter(row["catalog_relevance"] or "unmatched" for row in rows).items())),
            "release_url_present": count("release_url_present"), "release_url_presence_rate": count("release_url_present") / n if n else None,
            "release_captured": count("release_captured"), "release_capture_recall": count("release_captured") / n if n else None,
            "manifestation_linked": count("manifestation_linked"), "manifestation_link_recall": count("manifestation_linked") / n if n else None,
            "canonical_work_present": count("canonical_work_present"), "canonical_work_recall": count("canonical_work_present") / n if n else None,
            "canonical_identity_resolved": count("canonical_identity_resolved"), "canonical_resolution_rate": count("canonical_identity_resolved") / n if n else None,
            "formal_visible": count("formal_visible"), "formal_visible_recall": count("formal_visible") / n if n else None}


def audit_release_recall(records: list[dict], catalog: dict, *, catalog_hash: str | None = None) -> dict:
    errors = validate_gold(records)
    if errors:
        raise ValueError("Invalid gold sample: " + "; ".join(errors))
    releases = [row for row in records if row["record_type"] == "release"]
    gaps = [row for row in records if row["record_type"] == "source_gap"]
    index = build_match_index(catalog)
    results = [match_release(row, index) for row in releases]
    organizations = sorted({row["organization_id"] for row in records})
    return {"schema_version": "1", "scope": "stratified_regression_sample_not_internet_census", "catalog_hash": catalog_hash,
            "gold_hash": hashlib.sha256(json.dumps(records, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
            "sample_frozen_at": sorted({row["frozen_at"] for row in releases}),
            "sampled_organizations": len(organizations), "organizations_with_at_least_two_releases": sum(sum(row["organization_id"] == oid for row in releases) >= 2 for oid in organizations),
            "source_gaps": gaps, "overall": summarize(results),
            "research_artifacts": summarize([row for row in results if row["release_type"] in RESEARCH_TYPES]),
            "observational_releases": summarize([row for row in results if row["release_type"] not in RESEARCH_TYPES]),
            "organizations": [{"organization_id": oid, **summarize([row for row in results if row["organization_id"] == oid])} for oid in organizations],
            "results": results,
            "limitations": ["A frozen source-first sample, not a census of all public releases or all T0 organizations.",
                            "Presence is not correctness, peer review, reliable attribution, or independent replication.",
                            "Release URL presence includes ambiguous/unlinked receipts; release_capture_recall requires a unique canonical binding. Hard-evidence ambiguous receipts count toward work presence but not identity resolution or formal visibility.",
                            "Known work without the observed release URL is not counted as release capture.",
                            "Exact-title fallback is a review candidate, never identity or recall credit without author/project/identifier corroboration.",
                            "Missing, excluded, candidate, manual-review and ambiguous items remain in the denominator."]}


def recall_gate(report: dict, policy: dict) -> dict:
    """Enforce the frozen denominator, not a post-hoc set of successful hits."""
    errors = []
    research = report.get("research_artifacts", {})
    minimum = policy["minimum_manifestation_link_recall"]
    if not 0 <= minimum <= 1:
        raise ValueError("Recall threshold must be a fraction between zero and one")
    if report.get("scope") != policy["scope"]:
        errors.append("sample_scope_mismatch")
    if report.get("gold_hash") != policy["gold_hash"]:
        errors.append("frozen_sample_changed_without_policy_revision")
    if report.get("sampled_organizations", 0) < policy["minimum_sampled_organizations"]:
        errors.append("insufficient_sampled_organizations")
    if research.get("denominator", 0) < policy["minimum_research_releases"]:
        errors.append("research_denominator_shrunk")
    measured = research.get("manifestation_link_recall")
    if measured is None or measured < minimum:
        errors.append("research_release_manifestation_recall_below_threshold")
    return {"status": "failed" if errors else "passed", "scope": policy["scope"],
            "policy_version": policy["version"], "metric": "research_artifacts.manifestation_link_recall",
            "measured": measured, "minimum": minimum, "errors": errors,
            "does_not_prove": ["all_T0_release_recall", "classification_accuracy", "independent_experimental_validation"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=ROOT / "data/coverage-gold-releases.jsonl")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog")
    parser.add_argument("--policy", type=Path, help="Enforce a frozen-sample regression policy; otherwise report only")
    args = parser.parse_args(argv)
    records = [json.loads(line) for line in args.gold.read_text().splitlines() if line.strip()]
    catalog, metadata = load_catalog(args.catalog)
    report = audit_release_recall(records, catalog, catalog_hash=metadata.get("catalog_hash"))
    if args.policy:
        report["regression_gate"] = recall_gate(report, json.loads(args.policy.read_text()))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(report.get("regression_gate", {}).get("status") == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
