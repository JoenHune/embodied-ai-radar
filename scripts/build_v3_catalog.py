#!/usr/bin/env python3
"""Build the v3 canonical catalog, trend snapshots, static API, and SQLite export.

The existing JSON corpora remain immutable migration inputs.  This script is
deterministic for a given --as-of date and is the only writer for v3 derived
data.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import re
import shutil
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from radar_common import ROOT, normalize_doi, normalize_title
from catalog_store import load_catalog, save_catalog, read_table, revision_snapshot, fingerprint, write_if_changed
from sqlite_download import SQLITE_DOWNLOAD_URL, sqlite_export
from catalog_rules import publication_verified, eligible_month, research_eligible, attribution_valid, event_eligible, independent_clusters
from temporal_evidence import evidence_as_of, public_day
from versioned_text import text_as_of
from report_text import report_text_as_of, audit_report_text, register_report_text_additions
from report_editorial import report_editorial_view, report_view_with_provenance, report_quote_text, render_report_measurements
from research_status_views import STATUS_EVENTS, status_work_views, status_changes, editorial_status_dependencies, latest_status_observation

DATA = ROOT / "data"
CATALOG = DATA / "catalog"
PUBLIC_API = ROOT / "docs" / "public" / "api" / "v1"
DOWNLOADS = ROOT / "docs" / "public" / "downloads"
VERSION = "3.1"
RULE_SOURCE_FILES = ("build_v3_catalog.py", "catalog_rules.py", "temporal_evidence.py", "trend_signals.py", "organization_coverage.py", "report_coverage.py", "versioned_text.py", "signal_evidence.py", "generate_v3_editorial.py", "editorial_response_schema.py", "editorial_completeness.py", "audit_release_recall.py", "conference_changes.py", "sqlite_search_export.py", "sqlite_catalog_fidelity.py", "sqlite_editorial_export.py", "report_text.py", "report_editorial.py", "extract_report_archive.py")
RULE_CONFIG_FILES = ("taxonomy-v2.json", "facets-v3.json", "research-agenda.json", "trend-signals.json", "conference-editions.json", "release-recall-policy.json", "editorial-v3.schema.json", "signal-evidence.schema.json", "report-text.schema.json")
RULE_SOURCE_FILES += ("research_status.py", "research_status_views.py", "ingest_research_status.py", "lib/search-status.mjs", "lib/search-records.mjs", "build-pagefind-index.mjs")
RULE_CONFIG_FILES += ("research-status.schema.json",)
RULE_SOURCE_FILES += ("people_radar.py",)
RULE_SOURCE_FILES += ("equipment_radar.py",)
RULE_SOURCE_FILES += ("sqlite_download.py",)
RULE_SOURCE_FILES += ("hardware_census.py", "hardware_coverage_export.py", "fulltext_reading_reviews.py")
RULE_SOURCE_FILES += ("editorial_readings.py", "editorial_history.py")
RULE_SOURCE_FILES += ("source_content_conflicts.py",)
RULE_SOURCE_FILES += ("source_review_clock.py",)
RULE_SOURCE_FILES += ("fulltext_classification_reviews.py",)
RULE_CONFIG_FILES += ("source-content-conflicts.schema.json",)
RULE_SOURCE_FILES += ("pdf_reading_reviews.py", "pdf_coverage_export.py")
RULE_CONFIG_FILES += ("hardware-dictionary.json",)
RULE_SOURCE_FILES += ("../docs/.vitepress/theme/lib/research-card.mjs",)
RULE_SOURCE_FILES += ("../docs/.vitepress/theme/lib/work-status.mjs",)
RULE_SOURCE_FILES += ("../docs/.vitepress/theme/lib/source-conflicts.mjs",)
RULE_CONFIG_FILES += ("people-review.schema.json",)


def read_json(path: Path, fallback: Any) -> Any:
    return json.loads(path.read_text()) if path.exists() else fallback


def localization_source_view(work: dict, selected_text: dict, selected_report: dict | None = None) -> dict | None:
    """An absent historical edition must never fall back to a future abstract."""
    versioned = bool(work.get("identifiers", {}).get("arxiv") or work.get("work_id", "").startswith("arxiv:")
                     or any(str(alias).startswith("arxiv:") for alias in work.get("aliases", [])))
    if not versioned:
        if selected_report is not None or work.get("work_id", "").startswith(("report:", "artifact:")):
            return report_editorial_view(work, selected_report or {})
        return work
    if selected_text.get("status") not in {"available", "available_unversioned"}:
        return None
    return {**work, "title": selected_text["title"], "abstract": selected_text["abstract"],
            "source_record_ids": list(selected_text["source_ids"])}


def write_json(path: Path, value: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=None if compact else 2,
            separators=(",", ":") if compact else None,
        )
        + "\n"
    )


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            count += 1
    return count


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable_hash(*values: Any, length: int = 20) -> str:
    payload = "|".join(clean(value) for value in values)
    return hashlib.sha1(payload.encode()).hexdigest()[:length]


def month_of(value: str | None) -> str | None:
    when = public_day(value)
    return when.strftime("%Y-%m") if when else None


def calendar_end(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{month}-{calendar.monthrange(year, number)[1]:02d}"


CAPABILITY_LABELS = {"real_robot": "真机实验", "cross_embodiment": "跨本体", "long_horizon": "长时序", "deployment": "部署", "open_code": "开放代码", "open_data": "开放数据", "open_model": "开放模型"}


def capability_counts(rows: list[dict]) -> list[dict]:
    return [{"key": key, "label": label,
             "count": sum(bool(w.get("evidence_flags", {}).get(key)) for w in rows),
             "work_ids": [w["work_id"] for w in rows if w.get("evidence_flags", {}).get(key)]}
            for key, label in CAPABILITY_LABELS.items()]


def dated_work_view(work: dict, versions: list[dict], cutoff: str, sources: dict, raw_work: dict | None = None) -> dict:
    evidence = evidence_as_of(raw_work or work, versions, cutoff, sources)
    base = {key: value for key, value in work.items() if key not in {"research_status", "research_status_as_of", "validation_eligible"}}
    return {**base, **{key: evidence[key] for key in ["evidence_grade", "evidence_flags", "strict_peer_reviewed"]},
            **{key: evidence[key] for key in ["research_status", "validation_eligible"] if key in evidence},
            "temporal_evidence": evidence}


def organization_event_views(events: list[dict], links_by_work: dict, works_by_id: dict | None = None) -> list[dict]:
    """Fan out a canonical validation event only for group presentation.

    The canonical event ID remains shared, so global validation statistics are
    counted once while every evidenced collaborator sees the update.
    """
    from copy import deepcopy
    result = []
    status_types = {"withdrawn", "retracted", "corrected", "expression_of_concern", "reinstated"}
    for event in events:
        is_status = bool(event.get("research_status_notice_id") or event.get("event_type") in status_types)
        work = (works_by_id or {}).get(event.get("work_id"))
        if is_status and (work is None or not event_eligible(event, work)):
            continue
        if event.get("organization_id") and not is_status:
            result.append(event)
        elif is_status or event.get("event_type") in {"accepted", "published", "independent_replication"}:
            for org_id, link in links_by_work.get(event.get("work_id"), {}).items():
                if not isinstance(link, dict):
                    continue
                if link.get("evidence_grade") not in {"G1", "G2"} or any(link.get(flag) for flag in ["review_required", "date_review_required", "source_review_required", "date_conflict", "source_conflict"]):
                    continue
                if link.get("review_status") in {"draft", "rejected", "invalid"} or link.get("organization_id", org_id) != org_id:
                    continue
                try:
                    url = link.get("evidence_url")
                    if not isinstance(url, str) or any(char.isspace() for char in url):
                        continue
                    parsed = urlparse(url)
                    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                        continue
                except ValueError:
                    continue
                if work is not None and (not attribution_valid(link, work) or link.get("work_id", work["work_id"]) not in {work["work_id"], *work.get("aliases", [])}):
                    continue
                view = {**event, "organization_id": org_id, "source_event_id": event["event_id"],
                        "attribution_grade": link["evidence_grade"], "attribution_evidence_url": link["evidence_url"],
                        "attribution_basis": "existing_work_attribution_not_current_employer"}
                if is_status:
                    context = "该组已归属工作的状态变化；不表示该组发布声明，也不按作者当前雇主重建归属。"
                    view.update(original_work_attribution=deepcopy(link), statement_publisher_is_organization=False,
                                status_change_context=context, source_event_title=event.get("title"),
                                title="已归属工作状态变化｜" + (event.get("title") or work.get("title") or work["work_id"]),
                                summary_zh=context + " " + (event.get("summary_zh") or ""))
                result.append(view)
    return result


def monthly_organization_change(event: dict, organization: dict) -> dict:
    """Keep identity and date precision through the compact monthly projection."""
    return {
        "event_id": event["event_id"], "work_id": event.get("work_id"),
        "organization_id": event.get("organization_id"),
        "organization_name": organization.get("display_name") or event.get("organization_id"),
        "tier": organization.get("tier", "T2"), "event_type": event["event_type"],
        "title": event["title"], "url": event["url"],
        "published_at": event.get("published_at"), "date_precision": event.get("date_precision", "unknown"),
        "direction_codes": event.get("direction_codes") or [], "summary_zh": event.get("summary_zh") or "",
        **{key: event[key] for key in ["source_event_id", "research_status_notice_id", "scope", "review_status", "source_record_id", "source_record_ids",
                                     "attribution_grade", "attribution_evidence_url", "attribution_basis", "original_work_attribution",
                                     "statement_publisher_is_organization", "status_change_context", "source_event_title"] if key in event},
    }


def add_months(month: str, delta: int) -> str:
    year, number = map(int, month.split("-"))
    index = year * 12 + number - 1 + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def complete_months(as_of: date, count: int = 12) -> list[str]:
    current = f"{as_of.year:04d}-{as_of.month:02d}"
    month_end = calendar.monthrange(as_of.year, as_of.month)[1]
    latest = current if as_of.day == month_end else add_months(current, -1)
    return [add_months(latest, offset) for offset in range(-(count - 1), 1)]


def all_months(first: str, last: str) -> list[str]:
    months = []
    current = first
    while current <= last:
        months.append(current)
        current = add_months(current, 1)
    return months


def direction_maps(taxonomy: dict) -> tuple[dict[str, str], dict[str, str]]:
    topic_to_code = {
        topic: spec["code"] for topic, spec in taxonomy["categories"].items()
    }
    code_to_label = {
        spec["code"]: spec["label"] for spec in taxonomy["categories"].values()
    }
    return topic_to_code, code_to_label


def match_terms(text: str, groups: dict[str, list[str]]) -> list[str]:
    lowered = unicodedata.normalize("NFKC", text).lower()
    return [key for key, terms in groups.items() if any(term.lower() in lowered for term in terms)]


def manifestation_kind(value: str | None) -> str:
    mapping = {
        "repository": "code",
        "model_release": "model",
        "dataset_release": "dataset",
        "benchmark_release": "benchmark",
        "company_demo": "demo",
        "deployment": "deployment",
        "paper": "preprint",
    }
    return mapping.get(value or "", value or "project")


def source_url_for_work(work: dict) -> str:
    for version in work.get("versions") or []:
        if version.get("url"):
            return version["url"]
    if work.get("arxiv_id"):
        return f"https://arxiv.org/abs/{work['arxiv_id']}"
    if work.get("doi"):
        return f"https://doi.org/{normalize_doi(work['doi'])}"
    return ""


def evidence_flags(work: dict, text: str) -> dict[str, bool]:
    legacy = work.get("evidence") or {}
    tags = set(work.get("tags") or [])
    lowered = text.lower()
    return {
        "real_robot": bool(legacy.get("real_robot")),
        "cross_embodiment": bool(legacy.get("cross_embodiment")),
        "long_horizon": bool(legacy.get("long_horizon")),
        "open_code": bool(legacy.get("open_code") or work.get("repositories")),
        "open_data": bool(legacy.get("open_data")),
        "open_model": bool(legacy.get("open_model")),
        "benchmark": bool(legacy.get("benchmark")),
        "deployment": bool(legacy.get("deployment")),
    }


def grade_evidence(*, peer_reviewed: bool, flags: dict[str, bool], technical_report: bool = False, independent: bool = False, organization_count: int = 0) -> str:
    if technical_report and not peer_reviewed and not independent:
        return "E1"
    if peer_reviewed and flags.get("real_robot") and independent:
        return "E4"
    if peer_reviewed or independent:
        return "E3"
    if flags.get("real_robot") or any(flags.get(key) for key in ["open_code", "open_data", "open_model", "benchmark", "deployment"]):
        return "E2"
    return "E0"


def migrate_legacy(args: argparse.Namespace) -> dict:
    taxonomy = read_json(ROOT / "config" / "taxonomy-v2.json", {})
    facets_config = read_json(ROOT / "config" / "facets-v3.json", {})
    questions_config = read_json(ROOT / "config" / "research-agenda.json", {"questions": []})
    organizations_config = read_json(ROOT / "config" / "organizations.json", {"organizations": []})
    works_v2 = read_json(DATA / "works.json", [])
    preprints = read_json(DATA / "preprints.json", [])
    publications = read_json(DATA / "publications.json", [])
    group_updates = read_json(DATA / "group-updates.json", {"updates": []}).get("updates", [])
    work_org_payload = read_json(DATA / "work-organization-links.json", {"links": []})
    work_org_links = list(work_org_payload.get("links", []))
    source_registry = read_json(ROOT / "config" / "source-registry.json", {})
    official_urls = {row.get("official_url") for row in read_json(DATA / "official-proceedings.json", [])}
    official_urls.update(row.get("official_url") for row in read_json(DATA / "peer-review.json", {}).get("records", []))
    as_of_text = args.as_of or source_registry.get("window", {}).get("until") or date.today().isoformat()
    as_of = date.fromisoformat(as_of_text)
    current_month = f"{as_of.year:04d}-{as_of.month:02d}"
    if as_of.day == calendar.monthrange(as_of.year, as_of.month)[1]:
        provisional_month = add_months(current_month, 1)
    else:
        provisional_month = current_month
    full_months = complete_months(as_of, 12)
    topic_to_code, code_to_label = direction_maps(taxonomy)
    question_by_id = {row["id"]: row for row in questions_config.get("questions", [])}

    preprint_by_arxiv = {row.get("arxiv_id"): row for row in preprints if row.get("arxiv_id")}
    preprint_by_title = {normalize_title(row.get("title", "")): row for row in preprints if row.get("title")}
    publication_by_title: dict[str, list[dict]] = defaultdict(list)
    for row in publications:
        publication_by_title[normalize_title(row.get("title", ""))].append(row)

    organizations_by_work: dict[str, set[str]] = defaultdict(set)
    for link in work_org_links:
        if link.get("evidence_grade") in {"G1", "G2"}:
            organizations_by_work[link["work_id"]].add(link["organization_id"])

    manifestations: list[dict] = []
    source_records: list[dict] = []
    provenance: list[dict] = []
    aliases: list[dict] = []
    taxonomy_assignments: list[dict] = []
    evidence_events: list[dict] = []
    canonical: dict[str, dict] = {}
    manifestation_seen: set[str] = set()
    source_seen: set[str] = set()

    def add_source(source_type: str, source_id: str, url: str, published_at: str | None, raw_ref: str) -> str:
        record_id = f"source:{stable_hash(source_type, source_id, url)}"
        if record_id not in source_seen:
            source_seen.add(record_id)
            source_records.append({
                "source_record_id": record_id,
                "source_type": source_type,
                "source_id": source_id,
                "url": url,
                "published_at": published_at,
                "retrieved_at": as_of_text,
                "raw_ref": raw_ref,
            })
        return record_id

    def add_manifestation(work_id: str, kind: str, url: str, published_at: str | None, venue: str | None, year: int | None, status: str | None, source_type: str, peer_reviewed: bool = False) -> tuple[str, str]:
        kind = manifestation_kind(kind)
        manifest_id = f"manifest:{stable_hash(work_id, kind, url, venue, year)}"
        source_id = add_source(source_type, manifest_id, url, published_at, f"manifestation:{manifest_id}")
        if manifest_id not in manifestation_seen:
            manifestation_seen.add(manifest_id)
            manifestations.append({
                "manifestation_id": manifest_id,
                "work_id": work_id,
                "kind": kind,
                "url": url,
                "published_at": published_at,
                "venue": venue,
                "year": year,
                "status": status,
                "peer_reviewed": peer_reviewed,
                "source_record_id": source_id,
            })
        return manifest_id, source_id

    for old in works_v2:
        work_id = old["work_id"]
        preprint = preprint_by_arxiv.get(old.get("arxiv_id")) or preprint_by_title.get(normalize_title(old.get("title", ""))) or {}
        if preprint and preprint.get("arxiv_id") == old.get("arxiv_id"):
            # Refresh factual source fields, while incremental ingestion below
            # protects any values edited since the preceding source snapshot.
            old = {**old, **{field: preprint[field] for field in ["title", "authors", "institutions", "primary_topic", "topics", "tags", "relevance"] if field in preprint}}
        publications_for_work = publication_by_title.get(normalize_title(old.get("title", "")), [])
        abstract = clean(preprint.get("abstract"))
        if not abstract:
            abstract = next((clean(row.get("abstract")) for row in publications_for_work if row.get("abstract")), "")
        text = f"{old.get('title', '')} {abstract}"
        topics = [topic_to_code[key] for key in old.get("topics") or [] if key in topic_to_code]
        primary = topic_to_code.get(old.get("primary_topic"))
        if primary and primary not in topics:
            topics.insert(0, primary)
        relevance = dict(old.get("relevance") or {})
        relevance.setdefault("status", "manual_review")
        relevance.setdefault("score", 0)
        relevance["classifier_version"] = VERSION
        classification_state = "accepted"
        scores = preprint.get("topic_scores") or {}
        positive = sorted((float(value), key) for key, value in scores.items() if value and key in topic_to_code)
        if len(positive) >= 2 and positive[-1][0] - positive[-2][0] <= 1:
            classification_state = "low_confidence_review"
            relevance["previous_status"] = relevance["status"]
            if relevance["status"] == "included":
                relevance["status"] = "manual_review"
        if relevance["status"] == "included" and not primary:
            relevance["status"] = "manual_review"
            classification_state = "missing_primary_review"
        questions = []
        lowered = text.lower()
        for question in questions_config.get("questions", []):
            if any(term.lower() in lowered for term in question.get("query_terms", [])):
                questions.append(question["id"])
        facets = {
            "methods": match_terms(text, facets_config.get("methods", {})),
            "capabilities": match_terms(text, facets_config.get("capabilities", {})),
            "embodiments": match_terms(text, facets_config.get("embodiments", {})),
            "modalities": match_terms(text, facets_config.get("modalities", {})),
        }
        flags = evidence_flags(old, text)
        manifest_ids = []
        source_ids = []
        reviewed = False
        for version in old.get("versions") or []:
            peer = publication_verified(version, official_urls)
            reviewed = reviewed or peer
            manifest_id, source_id = add_manifestation(
                work_id,
                version.get("kind") or "project",
                version.get("url") or source_url_for_work(old),
                version.get("date"),
                version.get("venue"),
                version.get("year"),
                version.get("status"),
                version.get("evidence_source") or "legacy_v2",
                peer,
            )
            manifest_ids.append(manifest_id)
            source_ids.append(source_id)
        if not manifest_ids and source_url_for_work(old):
            manifest_id, source_id = add_manifestation(work_id, "project", source_url_for_work(old), old.get("first_public_date"), None, None, "migrated", "legacy_v2")
            manifest_ids.append(manifest_id)
            source_ids.append(source_id)
        org_count = len(organizations_by_work.get(work_id, set()))
        evidence_grade = grade_evidence(peer_reviewed=reviewed, flags=flags, organization_count=org_count)
        row = {
            "work_id": work_id,
            "title": clean(old.get("title")),
            "title_zh": old.get("title_zh") or None,
            "authors": old.get("authors") or [],
            "institutions": old.get("institutions") or [],
            "abstract": abstract,
            "summary_zh": old.get("contribution_zh") or "",
            "first_public_date": old.get("first_public_date"),
            "first_public_date_precision": old.get("first_public_date_precision") or "unknown",
            "identifiers": {"arxiv": old.get("arxiv_id"), "doi": normalize_doi(old.get("doi"))},
            "relevance": relevance,
            "primary_direction": primary,
            "directions": sorted(set(topics), key=lambda code: int(code[1:])),
            "questions": sorted(set(questions), key=lambda code: int(code[1:])),
            "facets": facets,
            "evidence_flags": flags,
            "evidence_grade": evidence_grade,
            "strict_peer_reviewed": reviewed,
            "curated": bool(old.get("curated")),
            "repositories": old.get("repositories") or [],
            "manifestation_ids": manifest_ids,
            "source_record_ids": sorted(set(source_ids)),
            "aliases": [work_id],
            "classification_state": classification_state,
            "updated_at": as_of_text,
        }
        canonical[work_id] = row
        aliases.append({"alias": work_id, "work_id": work_id, "kind": "legacy_work_id", "valid_from": None, "valid_to": None})
        if old.get("arxiv_id"):
            aliases.append({"alias": f"arxiv:{old['arxiv_id']}", "work_id": work_id, "kind": "arxiv", "valid_from": None, "valid_to": None})
        if old.get("doi"):
            aliases.append({"alias": f"doi:{normalize_doi(old['doi'])}", "work_id": work_id, "kind": "doi", "valid_from": None, "valid_to": None})
        for field in ["title", "authors", "abstract", "first_public_date"]:
            if source_ids:
                provenance.append({"work_id": work_id, "field": field, "source_record_id": source_ids[0], "observed_at": as_of_text})

    # Convert every public research artifact in group updates into a work or a
    # manifestation. Personnel and organizational changes stay as events only.
    research_update_types = {"technical_report", "preprint", "paper", "model_release", "dataset_release", "benchmark_release", "repository", "project", "deployment", "company_demo"}
    from prepare_catalog import OBSERVATION_UPDATE_TYPES
    for update in group_updates:
        update_type = update.get("update_type") or "project"
        work_id = update.get("work_id")
        if not work_id and update_type in research_update_types:
            prefix = "report" if update_type == "technical_report" else "artifact"
            work_id = f"{prefix}:{stable_hash(update.get('update_id') or update.get('url'))}"
        event_id = update.get("update_id") or f"event:{stable_hash(update.get('url'), update.get('published_at'))}"
        evidence_events.append({
            "event_id": event_id,
            **({"source_record_id": f"source:group-updates:{fingerprint(update)[:24]}"} if update_type in OBSERVATION_UPDATE_TYPES else {}),
            "work_id": work_id,
            "organization_id": update.get("organization_id"),
            "event_type": update_type,
            "title": update.get("title"),
            "url": update.get("url"),
            "published_at": update.get("published_at"),
            "attribution_grade": update.get("evidence_grade") or "G0",
            "source_type": update.get("source_type"),
            "direction_codes": update.get("direction_codes") or [],
            "question_codes": update.get("question_codes") or [],
            "summary_zh": update.get("summary_zh") or "",
            "artifact_class": update.get("artifact_class"),
            "evidence_lane": update.get("evidence_lane"),
            "claim_status": update.get("claim_status"),
            "independent_validation": bool(update.get("independent_validation")),
            "report_metrics": update.get("report_metrics") or [],
            "validation_tags": update.get("validation_tags") or [],
            "technical_stack_tags": update.get("technical_stack_tags") or [],
            "open_assets": update.get("open_assets") or [],
            **({key: update.get(key) for key in ["evidence_layer", "research_eligible", "review_status", "observed_at", "observed_at_precision", "date_precision", "limitations_zh", "attribution_relation", "organization_evidence", "date_evidence", "counts_as_new_paper", "counts_as_new_model", "original_research_eligible"]} if update_type in OBSERVATION_UPDATE_TYPES else {}),
        })
        if not work_id or update_type in OBSERVATION_UPDATE_TYPES:
            continue
        if work_id not in canonical:
            flags = {
                "real_robot": "real_robot" in (update.get("validation_tags") or []),
                "cross_embodiment": "cross_embodiment" in (update.get("technical_stack_tags") or []),
                "long_horizon": "long_horizon" in (update.get("technical_stack_tags") or []),
                "open_code": "code" in (update.get("open_assets") or []),
                "open_data": "data" in (update.get("open_assets") or []),
                "open_model": "model" in (update.get("open_assets") or []),
                "benchmark": update_type == "benchmark_release",
                "deployment": update_type == "deployment" or update.get("evidence_lane") == "deployment",
            }
            canonical[work_id] = {
                "work_id": work_id,
                "title": clean(update.get("title")),
                "title_zh": None,
                "authors": [],
                "institutions": [],
                "abstract": "",
                "summary_zh": update.get("summary_zh") or "",
                "first_public_date": update.get("published_at"),
                "first_public_date_precision": update.get("date_precision") or "unknown",
                "identifiers": {"arxiv": None, "doi": None},
                "relevance": {"status": "included" if update.get("direction_codes") else "manual_review", "score": 1, "classifier_version": VERSION, "reasons": [f"official_group_{update_type}"]},
                "primary_direction": (update.get("direction_codes") or [None])[0],
                "directions": update.get("direction_codes") or [],
                "questions": update.get("question_codes") or [],
                "facets": {
                    "methods": [],
                    "capabilities": [],
                    "embodiments": [],
                    "modalities": [],
                },
                "evidence_flags": flags,
                "evidence_grade": grade_evidence(peer_reviewed=bool(update.get("peer_reviewed")), flags=flags, technical_report=update_type in {"technical_report", "company_demo"}, independent=bool(update.get("independent_validation")), organization_count=1),
                "strict_peer_reviewed": bool(update.get("strict_peer_reviewed")),
                "curated": bool(update.get("curated")),
                "repositories": [],
                "manifestation_ids": [],
                "source_record_ids": [],
                "aliases": [event_id],
                "classification_state": "accepted" if update.get("direction_codes") else "missing_primary_review",
                "updated_at": as_of_text,
            }
            aliases.append({"alias": event_id, "work_id": work_id, "kind": "group_update", "valid_from": update.get("published_at"), "valid_to": None})
        kind = manifestation_kind(update_type)
        manifest_id, source_id = add_manifestation(work_id, kind, update.get("url") or "", update.get("published_at"), None, int(update["published_at"][:4]) if update.get("published_at") else None, update.get("publication_status") or "official_group_update", update.get("source_type") or "official_group_update", bool(update.get("peer_reviewed")))
        if manifest_id not in canonical[work_id]["manifestation_ids"]:
            canonical[work_id]["manifestation_ids"].append(manifest_id)
        if source_id not in canonical[work_id]["source_record_ids"]:
            canonical[work_id]["source_record_ids"].append(source_id)
        org_id = update.get("organization_id")
        if org_id:
            organizations_by_work[work_id].add(org_id)
            if not any(link.get("work_id") == work_id and link.get("organization_id") == org_id for link in work_org_links):
                work_org_links.append({
                    "work_id": work_id,
                    "organization_id": org_id,
                    "role": "publisher",
                    "attribution_basis": "official_group_update",
                    "evidence_grade": update.get("evidence_grade") or "G1",
                    "confidence": 1,
                    "evidence_url": update.get("url"),
                    "verified_at": as_of_text,
                })

    return {
        "works": list(canonical.values()), "manifestations": manifestations,
        "source-records": source_records, "field-provenance": provenance,
        "work-aliases": aliases, "work-organization-links": work_org_links,
        "evidence-events": evidence_events, "organizations": organizations_config.get("organizations", []),
        "editorial-claims": [], "work-relations": [], "reconciliation": [],
        "taxonomy-assignments": [],
        "source-health": read_json(DATA / "group-source-status.json", {"sources": []}).get("sources", []),
    }


def export_catalog(payload: dict, metadata: dict, args: argparse.Namespace) -> None:
    from generate_v3_editorial import valid_work_localization, localization_status
    from signal_evidence import load_signal_evidence, overlay_signal_evidence
    from hardware_coverage_export import load_hardware_dictionary
    # Coverage without its configured dictionary is unknown, not a successful
    # all-catalog zero-hit scan. Fail before producing any partial public files.
    hardware_dictionary = load_hardware_dictionary(ROOT / 'config/hardware-dictionary.json')
    taxonomy = read_json(ROOT / "config" / "taxonomy-v2.json", {})
    facets_config = read_json(ROOT / "config" / "facets-v3.json", {})
    questions_config = read_json(ROOT / "config" / "research-agenda.json", {"questions": []})
    as_of_text = args.as_of or metadata["data_through"]
    from source_review_clock import resolve_source_review_clock
    review_clock = resolve_source_review_clock(ROOT, as_of_text)
    review_as_of = review_clock["source_review_as_of"]
    from fulltext_classification_reviews import audit_classification_reviews
    classification_audit = audit_classification_reviews(
        payload, read_table(DATA / "hardware-review", "fulltext-readings"),
        read_table(DATA / "hardware-review", "source-observations"),
        data_through=as_of_text, source_review_as_of=review_as_of,
        conflicts=read_table(DATA / "editorial", "source-content-conflicts"))
    from editorial_readings import load_reading_index
    from editorial_history import load_editorial_history, editorial_history_reference
    editorial_reading_index = load_reading_index(payload, DATA / "hardware-review", review_as_of)
    from source_content_conflicts import load_source_conflicts, conflicts_for_work
    source_conflicts = load_source_conflicts(payload, DATA, review_as_of)
    as_of = date.fromisoformat(as_of_text[:10])
    full_months = complete_months(as_of, 12)
    provisional_month = add_months(full_months[-1], 1)
    topic_to_code, code_to_label = direction_maps(taxonomy)
    question_by_id = {row["id"]: row for row in questions_config.get("questions", [])}
    works = sorted([dict(row) for row in payload["works"]], key=lambda row: ((row.get("first_public_date") or "9999-99-99"), row["work_id"]))
    text_snapshots = payload.get("text-snapshots", [])
    report_snapshots = payload.get("report-text-snapshots", [])
    report_audit = audit_report_text(report_snapshots, payload["works"], payload["manifestations"], payload["source-records"])
    if report_audit["status"] != "passed":
        raise ValueError("Report text audit failed: " + str(report_audit["errors"][:3]))
    report_by_work = defaultdict(list)
    for work in works:
        identifiers = {work["work_id"], *work.get("aliases", [])}
        report_by_work[work["work_id"]] = [row for row in report_snapshots if row["work_id"] in identifiers]
    report_source_map = {row["source_record_id"]: row for row in payload["source-records"]}
    report_views = {work["work_id"]: report_view_with_provenance(report_text_as_of(work, report_by_work[work["work_id"]], as_of_text), report_source_map, as_of_text)
                    for work in works if report_by_work[work["work_id"]]}
    text_by_work = defaultdict(list)
    for snapshot in text_snapshots:
        text_by_work[snapshot["work_id"]].append(snapshot)
    signal_review = load_signal_evidence(DATA / "editorial" / "signal-evidence.jsonl", works=payload["works"], source_records=payload["source-records"])
    works = overlay_signal_evidence(works, signal_review["records"])
    # Persistent editorial text overlays immutable factual records at export.
    localizations = {row["work_id"]: row for row in read_table(DATA / "editorial", "work-localizations")}
    legacy_notes = {row["work_id"]: row for row in read_table(DATA / "editorial" / "legacy", "work-notes") if row.get("work_id")}
    for work in works:
        notices = conflicts_for_work(source_conflicts, work["work_id"])
        if notices:
            work["source_conflicts"] = notices
        note = legacy_notes.get(work["work_id"])
        if note:
            work["summary_zh"] = work.get("summary_zh") or note.get("contribution_zh", "")
            work["limitation_zh"] = note.get("limitation_zh", "")
            work["editorial_source"] = "legacy_editorial"
        localization = localizations.get(work["work_id"])
        if localization:
            text = text_as_of(work, text_by_work[work["work_id"]], as_of_text) if text_by_work[work["work_id"]] else {}
            translation_source = localization_source_view(work, text, report_views.get(work["work_id"]))
            work["localization_status"] = localization_status(localization, translation_source) if translation_source is not None else "historical_text_unavailable"
            if translation_source is not None and valid_work_localization(localization, translation_source):
                work.update({key: localization[key] for key in ["title_zh", "summary_zh", "keywords_zh"] if key in localization})
                work["localization_text_version"] = text.get("version")
                work["editorial_source"] = "source_bound_localization"
            else:
                work["previous_localization"] = localization
    canonical = {row["work_id"]: row for row in works}
    manifestations = payload["manifestations"]
    source_records = payload["source-records"]
    provenance = payload["field-provenance"]
    aliases = payload["work-aliases"]
    work_org_links = payload["work-organization-links"]
    evidence_events = payload["evidence-events"]
    organizations_config = {"organizations": payload["organizations"]}
    source_health = payload.get("source-health", [])
    # Export the authoritative classifications verbatim. Reconstructing from
    # current work labels loses reviewed confidence/version history; absence
    # of an authority table is not permission to invent assignments here.
    taxonomy_assignments = payload.get("taxonomy-assignments", [])
    organizations_by_work = defaultdict(set)
    links_by_work = defaultdict(dict)
    all_links_by_work = defaultdict(list)
    for link in work_org_links:
        all_links_by_work[link["work_id"]].append(link)
        if attribution_valid(link, canonical.get(link["work_id"])):
            organizations_by_work[link["work_id"]].add(link["organization_id"])
            links_by_work[link["work_id"]][link["organization_id"]] = link
    manifestations_by_work: dict[str, list[dict]] = defaultdict(list)
    for manifestation in manifestations:
        manifestations_by_work[manifestation["work_id"]].append(manifestation)
    sources_by_id = {row["source_record_id"]: row for row in source_records}
    # Retain the source-derived facts for all dated projections. Current
    # status gates below must not erase what an earlier month could know.
    dated_basis = {row["work_id"]: dict(row) for row in works}
    status_as_of = latest_status_observation(works, sources_by_id, as_of_text)
    current_status_views = status_work_views(works, status_as_of, sources_by_id)
    current_status_by_id = {row["work_id"]: row for row in current_status_views}
    for work in works:
        if work["work_id"] in current_status_by_id:
            work["research_status"] = current_status_by_id[work["work_id"]]
            work["research_status_as_of"] = status_as_of
            if work["research_status"]["validation_eligible"] is False:
                checked = evidence_as_of(work, [row for row in manifestations if row["work_id"] == work["work_id"]], status_as_of, sources_by_id)
                work.update({key: checked[key] for key in ["evidence_grade", "evidence_flags", "strict_peer_reviewed"]})
                work["validation_eligible"] = False
    for work in works:
        work["manifestation_ids"] = sorted(set(work["manifestation_ids"]))
        work["source_record_ids"] = sorted(set(work["source_record_ids"]))

    named_t0 = {"org:nvidia-gear", "org:physical-intelligence", "org:cmu-robotics-institute", "org:google-deepmind-robotics", "org:tri-robotics", "org:rai-institute", "org:genesis-ai", "org:generalist-ai", "org:figure-ai", "org:dyna-robotics", "org:sunday-robotics"}
    recent_cutoff = add_months(full_months[-1], -11)
    org_recent_counts: Counter[str] = Counter()
    org_high_grade: set[str] = set()
    work_by_id = {row["work_id"]: row for row in works}
    for work_id, org_ids in organizations_by_work.items():
        work = work_by_id.get(work_id)
        if not work or not research_eligible(work) or not recent_cutoff <= (eligible_month(work, as_of_text) or "") <= full_months[-1]:
            continue
        for org_id in org_ids:
            org_recent_counts[org_id] += 1
            if work.get("evidence_grade") in {"E2", "E3", "E4"}:
                org_high_grade.add(org_id)
    organizations = []
    for org in organizations_config.get("organizations", []):
        org_id = org["organization_id"]
        if org.get("tier") == "T0" or org_id in named_t0:
            tier = "T0"
        elif org.get("tier") in {"T1", "T2"}:
            tier = org["tier"]
        elif org.get("tracking_unit"):
            tier = "T0"
        else:
            tier = "T2"
        row = dict(org)
        row["tier"] = tier
        row["recent_work_count"] = org_recent_counts[org_id]
        row["source_health"] = org.get("source_health") or "unknown"
        organizations.append(row)

    clusters = independent_clusters([row for row in works if research_eligible(row)])
    for work in works:
        work["evidence_cluster_id"] = clusters.get(work["work_id"], work["work_id"])

    included = [row for row in works if research_eligible(row) and eligible_month(row, as_of_text)]
    first_month = min([full_months[0], *(month_of(row["first_public_date"]) for row in included)])
    archive_months = all_months(first_month, provisional_month)
    by_month: dict[str, list[dict]] = defaultdict(list)
    for work in included:
        by_month[month_of(work["first_public_date"])].append(work)
    events_by_month: dict[str, list[dict]] = defaultdict(list)
    for event in evidence_events:
        month = month_of(event.get("published_at"))
        if month and event_eligible(event, canonical.get(event.get("work_id"))):
            events_by_month[month].append(event)

    org_by_id = {row["organization_id"]: row for row in organizations}
    current_evidence_views = {w["work_id"]: dated_work_view(w, manifestations_by_work.get(w["work_id"], []), as_of_text, sources_by_id, dated_basis[w["work_id"]]) for w in included}
    snapshots: dict[str, dict] = {}
    editorial_claims: list[dict] = []
    for month in archive_months:
        original_rows = by_month.get(month, [])
        evidence_cutoff = min(calendar_end(month), as_of_text)
        rows = [dated_work_view(w, manifestations_by_work.get(w["work_id"], []), evidence_cutoff, sources_by_id, dated_basis[w["work_id"]]) for w in original_rows]
        retrospective_rows = [current_evidence_views[w["work_id"]] for w in original_rows]
        total = len(rows)
        primary_counts = Counter(row.get("primary_direction") for row in rows if row.get("primary_direction"))
        multi_counts = Counter(code for row in rows for code in row.get("directions") or [])
        question_counts = Counter(code for row in rows for code in row.get("questions") or [])
        output_counts = Counter(kind for row in rows for kind in {version["kind"] for version in row["temporal_evidence"]["manifestations"]})
        evidence_counts = Counter(row.get("evidence_grade") or "E0" for row in rows)
        previous_rows = by_month.get(add_months(month, -1), [])
        previous_counts = Counter(row.get("primary_direction") for row in previous_rows if row.get("primary_direction"))
        directions = []
        for code in sorted(code_to_label, key=lambda item: int(item[1:])):
            count = primary_counts[code]
            previous = previous_counts[code]
            share = count / total if total else 0
            previous_share = previous / len(previous_rows) if previous_rows else 0
            supporting = sorted(
                [row for row in rows if code in (row.get("directions") or [])],
                key=lambda row: (int(row.get("evidence_grade", "E0")[1:]), row.get("strict_peer_reviewed", False), row.get("curated", False)),
                reverse=True,
            )[:5]
            directions.append({
                "code": code,
                "label": code_to_label[code],
                "primary_count": count,
                "multi_label_count": multi_counts[code],
                "share": round(share, 6),
                "previous_share": round(previous_share, 6),
                "share_delta": round(share - previous_share, 6),
                "supporting_work_ids": [row["work_id"] for row in supporting],
            })
        org_changes = []
        for event in organization_event_views(events_by_month.get(month, []), links_by_work, canonical):
            if not event.get("organization_id"):
                # Global acceptance/publication events belong in the evidence
                # lane, not in a fictitious unnamed organization's activity.
                continue
            org = org_by_id.get(event.get("organization_id"), {})
            org_changes.append(monthly_organization_change(event, org))
        high_signal = sorted(
            rows,
            key=lambda row: (int(row.get("evidence_grade", "E0")[1:]), row.get("strict_peer_reviewed", False), row.get("curated", False)),
            reverse=True,
        )[:12]
        top_risers = sorted(directions, key=lambda row: (row["share_delta"], row["primary_count"]), reverse=True)[:3]
        findings = []
        for rank, direction in enumerate(top_risers, 1):
            if not direction["supporting_work_ids"]:
                continue
            finding = {
                "claim_id": f"claim:{month}:direction:{direction['code']}",
                "kind": "direction_change",
                "text": f"{direction['code']} {direction['label']}当月主方向占比为 {direction['share'] * 100:.1f}%，较上月变化 {direction['share_delta'] * 100:+.1f} 个百分点。",
                "supporting_ids": direction["supporting_work_ids"],
                "counterevidence_ids": [],
                "generator": "deterministic_v3",
            }
            findings.append(finding)
            editorial_claims.append({**finding, "month": month})
        snapshots[month] = {
            "version": VERSION,
            "month": month,
            "temporal_basis": "as_of_month",
            "evidence_as_of": evidence_cutoff,
            "work_ids": sorted(w["work_id"] for w in rows),
            "status": "provisional" if month == provisional_month else "complete",
            "data_through": as_of_text,
            "revision": 1,
            "coverage": {
                "included_works": total,
                "strict_peer_reviewed": sum(row.get("strict_peer_reviewed", False) for row in rows),
                "technical_reports": output_counts["technical_report"],
                "works_with_abstract": sum(bool(row.get("abstract")) for row in rows),
                "source_health": "partial" if any(s.get("status") != "healthy" for s in source_health) else "healthy" if source_health else "unknown",
                "classification_pending": sum(eligible_month(w, as_of_text) == month and w.get("classification_state") == "low_confidence_review" for w in works),
                "date_precision_unknown": sum(research_eligible(w) and w.get("first_public_date_precision") not in {"day", "month"} and (w.get("first_public_date") or "")[:4] == month[:4] for w in works),
                "evidence_timing_unverified_works": sum(bool(w["temporal_evidence"]["information_gaps"]) for w in rows),
            },
            "executive_findings": findings,
            "directions": directions,
            "questions": [{"code": code, "title": question_by_id.get(code, {}).get("title", code), "count": question_counts[code]} for code in sorted(question_by_id, key=lambda item: int(item[1:]))],
            "evidence_lanes": dict(sorted(output_counts.items())),
            "evidence_grades": {grade: evidence_counts[grade] for grade in ["E0", "E1", "E2", "E3", "E4"]},
            "organization_changes": sorted(org_changes, key=lambda row: (row["published_at"] or "", row["organization_name"]), reverse=True),
            "high_signal_works": [{
                "work_id": row["work_id"],
                "title": row["title"],
                "summary_zh": row.get("summary_zh") or "",
                "url": source_url_for_work({**row, "versions": manifestations_by_work.get(row["work_id"], [])}) or next((item.get("url") for item in manifestations_by_work.get(row["work_id"], []) if item.get("url")), ""),
                "primary_direction": row.get("primary_direction"),
                "evidence_grade": row.get("evidence_grade"),
                "strict_peer_reviewed": row.get("strict_peer_reviewed"),
                "organization_ids": sorted(organizations_by_work.get(row["work_id"], [])),
            } for row in high_signal],
            "counterevidence": [],
            "watchlist": [direction["code"] for direction in top_risers if direction["share_delta"] > 0],
            "editorial_status": "data_only",
        }
        snapshot = snapshots[month]
        snapshot["retrospective_evidence"] = {
            "as_of": as_of_text, "basis": "same_first_publication_cohort_with_later_dated_validation",
            "strict_peer_reviewed": sum(w["strict_peer_reviewed"] for w in retrospective_rows),
            "evidence_grades": {grade: sum(w["evidence_grade"] == grade for w in retrospective_rows) for grade in ["E0", "E1", "E2", "E3", "E4"]},
            "capability_evidence": capability_counts(retrospective_rows),
        }
        snapshot["research_status"] = status_work_views(original_rows, evidence_cutoff, sources_by_id)
        snapshot["research_status_current"] = status_work_views(original_rows, status_as_of, sources_by_id)
        snapshot["retrospective_evidence"]["research_status"] = status_work_views(original_rows, as_of_text, sources_by_id)
        snapshot["research_status_changes"] = status_changes([row for row in current_status_views if row["relevance_status"] == "included"], month=month)
        monthly_reports = [w for w in rows if any(v.get("kind") == "technical_report" for v in manifestations_by_work[w["work_id"]])]
        def report_evidence_for(cutoff):
            return [{"work_id": w["work_id"], "title": w["title"],
                     "selection": report_view_with_provenance(report_text_as_of(w, report_by_work[w["work_id"]], cutoff), sources_by_id, cutoff)}
                    for w in monthly_reports if any(v.get("kind") == "technical_report" for v in evidence_as_of(w, manifestations_by_work[w["work_id"]], cutoff, sources_by_id)["manifestations"])]
        snapshot["report_text_evidence"] = report_evidence_for(evidence_cutoff)
        snapshot["retrospective_evidence"]["report_text_evidence"] = report_evidence_for(as_of_text)
        snapshot["coverage"]["reports_with_dated_text"] = sum(row["selection"]["status"] == "available" for row in snapshot["report_text_evidence"])
        validation_events = [e for e in events_by_month.get(month, []) if e.get("event_type") in {"accepted", "published", "independent_replication"}]
        snapshot["evidence_events"] = validation_events
        snapshot["capability_evidence"] = capability_counts(rows)
        snapshot["information_gaps"] = ["仅年精度的记录不计入月度趋势。", "组织未归属和未披露实验条件不等于没有研究产出。"]
        if snapshot["coverage"]["evidence_timing_unverified_works"]:
            snapshot["information_gaps"].append("缺少逐项公开日期的实验/开源标记未回填历史证据等级；当月可用证据与今天回看分开显示。")
        if snapshot["coverage"]["classification_pending"]:
            snapshot["information_gaps"].append(f"{snapshot['coverage']['classification_pending']} 项主方向分类待复核，未计入确定方向统计。")
        for direction in snapshot["directions"]:
            direction["summary"] = f"本月确定主方向 {direction['primary_count']} 项，多标签命中 {direction['multi_label_count']} 项；具体技术结论需阅读证据。" if direction["multi_label_count"] else "本月无已确定归类的新增工作。"
            blocked = [w["work_id"] for w in rows if direction["code"] in w.get("directions", []) and w.get("validation_eligible") is False]
            if blocked:
                direction["status_blocked_work_ids"] = sorted(set(blocked))
                if len(set(blocked)) == direction["multi_label_count"]:
                    direction["summary"] = "本月已登记工作在所选时点均有撤回或撤稿通知，保留数量，但不再使用受影响的实验结果形成方向判断。"
        for question in snapshot["questions"]:
            question["supporting_ids"] = [w["work_id"] for w in rows if question["code"] in w.get("questions", [])]
            question["summary"] = f"检索命中 {question['count']} 项，属于问题相关性线索。" if question["count"] else "本月暂无已命中该问题的新增工作。"
            blocked = [w["work_id"] for w in rows if question["code"] in w.get("questions", []) and w.get("validation_eligible") is False]
            if blocked:
                question["status_blocked_work_ids"] = sorted(set(blocked))
                if len(set(blocked)) == question["count"]:
                    question["summary"] = "本月相关工作在所选时点均有撤回或撤稿通知，保留登记数量，不用受影响的结果回答该研究问题。"
        saved_editorial = read_json(DATA / "editorial" / "monthly" / f"{month}.json", {})
        cohort_ids = {row["work_id"] for row in rows}
        month_conflicts = [notice for notice in source_conflicts if notice["work_id"] in cohort_ids and notice["experimental_use"] == "hold"]
        if month_conflicts:
            snapshot["source_conflicts"] = month_conflicts
            snapshot["information_gaps"].append("存在来源内容待核差异；当前编辑暂停受争议版本的实验引用，发现时间不倒写成论文当时已撤回或撤稿。")
        legacy_editorial = read_json(DATA / "editorial" / "legacy" / f"{month}.json", {})
        snapshot["historical_findings"] = legacy_editorial.get("claims", [])
        snapshot["historical_watchlist"] = legacy_editorial.get("historical_watchlist", [])
        history = load_editorial_history(DATA / "editorial", month)
        editorial_usable = False
        if saved_editorial.get("status") == "complete":
            from generate_v3_editorial import build_evidence_packet, validated_editorial_overlay
            saved_history_reference = editorial_history_reference(DATA / "editorial", saved_editorial)
            editorial_packet = build_evidence_packet(snapshot, payload, reading_index=editorial_reading_index, source_conflicts=source_conflicts,
                                                     source_review_as_of=review_as_of)
            editorial_check = validated_editorial_overlay(saved_editorial, editorial_packet)
            editorial_usable = editorial_check["usable"]
            if not editorial_usable:
                snapshot["previous_editorial"] = saved_editorial
                snapshot["editorial_unavailable_reason"] = editorial_check["reason"]
                snapshot["information_gaps"].append("历史摘要对应的证据包已变化或未通过当前校验；保留旧版供查阅，本版仅发布当前数据。")
                history.append({"artifact": saved_editorial,
                                "reference": saved_history_reference})
        # Export old text without making it current, nor writing authority
        # archives during a read-only build. Successful regeneration archives
        # the old artifact permanently before replacing it.
        unique_history = {item["reference"]["artifact_digest"]: item for item in history}
        if unique_history:
            snapshot["editorial_history"] = [unique_history[key]["reference"] for key in sorted(unique_history)]
            for key, item in unique_history.items():
                write_json(PUBLIC_API / "editorial-history" / month / f"{key}.json", item["artifact"], compact=True)
        if editorial_usable:
            snapshot["editorial_status"] = "llm_complete"
            snapshot["editorial"] = saved_editorial
            reviews = saved_editorial.get("post_edit_reviews", [])
            if reviews:
                snapshot["editorial_reviews"] = [{key: review.get(key) for key in ("review_id", "reviewer", "reviewer_kind", "reviewed_at")} for review in reviews]
            rendered = lambda claim: render_report_measurements(claim, editorial_packet["facts"])
            snapshot["evidence_id_to_work_id"] = {card["evidence_id"]: card["work_id"] for card in editorial_packet["evidence_cards"] if card["kind"] == "event"}
            snapshot["organization_findings"] = [rendered(claim) for claim in saved_editorial.get("organization_changes", [])]
            snapshot["executive_findings"] = [{**rendered(claim), "text": rendered(claim)["summary"], "generator": saved_editorial["model"] + (" + content_review" if reviews else "")} for claim in saved_editorial["claims"]]
            for axis in ["direction", "question"]:
                summaries = {row["code"]: row for row in saved_editorial.get(f"{axis}_summaries", [])}
                for entry in snapshot["directions" if axis == "direction" else "questions"]:
                    if entry["code"] in summaries:
                        entry.update(rendered(summaries[entry["code"]]))
            snapshot["counterevidence"] = [rendered(claim) for claim in saved_editorial.get("counterevidence", [])] + [rendered(claim) for claim in saved_editorial["claims"] if claim.get("counterevidence_ids")]
            snapshot["watchlist"] = [rendered(claim) for claim in saved_editorial.get("watchlist", [])]
            snapshot["information_gaps"].extend(saved_editorial.get("limitations", []))
        elif legacy_editorial.get("claims"):
            snapshot["editorial_status"] = "legacy_editorial"
            snapshot["information_gaps"].append("历史研究编辑已恢复；其中引用待复核论文的判断有明确标识，未自动升级为已验证趋势。")
        from editorial_completeness import assess_editorial_completeness
        snapshot["editorial_completeness"] = assess_editorial_completeness(snapshot)
        snapshot["editorial_status_dependencies"] = editorial_status_dependencies(saved_editorial, current_status_views, evidence_events)

    editorial_claims = [{**claim, "month": month, "kind": claim.get("kind", "editorial"), "generator": claim.get("generator", "deterministic_v3")} for month, snapshot in snapshots.items() for claim in snapshot["executive_findings"]]
    trend_months = full_months + ([provisional_month] if provisional_month not in full_months else [])
    direction_series = []
    trend_ledger = []
    cooccurrence: Counter[tuple[str, str]] = Counter()
    trend_rows = [row for month in trend_months for row in by_month.get(month, [])]
    for row in trend_rows:
        codes = sorted(set(row.get("directions") or []), key=lambda code: int(code[1:]))
        for index, left in enumerate(codes):
            for right in codes[index + 1 :]:
                cooccurrence[(left, right)] += 1
    for code in sorted(code_to_label, key=lambda item: int(item[1:])):
        counts = []
        shares = []
        multi = []
        for month in trend_months:
            snapshot = snapshots.get(month, {})
            direction = next((row for row in snapshot.get("directions", []) if row["code"] == code), None)
            counts.append(direction["primary_count"] if direction else 0)
            shares.append(direction["share"] if direction else 0)
            multi.append(direction["multi_label_count"] if direction else 0)
        direction_series.append({"code": code, "label": code_to_label[code], "counts": counts, "shares": shares, "multi_label_counts": multi})
        latest_complete = full_months[-1]
        latest_rows = [dated_work_view(row, manifestations_by_work.get(row["work_id"], []), calendar_end(latest_complete), sources_by_id, dated_basis[row["work_id"]]) for month in full_months[-2:] for row in by_month.get(month, []) if code in (row.get("directions") or [])]
        cluster_count = len(set(row.get("evidence_cluster_id") for row in latest_rows))
        org_count = len(set(org for row in latest_rows for org in organizations_by_work.get(row["work_id"], [])))
        # D codes are broad navigation categories, not falsifiable claims.
        # Concrete lifecycle assessments are exported in trends.signals below.
        lifecycle = "candidate"
        prior_avg = sum(shares[-5:-2]) / 3 if len(shares) >= 5 else 0
        latest_share = shares[-2] if provisional_month not in full_months else shares[-1]
        latest_clusters = {row.get("evidence_cluster_id") for row in by_month.get(latest_complete, []) if code in (row.get("directions") or [])}
        prior_clusters = {row.get("evidence_cluster_id") for month in full_months[-4:-1] for row in by_month.get(month, []) if code in (row.get("directions") or [])}
        if prior_avg and latest_share >= prior_avg * 1.25 and len(latest_clusters - prior_clusters) >= 2:
            momentum = "rising"
        elif len(shares) >= 4 and shares[-2] <= shares[-3] * 0.75 and shares[-3] <= shares[-4] * 0.75 and not any(row.get("evidence_grade") in {"E3", "E4"} for row in latest_rows):
            momentum = "cooling"
        else:
            momentum = "stable"
        max_grade = max((int(row.get("evidence_grade", "E0")[1:]) for row in latest_rows), default=0)
        trend_ledger.append({
            "code": code,
            "label": code_to_label[code],
            "lifecycle": lifecycle,
            "assessment_scope": "direction_summary_only",
            "temporal_basis": "as_of_month",
            "evidence_as_of": calendar_end(latest_complete),
            "momentum": momentum,
            "evidence_grade": f"E{max_grade}",
            "rolling_two_month_works": len(latest_rows),
            "independent_clusters": cluster_count,
            "organization_count": org_count,
            "supporting_work_ids": [row["work_id"] for row in sorted(latest_rows, key=lambda row: int(row.get("evidence_grade", "E0")[1:]), reverse=True)[:6]],
        })

    org_api = []
    updates_by_org: dict[str, list[dict]] = defaultdict(list)
    for event in organization_event_views(evidence_events, links_by_work, canonical):
        if event.get("organization_id") and event_eligible(event, work_by_id.get(event.get("work_id"))):
            updates_by_org[event["organization_id"]].append(event)
    for org in organizations:
        org_id = org["organization_id"]
        all_attributed = sorted(work_id for work_id, ids in organizations_by_work.items() if org_id in ids)
        org_work_ids = [wid for wid in all_attributed if work_by_id[wid]["relevance"]["status"] != "excluded"]
        formal_work_ids = [wid for wid in org_work_ids if research_eligible(work_by_id[wid])]
        review_work_ids = [wid for wid in org_work_ids if not research_eligible(work_by_id[wid])]
        recent_work_ids = [work_id for work_id in formal_work_ids if full_months[0] <= (eligible_month(work_by_id[work_id], as_of_text) or "") <= provisional_month]
        direction_counts = Counter(code for work_id in recent_work_ids for code in work_by_id.get(work_id, {}).get("directions") or [])
        org_api.append({
            "organization_id": org_id,
            "slug": org.get("slug"),
            "name": org.get("display_name"),
            "short_name": org.get("short_name"),
            "entity_type": org.get("entity_type"),
            "tracking_category": org.get("tracking_category"),
            "startup_frontier": bool(org.get("startup_frontier")),
            "tier": org.get("tier"),
            "region": org.get("region"),
            "country": org.get("country"),
            "source_health": org.get("source_health"),
            "last_checked": org.get("last_checked"),
            "last_changed": max([event.get("published_at") or "" for event in updates_by_org.get(org_id, [])] + [org.get("last_changed") or ""]) or None,
            "leaders": org.get("leaders", []),
            "parent_relations": org.get("parent_relations", []),
            "information_gaps": org.get("information_gaps", []),
            "project_series": org.get("project_series", []),
            "collaborators": [{"organization_id": collaborator, "work_ids": sorted(wid for wid in recent_work_ids if collaborator in organizations_by_work[wid])} for collaborator in sorted({other for wid in recent_work_ids for other in organizations_by_work[wid] if other != org_id})],
            "official_urls": org.get("official_urls") or {},
            "summary_zh": org.get("summary_zh") or "",
            "declared_direction_codes": org.get("declared_direction_codes") or [],
            "actual_direction_counts": dict(direction_counts),
            "recent_work_count": len(recent_work_ids),
            "work_ids": org_work_ids,
            "research_work_ids": formal_work_ids,
            "review_work_ids": review_work_ids,
            "recent_work_ids": recent_work_ids,
            "updates": sorted(updates_by_org.get(org_id, []), key=lambda row: row.get("published_at") or "", reverse=True),
            "attributions": [link for link in work_org_links if link["organization_id"] == org_id],
        })

    trends = {
        "version": VERSION,
        "data_through": as_of_text,
        "complete_months": full_months,
        "provisional_month": provisional_month,
        "months": trend_months,
        "directions": direction_series,
        "ledger": trend_ledger,
        "cooccurrence": [{"source": left, "target": right, "count": count} for (left, right), count in cooccurrence.most_common()],
        "organization_changes": snapshots.get(full_months[-1], {}).get("organization_changes", []) + snapshots.get(provisional_month, {}).get("organization_changes", []),
    }
    from trend_signals import assess_signal
    signal_specs = read_json(ROOT / "config" / "trend-signals.json", {"signals": []})["signals"]
    trends["temporal_basis"] = "as_of_month"
    trends["evidence_as_of"] = calendar_end(full_months[-1])
    trends["signals"] = [assess_signal(spec, list(dated_basis.values()), full_months, organizations_by_work, manifestations_by_work, source_records=sources_by_id) for spec in signal_specs]
    trends["validation_events"] = [event for event in evidence_events if event.get("event_type") in {"accepted", "published", "independent_replication"} and event.get("research_eligible")]

    counts = {
        "works": len(works),
        "included": sum(row["relevance"]["status"] == "included" for row in works),
        "candidate": sum(row["relevance"]["status"] == "candidate" for row in works),
        "manual_review": sum(row["relevance"]["status"] == "manual_review" for row in works),
        "excluded": sum(row["relevance"]["status"] == "excluded" for row in works),
        "manifestations": len(manifestations),
        "technical_reports": len({row["work_id"] for row in manifestations if row["kind"] == "technical_report"}),
        "technical_report_manifestations": sum(row["kind"] == "technical_report" for row in manifestations),
        "strict_peer_reviewed": sum(row.get("strict_peer_reviewed", False) for row in works),
        "organizations": len(organizations),
        "t0_organizations": sum(row.get("tier") == "T0" for row in organizations),
        "t1_organizations": sum(row.get("tier") == "T1" for row in organizations),
        "events": len(evidence_events),
    }

    alias_rows = [json.loads(value) for value in sorted({(row["alias"], row["work_id"]): json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in aliases}.values())]

    migration_report = {
        "version": VERSION,
        "generated_at": as_of_text,
        "inputs": metadata.get("input_counts", {}),
        "outputs": counts,
        "reconciliation": {
            "v2_work_delta": len(works) - metadata.get("input_counts", {}).get("works", 0),
            "research_updates_without_work_after_migration": sum(event.get("event_type") == "technical_report" and not event.get("work_id") for event in evidence_events),
            "included_without_primary_direction": sum(row["relevance"]["status"] == "included" and not row.get("primary_direction") for row in works),
            "links_without_work": sum(link.get("work_id") not in work_by_id and link.get("work_id") not in canonical for link in work_org_links),
        },
        "notes": [
            "Existing source corpora are retained as immutable migration inputs.",
            "Technical reports and other official research artifacts receive stable work IDs.",
            "Current-employer inference is never used to rewrite historical attribution.",
        ],
    }
    migration_report["source_row_reconciliation"] = dict(Counter(row["status"] for row in payload.get("reconciliation", [])))
    if args.migrate or args.ingest:
        write_json(CATALOG / "migration-report.json", migration_report)
    (PUBLIC_API / "monthly").mkdir(parents=True, exist_ok=True)
    (PUBLIC_API / "organizations").mkdir(parents=True, exist_ok=True)
    (PUBLIC_API / "works").mkdir(parents=True, exist_ok=True)
    for month, snapshot in snapshots.items():
        window = [add_months(month, offset) for offset in range(-11, 1)]
        snapshot["trend_ledger"] = [assess_signal(spec, list(dated_basis.values()), window, organizations_by_work, manifestations_by_work, source_records=sources_by_id) for spec in signal_specs] if snapshot["status"] == "complete" else []
        snapshot["retrospective_evidence"]["trend_ledger"] = [assess_signal(spec, list(dated_basis.values()), window, organizations_by_work, manifestations_by_work, evidence_cutoff=as_of_text, source_records=sources_by_id) for spec in signal_specs] if snapshot["status"] == "complete" else []
        snapshot = revision_snapshot(DATA / "snapshots" / "monthly", month, snapshot, persist=args.migrate or args.ingest)
        for revision in snapshot["revisions"]:
            archived_path = DATA / "snapshots" / "monthly" / month / f"r{revision['revision']}.json"
            if archived_path.exists():
                archived = read_json(archived_path, {})
                # Preserve old authority snapshots verbatim; normalize a known
                # prototype revision-header issue only in the derived view.
                if archived.get("revision") != revision["revision"]:
                    archived["original_snapshot_revision"] = archived.get("revision")
                archived["revision"] = revision["revision"]
                revision["url"] = f"/api/v1/monthly/history/{month}/r{revision['revision']}.json"
                write_json(PUBLIC_API / "monthly" / "history" / month / f"r{revision['revision']}.json", archived, compact=True)
        write_json(PUBLIC_API / "monthly" / f"{month}.json", snapshot, compact=True)
        if snapshot.get("editorial_reviews"):
            write_json(PUBLIC_API / "editorial-reviews" / f"{month}.json", snapshot["editorial"]["post_edit_reviews"], compact=True)
    write_json(PUBLIC_API / "trends.json", trends, compact=True)
    write_json(PUBLIC_API / "organizations.json", org_api, compact=True)
    write_json(PUBLIC_API / "events.json", evidence_events, compact=True)
    write_json(PUBLIC_API / "evidence-events.json", evidence_events, compact=True)
    conference_statuses = [read_json(p, {}) for p in sorted((DATA / "conferences").glob("*/source-status.json"))]
    write_json(PUBLIC_API / "conferences.json", conference_statuses, compact=True)
    conference_editions = read_json(ROOT / "config" / "conference-editions.json", {"editions": []})
    write_json(PUBLIC_API / "conference-editions.json", conference_editions, compact=True)
    from conference_changes import build_conference_changes
    for edition in conference_editions["editions"]:
        conference_status = next((row for row in conference_statuses if row.get("edition_id") == edition["edition_id"]), {})
        conference_delta = build_conference_changes(edition, works, manifestations, source_records, conference_status,
                                                    work_relations=payload.get("work-relations", []), aliases=aliases)
        conference_delta["catalog_hash"] = metadata["catalog_hash"]
        write_json(PUBLIC_API / "conference-changes" / f"{edition['edition_id']}.json", conference_delta, compact=True)
    write_json(PUBLIC_API / "source-health.json", source_health, compact=True)
    write_json(PUBLIC_API / "work-organization-links.json", work_org_links, compact=True)
    write_json(PUBLIC_API / "signal-evidence.json", signal_review, compact=True)
    write_json(PUBLIC_API / "report-text-snapshots.json", report_snapshots, compact=True)
    write_json(PUBLIC_API / "report-text-index.json", {"catalog_hash": metadata["catalog_hash"], "data_through": as_of_text, "works": report_views}, compact=True)
    text_shards = defaultdict(list)
    for snapshot in text_snapshots:
        shard = hashlib.sha1(snapshot["snapshot_id"].encode()).hexdigest()[:2]
        text_shards[shard].append(snapshot)
    for shard, values in text_shards.items():
        write_json(PUBLIC_API / "text" / f"{shard}.json", values, compact=True)
    from organization_coverage import build_organization_coverage
    organization_coverage = build_organization_coverage(works, organizations, work_org_links, {"registered": source_health, "records": source_records}, as_of_text)
    collection_coverage = read_json(DATA / "weekly-v3/source-coverage.json", {"schema_version": "1", "status": "not_run", "requested_source_cutoff": None,
        "available_data_through": None, "registered_scope_complete": None, "primary_corpora_complete": None, "complete_through": None,
        "primary_corpora_complete_through": None, "incomplete_sources": [], "sources": [], "scope_note": "尚无真实周更采集运行记录；现有迁移数据不代表周更已启用。"})
    organization_coverage["collection_coverage"] = collection_coverage
    write_json(PUBLIC_API / "source-coverage.json", collection_coverage, compact=True)
    gold_records = read_table(DATA, "coverage-gold-releases")
    release_recall = None
    if gold_records:
        from audit_release_recall import audit_release_recall, recall_gate
        release_recall = audit_release_recall(gold_records, payload, catalog_hash=metadata["catalog_hash"])
        release_recall["regression_gate"] = recall_gate(release_recall, read_json(ROOT / "config/release-recall-policy.json", {}))
        write_json(PUBLIC_API / "release-recall.json", release_recall, compact=True)
        write_json(PUBLIC_API / "coverage-gold-releases.json", gold_records, compact=True)
        organization_coverage["recall_sample"] = {key: release_recall[key] for key in ["scope", "gold_hash", "sampled_organizations", "overall", "research_artifacts", "observational_releases", "regression_gate"]}
        organization_coverage["recall_sample"]["total_core_groups"] = sum(org.get("tier") == "T0" for org in organizations)
        organization_coverage["recall_sample"]["pending_classification"] = [row for row in release_recall["results"] if row.get("catalog_relevance") in {"candidate", "manual_review"}]
    write_json(PUBLIC_API / "organization-coverage.json", organization_coverage, compact=True)
    from report_coverage import build_report_coverage
    report_coverage = build_report_coverage(payload, as_of_text)
    report_coverage["catalog_hash"] = metadata["catalog_hash"]
    write_json(PUBLIC_API / "report-coverage.json", report_coverage, compact=True)
    report_coverage_by_org = {row["organization_id"]: row for row in report_coverage["organizations"]}
    write_json(PUBLIC_API / "aliases.json", {row["alias"]: row["work_id"] for row in alias_rows}, compact=True)
    write_json(PUBLIC_API / "research-status.json", {"schema_version": "1", "as_of": status_as_of, "text_data_through": as_of_text,
                "catalog_hash": metadata["catalog_hash"], "works": current_status_views,
                "changes": status_changes(current_status_views)}, compact=True)
    for org in org_api:
        org["report_coverage"] = report_coverage_by_org.get(org["organization_id"])
        write_json(PUBLIC_API / "organizations" / f"{org['slug']}.json", org, compact=True)
    shards: dict[str, list[dict]] = defaultdict(list)
    work_events = defaultdict(list)
    classification_history = defaultdict(list)
    for source in source_records:
        if source.get("source_type") == "ai_fulltext_classification_review":
            classification_history[source["classification_review"]["work_id"]].append({
                key: source[key] for key in ("source_record_id", "url", "reviewed_at", "assurance", "classification_review")})
    for event in evidence_events:
        if event.get("work_id"):
            work_events[event["work_id"]].append(event)
    for work in works:
        shard = hashlib.sha1(work["work_id"].encode()).hexdigest()[:2]
        detail = {key: value for key, value in work.items() if not key.startswith("_")}
        detail["manifestations"] = manifestations_by_work.get(work["work_id"], [])
        detail["organizations"] = sorted(organizations_by_work.get(work["work_id"], []))
        detail["organization_details"] = [{"organization_id": org_id, "name": org_by_id.get(org_id, {}).get("display_name", org_id), "slug": org_by_id.get(org_id, {}).get("slug")} for org_id in detail["organizations"]]
        detail["organization_attributions"] = [{**link, "name": org_by_id.get(link["organization_id"], {}).get("display_name", link["organization_id"])} for link in all_links_by_work[work["work_id"]]]
        detail["evidence_events"] = work_events.get(work["work_id"], [])
        if work["work_id"] in classification_history:
            detail["classification_reviews"] = sorted(classification_history[work["work_id"]],
                                                       key=lambda row: row["reviewed_at"])
        detail["text_versions"] = [{key: row[key] for key in ["snapshot_id", "source_record_id", "version", "title", "authors", "available_at", "date_precision", "source_url"]} for row in text_by_work[work["work_id"]]]
        selected_text = text_as_of(work, text_by_work[work["work_id"]], as_of_text)
        detail["current_text"] = {key: value for key, value in selected_text.items() if key not in {"title", "abstract", "authors"}}
        detail["current_text"]["as_of"] = as_of_text
        detail["report_text_versions"] = [{key: row[key] for key in ["snapshot_id", "source_record_id", "available_at", "date_precision", "source_url", "report_url"]} for row in report_by_work[work["work_id"]]]
        if work["work_id"] in report_views:
            detail["current_report_text"] = report_views[work["work_id"]]
        shards[shard].append(detail)
    for shard in [f"{value:02x}" for value in range(256)]:
        write_json(PUBLIC_API / "works" / f"{shard}.json", shards.get(shard, []), compact=True)
    recent = sorted(
        [row for row in works if row["relevance"]["status"] == "included"],
        key=lambda row: (row.get("first_public_date") or "", int(row.get("evidence_grade", "E0")[1:])),
        reverse=True,
    )[:60]
    write_json(PUBLIC_API / "recent.json", [{
        "work_id": row["work_id"],
        "title": row["title"],
        "summary_zh": row.get("summary_zh") or "",
        "date": row.get("first_public_date"),
        "primary_direction": row.get("primary_direction"),
        "evidence_grade": row.get("evidence_grade"),
        "strict_peer_reviewed": row.get("strict_peer_reviewed"),
        "shard": hashlib.sha1(row["work_id"].encode()).hexdigest()[:2],
    } for row in recent], compact=True)
    filter_options = {
        "directions": [{"value": code, "label": f"{code} · {label}"} for code, label in sorted(code_to_label.items(), key=lambda item: int(item[0][1:]))],
        "questions": [{"value": code, "label": f"{code} · {question_by_id[code].get('title', code)}"} for code in sorted(question_by_id, key=lambda item: int(item[1:]))],
        "organizations": [{"value": row["organization_id"], "label": row["name"], "tier": row["tier"]} for row in org_api if row["tier"] in {"T0", "T1"}],
        "output_types": sorted(set(row["kind"] for row in manifestations)),
        "evidence": ["E0", "E1", "E2", "E3", "E4"],
        "relevance": ["included", "candidate", "manual_review", "excluded"],
    }
    manifest = {
        **review_clock,
        "version": VERSION,
        "generated_at": metadata.get("ingested_at"),
        "data_through": as_of_text,
        "catalog_hash": metadata["catalog_hash"],
        "counts": counts,
        "classification_reviews": classification_audit,
        "complete_months": full_months,
        "provisional_month": provisional_month,
        "available_months": archive_months,
        "work_shards": 256,
        "text_snapshot_count": len(text_snapshots),
        "report_text_snapshot_count": len(report_snapshots),
        "text_shards": sorted(text_shards),
        "filter_options": filter_options,
        "downloads": {"sqlite": SQLITE_DOWNLOAD_URL, "migration_report": "/api/v1/migration-report.json"},
    }
    editorial_paths = sorted(p for p in (DATA / "editorial").rglob("*") if p.is_file() and p.suffix in {".json", ".jsonl"} and not p.name.endswith(".attempt.json") and p.name != "status.json")
    manifest["editorial_hash"] = fingerprint({str(p.relative_to(DATA / "editorial")): hashlib.sha256(p.read_bytes()).hexdigest() for p in editorial_paths})
    manifest["research_status_as_of"] = status_as_of
    rule_paths = [ROOT / "scripts" / name for name in RULE_SOURCE_FILES]
    rule_paths.extend(ROOT / "config" / name for name in RULE_CONFIG_FILES)
    clock_config = ROOT / "config/source-review-clock.json"
    if clock_config.exists():
        rule_paths.append(clock_config)
    manifest["rules_hash"] = fingerprint({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in rule_paths})
    # Source-first gold and conference access states are not canonical works,
    # but their public views must invalidate the shared website/search revision.
    from people_radar import (TABLES as PEOPLE_TABLES, load_people_authority, build_people_radar,
                              export_people_files, build_people_sqlite)
    from equipment_radar import (TABLES as EQUIPMENT_TABLES, load_equipment_authority, build_equipment_bundle,
                                 export_equipment, equipment_sqlite)
    from hardware_coverage_export import build_coverage, export_coverage, coverage_sqlite
    from pdf_coverage_export import build_pdf_coverage, export_pdf_coverage, pdf_coverage_sqlite, attach_pdf_coverage
    supplemental_paths = [DATA / "coverage-gold-releases.jsonl", DATA / "weekly-v3/source-coverage.json", *sorted((DATA / "conferences").glob("*/source-status.json")),
                          *[DATA / "people" / f"{table}.jsonl" for table in PEOPLE_TABLES],
                          *[DATA / "equipment" / f"{table}.jsonl" for table in EQUIPMENT_TABLES],
                          *[DATA / "hardware-review" / f"{table}.jsonl" for table in ('source-observations', 'source-scans', 'section-reviews', 'fulltext-readings', 'pdf-source-observations', 'pdf-readings')]]
    manifest["supplemental_hash"] = fingerprint({str(p.relative_to(DATA)): hashlib.sha256(p.read_bytes()).hexdigest() for p in supplemental_paths if p.exists()})
    manifest["dataset_version"] = fingerprint({key: manifest[key] for key in ["catalog_hash", "editorial_hash", "rules_hash", "supplemental_hash", "data_through",
                                                                            "source_review_as_of", "source_review_clock_digest"]})
    write_json(PUBLIC_API / "source-review-clock.json", {"schema_version": "1", "data_through": as_of_text,
               "dataset_version": manifest["dataset_version"], **review_clock}, compact=True)
    write_json(PUBLIC_API / "source-content-conflicts.json", {"schema_version": "1", "as_of": review_as_of,
               "data_through": as_of_text, "source_review_as_of": review_as_of,
               "source_review_clock_digest": review_clock["source_review_clock_digest"],
               "dataset_version": manifest["dataset_version"], "conflicts": source_conflicts}, compact=True)
    # Person staging is never read here: the four JSONL tables are the only
    # person authority, alongside (not replacing) canonical work facts.
    people_bundle = build_people_radar(payload, load_people_authority(DATA / "people"), as_of_text,
                                       generated_at=metadata.get("ingested_at"), dataset_version=manifest["dataset_version"], research_status_as_of=status_as_of)
    export_people_files(people_bundle, PUBLIC_API / "people", DOWNLOADS / "people")
    manifest["people"] = {"api": "/api/v1/people/index.json", "schema_version": "1",
                          "authority_hash": people_bundle["index"]["review_hash"], "counts": people_bundle["index"]["counts"]}
    manifest["downloads"]["people"] = people_bundle["index"]["downloads"]
    equipment_authority = load_equipment_authority(DATA / "equipment")
    equipment_bundle = build_equipment_bundle(payload, equipment_authority, manifest)
    export_equipment(equipment_bundle, PUBLIC_API / "equipment", DOWNLOADS / "equipment")
    hardware_coverage = build_coverage(payload, equipment_authority, hardware_dictionary,
        read_table(DATA / 'hardware-review', 'source-scans'), read_table(DATA / 'hardware-review', 'source-observations'), manifest,
        reading_reviews=read_table(DATA / 'hardware-review', 'fulltext-readings'))
    pdf_coverage = build_pdf_coverage(payload, read_table(DATA / 'hardware-review', 'pdf-source-observations'),
        read_table(DATA / 'hardware-review', 'pdf-readings'), manifest, hardware_coverage['summary']['dictionary_hash'])
    attach_pdf_coverage(hardware_coverage, pdf_coverage)
    export_pdf_coverage(pdf_coverage, PUBLIC_API / 'equipment', DOWNLOADS / 'equipment')
    export_coverage(hardware_coverage, PUBLIC_API / 'equipment', DOWNLOADS / 'equipment')
    manifest["equipment"] = {"api": "/api/v1/equipment/index.json", "loco_api": "/api/v1/equipment/loco-manip.json", "counts": equipment_bundle['index']['counts'], "authority_hash": equipment_bundle['index']['authority_hash']}
    manifest['equipment']['coverage_api'] = '/api/v1/equipment/coverage-summary.json'
    manifest['equipment']['readings_api'] = '/api/v1/equipment/coverage-readings.json'
    manifest['equipment']['pdf_readings_api'] = '/api/v1/equipment/coverage-pdf-readings.json'
    manifest['downloads']['hardware_coverage'] = '/downloads/equipment/hardware-coverage.jsonl.gz'
    manifest['downloads']['fulltext_readings'] = '/downloads/equipment/fulltext-readings.jsonl'
    manifest['downloads']['pdf_readings'] = '/downloads/equipment/pdf-readings.jsonl'
    manifest['downloads']['pdf_source_observations'] = '/downloads/equipment/pdf-source-observations.jsonl'
    write_json(PUBLIC_API / "migration-report.json", migration_report, compact=True)

    with sqlite_export(ROOT, DOWNLOADS, PUBLIC_API / "catalog-manifest.json", manifest) as connection:
        connection.executescript("""
            -- Physical layout only: preserve all tables, values, indexes and views.
            -- 16 KiB pages reduce overflow/unused space in the long JSON records.
            PRAGMA page_size=16384;
            PRAGMA journal_mode=OFF;
            PRAGMA synchronous=OFF;
            CREATE TABLE works (work_id TEXT PRIMARY KEY, title TEXT NOT NULL, title_zh TEXT, abstract TEXT, authors_json TEXT NOT NULL, first_public_date TEXT, relevance_status TEXT NOT NULL, primary_direction TEXT, directions_json TEXT NOT NULL, questions_json TEXT NOT NULL, facets_json TEXT NOT NULL, evidence_grade TEXT NOT NULL, strict_peer_reviewed INTEGER NOT NULL, summary_zh TEXT);
            CREATE TABLE manifestations (manifestation_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, kind TEXT NOT NULL, url TEXT NOT NULL, published_at TEXT, venue TEXT, year INTEGER, status TEXT, peer_reviewed INTEGER NOT NULL, source_record_id TEXT);
            CREATE TABLE organizations (organization_id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT, tier TEXT NOT NULL, entity_type TEXT, region TEXT, country TEXT, source_health TEXT);
            CREATE TABLE work_organizations (work_id TEXT NOT NULL, organization_id TEXT NOT NULL, role TEXT, attribution_grade TEXT, confidence REAL, evidence_url TEXT, PRIMARY KEY(work_id, organization_id, evidence_url));
            CREATE TABLE taxonomy_assignments (work_id TEXT NOT NULL, axis TEXT NOT NULL, code TEXT NOT NULL, is_primary INTEGER NOT NULL, confidence TEXT, classifier_version TEXT);
            CREATE TABLE evidence_events (event_id TEXT PRIMARY KEY, work_id TEXT, organization_id TEXT, event_type TEXT NOT NULL, title TEXT, url TEXT, published_at TEXT, payload_json TEXT NOT NULL);
            CREATE TABLE editorial_claims (claim_id TEXT PRIMARY KEY, month TEXT NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL, supporting_ids_json TEXT NOT NULL, counterevidence_ids_json TEXT NOT NULL, generator TEXT NOT NULL);
            CREATE TABLE field_provenance (work_id TEXT NOT NULL, field TEXT NOT NULL, source_record_id TEXT NOT NULL, observed_at TEXT);
            CREATE TABLE work_extra_payloads (work_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
            CREATE VIEW work_payloads AS SELECT w.work_id, json_set(e.payload_json,
              '$.work_id',w.work_id,'$.title',w.title,'$.title_zh',w.title_zh,'$.abstract',w.abstract,'$.authors',json(w.authors_json),
              '$.first_public_date',w.first_public_date,'$.primary_direction',w.primary_direction,'$.directions',json(w.directions_json),
              '$.questions',json(w.questions_json),'$.facets',json(w.facets_json),'$.evidence_grade',w.evidence_grade,
              '$.strict_peer_reviewed',json(CASE WHEN w.strict_peer_reviewed THEN 'true' ELSE 'false' END),'$.summary_zh',w.summary_zh
            ) AS payload_json FROM works w JOIN work_extra_payloads e USING(work_id);
            CREATE TABLE source_records (source_record_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
            CREATE TABLE work_aliases (alias TEXT NOT NULL, work_id TEXT NOT NULL, payload_json TEXT NOT NULL);
            CREATE TABLE work_relations (payload_json TEXT NOT NULL);
            CREATE TABLE source_reconciliation (source_record_id TEXT NOT NULL, work_id TEXT, payload_json TEXT NOT NULL);
            CREATE TABLE signal_evidence (record_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, signal_id TEXT NOT NULL, stance TEXT NOT NULL, review_status TEXT NOT NULL, public_at TEXT, payload_json TEXT NOT NULL);
            CREATE TABLE text_snapshots (snapshot_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, version TEXT, available_at TEXT, payload_json TEXT NOT NULL);
            CREATE TABLE report_text_snapshots (snapshot_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, canonical_work_id TEXT NOT NULL, available_at TEXT, payload_json TEXT NOT NULL);
            CREATE TABLE report_coverage (organization_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
            CREATE TABLE report_coverage_metadata (key TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
            CREATE TABLE release_recall_gold (gold_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
        """)
        org_names_by_work = {work_id: [org_by_id.get(org_id, {}).get("display_name", org_id) for org_id in org_ids] for work_id, org_ids in organizations_by_work.items()}
        alias_codes = {
            "vla": {"D1"},
            "大小脑": {"D2"},
            "世界模型": {"D3"},
            "灵巧操作": {"D4"},
            "跨本体": {"D1", "D8", "D9"},
            "π0": set(),
            "技术报告": set(),
        }

        def aliases_for_work(row: dict) -> str:
            values = []
            directions = set(row.get("directions") or [])
            kinds = {item["kind"] for item in manifestations_by_work.get(row["work_id"], [])}
            for key, terms in facets_config.get("search_aliases", {}).items():
                is_pi = key == "π0" and bool(re.search(r"(?:π|\\pi|\bpi)[_ .-]?0(?:\b|\.)", row["title"], re.I))
                if directions & alias_codes.get(key, set()) or (key == "技术报告" and "technical_report" in kinds) or is_pi:
                    values.extend([key, *terms])
            return " ".join(values)
        def sqlite_json(value):
            # Compact whitespace only; the full JSON values remain round-trip exact.
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

        connection.executemany("INSERT INTO works VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [(
            row["work_id"], row["title"], row.get("title_zh"), row.get("abstract", ""), sqlite_json(row.get("authors") or []), row.get("first_public_date"), row["relevance"]["status"], row.get("primary_direction"), sqlite_json(row.get("directions") or []), sqlite_json(row.get("questions") or []), sqlite_json(row.get("facets") or {}), row.get("evidence_grade", "E0"), int(bool(row.get("strict_peer_reviewed"))), row.get("summary_zh", ""),
        ) for row in works])
        connection.executemany("INSERT INTO manifestations VALUES (?,?,?,?,?,?,?,?,?,?)", [(row["manifestation_id"], row["work_id"], row["kind"], row["url"], row.get("published_at"), row.get("venue"), row.get("year"), row.get("status"), int(bool(row.get("peer_reviewed"))), row.get("source_record_id")) for row in manifestations])
        connection.executemany("INSERT INTO organizations VALUES (?,?,?,?,?,?,?,?)", [(row["organization_id"], row.get("display_name") or row["organization_id"], row.get("slug"), row.get("tier"), row.get("entity_type"), row.get("region"), row.get("country"), row.get("source_health")) for row in organizations])
        connection.executemany("INSERT OR IGNORE INTO work_organizations VALUES (?,?,?,?,?,?)", [(row.get("work_id"), row.get("organization_id"), row.get("role"), row.get("evidence_grade"), row.get("confidence"), row.get("evidence_url") or "") for row in work_org_links if row.get("work_id") and row.get("organization_id")])
        connection.executemany("INSERT INTO taxonomy_assignments VALUES (?,?,?,?,?,?)", [(row["work_id"], row["axis"], row["code"], int(row["is_primary"]), row.get("confidence"), row.get("classifier_version")) for row in taxonomy_assignments])
        connection.executemany("INSERT INTO evidence_events VALUES (?,?,?,?,?,?,?,?)", [(row["event_id"], row.get("work_id"), row.get("organization_id"), row["event_type"], row.get("title"), row.get("url"), row.get("published_at"), sqlite_json(row)) for row in evidence_events])
        connection.executemany("INSERT INTO editorial_claims VALUES (?,?,?,?,?,?,?)", [(row["claim_id"], row["month"], row["kind"], row["text"], sqlite_json(row["supporting_ids"]), sqlite_json(row["counterevidence_ids"]), row["generator"]) for row in editorial_claims])
        connection.executemany("INSERT INTO field_provenance VALUES (?,?,?,?)", [(row["work_id"], row["field"], row["source_record_id"], row["observed_at"]) for row in provenance])
        mapped_fields = {"work_id", "title", "title_zh", "abstract", "authors", "first_public_date", "primary_direction", "directions", "questions", "facets", "evidence_grade", "strict_peer_reviewed", "summary_zh"}
        connection.executemany("INSERT INTO work_extra_payloads VALUES (?,?)", [(row["work_id"], sqlite_json({key: value for key, value in row.items() if not key.startswith("_") and key not in mapped_fields})) for row in works])
        connection.executemany("INSERT INTO source_records VALUES (?,?)", [(row["source_record_id"], sqlite_json(row)) for row in source_records])
        connection.executemany("INSERT INTO work_aliases VALUES (?,?,?)", [(row["alias"], row["work_id"], sqlite_json(row)) for row in alias_rows])
        connection.executemany("INSERT INTO work_relations VALUES (?)", [(sqlite_json(row),) for row in payload.get("work-relations", [])])
        connection.executemany("INSERT INTO source_reconciliation VALUES (?,?,?)", [(row["source_record_id"], row.get("work_id"), sqlite_json(row)) for row in payload.get("reconciliation", [])])
        connection.executemany("INSERT INTO signal_evidence VALUES (?,?,?,?,?,?,?)", [(row["record_id"], row["work_id"], row["signal_id"], row["stance"], row["review_status"], row.get("public_at"), sqlite_json(row)) for row in signal_review["records"]])
        connection.executemany("INSERT INTO text_snapshots VALUES (?,?,?,?,?)", [(row["snapshot_id"], row["work_id"], row.get("version"), row.get("available_at"), sqlite_json(row)) for row in text_snapshots])
        report_owners = {row["snapshot_id"]: work_id for work_id, records in report_by_work.items() for row in records}
        connection.executemany("INSERT INTO report_text_snapshots VALUES (?,?,?,?,?)", [(row["snapshot_id"], row["work_id"], report_owners[row["snapshot_id"]], row.get("available_at"), sqlite_json(row)) for row in report_snapshots])
        connection.executemany("INSERT INTO report_coverage VALUES (?,?)", [(row["organization_id"], sqlite_json(row)) for row in report_coverage["organizations"]])
        connection.executemany("INSERT INTO report_coverage_metadata VALUES (?,?)", [(key, sqlite_json(value)) for key, value in report_coverage.items() if key != "organizations"])
        connection.executemany("INSERT INTO release_recall_gold VALUES (?,?)", [(row["gold_id"], sqlite_json(row)) for row in gold_records])
        build_people_sqlite(connection, people_bundle)
        equipment_sqlite(connection, equipment_bundle)
        coverage_sqlite(connection, hardware_coverage)
        pdf_coverage_sqlite(connection, pdf_coverage)
        from sqlite_catalog_fidelity import build_catalog_fidelity
        from sqlite_editorial_export import build_editorial_archive, read_editorial_artifacts
        fidelity = build_catalog_fidelity(connection, payload)
        editorial_archive = build_editorial_archive(connection, read_editorial_artifacts(DATA / "editorial"))
        write_json(PUBLIC_API / "sqlite-fidelity.json", {"catalog": fidelity, "editorial": editorial_archive}, compact=True)
        from sqlite_search_export import build_sqlite_search
        build_sqlite_search(connection, [{"work_id": row["work_id"], "organizations": " ".join(org_names_by_work.get(row["work_id"], [])),
            "keywords": " ".join([*(row.get("directions") or []), *(row.get("questions") or []), *(value for values in row.get("facets", {}).values() for value in values), aliases_for_work(row), report_quote_text({"report_text": report_views.get(row["work_id"])})])} for row in works])

    print(json.dumps({"status": "ok", "counts": counts, "migration_report": str(CATALOG / "migration-report.json")}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", help="Data cut in YYYY-MM-DD; defaults to source registry window end")
    parser.add_argument("--summary-status", choices=["data_only", "llm_complete"], default="data_only")
    parser.add_argument("--migrate", action="store_true", help="One-time migration into the authoritative sharded catalog")
    parser.add_argument("--ingest", action="store_true", help="Ingest source deltas without overwriting curated catalog records")
    parser.add_argument("--ingest-status", action="store_true", help="Import only explicit reviewed research-status notices, preserving all other authority records")
    parser.add_argument("--ingest-people", action="store_true", help="Explicitly import person review staging into the separate four-table JSONL authority")
    return parser.parse_args()


def build(args: argparse.Namespace) -> None:
    from prepare_catalog import reconcile
    from catalog_enrichment import finalize_facts, ingest_delta, ingest_conferences
    from ingest_attribution import ingest_attribution_additions
    from ingest_capability_evidence import ingest_capability_additions
    from merge_reviewed_identities import merge_reviewed_identities
    from ingest_date_reviews import ingest_date_reviews
    from archive_versioned_text import archive_versioned_text
    from ingest_reviewed_releases import ingest_reviewed_releases
    from ingest_research_status import ingest_research_status_additions
    from organization_coverage import build_organization_coverage
    registry = read_json(ROOT / "config" / "source-registry.json", {})
    when = args.as_of or registry.get("window", {}).get("until")
    if args.migrate and not (CATALOG / "manifest.json").exists():
        payload = reconcile(migrate_legacy(args), DATA, when)
        payload = finalize_facts(payload, when)
        metadata = save_catalog(CATALOG, payload, {"data_through": when, "input_counts": payload.pop("input_counts", {})})
    else:
        payload, metadata = load_catalog(CATALOG)
        if args.ingest:
            incoming = reconcile(migrate_legacy(args), DATA, when)
            payload = ingest_delta(payload, incoming)
            payload = ingest_conferences(payload, DATA / "conferences")
            payload = ingest_attribution_additions(payload, DATA)
            payload = merge_reviewed_identities(payload, DATA)
            payload = ingest_capability_additions(payload, DATA)
            payload = finalize_facts(payload, when)
            payload = ingest_reviewed_releases(payload, DATA)
            payload = ingest_date_reviews(payload, DATA)
            # Recompute derived event/flag views after precision corrections;
            # raw source observations and historical IDs remain unchanged.
            payload = finalize_facts(payload, when)
            payload = archive_versioned_text(payload, DATA, read_json(DATA / "preprints.json", []))
            from extract_report_archive import register_report_archive_proofs
            report_additions = read_table(DATA, "report-text-additions")
            payload = register_report_archive_proofs(payload, read_table(DATA, "report-archive-proofs"), report_additions, root=ROOT)
            payload = register_report_text_additions(payload, report_additions)
            payload = ingest_research_status_additions(payload, DATA)
            coverage = build_organization_coverage(payload["works"], payload["organizations"], payload["work-organization-links"], {"registered": payload.get("source-health", []), "records": payload["source-records"]}, when)
            payload["organization-candidates"] = coverage["t2_candidates"]
            changes = {change["organization_id"]: change for change in coverage["tier_changes"]}
            for org in payload["organizations"]:
                if org["organization_id"] in changes:
                    change = changes[org["organization_id"]]
                    org["tier"] = change["to"]
                    org.setdefault("tier_history", []).append({**change, "recorded_at": when})
            metadata = save_catalog(CATALOG, payload, {**metadata, "data_through": when, "input_counts": incoming.get("input_counts", {})})
        elif getattr(args, "ingest_status", False):
            payload = ingest_research_status_additions(payload, DATA)
            metadata = save_catalog(CATALOG, payload, {**metadata, "data_through": when})
    if getattr(args, "ingest_people", False):
        from people_radar import load_people_reviews, load_people_authority, ingest_people_reviews, save_people_authority
        people = ingest_people_reviews(payload, load_people_reviews(DATA / "people/reviews"), load_people_authority(DATA / "people"))
        save_people_authority(DATA / "people", people)
    export_catalog(payload, metadata, args)


if __name__ == "__main__":
    build(parse_args())
