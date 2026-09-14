"""Pure, denominator-explicit organization coverage and discovery audit.

Affiliations are G0 observations of parent institutions, never lab attribution.
This module does not fetch sources, modify the registry, or infer official URLs.
"""
from __future__ import annotations

import calendar
import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit


def normalized(value) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or "")).casefold()).strip()


def parsed_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def valid_url(value) -> bool:
    try:
        parsed = urlsplit(str(value or ""))
        return parsed.scheme in {"https", "http"} and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def official_urls(org: dict) -> set[str]:
    values = org.get("official_urls") or {}
    if isinstance(values, dict):
        values = values.values()
    return {value for value in values if isinstance(value, str) and valid_url(value)}


def attribution_valid(link: dict, work: dict, org: dict) -> bool:
    if not valid_url(link.get("evidence_url")):
        return False
    when = parsed_date(work.get("first_public_date"))
    start, end = parsed_date(org.get("active_from")), parsed_date(org.get("active_to"))
    if when and ((start and when < start) or (end and when > end)):
        return False
    if link.get("evidence_grade") == "G1":
        return True
    if link.get("evidence_grade") != "G2" or work.get("first_public_date_precision") in {"year", "unknown"}:
        return False
    membership = link.get("membership_evidence") or {}
    start, end = parsed_date(membership.get("valid_from")), parsed_date(membership.get("valid_to"))
    authors = {normalized(author if isinstance(author, str) else author.get("name")) for author in work.get("authors", [])}
    return bool(start and when and valid_url(membership.get("source_url")) and normalized(membership.get("author")) in authors
                and start <= when and (not end or when <= end))


def source_rows(sources) -> tuple[list[dict], list[dict]]:
    if isinstance(sources, dict):
        return sources.get("registered", sources.get("sources", sources.get("health", []))), sources.get("records", [])
    values = sources or []
    return [row for row in values if row.get("organization_id")], [row for row in values if row.get("source_record_id")]


def source_health(organizations: list[dict], sources, as_of: date) -> list[dict]:
    registered, _ = source_rows(sources)
    by_org = {row["organization_id"]: row for row in organizations}
    observed = {}
    for row in registered:
        key = (row.get("organization_id"), row.get("url"))
        if key[0] not in by_org or not valid_url(key[1]):
            continue
        previous = observed.get(key)
        if not previous or (parsed_date(row.get("last_checked")) or date.min) >= (parsed_date(previous.get("last_checked")) or date.min):
            observed[key] = row
    for org in organizations:
        for url in official_urls(org):
            observed.setdefault((org["organization_id"], url), {"organization_id": org["organization_id"], "url": url, "status": "unverified", "kind": "registered_official_url"})
    output = []
    for (org_id, url), raw in sorted(observed.items()):
        org = by_org[org_id]
        cadence = 7 if org.get("tier") in {"T0", "T1"} else 31
        checked = parsed_date(raw.get("last_checked"))
        valid_check = bool(checked and checked <= as_of)
        age = (as_of - checked).days if valid_check else None
        failures = raw.get("consecutive_failures", 0)
        failures = failures if type(failures) is int and failures >= 0 else 0
        stale = failures >= 2 or bool(age is not None and age >= 2 * cadence)
        healthy = raw.get("status") == "healthy" and valid_check and age <= cadence and failures == 0
        output.append({"source_id": raw.get("source_id") or "source:registered:" + hashlib.sha256(f"{org_id}|{url}".encode()).hexdigest()[:16],
                       "organization_id": org_id, "url": url, "kind": raw.get("kind"),
                       "status": "stale" if stale else "healthy" if healthy else "overdue" if age is not None and age > cadence else raw.get("status", "unverified") if valid_check else "unverified",
                       "observed_status": raw.get("status", "unverified"), "last_checked": raw.get("last_checked"),
                       "last_success": raw.get("last_success"), "consecutive_failures": failures,
                       "check_age_days": age, "cadence_days": cadence, "verified_healthy": healthy,
                       "stale_warning": stale, "registration_only": not valid_check,
                       "official_registered": url in official_urls(org) or str(raw.get("source_type", "")).startswith("official_")})
    return output


def affiliation_names(work: dict) -> list[str]:
    names = []
    for field in ("institutions", "affiliations"):
        values = work.get(field) or []
        if isinstance(values, str):
            values = [values]
        for value in values:
            name = value if isinstance(value, str) else value.get("display_name") or value.get("name") or value.get("institution") if isinstance(value, dict) else None
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    return list(dict.fromkeys(names))


def root_entities(org_id: str, organizations: dict, visited=None) -> set[str]:
    visited = set(visited or ())
    if org_id in visited:
        return set()
    visited.add(org_id)
    org = organizations[org_id]
    parents = [row["parent_id"] for row in org.get("parent_relations", [])
               if row.get("parent_id") in organizations and valid_url(row.get("evidence_url"))]
    if parents:
        return {root for parent in parents for root in root_entities(parent, organizations, visited)}
    # A standalone laboratory label is still not an institution attribution.
    return {org_id} if org.get("entity_type") in {"university", "company", "research_company", "research_institute"} else set()


def discover_affiliations(works: list[dict], organizations: list[dict]) -> tuple[list[dict], list[dict]]:
    by_id = {row["organization_id"]: row for row in organizations}
    names = defaultdict(set)
    for org in organizations:
        for name in [org.get("display_name"), org.get("short_name"), *org.get("aliases", [])]:
            if name:
                names[normalized(name)].add(org["organization_id"])
    # Unambiguous institution abbreviations remain parent-only observations.
    for org in organizations:
        label = normalized(org.get("display_name"))
        if org.get("entity_type") == "university" and label == "carnegie mellon university":
            names["cmu"].add(org["organization_id"])
        if org.get("entity_type") == "company" and label in {"nvidia", "nvidia corporation"}:
            names["nvidia"].add(org["organization_id"])
    candidates, observations = {}, []
    for work in works:
        for name in affiliation_names(work):
            key = normalized(name)
            malformed = not any(char.isalpha() for char in key) or key in {"unknown", "none", "n/a", "university", "research", "company"}
            collision = key in {"pi", "physical intelligence", "physical intelligence π"}
            matches = sorted(names.get(key, set()))
            parents = sorted({parent for match in matches for parent in root_entities(match, by_id)}) if not collision else []
            ambiguous = collision or len(parents) > 1 or len(matches) > 1 and not parents
            observation = {"work_id": work["work_id"], "affiliation": name, "evidence_grade": "G0",
                           "parent_organization_ids": [] if ambiguous else parents,
                           "matched_label_organization_ids": matches, "status": "invalid_label" if malformed else "ambiguous" if ambiguous else "parent_only" if parents else "unregistered",
                           "ambiguity_flags": ["malformed_affiliation_label"] if malformed else ["physical_intelligence_company_vs_mpi_is"] if collision else ["nonunique_registry_name"] if ambiguous else []}
            observations.append(observation)
            if malformed:
                continue
            if key not in candidates:
                candidates[key] = {"candidate_id": "candidate:affiliation:" + hashlib.sha256(key.encode()).hexdigest()[:16],
                                   "name": name, "aliases": [], "status": "discovery_only", "tier": "T2", "parent_affiliation_only": True,
                                   "official_homepage": None, "leaders": [], "evidence_grade": "G0", "evidence_work_ids": [],
                                   "existing_parent_organization_ids": observation["parent_organization_ids"],
                                   "matched_label_organization_ids": matches, "ambiguity_flags": observation["ambiguity_flags"],
                                   "next_action": "resolve_entity_and_verify_official_source"}
            candidate = candidates[key]
            candidate["aliases"] = sorted(set(candidate["aliases"]) | {name})
            candidate["evidence_work_ids"] = sorted(set(candidate["evidence_work_ids"]) | {work["work_id"]})
    return sorted(candidates.values(), key=lambda row: normalized(row["name"])), sorted(observations, key=lambda row: (row["work_id"], row["affiliation"]))


def work_source_urls(work: dict, records: dict) -> list[str]:
    urls = {records[value]["url"] for value in work.get("source_record_ids", []) if value in records and valid_url(records[value].get("url"))}
    identifiers = work.get("identifiers", {})
    arxiv = str(identifiers.get("arxiv") or "")
    if re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", arxiv):
        urls.add("https://arxiv.org/abs/" + arxiv)
    doi = str(identifiers.get("doi") or "")
    if doi.startswith("10.") and "/" in doi:
        urls.add("https://doi.org/" + doi)
    return sorted(urls)


def build_organization_coverage(works, organizations, links, sources, as_of) -> dict:
    """Return an audit/proposed changes only; every supplied collection is read-only."""
    end = parsed_date(as_of)
    if end is None:
        raise ValueError("as_of must be an ISO calendar date")
    start = end.replace(year=end.year - 1, day=min(end.day, calendar.monthrange(end.year - 1, end.month)[1])) + timedelta(days=1)
    by_org = {row["organization_id"]: row for row in organizations}
    by_work = {row["work_id"]: row for row in works}
    organizations, works = list(by_org.values()), list(by_work.values())
    recent = [row for row in works if row.get("relevance", {}).get("status") == "included"
              and row.get("first_public_date_precision") not in {"year", "unknown"}
              and parsed_date(row.get("first_public_date")) is not None and start <= parsed_date(row["first_public_date"]) <= end]
    recent_ids = {row["work_id"] for row in recent}
    _, record_rows = source_rows(sources)
    records = {row["source_record_id"]: row for row in record_rows if row.get("source_record_id")}
    health = source_health(organizations, sources, end)
    health_by_org = defaultdict(list)
    for row in health:
        health_by_org[row["organization_id"]].append(row)
    verified_by_org, verified_by_work, all_grades = defaultdict(set), defaultdict(set), defaultdict(set)
    link_issues = []
    for link in links:
        wid, oid = link.get("work_id"), link.get("organization_id")
        if wid in by_work:
            all_grades[wid].add(link.get("evidence_grade", "unknown"))
        if wid not in by_work or oid not in by_org:
            link_issues.append({"work_id": wid, "organization_id": oid, "reason": "unregistered_identity"})
            continue
        if not attribution_valid(link, by_work[wid], by_org[oid]):
            if wid in recent_ids:
                link_issues.append({"work_id": wid, "organization_id": oid, "reason": "attribution_not_verified", "evidence_grade": link.get("evidence_grade")})
            continue
        if wid in recent_ids:
            verified_by_org[oid].add(wid)
            if by_org[oid].get("tracking_unit") is not False:
                verified_by_work[wid].add(oid)
    def high_signal(work):
        types = set(work.get("output_types", [])) | {work.get("kind")}
        source_types = {str(records[s].get("source_type", "")).lower() for s in work.get("source_record_ids", []) if s in records}
        return bool(work.get("curated") or work.get("strict_peer_reviewed") or work.get("evidence_grade") in {"E1", "E2", "E3", "E4"}
                    or "technical_report" in types or any("technical_report" in value for value in source_types))
    high = [row for row in recent if high_signal(row)]
    queue = [{"work_id": row["work_id"], "title": row.get("title"), "directions": row.get("directions", []),
              "evidence_grade": row.get("evidence_grade", "E0"), "source_urls": work_source_urls(row, records),
              "current_link_grades": sorted(all_grades[row["work_id"]]), "first_public_date": row.get("first_public_date"),
              "reason": "no_verified_research_group_attribution", "affiliations": affiliation_names(row)}
             for row in high if not verified_by_work[row["work_id"]]]
    queue.sort(key=lambda row: (row["first_public_date"] or "", row["work_id"]), reverse=True)
    coverage, changes = [], []
    for org in organizations:
        oid = org["organization_id"]
        tier = org.get("tier") or ("T0" if org.get("tracking_unit") else "T2")
        verified = sorted(verified_by_org[oid])
        checks = health_by_org[oid]
        official = [row for row in checks if row["official_registered"] and row["verified_healthy"]]
        strong = [wid for wid in verified if by_work[wid].get("evidence_grade") in {"E2", "E3", "E4"}]
        promotion_eligible = bool(tier == "T2" and org.get("tracking_unit") is not False and org.get("entity_type") not in {"university", "company"}
                                  and official and (len(verified) >= 2 or strong))
        effective = "T1" if promotion_eligible else tier
        if promotion_eligible:
            changes.append({"organization_id": oid, "from": tier, "to": "T1", "reason": "verified_official_source_and_research_threshold",
                            "evidence_work_ids": verified, "official_source_urls": sorted(row["url"] for row in official)})
        gaps = []
        if not checks:
            gaps.append("no_registered_official_source")
        if not official:
            gaps.append("official_source_not_recently_verified")
        if not verified:
            gaps.append("no_recent_g1_g2_relevant_work")
        if any(row["stale_warning"] for row in checks):
            gaps.append("stale_source")
        checked_dates = [row["last_checked"] for row in checks if row.get("last_checked")]
        coverage.append({"organization_id": oid, "name": org.get("display_name") or org.get("name") or oid,
                         "slug": org.get("slug"), "tier": tier, "effective_tier": effective, "tracking_unit": org.get("tracking_unit", False),
                         "registered_official_urls": sorted(official_urls(org)), "source_counts": {"registered": len(checks), "verified_healthy": len(official),
                             "stale": sum(row["stale_warning"] for row in checks), "unverified": sum(row["registration_only"] for row in checks)},
                         "verified_work_count": len(verified), "verified_work_ids": verified,
                         "monthly_relevant_work_count": sum(str(by_work[wid].get("first_public_date", "")).startswith(end.strftime("%Y-%m")) for wid in verified),
                         "last_checked": max(checked_dates) if checked_dates else None,
                         "stale_warning": any(row["stale_warning"] for row in checks), "gaps": gaps,
                         "tier_policy": "core_retained" if tier == "T0" else "promotion_eligible" if promotion_eligible else "retained"})
    candidates, observations = discover_affiliations(recent, organizations)
    attributed = sum(bool(verified_by_work[row["work_id"]]) for row in high)
    tracked = [row for row in coverage if row["tracking_unit"] or row["effective_tier"] in {"T0", "T1"}]
    tracked_ids = {row["organization_id"] for row in tracked}
    return {"schema_version": "3", "as_of": end.isoformat(), "window": {"from": start.isoformat(), "to": end.isoformat(), "basis": "canonical_first_public_date"},
            "scope_note": "覆盖率仅针对当前登记来源与已纳入语料；没有全球发布清单金标准，官方发布召回率未测量。",
            "metrics": {"registered_entities": len(organizations), "registered_tracking_groups": len(tracked),
                        "core_groups": sum(row["tier"] == "T0" for row in coverage), "core_groups_visible": sum(row["tier"] == "T0" for row in tracked),
                        "registered_sources": len(health), "verified_healthy_sources": sum(row["verified_healthy"] for row in health),
                        "registered_tracking_sources": sum(row["organization_id"] in tracked_ids for row in health),
                        "verified_healthy_tracking_sources": sum(row["organization_id"] in tracked_ids and row["verified_healthy"] for row in health),
                        "stale_sources": sum(row["stale_warning"] for row in health),
                        "source_verification_rate": round(sum(row["verified_healthy"] for row in health) / len(health), 6) if health else None,
                        "relevant_works_in_window": len(recent), "high_signal_works": len(high), "high_signal_attributed_works": attributed,
                        "high_signal_attribution_rate": round(attributed / len(high), 6) if high else None,
                        "high_signal_unattributed_works": len(queue), "discovered_affiliation_candidates": len(candidates),
                        "affiliation_labels_requiring_cleanup": sum(row["status"] == "invalid_label" for row in observations),
                        "official_release_recall": None, "recall_status": "not_measured", "gold_release_set_size": None},
            "organization_coverage": sorted(coverage, key=lambda row: (row["effective_tier"], normalized(row["name"]))),
            "tier_changes": sorted(changes, key=lambda row: row["organization_id"]), "t2_candidates": candidates,
            "affiliation_observations": observations, "high_signal_unattributed": queue,
            "source_status": health, "attribution_review_queue": link_issues,
            "policies": {"promotion": "Existing T2 research execution units need a recently checked healthy registered official channel and two distinct G1/G2 relevant works, or one E2+ work, within the dated window.",
                         "no_demotion": "Existing tiers, especially all T0 entities, are retained; stale sources and sparse work coverage remain visible.",
                         "discovery": "Affiliation labels are G0 parent observations only. Candidate names never generate official homepages, leaders or lab memberships.",
                         "high_signal": "Included dated works with curated, strict peer-review, E1–E4, or technical-report evidence; canonical work deduplicated."}}
