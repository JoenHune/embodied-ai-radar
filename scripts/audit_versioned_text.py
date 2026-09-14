"""Pure full-population validation of archived metadata, never a sample."""
from __future__ import annotations

from jsonschema import Draft202012Validator, FormatChecker
from urllib.parse import urlsplit
import re
from versioned_text import validate_snapshot


def audit_versioned_text(snapshots, works, sources, schema):
    work_map = {row["work_id"]: row for row in works}
    source_map = {row["source_record_id"]: row for row in sources}
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    seen, errors = set(), []
    for row in snapshots:
        sid = row.get("snapshot_id")
        if sid in seen:
            errors.append({"snapshot_id": sid, "reason": "duplicate_snapshot_id"})
        seen.add(sid)
        failures = list(validator.iter_errors(row))
        if failures:
            errors.extend({"snapshot_id": sid, "reason": "schema", "path": list(error.path), "message": error.message} for error in failures)
            continue
        try:
            url = urlsplit(row["source_url"])
            valid_url = url.scheme in {"http", "https"} and bool(url.hostname) and not url.username and not url.password and not any(char.isspace() for char in row["source_url"])
        except ValueError:
            valid_url = False
        if not valid_url:
            errors.append({"snapshot_id": sid, "reason": "invalid_source_url"})
            continue
        if row["work_id"] not in work_map:
            errors.append({"snapshot_id": sid, "reason": "orphan_snapshot"})
            continue
        work = work_map[row["work_id"]]
        source = source_map.get(row["source_record_id"], {})
        if source.get("source_type") == "official_arxiv_version_metadata":
            path = re.fullmatch(r"/(?:abs|pdf)/(\d{4}\.\d{4,5})(v[1-9]\d*)?(?:\.pdf)?", url.path)
            identifiers = {str(work.get("identifiers", {}).get("arxiv") or ""), work["work_id"], *work.get("aliases", [])}
            arxiv_ids = {re.sub(r"v\d+$", "", value.removeprefix("arxiv:")) for value in identifiers}
            if url.hostname not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"} or not path or path[1] not in arxiv_ids or (path[2] and path[2] != row["version"]):
                errors.append({"snapshot_id": sid, "reason": "arxiv_identity_or_version_mismatch"})
            origin = source.get("source_origin_id")
            if origin and (origin not in source_map or origin not in work.get("source_record_ids", [])):
                errors.append({"snapshot_id": sid, "reason": "unresolved_or_foreign_origin_source"})
        errors.extend({"snapshot_id": sid, "reason": reason} for reason in validate_snapshot(row, work_map[row["work_id"]], source_map))
    return {"status": "failed" if errors else "passed", "checked_snapshots": len(snapshots),
            "unique_snapshots": len(seen), "works_with_archived_text": len({row.get("work_id") for row in snapshots}), "errors": errors}
