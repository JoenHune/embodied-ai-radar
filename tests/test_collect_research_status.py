"""Template-shaped fixtures, not archived live HTML or a batch collection."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from scripts import collect_research_status as collector
from scripts.ingest_research_status import apply_research_status_additions

BASE = "2607.04837"
WORK = "arxiv:" + BASE
URL = "https://arxiv.org/abs/" + BASE + "v3"
OBSERVED = "2026-09-06T09:00:00Z"
HISTORY = """<strong><a href="/abs/2607.04837v1">[v1]</a></strong> Mon, 6 Jul 2026 09:10:04 UTC (100 KB)<br/>
<strong><a href="/abs/2607.04837v2">[v2]</a></strong> Tue, 7 Jul 2026 03:57:02 UTC (100 KB)<br/>
<strong>[v3]</strong> Mon, 24 Aug 2026 07:00:55 UTC (1 KB) <em>(withdrawn)</em><br/>"""


def html_fixture(*, version="v3", banner="This paper has been withdrawn by Example Author", history=HISTORY,
                 abstract="Synthetic research abstract.", comments="Withdrawn for a synthetic fixture reason that must not become an independently verified causal explanation."):
    status = f'<span class="error" style="border: 2px solid grey">{banner}</span>' if banner else ""
    return f"""<!DOCTYPE html><html><head><title>[{BASE}{version}] Synthetic research title</title>
<meta property="og:url" content="https://arxiv.org/abs/{BASE}{version}"/>
<meta name="citation_arxiv_id" content="{BASE}"/></head><body><div class="leftcolumn">
<div id="content-inner"><div id="abs">{status}<div class="dateline">Submitted version</div>
<h1 class="title mathjax"><span class="descriptor">Title:</span>Synthetic research title</h1>
<blockquote class="abstract mathjax">{abstract}</blockquote>
<div class="metatable"><table><tr><td>Comments:</td><td class="tablecell comments mathjax">{comments}</td></tr></table></div>
</div></div><div class="submission-history"><h2>Submission history</h2>From: Example Author<br/>{history}</div>
</div></body></html>"""


class CollectResearchStatusTests(unittest.TestCase):
    def extract(self, html=None, **kwargs):
        return collector.extract_arxiv_status(html or html_fixture(), kwargs.get("url", URL), kwargs.get("work_id", WORK), kwargs.get("observed_at", OBSERVED))

    def test_header_and_same_version_utc_marker_produce_importable_notice(self):
        notice = self.extract()
        self.assertEqual(notice["event_type"], "withdrawn")
        self.assertEqual(notice["public_at"], "2026-08-24T07:00:55Z")
        self.assertNotEqual(notice["public_at"], OBSERVED)
        self.assertEqual(notice["date_precision"], "second")
        self.assertEqual(notice["source_record"]["observed_at"], OBSERVED)
        self.assertEqual(notice["source_record"]["published_at"], notice["public_at"])
        self.assertEqual(notice["source_record"]["raw"]["version"], "v3")
        payload = {"works": [{"work_id": WORK, "title": "Synthetic title", "identifiers": {"arxiv": BASE}, "first_public_date": "2026-07-06", "source_record_ids": []}],
                   "manifestations": [], "source-records": [], "evidence-events": [], "field-provenance": [], "work-aliases": []}
        result = apply_research_status_additions(payload, [notice])
        self.assertEqual(result["works"][0]["first_public_date"], "2026-07-06")
        self.assertEqual(result["works"][0]["research_status_notices"][0]["notice_id"], notice["notice_id"])

    def test_abstract_and_reference_mentions_do_not_trigger_status(self):
        history = HISTORY.replace("<em>(withdrawn)</em>", "")
        for abstract in ("The robot must withdraw its gripper.", "This paper has been withdrawn is quoted from a related reference.",
                         '<span class="error">This paper has been withdrawn</span>'):
            self.assertIsNone(self.extract(html_fixture(banner="", history=history, abstract=abstract, comments="")))

    def test_comments_are_only_review_hints_not_withdrawal_decisions(self):
        value = self.extract(html_fixture(banner="", history=HISTORY.replace("<em>(withdrawn)</em>", ""), comments="Withdrawn by the authors."))
        self.assertEqual(value["status"], "review_required")
        self.assertNotIn("event_type", value)

    def test_both_header_and_matching_version_marker_are_required(self):
        for html in (html_fixture(banner="", comments=""), html_fixture(history=HISTORY.replace("<em>(withdrawn)</em>", ""))):
            result = self.extract(html)
            self.assertEqual(result["status"], "review_required")
            self.assertNotIn("public_at", result)

    def test_older_version_banner_never_backdates_newer_withdrawal(self):
        result = self.extract(html_fixture(version="v2", banner="A newer version of this paper has been withdrawn by Example Author"), url=URL.replace("v3", "v2"))
        self.assertEqual(result["error_code"], "newer_version_withdrawn_not_requested_version")
        self.assertEqual(result["suggested_source_url"], URL)
        self.assertNotIn("public_at", result)

    def test_missing_or_non_utc_target_date_never_uses_observation_as_status_date(self):
        for replacement in ("24 Aug 2026", "Mon, 24 Aug 2026 07:00:55 GMT", "Mon, 24 Aug 2026 15:00:55 +08:00"):
            history = HISTORY.replace("Mon, 24 Aug 2026 07:00:55 UTC", replacement)
            result = self.extract(html_fixture(history=history))
            self.assertEqual(result["error_code"], "requested_status_version_has_no_utc_time")
            self.assertNotIn("public_at", result)

    def test_work_host_path_and_version_identity_are_strict(self):
        for url in ("http://arxiv.org/abs/2607.04837v3", "https://arxiv.org.evil.test/abs/2607.04837v3", "https://arxiv.org/abs/2607.04837",
                    "https://arxiv.org/pdf/2607.04837v3", "https://user:secret@arxiv.org/abs/2607.04837v3", URL + "?redirect=example.test"):
            result = self.extract(url=url)
            self.assertEqual(result["error_code"], "official_versioned_arxiv_url_required")
            self.assertNotIn("secret", json.dumps(result))
        self.assertEqual(self.extract(work_id="arxiv:2607.99999")["error_code"], "work_identity_mismatch")
        self.assertEqual(self.extract(html_fixture(version="v2"))["error_code"], "page_version_identity_mismatch")
        html = html_fixture().replace(f'content="{BASE}"', 'content="2607.99999"')
        self.assertEqual(self.extract(html)["error_code"], "page_work_identity_mismatch")

    def test_malformed_or_future_times_require_review(self):
        for observed in ("2026-09-06", "2026-09-06T17:00:00+08:00", "2026-08-24T06:00:00Z"):
            self.assertEqual(self.extract(observed_at=observed)["status"], "review_required")
        result = self.extract(html_fixture(history=HISTORY.replace("Mon, 24 Aug", "Tue, 24 Aug")))
        self.assertEqual(result["error_code"], "submission_history_weekday_mismatch")

    def test_reinstatement_needs_explicit_header_and_same_version_marker(self):
        history = HISTORY + "<strong>[v4]</strong> Tue, 25 Aug 2026 10:00:00 UTC (100 KB) <em>(reinstated)</em><br/>"
        url = URL.replace("v3", "v4")
        notice = self.extract(html_fixture(version="v4", banner="This paper has been reinstated", history=history), url=url)
        self.assertEqual(notice["event_type"], "reinstated")
        self.assertEqual(notice["public_at"], "2026-08-25T10:00:00Z")
        normal = html_fixture(version="v4", banner="", history=history.replace("<em>(reinstated)</em>", ""), comments="Updated manuscript.")
        result = self.extract(normal, url=url)
        self.assertEqual(result["status"], "review_required")
        self.assertNotIn("event_type", result)

    def test_conflicting_or_duplicate_status_structure_is_not_accepted(self):
        history = HISTORY + "<strong>[v3]</strong> Mon, 24 Aug 2026 07:00:55 UTC (withdrawn)"
        self.assertEqual(self.extract(html_fixture(history=history))["error_code"], "duplicate_submission_history_version")
        html = html_fixture().replace('<div class="dateline">', '<span class="error">This paper has been reinstated</span><div class="dateline">')
        self.assertEqual(self.extract(html)["error_code"], "ambiguous_official_status_banner")
        self.assertEqual(self.extract("<html><body>error</body></html>")["status"], "review_required")

    def test_excerpt_budget_is_global_and_reason_is_metadata_not_a_causal_claim(self):
        comments = "Withdrawn because " + "authorization governance uncertainty " * 100
        notice = self.extract(html_fixture(comments=comments))
        raw = notice["source_record"]["raw"]
        words = sum(len(collector.WORD.findall(row["text"])) for row in raw["excerpts"])
        self.assertLessEqual(words, 25)
        self.assertEqual(raw["excerpt_word_count"], words)
        self.assertEqual(raw["html_sha256"], collector._sha(html_fixture(comments=comments)))
        reason = next(row for row in raw["excerpts"] if row["label"] == "comments_metadata_fragment")
        self.assertTrue(reason["truncated"])
        self.assertEqual(reason["text"], comments[reason["start"]:reason["end"]])
        self.assertEqual(reason["interpretation"], "source_metadata_only_not_a_verified_causal_explanation")
        self.assertNotIn("authorization", notice["summary_zh"])
        self.assertNotIn("abstract", raw)

    def test_identical_observations_have_stable_ids_and_keep_first_observation(self):
        notice = self.extract()
        again = self.extract(observed_at="2026-09-07T00:00:00Z")
        self.assertEqual(notice["notice_id"], again["notice_id"])
        self.assertEqual(notice["source_record_ids"], again["source_record_ids"])
        before = copy.deepcopy(notice)
        self.assertEqual(collector.merge_status_notice([notice], again), [notice])
        self.assertEqual(notice, before)

    def test_changed_content_conflicts_without_overwriting_existing_notice(self):
        notice, existing = self.extract(), [self.extract()]
        changed = self.extract(html_fixture() + "<!-- updated source metadata -->")
        self.assertEqual(notice["notice_id"], changed["notice_id"])
        self.assertNotEqual(notice["source_record_ids"], changed["source_record_ids"])
        before = copy.deepcopy(existing)
        with self.assertRaisesRegex(collector.StatusExtractionError, "notice_content_conflict"):
            collector.merge_status_notice(existing, changed)
        self.assertEqual(existing, before)

    def test_cli_defaults_to_stdout_and_only_explicit_output_creates_staging(self):
        output = io.StringIO()
        with patch.object(collector, "fetch_html", return_value=html_fixture()), contextlib.redirect_stdout(output):
            self.assertEqual(collector.main(["--work-id", WORK, "--url", URL]), 0)
        self.assertEqual(json.loads(output.getvalue())["event_type"], "withdrawn")
        with tempfile.TemporaryDirectory(prefix="status-collector-fixture-") as directory:
            path = Path(directory) / "status-additions.jsonl"
            argv = ["--work-id", WORK, "--url", URL, "--output", str(path)]
            with patch.object(collector, "fetch_html", return_value=html_fixture()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(collector.main(argv), 0)
                first = path.read_bytes()
                self.assertEqual(collector.main(argv), 0)
                self.assertEqual(path.read_bytes(), first)
            with patch.object(collector, "fetch_html", return_value=html_fixture() + "<!-- changed -->"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(collector.main(argv), 2)
            self.assertEqual(path.read_bytes(), first)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_cli_does_not_append_review_records_or_fetch_invalid_sources(self):
        with patch.object(collector, "fetch_html") as fetch, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(collector.main(["--work-id", WORK, "--url", "https://example.test/abs/2607.04837v3"]), 2)
            fetch.assert_not_called()
        with tempfile.TemporaryDirectory(prefix="status-review-fixture-") as directory:
            path = Path(directory) / "status-additions.jsonl"
            with patch.object(collector, "fetch_html", return_value=html_fixture(banner="", comments="")), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(collector.main(["--work-id", WORK, "--url", URL, "--output", str(path)]), 2)
            self.assertFalse(path.exists())

    def test_cli_http_failure_is_reviewable_and_does_not_echo_provider_body(self):
        output = io.StringIO()
        error = urllib.error.HTTPError(URL, 403, "private provider message", {}, None)
        with patch.object(collector, "fetch_html", side_effect=error), contextlib.redirect_stdout(output):
            self.assertEqual(collector.main(["--work-id", WORK, "--url", URL]), 2)
        result = json.loads(output.getvalue())
        self.assertEqual(result["http_status"], 403)
        self.assertNotIn("private", output.getvalue())

    def test_fetch_helper_itself_rejects_untrusted_urls_before_network(self):
        with patch.object(collector.urllib.request, "build_opener") as opener:
            with self.assertRaisesRegex(collector.StatusExtractionError, "official_versioned_arxiv_url_required"):
                collector.fetch_html("http://127.0.0.1/abs/2607.04837v3")
            opener.assert_not_called()

    def test_redirects_cannot_leave_the_explicit_official_version(self):
        with self.assertRaisesRegex(collector.StatusExtractionError, "redirect_requires_review"):
            collector._NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://elsewhere.example/notice")


if __name__ == "__main__":
    unittest.main()
