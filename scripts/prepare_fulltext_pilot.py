#!/usr/bin/env python3
"""Prepare an OFFLINE, source-bound stratified reading pilot, never a reader.

Only public metadata is loaded. No HTML, body cache, private acquisition log,
LLM, queue or authority write is used. Output must be an explicit NEW private
directory; inside this repository it must be under .research. Default size:
100 distinct canonical works. This purposive available-source sample is NOT
a representative sample of all research or an independent gold standard.

Required CLI: --catalog DIR --published-dir DIR --dictionary FILE
              --as-of YYYY-MM-DD --output-dir NEW_ABSOLUTE_PRIVATE_DIR
Optional: --readings FILE --hardware-reviews FILE --size 100 --seed STRING.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timezone
from pathlib import Path

sys.dont_write_bytecode = True
from catalog_store import encode, fingerprint
from hardware_census import detect_mentions, dictionary_hash
from organization_coverage import valid_url
from promote_hardware_snapshot import _open_directory, _read_path
from snapshot_hardware_sources import (AVAILABLE, HASH, PARSER_VERSION, SnapshotError, arxiv_identity,
                                       parse_jsonl, scan_key, timestamp, validate_public, validate_scan)

ROOT = Path(__file__).resolve().parents[1]
POLICY = "fulltext-pilot-v1"
DEFAULT_SEED = "fulltext-pilot-2026-v1"
DIRECTIONS = [f"D{number}" for number in range(1, 16)]
RELEVANCE = ["included", "manual_review", "candidate", "excluded", "unknown"]
LENGTHS = ["lt_10000", "10000_29999", "30000_59999", "60000_plus"]
FLAGS = {"review_required", "date_review_required", "source_review_required", "date_conflict", "source_conflict"}
SOURCE_FIELDS = ("observation_id", "source_url", "effective_url", "version", "raw_sha256", "text_sha256",
                 "observed_at", "parser_version", "body_characters", "status")
LIMITATIONS = [
    "Purposive throughput/quality pilot among registered, text-available, current-dictionary-scanned sources only; not a probability sample.",
    "Unavailable sources, uncollected works and the unobserved web are outside the eligible population; do not infer global representativeness or recall.",
    "No HTML/body/image was read and no paper understanding, hardware use, correctness or completed reading is asserted.",
    "Known dates use 12 complete calendar months plus the as-of provisional month; unknown dates are an auxiliary stratum, not claimed to fall inside the window.",
    "Existing readings and verified hardware reviews are convenience controls, never independent gold or blind evaluation.",
    "Relevance is the stored routing status, not publication validity; research-status notices are flagged but not independently adjudicated here.",
    "Public metadata and organization judgments are the current recorded snapshot, not a reconstructed historical catalog.",
]


def require(condition, reason):
    if not condition:
        raise SnapshotError(reason)


def canonical_rows(rows, key):
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(key), str) and row[key], "missing_canonical_identity:" + key)
        require(row[key] not in result, "duplicate_canonical_identity:" + key)
        result[row[key]] = row
    return result


def month_shift(month, delta):
    year, number = map(int, month.split("-"))
    absolute = year * 12 + number - 1 + delta
    return f"{absolute // 12:04d}-{absolute % 12 + 1:02d}"


def date_interval(value, precision=None):
    """Preserve day/month/year precision; no fabricated publication day."""
    if not isinstance(value, str):
        return None
    try:
        if precision == "day" or precision is None and len(value) == 10:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                return None
            parsed = date.fromisoformat(value)
            return parsed, parsed
        if precision == "month" or precision is None and len(value) == 7:
            month = value[:7]
            if not re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", value):
                return None
            if len(value) == 10:
                date.fromisoformat(value)
            year, number = map(int, month.split("-"))
            return date(year, number, 1), date(year, number, calendar.monthrange(year, number)[1])
        if precision == "year" or precision is None and len(value) == 4:
            year = int(value[:4])
            return date(year, 1, 1), date(year, 12, 31)
    except (ValueError, TypeError):
        pass
    return None


def month_stratum(work, as_of, months):
    value, precision = work.get("first_public_date"), work.get("first_public_date_precision")
    interval = date_interval(value, precision) if precision in {"day", "month", "year"} else None
    if interval and interval[0] > as_of:
        return None, "publication_after_as_of"
    if interval and interval[1] < date.fromisoformat(months[0] + "-01"):
        return None, "publication_before_window"
    if precision not in {"day", "month"} or interval is None:
        return "unknown_date", "missing_invalid_or_insufficient_month_precision"
    return interval[0].strftime("%Y-%m"), "canonical_" + precision + "_precision"


def date_not_after(value, as_of):
    if not isinstance(value, str):
        return False
    try:
        return timestamp(value).date() <= as_of if "T" in value else date.fromisoformat(value) <= as_of
    except (ValueError, SnapshotError):
        return False


def reliable_link(link, work, organization, as_of):
    if link.get("evidence_grade") not in {"G1", "G2"}:
        return False, "not_g1_g2"
    if any(link.get(flag) for flag in FLAGS):
        return False, "attribution_pending_review_or_conflict"
    if not valid_url(link.get("evidence_url")):
        return False, "missing_attribution_evidence_url"
    if not date_not_after(link.get("verified_at"), as_of):
        return False, "attribution_verification_after_as_of_or_invalid"
    when = date_interval(work.get("first_public_date"), work.get("first_public_date_precision"))
    if work.get("first_public_date_precision") not in {"day", "month"}:
        when = None
    for field, lower in (("active_from", True), ("active_to", False)):
        value = organization.get(field)
        if value is None:
            continue
        interval = date_interval(value)
        # A year-only start is safe for later years, not evidence of a day
        # within its boundary year. Use the conservative end of each bound.
        if interval is None or when is None or (when[0] < interval[1] if lower else when[1] > interval[0]):
            return False, "organization_active_interval_unresolved_or_outside"
    if link["evidence_grade"] == "G1":
        return True, "g1_direct_evidence"
    membership = link.get("membership_evidence") or {}
    normalize = lambda value: re.sub(r"\W+", "", str(value or "")).casefold()
    authors = {normalize(author if isinstance(author, str) else author.get("name")) for author in work.get("authors", [])}
    start = date_interval(membership.get("valid_from"))
    end = date_interval(membership.get("valid_to")) if membership.get("valid_to") else None
    valid = (when and start and valid_url(membership.get("source_url")) and
             normalize(membership.get("author")) in authors - {""} and when[0] >= start[1] and
             (not membership.get("valid_to") or end and when[1] <= end[0]))
    return bool(valid), "g2_author_membership_interval" if valid else "g2_membership_unresolved_or_outside"


def latest_unambiguous(rows):
    """Order-independent latest observation; same-time lineage beats its parent.

    Unrelated conflicting latest records are ineligible, never hash-picked as
    a substitute for a meaningful source order.
    """
    if not rows:
        return None
    newest = max(timestamp(row["observed_at"]) for row in rows)
    tied = [row for row in rows if timestamp(row["observed_at"]) == newest]
    parents = {row.get("parent_observation_id") for row in tied}
    leaves = [row for row in tied if row["observation_id"] not in parents]
    return leaves[0] if len(leaves) == 1 else None


def length_band(characters):
    return LENGTHS[0 if characters < 10000 else 1 if characters < 30000 else 2 if characters < 60000 else 3]


def control_metadata(work_id, source, readings, reviews, as_of, source_bindings):
    flags, reading_ids, review_ids = set(), set(), set()
    for kind, records, status_field, status_value, date_field, id_field, ids in (
            ("prior_reading", readings, "reading_status", "completed", "read_completed_at", "reading_id", reading_ids),
            ("prior_hardware_review", reviews, "review_status", "verified", "reviewed_at", "usage_id", review_ids)):
        for row in records.get(work_id, []):
            completed = row.get(date_field) if kind == "prior_reading" else row.get(date_field) or row.get("observed_at")
            version = row.get("version") if kind == "prior_reading" else row.get("source_version")
            binding = (work_id, row.get("source_url"), row.get("raw_sha256"), version)
            if (row.get(status_field) != status_value or not date_not_after(completed, as_of) or
                    not isinstance(row.get(id_field), str) or not row[id_field] or binding not in source_bindings):
                continue
            same_source = binding == (work_id, source["source_url"], source["raw_sha256"], source["version"])
            flags.add(kind + ("_same_source" if same_source else "_other_source"))
            if isinstance(row.get(id_field), str):
                ids.add(row[id_field])
    return {"labels": sorted(flags), "reading_ids": sorted(reading_ids), "hardware_review_ids": sorted(review_ids),
            "independent_gold": False, "assurance": "convenience_control_not_blind_or_independent_gold"}


def _group(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get(key)].append(row)
    return grouped


def plan_pilot(*, works, observations, scans, dictionary, organizations, links, as_of,
               readings=(), hardware_reviews=(), seed=DEFAULT_SEED, size=100, control_target=10):
    require(type(size) is int and 1 <= size <= 1000, "pilot_size_must_be_1_to_1000")
    require(type(control_target) is int and control_target >= 0, "control_target_invalid")
    require(isinstance(seed, str) and 0 < len(seed) <= 200, "seed_invalid")
    require(isinstance(as_of, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of), "as_of_date_required")
    anchor = date.fromisoformat(as_of)
    readings, hardware_reviews = list(readings), list(hardware_reviews)
    cutoff = datetime.combine(anchor, time.max, tzinfo=timezone.utc)
    months = [month_shift(as_of[:7], offset) for offset in range(-12, 1)]
    by_work, by_org = canonical_rows(works, "work_id"), canonical_rows(organizations, "organization_id")
    canonical = {wid: (identity[0] if (identity := arxiv_identity(work.get("identifiers", {}).get("arxiv"))) else None)
                 for wid, work in by_work.items()}
    core = {oid for oid, organization in by_org.items() if organization.get("tier") == "T0" and organization.get("tracking_unit") is True}
    detect_mentions("", dictionary)  # validate dictionary schema, not source text
    dhash = dictionary_hash(dictionary)
    orgs_by_work, link_issues = defaultdict(dict), Counter()
    for link in sorted(links, key=encode):
        wid, oid = link.get("work_id"), link.get("organization_id")
        if wid not in by_work or oid not in by_org:
            link_issues["unregistered_link_identity"] += 1
            continue
        valid, reason = reliable_link(link, by_work[wid], by_org[oid], anchor)
        if valid:
            old = orgs_by_work[wid].get(oid)
            if old is None or link["evidence_grade"] < old["evidence_grade"]:
                orgs_by_work[wid][oid] = {"organization_id": oid, "evidence_grade": link["evidence_grade"],
                                        "evidence_url": link["evidence_url"], "verified_at": link.get("verified_at"), "basis": reason}
        else:
            link_issues[reason] += 1
    known_observations, source_groups = {}, defaultdict(list)
    for row in observations:
        require(row.get("work_id") in by_work, "source_work_not_canonical")
        validate_public(row, canonical)
        oid = row["observation_id"]
        require(oid not in known_observations or known_observations[oid] == row, "source_observation_id_conflict")
        if oid in known_observations:
            continue
        known_observations[oid] = row
        if timestamp(row["observed_at"]) <= cutoff and (row.get("fetched_at") is None or timestamp(row["fetched_at"]) <= cutoff):
            source_groups[(row["work_id"], row.get("source_url"))].append(row)
    body_bindings = {(row["work_id"], row.get("source_url"), row.get("text_sha256")) for row in known_observations.values()}
    raw_bindings = {(*binding, row.get("raw_sha256")) for row in known_observations.values()
                    for binding in [(row["work_id"], row.get("source_url"), row.get("text_sha256"))]}
    first_body_times, first_raw_times = {}, {}
    for source in known_observations.values():
        when = timestamp(source["observed_at"])
        body = (source["work_id"], source.get("source_url"), source.get("text_sha256"))
        raw = (*body, source.get("raw_sha256"))
        first_body_times[body] = min(first_body_times.get(body, when), when)
        first_raw_times[raw] = min(first_raw_times.get(raw, when), when)
    scan_groups, scan_events = defaultdict(list), {}
    for row in scans:
        validate_scan(row, canonical)
        binding = row["work_id"], row["source_url"], row["content_hash"]
        require(((*binding, row["source_observation_hash"]) in raw_bindings if "source_observation_hash" in row else binding in body_bindings),
                "scan_source_binding_missing")
        observed_at = timestamp(row["observed_at"])
        source_time = (first_raw_times[(*binding, row["source_observation_hash"])] if "source_observation_hash" in row else first_body_times[binding])
        require(observed_at >= source_time, "scan_precedes_bound_source_observation")
        event_key = (*scan_key(row), observed_at)
        equivalent = lambda record: {**record, "observed_at": timestamp(record["observed_at"]).isoformat()}
        require(event_key not in scan_events or equivalent(scan_events[event_key]) == equivalent(row), "scan_event_conflict")
        if event_key in scan_events:
            scan_events[event_key] = min(scan_events[event_key], row, key=encode)
            continue
        scan_events[event_key] = row
    for row in scan_events.values():
        if timestamp(row["observed_at"]) <= cutoff and row["dictionary_hash"] == dhash:
            scan_groups[scan_key(row)].append(row)
    available, source_issues = defaultdict(list), defaultdict(set)
    for (wid, _), group in source_groups.items():
        source = latest_unambiguous(group)
        reason = None
        if source is None:
            reason = "ambiguous_latest_source_tie"
        elif source["status"] not in AVAILABLE:
            reason = "latest_source_" + source["status"]
        elif source.get("parser_version") != PARSER_VERSION:
            reason = "latest_source_parser_not_current"
        elif not source.get("version") or any(not isinstance(source.get(key), str) or not HASH.fullmatch(source[key]) for key in ("raw_sha256", "text_sha256")):
            reason = "source_version_or_hash_unresolved"
        elif type(source.get("body_characters")) is not int or source["body_characters"] <= 0:
            reason = "body_length_unknown_or_empty"
        elif source["status"] == "full_text_available" and (source.get("transport_complete") is False or source.get("transport_truncated") is True or
               source.get("transport_verification") == "incomplete" or any(source.get(key) not in (None, 0) for key in ("transport_returncode", "curl_exit_code"))):
            reason = "full_source_has_incomplete_transport"
        if reason is None:
            matches = scan_groups.get((wid, source["source_url"], dhash, source["text_sha256"]), [])
            latest_scan = max(matches, key=lambda row: timestamp(row["observed_at"])) if matches else None
            if latest_scan is None or latest_scan["status"] != "scanned":
                reason = "current_dictionary_scan_missing" if latest_scan is None else "latest_current_dictionary_scan_failed"
            elif latest_scan.get("parser_version") != PARSER_VERSION:
                reason = "latest_current_dictionary_scan_parser_not_current"
            else:
                available[wid].append((source, latest_scan))
        if reason:
            source_issues[wid].add(reason)
    readings_by_work, reviews_by_work = _group(readings, "work_id"), _group(hardware_reviews, "work_id")
    control_bindings = {(row["work_id"], row.get("source_url"), row.get("raw_sha256"), row.get("version"))
                        for group in source_groups.values() for row in group if row["status"] in AVAILABLE}
    population, window_works, excluded = [], [], []
    for wid, work in sorted(by_work.items()):
        month, date_basis = month_stratum(work, anchor, months)
        if month is None:
            excluded.append({"work_id": wid, "reasons": [date_basis]})
            continue
        org_links = [value for _, value in sorted(orgs_by_work[wid].items())]
        direction = work.get("primary_direction") if work.get("primary_direction") in DIRECTIONS else "unassigned"
        relevance = work.get("relevance") or {}
        state = relevance.get("status", "unknown") if isinstance(relevance, dict) else "unknown"
        state = state if state in RELEVANCE else "unknown"
        base = {"work_id": wid, "title": work.get("title"), "arxiv_id": canonical[wid],
                "first_public_date": work.get("first_public_date"), "date_precision": work.get("first_public_date_precision", "unknown"),
                "month": month, "date_basis": date_basis, "primary_direction": direction, "relevance_status": state,
                "reliable_organization_links": org_links, "core_organization_ids": sorted(set(orgs_by_work[wid]) & core),
                "organization_evidence": "G1" if any(row["evidence_grade"] == "G1" for row in org_links) else "G2" if org_links else "none",
                "research_status_notice_present": bool(work.get("research_status_notices"))}
        window_works.append(base)
        candidates = available.get(wid, [])
        if not candidates:
            excluded.append({"work_id": wid, "reasons": sorted(source_issues[wid]) or ["no_as_of_public_available_source"]})
            continue
        source, scan = sorted(candidates, key=lambda pair: (-int(pair[0]["version"][1:]),
                              -timestamp(pair[0]["observed_at"]).timestamp(), pair[0]["observation_id"]))[0]
        control = control_metadata(wid, source, readings_by_work, reviews_by_work, anchor, control_bindings)
        population.append({**base, "source_observation_id": source["observation_id"],
                           **{key: source.get(key) for key in SOURCE_FIELDS if key != "observation_id"},
                           "length_band": length_band(source["body_characters"]), "source_status": source["status"],
                           "dictionary_hash": dhash, "scan_observed_at": scan["observed_at"], "scan_event_hash": fingerprint(scan),
                           "scan_raw_sha256": scan.get("source_observation_hash"), "scan_parser_version": scan.get("parser_version"),
                           "scan_binding": ("exact_raw_and_body" if scan.get("source_observation_hash") == source["raw_sha256"] else
                                            "historical_raw_same_body" if scan.get("source_observation_hash") else "legacy_body_only"),
                           "eligible_source_count": len(candidates), "source_choice": "highest_available_explicit_version_then_observation_time_not_global_latest_claim",
                           "control": control, "control_kind": "prior_review_convenience_control" if control["labels"] else "no_prior_review_record"})
    scalar_dimensions = ("primary_direction", "relevance_status", "length_band", "organization_evidence", "source_status", "control_kind")
    counts, selected, remaining = Counter(), [], {row["work_id"]: row for row in population}
    tie = lambda value: fingerprint([POLICY, seed, value])
    buckets = _group(population, "month")
    control_selected = 0
    while remaining and len(selected) < size:
        active_months = [month for month, rows in buckets.items() if any(row["work_id"] in remaining for row in rows)]
        month = min(active_months, key=lambda value: (counts[("month", value)], tie("month:" + value), value))
        candidates = [row for row in buckets[month] if row["work_id"] in remaining]
        def rank(row):
            tokens = [(dimension, row[dimension]) for dimension in scalar_dimensions]
            org_tokens = [("core_organization", oid) for oid in row["core_organization_ids"]]
            novelty = sum(counts[token] == 0 for token in tokens) + any(counts[token] == 0 for token in org_tokens)
            balance = sum(1000 // (1 + counts[token]) for token in tokens) + max([1000 // (1 + counts[token]) for token in org_tokens] or [0])
            control_preference = bool(row["control"]["labels"]) and control_selected < min(control_target, size)
            return -int(control_preference), -novelty, -balance, tie(row["work_id"]), row["work_id"]
        chosen = min(candidates, key=rank)
        tokens = [(dimension, chosen[dimension]) for dimension in scalar_dimensions]
        tokens += [("core_organization", oid) for oid in chosen["core_organization_ids"]]
        new_coverage = [dimension + ":" + value for dimension, value in tokens if counts[(dimension, value)] == 0]
        selected.append({**chosen, "selection_rank": len(selected) + 1,
                         "selection_reason": {"policy": "least_selected_month_round_robin_then_deterministic_greedy_stratum_coverage",
                                              "month_turn": month, "newly_covered_strata": new_coverage,
                                              "control_preference_used": bool(chosen["control"]["labels"]) and control_selected < min(control_target, size)}})
        for token in [*tokens, ("month", month)]:
            counts[token] += 1
        control_selected += bool(chosen["control"]["labels"])
        remaining.pop(chosen["work_id"])
    def distribution(field, values, *, multiple=False, catalog=False):
        count = lambda rows, value: sum(value in row.get(field, []) if multiple else row.get(field) == value for row in rows)
        result = []
        for value in values:
            eligible, chosen = count(population, value), count(selected, value)
            entry = {"stratum": value, "eligible": eligible, "selected": chosen}
            if catalog:
                entry["catalog_in_window_or_unknown"] = count(window_works, value)
            entry["gap"] = ("no_eligible_available_current_scan" if eligible == 0 else "not_selected_within_budget" if chosen == 0 else None)
            result.append(entry)
        return result
    coverage = {"months": distribution("month", [*months, "unknown_date"], catalog=True),
                "directions": distribution("primary_direction", [*DIRECTIONS, "unassigned"], catalog=True),
                "core_organizations": distribution("core_organization_ids", sorted(core), multiple=True, catalog=True),
                "length_bands": distribution("length_band", LENGTHS), "relevance": distribution("relevance_status", RELEVANCE, catalog=True),
                "organization_evidence": distribution("organization_evidence", ["G1", "G2", "none"]),
                "source_status": distribution("source_status", sorted(AVAILABLE)),
                "controls": distribution("control_kind", ["prior_review_convenience_control", "no_prior_review_record"])}
    hashes = {name: fingerprint(sorted(rows, key=encode)) for name, rows in (
        ("works", works), ("source_observations", observations), ("source_scans", scans), ("organizations", organizations),
        ("organization_links", links), ("readings", list(readings)), ("hardware_reviews", list(hardware_reviews)))}
    hashes["dictionary"] = dhash
    manifest = {"schema_version": "1", "kind": "fulltext_reading_pilot_selection", "policy_version": POLICY,
                "seed": seed, "as_of": as_of, "as_of_timezone": "UTC", "as_of_boundary": "inclusive_end_of_day",
                "requested_count": size, "selected_count": len(selected),
                "shortfall": max(0, size - len(selected)), "catalog_work_count": len(works), "window_or_unknown_work_count": len(window_works),
                "eligible_population_count": len(population), "selection_source": "public_registered_available_sources_with_current_successful_dictionary_scan",
                "complete_months": months[:-1], "provisional_month": months[-1], "unknown_dates_separate": True,
                "core_organization_basis": "canonical_organizations_tier_T0_and_tracking_unit_true",
                "primary_direction_basis": "canonical_work_primary_direction_no_inference_from_multilabel_directions",
                "control_target_preference_not_quota": min(control_target, size), "control_selected": control_selected,
                "controls_independent_gold": False, "input_hashes": hashes, "organization_link_issues": dict(sorted(link_issues.items())),
                "exclusion_reason_counts": dict(sorted(Counter(reason for row in excluded for reason in row["reasons"]).items())),
                "uncovered_months": [row for row in coverage["months"] if row["selected"] == 0],
                "uncovered_directions": [row for row in coverage["directions"] if row["selected"] == 0],
                "uncovered_core_organizations": [row for row in coverage["core_organizations"] if row["selected"] == 0],
                "limitations": LIMITATIONS, "reading_executed": False, "network_requests": 0, "cache_read": False,
                "authority_modified": False, "acquisition_queue_modified": False}
    manifest["batch_hash"] = fingerprint({"manifest": manifest, "selected": selected, "eligible_population": population})
    return {"manifest": manifest, "selected": selected, "eligible_population": population, "coverage": coverage, "exclusions": excluded}


def prepare_pilot(*, catalog, published_dir, dictionary, output_dir, as_of, readings=None, hardware_reviews=None,
                  seed=DEFAULT_SEED, size=100, control_target=10):
    catalog, published_dir, dictionary, output_dir = map(Path, (catalog, published_dir, dictionary, output_dir))
    require(all(path.is_absolute() for path in (catalog, published_dir, dictionary, output_dir)), "explicit_absolute_paths_required")
    require(not output_dir.exists() and not output_dir.is_symlink(), "output_directory_must_be_new")
    require(output_dir.parent.is_dir(), "output_parent_must_exist")
    output = output_dir.resolve()
    require(not output.is_relative_to(ROOT) or output.is_relative_to(ROOT / ".research"), "repository_output_must_be_private")
    for protected in (catalog.resolve(), published_dir.resolve(), dictionary.resolve()):
        require(not output.is_relative_to(protected) and not protected.is_relative_to(output), "output_overlaps_inputs")
    require(not output.is_relative_to(ROOT / ".research/hardware-fulltext"), "output_must_not_enter_acquisition_cache")
    file_hashes = {}
    def read(path, label):
        raw = _read_path(path)
        file_hashes[label] = hashlib.sha256(raw).hexdigest()
        return raw
    def table(name):
        directory = catalog / name
        paths = sorted(directory.glob("*.jsonl")) if directory.is_dir() else [catalog / (name + ".jsonl")]
        require(bool(paths), "canonical_table_required:" + name)
        return [row for path in paths for row in parse_jsonl(read(path, "catalog/" + str(path.relative_to(catalog))))[0]]
    def optional(path, label):
        if path is None:
            file_hashes[label] = None
            return []
        return parse_jsonl(read(Path(path), label))[0]
    readings_path = readings if readings is not None else (published_dir / "fulltext-readings.jsonl" if (published_dir / "fulltext-readings.jsonl").exists() else None)
    result = plan_pilot(works=table("works"), organizations=table("organizations"), links=table("work-organization-links"),
                        observations=parse_jsonl(read(published_dir / "source-observations.jsonl", "public/source-observations.jsonl"))[0],
                        scans=parse_jsonl(read(published_dir / "source-scans.jsonl", "public/source-scans.jsonl"))[0],
                        dictionary=json.loads(read(dictionary, "dictionary")),
                        readings=optional(readings_path, "readings"), hardware_reviews=optional(hardware_reviews, "hardware_reviews"),
                        as_of=as_of, seed=seed, size=size, control_target=control_target)
    payloads = {"pilot.jsonl": "".join(encode(row) + "\n" for row in result["selected"]),
                "eligible-population.jsonl": "".join(encode(row) + "\n" for row in result["eligible_population"]),
                "coverage.json": encode({"coverage": result["coverage"], "exclusions": result["exclusions"]}) + "\n"}
    manifest = {**result["manifest"], "input_file_content_hashes": file_hashes,
                "output_content_hashes": {name: hashlib.sha256(value.encode()).hexdigest() for name, value in payloads.items()}}
    # Pinned parent, exclusive names, private permissions. Manifest is last.
    parent_fd = _open_directory(output_dir.parent)
    output_fd = None
    try:
        os.mkdir(output_dir.name, mode=0o700, dir_fd=parent_fd)
        output_fd = os.open(output_dir.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        for name, value in {**payloads, "pilot-manifest.json": encode(manifest) + "\n"}.items():
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=output_fd)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(value)
    finally:
        if output_fd is not None:
            os.close(output_fd)
        os.close(parent_fd)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("catalog", "published-dir", "dictionary", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("readings", "hardware-reviews"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--size", type=int, default=100)
    args = parser.parse_args(argv)
    try:
        result = prepare_pilot(catalog=args.catalog, published_dir=args.published_dir, dictionary=args.dictionary,
                               output_dir=args.output_dir, readings=args.readings, hardware_reviews=args.hardware_reviews,
                               as_of=args.as_of, seed=args.seed, size=args.size)
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        print(encode({"prepared": False, "error": str(exc) if isinstance(exc, SnapshotError) else "pilot_input_or_output_failure"}))
        return 2
    print(encode({key: result[key] for key in ("batch_hash", "selected_count", "eligible_population_count", "shortfall", "reading_executed", "network_requests")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
