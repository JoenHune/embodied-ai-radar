"""Pure conference-release accounting; no collection, writes or inferred IDs.

First publication, first discovery and acceptance are separate clocks. A
retrieval timestamp or an early public date does not prove prior catalog
membership. All counters describe the supplied, source-verified sample unless
the corresponding track has a reconciled complete source snapshot.
"""
from __future__ import annotations

import calendar
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Shanghai")
BUCKETS = {
    "existing_work_accepted": "已有 work 获接收",
    "newly_discovered_prior_publication": "新发现，但此前已公开",
    "first_publication_in_release_window": "本次窗口首次公开",
    "identity_or_date_review": "身份 / 日期待核验",
}
ACCEPTED = {"accepted_peer_reviewed", "accepted_official", "Accept", "Accept (Poster)", "Accept (Oral)"}
OFFICIAL_DECISIONS = {"official_openreview_decision", "official_acceptance_decision", "official_conference_decision", "official_peer_review_decision"}


def _interval(value, precision=None):
    """Conservative local-calendar bounds; a month is not a guessed day."""
    if not isinstance(value, str) or precision in {"unknown", "undated"}:
        return None
    try:
        if precision == "year" or len(value) == 4:
            return date(int(value[:4]), 1, 1), date(int(value[:4]), 12, 31)
        if precision == "month" or len(value) == 7:
            year, month = map(int, value[:7].split("-"))
            return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
        if len(value) == 10:
            day = date.fromisoformat(value)
        else:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if instant.tzinfo is None:
                return None
            day = instant.astimezone(ZONE).date()
        return day, day
    except (ValueError, OverflowError):
        return None


def _url(value):
    try:
        parsed = urlsplit(value or "")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return None
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, "")).rstrip("/")
    except ValueError:
        return None


def _forum(url):
    parsed = urlsplit(url)
    if parsed.hostname == "openreview.net" and parsed.path == "/forum":
        forum = parse_qs(parsed.query).get("id", [None])[0]
        return "https://openreview.net/forum?" + urlencode({"id": forum}) if forum else None
    return url


def _stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()[:20]


def _track(version):
    value = str(version.get("track") or version.get("venue_scope") or "").lower()
    return "main" if value in {"main", "main_conference"} else "workshop" if "workshop" in value else "unknown"


def _date_proof(work, versions, sources):
    bounds = _interval(work.get("first_public_date"), work.get("first_public_date_precision"))
    if bounds is None:
        return None, [], "first_publication_date_unknown"
    evidence = []
    for sid in work.get("source_record_ids", []):
        source = sources.get(sid, {})
        if source.get("date_supersession") or not _url(source.get("url")):
            continue
        value = source.get("public_at") or source.get("published_at")
        source_bounds = _interval(value, source.get("public_at_precision", source.get("date_precision")))
        if source_bounds == bounds:
            evidence.append(sid)
    for version in versions:
        source = sources.get(version.get("source_record_id"), {})
        # An acceptance timestamp is not itself the first public release.
        if version.get("kind") not in {"preprint", "conference", "journal", "technical_report", "project"}:
            continue
        if _url(version.get("url")) and _url(source.get("url")) == _url(version.get("url")) and not source.get("date_supersession"):
            released = _interval(version.get("public_at") or version.get("published_at"), version.get("date_precision"))
            if released == bounds:
                evidence.append(version["source_record_id"])
            elif released and released[1] < bounds[0]:
                return None, [version["source_record_id"]], "earlier_public_version_requires_date_review"
    return (bounds, sorted(set(evidence)), None) if evidence else (None, [], "first_publication_lacks_dated_source")


def build_conference_changes(edition, works, manifestations, source_records, source_status=None, *,
                             historical_baseline=None, work_relations=None, aliases=None, as_of=None):
    """Return export-ready JSON without mutating any supplied object.

    Optional baseline: {as_of, work_ids, snapshot_id}; only IDs explicitly
    present prove existing catalog membership. Explicit first_seen_at or
    first_observed_at are also accepted (not ordinary retrieved_at/updated_at).
    ``as_of`` is the conference observation cutoff, not a stale corpus cutoff.
    """
    status = source_status or {}
    by_work = {row["work_id"]: row for row in works}
    sources = source_records if isinstance(source_records, dict) else {row["source_record_id"]: row for row in source_records}
    release = _interval(edition.get("notification_date")) if _url(edition.get("notification_date_source")) else None
    cutoff = _interval(as_of or status.get("checked_at"))
    # Aliases and explicit reviewed merges are identity evidence; titles are not.
    identity = defaultdict(set)
    for wid, work in by_work.items():
        identity[wid].add(wid)
        for alias in work.get("aliases", []):
            if isinstance(alias, str):
                identity[alias].add(wid)
    for row in aliases or []:
        if row.get("work_id") in by_work and row.get("alias"):
            identity[row["alias"]].add(row["work_id"])
    for row in work_relations or []:
        if row.get("relation") == "merged_into" and row.get("work_id") in by_work and row.get("previous_id") and row.get("review_id"):
            identity[row["previous_id"]].add(row["work_id"])

    def resolve(wid):
        matches = identity.get(wid, set())
        return next(iter(matches)) if len(matches) == 1 else None

    versions_by_work = defaultdict(list)
    for version in manifestations:
        wid = resolve(version.get("work_id"))
        if wid:
            versions_by_work[wid].append(version)
    baseline = historical_baseline or {}
    baseline_bounds = _interval(baseline.get("as_of")) if baseline.get("snapshot_id") else None
    baseline_ids = {resolve(wid) for wid in baseline.get("work_ids", [])} - {None}
    pending, event_candidates = [], defaultdict(list)
    for version in manifestations:
        if version.get("kind") != "conference" or str(version.get("venue", "")).casefold() != str(edition.get("venue", "")).casefold() or str(version.get("year")) != str(edition.get("year")):
            continue
        if version.get("edition_id") not in {None, edition.get("edition_id")}:
            continue
        acceptance = version.get("status") in ACCEPTED or version.get("publication_status") in ACCEPTED
        if not acceptance:
            continue
        owner = resolve(version.get("work_id"))
        if not owner or version.get("source_record_id") not in by_work[owner].get("source_record_ids", []):
            pending.append({"manifestation_id": version.get("manifestation_id"), "work_id": owner,
                            "reason": "canonical_identity_unresolved" if not owner else "acceptance_source_not_owned_by_work",
                            "source_url": _url(version.get("url"))})
            continue
        source = sources.get(version.get("source_record_id"), {})
        url = _url(version.get("url"))
        source_url = _url(source.get("url"))
        safe_source = bool(url and source_url and _forum(url) == _forum(source_url) and source.get("source_type") in OFFICIAL_DECISIONS)
        if source.get("source_type") == "official_openreview_decision":
            safe_source = safe_source and urlsplit(url or "").hostname == "openreview.net" and urlsplit(url or "").path == "/forum" and bool(parse_qs(urlsplit(url or "").query).get("id"))
        if not safe_source or version.get("peer_reviewed") is not True or str(version.get("decision_status", "accepted")).lower() in {"reject", "rejected", "withdrawn"}:
            pending.append({"manifestation_id": version.get("manifestation_id"), "work_id": resolve(version.get("work_id")), "reason": "acceptance_not_supported_by_official_source", "source_url": url})
            continue
        accepted = _interval(version.get("accepted_at"), version.get("accepted_date_precision", version.get("date_precision")))
        if cutoff and accepted and accepted[0] > cutoff[1]:
            pending.append({"manifestation_id": version.get("manifestation_id"), "work_id": resolve(version.get("work_id")), "reason": "acceptance_after_observation_cutoff", "source_url": url})
            continue
        track = _track(version)
        # Re-fetches / snapshot revisions of the same forum decision are one event.
        event_key = (track, _forum(url), "acceptance")
        event_candidates[event_key].append((version, accepted))

    events, grouped = [], defaultdict(list)
    for key, candidates in sorted(event_candidates.items()):
        work_ids = {resolve(v.get("work_id")) for v, _ in candidates}
        work_ids.discard(None)
        wid = next(iter(work_ids)) if len(work_ids) == 1 and all(resolve(v.get("work_id")) for v, _ in candidates) else None
        dates = {bounds for _, bounds in candidates if bounds}
        bounds = next(iter(dates)) if len(dates) == 1 else None
        dated_candidates = [pair for pair in candidates if pair[1] == bounds] if bounds else candidates
        chosen = sorted(dated_candidates, key=lambda pair: (str(pair[0].get("accepted_at") or ""), str(pair[0].get("manifestation_id") or "")))[0][0]
        decision_ids = sorted({str(v["decision_note_id"]) for v, _ in candidates if v.get("decision_note_id")} | {str(r["note_id"]) for v, _ in candidates for r in v.get("review_records", []) if r.get("kind") == "decision" and r.get("note_id")})
        event = {"event_id": "conference-acceptance:" + _stable([edition["edition_id"], *key]), "work_id": wid,
                 "track": key[0], "forum_url": key[1], "decision_ids": decision_ids, "accepted_at": chosen.get("accepted_at") if bounds else None,
                 "accepted_date_precision": chosen.get("accepted_date_precision", chosen.get("date_precision", "unknown")) if bounds else "unknown",
                 "local_acceptance_date": bounds[0].isoformat() if bounds and bounds[0] == bounds[1] else None,
                 "source_record_ids": sorted({v["source_record_id"] for v, _ in candidates}),
                 "manifestation_ids": sorted({v["manifestation_id"] for v, _ in candidates if v.get("manifestation_id")}),
                 "identity_candidates": sorted(work_ids), "identity_conflict": len(work_ids) > 1, "date_conflict": len(dates) > 1}
        events.append(event)
        grouped[(key[0], wid or "unresolved:" + event["event_id"])].append(event)

    items = []
    for (track, _), work_events in sorted(grouped.items()):
        wid = work_events[0]["work_id"]
        work = by_work.get(wid, {})
        reasons, proof_ids = [], []
        bucket = "identity_or_date_review"
        public, proof_ids, public_error = _date_proof(work, versions_by_work.get(wid, []), sources) if wid else (None, [], "canonical_identity_unresolved")
        discovery = []
        # A new source's first sighting is not necessarily the work's first
        # discovery: the work may already have other versions in the catalog.
        scoped_sources = [(sources[sid], sid) for sid in work.get("source_record_ids", []) if sid in sources and sources[sid].get("observation_scope") == "canonical_work"]
        for owner, label in [(work, "work_first_observation"), *scoped_sources]:
            for field in ["first_seen_at", "first_observed_at"]:
                bounds = _interval(owner.get(field), owner.get("first_seen_precision"))
                if bounds:
                    discovery.append((bounds, owner[field], label))
        first_seen = min(discovery, key=lambda item: (item[0], item[1])) if discovery else None
        accepted_bounds = [_interval(e["accepted_at"], e["accepted_date_precision"]) for e in work_events]
        if not wid:
            reasons.append("canonical_identity_unresolved")
        if public_error:
            reasons.append(public_error)
        if release is None:
            reasons.append("release_window_unknown")
        if cutoff is None:
            reasons.append("observation_cutoff_unknown")
        if any(value is None for value in accepted_bounds):
            reasons.append("individual_acceptance_date_unknown_or_conflicting")
        if track == "unknown":
            reasons.append("conference_track_unknown")
        if cutoff and first_seen and first_seen[0][1] > cutoff[1]:
            reasons.append("first_discovery_after_observation_cutoff")
        if cutoff and public and public[1] > cutoff[1]:
            reasons.append("public_date_not_yet_fully_observed")
        if release and cutoff and cutoff[1] < release[0]:
            reasons.append("observation_precedes_release_window")
        baseline_before = bool(release and baseline_bounds and baseline_bounds[1] < release[0] and wid in baseline_ids)
        if not reasons:
            known_before = baseline_before
            known_before = known_before or bool(first_seen and first_seen[0][1] < release[0])
            if public[1] < release[0]:
                if known_before:
                    bucket = "existing_work_accepted"
                elif first_seen and first_seen[0][0] >= release[0] and first_seen[0][1] <= cutoff[1]:
                    bucket = "newly_discovered_prior_publication"
                else:
                    reasons.append("first_discovery_or_prior_catalog_baseline_unknown")
            elif public[0] >= release[0]:
                bucket = "first_publication_in_release_window"
            else:
                reasons.append("public_date_precision_overlaps_release_boundary")
        items.append({"item_id": "conference-change:" + _stable([edition["edition_id"], track, wid or work_events[0]["event_id"]]),
                      "work_id": wid, "title": work.get("title") or "身份待核验的官方接收记录", "track": track, "category": bucket,
                      "relevance": work.get("relevance", {}).get("status", "unknown"),
                      "first_public_date": work.get("first_public_date"), "first_public_date_precision": work.get("first_public_date_precision", "unknown"),
                      "first_seen_at": first_seen[1] if first_seen else None, "discovery_basis": "historical_baseline" if baseline_before else first_seen[2] if first_seen else "unknown",
                      "baseline_snapshot_id": baseline.get("snapshot_id") if baseline_before else None,
                      "baseline_as_of": baseline.get("as_of") if baseline_before else None,
                      "accepted_at": next((e["accepted_at"] for e in work_events if e["accepted_at"]), None),
                      "accepted_date_precision": next((e["accepted_date_precision"] for e in work_events if e["accepted_at"]), "unknown"),
                      "event_ids": sorted(e["event_id"] for e in work_events), "event_count": len(work_events),
                      "source_record_ids": sorted(set(proof_ids) | {sid for e in work_events for sid in e["source_record_ids"]}),
                      "official_urls": sorted({e["forum_url"] for e in work_events}), "public_source_urls": sorted({_url(sources[sid].get("url")) for sid in proof_ids if _url(sources[sid].get("url"))}), "reasons": sorted(set(reasons)),
                      "database_path": "/database/?" + urlencode({"ids": wid, "relevance": "all"}) if wid else None})

    tracks = []
    for track, label in [("main", "主会"), ("workshop", "Workshop"), ("unknown", "轨道待核验")]:
        track_events = [e for e in events if e["track"] == track]
        track_items = [r for r in items if r["track"] == track]
        # This edition's official count covers only its registered track.
        # Workshops require their own registered edition/source, never the
        # main-conference count borrowed as a denominator.
        track_status = status if track == edition.get("scope", "main") else {}
        expected = track_status.get("expected_count")
        forums = {e["forum_url"] for e in track_events}
        source_url = _url(track_status.get("source_url"))
        parsed_source = urlsplit(source_url or "")
        registered_source = bool(track_status.get("edition_id") == edition.get("edition_id")
                                 and str(track_status.get("year", edition.get("year"))) == str(edition.get("year"))
                                 and track_status.get("source_kind") == "official_openreview"
                                 and parsed_source.scheme == "https" and parsed_source.hostname == "api2.openreview.net" and parsed_source.path == "/notes"
                                 and edition.get("accepted_venue_id")
                                 and parse_qs(parsed_source.query).get("content.venueid") == [edition["accepted_venue_id"]])
        complete = bool(registered_source and track_status.get("complete") is True and type(expected) is int and expected > 0
                        and type(track_status.get("fetched_count")) is int and expected == track_status["fetched_count"] == len(forums))
        coverage = "complete" if complete else "partial" if track_events else "unknown"
        tracks.append({"track": track, "label": label, "coverage_status": coverage,
                       "source_status": track_status.get("status", "not_registered"), "expected_acceptances": expected if registered_source and type(expected) is int else None,
                       "observed_work_count": len({r["work_id"] for r in track_items if r["work_id"]}), "observed_event_count": len(track_events),
                       "display_work_count": len({r["work_id"] for r in track_items if r["work_id"]}) if track_items or complete else None,
                       "display_event_count": len(track_events) if track_events or complete else None,
                       "unresolved_identity_events": sum(e["work_id"] is None for e in track_events),
                       "allow_conference_share": complete and not any(r["category"] == "identity_or_date_review" for r in track_items),
                       "categories": [{"category": key, "label": text, "item_count": sum(r["category"] == key for r in track_items) if track_items or complete else None,
                                       "work_ids": sorted(r["work_id"] for r in track_items if r["category"] == key and r["work_id"]),
                                       "event_count": sum(r["event_count"] for r in track_items if r["category"] == key) if track_items or complete else None} for key, text in BUCKETS.items()],
                       "items": track_items})
    pending.sort(key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False))
    return {"schema_version": "1.0", "edition_id": edition["edition_id"], "venue": edition.get("venue"), "year": edition.get("year"),
            "observation_as_of": as_of or status.get("checked_at"), "release_window": {"from": edition.get("notification_date"), "source_url": edition.get("notification_date_source"), "is_individual_acceptance_date": False},
            "tracks": tracks, "events": events, "acceptance_review_queue": pending,
            "method": {"unit": "canonical_work_and_official_acceptance_event_separate", "first_seen_policy": "explicit_first_observation_or_dated_catalog_baseline_only",
                       "unknown_is_not_zero": True, "no_acceptance_rate": True, "no_relevance_promotion": True,
                       "note": "接收只增加验证事件；首次公开月份不变。新发现不等于新研究；缺历史发现证据时保留待核验。"}}
