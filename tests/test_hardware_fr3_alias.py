"""Manufacturer-documented model alias; never a broad Franka-brand merge."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from import_hardware_source_reviews import resolve_device


class FrankaAliasTests(unittest.TestCase):
    def setUp(self):
        self.device = {"hardware_id": "hardware:franka-research-3", "name": "Franka Research 3",
                       "vendor": "Franka", "category": "robot_arm", "identity_level": "model_specified", "aliases": []}
        self.review = {"work_id": "arxiv:fixture", "source_url": "https://example.test/paper"}
        self.assertion = {key: self.device[key] for key in ("name", "vendor", "category", "identity_level")}

    def test_fr3_reuses_research_3_and_leaves_reported_name_unchanged(self):
        value = {**self.assertion, "name": "Franka FR3"}
        before = copy.deepcopy(value)
        proposed = []
        self.assertEqual(resolve_device(value, self.review, {self.device["hardware_id"]: self.device}, {}, proposed), self.device["hardware_id"])
        self.assertEqual(proposed, [])
        self.assertEqual(value, before)

    def test_panda_duo_and_unqualified_brand_are_not_aliases(self):
        for name in ("Franka Panda", "Franka FR3 Duo", "Franka robot arm"):
            proposed = []
            value = {**self.assertion, "name": name}
            self.assertNotEqual(resolve_device(value, self.review, {self.device["hardware_id"]: self.device}, {}, proposed), self.device["hardware_id"])

    def test_preexisting_duplicate_alias_is_rejected_instead_of_selected_arbitrarily(self):
        duplicate = {**self.device, "hardware_id": "hardware:franka-fr3", "name": "Franka FR3"}
        with self.assertRaisesRegex(ValueError, "ambiguous_or_conflicting_named_device"):
            resolve_device({**self.assertion, "name": "Franka FR3"}, self.review,
                           {self.device["hardware_id"]: self.device, duplicate["hardware_id"]: duplicate}, {}, [])


if __name__ == "__main__":
    unittest.main()
