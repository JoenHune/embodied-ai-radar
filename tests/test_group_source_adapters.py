"""Publication extraction must not execute scripts or fabricate empty results."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("adapters", ROOT / "scripts/group_source_adapters.py")
adapters = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapters)
PAGE = "https://research.nvidia.com/labs/gear/publications/"
HTML = (ROOT / "tests/fixtures/gear-publications-skeleton.html").read_text()
JAVASCRIPT = (ROOT / "tests/fixtures/gear-publications-data.js").read_text()


class GroupSourceAdapterTests(unittest.TestCase):
    def test_discovery_uses_only_declared_same_origin_publication_chunks(self):
        values = adapters.discover_publication_scripts(PAGE, HTML)
        self.assertEqual(values, ["https://research.nvidia.com/labs/gear/_next/static/chunks/pages/publications-fixture.js"])
        self.assertNotIn("tracking.invalid", " ".join(values))

    def test_explicit_resource_origin_supported_but_unlisted_chunk_never_invented(self):
        html = '<script src="https://static.example/research-data.js"></script>'
        self.assertEqual(adapters.discover_publication_scripts(PAGE, html), [])
        self.assertEqual(adapters.discover_publication_scripts(PAGE, html, ["https://static.example"]), ["https://static.example/research-data.js"])
        self.assertEqual(adapters.discover_publication_scripts(PAGE, ""), [])

    def test_javascript_wrapper_is_never_executed_and_records_deduplicate(self):
        parsed = adapters.extract_publication_literals(JAVASCRIPT)
        self.assertEqual(len(parsed["records"]), 2)
        self.assertEqual(parsed["rejected_candidate_count"], 0)
        self.assertIn("javascript_literal", parsed["formats"])
        row = next(row for row in parsed["records"] if "Dream" in row["title"])
        self.assertEqual(row["authors"], "Ada Example, Bert O'Example")
        self.assertTrue(any("π" in row["title"] for row in parsed["records"]))

    def test_adapter_preserves_old_links_and_returns_page_and_script_provenance(self):
        fetched = []
        def fetch(url):
            fetched.append(url)
            return JAVASCRIPT.encode(), "application/javascript"
        result = adapters.adapt_group_publications(PAGE, HTML, fetch, previous_known_links=["https://arxiv.org/abs/2501.12345"])
        self.assertEqual(len(fetched), 1)
        self.assertEqual(result["parser_status"], "parsed")
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(len(result["links"]), 4)
        self.assertTrue(result["previous_links_preserved"])
        self.assertIn("https://arxiv.org/abs/2501.12345", result["known_links"])
        self.assertTrue(all(row["evidence_url"] == PAGE and row["structured_source_url"] in fetched for row in result["links"]))
        self.assertFalse(result["code_executed"])

    def test_fetch_failure_preserves_known_data_and_does_not_claim_zero_publications(self):
        def failed(url):
            raise ValueError("sensitive failure text not exposed")
        result = adapters.adapt_group_publications(PAGE, HTML, failed, previous_known_links=["https://arxiv.org/abs/2501.12345"])
        self.assertEqual(result["parser_status"], "partial")
        self.assertEqual(result["content_state"], "not_loaded")
        self.assertFalse(result["empty_verified"])
        self.assertEqual(len(result["known_links"]), 1)
        self.assertNotIn("sensitive", str(result))

    def test_empty_skeleton_without_script_manifest_remains_partial(self):
        result = adapters.adapt_group_publications(PAGE, "<h1>Publications</h1>", lambda _: self.fail("No fetch"))
        self.assertTrue(result["applicable"])
        self.assertEqual(result["parser_status"], "partial")
        self.assertFalse(result["empty_verified"])

    def test_plain_html_without_dynamic_records_is_not_applicable(self):
        result = adapters.adapt_group_publications("https://lab.example/publications", '<a href="https://arxiv.org/abs/2601.00001">Paper</a>', lambda _: self.fail("No fetch"))
        self.assertFalse(result["applicable"])

    def test_roster_and_home_sources_do_not_emit_g1_publication_data(self):
        for kind in ("people", "home", "hiring"):
            result = adapters.adapt_group_publications(PAGE, HTML, lambda _: self.fail("No fetch"), source_kind=kind)
            self.assertFalse(result["applicable"])

    def test_json_parse_accepts_static_string_but_not_expression(self):
        payload = {"publications": [{"title": "Fixture JSON Paper", "paperLink": "https://arxiv.org/abs/2601.00003"}]}
        literal = json.dumps(json.dumps(payload))
        result = adapters.extract_publication_literals("const data = JSON.parse(" + literal + ");")
        self.assertEqual(len(result["records"]), 1)
        self.assertIn("json_parse_string", result["formats"])
        self.assertEqual(adapters.extract_publication_literals("JSON.parse(" + literal + "+fetchSecret());")["records"], [])

    def test_json_parse_inside_comment_or_string_is_not_a_record(self):
        payload = json.dumps(json.dumps({"title": "Not a publication", "paperLink": "https://arxiv.org/abs/2601.00004"}))
        for text in ["// JSON.parse(" + payload + ")", "/* JSON.parse(" + payload + ") */", json.dumps("JSON.parse(" + payload + ")")]:
            self.assertEqual(adapters.extract_publication_literals(text)["records"], [])

    def test_computed_title_link_or_template_is_rejected(self):
        for text in ['{title: "Fake" + execute(), paperLink:"https://arxiv.org/abs/2601.00005"}',
                     '{title: "Fake", paperLink: makeUrl()}',
                     '{title: `Fake ${execute()}`, paperLink:"https://arxiv.org/abs/2601.00005"}']:
            parsed = adapters.extract_publication_literals(text)
            self.assertEqual(parsed["records"], [])
            self.assertGreater(parsed["rejected_candidate_count"], 0)

    def test_react_renderer_props_are_ignored_not_counted_as_failed_publications(self):
        script = JAVASCRIPT + '; const props = {title:a.title, paperLink:a.paperLink};'
        parsed = adapters.extract_publication_literals(script)
        self.assertEqual(len(parsed["records"]), 2)
        self.assertEqual(parsed["rejected_candidate_count"], 0)
        self.assertEqual(parsed["ignored_expression_objects"], 1)

    def test_inline_json_and_duplicate_title_different_url_preserved(self):
        payload = {"props": {"publications": [{"title": "Same Title", "paperLink": "https://arxiv.org/abs/2601.00001"},
                                               {"title": "Same Title", "paperLink": "https://arxiv.org/abs/2601.00002"}]}}
        html = '<script type="application/json">' + json.dumps(payload) + '</script>'
        result = adapters.adapt_group_publications(PAGE, html, lambda _: self.fail("No fetch"))
        self.assertEqual(len(result["links"]), 2)

    def test_redirect_outside_registered_origins_is_not_read_as_evidence(self):
        result = adapters.adapt_group_publications(PAGE, HTML, lambda _: {"text": JAVASCRIPT, "final_url": "https://unregistered.example/publications.js"})
        self.assertEqual(result["links"], [])
        self.assertIn("resource_redirect_outside_registered_origins", result["errors"])

    def test_unsafe_publication_urls_and_resource_urls_are_rejected(self):
        parsed = adapters.extract_publication_literals('{title:"Unsafe",paperLink:"javascript:execute()"}')
        self.assertEqual(parsed["records"], [])
        html = '<script src="https://secret:token@research.nvidia.com/publications.js"></script><script src="https://[bad/publications.js"></script>'
        self.assertEqual(adapters.discover_publication_scripts(PAGE, html), [])

    def test_unicode_surrogate_pairs_and_depth_size_limits(self):
        value, _ = adapters.string_literal('"\u005c\u0075D83D\u005c\u0075DE00"', 0)
        self.assertEqual(value, "😀")
        oversized = adapters.extract_publication_literals("x" * (adapters.MAX_RESOURCE_BYTES + 1))
        self.assertEqual(oversized["error"], "resource_size_limit")
        with self.assertRaises(adapters.NotLiteral):
            adapters.parse_literal("[" * 30 + "0" + "]" * 30)


if __name__ == "__main__":
    unittest.main()
