"""Source-reviewed people overlay; canonical works remain the only work authority.

Review JSON files are staging; four JSONL tables are the person authority. Name matches are candidates,
never person identities or verified authorship. Exported JSONL/SQLite tables are
reproducible projections, and no author-list position is a contribution claim.
"""
from __future__ import annotations

import calendar
import copy
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from catalog_rules import eligible_month, research_eligible
from catalog_store import encode, fingerprint, read_table, write_if_changed
from temporal_evidence import evidence_as_of, public_day
from versioned_text import text_as_of
from research_status import research_status_as_of as resolve_research_status
from research_status_views import latest_status_observation

SCHEMA_VERSION = "1"
TABLES = ("persons", "authorship-reviews", "organization-links", "influence-evidence")
TABLE_KEYS = {"persons": "person_id", "authorship-reviews": "authorship_id", "organization-links": "link_id", "influence-evidence": "evidence_id"}
LIMITATIONS = [
    "人物身份已核验不等于所有同名作品已核验；逐篇官网或 ORCID 硬链接支持的署名才进入统计。",
    "统计为已登记语料中的研究活动，不是影响力总排名；引用、实际贡献与采用程度未测量时为未知。",
    "作者数组保留原始署名，顺序不推断第一作者、通讯作者或共同贡献；现任机构不追溯覆盖历史论文。",
    "近期窗口使用最近十二个完整自然月，计入 included canonical work；多版本和多人共同作品全局只计一次。",
    "月度活动定位的是已核验关联作品的首次公开月，不是作者个人加入项目或贡献发生的日期。",
]


def _url(value):
    if not isinstance(value, str) or any(char.isspace() for char in value):
        raise ValueError("people_url_required")
    parts = urlparse(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("people_url_invalid")
    return value


def _observed(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("people_observed_at_utc_required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("people_observed_at_invalid") from exc
    if parsed.tzinfo != timezone.utc or "T" not in value:
        raise ValueError("people_observed_at_utc_required")


def people_window(as_of):
    # Import lazily because the catalog exporter loads this overlay at runtime.
    # Share the actual site's month-end semantics, not a second approximation.
    from build_v3_catalog import complete_months
    months = complete_months(date.fromisoformat(as_of[:10]), 12)
    year, month = map(int, months[-1].split("-"))
    return {"from": months[0], "to": months[-1], "months": months,
            "cutoff": f"{months[-1]}-{calendar.monthrange(year, month)[1]:02d}",
            "basis": "first_public_month_included_canonical_works_verified_authorship"}


def author_label_kind(label):
    """Conservative quality label, never destructive normalization."""
    if not isinstance(label, str) or not any(char.isalnum() for char in label):
        return "punctuation_or_empty"
    if label in {"NVIDIA", "Google", "Google DeepMind", "Physical Intelligence", "OpenAI"} or re.search(r"\b(?:Team|Consortium|Collaboration)\s*$", label):
        return "collective_or_organization"
    if re.search(r"(?:Member|Fellow)\s*,?\s*IEEE", label, re.I):
        return "metadata_contamination"
    return "unresolved_person_label"


def _hard_identity(value):
    """Compare explicit identifiers, not fuzzy titles or author-name variants."""
    if not isinstance(value, str):
        return None
    if value.startswith("arxiv:"):
        return "arxiv:" + re.sub(r"v\d+$", "", value[6:])
    if value.startswith("doi:"):
        return "doi:" + value[4:].lower()
    parts = urlparse(value)
    host = (parts.hostname or "").lower()
    if host in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
        match = re.fullmatch(r"/(?:abs|pdf|html)/(.+?)(?:\.pdf)?/?", parts.path)
        if match:
            return "arxiv:" + re.sub(r"v\d+$", "", match.group(1))
    if host in {"doi.org", "dx.doi.org"}:
        return "doi:" + unquote(parts.path.lstrip("/")).lower()
    if parts.scheme in {"http", "https"} and host:
        # Program pages can identify different papers by fragment. Dropping it
        # would collapse hundreds of distinct entries onto one shared identity.
        return "url:" + host + parts.path.rstrip("/") + ("?" + parts.query if parts.query else "") + ("#" + parts.fragment if parts.fragment else "")
    return value if ":" in value else None


def _work_identities(work, manifestations):
    values = {work["work_id"], *work.get("aliases", [])}
    for key, value in (work.get("identifiers") or {}).items():
        if key in {"arxiv", "doi"} and isinstance(value, str):
            values.add(key + ":" + value)
    values.update(row.get("url") for row in manifestations if row.get("url"))
    values.update(work.get(key) for key in ("url", "project_url") if work.get(key))
    return {_hard_identity(value) for value in values} - {None}


def load_people_reviews(directory):
    reviews = []
    for path in sorted(Path(directory).glob("*.json")):
        row = json.loads(path.read_text())
        if not isinstance(row, dict):
            raise ValueError("people_review_object_required:" + path.name)
        reviews.append(row)
    return reviews


def _prepare_reviews(payload, reviews):
    works = {row["work_id"]: row for row in payload.get("works", [])}
    owners = defaultdict(set)
    versions = defaultdict(list)
    for work in works.values():
        for key in [work["work_id"], *work.get("aliases", [])]:
            owners[key].add(work["work_id"])
    for row in payload.get("work-aliases", []):
        owners[row["alias"]].add(row["work_id"])
    for row in payload.get("manifestations", []):
        versions[row["work_id"]].append(row)
    identity_owners = defaultdict(set)
    for work in works.values():
        for identity in _work_identities(work, versions[work["work_id"]]):
            identity_owners[identity].add(work["work_id"])
    tables = {key: [] for key in TABLES}
    seen_people, seen_slugs, seen_reviews = set(), set(), set()
    for review in reviews:
        if review.get("schema_version") != SCHEMA_VERSION or not review.get("review_id") or not isinstance(review.get("people"), list):
            raise ValueError("people_review_schema_invalid")
        if review["review_id"] in seen_reviews:
            raise ValueError("people_review_id_conflict")
        seen_reviews.add(review["review_id"])
        for source_person in review["people"]:
            person = copy.deepcopy(source_person)
            person_id, slug, name = person.get("person_id"), person.get("slug"), person.get("name")
            if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug == "index":
                raise ValueError("people_slug_invalid")
            if person_id != "person:" + slug or person_id in seen_people or slug in seen_slugs:
                raise ValueError("people_identity_conflict")
            if not isinstance(name, str) or not name.strip() or author_label_kind(name) != "unresolved_person_label":
                raise ValueError("people_person_name_required")
            seen_people.add(person_id)
            seen_slugs.add(slug)
            if person.get("identity_status") not in {"profile_verified", "candidate"} or not isinstance(person.get("official_profiles"), list):
                raise ValueError("people_official_identity_required")
            if person["identity_status"] == "profile_verified" and not person["official_profiles"]:
                raise ValueError("people_official_identity_required")
            for source in person["official_profiles"]:
                _url(source.get("url"))
                _observed(source.get("observed_at"))
                if not source.get("label"):
                    raise ValueError("people_profile_label_required")
            aliases = person.setdefault("aliases", [])
            if not isinstance(aliases, list) or any(not isinstance(alias, str) or not alias.strip() for alias in aliases):
                raise ValueError("people_aliases_invalid")
            person.setdefault("name_zh", None)
            person.setdefault("notes", [])
            roles = person.pop("official_roles", [])
            for role in roles:
                _url(role.get("source_url"))
                _observed(role.get("observed_at"))
                if not role.get("organization_name") or not role.get("title"):
                    raise ValueError("people_role_context_required")
                if role.get("organization_id") is not None and role["organization_id"] not in {row["organization_id"] for row in payload.get("organizations", [])}:
                    raise ValueError("people_role_organization_unknown")
                for key in ["valid_from", "valid_to"]:
                    if role.get(key) is not None:
                        date.fromisoformat(role[key])
                if role.get("valid_from") and role.get("valid_to") and role["valid_to"] < role["valid_from"]:
                    raise ValueError("people_role_interval_invalid")
                row = {**role, "person_id": person_id, "review_id": review["review_id"],
                       "basis": "official_role_not_historical_work_affiliation"}
                row["link_id"] = "person-org:" + fingerprint(row)[:24]
                tables["organization-links"].append(row)
            seen_works = set()
            for link in person.pop("authorships", []):
                submitted_id = link.get("work_id")
                matched = owners.get(submitted_id, set())
                if len(matched) != 1:
                    raise ValueError("people_work_identity_unresolved:" + str(submitted_id))
                work_id = next(iter(matched))
                if work_id in seen_works:
                    raise ValueError("people_duplicate_authorship:" + person_id + ":" + work_id)
                seen_works.add(work_id)
                if link.get("status") not in {"verified", "candidate"}:
                    raise ValueError("people_authorship_status_invalid")
                if person["identity_status"] != "profile_verified" and link["status"] == "verified":
                    raise ValueError("people_candidate_identity_cannot_verify_authorship")
                audit = link.get("verification_audit")
                if audit is not None:
                    if not isinstance(audit, dict) or audit.get("result") not in {"verified", "unresolved"} or not audit.get("reason") or not audit.get("batch_id"):
                        raise ValueError("people_verification_audit_invalid")
                    _observed(audit.get("checked_at"))
                    if (audit["result"] == "verified") != (link["status"] == "verified"):
                        raise ValueError("people_verification_audit_status_mismatch")
                    if not isinstance(audit.get("checked_sources"), list):
                        raise ValueError("people_verification_audit_sources_required")
                    for url in audit["checked_sources"]:
                        _url(url)
                identities = _work_identities(works[work_id], versions[work_id])
                for evidence in link.get("evidence", []):
                    _url(evidence.get("url"))
                    _observed(evidence.get("observed_at"))
                    if evidence.get("kind") not in {"official_publications", "official_project", "orcid"} or not evidence.get("statement"):
                        raise ValueError("people_authorship_source_invalid")
                    hard = _hard_identity(_url(evidence.get("work_url", evidence["url"])))
                    if hard not in identities:
                        raise ValueError("people_authorship_work_url_mismatch:" + work_id)
                    if link["status"] == "verified" and identity_owners[hard] != {work_id}:
                        raise ValueError("people_authorship_work_url_ambiguous:" + work_id)
                if link["status"] == "verified" and not link.get("evidence"):
                    raise ValueError("people_verified_authorship_evidence_required")
                roles = link.get("roles")
                if roles is not None:
                    if not isinstance(roles, list) or not roles or link["status"] != "verified":
                        raise ValueError("people_contribution_roles_require_verified_source")
                    for role in roles:
                        if not isinstance(role, dict) or not re.fullmatch(r"[a-z][a-z0-9_]{1,39}", str(role.get("role", ""))) or role.get("scope") not in {"project", "paper"}:
                            raise ValueError("people_contribution_roles_invalid")
                        if role["role"] not in {"project_lead", "equal_contribution", "corresponding_author", "equal_advising"} and not role.get("label"):
                            raise ValueError("people_contribution_roles_official_label_required")
                        _url(role.get("source_url"))
                        _observed(role.get("observed_at"))
                        if role["source_url"] not in {source["url"] for source in link.get("evidence", [])} or not role.get("statement"):
                            raise ValueError("people_contribution_roles_source_unchecked")
                        role_identity = _hard_identity(_url(role.get("work_url")))
                        if role_identity not in identities or identity_owners[role_identity] != {work_id}:
                            raise ValueError("people_contribution_roles_work_url_mismatch")
                row = {**link, "person_id": person_id, "work_id": work_id,
                       "submitted_work_id": submitted_id, "review_id": review["review_id"], "roles": roles,
                       "basis": "direct_official_person_work_link" if link["status"] == "verified" else "reviewed_candidate"}
                row["authorship_id"] = "authorship:" + fingerprint([person_id, work_id])[:24]
                tables["authorship-reviews"].append(row)
            for evidence in person.pop("influence_evidence", []):
                _url(evidence.get("source_url"))
                _observed(evidence.get("observed_at"))
                dimension = evidence.get("dimension")
                if not evidence.get("statement") or dimension not in {"citation_count", "independent_adoption", "independent_replication"} or evidence.get("review_status") not in {"verified", "draft"}:
                    raise ValueError("people_influence_context_required")
                matched = owners.get(evidence.get("work_id"), set())
                if len(matched) != 1:
                    raise ValueError("people_influence_work_unresolved")
                work_id = next(iter(matched))
                hard = _hard_identity(_url(evidence.get("work_url")))
                if hard not in _work_identities(works[work_id], versions[work_id]) or (evidence["review_status"] == "verified" and identity_owners[hard] != {work_id}):
                    raise ValueError("people_influence_work_url_mismatch")
                if evidence["review_status"] == "verified" and not any(row["person_id"] == person_id and row["work_id"] == work_id and row["status"] == "verified" for row in tables["authorship-reviews"]):
                    raise ValueError("people_influence_verified_authorship_required")
                measured = date.fromisoformat(evidence.get("as_of", ""))
                if measured > date.fromisoformat(evidence["observed_at"][:10]):
                    raise ValueError("people_influence_measurement_in_future")
                if dimension == "citation_count":
                    if not evidence.get("provider") or not isinstance(evidence.get("count"), int) or isinstance(evidence.get("count"), bool) or evidence["count"] < 0:
                        raise ValueError("people_citation_measurement_required")
                elif evidence["review_status"] == "verified":
                    if evidence.get("independent_team") is not True or not evidence.get("independence_statement") or not evidence.get("adopter_name"):
                        raise ValueError("people_independence_source_required")
                    _url(evidence.get("independence_source_url"))
                row = {**evidence, "person_id": person_id, "work_id": work_id, "review_id": review["review_id"]}
                row["evidence_id"] = "person-evidence:" + fingerprint(row)[:24]
                tables["influence-evidence"].append(row)
            person["review_id"] = review["review_id"]
            tables["persons"].append(person)
    measured = {}
    for row in tables["influence-evidence"]:
        if row["dimension"] == "citation_count" and row["review_status"] == "verified":
            key = (row["person_id"], row["work_id"], row["provider"], row["as_of"])
            if key in measured and measured[key] != row["count"]:
                raise ValueError("people_conflicting_citation_snapshot")
            measured[key] = row["count"]
    return tables


def load_people_authority(directory):
    return {table: read_table(Path(directory), table) for table in TABLES}


def _authority_reviews(authority):
    """Revalidate the stored source facts without trusting staging at export."""
    grouped = {}
    person_ids = {row["person_id"] for row in authority.get("persons", [])}
    for table in TABLES:
        ids = [row[TABLE_KEYS[table]] for row in authority.get(table, [])]
        if len(ids) != len(set(ids)):
            raise ValueError("people_authority_duplicate_id:" + table)
        if table != "persons" and any(row.get("person_id") not in person_ids for row in authority.get(table, [])):
            raise ValueError("people_authority_orphan:" + table)
    for source in authority.get("persons", []):
        person = copy.deepcopy(source)
        if any(key in person for key in ["official_roles", "authorships", "influence_evidence"]):
            raise ValueError("people_authority_nested_facts_must_use_separate_tables")
        review_id = person.pop("review_id")
        derived = {"person_id", "review_id", "basis", "link_id", "evidence_id", "authorship_id", "submitted_work_id"}
        def rows(table):
            return [{key: copy.deepcopy(value) for key, value in row.items() if key not in derived}
                    for row in authority.get(table, []) if row["person_id"] == person["person_id"]]
        person["official_roles"] = rows("organization-links")
        person["authorships"] = rows("authorship-reviews")
        person["influence_evidence"] = rows("influence-evidence")
        grouped.setdefault(review_id, {"schema_version": SCHEMA_VERSION, "review_id": review_id, "people": []})["people"].append(person)
    return list(grouped.values())


def ingest_people_reviews(payload, reviews, existing=None):
    """Preflight all staging, then return a new authority; conflicting IDs fail."""
    existing = existing or {table: [] for table in TABLES}
    _prepare_reviews(payload, _authority_reviews(existing))
    incoming = _prepare_reviews(payload, reviews)
    result = copy.deepcopy(existing)
    resolved = {}
    for work in payload.get("works", []):
        for value in [work["work_id"], *work.get("aliases", [])]:
            resolved[value] = work["work_id"]
    resolved.update({row["alias"]: row["work_id"] for row in payload.get("work-aliases", [])})

    def author_identity(row):
        return row["person_id"], resolved.get(row["work_id"], row["work_id"])

    def author_semantics(row):
        return {**{key: value for key, value in row.items() if key not in {"work_id", "submitted_work_id", "authorship_id", "verification_audit"}},
                "work_id": resolved.get(row["work_id"], row["work_id"])}

    for table in TABLES:
        result.setdefault(table, [])
        key = TABLE_KEYS[table]
        by_id = {row[key]: row for row in result[table]}
        existing_authorships = {author_identity(row): row for row in result[table]} if table == "authorship-reviews" else {}
        def influence_semantics(row):
            return fingerprint({**{name: value for name, value in row.items() if name not in {"work_id", "evidence_id"}},
                                "work_id": resolved.get(row["work_id"], row["work_id"])})
        existing_influence = {influence_semantics(row) for row in result[table]} if table == "influence-evidence" else set()
        for row in incoming[table]:
            if table == "authorship-reviews" and (old := existing_authorships.get(author_identity(row))) is not None:
                if author_semantics(old) != author_semantics(row):
                    raise ValueError("people_authority_conflict:" + table + ":" + row[key])
                # A canonical work becoming an alias is not a new person/work
                # observation. Preserve the first source identity and lineage.
                continue
            if table == "influence-evidence" and influence_semantics(row) in existing_influence:
                continue
            if row[key] in by_id and by_id[row[key]] != row:
                raise ValueError("people_authority_conflict:" + table + ":" + row[key])
            by_id[row[key]] = copy.deepcopy(row)
        result[table] = sorted(by_id.values(), key=lambda row: row[key])
    _prepare_reviews(payload, _authority_reviews(result))
    return result


def save_people_authority(directory, authority):
    """Explicit ingest only. Never called by ordinary export."""
    directory = Path(directory)
    for table in TABLES:
        write_if_changed(directory / f"{table}.jsonl", "".join(encode(row) + "\n" for row in authority[table]))


def _influence_metrics(records, selected, as_of):
    selected_ids = {row["work_id"] for row in selected}
    validation_ids = {row["work_id"] for row in selected if row.get("validation_eligible", True)}
    cutoff = date.fromisoformat(as_of[:10])
    eligible = [row for row in records if row["review_status"] == "verified" and row["work_id"] in selected_ids
                and row["as_of"] <= as_of[:10] and public_day(row["observed_at"]) <= cutoff]
    citation_groups = defaultdict(dict)
    for row in eligible:
        if row["dimension"] == "citation_count":
            key = (row["provider"], row["as_of"])
            previous = citation_groups[key].get(row["work_id"])
            if previous is not None and previous["count"] != row["count"]:
                raise ValueError("people_conflicting_citation_snapshot")
            citation_groups[key][row["work_id"]] = row
    full = [(key, values) for key, values in citation_groups.items() if set(values) == selected_ids and selected_ids]
    chosen = max(full, key=lambda item: (item[0][1], item[0][0])) if full else None
    adoption = [row for row in eligible if row["dimension"] == "independent_adoption" and row["work_id"] in validation_ids]
    replication = [row for row in eligible if row["dimension"] == "independent_replication" and row["work_id"] in validation_ids]
    return {"citations": sum(row["count"] for row in chosen[1].values()) if chosen else None,
            "citation_coverage": {"required_works": len(selected_ids), "measured_works": len({row["work_id"] for row in eligible if row["dimension"] == "citation_count"}),
                                  "provider": chosen[0][0] if chosen else None, "as_of": chosen[0][1] if chosen else None,
                                  "basis": "same_provider_same_date_sum_of_work_counts_not_unique_citing_works"},
            "adoption": len({row["adopter_name"] for row in adoption}) if adoption else None,
            "adoption_basis": "registered_source_checked_independent_adopters_not_exhaustive_market_adoption",
            "independent_replication_works_window": len({row["work_id"] for row in replication}) if replication else None}


def build_people_radar(payload, authority, as_of, *, generated_at=None, dataset_version=None, research_status_as_of=None):
    """Pure construction/validation. No network, input mutation or authority writes."""
    tables = _prepare_reviews(payload, _authority_reviews(authority))
    window = people_window(as_of)
    works = {row["work_id"]: row for row in payload.get("works", [])}
    versions, texts = defaultdict(list), defaultdict(list)
    sources = {row["source_record_id"]: row for row in payload.get("source-records", [])}
    current_cutoff = research_status_as_of or latest_status_observation(list(works.values()), sources, as_of)
    influence_cutoff = max([public_day(current_cutoff), public_day(as_of),
                           *[public_day(row["observed_at"]) for row in tables["influence-evidence"] if row["review_status"] == "verified"]]).isoformat()
    for row in payload.get("manifestations", []):
        versions[row["work_id"]].append(row)
    for row in payload.get("text-snapshots", []):
        texts[row["work_id"]].append(row)
    labels = defaultdict(set)
    reviewed_names = {name for row in tables["persons"] for name in [row["name"], *row.get("aliases", [])]}
    for work in works.values():
        for label in work.get("authors") or []:
            if isinstance(label, str) and author_label_kind(label) == "unresolved_person_label":
                labels[label].add(work["work_id"])
        # Historical source authors may differ from a merged current array.
        # Select the eligible version before using any such label, including
        # for candidates; a future author addition must not leak backwards.
        if any(name in reviewed_names for snapshot in texts[work["work_id"]] for name in snapshot.get("authors", [])):
            historical = text_as_of(work, texts[work["work_id"]], window["cutoff"])
            for label in historical["authors"]:
                if label in reviewed_names and author_label_kind(label) == "unresolved_person_label":
                    labels[label].add(work["work_id"])
    links = defaultdict(dict)
    for link in tables["authorship-reviews"]:
        links[link["person_id"]][link["work_id"]] = link
    person_summaries, details = [], {}
    in_window = lambda work: research_eligible(work) and eligible_month(work, window["cutoff"]) in window["months"]
    view_cache = {}

    def work_view(work_id):
        if work_id not in view_cache:
            work = works[work_id]
            text = text_as_of(work, texts[work_id], window["cutoff"])
            evidence = evidence_as_of(work, versions[work_id], window["cutoff"], sources)
            current_status = resolve_research_status(work, current_cutoff, sources)
            validation_eligible = current_status["validation_eligible"]
            current_flags = dict(evidence["evidence_flags"])
            if not validation_eligible:
                current_flags = {key: bool(value) if key in {"open_code", "open_model", "open_data", "benchmark"} else False for key, value in current_flags.items()}
            raw = list(work.get("authors") or [])
            view_cache[work_id] = {
                "work_id": work_id, "title": work.get("title"), "title_zh": work.get("title_zh"),
                "url": next((row["url"] for row in versions[work_id] if row.get("url")), work.get("url")),
                "first_public_date": work.get("first_public_date"), "first_public_date_precision": work.get("first_public_date_precision"),
                "primary_direction": work.get("primary_direction"), "directions": work.get("directions", []),
                "questions": work.get("questions", []), "relevance_status": work.get("relevance", {}).get("status"),
                "in_complete_window": in_window(work), "evidence_as_of": window["cutoff"],
                "evidence_grade": evidence["evidence_grade"] if validation_eligible else "E0",
                "strict_peer_reviewed": evidence["strict_peer_reviewed"] and validation_eligible,
                "evidence_flags": current_flags, "evidence_gaps": evidence["information_gaps"],
                "historical_evidence_as_of": window["cutoff"],
                "historical_evidence": {key: evidence.get(key) for key in ["evidence_grade", "strict_peer_reviewed", "evidence_flags", "research_status"]},
                "research_status": {**current_status, "as_of": current_cutoff},
                "validation_eligible": validation_eligible,
                "manifestations": copy.deepcopy(versions[work_id]), "available_manifestation_ids": evidence["available_manifestation_ids"],
                "raw_authors": raw, "author_labels": [{"raw": label, "kind": author_label_kind(label)} for label in raw],
                "version_authorship": {key: text.get(key) for key in ["status", "version", "available_at", "authors", "source_ids", "snapshot_ids"]},
                "roles": None,
            }
        return view_cache[work_id]

    for person in sorted(tables["persons"], key=lambda row: (row["name"], row["person_id"])):
        person_id = person["person_id"]
        # Exact string lookup only. Explicit aliases expand candidates, never verification.
        for label in [person["name"], *person["aliases"]]:
            for work_id in sorted(labels.get(label, set())):
                if work_id not in links[person_id]:
                    links[person_id][work_id] = {"person_id": person_id, "work_id": work_id,
                        "submitted_work_id": work_id, "status": "candidate", "matched_author_name": label,
                        "evidence": [], "roles": None, "review_id": None, "basis": "exact_name_label_not_disambiguated",
                        "authorship_id": "authorship:" + fingerprint([person_id, work_id])[:24]}
                    tables["authorship-reviews"].append(links[person_id][work_id])
        verified, candidates = [], []
        for work_id, link in sorted(links[person_id].items()):
            view = {**work_view(work_id), "authorship_evidence": copy.deepcopy(link), "roles": copy.deepcopy(link.get("roles"))}
            author_name = link.get("matched_author_name")
            archived = view["version_authorship"]
            view["authorship_version_match"] = ("unavailable" if archived["status"] not in {"available", "available_unversioned"}
                else "not_resolved_to_version_label" if not author_name else "exact_label_present" if author_name in archived["authors"] else "label_not_present_in_available_version")
            (verified if link["status"] == "verified" else candidates).append(view)
        selected = [row for row in verified if row["in_complete_window"]]
        candidate_selected = [row for row in candidates if row["in_complete_window"]]
        counts = Counter(row["primary_direction"] for row in selected if row["primary_direction"])
        monthly = Counter(works[row["work_id"]]["first_public_date"][:7] for row in selected)
        gaps = ["contribution_roles_not_inferred"]
        if person["identity_status"] != "profile_verified":
            gaps.append("person_identity_unresolved_not_in_verified_statistics")
        if not verified:
            gaps.append("profile_verified_but_no_verified_authorship")
        if candidates:
            gaps.append("same_name_candidate_works_not_counted")
        if any(row["version_authorship"]["status"] not in {"available", "available_unversioned"} for row in verified):
            gaps.append("historical_author_version_unavailable_for_some_verified_works")
        metrics = {"verified_works_window": len(selected), "verified_works_all": len(verified),
                   "candidate_works_window": len(candidate_selected), "candidate_works_all": len(candidates),
                   "peer_reviewed_window": sum(row["strict_peer_reviewed"] for row in selected),
                   "technical_reports_window": sum(any(version["kind"] == "technical_report" and version["manifestation_id"] in row["available_manifestation_ids"] for version in row["manifestations"]) for row in selected),
                   "real_robot_window": sum(bool(row["evidence_flags"].get("real_robot")) for row in selected),
                   "historical_peer_reviewed_window": sum(bool(row["historical_evidence"]["strict_peer_reviewed"]) for row in selected),
                   "validation_blocked_works_window": sum(not row["validation_eligible"] for row in selected),
                   "citations": None, "adoption": None}
        metrics.update(active_months=sum(bool(monthly[month]) for month in window["months"]),
                       independent_projects=None,
                       role_verified_work_count=sum(bool(row["roles"]) for row in selected) if any(row["roles"] for row in selected) else None)
        influence = [row for row in tables["influence-evidence"] if row["person_id"] == person_id]
        metrics.update(_influence_metrics(influence, selected, influence_cutoff))
        checked = [link["verification_audit"] for link in links[person_id].values() if link.get("verification_audit")]
        candidate_review = {"checked": len(checked), "confirmed": sum(row["result"] == "verified" for row in checked),
                            "unresolved": sum(row["result"] == "unresolved" for row in checked),
                            "last_checked": max((row["checked_at"] for row in checked), default=None),
                            "basis": "registered_candidate_cohort_official_source_checks_not_complete_bibliography"}
        if metrics["citations"] is None:
            gaps.append("citations_not_fully_measured")
        if metrics["adoption"] is None:
            gaps.append("adoption_not_measured")
        summary = {**copy.deepcopy(person), "official_roles": [copy.deepcopy(row) for row in tables["organization-links"] if row["person_id"] == person_id], "metrics": metrics,
                   "candidate_review": candidate_review,
                   "directions": [{"code": f"D{number}", "count": counts[f"D{number}"]} for number in range(1, 16)],
                   "monthly_activity": [{"month": month, "count": monthly[month]} for month in window["months"]],
                   "verified_work_ids": [row["work_id"] for row in verified], "candidate_work_ids": [row["work_id"] for row in candidates],
                   "data_gaps": gaps}
        person_summaries.append(summary)
        details[person["slug"]] = {**summary, "schema_version": SCHEMA_VERSION, "window": window,
                                  "verified_works": verified, "candidate_works": candidates,
                                  "influence_evidence": influence,
                                  "limitations": LIMITATIONS}
    verified_ids = {row["work_id"] for row in tables["authorship-reviews"] if row["status"] == "verified"}
    review_hash = fingerprint(authority)
    counts = {"persons": len(person_summaries),
              "profile_verified_persons": sum(row["identity_status"] == "profile_verified" for row in person_summaries),
              "candidate_identity_persons": sum(row["identity_status"] == "candidate" for row in person_summaries),
              "persons_with_verified_work": sum(bool(row["verified_work_ids"]) for row in person_summaries),
              "verified_authorships": sum(row["status"] == "verified" for row in tables["authorship-reviews"]),
              "candidate_authorships": sum(row["status"] == "candidate" for row in tables["authorship-reviews"]),
              "verified_included_works_window": sum(in_window(works[key]) for key in verified_ids)}
    version = dataset_version or fingerprint({"authority": review_hash, "people": person_summaries,
                                              "details": details, "window": window, "current_cutoff": current_cutoff})
    coauthors = defaultdict(set)
    for link in tables["authorship-reviews"]:
        if link["status"] == "verified" and in_window(works[link["work_id"]]):
            coauthors[link["work_id"]].add(link["person_id"])
    pairs = defaultdict(list)
    for work_id, person_ids in sorted(coauthors.items()):
        ordered = sorted(person_ids)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1:]:
                pairs[(left, right)].append(work_id)
    coauthorships = [{"person_ids": list(pair), "work_ids": ids, "count": len(ids),
                     "basis": "both_people_verified_same_canonical_work_not_independent_adoption"}
                    for pair, ids in sorted(pairs.items())]
    index = {"schema_version": SCHEMA_VERSION, "dataset_version": version, "review_hash": review_hash,
             "authority_hash": review_hash,
             "research_status_as_of": current_cutoff,
             "influence_observed_as_of": influence_cutoff,
             "generated_at": generated_at, "window": window, "counts": counts,
             "limitations": LIMITATIONS, "people": person_summaries, "coauthorships": coauthorships,
             "downloads": {key: f"/downloads/people/{key}.jsonl" for key in TABLES}}
    for detail in details.values():
        detail.update(dataset_version=version, review_hash=review_hash, generated_at=generated_at,
                      research_status_as_of=current_cutoff, influence_observed_as_of=influence_cutoff)
        detail["coauthorships"] = [row for row in coauthorships if detail["person_id"] in row["person_ids"]]
    # Derived exact-name candidates are public in the profiles, not promoted to authority.
    return {"index": index, "details": details, "tables": copy.deepcopy(authority)}


def export_people_files(bundle, api_directory, download_directory):
    """Only write declared derived people artifacts; never touch review inputs."""
    api_directory, download_directory = Path(api_directory), Path(download_directory)
    write_if_changed(api_directory / "index.json", encode(bundle["index"]) + "\n")
    for slug, detail in bundle["details"].items():
        write_if_changed(api_directory / f"{slug}.json", encode(detail) + "\n")
    for table in TABLES:
        write_if_changed(download_directory / f"{table}.jsonl", "".join(encode(row) + "\n" for row in bundle["tables"][table]))


def _sqlite_people_rows(table, bundle):
    resolved = {(detail["person_id"], identity): row["work_id"]
                for detail in bundle["details"].values() for row in detail["verified_works"] + detail["candidate_works"]
                for identity in [row["work_id"], row["authorship_evidence"].get("submitted_work_id")]}
    for index, row in enumerate(bundle["tables"][table]):
        canonical = resolved.get((row["person_id"], row.get("work_id")), row.get("work_id"))
        yield (index, row[TABLE_KEYS[table]], row["person_id"], row.get("work_id"), canonical,
               row.get("status") or row.get("review_status") or row.get("identity_status"), encode(row))


def build_people_sqlite(connection, bundle):
    for table in TABLES:
        name = "people_" + table.replace("-", "_")
        connection.execute(f"CREATE TABLE {name} (row_index INTEGER PRIMARY KEY, record_id TEXT UNIQUE NOT NULL, person_id TEXT NOT NULL, work_id TEXT, canonical_work_id TEXT, status TEXT, payload_json TEXT NOT NULL)")
        connection.execute(f"CREATE INDEX {name}_person ON {name}(person_id)")
        connection.executemany(f"INSERT INTO {name} VALUES (?,?,?,?,?,?,?)", _sqlite_people_rows(table, bundle))
    connection.execute("CREATE TABLE people_api (path TEXT PRIMARY KEY, payload_json TEXT NOT NULL)")
    connection.executemany("INSERT INTO people_api VALUES (?,?)", [("index", encode(bundle["index"])), *[(slug, encode(detail)) for slug, detail in bundle["details"].items()]])


def audit_people_exports(bundle, api_directory, download_directory, connection):
    errors = []
    api_directory, download_directory = Path(api_directory), Path(download_directory)
    for key, value in {"index": bundle["index"], **bundle["details"]}.items():
        path = api_directory / f"{key}.json"
        if not path.exists() or json.loads(path.read_text()) != value:
            errors.append("people_api_mismatch:" + key)
    for table in TABLES:
        path = download_directory / f"{table}.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else None
        if rows != bundle["tables"][table]:
            errors.append("people_download_mismatch:" + table)
        name = "people_" + table.replace("-", "_")
        saved = list(connection.execute(f"SELECT row_index,record_id,person_id,work_id,canonical_work_id,status,payload_json FROM {name} ORDER BY row_index"))
        if saved != list(_sqlite_people_rows(table, bundle)):
            errors.append("people_sqlite_mismatch:" + table)
    saved_api = {key: json.loads(value) for key, value in connection.execute("SELECT path,payload_json FROM people_api")}
    if saved_api != {"index": bundle["index"], **bundle["details"]}:
        errors.append("people_sqlite_api_mismatch")
    return {"status": "passed" if not errors else "failed", "counts": bundle["index"]["counts"], "errors": errors}
