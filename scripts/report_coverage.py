"""Pure, denominator-explicit report coverage; absence is not nonexistence.

Only registered technical_report manifestations define the report population.
All relevance strata survive. Source-content checks/author observations are
not independent validation, human semantic review, or full-report coverage.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

try:
    from organization_coverage import attribution_valid, source_health, source_rows, valid_url
    from catalog_rules import publication_verified
    from temporal_evidence import evidence_as_of, public_day, cutoff_day
    from report_text import audit_report_text, report_text_as_of, _bounds
    from versioned_text import text_as_of, validate_snapshot
except ModuleNotFoundError:
    from scripts.organization_coverage import attribution_valid, source_health, source_rows, valid_url
    from scripts.catalog_rules import publication_verified
    from scripts.temporal_evidence import evidence_as_of, public_day, cutoff_day
    from scripts.report_text import audit_report_text, report_text_as_of, _bounds
    from scripts.versioned_text import text_as_of, validate_snapshot

STRATA = ("included", "candidate", "review", "excluded")
EXPERIMENT_FLAGS = {"real_robot", "cross_embodiment", "long_horizon", "deployment"}
ROOT_TYPES = {"company", "research_company", "university", "research_institute"}


def _unique(rows, key):
    out = {}
    for row in rows:
        identifier = row[key]
        if identifier in out:
            raise ValueError("duplicate_report_coverage_identity:" + str(identifier))
        out[identifier] = row
    return out


def _relevance(work):
    value = work.get("relevance", {})
    original = value.get("status") if isinstance(value, dict) else value
    return original if original in {"included", "candidate", "excluded"} else "review"


def _clock(payload, source_status, end, explicit):
    if explicit is not None:
        current = cutoff_day(explicit)
        if current < end:
            raise ValueError("current_observation_cutoff_predates_data_through")
        return current, "explicit_observed_through"
    # Publications/acceptance dates are never clocks: scheduled future works
    # cannot make future report text seem currently observed.
    days = [end]
    registered, _ = source_rows(source_status if source_status is not None else payload.get("source-health", []))
    for row in [*payload.get("source-records", []), *payload.get("report-text-snapshots", []), *registered]:
        for key in ["retrieved_at", "last_checked", "captured_at", "verified_at"]:
            observed = public_day(row.get(key))
            if observed:
                days.append(observed)
    return max(days), "latest_registered_observation_not_live_now"


def _parent_graph(organizations):
    parents, issues = defaultdict(list), []
    for oid, org in organizations.items():
        for relation in org.get("parent_relations", []):
            parent = relation.get("parent_id")
            if parent not in organizations or not valid_url(relation.get("evidence_url")):
                issues.append({"organization_id": oid, "parent_id": parent, "reason": "parent_relation_unverified"})
                continue
            parents[oid].append(relation)
    def visit(oid, path):
        if oid in path:
            raise ValueError("report_coverage_organization_cycle")
        for relation in parents[oid]:
            visit(relation["parent_id"], path | {oid})
    for oid in organizations:
        visit(oid, set())
    return parents, issues


def _relation_available(relation, work):
    # A bounded historical parent relationship must cover the whole uncertain
    # publication interval. Undated registered relations remain explicitly
    # labeled aggregations, not newly inferred historical affiliations.
    if not relation.get("valid_from") and not relation.get("valid_to"):
        return True
    bounds = _bounds(work.get("first_public_date"), work.get("first_public_date_precision", "unknown"))
    if not bounds or bounds[0] is None:
        return False
    start = _bounds(relation.get("valid_from")) if relation.get("valid_from") else None
    end = _bounds(relation.get("valid_to")) if relation.get("valid_to") else None
    return not ((start and bounds[0] < start[0]) or (end and bounds[1] > end[1]))


def _checked_attribution(link, work, organization):
    if not attribution_valid(link, work, organization) or link.get("review_status") in {"draft", "rejected", "invalid"}:
        return False
    if link.get("evidence_grade") == "G2":
        membership = link.get("membership_evidence") or {}
        bounds = _bounds(work.get("first_public_date"), work.get("first_public_date_precision", "unknown"))
        start = _bounds(membership.get("valid_from"))
        end = _bounds(membership.get("valid_to")) if membership.get("valid_to") else None
        return bool(bounds and bounds[0] and start and bounds[0] >= start[0] and (not end or bounds[1] <= end[1]))
    return True


def _health(organizations, registered, current):
    originals, normalized = {}, []
    for raw in registered:
        key = (raw.get("organization_id"), raw.get("url"))
        originals.setdefault(key, []).append(raw)
    selected = {}
    for key, candidates in originals.items():
        eligible = [row for row in candidates if (day := public_day(row.get("last_checked"))) and day <= current]
        raw = max(eligible or candidates, key=lambda value: public_day(value.get("last_checked")) or date.min)
        selected[key] = raw
        observed = public_day(raw.get("last_checked"))
        valid_check = observed is not None and observed <= current
        normalized.append({**raw, "last_checked": observed.isoformat() if valid_check else None,
                           **({"consecutive_failures": 0, "status": "unverified"} if not valid_check else {})})
    rows = source_health(list(organizations.values()), {"registered": normalized}, current)
    for row in rows:
        raw = selected.get((row["organization_id"], row["url"]), {})
        row["last_checked"] = raw.get("last_checked")
        row["parser_status"] = raw.get("parser_status")
        parser = str(raw.get("parser_status") or "").lower()
        partial = parser.startswith("partial") or parser in {"empty_unverified", "blocked", "access_blocked", "unsupported"}
        failed = not row["registration_only"] and bool(row["consecutive_failures"] > 0 or str(raw.get("status") or "").lower() in {"failed", "error", "http_error", "access_blocked", "blocked", "unreachable"})
        row["check_state"] = "failed" if failed else "healthy" if row["verified_healthy"] and not partial else "unknown"
        row["parser_partial"] = partial
    return rows


def _check_counts(rows):
    return {"registered": len(rows), "healthy": sum(row["check_state"] == "healthy" for row in rows),
            "unknown": sum(row["check_state"] == "unknown" for row in rows), "failed": sum(row["check_state"] == "failed" for row in rows),
            "stale": sum(row["stale_warning"] for row in rows), "partial": sum(row["parser_partial"] for row in rows)}


def _text_view(work, reports, abstracts, cutoff):
    report = report_text_as_of(work, reports, cutoff)
    abstract = text_as_of(work, abstracts, cutoff)
    report_ok = report["status"] == "available"
    abstract_ok = abstract["status"] in {"available", "available_unversioned"} and bool(abstract.get("abstract", "").strip())
    status = "available" if report_ok or abstract_ok else "conflicting_snapshots" if "conflicting_snapshots" in {report["status"], abstract["status"]} else "retrospective_only" if "retrospective_only" in {report["status"], abstract["status"]} else "unavailable"
    return {"status": status, "as_of": cutoff, "report_excerpt_available": report_ok, "arxiv_abstract_available": abstract_ok,
            "report_status": report["status"], "arxiv_status": abstract["status"], "full_report_text_covered": False,
            "report_snapshot_ids": report["snapshot_ids"], "arxiv_snapshot_ids": abstract["snapshot_ids"],
            "source_record_ids": sorted({row["source_record_id"] for row in report["snapshots"]} | set(abstract["source_ids"] if abstract_ok else [])),
            "report_available_at": report["available_at"], "report_date_precision": report["date_precision"],
            "arxiv_available_at": abstract["available_at"], "arxiv_date_precision": abstract.get("date_precision", "unknown"),
            "author_observation_ids": sorted({ob["id"] for snapshot in report["snapshots"] for ob in snapshot["observations"]})}


def _counts(reports):
    result = {"report_canonical_count": len(reports), "report_manifestation_count": sum(len(row["manifestations"]) for row in reports)}
    for view in ["as_of", "current"]:
        result.update({
            "text_available_" + view: sum(row["text"][view]["status"] == "available" for row in reports),
            "text_unknown_" + view: sum(row["text"][view]["status"] != "available" for row in reports),
            "report_excerpt_available_" + view: sum(row["text"][view]["report_excerpt_available"] for row in reports),
            "arxiv_abstract_available_" + view: sum(row["text"][view]["arxiv_abstract_available"] for row in reports),
            "experiment_fact_work_count_" + view: sum(row["experiment_facts"][view]["has_fact"] for row in reports),
            "strict_peer_reviewed_" + view: sum(row["peer_review"][view]["strict_peer_reviewed"] for row in reports),
        })
    return result


def build_report_coverage(payload, data_through, source_status=None, *, observed_through=None):
    """Return matrix + item-level gaps. No IO, clock, network, or mutations.

    data_through is the historical evidence cutoff. current_as_of is an
    explicit caller observation bound or latest registered capture/check day,
    never an assertion that the whole internet has been checked through today.
    """
    end = cutoff_day(data_through)
    cutoff = end.isoformat()
    current, clock_basis = _clock(payload, source_status, end, observed_through)
    current_cutoff = current.isoformat()
    works = _unique(payload.get("works", []), "work_id")
    organizations = _unique(payload.get("organizations", []), "organization_id")
    sources = _unique(payload.get("source-records", []), "source_record_id")
    aliases = defaultdict(set)
    for wid, work in works.items():
        for identifier in [wid, *work.get("aliases", [])]:
            aliases[identifier].add(wid)
    for row in payload.get("work-aliases", []):
        if row.get("work_id") in works:
            aliases[row["alias"]].add(row["work_id"])
    def resolve(identifier):
        matches = aliases.get(identifier, set())
        return next(iter(matches)) if len(matches) == 1 else None
    parents, hierarchy_issues = _parent_graph(organizations)
    target = {oid for oid, org in organizations.items() if org.get("tier") in {"T0", "T1"}}
    roots = {oid for oid, org in organizations.items() if not parents[oid] and org.get("entity_type") in ROOT_TYPES}
    target |= roots
    pending = list(target)
    while pending:
        for relation in parents[pending.pop()]:
            if relation["parent_id"] not in target:
                target.add(relation["parent_id"])
                pending.append(relation["parent_id"])
    manifestations, report_versions, orphan_versions = defaultdict(list), defaultdict(list), []
    for version in _unique(payload.get("manifestations", []), "manifestation_id").values():
        wid = resolve(version.get("work_id"))
        if wid:
            canonical_version = {**version, "work_id": wid}
            manifestations[wid].append(canonical_version)
            if version.get("kind") == "technical_report":
                report_versions[wid].append(canonical_version)
        elif version.get("kind") == "technical_report":
            orphan_versions.append({"manifestation_id": version["manifestation_id"], "work_id": version.get("work_id"), "url": version.get("url"), "reason": "report_work_unresolved_or_ambiguous"})
    report_snapshots = payload.get("report-text-snapshots", [])
    audit = audit_report_text(report_snapshots, list(works.values()), payload.get("manifestations", []), sources)
    if audit["status"] != "passed":
        raise ValueError("report_coverage_invalid_report_archive:" + str(audit["errors"][:3]))
    report_texts, abstract_texts, invalid_text = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in report_snapshots:
        report_texts[audit["canonical_work_ids"][row["snapshot_id"]]].append(row)
    for row in payload.get("text-snapshots", []):
        wid = resolve(row.get("work_id"))
        if wid in report_versions:
            failures = validate_snapshot(row, works[wid], sources)
            if failures:
                invalid_text[wid].append({"snapshot_id": row.get("snapshot_id"), "reasons": failures})
            else:
                abstract_texts[wid].append(row)
    attributed, reviews = defaultdict(lambda: defaultdict(list)), []
    for link in payload.get("work-organization-links", []):
        wid, oid = resolve(link.get("work_id")), link.get("organization_id")
        if wid not in report_versions:
            continue
        proof = {key: link.get(key) for key in ["evidence_grade", "evidence_url", "attribution_basis", "verified_at", "membership_evidence"] if link.get(key) is not None}
        proof["source_organization_id"] = oid
        if oid not in organizations or not _checked_attribution(link, works[wid], organizations[oid]):
            reviews.append({"work_id": wid, "title": works[wid]["title"], "organization_id": oid,
                            "relevance": _relevance(works[wid]), "attribution": proof, "reason": "no_reliable_group_attribution",
                            "urls": sorted({v["url"] for v in report_versions[wid] if v.get("url")})})
            continue
        attributed[oid][wid].append({**proof, "scope": "direct_g1_g2", "parent_path": []})
        def ascend(child, path):
            for relation in parents[child]:
                if not _relation_available(relation, works[wid]):
                    continue
                step = {"child_id": child, "parent_id": relation["parent_id"], "evidence_url": relation["evidence_url"],
                        "valid_from": relation.get("valid_from"), "valid_to": relation.get("valid_to")}
                chain = [*path, step]
                attributed[relation["parent_id"]][wid].append({**proof, "scope": "registered_descendant_aggregation", "parent_path": chain})
                ascend(relation["parent_id"], chain)
        ascend(oid, [])
    registered, _ = source_rows(source_status if source_status is not None else payload.get("source-health", []))
    health = _health(organizations, registered, current)
    health_by_org = defaultdict(list)
    for row in health:
        health_by_org[row["organization_id"]].append(row)
    reports = {}
    for wid in sorted(report_versions):
        work = works[wid]
        safe_versions = []
        for version in manifestations[wid]:
            source = sources.get(version.get("source_record_id"), {})
            official = {source["url"]} if source.get("url") and version.get("source_record_id") in work.get("source_record_ids", []) else set()
            safe_versions.append({**version, "peer_reviewed": bool(version.get("peer_reviewed") and publication_verified(version, official))})
        text, experiments, peers = {}, {}, {}
        for name, when in [("as_of", cutoff), ("current", current_cutoff)]:
            text[name] = _text_view(work, report_texts[wid], abstract_texts[wid], when)
            evidence = evidence_as_of(work, safe_versions, when, sources)
            flags = sorted(flag for flag in EXPERIMENT_FLAGS if evidence["evidence_flags"].get(flag))
            experiments[name] = {"has_fact": bool(flags or text[name]["author_observation_ids"]), "flags": flags,
                                 "evidence_ids": sorted({eid for flag in flags for eid in evidence["flag_evidence_ids"].get(flag, [])}),
                                 "author_observation_ids": text[name]["author_observation_ids"], "scope": "source_reported_not_independent_validation"}
            peers[name] = {"strict_peer_reviewed": evidence["strict_peer_reviewed"],
                           "manifestation_ids": sorted(v["manifestation_id"] for v in evidence["peer_reviewed_manifestations"])}
        gaps = []
        for name in ["as_of", "current"]:
            if text[name]["status"] != "available":
                gaps.append({"code": "text_not_available", "view": name, "status": text[name]["status"]})
            if not experiments[name]["has_fact"]:
                gaps.append({"code": "no_dated_source_reported_experiment_fact", "view": name})
        if invalid_text[wid]:
            gaps.append({"code": "arxiv_text_source_validation_failed", "snapshots": invalid_text[wid]})
        if any(public_day(v.get("published_at"), v.get("date_precision", "unknown")) is None for v in report_versions[wid]):
            gaps.append({"code": "report_publication_date_unknown"})
        reports[wid] = {"work_id": wid, "title": work["title"], "relevance": _relevance(work), "original_relevance": work.get("relevance"),
                        "first_public_date": work.get("first_public_date"), "first_public_date_precision": work.get("first_public_date_precision"),
                        "urls": sorted({v["url"] for v in report_versions[wid] if v.get("url")}),
                        "manifestations": [{key: v.get(key) for key in ["manifestation_id", "url", "published_at", "date_precision", "source_record_id", "status"]} for v in sorted(report_versions[wid], key=lambda v: v["manifestation_id"])],
                        "text": text, "experiment_facts": experiments, "peer_review": peers, "gaps": gaps}
    output = []
    for oid in sorted(target):
        org = organizations[oid]
        items = [{**reports[wid], "attribution_evidence": attributed[oid][wid]} for wid in sorted(attributed[oid])]
        checks = health_by_org[oid]
        gaps = ([{"code": "no_registered_reports", "meaning": "not_registered_not_evidence_of_no_reports"}] if not items else [])
        if not checks:
            gaps.append({"code": "no_registered_source_checks"})
        gaps.extend({"code": "source_" + row["check_state"], "source_id": row["source_id"], "url": row["url"], "last_checked": row["last_checked"], "stale": row["stale_warning"]} for row in checks if row["check_state"] != "healthy" or row["stale_warning"])
        output.append({"organization_id": oid, "name": org.get("display_name") or oid, "slug": org.get("slug"), "tier": org.get("tier"),
                       "tracking_unit": bool(org.get("tracking_unit")), "is_root": oid in roots,
                       "status": "registered_reports" if items else "not_registered", "counts": _counts(items),
                       "by_relevance": {state: _counts([item for item in items if item["relevance"] == state]) for state in STRATA},
                       "source_checks": {**_check_counts(checks), "sources": checks}, "reports": items, "gaps": gaps,
                       "attribution_review_queue": [row for row in reviews if row["organization_id"] == oid]})
    attributed_ids = {wid for org_reports in attributed.values() for wid in org_reports}
    visible_ids = {wid for oid in target for wid in attributed[oid]}
    all_reports = list(reports.values())
    return {"schema_version": "1", "data_through": cutoff, "current_as_of": current_cutoff, "current_as_of_basis": clock_basis,
            "scope": {"population": "registered_technical_report_manifestations_all_relevance_states", "global_deduplication": "canonical_work_id",
                      "absence_meaning": "not_registered_not_evidence_of_no_reports", "text_meaning": "dated_short_excerpts_or_arxiv_abstract_not_full_report",
                      "experiment_fact_meaning": "source_reported_not_independent_validation", "parent_meaning": "source_backed_registered_hierarchy_not_inferred_lab_affiliation",
                      "source_check_population": "all_registered_entities_with_own_channels_not_inherited_checks",
                      "official_release_recall": None, "recall_status": "not_measured", "gold_sample_not_population": True},
            "global_summary": {**_counts(all_reports), "organizations": len(output), "reliably_attributed_report_works": len(attributed_ids),
                               "unattributed_report_works": len(set(reports) - attributed_ids), "unresolved_report_manifestations": len(orphan_versions),
                               "matrix_visible_report_works": len(visible_ids), "reliably_attributed_outside_matrix_works": len(attributed_ids - visible_ids),
                               "by_relevance": {state: _counts([row for row in all_reports if row["relevance"] == state]) for state in STRATA}},
            "organizations": output, "unattributed_reports": [reports[wid] for wid in sorted(set(reports) - attributed_ids)],
            "outside_matrix_reports": [reports[wid] for wid in sorted(attributed_ids - visible_ids)],
            "attribution_review_queue": reviews, "unresolved_report_manifestations": orphan_versions,
            "source_checks": {**_check_counts(health), "sources": health}, "organization_hierarchy_issues": hierarchy_issues}
