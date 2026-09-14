"""Packet schema tests are entirely local; no model/network calls."""
import copy
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from editorial_response_schema import packet_response_schema, schema_budget
from test_v3_editorial import evidence_fixture, valid_editorial, editor


class PacketResponseSchemaTests(unittest.TestCase):
    def setUp(self):
        snapshot, catalog = evidence_fixture()
        self.packet = editor.build_evidence_packet(snapshot, catalog)
        self.base = copy.deepcopy(editor.OUTPUT_SCHEMA)
        self.value = valid_editorial(self.packet)

    def compile(self, packet=None, base=None):
        return packet_response_schema(base or self.base, packet or self.packet, editor.MISSING_VERSION_SUMMARY)

    def assert_invalid(self, value, packet=None, schema=None):
        self.assertFalse(Draft202012Validator(schema or self.compile(packet)).is_valid(value))

    def test_normal_fixture_valid_and_inputs_unchanged(self):
        before, before_packet = copy.deepcopy(self.base), copy.deepcopy(self.packet)
        schema = self.compile()
        self.assertTrue(Draft202012Validator(schema).is_valid(self.value))
        editor.validate_editorial(self.value, self.packet)
        self.assertEqual(self.base, before)
        self.assertEqual(self.packet, before_packet)
        self.assertEqual(schema, self.compile())

    def test_unavailable_or_wrong_month_id_cannot_enter_ordinary_research_sections(self):
        for unavailable in [True, False]:
            packet = copy.deepcopy(self.packet)
            card = copy.deepcopy(packet["evidence_cards"][0])
            card.update(evidence_id="work:later", work_id="work:later")
            if unavailable:
                card["experimental_text_available"] = False
            else:
                card["evidence_month"] = "2026-09"
            packet["evidence_cards"].append(card)
            schema = self.compile(packet)
            for section in ["claims", "counterevidence", "watchlist"]:
                value = copy.deepcopy(self.value)
                value[section] = [{**copy.deepcopy(value["claims"][0]), "supporting_ids": ["work:later"]}]
                self.assert_invalid(value, schema=schema)
                value[section][0].update(supporting_ids=["work:first"], counterevidence_ids=["work:later"])
                self.assert_invalid(value, schema=schema)

    def test_facet_branches_reject_wrong_or_unknown_citations(self):
        for section in ["direction_summaries", "question_summaries"]:
            value = copy.deepcopy(self.value)
            value[section][0]["supporting_ids"] = ["work:second"]
            self.assert_invalid(value)
            value[section][0].update(supporting_ids=["work:first"], counterevidence_ids=["missing"])
            self.assert_invalid(value)

    def test_available_facet_excludes_missing_text_even_when_one_valid_id_present(self):
        packet = copy.deepcopy(self.packet)
        missing = copy.deepcopy(packet["evidence_cards"][0])
        missing.update(evidence_id="work:missing", work_id="work:missing", experimental_text_available=False)
        packet["evidence_cards"].append(missing)
        value = copy.deepcopy(self.value)
        value["direction_summaries"][0]["supporting_ids"].append("work:missing")
        self.assert_invalid(value, packet)

    def test_no_text_facet_requires_exact_placeholder_and_empty_numbers_counterevidence(self):
        packet = copy.deepcopy(self.packet)
        for card in packet["evidence_cards"]:
            if "D1" in card["directions"]:
                card["experimental_text_available"] = False
        packet["required_localization_ids"] = []
        value = copy.deepcopy(self.value)
        value["claims"] = []
        value["localizations"] = []
        for section in ["direction_summaries", "question_summaries"]:
            value[section][0]["summary"] = editor.MISSING_VERSION_SUMMARY
        schema = self.compile(packet)
        self.assertTrue(Draft202012Validator(schema).is_valid(value))
        editor.validate_editorial(value, packet)
        changed = copy.deepcopy(value)
        changed["direction_summaries"][0]["summary"] = "论文没有进行任何实验。"
        self.assert_invalid(changed, schema=schema)
        changed = copy.deepcopy(value)
        changed["direction_summaries"][0]["counterevidence_ids"] = ["work:first"]
        self.assert_invalid(changed, schema=schema)
        changed = copy.deepcopy(value)
        changed["direction_summaries"][0]["numeric_claims"] = [{"metric": "coverage.included_works", "value": 2, "unit": "count", "evidence_ids": ["work:first"]}]
        self.assert_invalid(changed, schema=schema)

    def test_organization_metadata_event_has_separate_safe_citation_set(self):
        packet = copy.deepcopy(self.packet)
        event = next(card for card in packet["evidence_cards"] if card["kind"] == "event")
        event["experimental_text_available"] = False
        value = copy.deepcopy(self.value)
        value["organization_changes"] = [{**copy.deepcopy(value["claims"][0]), "supporting_ids": ["event:accept"]}]
        schema = self.compile(packet)
        self.assertTrue(Draft202012Validator(schema).is_valid(value))
        editor.validate_editorial(value, packet)
        value["organization_changes"][0]["supporting_ids"] = ["work:first"]
        self.assert_invalid(value, schema=schema)
        event["organization_id"] = None
        schema = self.compile(packet)
        self.assertEqual(schema["properties"]["organization_changes"]["maxItems"], 0)

    def test_localization_uses_only_required_work_and_its_own_source_enum(self):
        schema = self.compile()
        for wid, source in [("work:second", "source:second"), ("work:first", "source:second"), ("work:first", "missing-source")]:
            value = copy.deepcopy(self.value)
            value["localizations"][0].update(work_id=wid, source_ids=[source])
            self.assert_invalid(value, schema=schema)
        packet = copy.deepcopy(self.packet)
        next(card for card in packet["evidence_cards"] if card["evidence_id"] == "work:first")["experimental_text_available"] = False
        with self.assertRaisesRegex(ValueError, "required_localization_has_no_eligible_source"):
            self.compile(packet)

    def test_month_and_limitations_are_closed_to_packet_values(self):
        value = copy.deepcopy(self.value)
        value["month"] = "2026-09"
        self.assert_invalid(value)
        value = copy.deepcopy(self.value)
        value["limitations"].append("所有论文均没有同行评审。")
        self.assert_invalid(value)

    def test_no_eligible_ids_empty_sections_without_fake_enum_values(self):
        packet = {**self.packet, "evidence_cards": [], "required_direction_codes": [], "required_question_codes": [],
                  "required_localization_ids": [], "known_limitations": []}
        schema = self.compile(packet)
        for section in ["claims", "counterevidence", "watchlist", "organization_changes", "direction_summaries", "question_summaries", "localizations", "limitations"]:
            self.assertEqual(schema["properties"][section]["maxItems"], 0)
        def walk(node):
            if isinstance(node, dict):
                if "enum" in node:
                    self.assertTrue(node["enum"])
                for child in node.values():
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)
        walk(schema)
        value = {"month": packet["month"], **{key: [] for key in self.value if key != "month"}}
        self.assertTrue(Draft202012Validator(schema).is_valid(value))

    def test_base_constraints_are_retained_not_overwritten_by_broader_enums(self):
        base = copy.deepcopy(self.base)
        base["$defs"]["claim"]["properties"]["title"]["minLength"] = 40
        base["$defs"]["support"]["items"]["pattern"] = "^work:first$"
        # Some required Q1 rows would become unsatisfiable under this altered
        # base, so use only Q0/D1 and the one allowed source work.
        packet = copy.deepcopy(self.packet)
        packet.update(required_direction_codes=["D1"], required_question_codes=["Q0"], required_localization_ids=[])
        packet["evidence_cards"] = [card for card in packet["evidence_cards"] if card["evidence_id"] == "work:first"]
        schema = self.compile(packet, base)
        value = valid_editorial(packet)
        self.assert_invalid(value, schema=schema)
        value["claims"][0]["title"] = "一" * 40
        self.assertTrue(Draft202012Validator(schema).is_valid(value))
        self.assertTrue(Draft202012Validator(base).is_valid(value))
        value["claims"] *= 9
        self.assert_invalid(value, schema=schema)

    def test_objects_remain_closed_all_fields_required_and_no_unsupported_composition(self):
        schema = self.compile()
        self.assertEqual(schema["type"], "object")
        self.assertNotIn("anyOf", schema)
        def walk(node):
            if isinstance(node, dict):
                self.assertFalse(set(node) & {"allOf", "if", "then", "else", "not"})
                if node.get("type") == "object":
                    self.assertFalse(node["additionalProperties"])
                    self.assertEqual(set(node["required"]), set(node["properties"]))
                for child in node.values():
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)
        walk(schema)

    def test_shared_enum_references_limit_duplicate_storage(self):
        schema = self.compile()
        ordinary = schema["properties"]["claims"]["items"]
        self.assertEqual(ordinary, schema["properties"]["counterevidence"]["items"])
        self.assertEqual(ordinary, schema["properties"]["watchlist"]["items"])
        definition = schema["$defs"][ordinary["$ref"].split("/")[-1]]
        self.assertEqual(definition["properties"]["supporting_ids"]["items"], definition["properties"]["counterevidence_ids"]["items"])
        self.assertLess(schema_budget(schema)["enum_values"], 1000)
        self.assertLessEqual(schema_budget(schema)["max_container_nesting"], 10)

    def test_required_facets_and_localizations_cannot_be_omitted_by_shortening_arrays(self):
        schema = self.compile()
        for section, key in [("direction_summaries", "required_direction_codes"), ("question_summaries", "required_question_codes"),
                             ("localizations", "required_localization_ids")]:
            self.assertEqual(schema["properties"][section]["minItems"], len(self.packet[key]))
            self.assertEqual(schema["properties"][section]["maxItems"], len(self.packet[key]))
            value = copy.deepcopy(self.value)
            value[section].pop()
            self.assert_invalid(value, schema=schema)

    def test_enum_budget_failure_is_explicit_not_fallback_to_unrestricted_strings(self):
        packet = {**self.packet, "required_direction_codes": [], "required_question_codes": [], "required_localization_ids": []}
        original = packet["evidence_cards"][0]
        packet["evidence_cards"] = [{**original, "evidence_id": f"work:{index}", "work_id": f"work:{index}"} for index in range(1001)]
        with self.assertRaisesRegex(ValueError, "schema_budget_exceeded"):
            self.compile(packet)


if __name__ == "__main__":
    unittest.main()
