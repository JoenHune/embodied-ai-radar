"""Import explicit source-content checks, never infer independent replication."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from catalog_store import fingerprint, read_table
from temporal_evidence import CAPABILITY_FLAGS, public_day


def ingest_capability_additions(payload: dict, data: Path) -> dict:
    works = {row["work_id"]: row for row in payload["works"]}
    sources = {row["source_record_id"]: row for row in payload["source-records"]}
    aliases = {row["alias"]: row["work_id"] for row in payload["work-aliases"]}
    for incoming in read_table(data, "capability-evidence-additions"):
        row = dict(incoming)
        row["work_id"] = aliases.get(row["work_id"], row["work_id"])
        work = works.get(row["work_id"])
        url = row.get("source_url", "")
        parsed = urlsplit(url)
        ids = row.get("source_record_ids", [])
        if not work or row.get("flag") not in CAPABILITY_FLAGS or row.get("value") is not True or row.get("review_status") != "verified":
            raise ValueError("Invalid capability source-content record")
        if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password or not ids:
            raise ValueError("Capability evidence requires a public source URL")
        if not set(ids) <= set(work.get("source_record_ids", [])) or any(sid not in sources or sources[sid].get("url", "").rstrip("/") != url.rstrip("/") for sid in ids):
            raise ValueError("Capability source does not belong to this work")
        if not all(row.get(key) for key in ["source_excerpt", "observation_scope", "verified_by", "verified_at"]):
            raise ValueError("Capability evidence requires inspected content and an explicit audit scope")
        observed, public = public_day(row["verified_at"]), public_day(row.get("public_at"), row.get("date_precision"))
        if not observed or (row.get("date_precision") != "unknown" and not public) or (public and public > observed):
            raise ValueError("Invalid or future capability evidence date")
        # A content check may establish a date absent from the older source
        # metadata (e.g. the inspected arXiv v1 header). Keep that assertion and
        # scope here instead of silently rewriting the raw source timestamp.
        row["record_id"] = "capability-evidence:" + fingerprint([row["work_id"], row["flag"], url, row.get("public_at"), row.get("date_precision")])[:24]
        evidence = work.setdefault("evidence_flag_evidence", [])
        existing = next((item for item in evidence if item["record_id"] == row["record_id"]), None)
        if existing and fingerprint(existing) != fingerprint(row):
            raise ValueError("An existing source-content check changed; add a new reviewed revision explicitly")
        if not existing:
            evidence.append(row)
    return payload
