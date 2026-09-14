"""A work notice is never a new organizational attribution or paper."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_rules import event_eligible
from build_v3_catalog import organization_event_views, monthly_organization_change


def fixture():
    notice = {"notice_id": "notice:withdraw", "work_id": "work:paper", "event_type": "withdrawn", "scope": "work",
              "public_at": "2026-08-24T07:00:55Z", "date_precision": "second", "source_record_ids": ["source:notice"],
              "source_url": "https://example.test/official-withdrawal", "review_status": "verified", "summary_zh": "官方撤回通知。"}
    work = {"work_id": "work:paper", "title": "Original paper", "aliases": ["arxiv:2607.00001"], "authors": ["Ada Researcher"],
            "first_public_date": "2026-07-06", "first_public_date_precision": "day", "relevance": {"status": "included"},
            "current_employer": "org:new-employer", "source_record_ids": ["source:notice"], "research_status_notices": [notice]}
    event = {"event_id": "event:status", "work_id": work["work_id"], "event_type": notice["event_type"], "scope": "work", "title": work["title"],
             "summary_zh": notice["summary_zh"], "research_status_notice_id": notice["notice_id"], "review_status": "verified",
             "published_at": notice["public_at"], "public_at": notice["public_at"], "occurred_at": notice["public_at"],
             "date_precision": notice["date_precision"], "url": notice["source_url"], "source_url": notice["source_url"],
             "source_record_id": "source:notice", "source_record_ids": ["source:notice"]}
    links = {work["work_id"]: {
        "org:direct-lab": {"work_id": work["work_id"], "organization_id": "org:direct-lab", "evidence_grade": "G1", "evidence_url": "https://example.edu/lab/papers", "attribution_basis": "official publication list"},
        "org:historic-lab": {"work_id": work["work_id"], "organization_id": "org:historic-lab", "evidence_grade": "G2", "evidence_url": "https://example.edu/member-history",
                             "membership_evidence": {"author": "Ada Researcher", "valid_from": "2025-01-01", "valid_to": "2026-07-31", "source_url": "https://example.edu/member-history"}},
    }}
    return work, event, links


class StatusOrganizationEventsTests(unittest.TestCase):
    def test_verified_work_notice_is_global_event_without_g1_or_org(self):
        work, event, links = fixture()
        self.assertNotIn("attribution_grade", event)
        self.assertNotIn("organization_id", event)
        self.assertTrue(event_eligible(event, work))
        self.assertFalse(event_eligible({**event, "research_status_notice_id": "unknown"}, work))
        self.assertFalse(event_eligible({**event, "research_status_notice_id": None, "attribution_grade": "G1"}, work))

    def test_all_supported_notice_types_match_the_authority_notice(self):
        for kind in ["withdrawn", "retracted", "corrected", "expression_of_concern", "reinstated"]:
            work, event, links = fixture()
            work["research_status_notices"][0]["event_type"] = event["event_type"] = kind
            self.assertTrue(event_eligible(event, work), kind)

    def test_missing_or_duplicate_notice_identity_cannot_bypass_matching(self):
        work, event, links = fixture()
        event.pop("research_status_notice_id")
        work["research_status_notices"][0].pop("notice_id")
        self.assertFalse(event_eligible(event, work))
        work, event, links = fixture()
        work["research_status_notices"].append(copy.deepcopy(work["research_status_notices"][0]))
        self.assertFalse(event_eligible(event, work))

    def test_date_precision_type_and_source_conflicts_cannot_enter_formal_events(self):
        changes = [{"event_type": "corrected"}, {"published_at": "2026-08-25"}, {"public_at": "2026-08-25"},
                   {"occurred_at": "2026-08-25"}, {"date_precision": "day"}, {"url": "https://example.test/other"},
                   {"source_url": "https://example.test/other"}, {"source_record_id": "wrong"}, {"source_record_ids": ["wrong"]},
                   {"scope": "organization"}, {"review_status": "draft"}, {"work_id": "work:other"}, {"attribution_grade": "G3"}]
        for change in changes:
            with self.subTest(change=change):
                work, event, links = fixture()
                event.update(change)
                self.assertFalse(event_eligible(event, work))
                self.assertEqual(organization_event_views([event], links, {work["work_id"]: work}), [])

    def test_included_and_review_flags_are_required_for_notice_and_event(self):
        for target in ["event", "notice"]:
            for flag in ["review_required", "date_review_required", "source_review_required", "date_conflict", "source_conflict"]:
                work, event, links = fixture()
                (event if target == "event" else work["research_status_notices"][0])[flag] = True
                self.assertFalse(event_eligible(event, work), (target, flag))
        for state in ["candidate", "manual_review", "excluded"]:
            work, event, links = fixture()
            work["relevance"]["status"] = state
            self.assertFalse(event_eligible(event, work))

    def test_unknown_date_unverified_or_wrong_work_notice_is_not_a_fact(self):
        for change in [{"public_at": None, "date_precision": "unknown"}, {"review_status": "draft"}, {"work_id": "work:other"}, {"scope": "manifestation"}]:
            work, event, links = fixture()
            work["research_status_notices"][0].update(change)
            self.assertFalse(event_eligible(event, work))
        work, event, links = fixture()
        work["source_record_ids"] = []
        self.assertFalse(event_eligible(event, work))

    def test_organization_views_require_work_context_and_only_use_historical_links(self):
        work, event, links = fixture()
        self.assertEqual(organization_event_views([event], links), [])
        # The author left the historic lab before the withdrawal, but was a
        # member when the paper appeared. Notice time is NOT affiliation time.
        views = organization_event_views([event], links, {work["work_id"]: work})
        self.assertEqual({view["organization_id"] for view in views}, {"org:direct-lab", "org:historic-lab"})
        self.assertNotIn("org:new-employer", {view["organization_id"] for view in views})
        self.assertTrue(all(event_eligible(view, work) for view in views))

    def test_event_claimed_org_does_not_create_an_attribution(self):
        work, event, links = fixture()
        event["organization_id"] = "org:new-employer"
        views = organization_event_views([event], links, {work["work_id"]: work})
        self.assertEqual({view["organization_id"] for view in views}, set(links[work["work_id"]]))
        self.assertEqual(organization_event_views([event], {}, {work["work_id"]: work}), [])
        self.assertTrue(event_eligible(event, work), 'The reliable work-level notice stays globally eligible without any lab attribution')

    def test_g0_g3_reviewed_conflict_or_invalid_membership_links_not_fanned_out(self):
        for change in [{"evidence_grade": "G0"}, {"evidence_grade": "G3"}, {"review_required": True}, {"date_review_required": True},
                       {"source_conflict": True}, {"review_status": "draft"}, {"organization_id": "wrong"}, {"work_id": "wrong"},
                       {"evidence_url": "javascript:alert(1)"}, {"evidence_url": "https://example.edu bad/path"},
                       {"membership_evidence": {"author": "Ada Researcher", "valid_from": "2026-08-01", "source_url": "https://example.edu/member-history"}}]:
            work, event, links = fixture()
            links[work["work_id"]]["org:historic-lab"].update(change)
            views = organization_event_views([event], links, {work["work_id"]: work})
            self.assertEqual([view["organization_id"] for view in views], ["org:direct-lab"], change)

    def test_shared_event_id_and_original_attribution_survive_monthly_projection(self):
        work, event, links = fixture()
        before = copy.deepcopy((work, event, links))
        views = organization_event_views([event], links, {work["work_id"]: work})
        self.assertEqual((work, event, links), before)
        self.assertEqual({view["event_id"] for view in views}, {event["event_id"]})
        self.assertEqual({view["source_event_id"] for view in views}, {event["event_id"]})
        for view in views:
            self.assertFalse(view["statement_publisher_is_organization"])
            self.assertIn("该组已归属工作的状态变化", view["summary_zh"])
            self.assertIn("不表示该组发布声明", view["summary_zh"])
            compact = monthly_organization_change(view, {"display_name": view["organization_id"], "tier": "T0"})
            self.assertEqual(compact["source_event_id"], event["event_id"])
            self.assertEqual(compact["research_status_notice_id"], event["research_status_notice_id"])
            self.assertEqual(compact["original_work_attribution"], links[work["work_id"]][view["organization_id"]])
            self.assertEqual(compact["published_at"], event["published_at"])
            self.assertEqual(compact["date_precision"], "second")
        self.assertEqual(work["first_public_date"], "2026-07-06")
        self.assertEqual(len({view["work_id"] for view in views}), 1)

    def test_ordinary_acceptance_and_publication_remain_backward_compatible(self):
        event = {"event_id": "accepted", "event_type": "accepted", "work_id": "w", "organization_id": None}
        links = {"w": {"lab": {"evidence_grade": "G1", "evidence_url": "https://example.edu/papers"}}}
        views = organization_event_views([event], links)
        self.assertEqual(len(views), 1)
        self.assertNotIn("research_status_notice_id", views[0])
        self.assertNotIn("statement_publisher_is_organization", views[0])


if __name__ == "__main__":
    unittest.main()
