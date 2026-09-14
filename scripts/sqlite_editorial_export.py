"""Lossless, separately labelled SQLite archive of the persistent editorial layer.

These artifacts are generated/reviewed interpretation, not catalog facts.  The
archive excludes transient attempts, diagnostics and runtime configuration.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SECTIONS = ("claims", "direction_summaries", "question_summaries", "organization_changes", "counterevidence", "watchlist")
PATH_RULES = (
    (r"monthly/\d{4}-\d{2}\.json", "monthly"),
    (r"revisions/\d{4}-\d{2}/[a-f0-9]{64}\.json", "revision"),
    (r"reviews/[^/]+\.json", "review"),
    (r"evidence-packets/[a-f0-9]{64}\.json", "evidence_packet"),
    (r"work-localizations\.jsonl", "localizations"),
    (r"signal-evidence\.jsonl", "signal_evidence"),
    (r"source-content-conflicts\.jsonl", "source_conflicts"),
)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read_editorial_artifacts(directory: Path) -> dict:
    """Only explicitly public editorial artifacts may enter a downloadable DB."""
    result = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(directory).as_posix()
        if not any(re.fullmatch(pattern, relative) for pattern, _ in PATH_RULES):
            continue
        if not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Editorial artifact escapes its source directory")
        result[relative] = ([json.loads(line) for line in path.read_text().splitlines() if line.strip()]
                            if path.suffix == ".jsonl" else json.loads(path.read_text()))
    return result


def artifact_rows(artifacts):
    rows = []
    for path, value in sorted(artifacts.items()):
        kind = next((kind for pattern, kind in PATH_RULES if re.fullmatch(pattern, path)), None)
        if kind is None:
            raise ValueError(f"Non-public editorial artifact path: {path}")
        month = value.get("month") if isinstance(value, dict) else None
        rows.append((path, kind, month, digest(value), canonical(value)))
    return rows


def build_editorial_archive(connection, artifacts):
    rows = artifact_rows(artifacts)
    if not connection.in_transaction:
        connection.execute("BEGIN")
    connection.execute("SAVEPOINT editorial_archive")
    try:
        connection.execute("DROP VIEW IF EXISTS editorial_narratives")
        connection.execute("DROP VIEW IF EXISTS monthly_editorial")
        connection.execute("DROP TABLE IF EXISTS editorial_artifacts")
        connection.execute("""CREATE TABLE editorial_artifacts (
            path TEXT PRIMARY KEY, kind TEXT NOT NULL, month TEXT,
            digest TEXT NOT NULL, payload_json TEXT NOT NULL CHECK(json_valid(payload_json)))""")
        connection.executemany("INSERT INTO editorial_artifacts VALUES (?,?,?,?,?)", rows)
        connection.execute("""CREATE VIEW monthly_editorial AS SELECT path, month,
            json_extract(payload_json,'$.status') AS status,
            json_extract(payload_json,'$.model') AS model,
            json_extract(payload_json,'$.response_id') AS response_id,
            digest, payload_json FROM editorial_artifacts WHERE kind='monthly'""")
        # Whole rows remain accessible, including evidence IDs, numeric claims,
        # exceptions and future fields.  This is not the authority claims table.
        connection.execute("CREATE VIEW editorial_narratives AS " + " UNION ALL ".join(
            f"SELECT m.month, '{section}' AS section, j.key AS ordinal, "
            f"j.value AS payload_json FROM monthly_editorial m, json_each(m.payload_json,'$.{section}') j"
            for section in SECTIONS))
        connection.execute("RELEASE editorial_archive")
    except Exception:
        connection.execute("ROLLBACK TO editorial_archive")
        connection.execute("RELEASE editorial_archive")
        raise
    return {"artifact_count": len(rows), "digest": digest({path: value for path, _, _, value, _ in rows}),
            "digest_method": "sha256_canonical_path_to_payload_digest", "table": "editorial_artifacts",
            "layer": "generated_and_reviewed_editorial_not_catalog_facts"}


def audit_editorial_archive(connection, artifacts):
    expected = artifact_rows(artifacts)
    actual = connection.execute("SELECT path,kind,month,digest,payload_json FROM editorial_artifacts ORDER BY path").fetchall()
    errors = []
    if actual != expected:
        errors.append("editorial_artifacts_differ_from_persistent_sources")
    wanted = [(value.get("month"), section, index, canonical(row))
              for path, value in sorted(artifacts.items()) if re.fullmatch(PATH_RULES[0][0], path)
              for section in SECTIONS for index, row in enumerate(value.get(section, []))]
    restored = [(month, section, index, canonical(json.loads(raw))) for month, section, index, raw in
                connection.execute("SELECT month,section,ordinal,payload_json FROM editorial_narratives")]
    if sorted(wanted) != sorted(restored):
        errors.append("editorial_narrative_view_loses_rows_or_fields")
    return {"status": "passed" if not errors else "failed", "artifact_count": len(expected),
            "narrative_count": len(wanted), "errors": errors}
