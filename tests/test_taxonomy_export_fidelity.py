"""Execute only the real exporter classification block, never a full build."""
import ast
import copy
import json
import sqlite3
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/build_v3_catalog.py"
TREE = ast.parse(SOURCE.read_text())
EXPORT = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == "export_catalog")


def canonical(row):
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def run_export_block(payload):
    assignment = next(node for node in EXPORT.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "taxonomy_assignments" for target in node.targets))
    normalizer = next(node for node in EXPORT.body if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "work"
                      and isinstance(node.body[0], ast.Assign) and any(isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) and target.slice.value == "manifestation_ids" for target in node.body[0].targets))
    environment = {"payload": payload, "works": copy.deepcopy(payload.get("works", [])), "VERSION": "not-authority-export-version"}
    exec(compile(ast.Module(body=[assignment, normalizer], type_ignores=[]), str(SOURCE), "exec"), environment)
    return environment["taxonomy_assignments"]


def fixture():
    row = {"work_id": "arxiv:2407.03245", "axis": "capabilities", "code": "bimanual_manipulation", "confidence": "accepted", "classifier_version": "3.0", "is_primary": False}
    return {"taxonomy-assignments": [row, copy.deepcopy(row), {"work_id": row["work_id"], "axis": "direction", "code": "D4", "confidence": "reviewed", "classifier_version": "review-2025", "is_primary": True}],
            "works": [{"work_id": row["work_id"], "directions": ["D1"], "primary_direction": "D1", "questions": ["Q9"],
                       "facets": {"capabilities": ["different_capability"]}, "classification_state": "low_confidence_review",
                       "relevance": {"classifier_version": "newer-work-version"}, "manifestation_ids": ["b", "a", "b"], "source_record_ids": ["s", "s"]}]}


class TaxonomyExportFidelityTests(unittest.TestCase):
    def test_authority_values_and_duplicates_survive_conflicting_current_work_labels(self):
        payload = fixture()
        original = copy.deepcopy(payload)
        exported = run_export_block(payload)
        self.assertEqual(exported, payload["taxonomy-assignments"])
        self.assertEqual(Counter(map(canonical, exported)), Counter(map(canonical, original["taxonomy-assignments"])))
        self.assertEqual(payload, original)
        self.assertEqual(exported[0]["confidence"], "accepted")
        self.assertEqual(exported[0]["classifier_version"], "3.0")
        self.assertNotIn("D1", {row["code"] for row in exported})

    def test_actual_sql_insert_preserves_each_field_and_multiset_not_just_count(self):
        payload = fixture()
        exported = run_export_block(payload)
        # SQL publication is now inside a transactional packaging context.
        # Exercise the actual nested INSERT, preserving the full multiset check.
        statements = [node for node in ast.walk(EXPORT) if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                         and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "executemany"
                         and node.value.args and isinstance(node.value.args[0], ast.Constant)
                         and str(node.value.args[0].value).startswith("INSERT INTO taxonomy_assignments")]
        self.assertEqual(len(statements), 1)
        statement = statements[0]
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE taxonomy_assignments(work_id TEXT, axis TEXT, code TEXT, is_primary INTEGER, confidence TEXT, classifier_version TEXT)")
        exec(compile(ast.Module(body=[statement], type_ignores=[]), str(SOURCE), "exec"), {"connection": connection, "taxonomy_assignments": exported})
        restored = [{**dict(row), "is_primary": bool(row["is_primary"])} for row in connection.execute("SELECT * FROM taxonomy_assignments")]
        connection.close()
        self.assertEqual(Counter(map(canonical, restored)), Counter(map(canonical, payload["taxonomy-assignments"])))
        self.assertEqual(Counter(map(canonical, restored))[canonical(payload["taxonomy-assignments"][0])], 2)

    def test_missing_or_empty_authority_never_generates_from_work_fields(self):
        payload = fixture()
        payload["taxonomy-assignments"] = []
        self.assertEqual(run_export_block(payload), [])
        payload.pop("taxonomy-assignments")
        self.assertEqual(run_export_block(payload), [])

    def test_optional_fields_are_not_filled_with_exporter_defaults(self):
        payload = fixture()
        payload["taxonomy-assignments"] = [{"work_id": "work:x", "axis": "direction", "code": "D1", "is_primary": True}]
        self.assertEqual(run_export_block(payload), payload["taxonomy-assignments"])
        self.assertNotIn("classifier_version", run_export_block(payload)[0])
        self.assertNotIn("confidence", run_export_block(payload)[0])

    def test_additional_authority_fields_are_not_dropped_in_export_selection(self):
        payload = fixture()
        payload["taxonomy-assignments"][0].update(review_id="review:fixture", review_status="pending", source_record_ids=["source:fixture"])
        self.assertEqual(run_export_block(payload), payload["taxonomy-assignments"])
        # Current SQL DDL still has six columns. This test deliberately does
        # not claim that future extra fields are already mirrored in SQLite.

    def test_no_other_export_loop_can_append_or_reassign_taxonomy_records(self):
        assignments = [node for node in ast.walk(EXPORT) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "taxonomy_assignments" for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        writes = [node for node in ast.walk(EXPORT) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and isinstance(node.func.value, ast.Name) and node.func.value.id == "taxonomy_assignments"
                  and node.func.attr in {"append", "extend", "insert", "clear", "pop", "remove", "sort"}]
        self.assertEqual(writes, [])


if __name__ == "__main__":
    unittest.main()
