#!/usr/bin/env python3
"""Collect public main-conference acceptances and public forum evidence.

Uses the official API v2 venueid query and paginated forum queries, without
credentials or attempts to solve/bypass access challenges. Incomplete responses
never replace an existing acceptance snapshot. An official API export can be
imported offline; see data/conferences/README.md for its envelope contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "conference-editions.json"
USER_AGENT = "embodied-ai-radar/3.0 (public scholarly metadata collection)"


class CollectionError(Exception):
    def __init__(self, status: str, reason: str, *, count: int | None = None,
                 fetched: int = 0, endpoint: str | None = None):
        super().__init__(reason)
        self.status, self.reason = status, reason
        self.count, self.fetched, self.endpoint = count, fetched, endpoint


def unwrap(value: Any) -> Any:
    return value.get("value") if isinstance(value, dict) and "value" in value else value


def fields(note: dict) -> dict:
    return {key: unwrap(value) for key, value in (note.get("content") or {}).items()}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def note_timestamp(note: dict, keys: tuple[str, ...]) -> tuple[str | None, str]:
    for key in keys:
        value = note.get(key)
        if isinstance(value, (int, float)) and value > 0:
            try:
                return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"), key
            except (OverflowError, OSError, ValueError):
                continue
    return None, "unknown"


def official_api_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme == "https" and parsed.hostname == "api2.openreview.net" and not parsed.username


def request_json(url: str) -> dict:
    if not official_api_url(url):
        raise CollectionError("invalid_source", "Only the official HTTPS API v2 endpoint is allowed.")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not retry a challenge or persist challenge URLs/tokens.
        status = "access_blocked" if exc.code in {401, 403} else "rate_limited" if exc.code == 429 else "source_error"
        raise CollectionError(status, f"Official API returned HTTP {exc.code}.", endpoint=url) from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise CollectionError("source_error", f"Official API request failed ({type(exc).__name__}).", endpoint=url) from exc
    if not isinstance(payload, dict):
        raise CollectionError("invalid_response", "API response must be an object.", endpoint=url)
    return payload


def endpoint(edition: dict, route: str, **params: Any) -> str:
    return edition["openreview_api_url"].rstrip("/") + "/" + route + "?" + urllib.parse.urlencode(params)


def validate_group(group: dict, edition: dict) -> dict:
    if group.get("id") != edition["openreview_group_id"] or "everyone" not in (group.get("readers") or []):
        raise CollectionError("invalid_metadata", "Conference metadata is not the registered public main-conference group.")
    content = fields(group)
    if not content.get("accept_decision_options") or not content.get("decision_field_name"):
        raise CollectionError("invalid_metadata", "Conference metadata does not identify its acceptance decisions.")
    return content


def public_note(note: dict) -> bool:
    return isinstance(note, dict) and "everyone" in (note.get("readers") or []) and not note.get("ddate")


def scope_of(note: dict, edition: dict) -> str:
    content = fields(note)
    venue_id = str(content.get("venueid") or "")
    if venue_id == edition["accepted_venue_id"]:
        return "main"
    if "workshop" in venue_id.lower():
        return "workshop"
    if str(edition["year"]) in str(content.get("venue") or "") and "corl" in str(content.get("venue") or "").lower():
        return "author_claim"
    return "other_venue"


def paginate(edition: dict, params: dict, getter: Callable[[str], dict], *, page_size: int = 1000) -> tuple[list[dict], int]:
    offset, expected, rows, seen = 0, None, [], set()
    while expected is None or offset < expected:
        url = endpoint(edition, "notes", **params, limit=page_size, offset=offset)
        try:
            payload = getter(url)
        except CollectionError as exc:
            exc.count, exc.fetched = expected, len(rows)
            raise
        batch, count = payload.get("notes"), payload.get("count")
        if not isinstance(batch, list) or not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise CollectionError("incomplete", "Missing notes or a verifiable API count.", count=expected, fetched=len(rows), endpoint=url)
        if expected is not None and count != expected:
            raise CollectionError("incomplete", "API count changed while paginating; retry next collection.", count=count, fetched=len(rows), endpoint=url)
        expected = count
        if not batch and offset < expected:
            raise CollectionError("incomplete", "Pagination ended before the official count.", count=count, fetched=len(rows), endpoint=url)
        for note in batch:
            if not isinstance(note, dict) or not note.get("id") or note["id"] in seen:
                raise CollectionError("incomplete", "Duplicate or invalid note in pagination.", count=count, fetched=len(rows), endpoint=url)
            seen.add(note["id"])
            rows.append(note)
        offset += len(batch)
        if offset > expected:
            raise CollectionError("incomplete", "Received more notes than the official count.", count=count, fetched=len(rows), endpoint=url)
    return rows, expected or 0


def invitation_ids(note: dict) -> list[str]:
    value = note.get("invitations") or ([note["invitation"]] if note.get("invitation") else [])
    return [item for item in value if isinstance(item, str)]


def reply_kind(note: dict, metadata: dict, edition: dict) -> str | None:
    official = edition["openreview_group_id"] + "/"
    mapping = {metadata.get("review_name", "Official_Review"): "review",
               metadata.get("meta_review_name", "Meta_Review"): "meta_review",
               metadata.get("decision_name", "Decision"): "decision",
               "Rebuttal": "rebuttal", "Official_Comment": "comment", "Author_Response": "rebuttal"}
    for invitation_id in invitation_ids(note):
        if invitation_id.startswith(official) and invitation_id.rsplit("/-/", 1)[-1] in mapping:
            return mapping[invitation_id.rsplit("/-/", 1)[-1]]
    return None


def schema_for_field(invitation: dict | None, field: str) -> dict | None:
    if not invitation:
        return None
    content_schema = (invitation.get("edit") or {}).get("note", {}).get("content", {})
    candidate = content_schema.get(field)
    return candidate if isinstance(candidate, dict) else None


def normalize_submission(note: dict, replies: list[dict], metadata: dict, edition: dict,
                         invitations: dict[str, dict], observed_at: str) -> dict:
    content, forum_id = fields(note), note.get("forum") or note["id"]
    if scope_of(note, edition) != "main" or not public_note(note):
        raise CollectionError("invalid_response", "Only public main-conference accepted notes may become records.")
    if forum_id != note["id"] or not isinstance(content.get("title"), str) or not content["title"].strip():
        raise CollectionError("invalid_response", "Submission lacks a title or is not a forum root.")
    authors = content.get("authors") or []
    if not isinstance(authors, list) or any(not isinstance(author, str) for author in authors):
        raise CollectionError("invalid_response", "Invalid public author list.")
    review_records, decisions = [], []
    for reply in replies:
        if reply.get("forum") != forum_id or not public_note(reply):
            continue
        kind = reply_kind(reply, metadata, edition)
        if not kind:
            continue
        raw_fields = fields(reply)
        published_at, published_basis = note_timestamp(reply, ("pdate",))
        created_at, created_basis = note_timestamp(reply, ("cdate", "tcdate"))
        native_scores = {}
        for role, key in [("rating", metadata.get("review_rating")), ("confidence", metadata.get("review_confidence"))]:
            if key and key in raw_fields:
                definitions = [{"invitation_id": invitation_id, "schema": schema_for_field(invitations.get(invitation_id), key)}
                               for invitation_id in invitation_ids(reply) if schema_for_field(invitations.get(invitation_id), key)]
                native_scores[role] = {"field": key, "value": raw_fields[key], "scale_definitions": definitions,
                                       "scale_status": "official_schema" if definitions else "unavailable", "normalized": False}
        row = {"note_id": reply["id"], "forum_id": forum_id, "kind": kind,
               "url": "https://openreview.net/forum?id=" + urllib.parse.quote(forum_id) + "&noteId=" + urllib.parse.quote(reply["id"]),
               "invitation_ids": invitation_ids(reply), "fields": raw_fields,
               "created_at": created_at, "created_at_basis": created_basis,
               "published_at": published_at, "published_at_basis": published_basis,
               "native_scores": native_scores}
        review_records.append(row)
        if kind == "decision":
            decisions.append((reply, raw_fields.get(metadata["decision_field_name"])))
    accepted_options = set(metadata["accept_decision_options"])
    accepted = [(reply, value) for reply, value in decisions if value in accepted_options]
    conflicts = [value for _, value in decisions if value and value not in accepted_options]
    if conflicts:
        raise CollectionError("conflicting_decision", "Accepted venueid conflicts with a public main-conference decision.")
    accepted.sort(key=lambda item: item[0].get("cdate", item[0].get("tcdate", 0)))
    decision = accepted[0][0] if accepted else None
    accepted_at, accepted_basis = note_timestamp(decision or {}, ("cdate", "tcdate"))
    published_at, published_basis = note_timestamp(note, ("pdate",))
    id_text = " ".join(str(content.get(key) or "") for key in ("arxiv_id", "arxiv", "arxiv_url", "external_links"))
    arxiv = re.search(r"(?:arxiv:|arxiv\.org/(?:abs|pdf)/)?(\d{4}\.\d{4,5})(?:v\d+)?", id_text, re.I)
    doi = str(content.get("doi") or "").strip().removeprefix("https://doi.org/").lower() or None
    forum_url = "https://openreview.net/forum?id=" + urllib.parse.quote(forum_id)
    return {
        "edition_id": edition["edition_id"], "venue": edition["venue"], "year": edition["year"],
        "venue_scope": "main", "source_kind": "official_openreview", "forum_id": forum_id, "note_id": note["id"],
        "title": content["title"].strip(), "authors": authors, "abstract": content.get("abstract") or "",
        "arxiv_id": arxiv.group(1) if arxiv else None, "doi": doi,
        "accepted_at": accepted_at, "accepted_at_precision": "millisecond" if accepted_at else "unknown",
        "accepted_at_basis": "decision_note_" + accepted_basis if accepted_at else "unknown",
        "published_at": published_at, "published_at_basis": published_basis,
        # pdate belongs to this verified public root note. Submission cdate /
        # tcdate and a decision's creation time are not public release dates.
        "root_note_public": True, "root_note_id": note["id"],
        "first_public_at": published_at,
        "first_public_at_precision": "millisecond" if published_at else "unknown",
        "first_public_at_basis": "public_root_note_pdate" if published_at else "unknown",
        "observed_at": observed_at, "last_observed_at": observed_at,
        "decision_status": "accepted", "decision_label": accepted[0][1] if accepted else content.get("venue"),
        "decision_evidence": "official_decision_note" if accepted else "official_accepted_venueid",
        "decision_url": forum_url + "&noteId=" + urllib.parse.quote(decision["id"]) if decision else forum_url,
        "forum_url": forum_url, "review_records": sorted(review_records, key=lambda row: row["note_id"]),
        "source_urls": sorted({forum_url, endpoint(edition, "notes", id=note["id"]),
                               endpoint(edition, "notes", forum=forum_id)}),
    }


def collect_live(edition: dict, getter: Callable[[str], dict] = request_json,
                 metadata_sink: Callable[[dict], None] | None = None) -> tuple[dict, list[dict], dict[str, list[dict]], dict[str, dict], int]:
    group_url = endpoint(edition, "groups", id=edition["openreview_group_id"])
    groups = getter(group_url).get("groups") or []
    if len(groups) != 1:
        raise CollectionError("invalid_metadata", "Official group query did not return exactly one group.")
    group = groups[0]
    validate_group(group, edition)
    if metadata_sink:
        metadata_sink(group)
    notes, expected = paginate(edition, {"content.venueid": edition["accepted_venue_id"]}, getter)
    forums, invitations = {}, {}
    for note in notes:
        forum_id = note.get("forum") or note["id"]
        try:
            replies, _ = paginate(edition, {"forum": forum_id}, getter)
        except CollectionError as exc:
            exc.count, exc.fetched = expected, len(notes)
            raise
        forums[forum_id] = replies
        for reply in replies:
            if not public_note(reply):
                continue
            for invitation_id in invitation_ids(reply):
                if invitation_id in invitations or not invitation_id.startswith(edition["openreview_group_id"] + "/"):
                    continue
                url = endpoint(edition, "invitations", id=invitation_id)
                try:
                    values = getter(url).get("invitations") or []
                    invitations[invitation_id] = next((row for row in values if row.get("id") == invitation_id), {})
                except CollectionError as exc:
                    if exc.status == "access_blocked":
                        exc.count, exc.fetched = expected, len(notes)
                        raise
                    # Missing schema does not invent a score scale or drop a public review.
                    invitations[invitation_id] = {}
    return group, notes, forums, invitations, expected


def load_export(path: Path, edition: dict) -> tuple[dict, list[dict], dict[str, list[dict]], dict[str, dict], int]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict) or payload.get("schema_version") != "openreview-public-export-v1":
        raise CollectionError("invalid_export", "Expected an openreview-public-export-v1 envelope, not third-party normalized records.")
    source_url = payload.get("source_url", "")
    params = urllib.parse.parse_qs(urllib.parse.urlsplit(source_url).query)
    if not official_api_url(source_url) or params.get("content.venueid") != [edition["accepted_venue_id"]]:
        raise CollectionError("invalid_export", "Export source URL must identify the official accepted-venue query.")
    group = payload.get("group") or {}
    validate_group(group, edition)
    notes, count = payload.get("notes"), payload.get("count")
    if payload.get("complete") is not True or not isinstance(notes, list) or not isinstance(count, int) or isinstance(count, bool) or count < 0 or len(notes) != count:
        raise CollectionError("incomplete", "Official export lacks a complete acceptance count.", count=count if type(count) is int else None,
                              fetched=len(notes) if isinstance(notes, list) else 0)
    forum_notes = payload.get("forum_notes") or {}
    forums = {}
    for note in notes:
        forum_id = note.get("forum") or note.get("id")
        page = forum_notes.get(forum_id) or {}
        batch = page.get("notes")
        if page.get("complete") is not True or not isinstance(batch, list) or type(page.get("count")) is not int or page.get("count") != len(batch):
            raise CollectionError("incomplete", "Official export is missing complete forum replies.", count=count, fetched=len(notes))
        ids = [item.get("id") for item in batch if isinstance(item, dict)]
        if len(ids) != len(batch) or not all(ids) or len(ids) != len(set(ids)):
            raise CollectionError("incomplete", "Official export contains duplicate or invalid forum notes.", count=count, fetched=len(notes))
        if not any(item.get("id") == forum_id for item in batch):
            raise CollectionError("incomplete", "Official forum export must include its root submission.", count=count, fetched=len(notes))
        forums[forum_id] = batch
    invitations = {row["id"]: row for row in payload.get("invitations", []) if row.get("id")}
    return group, notes, forums, invitations, count


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text)
    temporary.replace(path)


def write_json(path: Path, value: dict) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def save_group(output: Path, group: dict, edition: dict, checked_at: str) -> None:
    metadata = validate_group(group, edition)
    keys = ("title", "subtitle", "website", "public_submissions", "review_name", "review_rating", "review_confidence", "meta_review_name", "decision_name", "decision_field_name", "accept_decision_options", "decision_heading_map")
    write_json(output / "group-metadata.json", {"id": group["id"], "checked_at": checked_at,
                "source_url": endpoint(edition, "groups", id=group["id"]),
                "content": {key: metadata[key] for key in keys if key in metadata}})


def save_failure(output: Path, edition: dict, error: CollectionError, checked_at: str) -> dict:
    previous = json.loads((output / "source-status.json").read_text()) if (output / "source-status.json").exists() else {}
    records = output / "records.jsonl"
    retained = sum(1 for line in records.read_text().splitlines() if line.strip()) if records.exists() else 0
    # The initialized empty file denotes no verified snapshot, never a verified zero-paper result.
    if not records.exists():
        atomic_text(records, "")
    status = {
        "edition_id": edition["edition_id"], "source_kind": "official_openreview",
        "source_url": endpoint(edition, "notes", **{"content.venueid": edition["accepted_venue_id"]}),
        "expected_count": error.count, "fetched_count": error.fetched, "complete": False,
        "checked_at": checked_at, "status": error.status, "reason": error.reason,
        "records_retained": retained, "snapshot_preserved": retained > 0,
        "last_successful_at": previous.get("last_successful_at"),
        "last_successful_count": previous.get("last_successful_count"),
        "consecutive_failures": previous.get("consecutive_failures", 0) + 1,
        "stale_warning": previous.get("consecutive_failures", 0) + 1 >= 2,
        "failed_endpoint": error.endpoint,
    }
    write_json(output / "source-status.json", status)
    return status


def run_collection(edition: dict, output: Path, *, official_export: Path | None = None,
                   getter: Callable[[str], dict] = request_json, checked_at: str | None = None) -> dict:
    checked_at = checked_at or utc_now()
    try:
        group, notes, forums, invitations, expected = load_export(official_export, edition) if official_export else collect_live(
            edition, getter, metadata_sink=lambda group: save_group(output, group, edition, checked_at))
        metadata = validate_group(group, edition)
        if official_export:
            save_group(output, group, edition, checked_at)
        if not expected:
            raise CollectionError("not_published", "The accepted-venue query is empty; publication completeness is unverified.", count=0)
        records, rejected, seen = [], [], set()
        for note in notes:
            if not isinstance(note, dict) or not note.get("id") or note["id"] in seen:
                raise CollectionError("incomplete", "Duplicate or invalid exported note.", count=expected, fetched=len(records))
            seen.add(note["id"])
            scope = scope_of(note, edition)
            if scope != "main" or not public_note(note):
                # Do not persist private titles, author identities, or review text.
                rejected.append({"note_id": note["id"] if public_note(note) else None,
                                 "venue_scope": scope, "reason": "not_main_acceptance" if scope != "main" else "not_public"})
                continue
            records.append(normalize_submission(note, forums[note.get("forum") or note["id"]], metadata, edition, invitations, checked_at))
        if rejected or len(records) != expected:
            write_json(output / "validation-rejections.json", {"checked_at": checked_at, "records": rejected})
            raise CollectionError("incomplete", "Accepted-venue response includes non-main, unverified, or non-public notes.", count=expected, fetched=len(records))
        old_records = {row["forum_id"]: row for row in (json.loads(line) for line in (output / "records.jsonl").read_text().splitlines() if line)} if (output / "records.jsonl").exists() else {}
        for row in records:
            if row["forum_id"] in old_records:
                row["observed_at"] = old_records[row["forum_id"]]["observed_at"]
        records.sort(key=lambda row: row["forum_id"])
        body = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records)
        atomic_text(output / "records.jsonl", body)
        status = {
            "edition_id": edition["edition_id"], "source_kind": "official_openreview",
            "source_url": endpoint(edition, "notes", **{"content.venueid": edition["accepted_venue_id"]}),
            "expected_count": expected, "fetched_count": len(records), "complete": True,
            "checked_at": checked_at, "status": "complete", "reason": None,
            "records_retained": len(records), "snapshot_preserved": False,
            "last_successful_at": checked_at, "last_successful_count": len(records),
            "consecutive_failures": 0, "stale_warning": False,
            "snapshot_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "retrieval_mode": "official_export" if official_export else "public_api",
            "review_scale_complete": all(score["scale_status"] == "official_schema" for row in records for review in row["review_records"] for score in review["native_scores"].values()),
            "public_forums_complete": True,
        }
        write_json(output / "source-status.json", status)
        return status
    except CollectionError as exc:
        return save_failure(output, edition, exc, checked_at)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return save_failure(output, edition, CollectionError("invalid_response", f"Collection validation failed ({type(exc).__name__})."), checked_at)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edition", default="corl-2026")
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--official-export", type=Path, help="Import an official public API export envelope; never trusts mirror lists.")
    parser.add_argument("--require-complete", action="store_true", help="Exit nonzero when the source is blocked or incomplete.")
    args = parser.parse_args()
    edition = next((row for row in json.loads(REGISTRY.read_text())["editions"] if row["edition_id"] == args.edition), None)
    if edition is None:
        parser.error("Edition is not registered.")
    output = args.output_directory or ROOT / edition["output_directory"]
    status = run_collection(edition, output, official_export=args.official_export)
    print(json.dumps(status, ensure_ascii=False))
    return int(args.require_complete and not status["complete"])


if __name__ == "__main__":
    sys.exit(main())
