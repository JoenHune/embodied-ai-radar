#!/usr/bin/env python3
"""Audit v3 catalog invariants, migration reconciliation, and static API."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import calendar
from pathlib import Path

from radar_common import ROOT
from catalog_store import read_table, load_catalog
from catalog_rules import publication_verified, attribution_valid, eligible_month, research_eligible
from jsonschema import Draft202012Validator
from prepare_catalog import audit_source_reconciliation
from audit_versioned_text import audit_versioned_text
from audit_release_recall import audit_release_recall, recall_gate
from versioned_text import text_as_of
from report_text import audit_report_text, report_text_as_of
from report_editorial import report_view_with_provenance
from temporal_evidence import evidence_as_of
from conference_changes import build_conference_changes
from research_status_views import status_work_views, status_changes, editorial_status_dependencies, latest_status_observation
from sqlite_download import local_sqlite_path, verify_archive
from collections import Counter, defaultdict

CATALOG = ROOT / "data" / "catalog"
API = ROOT / "docs" / "public" / "api" / "v1"
SQLITE = local_sqlite_path(ROOT)


def read_jsonl(name: str) -> list[dict]:
    return read_table(CATALOG, name.removesuffix(".jsonl"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def audit_editorial_review_history(saved, packet, editorial_directory):
    from apply_editorial_review import apply_editorial_review, REVIEW_FIELDS
    previous = None
    for receipt in saved.get("post_edit_reviews", []):
        review = {key: receipt.get(key) for key in REVIEW_FIELDS}
        fingerprint = review.get("parent_artifact_digest")
        require(isinstance(fingerprint, str) and len(fingerprint) == 64 and set(fingerprint) <= set("0123456789abcdef"), "Unsafe editorial review parent digest")
        parent_path = editorial_directory / "revisions" / saved["month"] / f"{fingerprint}.json"
        require(parent_path.exists(), "Editorial review parent archive missing")
        parent = json.loads(parent_path.read_text())
        if previous is not None:
            require(parent == previous, "Editorial review history chain is broken")
        previous = apply_editorial_review(parent, review, packet)
    if previous is not None:
        require(previous == saved, "Edited monthly content cannot be reproduced from its parent and review")


def audit_month_report_views(snapshot, month, works, versions_by_work, sources, report_by_work, data_through):
    year, number = map(int, month.split("-"))
    historical_cutoff = min(f"{month}-{calendar.monthrange(year, number)[1]:02d}", data_through)
    require(snapshot.get("evidence_as_of") == historical_cutoff, f"{month} historical evidence cutoff changed")
    require(snapshot.get("retrospective_evidence", {}).get("as_of") == data_through, f"{month} retrospective cutoff changed")
    cohort = [row for row in works if research_eligible(row) and eligible_month(row, data_through) == month]
    def expected(cutoff):
        result = {}
        for work in cohort:
            versions = versions_by_work.get(work["work_id"], [])
            if not any(row.get("kind") == "technical_report" for row in versions):
                continue
            if not any(row.get("kind") == "technical_report" for row in evidence_as_of(work, versions, cutoff, sources)["manifestations"]):
                continue
            result[work["work_id"]] = {"work_id": work["work_id"], "title": work["title"],
                "selection": report_view_with_provenance(report_text_as_of(work, report_by_work.get(work["work_id"], []), cutoff), sources, cutoff)}
        return result
    historical = expected(historical_cutoff)
    retrospective = expected(data_through)
    for actual, wanted, label in [(snapshot.get("report_text_evidence"), historical, "historical"),
                                  (snapshot["retrospective_evidence"].get("report_text_evidence"), retrospective, "retrospective")]:
        require(isinstance(actual, list), f"{month} missing {label} report view")
        require(len({row["work_id"] for row in actual}) == len(actual), f"{month} duplicated report work")
        require({row["work_id"]: row for row in actual} == wanted, f"{month} {label} report view does not match authority/cutoff")
    require(snapshot["coverage"].get("reports_with_dated_text") == sum(row["selection"]["status"] == "available" for row in historical.values()),
            f"{month} dated report coverage cannot be recomputed")


def main() -> None:
    works = read_jsonl("works.jsonl")
    manifestations = read_jsonl("manifestations.jsonl")
    organizations = read_jsonl("organizations.jsonl")
    links = read_jsonl("work-organization-links.jsonl")
    sources = read_jsonl("source-records.jsonl")
    events = read_jsonl("evidence-events.jsonl")
    claims = read_jsonl("editorial-claims.jsonl")
    report = json.loads((API / "migration-report.json").read_text())
    manifest = json.loads((API / "catalog-manifest.json").read_text())
    status_as_of = latest_status_observation(works, sources, manifest["data_through"])
    require(manifest.get("research_status_as_of") == status_as_of, "Status observation clock cannot be recomputed")
    expected_status = status_work_views(works, status_as_of, sources)
    status_by_work = {row["work_id"]: row for row in expected_status}
    require(json.loads((API / "research-status.json").read_text()) == {
        "schema_version": "1", "as_of": status_as_of, "text_data_through": manifest["data_through"], "catalog_hash": manifest["catalog_hash"],
        "works": expected_status, "changes": status_changes(expected_status)}, "Public research-status index cannot be recomputed")

    work_ids = {row["work_id"] for row in works}
    manifestation_ids = {row["manifestation_id"] for row in manifestations}
    source_ids = {row["source_record_id"] for row in sources}
    organization_ids = {row["organization_id"] for row in organizations}
    work_by_id = {row["work_id"]: row for row in works}
    validator = Draft202012Validator(json.loads((ROOT / "config" / "catalog-v3.schema.json").read_text()))
    for row in works:
        validator.validate(row)
    texts = read_jsonl("text-snapshots.jsonl")
    report_texts = read_jsonl("report-text-snapshots.jsonl")
    report_text_audit = audit_report_text(report_texts, works, manifestations, sources)
    require(report_text_audit["status"] == "passed", f"Report text audit failed: {report_text_audit['errors'][:5]}")
    require(manifest.get("report_text_snapshot_count") == len(report_texts), "Report excerpt count diverges")
    require(json.loads((API / "report-text-snapshots.json").read_text()) == report_texts, "Public report excerpts differ from authority")
    reports_by_work = defaultdict(list)
    for row in report_texts:
        reports_by_work[report_text_audit["canonical_work_ids"][row["snapshot_id"]]].append(row)
    report_sources_by_id = {row["source_record_id"]: row for row in sources}
    expected_report_views = {wid: report_view_with_provenance(report_text_as_of(work_by_id[wid], values, manifest["data_through"]), report_sources_by_id, manifest["data_through"])
                             for wid, values in reports_by_work.items()}
    require(json.loads((API / "report-text-index.json").read_text()) == {"catalog_hash": manifest["catalog_hash"], "data_through": manifest["data_through"], "works": expected_report_views}, "Report search views differ from authority or cutoff")
    text_audit = audit_versioned_text(texts, works, sources, json.loads((ROOT / "config/versioned-text.schema.json").read_text()))
    require(text_audit["status"] == "passed", f"Version text audit failed: {text_audit['errors'][:5]}")
    require(manifest.get("text_snapshot_count") == len(texts), "Text snapshot manifest count diverges")
    exported_texts = {}
    for path in sorted((API / "text").glob("*.json")):
        for row in json.loads(path.read_text()):
            require(row["snapshot_id"] not in exported_texts, "Duplicate public text snapshot")
            require(hashlib.sha1(row["snapshot_id"].encode()).hexdigest()[:2] == path.stem, "Incorrect text shard")
            exported_texts[row["snapshot_id"]] = row
    require(exported_texts == {row["snapshot_id"]: row for row in texts}, "Public text differs from version authority")
    gold = read_table(ROOT / "data", "coverage-gold-releases")
    gold_validator = Draft202012Validator(json.loads((ROOT / "config/coverage-gold-release.schema.json").read_text()))
    for row in gold:
        gold_validator.validate(row)
    recall = audit_release_recall(gold, {"works": works, "manifestations": manifestations, "source-records": sources,
                                       "work-aliases": read_jsonl("work-aliases.jsonl"), "reconciliation": read_jsonl("reconciliation.jsonl")},
                                  catalog_hash=manifest["catalog_hash"])
    recall["regression_gate"] = recall_gate(recall, json.loads((ROOT / "config/release-recall-policy.json").read_text()))
    require(recall["regression_gate"]["status"] == "passed", f"Release recall regression failed: {recall['regression_gate']}")
    require(json.loads((API / "release-recall.json").read_text()) == recall, "Published recall cannot be reproduced from authority")
    require(json.loads((API / "coverage-gold-releases.json").read_text()) == gold, "Published recall denominator changed")
    official_urls = {source.get("url") for source in sources if source.get("source_type") in {"official-proceedings", "peer-review", "official_openreview_decision"} and source.get("url")}
    for version in manifestations:
        require(version["peer_reviewed"] == publication_verified(version, official_urls), f"False peer-review evidence: {version['manifestation_id']}")
    for link in links:
        if link.get("evidence_grade") == "G2":
            require(attribution_valid(link, work_by_id.get(link["work_id"])), "G2 lacks date-overlapping official membership")
    require(not any(row["relevance"]["status"] == "included" and row.get("classification_state") == "low_confidence_review" for row in works), "Unreviewed primary classification entered official statistics")
    mappings = read_jsonl("reconciliation.jsonl")
    # Reconciliation is a history, so later revisions can add source rows without
    # deleting old ones. Current input coverage is checked by stable payload IDs.
    source_audit = audit_source_reconciliation(ROOT / "data", sources, mappings, work_ids)
    require(source_audit["status"] == "ok", f"Source rows not reconciled: {source_audit['errors'][:5]}")
    require(source_audit["input_counts"] == report["inputs"], "Migration report does not describe the current raw source corpus")
    for row in mappings:
        require(row.get("source_record_id") in source_ids, "Reconciliation references missing source")
        require(row.get("work_id") in work_ids or row.get("status") in {"event_only", "manual_review"}, "Source row silently dropped")
    require(all(path.stat().st_size < 100 * 1024 * 1024 for path in CATALOG.rglob("*.jsonl")), "Catalog has an unpublishable >100 MiB shard")
    require(len(work_ids) == len(works), "Duplicate work IDs")
    require(len(manifestation_ids) == len(manifestations), "Duplicate manifestation IDs")
    require(len(source_ids) == len(sources), "Duplicate source record IDs")
    require(all(row.get("title") for row in works), "Every work must have a title")
    require(all(row.get("primary_direction") for row in works if row["relevance"]["status"] == "included"), "Included work without primary D")
    require(all(row["primary_direction"] in row["directions"] for row in works if row.get("primary_direction")), "Primary direction missing from multi-label directions")
    require(all(row["work_id"] in work_ids for row in manifestations), "Manifestation without canonical work")
    require(all(row["source_record_id"] in source_ids for row in manifestations), "Manifestation without source record")
    require(all(row["work_id"] in work_ids for row in links), "Organization link without work")
    require(all(row["organization_id"] in organization_ids for row in links), "Organization link without organization")
    require(all(row.get("evidence_grade") in {"G0", "G1", "G2", "G3"} for row in links), "Invalid attribution grade")
    require(all(row.get("work_id") in work_ids for row in events if row.get("event_type") in {"technical_report", "preprint", "paper", "model_release", "dataset_release", "benchmark_release", "repository", "project", "deployment", "company_demo"}), "Research event without canonical work")

    technical_reports = [row for row in manifestations if row["kind"] == "technical_report"]
    technical_report_ids = {row["work_id"] for row in technical_reports}
    require(manifest["counts"]["technical_reports"] == len(technical_report_ids), "Report count must count canonical works")
    require(manifest["counts"]["technical_report_manifestations"] == len(technical_reports), "Report version count diverges")
    require(len(technical_reports) >= 17, "Expected all 17 company technical reports")
    require(all(row["work_id"] in work_ids and row["url"] for row in technical_reports), "Technical report missing work or URL")
    require(report["reconciliation"]["research_updates_without_work_after_migration"] == 0, "Orphan research update remains")
    require(report["reconciliation"]["included_without_primary_direction"] == 0, "Migration report found included work without D")
    require(report["outputs"] == manifest["counts"], "Migration report and public manifest counts diverge")

    named = {
        "org:nvidia-gear",
        "org:physical-intelligence",
        "org:cmu-robotics-institute",
        "org:google-deepmind-robotics",
        "org:tri-robotics",
        "org:rai-institute",
        "org:genesis-ai",
        "org:generalist-ai",
        "org:figure-ai",
        "org:dyna-robotics",
        "org:sunday-robotics",
    }
    public_orgs = json.loads((API / "organizations.json").read_text())
    coverage = json.loads((API / "organization-coverage.json").read_text())
    from report_coverage import build_report_coverage
    expected_report_coverage = build_report_coverage({"works": works, "manifestations": manifestations, "organizations": organizations,
        "source-records": sources, "source-health": read_jsonl("source-health.jsonl"), "work-aliases": read_jsonl("work-aliases.jsonl"),
        "work-organization-links": links, "text-snapshots": texts, "report-text-snapshots": report_texts}, manifest["data_through"])
    expected_report_coverage["catalog_hash"] = manifest["catalog_hash"]
    require(json.loads((API / "report-coverage.json").read_text()) == expected_report_coverage, "Report coverage differs from authority")
    expected_report_orgs = {row["organization_id"]: row for row in expected_report_coverage["organizations"]}
    require(named <= set(expected_report_orgs), "Required core organization omitted from report coverage")
    for org in public_orgs:
        profile = json.loads((API / "organizations" / f"{org['slug']}.json").read_text())
        require(profile.get("report_coverage") == expected_report_orgs.get(org["organization_id"]), "Organization report coverage diverges")
    attribution_rate = coverage["metrics"].get("high_signal_attribution_rate")
    require(attribution_rate is not None and attribution_rate >= .90, "High-signal attribution coverage is below the required 90%")
    tiers = {row["organization_id"]: row.get("tier") for row in public_orgs}
    require(named <= organization_ids, f"Missing required organizations: {sorted(named - organization_ids)}")
    require(all(tiers[org_id] == "T0" for org_id in named), "Required organization not in T0")

    for claim in claims:
        require(all(value in work_ids or any(event["event_id"] == value for event in events) for value in [*(claim.get("supporting_ids") or []), *(claim.get("counterevidence_ids") or [])]), f"Claim {claim['claim_id']} cites unknown evidence")
    require(len(manifest["complete_months"]) == 12, "Exactly 12 complete months are required")
    require(manifest["provisional_month"] not in manifest["complete_months"], "Provisional month must be separate")
    report_versions_by_work = defaultdict(list)
    for version in manifestations:
        report_versions_by_work[version["work_id"]].append(version)
    from editorial_readings import load_reading_index
    from editorial_history import load_editorial_history, editorial_history_reference
    editorial_catalog = {"works": works, "manifestations": manifestations, "evidence-events": events,
                         "source-records": sources, "text-snapshots": texts, "report-text-snapshots": report_texts}
    from source_review_clock import resolve_source_review_clock
    review_clock = resolve_source_review_clock(ROOT, manifest["data_through"])
    require(all(manifest.get(key) == value for key, value in review_clock.items()), "Source review clock manifest mismatch")
    review_as_of = review_clock["source_review_as_of"]
    require(json.loads((API / "source-review-clock.json").read_text()) == {
        "schema_version": "1", "data_through": manifest["data_through"],
        "dataset_version": manifest["dataset_version"], **review_clock}, "Source review clock API mismatch")
    editorial_reading_index = load_reading_index(editorial_catalog, ROOT / "data/hardware-review", review_as_of)
    from source_content_conflicts import load_source_conflicts, conflicts_for_work
    source_conflicts = load_source_conflicts(editorial_catalog, ROOT / "data", review_as_of)
    require(json.loads((API / "source-content-conflicts.json").read_text()) == {
        "schema_version": "1", "as_of": review_as_of, "data_through": manifest["data_through"],
        "source_review_as_of": review_as_of, "source_review_clock_digest": review_clock["source_review_clock_digest"],
        "dataset_version": manifest["dataset_version"],
        "conflicts": source_conflicts}, "Source comparison API differs from audited ledger")
    for month in [*manifest["complete_months"], manifest["provisional_month"]]:
        snapshot_path = API / "monthly" / f"{month}.json"
        require(snapshot_path.exists(), f"Missing monthly API snapshot {month}")
        snapshot = json.loads(snapshot_path.read_text())
        cohort = [work for work in works if research_eligible(work) and eligible_month(work, manifest["data_through"]) == month]
        cohort_ids = {row["work_id"] for row in cohort}
        require(snapshot.get("source_conflicts", []) == [notice for notice in source_conflicts
            if notice["work_id"] in cohort_ids and notice["experimental_use"] == "hold"], f"{month} source comparison holds differ")
        require(snapshot.get("research_status") == status_work_views(cohort, snapshot["evidence_as_of"], sources), f"{month} status backdates later notices")
        require(snapshot.get("research_status_current") == status_work_views(cohort, status_as_of, sources), f"{month} omits notices newer than text coverage")
        require(snapshot["retrospective_evidence"].get("research_status") == status_work_views(cohort, manifest["data_through"], sources), f"{month} later status warnings missing")
        require(snapshot.get("research_status_changes") == status_changes([row for row in expected_status if row["relevance_status"] == "included"], month=month), f"{month} status changes mixed with out-of-scope or undated notices")
        saved_status_editorial_path = ROOT / "data/editorial/monthly" / f"{month}.json"
        saved_for_status = json.loads(saved_status_editorial_path.read_text()) if saved_status_editorial_path.exists() else {}
        require(snapshot.get("editorial_status_dependencies") == editorial_status_dependencies(saved_for_status, expected_status, events), f"{month} affected editorial dependency queue differs")
        from editorial_completeness import assess_editorial_completeness
        require(snapshot.get("editorial_completeness") == assess_editorial_completeness(snapshot), f"{month} editorial completeness cannot be recomputed")
        packet = None
        if saved_for_status.get("status") == "complete":
            from generate_v3_editorial import build_evidence_packet, validated_editorial_overlay, available_reading_references
            packet = build_evidence_packet(snapshot, editorial_catalog, reading_index=editorial_reading_index, source_conflicts=source_conflicts,
                                           source_review_as_of=review_as_of)
            check = validated_editorial_overlay(saved_for_status, packet)
            require((snapshot.get("editorial_status") == "llm_complete") == check["usable"], f"{month} editorial currentness differs from rebuilt evidence")
            editorial_history_reference(ROOT / "data/editorial", saved_for_status)
            if not check["usable"]:
                require(snapshot.get("previous_editorial") == saved_for_status, f"{month} stale complete editorial was hidden or lost")
                require(snapshot.get("editorial_unavailable_reason") == check["reason"], f"{month} old editorial reason differs")
            elif saved_for_status.get("evidence_packet_ref"):
                require(saved_for_status.get("available_reading_references", {}) == available_reading_references(packet), f"{month} reading context provenance differs")
        history = load_editorial_history(ROOT / "data/editorial", month)
        if snapshot.get("previous_editorial"):
            require(snapshot["previous_editorial"] == saved_for_status, f"{month} old editorial changed")
            history.append({"artifact": saved_for_status,
                            "reference": editorial_history_reference(ROOT / "data/editorial", saved_for_status)})
        expected_history = {item["reference"]["artifact_digest"]: item for item in history}
        require(snapshot.get("editorial_history", []) == [expected_history[key]["reference"] for key in sorted(expected_history)], f"{month} editorial history differs")
        for key, item in expected_history.items():
            require(json.loads((API / "editorial-history" / month / f"{key}.json").read_text()) == item["artifact"], f"{month} historical editorial download differs")
        if snapshot.get("editorial_status") == "llm_complete":
            require(packet is not None, f"{month} current editorial has no saved complete artifact")
            saved = json.loads((ROOT / "data/editorial/monthly" / f"{month}.json").read_text())
            require(validated_editorial_overlay(saved, packet)["usable"], "Published monthly editorial is not current or valid")
            require(snapshot.get("editorial") == saved, "Public monthly editorial differs from saved model/review artifact")
            require(snapshot.get("evidence_id_to_work_id") == {card["evidence_id"]: card["work_id"] for card in packet["evidence_cards"] if card["kind"] == "event"}, "Monthly event citations cannot resolve to canonical works")
            audit_editorial_review_history(saved, packet, ROOT / "data/editorial")
            if saved.get("post_edit_reviews"):
                require(json.loads((API / "editorial-reviews" / f"{month}.json").read_text()) == saved["post_edit_reviews"], "Public editorial review record omitted or changed")
        require({row["code"] for row in snapshot["directions"]} == {f"D{i}" for i in range(1, 16)}, f"{month} does not cover D1–D15")
        require({row["code"] for row in snapshot["questions"]} == {f"Q{i}" for i in range(11)}, f"{month} does not cover Q0–Q10")
        expected_count = sum(research_eligible(row) and eligible_month(row, manifest["data_through"]) == month for row in works)
        require(snapshot["coverage"]["included_works"] == expected_count, f"{month} includes uncertain/out-of-period records")
        audit_month_report_views(snapshot, month, works, report_versions_by_work, report_sources_by_id, reports_by_work, manifest["data_through"])
        for event in snapshot["organization_changes"]:
            original = next((row for row in events if row["event_id"] == event["event_id"]), {})
            require(research_eligible(work_by_id.get(original.get("work_id"), {})), f"Out-of-scope event {event['event_id']}")

    texts_by_work = defaultdict(list)
    for text in texts:
        texts_by_work[text["work_id"]].append(text)
    checked_work_ids = set()
    for path in sorted((API / "works").glob("*.json")):
        for detail in json.loads(path.read_text()):
            wid = detail["work_id"]
            require(wid in work_by_id and wid not in checked_work_ids, "Unknown or duplicate public work")
            checked_work_ids.add(wid)
            require(detail.get("source_conflicts", []) == conflicts_for_work(source_conflicts, wid), f"Work source comparison omitted or changed: {wid}")
            require(hashlib.sha1(wid.encode()).hexdigest()[:2] == path.stem, "Work exported to wrong shard")
            for key in ["title", "abstract", "authors", "first_public_date", "first_public_date_precision", "aliases"]:
                require(detail.get(key) == work_by_id[wid].get(key), f"Public work changed authority field {wid}:{key}")
            selected = text_as_of(work_by_id[wid], texts_by_work[wid], manifest["data_through"])
            expected = {key: value for key, value in selected.items() if key not in {"title", "abstract", "authors"}}
            expected["as_of"] = manifest["data_through"]
            require(detail.get("current_text") == expected, f"Incorrect current text selection: {wid}")
            require({row["snapshot_id"] for row in detail.get("text_versions", [])} == {row["snapshot_id"] for row in texts_by_work[wid]}, "Work text archive links omitted")
            require({row["snapshot_id"] for row in detail.get("report_text_versions", [])} == {row["snapshot_id"] for row in reports_by_work[wid]}, "Work report excerpt links omitted")
            require(detail.get("current_report_text") == expected_report_views.get(wid), "Incorrect current report excerpt selection")
            if wid in status_by_work:
                require(detail.get("research_status") == status_by_work[wid], "Work detail omits or changes its status warning")
                require(detail.get("research_status_as_of") == status_as_of, "Work status cutoff is ambiguous")
                if status_by_work[wid]["validation_eligible"] is False:
                    gate = evidence_as_of(work_by_id[wid], detail["manifestations"], status_as_of, sources)
                    require(all(detail.get(key) == gate[key] for key in ("evidence_grade", "evidence_flags", "strict_peer_reviewed")), "Withdrawn results still appear as active validation in work detail")
    require(checked_work_ids == work_ids, "Public work population differs from authority")
    conference_status = {row["edition_id"]: row for row in json.loads((API / "conferences.json").read_text())}
    aliases = read_jsonl("work-aliases.jsonl")
    relations = read_jsonl("work-relations.jsonl")
    for edition in json.loads((ROOT / "config/conference-editions.json").read_text())["editions"]:
        expected = build_conference_changes(edition, works, manifestations, sources, conference_status.get(edition["edition_id"], {}), work_relations=relations, aliases=aliases)
        expected["catalog_hash"] = manifest["catalog_hash"]
        require(json.loads((API / "conference-changes" / f"{edition['edition_id']}.json").read_text()) == expected, "Conference changes cannot be reproduced")
    source_coverage = json.loads((API / "source-coverage.json").read_text())
    coverage_input = ROOT / "data/weekly-v3/source-coverage.json"
    if coverage_input.exists():
        require(source_coverage == json.loads(coverage_input.read_text()), "Public source windows differ from actual collection receipt")
    else:
        require(source_coverage.get("status") == "not_run" and not source_coverage.get("sources") and source_coverage.get("complete_through") is None, "Migration incorrectly claims a real collection run")

    require(manifest.get("downloads", {}).get("sqlite") == "/downloads/radar.sqlite.zip", "ZIP SQLite download missing from manifest")
    require(not any((ROOT / "docs/public/downloads" / name).exists() or (ROOT / "docs/public/downloads" / name).is_symlink()
                    for name in ("radar.sqlite", "radar.sqlite.gz")), "Raw or gzip SQLite must not duplicate the public ZIP download")
    sqlite_download_audit = verify_archive(ROOT / "docs/public/downloads/radar.sqlite.zip",
                                           manifest.get("downloads", {}).get("sqlite_integrity"), raw_path=SQLITE)
    require(SQLITE.exists(), "Private derived SQLite export missing")
    connection = sqlite3.connect(f"file:{SQLITE}?mode=ro", uri=True)
    from sqlite_catalog_fidelity import audit_catalog_fidelity
    from sqlite_editorial_export import audit_editorial_archive, read_editorial_artifacts
    from catalog_store import TABLES
    authority = {"works": works, "manifestations": manifestations, "organizations": organizations,
                 "work-organization-links": links, "source-records": sources, "evidence-events": events,
                 "editorial-claims": claims, "text-snapshots": texts, "report-text-snapshots": report_texts}
    authority.update({table: read_table(CATALOG, table) for table in TABLES if table not in authority})
    from people_radar import load_people_authority, build_people_radar, audit_people_exports
    people_bundle = build_people_radar(authority, load_people_authority(ROOT / "data/people"), manifest["data_through"],
                                       generated_at=manifest["generated_at"], dataset_version=manifest["dataset_version"], research_status_as_of=status_as_of)
    people_audit = audit_people_exports(people_bundle, API / "people", ROOT / "docs/public/downloads/people", connection)
    require(people_audit["status"] == "passed", f"People identity/authorship/API/download audit failed: {people_audit['errors']}")
    require(manifest.get("people") == {"api": "/api/v1/people/index.json", "schema_version": "1",
            "authority_hash": people_bundle["index"]["review_hash"], "counts": people_bundle["index"]["counts"]},
            "People manifest is not reproducible from the four JSONL authority tables")
    require(manifest.get("downloads", {}).get("people") == people_bundle["index"]["downloads"], "People JSONL downloads missing from manifest")
    from ingest_research_status import apply_research_status_additions
    source_lookup = {source["source_record_id"]: source for source in sources}
    status_inputs = []
    for work in works:
        for notice in work.get("research_status_notices", []):
            source = next((source_lookup[sid] for sid in notice.get("source_record_ids", []) if sid in source_lookup
                           and source_lookup[sid].get("url") == notice.get("source_url")
                           and str(source_lookup[sid].get("source_type", "")).endswith("_status_notice")), None)
            require(source is not None, "Status notice lacks its exact official source")
            status_inputs.append({**notice, "source_record": source})
    require(apply_research_status_additions(authority, status_inputs) == authority,
            "Status source, observation, immutable event or field provenance is incomplete")
    catalog_fidelity = audit_catalog_fidelity(connection, authority)
    require(catalog_fidelity["status"] == "passed", f"SQLite authority restoration failed: {catalog_fidelity['errors'][:5]}")
    editorial_fidelity = audit_editorial_archive(connection, read_editorial_artifacts(ROOT / "data/editorial"))
    require(editorial_fidelity["status"] == "passed", f"SQLite editorial restoration failed: {editorial_fidelity['errors']}")
    public_fidelity = json.loads((API / "sqlite-fidelity.json").read_text())
    fidelity_columns = ["table_name", "source_table", "restore_view", "record_count", "digest", "digest_method", "storage_mode"]
    saved_fidelity = [dict(zip(fidelity_columns, row)) for row in connection.execute("SELECT " + ",".join(fidelity_columns) + " FROM catalog_fidelity_manifest")]
    require(public_fidelity["catalog"]["tables"] == saved_fidelity, "Public SQLite restore manifest differs from the downloadable database")
    require(public_fidelity["editorial"]["artifact_count"] == editorial_fidelity["artifact_count"], "Public editorial archive count differs")
    sqlite_work_count = connection.execute("SELECT count(*) FROM works").fetchone()[0]
    require(sqlite_work_count == len(works), "SQLite work count diverges")
    taxonomy_authority = read_jsonl("taxonomy-assignments.jsonl")
    expected_taxonomy = Counter((row["work_id"], row["axis"], row["code"], bool(row["is_primary"]), row.get("confidence"), row.get("classifier_version")) for row in taxonomy_authority)
    sqlite_taxonomy = Counter((wid, axis, code, bool(primary), confidence, version) for wid, axis, code, primary, confidence, version in connection.execute("SELECT work_id,axis,code,is_primary,confidence,classifier_version FROM taxonomy_assignments"))
    require(sqlite_taxonomy == expected_taxonomy, "SQLite taxonomy values differ from the JSONL authority")
    require(connection.execute("SELECT count(*) FROM sqlite_master WHERE name='works_fts_content'").fetchone()[0] == 0, "SQLite duplicated the full original text inside FTS")
    require(connection.execute("SELECT count(*) FROM works_search_content").fetchone()[0] == len(works), "SQLite search content omits canonical works")
    for wid, title, abstract, authors, first_date, work_aliases in connection.execute("SELECT w.work_id,w.title,w.abstract,w.authors_json,w.first_public_date,json_extract(e.payload_json,'$.aliases') FROM works w JOIN work_extra_payloads e USING(work_id)"):
        original = work_by_id[wid]
        require((title, abstract, json.loads(authors), first_date, json.loads(work_aliases) if work_aliases is not None else None)
                == (original["title"], original.get("abstract", ""), original.get("authors") or [], original.get("first_public_date"), original.get("aliases")), f"SQLite changed original identity or text: {wid}")
    sqlite_texts = {row[0]: json.loads(row[1]) for row in connection.execute("SELECT snapshot_id,payload_json FROM text_snapshots")}
    require(sqlite_texts == exported_texts, "SQLite archived texts differ from JSON authority")
    sqlite_reports = {row[0]: json.loads(row[1]) for row in connection.execute("SELECT snapshot_id,payload_json FROM report_text_snapshots")}
    require(sqlite_reports == {row["snapshot_id"]: row for row in report_texts}, "SQLite report excerpts differ from JSON authority")
    require(dict(connection.execute("SELECT snapshot_id,canonical_work_id FROM report_text_snapshots")) == report_text_audit["canonical_work_ids"], "SQLite report canonical bindings diverge")
    require({row[0]: json.loads(row[1]) for row in connection.execute("SELECT organization_id,payload_json FROM report_coverage")} == expected_report_orgs, "SQLite report coverage differs")
    require({row[0]: json.loads(row[1]) for row in connection.execute("SELECT key,payload_json FROM report_coverage_metadata")} == {key: value for key, value in expected_report_coverage.items() if key != "organizations"}, "SQLite report coverage metadata differs")
    sqlite_gold = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM release_recall_gold ORDER BY gold_id")]
    require(sqlite_gold == sorted(gold, key=lambda row: row["gold_id"]), "SQLite recall denominator differs from JSON authority")
    for query in ["VLA", "大小脑", "世界模型", "灵巧操作", "π0", "cross embodiment"]:
        result = connection.execute("SELECT count(*) FROM works_fts WHERE works_fts MATCH ?", (f'"{query}"',)).fetchone()[0]
        require(result > 0, f"SQLite search smoke test failed for {query}")
    connection.close()
    print(json.dumps({
        "status": "ok",
        "works": len(works),
        "manifestations": len(manifestations),
        "technical_reports": len(technical_report_ids),
        "technical_report_manifestations": len(technical_reports),
        "text_snapshots": len(texts),
        "report_text_snapshots": len(report_texts),
        "sqlite_download": sqlite_download_audit,
        "release_recall_regression": recall["regression_gate"],
        "organizations": len(organizations),
        "months": len(manifest["complete_months"]) + 1,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
