"""SQLite-native fixtures; no catalog export, network, or original data edits."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sqlite_search_export import FTS_COLUMNS, build_sqlite_search, check_sqlite_search_integrity, rebuild_sqlite_search

WORKS_DDL = """CREATE TABLE works (
 work_id TEXT PRIMARY KEY, title TEXT NOT NULL, title_zh TEXT,
 abstract TEXT, authors_json TEXT NOT NULL, untouched_payload TEXT
)"""
WORKS = [
    {"work_id": "arxiv:fixture-one", "title": "π0: World Model for Robot Control", "title_zh": "世界模型 机器人控制",
     "abstract": "A full abstract keeps every word. Contact-rich manipulation reaches robust control; Unicode: α β 世界模型.\nSecond paragraph is preserved exactly.",
     "authors": ["O’Neil, A.", 'Li "Ming"', "García-López", "王 强"]},
    {"work_id": "doi:10.5555/fixture-two", "title": "Dexterous Manipulation with Tactile Feedback", "title_zh": None,
     "abstract": "Tactile feedback and precise grasping. 灵巧操作 触觉反馈", "authors": ["B. Researcher", "Ito, A/B"]},
    {"work_id": "report:fixture-three", "title": "世界模型 开源数据集", "title_zh": "", "abstract": None, "authors": []},
]
METADATA = [
    {"work_id": WORKS[0]["work_id"], "organizations": "Synthetic Physical Intelligence", "keywords": "D1 D3 Q1 world model π0 大小脑"},
    {"work_id": WORKS[1]["work_id"], "organizations": "Synthetic Dexterous Lab", "keywords": "D4 D15 Q5 灵巧操作 force-feedback"},
    {"work_id": WORKS[2]["work_id"], "organizations": "", "keywords": "D9 Q2 dataset 数据集"},
]


def connect(works=WORKS):
    connection = sqlite3.connect(":memory:")
    connection.execute(WORKS_DDL)
    connection.executemany("INSERT INTO works VALUES(?,?,?,?,?,?)", [(w["work_id"], w["title"], w.get("title_zh"), w.get("abstract"), json.dumps(w["authors"], ensure_ascii=False), "original sentinel") for w in works])
    return connection


def legacy_rows(works=WORKS, metadata=METADATA):
    by_id = {m["work_id"]: m for m in metadata}
    return [(w["work_id"], w["title"], w.get("title_zh") or "", w.get("abstract") or "", " ".join(w["authors"]), by_id[w["work_id"]]["organizations"], by_id[w["work_id"]]["keywords"]) for w in works]


class SqliteSearchExportTests(unittest.TestCase):
    def setUp(self):
        self.connection = connect()
        self.addCleanup(self.connection.close)

    def matches(self, query):
        return [row[0] for row in self.connection.execute("SELECT work_id FROM works_fts WHERE works_fts MATCH ? ORDER BY work_id", (query,))]

    def test_one_external_row_per_work_and_exact_legacy_columns(self):
        result = build_sqlite_search(self.connection, METADATA)
        self.assertEqual(result["indexed_works"], len(WORKS))
        self.assertTrue(result["integrity_checked_against_content"])
        self.assertEqual(tuple(row[1] for row in self.connection.execute("PRAGMA table_info(works_fts)")), FTS_COLUMNS)
        self.assertEqual(self.connection.execute("SELECT count(*),count(DISTINCT work_id) FROM works_fts").fetchone(), (3, 3))
        self.assertEqual(self.connection.execute("SELECT rowid FROM works_fts ORDER BY rowid").fetchall(), self.connection.execute("SELECT rowid FROM works ORDER BY rowid").fetchall())
        self.assertEqual(self.connection.execute("SELECT * FROM works_fts ORDER BY work_id").fetchall(), sorted(legacy_rows()))

    def test_original_fields_and_caller_metadata_are_unchanged(self):
        before = self.connection.execute("SELECT * FROM works ORDER BY work_id").fetchall()
        metadata = copy.deepcopy(METADATA)
        build_sqlite_search(self.connection, iter(metadata))
        self.assertEqual(before, self.connection.execute("SELECT * FROM works ORDER BY work_id").fetchall())
        self.assertEqual(metadata, METADATA)

    def test_multilingual_special_symbol_and_fielded_match(self):
        build_sqlite_search(self.connection, METADATA)
        self.assertEqual(self.matches('title:"π0"'), [WORKS[0]["work_id"]])
        self.assertEqual(self.matches('"WORLD model"'), [WORKS[0]["work_id"]])
        self.assertEqual(self.matches('"世界模型"'), sorted([WORKS[0]["work_id"], WORKS[2]["work_id"]]))
        self.assertEqual(self.matches('"灵巧操作"'), [WORKS[1]["work_id"]])
        self.assertEqual(self.matches('keywords:"大小脑"'), [WORKS[0]["work_id"]])

    def test_author_order_punctuation_quotes_and_accents_preserved(self):
        build_sqlite_search(self.connection, METADATA)
        authors = self.connection.execute("SELECT authors FROM works_fts WHERE work_id=?", (WORKS[0]["work_id"],)).fetchone()[0]
        self.assertEqual(authors, 'O’Neil, A. Li "Ming" García-López 王 强')
        self.assertEqual(self.matches('authors:"Garcia Lopez"'), [WORKS[0]["work_id"]])
        self.assertEqual(self.matches('authors:"O’Neil"'), [WORKS[0]["work_id"]])

    def test_metadata_join_preserves_organization_and_keyword_phrase_semantics(self):
        build_sqlite_search(self.connection, METADATA)
        self.assertEqual(self.matches('organizations:"Synthetic Dexterous Lab"'), [WORKS[1]["work_id"]])
        self.assertEqual(self.matches('keywords:"D4 D15 Q5"'), [WORKS[1]["work_id"]])
        self.assertEqual(self.connection.execute("SELECT keywords FROM works_fts WHERE work_id=?", (WORKS[1]["work_id"],)).fetchone()[0], METADATA[1]["keywords"])

    def test_full_original_abstract_retrieval_highlight_snippet_and_rank(self):
        build_sqlite_search(self.connection, METADATA)
        row = self.connection.execute("SELECT abstract, highlight(works_fts,3,'<mark>','</mark>'), snippet(works_fts,3,'[',']','…',12),bm25(works_fts) FROM works_fts WHERE works_fts MATCH ?", ('abstract:"Contact-rich manipulation"',)).fetchone()
        self.assertEqual(row[0], WORKS[0]["abstract"])
        self.assertIn('<mark>Contact-rich manipulation</mark>', row[1])
        self.assertIn('[Contact-rich manipulation]', row[2])
        self.assertIsInstance(row[3], float)
        title = self.connection.execute("SELECT highlight(works_fts,1,'[',']') FROM works_fts WHERE works_fts MATCH ?", ('title:"π0"',)).fetchone()[0]
        self.assertEqual(title, '[π0]: World Model for Robot Control')

    def test_missing_title_zh_abstract_and_empty_authors_keep_legacy_empty_text(self):
        build_sqlite_search(self.connection, METADATA)
        self.assertEqual(self.connection.execute("SELECT title_zh FROM works_fts WHERE work_id=?", (WORKS[1]["work_id"],)).fetchone()[0], '')
        self.assertEqual(self.connection.execute("SELECT title_zh,abstract,authors FROM works_fts WHERE work_id=?", (WORKS[2]["work_id"],)).fetchone(), ('', '', ''))
        self.assertIsNone(self.connection.execute("SELECT abstract FROM works WHERE work_id=?", (WORKS[2]["work_id"],)).fetchone()[0])

    def test_no_private_content_copy_and_metadata_stores_no_original_text(self):
        build_sqlite_search(self.connection, METADATA)
        names = {row[0] for row in self.connection.execute("SELECT name FROM sqlite_master")}
        self.assertNotIn('works_fts_content', names)
        self.assertEqual(self.connection.execute("SELECT type FROM sqlite_master WHERE name='works_search_content'").fetchone()[0], 'view')
        self.assertEqual([row[1] for row in self.connection.execute("PRAGMA table_info(search_metadata)")], ['work_id', 'organizations', 'keywords'])

    def test_rebuild_detects_stale_original_text_then_restores_integrity(self):
        build_sqlite_search(self.connection, METADATA)
        self.connection.execute("UPDATE works SET abstract='Newlyverifiedmarker with full replacement text' WHERE work_id=?", (WORKS[0]["work_id"],))
        with self.assertRaises(sqlite3.DatabaseError):
            check_sqlite_search_integrity(self.connection)
        rebuild_sqlite_search(self.connection)
        self.assertEqual(self.matches('Newlyverifiedmarker'), [WORKS[0]["work_id"]])
        self.assertEqual(self.matches('abstract:"Contact-rich manipulation"'), [])
        check_sqlite_search_integrity(self.connection)

    def test_metadata_update_requires_rebuild_and_highlights_fresh_value(self):
        build_sqlite_search(self.connection, METADATA)
        self.connection.execute("UPDATE search_metadata SET organizations='Neworganizationmarker' WHERE work_id=?", (WORKS[0]["work_id"],))
        with self.assertRaises(sqlite3.DatabaseError):
            check_sqlite_search_integrity(self.connection)
        rebuild_sqlite_search(self.connection)
        self.assertEqual(self.matches('organizations:Neworganizationmarker'), [WORKS[0]["work_id"]])
        self.assertEqual(self.connection.execute("SELECT highlight(works_fts,5,'[',']') FROM works_fts WHERE works_fts MATCH ?", ('organizations:Neworganizationmarker',)).fetchone()[0], '[Neworganizationmarker]')

    def test_replacement_and_rebuild_are_idempotent(self):
        build_sqlite_search(self.connection, METADATA)
        first = self.connection.execute("SELECT * FROM works_fts ORDER BY work_id").fetchall()
        build_sqlite_search(self.connection, list(reversed(METADATA)))
        rebuild_sqlite_search(self.connection)
        self.assertEqual(first, self.connection.execute("SELECT * FROM works_fts ORDER BY work_id").fetchall())
        self.assertNotIn('works_fts_content', {r[0] for r in self.connection.execute("SELECT name FROM sqlite_master")})

    def test_duplicate_missing_unknown_and_fulltext_metadata_fail_without_losing_index(self):
        build_sqlite_search(self.connection, METADATA)
        bad_cases = [METADATA + [METADATA[0]], METADATA[:-1], METADATA + [{"work_id": "unknown"}], [{**METADATA[0], "abstract": WORKS[0]["abstract"]}, *METADATA[1:]]]
        for rows in bad_cases:
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                build_sqlite_search(self.connection, rows)
            self.assertEqual(self.matches('title:"π0"'), [WORKS[0]["work_id"]])
            check_sqlite_search_integrity(self.connection)

    def test_caller_transaction_is_not_committed(self):
        self.assertTrue(self.connection.in_transaction)
        build_sqlite_search(self.connection, METADATA)
        self.assertTrue(self.connection.in_transaction)
        self.connection.rollback()
        self.assertEqual(self.connection.execute("SELECT count(*) FROM works").fetchone()[0], 0)
        self.assertFalse(self.connection.execute("SELECT name FROM sqlite_master WHERE name='works_fts'").fetchone())

    def test_portable_reopen_needs_no_python_udf(self):
        build_sqlite_search(self.connection, METADATA)
        with tempfile.TemporaryDirectory(prefix='sqlite-search-export-') as directory:
            target = Path(directory) / 'fixture.sqlite'
            self.connection.commit()
            with sqlite3.connect(target) as disk:
                self.connection.backup(disk)
            with sqlite3.connect(target) as reopened:
                check_sqlite_search_integrity(reopened)
                self.assertEqual(reopened.execute("SELECT abstract FROM works_fts WHERE works_fts MATCH ?", ('title:"π0"',)).fetchone()[0], WORKS[0]["abstract"])

    def test_large_author_list_is_complete_and_ordered(self):
        authors = [f'Author {number}' for number in range(1200)]
        self.connection.execute("UPDATE works SET authors_json=? WHERE work_id=?", (json.dumps(authors), WORKS[0]["work_id"]))
        build_sqlite_search(self.connection, METADATA)
        self.assertEqual(self.connection.execute("SELECT authors FROM works_fts WHERE work_id=?", (WORKS[0]["work_id"],)).fetchone()[0], ' '.join(authors))

    def test_empty_catalog_is_valid_and_invalid_json_is_rejected(self):
        empty = connect([]); self.addCleanup(empty.close)
        self.assertEqual(build_sqlite_search(empty, [])['indexed_works'], 0)
        self.connection.execute("UPDATE works SET authors_json='not-json' WHERE work_id=?", (WORKS[0]["work_id"],))
        with self.assertRaises(ValueError):
            build_sqlite_search(self.connection, METADATA)

    def test_normalization_reduces_fixture_database_bytes_without_dropping_text(self):
        works = copy.deepcopy(WORKS)
        for work in works:
            work['abstract'] = ' '.join(f'physicaltoken{number}' for number in range(3000))
        normalized = connect(works); legacy = connect(works)
        self.addCleanup(normalized.close); self.addCleanup(legacy.close)
        build_sqlite_search(normalized, METADATA)
        legacy.execute("CREATE VIRTUAL TABLE works_fts USING fts5(work_id UNINDEXED,title,title_zh,abstract,authors,organizations,keywords,tokenize='unicode61 remove_diacritics 2')")
        legacy.executemany("INSERT INTO works_fts VALUES(?,?,?,?,?,?,?)", legacy_rows(works))
        size = lambda conn: conn.execute('PRAGMA page_count').fetchone()[0] * conn.execute('PRAGMA page_size').fetchone()[0]
        self.assertLess(size(normalized), size(legacy))
        self.assertEqual(normalized.execute('SELECT abstract FROM works_fts ORDER BY work_id').fetchall(), legacy.execute('SELECT abstract FROM works_fts ORDER BY work_id').fetchall())


if __name__ == '__main__':
    unittest.main()
