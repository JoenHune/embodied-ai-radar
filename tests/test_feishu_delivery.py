"""Dedicated-app publication tests; every remote operation is mocked."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publish_group_weekly_to_feishu as publisher


class FeishuDeliveryTest(unittest.TestCase):
    def test_markdown_links_remain_clickable_and_model_underscores_survive(self):
        blocks = publisher.markdown_blocks("# Week\n\n- Source: [Dyna_2](<https://example.org/report?a=1&b=2>)\n")
        elements = blocks[0]["bullet"]["elements"]
        self.assertEqual("".join(row["text_run"]["content"] for row in elements), "Source: Dyna_2")
        self.assertEqual(elements[-1]["text_run"]["text_element_style"]["link"]["url"], "https://example.org/report?a=1&b=2")
        self.assertEqual(publisher.plain_inline(r"technical\_report"), "technical_report")

    def test_index_contains_period_three_findings_and_focus_groups(self):
        markdown = "# Week\n覆盖北京时间 2026-08-24—2026-08-30；生成于 timestamp。\n## 本周判断\n- 第一条\n- 第二条\n- 第三条\n## 本周研究变化\n### GEAR · Paper\n### Physical Intelligence · Report\n"
        summary = publisher.index_summary(markdown)
        for item in ["2026-08-24—2026-08-30", "第一条", "第二条", "第三条", "GEAR", "Physical Intelligence"]:
            self.assertIn(item, summary)
        self.assertNotIn("timestamp", summary)

    def test_delete_uses_root_children_not_all_descendant_blocks(self):
        calls = []
        def request(method, endpoint, **kwargs):
            calls.append((method, endpoint, kwargs))
            if method == "GET":
                return {"data": {"block": {"block_id": "doc", "block_type": 1, "children": ["top-a", "top-b"]}}}
            return {"data": {}}
        with patch.object(publisher, "api_request", side_effect=request):
            publisher.replace_document_blocks("token", "doc", [{"block_type": 2, "text": {"elements": []}}])
        deletion = next(kwargs for method, _, kwargs in calls if method == "DELETE")
        self.assertEqual(deletion["body"], {"start_index": 0, "end_index": 2})
        self.assertEqual(deletion["attempts"], 1)

    def test_ambiguous_append_retries_complete_replacement_not_blind_append(self):
        state, calls = {"children": ["old"], "appends": 0}, []
        def request(method, endpoint, **kwargs):
            calls.append((method, kwargs))
            if method == "GET":
                return {"data": {"block": {"block_id": "doc", "block_type": 1, "children": list(state["children"])}}}
            if method == "DELETE":
                state["children"] = []
            if method == "POST":
                state["children"].append("new")
                state["appends"] += 1
                if state["appends"] == 1:
                    raise RuntimeError("response lost after mutation")
            return {"data": {}}
        with patch.object(publisher, "api_request", side_effect=request), patch.object(publisher.time, "sleep"):
            publisher.replace_document_blocks("token", "doc", [{"block_type": 2}])
        self.assertEqual(state["children"], ["new"])
        self.assertEqual([method for method, _ in calls], ["GET", "DELETE", "POST", "GET", "DELETE", "POST"])
        self.assertTrue(all(kwargs.get("attempts") == 1 for method, kwargs in calls if method == "POST"))

    def test_identity_guard_precedes_destructive_body_updates(self):
        with patch.object(publisher, "api_request", return_value={"data": {"document": {"document_id": "doc", "title": "Unrelated document"}}}) as request:
            with self.assertRaisesRegex(RuntimeError, "identity_mismatch"):
                publisher.replace_document_blocks("token", "doc", [], expected_title="Weekly report")
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.args[0], "GET")

    def test_existing_index_entry_is_found_through_pagination_and_updated(self):
        responses = [{"data": {"items": [], "has_more": True, "page_token": "next"}},
                     {"data": {"items": [{"block_id": "index-row", "bullet": {"elements": [{"text_run": {"content": "2026-W35 · Weekly · Old content"}}]}}], "has_more": False}}, {"data": {}}]
        with patch.object(publisher, "api_request", side_effect=responses) as request:
            block_id = publisher.upsert_index("token", "index", "2026-W35", "Weekly", "https://example.feishu.cn/docx/doc", "Updated findings")
        self.assertEqual(block_id, "index-row")
        self.assertEqual([call.args[0] for call in request.call_args_list], ["GET", "GET", "PATCH"])
        self.assertIn("page_token=next", request.call_args_list[1].args[1])
        elements = request.call_args.kwargs["body"]["update_text_elements"]["elements"]
        self.assertEqual("".join(row["text_run"]["content"] for row in elements), "2026-W35 · Weekly · Updated findings")

    def test_uncertain_missing_index_entry_does_not_create_a_second_copy(self):
        with patch.object(publisher, "api_request", return_value={"data": {"items": [], "has_more": False}}) as request:
            with self.assertRaisesRegex(RuntimeError, "uncertain"):
                publisher.upsert_index("token", "index", "2026-W35", "Weekly", "https://example.feishu.cn/docx/doc", "Summary", allow_create=False)
        self.assertEqual(request.call_count, 1)

    def test_document_url_comes_from_official_metadata_not_hardcoded_tenant(self):
        with patch.object(publisher, "api_request", return_value={"data": {"metas": [{"doc_token": "doc", "url": "https://actual-tenant.feishu.cn/docx/doc"}]}}) as request:
            self.assertEqual(publisher.document_url("token", "doc"), "https://actual-tenant.feishu.cn/docx/doc")
        self.assertTrue(request.call_args.kwargs["body"]["with_url"])

    def test_failed_url_lookup_preserves_created_id_for_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "docs/pulse/weekly/2026-w35.md"
            page.parent.mkdir(parents=True)
            page.write_text("# Week\n## 本周判断\n- Finding\n")
            deliveries = root / "deliveries.json"
            env = {key: "fixture" for key in ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_FOLDER_TOKEN", "FEISHU_INDEX_DOC_TOKEN"]}
            with patch.object(publisher, "ROOT", root), patch.object(publisher, "RADAR", root / "missing.json"), patch.object(publisher, "DELIVERIES", deliveries), patch.dict(os.environ, env), patch.object(sys, "argv", ["publish", "--week", "2026-W35"]), patch.object(publisher, "tenant_token", return_value="fixture"), patch.object(publisher, "create_document", return_value=("doc", None)) as create, patch.object(publisher, "document_url", side_effect=[RuntimeError("metadata unavailable"), "https://tenant.feishu.cn/docx/doc"]), patch.object(publisher, "replace_document_blocks"), patch.object(publisher, "upsert_index", return_value="row"), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    publisher.main()
                self.assertEqual(json.loads(deliveries.read_text())["deliveries"][0]["document_id"], "doc")
                publisher.main()
                self.assertEqual(create.call_count, 1)
                self.assertEqual(json.loads(deliveries.read_text())["deliveries"][0]["status"], "published")


if __name__ == "__main__":
    unittest.main()
