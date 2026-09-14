"""Normalized, external-content FTS5 export over the canonical works table.

SQLite explicitly supports a VIEW as external content and retains normal
column retrieval, MATCH, highlight() and snippet(). This is not contentless
FTS. See https://www.sqlite.org/fts5.html sections 4.4.3 and 6.7.

Call build_sqlite_search(connection, metadata_rows) AFTER populating works.
Each metadata row is {work_id, organizations, keywords}; keywords is the
existing ordered keyword string, including dictionary aliases unavailable in
works. Titles, abstracts and the authors display text are never duplicated.
The helper never commits the caller's transaction, reads/writes files, changes
canonical fields, or contacts the network. Only its derived search objects are
replaced. Exported databases are snapshots: after changing works or metadata,
call rebuild_sqlite_search() before using MATCH or highlighting again.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import contextmanager
import sqlite3

FTS_COLUMNS = ("work_id", "title", "title_zh", "abstract", "authors", "organizations", "keywords")
REQUIRED_WORK_COLUMNS = {"work_id", "title", "title_zh", "abstract", "authors_json"}

METADATA_DDL = """
CREATE TABLE search_metadata (
    work_id TEXT PRIMARY KEY REFERENCES works(work_id),
    organizations TEXT NOT NULL DEFAULT '',
    keywords TEXT NOT NULL DEFAULT ''
)
"""

# Authors retain source ordering and punctuation, matching the previous
# Python ' '.join(authors) representation without storing it a second time.
# A recursive CTE uses only core SQL + scalar JSON functions. json_each works
# in ordinary SELECTs but failed inside FTS5 rebuild on tested SQLite 3.51.2;
# neither a Python UDF nor a table-valued virtual function is required here.
CONTENT_VIEW_DDL = """
CREATE VIEW works_search_content AS
SELECT w.rowid AS rowid, w.work_id, w.title,
       COALESCE(w.title_zh, '') AS title_zh,
       COALESCE(w.abstract, '') AS abstract,
       COALESCE((
         WITH RECURSIVE author_parts(position, value) AS (
           SELECT 0, json_extract(w.authors_json, '$[0]')
             WHERE json_array_length(w.authors_json) > 0
           UNION ALL
           SELECT position + 1,
                  json_extract(w.authors_json, '$[' || (position + 1) || ']')
             FROM author_parts
             WHERE position + 1 < json_array_length(w.authors_json)
         )
         SELECT group_concat(value, ' ') FROM (
           SELECT value FROM author_parts ORDER BY position
         )
       ), '') AS authors,
       COALESCE(m.organizations, '') AS organizations,
       COALESCE(m.keywords, '') AS keywords
FROM works AS w LEFT JOIN search_metadata AS m ON m.work_id = w.work_id
"""

FTS_DDL = """
CREATE VIRTUAL TABLE works_fts USING fts5(
    work_id UNINDEXED, title, title_zh, abstract, authors, organizations, keywords,
    content='works_search_content', content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
)
"""


@contextmanager
def _savepoint(connection: sqlite3.Connection, name: str):
    # Fixed internal names, not caller-supplied SQL identifiers. executescript
    # is deliberately avoided because it may commit an existing transaction.
    connection.execute(f"SAVEPOINT {name}")
    try:
        yield
    except Exception:
        connection.execute(f"ROLLBACK TO {name}")
        connection.execute(f"RELEASE {name}")
        raise
    else:
        connection.execute(f"RELEASE {name}")


def _validate_works(connection):
    columns = {row[1] for row in connection.execute("PRAGMA table_info(works)")}
    missing = REQUIRED_WORK_COLUMNS - columns
    if missing:
        raise ValueError("Canonical works table lacks: " + ", ".join(sorted(missing)))
    connection.execute("SELECT rowid FROM works LIMIT 0")
    identifiers = [row[0] for row in connection.execute("SELECT work_id FROM works")]
    if any(not isinstance(wid, str) or not wid for wid in identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError("Every canonical work needs one nonempty unique work_id")
    bad = connection.execute("SELECT work_id FROM works WHERE CASE WHEN json_valid(authors_json) THEN json_type(authors_json) ELSE '' END != 'array' LIMIT 1").fetchone()
    if bad:
        raise ValueError("Invalid authors_json: expected a JSON array")
    if connection.execute("SELECT 1 FROM works w, json_each(w.authors_json) j WHERE j.type != 'text' LIMIT 1").fetchone():
        raise ValueError("authors_json must contain only strings")
    return set(identifiers)


def _metadata_text(value, field):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value):
        return " ".join(value)
    raise ValueError(f"Search metadata {field} must be text or a sequence of strings")


def check_sqlite_search_integrity(connection: sqlite3.Connection) -> None:
    """rank=1 verifies content/index agreement, not merely FTS b-tree health."""
    connection.execute("INSERT INTO works_fts(works_fts, rank) VALUES('integrity-check', 1)")


def rebuild_sqlite_search(connection: sqlite3.Connection) -> dict:
    """Rebuild from the live content view; never overwrite original columns."""
    with _savepoint(connection, "radar_search_rebuild"):
        connection.execute("INSERT INTO works_fts(works_fts) VALUES('rebuild')")
        check_sqlite_search_integrity(connection)
        total = connection.execute("SELECT count(*) FROM works_search_content").fetchone()[0]
    return {"indexed_works": total, "external_content": "works_search_content", "integrity_checked_against_content": True}


def build_sqlite_search(connection: sqlite3.Connection, metadata_rows: Iterable[Mapping]) -> dict:
    """Replace only derived FTS objects with complete, validated metadata.

    Supply exactly one metadata row per canonical work, including rows with
    empty organizations/aliases. Duplicate, missing or unknown work IDs fail
    before replacing an existing index. Original text is never accepted as
    metadata, preventing accidental reintroduction of full-text duplication.
    """
    work_ids = _validate_works(connection)
    metadata, seen = [], set()
    for row in metadata_rows:
        if not isinstance(row, Mapping) or set(row) - {"work_id", "organizations", "keywords"}:
            raise ValueError("Search metadata may contain only work_id, organizations and keywords")
        wid = row.get("work_id")
        if not isinstance(wid, str) or wid not in work_ids or wid in seen:
            raise ValueError("Search metadata references a duplicate or unknown canonical work")
        seen.add(wid)
        metadata.append((wid, _metadata_text(row.get("organizations"), "organizations"), _metadata_text(row.get("keywords"), "keywords")))
    if seen != work_ids:
        raise ValueError(f"Search metadata is incomplete: {len(work_ids - seen)} canonical works missing")
    with _savepoint(connection, "radar_search_export"):
        connection.execute("DROP TABLE IF EXISTS works_fts")
        connection.execute("DROP VIEW IF EXISTS works_search_content")
        connection.execute("DROP TABLE IF EXISTS search_metadata")
        connection.execute(METADATA_DDL)
        connection.executemany("INSERT INTO search_metadata(work_id, organizations, keywords) VALUES (?,?,?)", metadata)
        connection.execute(CONTENT_VIEW_DDL)
        connection.execute(FTS_DDL)
        result = rebuild_sqlite_search(connection)
    return {**result, "metadata_rows": len(metadata), "stored_original_text_columns": 0}
