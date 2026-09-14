"""Status changes suppress reliance on results, never erase publication history."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from temporal_evidence import evidence_as_of
from trend_signals import reviewed_signal_evidence


class ResearchStatusTemporalTests(unittest.TestCase):
    def setUp(self):
        self.work = {"work_id": "arxiv:2607.04837", "first_public_date": "2026-07-01", "first_public_date_precision": "day",
                     "source_record_ids": ["source:experiment", "source:notice", "source:peer"],
                     "evidence_flags": {"real_robot": True},
                     "evidence_flag_evidence": [{"record_id": "flag:real", "flag": "real_robot", "value": True,
                          "review_status": "verified", "source_url": "https://lab.test/experiment", "source_record_ids": ["source:experiment"],
                          "public_at": "2026-07-01", "date_precision": "day"}],
                     "research_status_notices": [{"notice_id": "notice:withdrawn", "work_id": "arxiv:2607.04837", "event_type": "withdrawn",
                          "scope": "work", "public_at": "2026-08-24T07:00:55Z", "date_precision": "second", "review_status": "verified",
                          "source_record_ids": ["source:notice"], "source_url": "https://arxiv.org/abs/2607.04837v3", "summary_zh": "合成撤回通知"}]}
        self.sources = [{"source_record_id": "source:experiment", "url": "https://lab.test/experiment"},
                        {"source_record_id": "source:peer", "url": "https://venue.test/work"},
                        {"source_record_id": "source:notice", "url": "https://arxiv.org/abs/2607.04837v3",
                         "source_type": "official_arxiv_status_notice", "published_at": "2026-08-24T07:00:55Z",
                         "raw": {"work_id": "arxiv:2607.04837"}}]
        self.versions = [{"manifestation_id": "version:peer", "work_id": self.work["work_id"], "kind": "conference",
                          "peer_reviewed": True, "published_at": "2026-07-02", "date_precision": "day", "venue": "FixtureConf",
                          "url": "https://venue.test/work"},
                         {"manifestation_id": "version:code", "work_id": self.work["work_id"], "kind": "code",
                          "status": "verified_asset_release", "published_at": "2026-07-03", "date_precision": "day", "url": "https://github.com/example/fixture"}]

    def test_later_notice_does_not_change_historical_packet(self):
        plain = copy.deepcopy(self.work)
        plain.pop("research_status_notices")
        self.assertEqual(evidence_as_of(self.work, self.versions, "2026-07", self.sources), evidence_as_of(plain, self.versions, "2026-07", self.sources))

    def test_current_results_are_blocked_but_history_and_assets_remain(self):
        original = copy.deepcopy((self.work, self.versions, self.sources))
        view = evidence_as_of(self.work, self.versions, "2026-08", self.sources)
        self.assertFalse(view["validation_eligible"])
        self.assertEqual(view["research_status"]["status"], "withdrawn")
        self.assertEqual(view["evidence_grade"], "E0")
        self.assertFalse(view["evidence_flags"]["real_robot"])
        self.assertTrue(view["evidence_flags"]["open_code"])
        self.assertFalse(view["strict_peer_reviewed"])
        self.assertEqual(view["peer_reviewed_manifestations"], [])
        self.assertEqual(len(view["manifestations"]), 2)
        self.assertTrue(view["reported_validation_before_status_gate"]["strict_peer_reviewed"])
        self.assertTrue(view["reported_validation_before_status_gate"]["evidence_flags"]["real_robot"])
        self.assertEqual((self.work, self.versions, self.sources), original)

    def test_unverified_notice_cannot_revoke_valid_results(self):
        self.work["research_status_notices"][0]["review_status"] = "draft"
        view = evidence_as_of(self.work, self.versions, "2026-08", self.sources)
        self.assertTrue(view["strict_peer_reviewed"])
        self.assertTrue(view["evidence_flags"]["real_robot"])

    def test_withdrawn_results_cannot_be_trend_support_or_counterevidence(self):
        record = {"record_id": "signal:fixture", "signal_id": "S1", "work_id": self.work["work_id"], "review_status": "verified",
                  "research_scope": "in_scope", "stance": "supports", "statement": "Synthetic fixture",
                  "experiment": {"setting": None, "baseline": None, "metric": None, "limitations": []},
                  "source_url": "https://lab.test/experiment", "source_record_ids": ["source:experiment"],
                  "public_at": "2026-07-01", "date_precision": "day"}
        self.work["signal_evidence"] = [record]
        for stance in ["supports", "contradicts", "neutral"]:
            record["stance"] = stance
            self.assertEqual(len(reviewed_signal_evidence(self.work, "S1", "2026-07", self.sources)), 1)
            self.assertEqual(reviewed_signal_evidence(self.work, "S1", "2026-08", self.sources), [])
        self.assertEqual(len(self.work["signal_evidence"]), 1)


if __name__ == "__main__":
    unittest.main()
