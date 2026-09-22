import gzip
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publish_token_free_batch as publisher
import token_free_research as runner


class TokenFreePublisherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.private = self.root / ".research/token-free-research"
        self.cache = self.root / ".research/hardware-fulltext"
        self.tree = self.root / ".research/token-free-publisher"
        self.private.mkdir(parents=True)
        (self.private / "cards").mkdir()
        (self.cache / "objects").mkdir(parents=True)
        (self.root / "config").mkdir()
        for name, value in (("ROOT", self.root), ("PRIVATE", self.private),
                            ("CACHE", self.cache), ("PUBLISH_TREE", self.tree),
                            ("RECEIPTS", self.private / "published-receipts.jsonl"),
                            ("STATE", self.private / "publish-state.json")):
            setting = patch.object(publisher, name, value)
            setting.start()
            self.addCleanup(setting.stop)

        self.work_id = "arxiv:2609.04545"
        self.observation_id = "hardware-source:" + "a" * 32
        self.source_url = "https://arxiv.org/html/2609.04545v1"
        self.private_text = "PRIVATE ARTICLE BODY /Users/Joen/private-research.txt"
        self.raw = ("<html><body>" + self.private_text + "</body></html>").encode()
        self.raw_hash = hashlib.sha256(self.raw).hexdigest()
        self.body_hash = hashlib.sha256(self.private_text.encode()).hexdigest()
        self.processing_key = "d" * 64
        self.objects = {
            "cache_ref": self.cache / "objects" / (self.raw_hash + ".html"),
            "blocks_ref": self.cache / "objects" / (self.raw_hash + ".blocks.json"),
            "body_cache_ref": self.cache / "objects" / (self.body_hash + ".txt"),
        }
        for field, path in self.objects.items():
            path.write_bytes(self.raw if field == "cache_ref" else self.private_text.encode())
        self.observation = {
            "work_id": self.work_id, "observation_id": self.observation_id,
            "source_url": self.source_url, "status": "full_text_available",
            "observed_at": "2026-09-22T00:00:00Z", "raw_sha256": self.raw_hash,
            "text_sha256": self.body_hash,
            **{field: str(path) for field, path in self.objects.items()},
        }
        (self.cache / "observations.jsonl").write_text(json.dumps(self.observation) + "\n")
        self.dictionary = {"entries": [{"dictionary_id": "robot:g1", "name": "Unitree G1"}]}
        (self.root / "config/hardware-dictionary.json").write_text(json.dumps(self.dictionary))
        self.candidate = {
            "dictionary_id": "robot:g1", "name": "Unitree G1",
            "category": "robot_platform", "context_only": False,
            "source_locator": self.source_url + "#S1.p1",
            "simulation_word_present": False, "negation_word_present": False,
            "status": "unverified_mention", "usage_verified": False,
            "excerpt": self.private_text,
        }
        self.card_path = self.private / "cards/example.json.gz"
        self.write_card()
        with runner.open_db(self.private / "research.sqlite") as db:
            cursor = db.execute("""INSERT INTO works
                (work_id,metadata,source_key,source_state,process_state,processed_key,card_path,active)
                VALUES (?,?,?,?,?,?,?,1)""",
                (self.work_id, "{}", self.processing_key, "full_text_available",
                 "extracted_not_read", self.processing_key, "cards/example.json.gz"))
            self.search_rowid = cursor.lastrowid
            db.execute("INSERT INTO search(rowid,work_id,title,abstract,body) VALUES (?,?,?,?,?)",
                       (self.search_rowid, self.work_id, "World model", "", self.private_text))
            db.execute("INSERT INTO candidates VALUES (?,?,?,?,?)",
                       (self.work_id, "robot:g1", "Unitree G1", 0, json.dumps(self.candidate)))
        self.dbrow = self.read_dbrow()
        self.record = publisher.make_record(self.observation, self.dbrow,
                                             {"robot:g1": self.dictionary["entries"][0]})
        self.public_path = self.tree / publisher.RECORDS_REL
        self.public_path.parent.mkdir(parents=True)
        self.public_path.write_text(publisher.encode(self.record) + "\n")

    def write_card(self):
        card = {"work_id": self.work_id, "processing_key": self.processing_key,
                "source": {"observation_id": self.observation_id, "raw_sha256": self.raw_hash,
                           "cache_ref": str(self.objects["cache_ref"])},
                "article_read_complete": False, "understanding_verified": False,
                "blocks": [{"text": self.private_text}],
                "hardware_candidates": [self.candidate]}
        self.card_path.write_bytes(gzip.compress(json.dumps(card).encode()))

    def read_dbrow(self):
        with sqlite3.connect(self.private / "research.sqlite") as db:
            db.row_factory = sqlite3.Row
            return dict(db.execute("SELECT rowid AS search_rowid,* FROM works WHERE work_id=?",
                                   (self.work_id,)).fetchone())

    def assert_private_material_present(self):
        self.assertTrue(self.card_path.exists())
        self.assertTrue(all(path.exists() for path in self.objects.values()))
        with sqlite3.connect(self.private / "research.sqlite") as db:
            self.assertEqual(db.execute("SELECT body FROM search WHERE rowid=?",
                                        (self.search_rowid,)).fetchone()[0], self.private_text)
            self.assertEqual(db.execute("SELECT count(*) FROM candidates").fetchone()[0], 1)

    def test_candidate_projection_omits_body_paths_and_rejects_private_locator(self):
        public = publisher.encode(self.record)
        self.assertNotIn(self.private_text, public)
        self.assertNotIn(str(self.private), public)
        self.assertNotIn(str(self.cache), public)
        self.assertEqual(len(self.record["matches"]), 1)
        self.candidate["source_locator"] = self.source_url + "#%2FUsers%2FJoen%2Fprivate-research.txt"
        self.write_card()
        with self.assertRaisesRegex(ValueError, "invalid_arxiv_url"):
            publisher.make_record(self.observation, self.dbrow,
                                  {"robot:g1": self.dictionary["entries"][0]})

    def test_rejects_private_observation_time_before_publication(self):
        self.observation["observed_at"] = "/Users/Joen/private-research.txt"
        with self.assertRaises(ValueError):
            publisher.make_record(self.observation, self.dbrow,
                                  {"robot:g1": self.dictionary["entries"][0]})

    def test_unconfirmed_online_publish_preserves_private_material(self):
        with (patch.object(publisher, "ensure_publish_tree", return_value=self.public_path),
              patch.object(publisher, "git", return_value="c" * 40),
              patch.object(publisher, "wait_online", side_effect=RuntimeError("not_online")) as online):
            with self.assertRaisesRegex(RuntimeError, "not_online"):
                publisher.publish()
        online.assert_called_once_with("c" * 40, hashlib.sha256(self.public_path.read_bytes()).hexdigest())
        self.assert_private_material_present()
        self.assertFalse(publisher.RECEIPTS.exists())

    def test_changed_processing_rules_republish_same_observation(self):
        self.processing_key = "e" * 64
        self.write_card()
        with sqlite3.connect(self.private / "research.sqlite") as db:
            db.execute("UPDATE works SET source_key=?,processed_key=? WHERE work_id=?",
                       (self.processing_key, self.processing_key, self.work_id))
        self.assertEqual(publisher.publish(dry_run=True)["new_records"], 1)

    def test_cleanup_after_confirmation_removes_private_copies_and_is_idempotent(self):
        commit = "c" * 40
        with (patch.object(publisher, "ensure_publish_tree", return_value=self.public_path),
              patch.object(publisher, "git", return_value=commit),
              patch.object(publisher, "wait_online", return_value=None) as online):
            result = publisher.publish()
        self.assertEqual(result["status"], "published_and_compacted")
        self.assertEqual(result["compacted_records"], 1)
        online.assert_called_once_with(commit, hashlib.sha256(self.public_path.read_bytes()).hexdigest())
        self.assertFalse(self.card_path.exists())
        self.assertTrue(all(not path.exists() for path in self.objects.values()))
        with sqlite3.connect(self.private / "research.sqlite") as db:
            self.assertEqual(db.execute("SELECT body FROM search WHERE rowid=?",
                                        (self.search_rowid,)).fetchone()[0], "")
            self.assertEqual(db.execute("SELECT count(*) FROM candidates").fetchone()[0], 0)
            state = db.execute("SELECT process_state,processed_key,card_path FROM works WHERE work_id=?",
                               (self.work_id,)).fetchone()
            self.assertEqual(state, ("published_compacted", self.processing_key, None))
        receipt_bytes = publisher.RECEIPTS.read_bytes()
        self.assertEqual(len(publisher.parse_jsonl(publisher.RECEIPTS)), 1)
        self.assertEqual(publisher.cleanup([self.record], {self.work_id: self.observation},
                                           {self.work_id: self.read_dbrow()}, commit), 0)
        self.assertEqual(publisher.RECEIPTS.read_bytes(), receipt_bytes)
        with (patch.object(publisher, "ensure_publish_tree", return_value=self.public_path),
              patch.object(publisher, "git", return_value=commit),
              patch.object(publisher, "wait_online", side_effect=AssertionError("unnecessary check"))):
            self.assertEqual(publisher.publish()["status"], "up_to_date")


if __name__ == "__main__":
    unittest.main()
