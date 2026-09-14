"""Original-reading context cannot silently change counts or erase old prose."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import generate_v3_editorial as editor
from test_v3_editorial import evidence_fixture, version_fixture, valid_editorial, response


def annotation():
    return {"reading_id": "reading:fixture", "work_id": "work:first", "version": "v1",
            "reading_source_url": "https://arxiv.org/html/2608.00404v1", "annotation_digest": "a" * 64,
            "findings": [{"statement": "Training uses a privileged teacher; deployment does not."}],
            "limitations": [{"statement": "Unseen-task generalization is not established."}]}


class ReadingIntegrationTests(unittest.TestCase):
    def enriched(self):
        snapshot, catalog = version_fixture()
        original = copy.deepcopy(catalog)
        base = editor.build_evidence_packet(snapshot, catalog)
        received = []
        def select(work, index, cutoff):
            received.append((copy.deepcopy(work), cutoff))
            return [annotation()] if work["work_id"] == "work:first" else []
        with patch("editorial_readings.annotations_for_work", side_effect=select):
            enriched = editor.build_evidence_packet(snapshot, catalog, reading_index={"work:first": ["audited receipt"]})
        self.assertEqual(catalog, original)
        work = next(work for work, _ in received if work["work_id"] == "work:first")
        self.assertEqual(work["text_version"], "v1")
        self.assertNotIn("Future experiment", work["abstract"])
        return base, enriched

    def test_attachment_preserves_selection_facts_grades_and_quote_contract(self):
        base, enriched = self.enriched()
        for key in ("facts", "sampling", "coverage", "directions", "questions", "signal_candidate_cards", "required_localization_ids"):
            self.assertEqual(base[key], enriched[key], key)
        self.assertEqual(len(base["evidence_cards"]), len(enriched["evidence_cards"]))
        for old, new in zip(base["evidence_cards"], enriched["evidence_cards"]):
            stripped = {key: value for key, value in new.items() if key != "reading_annotations"}
            self.assertEqual(old, stripped)
        self.assertNotEqual(editor.editorial_input_digest(base), editor.editorial_input_digest(enriched))

    def test_no_eligible_reading_preserves_existing_digest(self):
        snapshot, catalog = version_fixture()
        base = editor.build_evidence_packet(snapshot, catalog)
        with patch("editorial_readings.annotations_for_work", return_value=[]):
            enriched = editor.build_evidence_packet(snapshot, catalog, reading_index={"other": []})
        self.assertEqual(base, enriched)

    def test_reading_ids_are_not_new_works_or_authorized_measurements(self):
        _, packet = self.enriched()
        value = valid_editorial(packet)
        editor.validate_editorial(value, packet)
        value["claims"][0]["supporting_ids"] = ["reading:fixture"]
        with self.assertRaisesRegex(editor.EditorialError, "citation_unknown_or_wrong_month"):
            editor.validate_editorial(value, packet)
        value = valid_editorial(packet)
        value["claims"][0]["summary"] = "原文解读给出的实验成功率为98%。"
        with self.assertRaisesRegex(editor.EditorialError, "unbound_number_in_prose"):
            editor.validate_editorial(value, packet)

    def test_success_archives_original_and_stores_exact_new_packet(self):
        base, enriched = self.enriched()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            def run(packet):
                value = valid_editorial(packet)
                return editor.run_month(packet, packet["month"], output, base_url="http://fixture.invalid",
                                        requester=lambda *_: (value, response(value)), sleeper=lambda _: None)
            self.assertEqual(run(base)["status"], "complete")
            path = output / "monthly" / f"{base['month']}.json"
            old = json.loads(path.read_text())
            self.assertFalse(editor.validated_editorial_overlay(old, enriched)["usable"])
            self.assertEqual(run(enriched)["status"], "complete")
            new = json.loads(path.read_text())
            self.assertEqual(new["available_reading_references"], editor.available_reading_references(enriched))
            self.assertIn("not_independent_validation", new["reading_context_status"])
            self.assertEqual(json.loads((output / new["evidence_packet_ref"]["path"]).read_text()), enriched)
            from editorial_history import load_editorial_history
            history = load_editorial_history(output, base["month"])
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["artifact"], old)
            self.assertEqual(history[0]["reference"]["input_packet_status"], "available")
            self.assertTrue(run(enriched)["cached"])
            self.assertEqual(load_editorial_history(output, base["month"]), history)

    def test_failed_generation_preserves_old_complete_without_fake_archive(self):
        base, enriched = self.enriched()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            old = valid_editorial(base)
            old.update(status="complete", model="gpt-5.6-sol", generated_at="2026-09-01T00:00:00Z",
                       input_digest=editor.editorial_input_digest(base))
            target = output / "monthly" / f"{base['month']}.json"
            editor.write_json(target, old)
            before = target.read_bytes()
            result = editor.run_month(enriched, base["month"], output)
            self.assertTrue(result["previous_complete_preserved"])
            self.assertEqual(target.read_bytes(), before)
            self.assertFalse((output / "monthly-history").exists())

    def test_archive_error_does_not_retry_model_or_overwrite_previous(self):
        snapshot, catalog = evidence_fixture()
        packet = editor.build_evidence_packet(snapshot, catalog)
        value = valid_editorial(packet)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            target = output / "monthly" / f"{packet['month']}.json"
            old = {**value, "status": "complete", "input_digest": "b" * 64}
            editor.write_json(target, old)
            before = target.read_bytes()
            with patch("editorial_history.persist_evidence_packet", side_effect=ValueError("fixed_error")):
                with patch.object(editor, "_request_with_repair", return_value=(value, response(value))) as requester:
                    with self.assertRaisesRegex(RuntimeError, "editorial_history_persistence_failed"):
                        editor.run_month(packet, packet["month"], output, base_url="http://fixture.invalid")
                    self.assertEqual(requester.call_count, 1)
            self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
