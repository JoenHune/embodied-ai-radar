"""Known-ID polling fixtures never perform real network requests."""
from __future__ import annotations

import copy
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from scripts import research_status_watch as watch

A, B = "2601.12345", "2401.54321"
WHEN = "2026-09-06T10:00:00Z"


def work(base, **extra):
    return {"work_id": "arxiv:" + base, "identifiers": {"arxiv": base}, "first_public_date": "2024-01-01", **extra}


def metadata(base, version="v2", updated="2026-08-24T07:00:55Z", comment="Routine metadata."):
    return {"arxiv_id": base, "latest_version": version, "updated_at": updated, "comment": comment}


def notice(base=A, version="v2", state="withdrawn", public_at="2026-08-24T07:00:55Z", observed_at=WHEN, source_id="source:new-observation"):
    url = f"https://arxiv.org/abs/{base}{version}"
    return {"notice_id": f"notice:fixture:{base}:{version}:{state}", "work_id": "arxiv:" + base, "event_type": state,
            "scope": "work", "public_at": public_at, "date_precision": "second", "source_record_ids": [source_id],
            "source_url": url, "review_status": "verified", "summary_zh": "官方版本明确标注状态。",
            "source_record": {"source_record_id": source_id, "url": url, "published_at": public_at, "observed_at": observed_at,
                              "source_type": "official_arxiv_status_notice", "raw": {"status": state, "version": version}}}


def known_notice(**kwargs):
    value = notice(**kwargs)
    value.pop("source_record")
    value["notice_id"] = "notice:legacy-human-identity"
    return value


class ResearchStatusWatchTests(unittest.TestCase):
    def run_watch(self, works=None, preprints=None, rows=None, status=None, **kwargs):
        return watch.watch_research_status(works or [work(A)], preprints or [],
                                          metadata_fetcher=lambda ids: rows if rows is not None else [metadata(base) for base in ids],
                                          status_fetcher=status or (lambda *_: None), sleeper=lambda _: None, observed_at=WHEN, **kwargs)

    def test_first_run_checks_all_registered_ids_regardless_age_or_relevance(self):
        calls = []
        works = [work(A), work(B, relevance={"status": "excluded"}), {"work_id": "doi:10.1234/no-arxiv"}]
        result = self.run_watch(works, status=lambda url, wid, stamp: calls.append((url, wid, stamp)))
        self.assertEqual(result["coverage"]["requested_ids"], sorted([A, B]))
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["coverage"]["status"], "complete")
        self.assertEqual(result["notice_candidates"], [])
        self.assertEqual(len(result["observations"]), 4)

    def test_old_papers_new_version_is_checked_and_can_produce_a_candidate(self):
        old = {"arxiv_id": B, "updated": "2024-01-02", "pdf_url": f"https://arxiv.org/pdf/{B}v1", "comment": "Preprint"}
        result = self.run_watch([work(B)], [old], status=lambda *_: notice(B))
        self.assertEqual(result["notice_candidates"][0]["work_id"], "arxiv:" + B)
        observation = result["observations"][0]
        self.assertIn("latest_version_changed", observation["reasons"])
        self.assertTrue(result["metadata_updates"][0]["status_check_pending"])

    def test_unchanged_metadata_without_notice_or_hint_does_not_fetch_page(self):
        baseline = metadata(A)
        result = self.run_watch(preprints=[baseline], status=lambda *_: self.fail("No page fetch for unchanged ordinary metadata"))
        self.assertEqual(result["coverage"]["status_pages"]["requested"], 0)
        self.assertEqual(result["observations"][0]["outcome"], "unchanged")

    def test_withdrawal_comment_triggers_page_check_but_is_not_a_status_fact(self):
        row = metadata(A, comment="Withdrawn by authors pending review.")
        calls = []
        result = self.run_watch(preprints=[row], rows=[row], status=lambda *_: calls.append(True))
        self.assertEqual(calls, [True])
        self.assertEqual(result["notice_candidates"], [])
        self.assertIn("status_comment_hint", result["observations"][0]["reasons"])

    def test_same_logical_notice_does_not_reimport_different_observation_sources(self):
        existing = known_notice(source_id="source:first-official-check")
        source_work = work(A, research_status_notices=[existing])
        before = copy.deepcopy(source_work)
        incoming = notice(source_id="source:later-official-check")
        result = self.run_watch([source_work], [metadata(A)], status=lambda *_: incoming)
        self.assertEqual(result["notice_candidates"], [])
        self.assertEqual(source_work, before)
        observed = next(row for row in result["observations"] if row["kind"] == "version_status")
        self.assertEqual(observed["outcome"], "known_notice_observed")
        self.assertEqual(observed["notice_id"], "notice:legacy-human-identity")
        self.assertEqual(observed["observed_source_record"]["source_record_id"], "source:later-official-check")
        self.assertEqual(existing["source_record_ids"], ["source:first-official-check"])
        self.assertFalse(result["metadata_updates"][0]["status_check_pending"])

    def test_doi_canonical_work_is_checked_via_its_registered_arxiv_identity(self):
        value = work(A, work_id="doi:10.9999/example", aliases=["arxiv:" + A])
        existing = known_notice()
        existing["work_id"] = value["work_id"]
        result = self.run_watch([value], [metadata(A)], verified_notices=[existing], status=lambda *_: notice())
        self.assertEqual(result["coverage"]["requested_ids"], [A])
        self.assertEqual(result["notice_candidates"], [])
        self.assertEqual(result["observations"][-1]["outcome"], "known_notice_observed")

    def test_foreign_notice_cannot_suppress_a_new_candidate(self):
        foreign = known_notice()
        foreign["work_id"] = "arxiv:" + B
        result = self.run_watch(verified_notices=[foreign], status=lambda *_: notice())
        self.assertEqual(len(result["notice_candidates"]), 1)
        self.assertTrue(any(row["error_code"] == "known_notice_work_identity_mismatch" for row in result["review_queue"]))

    def test_repeated_checks_retain_distinct_observation_ids_not_new_notices(self):
        existing = known_notice()
        values = []
        for when in (WHEN, "2026-09-13T10:00:00Z"):
            values.append(watch.watch_research_status([work(A)], [metadata(A)], verified_notices=[existing],
                                                     metadata_fetcher=lambda _: [metadata(A)],
                                                     status_fetcher=lambda _, __, stamp: notice(observed_at=stamp), sleeper=lambda _: None, observed_at=when))
        self.assertEqual(values[0]["notice_candidates"], values[1]["notice_candidates"])
        self.assertEqual(values[0]["notice_candidates"], [])
        self.assertNotEqual(values[0]["observations"][-1]["observation_id"], values[1]["observations"][-1]["observation_id"])

    def test_existing_notice_date_or_state_conflicts_are_reviewed_not_overwritten(self):
        existing = known_notice()
        before = copy.deepcopy(existing)
        for incoming in (notice(public_at="2026-08-25T07:00:55Z"), notice(state="reinstated")):
            result = self.run_watch(preprints=[metadata(A)], verified_notices=[existing], status=lambda *_: incoming)
            self.assertEqual(result["notice_candidates"], [])
            self.assertTrue(any(row["error_code"] == "known_notice_state_or_date_conflict" for row in result["review_queue"]))
            self.assertEqual(existing, before)

    def test_equivalent_utc_spellings_are_not_false_notice_date_conflicts(self):
        existing = known_notice(public_at="2026-08-24T07:00:55+00:00")
        result = self.run_watch(preprints=[metadata(A)], verified_notices=[existing], status=lambda *_: notice())
        self.assertEqual(result["review_queue"], [])
        self.assertEqual(result["notice_candidates"], [])

    def test_normal_new_version_does_not_reinstate_previously_withdrawn_work(self):
        existing = known_notice()
        result = self.run_watch(preprints=[metadata(A)], rows=[metadata(A, version="v3")], verified_notices=[existing])
        self.assertEqual(result["notice_candidates"], [])
        self.assertEqual(existing["event_type"], "withdrawn")
        self.assertTrue(any(row["error_code"] == "no_explicit_status_for_previously_noticed_work" for row in result["review_queue"]))
        self.assertEqual(result["observations"][-1]["retained_notice_ids"], [existing["notice_id"]])

    def test_explicit_new_version_reinstatement_remains_a_separate_candidate(self):
        result = self.run_watch(preprints=[metadata(A)], rows=[metadata(A, version="v3")], verified_notices=[known_notice()],
                                status=lambda *_: notice(version="v3", state="reinstated", public_at="2026-08-25T00:00:00Z"))
        self.assertEqual(result["notice_candidates"][0]["event_type"], "reinstated")

    def test_short_response_has_missing_ids_and_is_never_complete(self):
        result = self.run_watch([work(A), work(B)], rows=[metadata(A)])
        self.assertEqual(result["coverage"]["requested_count"], 2)
        self.assertEqual(result["coverage"]["returned_ids"], [A])
        self.assertEqual(result["coverage"]["missing_ids"], [B])
        self.assertFalse(result["coverage"]["metadata_complete"])
        self.assertEqual(result["coverage"]["status"], "partial")
        self.assertTrue(any(row["arxiv_id"] == B and row["outcome"] == "missing_from_response" for row in result["observations"]))

    def test_metadata_failure_is_recorded_without_exposing_exception_text(self):
        def fail(_):
            raise OSError("private provider payload should not be emitted")
        result = watch.watch_research_status([work(A)], [], metadata_fetcher=fail, sleeper=lambda _: None, observed_at=WHEN)
        self.assertEqual(result["coverage"]["status"], "failed")
        self.assertEqual(result["coverage"]["missing_ids"], [A])
        self.assertNotIn("private provider", str(result))

    def test_one_failed_batch_does_not_block_another_batch(self):
        def fetch(ids):
            if ids == [B]:
                raise OSError("fixture failure")
            return [metadata(base) for base in ids]
        result = watch.watch_research_status([work(A), work(B)], [], metadata_fetcher=fetch, status_fetcher=lambda *_: notice(A),
                                             sleeper=lambda _: None, observed_at=WHEN, batch_size=1)
        self.assertEqual(result["coverage"]["status"], "partial")
        self.assertEqual(result["coverage"]["missing_ids"], [B])
        self.assertEqual(len(result["notice_candidates"]), 1)

    def test_page_failure_retries_even_if_new_metadata_baseline_was_persisted(self):
        def fail(*_):
            raise OSError("fixture page failure")
        first = self.run_watch(status=fail)
        self.assertTrue(first["metadata_updates"][0]["status_check_pending"])
        calls = []
        second = self.run_watch(preprints=first["metadata_updates"], status=lambda *_: calls.append(True))
        self.assertEqual(calls, [True])
        self.assertIn("previous_status_check_pending", second["observations"][0]["reasons"])
        self.assertFalse(second["metadata_updates"][0]["status_check_pending"])

    def test_partial_page_failures_keep_good_candidates_and_original_inputs(self):
        works, baseline = [work(A), work(B)], [metadata(A, version="v1"), metadata(B, version="v1")]
        before = copy.deepcopy((works, baseline))
        def fetch(url, wid, when):
            if wid == "arxiv:" + B:
                raise OSError("fixture failure")
            return notice(A, observed_at=when)
        result = self.run_watch(works, baseline, status=fetch)
        self.assertEqual((works, baseline), before)
        self.assertEqual(len(result["notice_candidates"]), 1)
        self.assertEqual(result["coverage"]["status_pages"]["failed"], 1)
        self.assertEqual(result["coverage"]["status"], "partial")

    def test_batches_are_at_most_200_and_all_public_requests_have_polite_gaps(self):
        bases = [f"2601.{index:05d}" for index in range(401)]
        batches, sleeps = [], []
        def fetch(ids):
            batches.append(ids)
            return [metadata(base) for base in ids]
        result = watch.watch_research_status([work(base) for base in bases], [metadata(base) for base in bases], metadata_fetcher=fetch,
                                             status_fetcher=lambda *_: self.fail("Unchanged rows should not fetch pages"), sleeper=sleeps.append, observed_at=WHEN)
        self.assertEqual([len(batch) for batch in batches], [200, 200, 1])
        self.assertEqual(sleeps, [3.0, 3.0])
        self.assertEqual(result["coverage"]["requested_count"], 401)
        sleeps.clear()
        watch.watch_research_status([work(A), work(B)], [], metadata_fetcher=lambda ids: [metadata(base) for base in ids],
                                    status_fetcher=lambda *_: None, sleeper=sleeps.append, observed_at=WHEN, batch_size=1)
        self.assertEqual(sleeps, [3.0, 3.0, 3.0])

    def test_unexpected_duplicate_or_versionless_ids_are_not_silently_accepted(self):
        for rows in ([metadata(A), metadata(B)], [metadata(A), metadata(A)], [{"arxiv_id": A, "comment": "routine"}]):
            result = self.run_watch(rows=rows)
            self.assertEqual(result["coverage"]["status"], "partial")
            self.assertEqual(result["notice_candidates"], [])
        result = self.run_watch(preprints=[metadata(A, version="v3")], rows=[metadata(A, version="v2")])
        self.assertEqual(result["metadata_updates"], [])
        self.assertTrue(any(row["error_code"] == "latest_version_regressed" for row in result["review_queue"]))

    def test_extractor_review_result_is_preserved_as_review_not_notice(self):
        result = self.run_watch(status=lambda *_: {"status": "review_required", "error_code": "newer_version_withdrawn_not_requested_version", "suggested_source_url": URL_FOR_NEWER})
        self.assertEqual(result["notice_candidates"], [])
        self.assertEqual(result["review_queue"][0]["extractor_result"]["suggested_source_url"], URL_FOR_NEWER)

    def test_invalid_extractor_source_identity_is_not_a_candidate(self):
        bad = notice()
        bad["source_record"]["url"] = "https://arxiv.org/abs/9999.99999v2"
        result = self.run_watch(status=lambda *_: bad)
        self.assertEqual(result["notice_candidates"], [])
        self.assertTrue(any(row["error_code"] == "status_notice_identity_or_scope_mismatch" for row in result["review_queue"]))

    def test_atom_parser_preserves_update_version_and_comment(self):
        body = f'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom"><entry>
<id>https://arxiv.org/abs/{A}v3</id><updated>2026-08-24T07:00:55Z</updated><arxiv:comment>Withdrawn by authors.</arxiv:comment>
</entry></feed>'''
        result = self.run_watch(rows=body, status=lambda *_: notice(version="v3"))
        self.assertEqual(result["metadata_updates"][0]["latest_version"], "v3")
        self.assertTrue(result["metadata_updates"][0]["status_comment_hint"])

    def test_default_api_requests_only_explicit_known_ids(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, _): return b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        with patch.object(watch.urllib.request, "urlopen", return_value=Response()) as fetch:
            self.assertEqual(watch.fetch_latest_metadata([A, B]), [])
        request = fetch.call_args.args[0]
        parsed = urlsplit(request.full_url)
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "export.arxiv.org")
        self.assertEqual(query["id_list"], [f"{A},{B}"])
        self.assertNotIn("search_query", query)
        self.assertNotIn("Authorization", request.headers)

    def test_empty_scope_does_not_scan_baseline_only_ids_or_use_network(self):
        result = watch.watch_research_status([], [metadata(A)], metadata_fetcher=lambda _: self.fail("No registered work"), observed_at=WHEN)
        self.assertEqual(result["coverage"]["status"], "not_run")
        self.assertEqual(result["coverage"]["request_count"], 0)
        self.assertEqual(result["observations"], [])


URL_FOR_NEWER = f"https://arxiv.org/abs/{A}v4"


if __name__ == "__main__":
    unittest.main()
