#!/usr/bin/env python3
"""Export a small, explicitly unverified public view of token-free results.

The tracked JSONL is the publication input. Private cards, cached article text,
and the local SQLite index are never read by this exporter.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/token-free-public/records.jsonl"
API = ROOT / "docs/public/api/v1/token-free"
DOWNLOADS = ROOT / "docs/public/downloads/token-free"
LATEST_LIMIT = 100
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
STATE = re.compile(r"[a-z][a-z0-9_]*\Z")
RECORD_FIELDS = {
    "schema_version", "work_id", "observation_id", "observed_at", "source_url",
    "source_state", "raw_sha256", "text_sha256", "process_state",
    "processing_key", "matches", "article_read_complete", "usage_verified",
}
MATCH_FIELDS = {
    "dictionary_id", "name", "category", "context_only", "source_locator",
    "simulation_word_present", "negation_word_present",
}


def _string(value: object, field: str, *, nullable: bool = False, max_length: int = 300) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > max_length or any(ord(c) < 32 for c in value):
        raise ValueError(f"invalid_{field}")
    return value


def _https_url(value: object, field: str, *, nullable: bool = False) -> str | None:
    result = _string(value, field, nullable=nullable, max_length=1000)
    if result is None:
        return None
    try:
        url = urlsplit(result)
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.port not in {None, 443}:
            raise ValueError
    except ValueError:
        raise ValueError(f"invalid_{field}") from None
    return result


def _hash(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not HEX_SHA256.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


def sanitize(record: object) -> dict:
    if not isinstance(record, dict) or set(record) != RECORD_FIELDS or record["schema_version"] != "1":
        raise ValueError("invalid_record_contract")
    if record["article_read_complete"] is not False or record["usage_verified"] is not False:
        raise ValueError("unverified_boundary_violated")
    work_id = _string(record["work_id"], "work_id", max_length=200)
    if not isinstance(record["source_state"], str) or not STATE.fullmatch(record["source_state"]):
        raise ValueError("invalid_source_state")
    if not isinstance(record["process_state"], str) or not STATE.fullmatch(record["process_state"]):
        raise ValueError("invalid_process_state")
    matches = record["matches"]
    if not isinstance(matches, list) or len(matches) > 10000:
        raise ValueError("invalid_matches")
    clean_matches = []
    for match in matches:
        if not isinstance(match, dict) or set(match) != MATCH_FIELDS:
            raise ValueError("invalid_match_contract")
        if any(type(match[key]) is not bool for key in
               ("context_only", "simulation_word_present", "negation_word_present")):
            raise ValueError("invalid_match_flags")
        clean_matches.append({
            "dictionary_id": _string(match["dictionary_id"], "dictionary_id", max_length=150),
            "name": _string(match["name"], "name", max_length=200),
            "category": _string(match["category"], "category", max_length=100),
            "context_only": match["context_only"],
            "source_locator": _https_url(match["source_locator"], "source_locator", nullable=True),
            "simulation_word_present": match["simulation_word_present"],
            "negation_word_present": match["negation_word_present"],
        })
    observed_at = _string(record["observed_at"], "observed_at", nullable=True, max_length=40)
    if observed_at is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", observed_at):
        raise ValueError("invalid_observed_at")
    return {
        "schema_version": "1", "work_id": work_id,
        "observation_id": _string(record["observation_id"], "observation_id", nullable=True),
        "observed_at": observed_at,
        "source_url": _https_url(record["source_url"], "source_url", nullable=True),
        "source_state": record["source_state"],
        "raw_sha256": _hash(record["raw_sha256"], "raw_sha256"),
        "text_sha256": _hash(record["text_sha256"], "text_sha256"),
        "process_state": record["process_state"],
        "processing_key": _hash(record["processing_key"], "processing_key"),
        "matches": clean_matches,
        "article_read_complete": False, "usage_verified": False,
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
    os.replace(temporary, path)


def export_public(source: Path = SOURCE, api: Path = API, downloads: Path = DOWNLOADS,
                  latest_limit: int = LATEST_LIMIT) -> dict:
    if latest_limit < 1:
        raise ValueError("invalid_latest_limit")
    api.mkdir(parents=True, exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)
    checksum = hashlib.sha256()
    process_states: Counter[str] = Counter()
    source_states: Counter[str] = Counter()
    frequency: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    recent: list[dict] = []
    seen: set[str] = set()
    total = 0
    candidate_works = 0
    candidate_mentions = 0
    archive = downloads / "records.jsonl.gz"
    with tempfile.NamedTemporaryFile(dir=downloads, prefix="records.", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped:
                if source.exists():
                    with source.open("rb") as rows:
                        for line_number, raw in enumerate(rows, 1):
                            checksum.update(raw)
                            if not raw.endswith(b"\n") or not raw.strip():
                                raise ValueError(f"invalid_jsonl_line:{line_number}")
                            try:
                                row = sanitize(json.loads(raw))
                            except (ValueError, UnicodeDecodeError) as error:
                                raise ValueError(f"invalid_jsonl_line:{line_number}:{error}") from None
                            wid = row["work_id"]
                            if wid in seen:
                                raise ValueError(f"duplicate_work_id:{wid}")
                            seen.add(wid)
                            total += 1
                            process_states[row["process_state"]] += 1
                            source_states[row["source_state"]] += 1
                            active = [match for match in row["matches"] if not match["context_only"]]
                            candidate_mentions += len(active)
                            candidate_works += bool(active)
                            for match in active:
                                frequency[(match["dictionary_id"], match["name"], match["category"])].add(wid)
                            zipped.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
                            recent.append({"work_id": wid, "observed_at": row["observed_at"],
                                           "source_url": row["source_url"], "source_state": row["source_state"],
                                           "process_state": row["process_state"],
                                           "candidate_names": list(dict.fromkeys(match["name"] for match in active))[:8],
                                           "candidate_name_count": len({match["dictionary_id"] for match in active}),
                                           "article_read_complete": False, "usage_verified": False})
                            if len(recent) > latest_limit * 2:
                                recent.sort(key=lambda item: (item["observed_at"] or "", item["work_id"]), reverse=True)
                                del recent[latest_limit:]
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, archive)
    recent.sort(key=lambda item: (item["observed_at"] or "", item["work_id"]), reverse=True)
    latest = recent[:latest_limit]
    ranked = sorted(({"dictionary_id": key[0], "name": key[1], "category": key[2],
                      "candidate_work_count": len(work_ids)} for key, work_ids in frequency.items()),
                    key=lambda item: (-item["candidate_work_count"], item["name"]))[:20]
    summary = {
        "schema_version": "1", "assurance": "machine_extracted_unverified",
        "article_read_complete": False, "usage_verified": False,
        "records_sha256": checksum.hexdigest(), "total_records": total,
        "source_states": dict(sorted(source_states.items())),
        "processing_states": dict(sorted(process_states.items())),
        "candidate_work_count": candidate_works,
        "candidate_mention_count": candidate_mentions,
        "candidate_frequency": ranked,
        "latest_observed_at": latest[0]["observed_at"] if latest else None,
        "latest_url": "/api/v1/token-free/latest.json",
        "download_url": "/downloads/token-free/records.jsonl.gz",
    }
    _write_json(api / "latest.json", {"schema_version": "1", "records_sha256": checksum.hexdigest(),
                                       "total_records": total, "rows": latest})
    _write_json(api / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--api", type=Path, default=API)
    parser.add_argument("--downloads", type=Path, default=DOWNLOADS)
    args = parser.parse_args()
    result = export_public(args.source, args.api, args.downloads)
    print(json.dumps({"status": "exported", "total_records": result["total_records"],
                      "records_sha256": result["records_sha256"]}))


if __name__ == "__main__":
    main()
