"""Import explicit official status notices without removing research history.

Staging: research-status-additions.jsonl (or its read_table shards). An addition
contains the notice and an attached source_record. Official source content is
reviewed upstream; this importer checks the declared official source type,
public URL, hard work identity, date consistency and immutable IDs. It does not
infer a withdrawal/retraction from keywords or decide its temporal effect.

All records are preflighted before copy-on-write output is assembled. There are
no network requests or writes, and all existing tables/versions are preserved.
"""
from __future__ import annotations

import copy
import ipaddress
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator

try:
    from catalog_store import fingerprint, read_table
except ModuleNotFoundError:
    from scripts.catalog_store import fingerprint, read_table

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "config/research-status.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def _url(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("research_status_invalid_source_url")
    parsed = urlsplit(value)
    host = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not host or parsed.username is not None or parsed.password is not None:
        raise ValueError("research_status_invalid_source_url")
    if host == "localhost" or host.endswith((".localhost", ".local")):
        raise ValueError("research_status_nonpublic_source_url")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("research_status_nonpublic_source_url")
    return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower(), fragment="").geturl().rstrip("/")


def _utc(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value):
        raise ValueError("research_status_observation_must_be_utc")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("research_status_invalid_timestamp") from exc
    return result


def _publication_start(value, precision):
    try:
        if precision == "second":
            return _utc(value)
        if precision == "day" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if precision == "month" and re.fullmatch(r"\d{4}-\d{2}(?:-01)?", value):
            return datetime.strptime(value[:7], "%Y-%m").replace(tzinfo=timezone.utc)
        if precision == "year" and re.fullmatch(r"\d{4}(?:-01-01)?", value):
            return datetime(int(value[:4]), 1, 1, tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("research_status_invalid_publication_date") from exc
    raise ValueError("research_status_date_precision_mismatch")


def _arxiv(value):
    if not isinstance(value, str):
        return None
    value = re.sub(r"^arxiv:", "", value.strip(), flags=re.I)
    value = re.sub(r"(?:v\d+)?(?:\.pdf)?$", "", value, flags=re.I)
    return value.lower() if re.fullmatch(r"(?:\d{4}\.\d{4,5}|[A-Za-z.-]+/\d{7})", value) else None


def _doi(value):
    if not isinstance(value, str):
        return None
    value = re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", "", value.strip(), flags=re.I)
    return value.lower() if re.fullmatch(r"10\.\d{4,9}/\S+", value) else None


def _index(rows, key):
    result = {}
    for row in rows:
        identity = row.get(key)
        if identity in result and fingerprint(result[identity]) != fingerprint(row):
            raise ValueError("research_status_conflicting_existing_" + key)
        result[identity] = row
    return result


def _resolver(payload, works):
    aliases = defaultdict(set)
    for wid, work in works.items():
        aliases[wid].add(wid)
        for alias in work.get("aliases", []):
            if isinstance(alias, str):
                aliases[alias].add(wid)
    for row in payload.get("work-aliases", []):
        if row.get("work_id") in works and isinstance(row.get("alias"), str):
            aliases[row["alias"]].add(row["work_id"])
    def resolve(identifier):
        targets = aliases.get(identifier, set())
        if len(targets) != 1:
            raise ValueError("research_status_unknown_or_ambiguous_work")
        return next(iter(targets))
    return resolve, aliases


def _verify_identity(work, source, resolve, aliases, existing_sources, manifestations):
    wid = work["work_id"]
    identifiers = work.get("identifiers") or {}
    names = [alias for alias, targets in aliases.items() if wid in targets]
    arxiv_ids = {identifier for name in [identifiers.get("arxiv"), *names] if (identifier := _arxiv(name))}
    dois = {identifier for name in [identifiers.get("doi"), *names] if (identifier := _doi(name))}
    parsed = urlsplit(source["url"])
    arxiv_url = None
    if parsed.hostname in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
        match = re.fullmatch(r"/(?:abs|pdf|html)/(.+?)/?", unquote(parsed.path))
        arxiv_url = _arxiv(match.group(1)) if match else None
        if arxiv_url not in arxiv_ids:
            raise ValueError("research_status_source_work_identity_mismatch")
    if source["source_type"] == "official_arxiv_status_notice" and not arxiv_url:
        raise ValueError("research_status_arxiv_source_must_be_official")
    raw, explicit = source["raw"], False
    if "work_id" in raw:
        if not isinstance(raw["work_id"], str) or resolve(raw["work_id"]) != wid:
            raise ValueError("research_status_source_work_identity_mismatch")
        explicit = True
    if "work_identifiers" in raw:
        subject = raw["work_identifiers"]
        if not isinstance(subject, dict) or not subject or set(subject) - {"arxiv", "doi"}:
            raise ValueError("research_status_invalid_source_work_identifiers")
        for kind, value in subject.items():
            normalized = _arxiv(value) if kind == "arxiv" else _doi(value)
            if not normalized or normalized not in (arxiv_ids if kind == "arxiv" else dois):
                raise ValueError("research_status_source_work_identity_mismatch")
        explicit = True
    if arxiv_url or explicit:
        return
    # A publisher's notice can have its own DOI: an explicit raw subject above
    # takes precedence. Without one, only a DOI naming this work is sufficient.
    doi_url = _doi(source["url"])
    if doi_url and doi_url in dois:
        return
    known_urls = {_url(row["url"]) for row in manifestations if row.get("work_id") == wid and row.get("url")}
    known_urls.update(_url(existing_sources[sid]["url"]) for sid in work.get("source_record_ids", [])
                      if sid in existing_sources and existing_sources[sid].get("url"))
    if _url(source["url"]) not in known_urls:
        raise ValueError("research_status_source_has_no_hard_work_identity")


def _immutable_put(index, identity, value, kind):
    if identity in index:
        existing = index[identity]
        # The catalogue finalizer may annotate relevance without changing the
        # official notice. Core event fields remain byte-semantically fixed.
        if kind == "event_id":
            existing = {key: val for key, val in existing.items() if key not in {"research_eligible", "review_required"}}
        if fingerprint(existing) != fingerprint(value):
            raise ValueError("research_status_conflicting_" + kind)
    index.setdefault(identity, value)


def apply_research_status_additions(payload: dict, additions: list[dict]) -> dict:
    """Preflight a batch, then return copy-on-write tables; never mutate input."""
    if not isinstance(additions, list):
        raise ValueError("research_status_additions_must_be_a_list")
    works = _index(payload.get("works", []), "work_id")
    sources = _index(payload.get("source-records", []), "source_record_id")
    events = _index(payload.get("evidence-events", []), "event_id")
    resolve, aliases = _resolver(payload, works)
    notices = {}
    for wid, work in works.items():
        existing = work.get("research_status_notices", [])
        if not isinstance(existing, list):
            raise ValueError("research_status_existing_notices_must_be_a_list")
        for notice in existing:
            if notice.get("work_id") != wid:
                raise ValueError("research_status_existing_notice_work_mismatch")
            _immutable_put(notices, notice["notice_id"], notice, "notice_id")
    planned_sources, planned_events, planned_notices = dict(sources), dict(events), dict(notices)
    prepared = []
    for incoming in additions:
        if not VALIDATOR.is_valid(incoming):
            raise ValueError("research_status_schema_validation_failed")
        try:
            json.dumps(incoming, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("research_status_source_metadata_must_be_json") from exc
        notice = copy.deepcopy({key: value for key, value in incoming.items() if key != "source_record"})
        notice["work_id"] = resolve(notice["work_id"])
        work = works[notice["work_id"]]
        source = copy.deepcopy(incoming["source_record"])
        sid = source["source_record_id"]
        if sid not in notice["source_record_ids"] or _url(source["url"]) != _url(notice["source_url"]):
            raise ValueError("research_status_source_url_or_id_mismatch")
        observed = _utc(source["observed_at"])
        public = _publication_start(notice["public_at"], notice["date_precision"])
        if public > observed:
            raise ValueError("research_status_publication_after_observation")
        if source["published_at"] != notice["public_at"] or source.get("date_precision", notice["date_precision"]) != notice["date_precision"]:
            raise ValueError("research_status_source_date_mismatch")
        if "retrieved_at" in source and _utc(source["retrieved_at"]) != observed:
            raise ValueError("research_status_source_observation_mismatch")
        source.setdefault("date_precision", notice["date_precision"])
        source.setdefault("retrieved_at", source["observed_at"])
        _verify_identity(work, source, resolve, aliases, sources, payload.get("manifestations", []))
        for identifier in notice["source_record_ids"]:
            if identifier == sid:
                continue
            other = sources.get(identifier)
            if not other or identifier not in work.get("source_record_ids", []) or _url(other.get("url")) != _url(notice["source_url"]):
                raise ValueError("research_status_source_not_owned_by_work")
        _immutable_put(planned_sources, sid, source, "source_record_id")
        _immutable_put(planned_notices, notice["notice_id"], notice, "notice_id")
        event_id = "event:research-status:" + fingerprint(notice["notice_id"])[:24]
        raw_title = source["raw"].get("title")
        event = {"event_id": event_id, "work_id": notice["work_id"], "event_type": notice["event_type"], "scope": "work",
                 "title": raw_title if isinstance(raw_title, str) and raw_title.strip() else notice["summary_zh"],
                 "summary_zh": notice["summary_zh"], "url": notice["source_url"], "source_url": notice["source_url"],
                 "public_at": notice["public_at"], "published_at": notice["public_at"], "occurred_at": notice["public_at"],
                 "observed_at": source["observed_at"],
                 "date_precision": notice["date_precision"], "source_record_id": sid, "source_record_ids": copy.deepcopy(notice["source_record_ids"]),
                 "research_status_notice_id": notice["notice_id"], "review_status": "verified"}
        _immutable_put(planned_events, event_id, event, "event_id")
        provenance = [{"work_id": notice["work_id"], "field": "research_status_notices", "source_record_id": identifier,
                       "observed_at": source["observed_at"], "basis": "verified_official_research_status_notice",
                       "research_status_notice_id": notice["notice_id"]} for identifier in notice["source_record_ids"]]
        prepared.append((notice, provenance))
    # No input object has been changed, including when a later record failed.
    result = dict(payload)
    result["works"] = list(payload.get("works", []))
    result["source-records"] = [*payload.get("source-records", []), *(row for sid, row in planned_sources.items() if sid not in sources)]
    result["evidence-events"] = [*payload.get("evidence-events", []), *(row for eid, row in planned_events.items() if eid not in events)]
    result["field-provenance"] = list(payload.get("field-provenance", []))
    provenance_keys = {fingerprint(row) for row in result["field-provenance"]}
    edited, positions = {}, {row["work_id"]: index for index, row in enumerate(result["works"])}
    for notice, provenance in prepared:
        wid = notice["work_id"]
        if wid not in edited:
            edited[wid] = copy.deepcopy(works[wid])
            result["works"][positions[wid]] = edited[wid]
        work = edited[wid]
        work.setdefault("research_status_notices", [])
        if not any(row["notice_id"] == notice["notice_id"] for row in work["research_status_notices"]):
            work["research_status_notices"].append(notice)
        work["source_record_ids"] = list(dict.fromkeys([*work.get("source_record_ids", []), *notice["source_record_ids"]]))
        for row in provenance:
            key = fingerprint(row)
            if key not in provenance_keys:
                result["field-provenance"].append(row)
                provenance_keys.add(key)
    return result


def ingest_research_status_additions(payload: dict, data_directory: Path) -> dict:
    return apply_research_status_additions(payload, read_table(Path(data_directory), "research-status-additions"))
