import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog_store import encode, fingerprint
from equipment_radar import TABLES
from import_hardware_source_reviews import audit_addenda_lineage, import_source_reviews, source_key
from test_equipment_radar import OBSERVED, fixture, make_work


class SourceReviewImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cache = self.root / "cache"
        self.cache.mkdir()
        self.directory = self.root / "equipment"
        self.directory.mkdir()
        self.observations = self.cache / "observations.jsonl"
        self.public = self.root / "public" / "section-reviews.jsonl"
        self.payload, self.existing, _ = fixture()
        for table in TABLES:
            (self.directory / (table + ".jsonl")).write_text("".join(encode(r) + "\n" for r in self.existing[table]))
        self.raw = {"schema_version": "1", "reviews": [self.review(2)]}

    def tearDown(self):
        self.temporary.cleanup()

    def review(self, number, *, name="Unitree G1", level="model_specified", role="real_robot", category="robot_platform", vendor="Unitree"):
        work = make_work(number)
        self.payload["works"].append(work)
        url = "https://arxiv.org/html/" + work["work_id"][6:] + "v1"
        raw = ("<html>Source for " + work["work_id"] + "</html>").encode()
        blocks = [{"section_id": "S4", "section_title": "Experiments", "text": "SECRET PAPER TEXT SHOULD NEVER BE PUBLIC"},
                  {"section_id": "A1", "section_title": "Appendix", "text": "Experimental implementation details"}]
        body = "\n\n".join(b["text"] for b in blocks).encode()
        raw_path, blocks_path = self.cache / f"{number}.html", self.cache / f"{number}.json"
        raw_path.write_bytes(raw)
        blocks_path.write_text(encode(blocks))
        observation = {"work_id": work["work_id"], "source_url": url, "version": "v1",
                       "observed_at": OBSERVED, "status": "full_text_available", "observation_id": f"source:{number}",
                       "raw_sha256": hashlib.sha256(raw).hexdigest(), "text_sha256": hashlib.sha256(body).hexdigest(),
                       "cache_ref": str(raw_path), "blocks_ref": str(blocks_path),
                       "identity_proofs": [{"kind": "original_abs_link", "arxiv_id": work["work_id"][6:], "version": "v1"}]}
        with self.observations.open("a") as out:
            out.write(encode(observation) + "\n")
        return {"work_id": work["work_id"], "source_url": url, "source_version": "v1",
                "raw_sha256": observation["raw_sha256"], "text_sha256": observation["text_sha256"],
                "observed_at": OBSERVED, "reviewed_at": "2026-09-14T02:00:00Z",
                "review_scope": "hardware_use_assertions_only", "images_inspected": False,
                "supplementary_materials_inspected": False, "reviewed_sections": ["S4", "A1"],
                "decision": "verified_use", "devices": [{"name": name, "vendor": vendor, "category": category,
                "identity_level": level, "role": role, "setting": "real", "usage_scope": "study",
                "configuration": "The paper does not specify an edition", "validation_context": "Real experiment",
                "statement_zh": "所审实验段落明确报告使用该设备。", "source_locator": "S4; A1"}]}

    def run_import(self, *, apply=False):
        return import_source_reviews(self.raw, self.payload, self.directory, self.observations, self.public, apply=apply)

    def start_addendum(self, *, negative_parent=False):
        original = copy.deepcopy(self.raw['reviews'][0])
        if negative_parent:
            self.raw['reviews'][0].update(decision='no_explicit_named_usage_in_reviewed_sections', devices=[], reviewed_sections=['S4'])
        self.run_import(apply=True)
        parent = json.loads(self.public.read_text())
        addon = original
        addon.update(extends_review_id=parent['review_id'], reviewed_at='2026-09-14T03:00:00Z', reviewed_sections=['A1'])
        addon['devices'][0].update(source_locator='A1', usage_scope='study' if negative_parent else 'calibration',
                                   configuration='Newly reviewed calibration configuration')
        self.raw = {'schema_version': '1', 'reviews': [addon]}
        return parent

    def test_dry_run_is_read_only_and_reuses_existing_exact_model(self):
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        result = self.run_import()
        self.assertFalse(result["applied"])
        self.assertEqual(result["added"]["devices"], 0)
        self.assertEqual(result["added"]["usage-evidence"], 1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.directory.iterdir()})
        self.assertFalse(self.public.exists())

    def test_general_experiment_compute_does_not_invent_training_or_inference(self):
        self.raw['reviews'] = [self.review(3, name='Intel Xeon Gold 6348', vendor='Intel',
                                          category='compute_platform', role='experiment_compute')]
        self.run_import(apply=True)
        uses = [json.loads(line) for line in (self.directory / 'usage-evidence.jsonl').read_text().splitlines()]
        added = [row for row in uses if row['work_id'] == self.raw['reviews'][0]['work_id']]
        self.assertEqual([row['role'] for row in added], ['experiment_compute'])

    def test_general_experiment_compute_rejects_non_compute_device(self):
        self.raw['reviews'][0]['devices'][0]['role'] = 'experiment_compute'
        with self.assertRaisesRegex(ValueError, 'compute_role_category_mismatch'):
            self.run_import()

    def test_import_is_idempotent_and_loco_files_are_byte_preserved(self):
        before = {name: (self.directory / (name + ".jsonl")).read_bytes() for name in ("loco-reviews", "loco-observations")}
        raw_before = copy.deepcopy(self.raw)
        first = self.run_import(apply=True)
        paths = [*self.directory.glob("*.jsonl"), self.public]
        bytes_before = {p: p.read_bytes() for p in paths}
        second = self.run_import(apply=True)
        self.assertEqual(first["counts"], second["counts"])
        self.assertEqual(set(second["added"].values()), {0})
        self.assertEqual(bytes_before, {p: p.read_bytes() for p in paths})
        self.assertEqual(self.raw, raw_before)
        for name, content in before.items():
            self.assertEqual(content, (self.directory / (name + ".jsonl")).read_bytes())

    def test_public_rows_state_AI_sections_only_and_never_include_body_or_paths(self):
        self.run_import(apply=True)
        public = json.loads(self.public.read_text())
        self.assertEqual(public["reviewer_kind"], "AI")
        self.assertEqual(public["review_scope"], "sections_only")
        self.assertFalse(public["images_inspected"])
        self.assertFalse(public["full_text_reviewed"])
        self.assertFalse(public["whole_paper_hardware_absence_conclusion"])
        combined = self.public.read_text() + (self.directory / "usage-evidence.jsonl").read_text()
        self.assertNotIn("SECRET PAPER TEXT", combined)
        self.assertNotIn(str(self.cache), combined)
        self.assertEqual(set(public["section_text_sha256"]), {"S4", "A1"})

    def test_negative_section_decision_never_adds_hardware_absence_or_usage(self):
        row = self.raw["reviews"][0]
        row.update(decision="no_explicit_named_usage_in_reviewed_sections", devices=[])
        result = self.run_import(apply=True)
        self.assertEqual(result["added"]["usage-evidence"], 0)
        public = json.loads(self.public.read_text())
        self.assertEqual(public["usage_ids"], [])
        self.assertFalse(public["whole_paper_hardware_absence_conclusion"])

    def test_historical_observation_valid_even_when_latest_version_changed(self):
        latest = json.loads(self.observations.read_text().splitlines()[0])
        latest.update(version="v2", source_url=latest["source_url"][:-2] + "v2", text_sha256="0" * 64,
                      status="unavailable", observation_id="source:newest", blocks_ref=None)
        with self.observations.open("a") as out:
            out.write(encode(latest) + "\n")
        self.assertEqual(self.run_import()["imported_assertion_count"], 1)

    def test_new_exact_models_share_same_category_name_identity(self):
        self.raw["reviews"] = [self.review(3, name="New Robot"), self.review(4, name="New Robot")]
        result = self.run_import(apply=True)
        self.assertEqual(result["added"]["devices"], 1)
        usages = [json.loads(line) for line in (self.directory / "usage-evidence.jsonl").read_text().splitlines()]
        self.assertEqual(len({r["hardware_id"] for r in usages if r["work_id"] in {"arxiv:2608.00003", "arxiv:2608.00004"}}), 1)

    def test_family_and_unspecified_never_auto_merge_across_works(self):
        for level in ("family_only", "unspecified"):
            with self.subTest(level=level):
                self.raw["reviews"] = [self.review(10 if level == "family_only" else 12, name="Robot family", level=level),
                                       self.review(11 if level == "family_only" else 13, name="Robot family", level=level)]
                self.assertEqual(self.run_import()["added"]["devices"], 2)

    def test_explicit_4090_alias_does_not_merge_4090D_or_composite_workstation(self):
        composite = {"hardware_id": "hardware:rtx-4090-core-i9-14900k-desktop-workstation",
                     "slug": "rtx-4090-core-i9-14900k-desktop-workstation",
                     "name": "RTX 4090 / Core i9-14900K desktop workstation", "vendor": "NVIDIA",
                     "category": "compute_platform", "identity_level": "model_specified",
                     "aliases": [], "official_url": "https://arxiv.org/abs/2608.00001"}
        with (self.directory / "devices.jsonl").open("a") as out:
            out.write(encode(composite) + "\n")
        self.raw["reviews"] = [self.review(3, name="NVIDIA GeForce RTX 4090", vendor="NVIDIA", category="compute_platform", role="inference_compute"),
                               self.review(4, name="NVIDIA RTX 4090", vendor="NVIDIA", category="compute_platform", role="training_compute"),
                               self.review(5, name="NVIDIA RTX 4090D", vendor="NVIDIA", category="compute_platform", role="training_compute")]
        result = self.run_import(apply=True)
        self.assertEqual(result["added"]["devices"], 2)
        rows = [json.loads(line) for line in (self.directory / "usage-evidence.jsonl").read_text().splitlines()]
        by_work = {r["work_id"]: r for r in rows}
        self.assertEqual(by_work["arxiv:2608.00003"]["hardware_id"], by_work["arxiv:2608.00004"]["hardware_id"])
        self.assertNotEqual(by_work["arxiv:2608.00004"]["hardware_id"], by_work["arxiv:2608.00005"]["hardware_id"])
        self.assertEqual(by_work["arxiv:2608.00003"]["reported_device_name"], "NVIDIA GeForce RTX 4090")
        self.assertEqual(self.run_import()["added"]["devices"], 0)

    def test_explicit_id_requires_matching_name_category_vendor_granularity(self):
        original = copy.deepcopy(self.raw)
        for field, value in (("name", "Other robot"), ("category", "robot_arm"), ("vendor", "Other maker"), ("identity_level", "family_only")):
            self.raw = copy.deepcopy(original)
            self.raw["reviews"][0]["devices"][0].update(hardware_id="hardware:unitree-g1", **{field: value})
            with self.assertRaisesRegex(ValueError, "explicit_hardware_id_identity_mismatch"):
                self.run_import()

    def test_explicit_family_id_cannot_be_shared_with_other_work(self):
        device = copy.deepcopy(self.existing["devices"][0])
        device.update(identity_level="family_only", identity_context_work_id="arxiv:2608.00001")
        (self.directory / "devices.jsonl").write_text(encode(device) + "\n")
        self.raw["reviews"][0]["devices"][0].update(hardware_id=device["hardware_id"], identity_level="family_only")
        with self.assertRaisesRegex(ValueError, "uncertain_hardware_identity_cross_work"):
            self.run_import()

    def test_exact_name_vendor_conflicts_and_ambiguous_existing_ids_fail(self):
        self.raw["reviews"][0]["devices"][0]["vendor"] = "Different manufacturer"
        with self.assertRaisesRegex(ValueError, "conflicting_named_device"):
            self.run_import()
        self.raw["reviews"][0]["devices"][0]["vendor"] = "Unitree"
        duplicate = {**self.existing["devices"][0], "hardware_id": "hardware:g1-other", "slug": "g1-other"}
        with (self.directory / "devices.jsonl").open("a") as out:
            out.write(encode(duplicate) + "\n")
        with self.assertRaisesRegex(ValueError, "ambiguous_or_conflicting_named_device"):
            self.run_import()

    def test_unknown_role_missing_evidence_and_mention_fail_before_writes(self):
        original = copy.deepcopy(self.raw)
        for field, value in (("role", "magic"), ("role", "mentioned"), ("role", "dataset_source"),
                             ("statement_zh", ""), ("validation_context", ""), ("source_locator", "")):
            self.raw = copy.deepcopy(original)
            self.raw["reviews"][0]["devices"][0][field] = value
            with patch("import_hardware_source_reviews.write_if_changed") as writer:
                with self.assertRaises(ValueError):
                    self.run_import(apply=True)
                writer.assert_not_called()

    def test_new_control_and_model_fitting_roles_keep_their_meaning(self):
        self.raw["reviews"] = [self.review(3, name="Raspberry Pi", category="compute_platform", vendor="Raspberry Pi", level="family_only", role="control_compute"),
                               self.review(4, name="Intel Core i7-13700H", category="compute_platform", vendor="Intel", role="model_fitting_compute")]
        self.run_import(apply=True)
        rows = [json.loads(line) for line in (self.directory / "usage-evidence.jsonl").read_text().splitlines()]
        self.assertEqual({r["role"] for r in rows if r.get("reviewer_kind") == "AI"}, {"control_compute", "model_fitting_compute"})

    def test_study_baseline_calibration_are_distinct_and_simulation_stays_simulation(self):
        base = self.raw["reviews"][0]["devices"][0]
        base.update(role="simulated_robot", setting="simulation")
        self.raw["reviews"][0]["devices"] = [{**base, "usage_scope": scope} for scope in ("study", "baseline", "calibration")]
        self.assertEqual(self.run_import()["imported_assertion_count"], 3)
        self.raw["reviews"][0]["devices"][0]["setting"] = "real"
        with self.assertRaisesRegex(ValueError, "simulation_setting_conflict"):
            self.run_import()

    def test_locators_bind_to_selected_source_sections_and_url(self):
        original = copy.deepcopy(self.raw)
        for locator in ("S9", "https://arxiv.org/html/2608.99999v1#S4", "S4; S4", "Section 4"):
            self.raw = copy.deepcopy(original)
            self.raw["reviews"][0]["devices"][0]["source_locator"] = locator
            with self.assertRaisesRegex(ValueError, "locator"):
                self.run_import()
        self.raw = original
        row = self.raw["reviews"][0]
        row["devices"][0]["source_locator"] = row["source_url"] + "#S4"
        self.assertEqual(self.run_import()["imported_assertion_count"], 1)

    def test_missing_or_conflicting_source_hashes_fail_closed(self):
        original = copy.deepcopy(self.raw)
        for field, value in (("raw_sha256", "0" * 64), ("text_sha256", "1" * 64), ("source_version", "v2")):
            self.raw = copy.deepcopy(original)
            self.raw["reviews"][0][field] = value
            with self.assertRaises(ValueError):
                self.run_import()
        self.raw = original
        (self.cache / "2.html").write_text("corrupted cache")
        with self.assertRaisesRegex(ValueError, "raw_cache_hash_mismatch"):
            self.run_import()

    def test_block_content_and_selected_sections_are_integrity_checked(self):
        original = (self.cache / "2.json").read_text()
        blocks = json.loads(original)
        blocks[0]["text"] += " changed"
        (self.cache / "2.json").write_text(encode(blocks))
        with self.assertRaisesRegex(ValueError, "body_blocks_hash_mismatch"):
            self.run_import()
        (self.cache / "2.json").write_text(original)
        self.raw["reviews"][0]["reviewed_sections"] = ["S99"]
        with self.assertRaisesRegex(ValueError, "reviewed_sections_not_bound"):
            self.run_import()

    def test_unavailable_source_and_uninspected_media_scope_cannot_be_promoted(self):
        row = json.loads(self.observations.read_text())
        row["status"] = "partial_text"
        self.observations.write_text(encode(row) + "\n")
        with self.assertRaisesRegex(ValueError, "no_matching_available_historical_observation"):
            self.run_import()
        row["status"] = "full_text_available"
        row["identity_proofs"] = []
        self.observations.write_text(encode(row) + "\n")
        with self.assertRaisesRegex(ValueError, "identity_proof_missing"):
            self.run_import()
        self.raw["reviews"][0]["images_inspected"] = True
        with self.assertRaisesRegex(ValueError, "uninspected_media_scope"):
            self.run_import()

    def test_cache_path_cannot_escape_private_root(self):
        outside = self.root / "outside.html"
        outside.write_bytes((self.cache / "2.html").read_bytes())
        row = json.loads(self.observations.read_text())
        row["cache_ref"] = str(outside)
        self.observations.write_text(encode(row) + "\n")
        with self.assertRaisesRegex(ValueError, "outside_root"):
            self.run_import()

    def test_full_four_table_and_public_ledger_preflight_precede_any_write(self):
        late = copy.deepcopy(self.existing["loco-observations"][0])
        late["supporting_ids"] = ["arxiv:unknown"]
        (self.directory / "loco-observations.jsonl").write_text(encode(late) + "\n")
        with patch("import_hardware_source_reviews.write_if_changed") as writer:
            with self.assertRaisesRegex(ValueError, "unreviewed_work"):
                self.run_import(apply=True)
            writer.assert_not_called()
        (self.directory / "loco-observations.jsonl").write_text(encode(self.existing["loco-observations"][0]) + "\n")
        self.run_import(apply=True)
        row = json.loads(self.public.read_text())
        row["decision"] = "ambiguous"
        self.public.write_text(encode(row) + "\n")
        with patch("import_hardware_source_reviews.write_if_changed") as writer:
            with self.assertRaisesRegex(ValueError, "existing_section_review_conflict"):
                self.run_import(apply=True)
            writer.assert_not_called()

    def test_duplicate_assertion_and_wrong_canonical_identity_fail(self):
        self.raw["reviews"][0]["devices"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate_usage_assertion"):
            self.run_import()
        self.raw["reviews"][0]["devices"] = self.raw["reviews"][0]["devices"][:1]
        self.payload["works"][1]["identifiers"]["arxiv"] = "2608.99999"
        with self.assertRaisesRegex(ValueError, "canonical_source_identity_mismatch"):
            self.run_import()

    def test_legacy_review_id_and_fields_are_unchanged_without_extends(self):
        expected = 'hardware-section-review:' + fingerprint(source_key(self.raw['reviews'][0], review=True))[:24]
        self.run_import(apply=True)
        record = json.loads(self.public.read_text())
        self.assertEqual(record['review_id'], expected)
        self.assertNotIn('extends_review_id', record)
        self.assertNotIn('review_kind', record)
        self.assertNotIn('addendum_scope', record)

    def test_addendum_is_new_record_new_usage_only_and_dry_run_is_read_only(self):
        parent = self.start_addendum()
        paths = [*self.directory.glob('*.jsonl'), self.public, *self.cache.glob('*')]
        before = {path: path.read_bytes() for path in paths}
        result = self.run_import()
        self.assertEqual(result['added']['usage-evidence'], 1)
        self.assertEqual(result['public_section_review_count'], 2)
        self.assertFalse(result['applied'])
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.run_import(apply=True)
        records = {row['review_id']: row for row in map(json.loads, self.public.read_text().splitlines())}
        self.assertEqual(records[parent['review_id']], parent)
        addon = next(row for rid, row in records.items() if rid != parent['review_id'])
        self.assertEqual(addon['extends_review_id'], parent['review_id'])
        self.assertEqual(addon['review_kind'], 'addendum')
        self.assertEqual(addon['addendum_scope'], 'new_semantic_usage_assertions_only')
        self.assertEqual(addon['source_observation_id'], parent['source_observation_id'])
        self.assertEqual(source_key(addon, review=True), source_key(parent, review=True))
        self.assertNotEqual(addon['review_id'], parent['review_id'])
        new_uses = [row for row in map(json.loads, (self.directory / 'usage-evidence.jsonl').read_text().splitlines()) if row.get('section_review_id') == addon['review_id']]
        self.assertEqual(len(new_uses), 1)
        self.assertEqual(new_uses[0]['extends_review_id'], parent['review_id'])
        self.assertEqual(new_uses[0]['review_kind'], 'addendum')
        old_uses = {row['usage_id']: row for row in map(json.loads, before[self.directory / 'usage-evidence.jsonl'].decode().splitlines())}
        all_uses = {row['usage_id']: row for row in map(json.loads, (self.directory / 'usage-evidence.jsonl').read_text().splitlines())}
        self.assertTrue(all(all_uses[uid] == row for uid, row in old_uses.items()))

    def test_addendum_apply_replay_is_byte_idempotent(self):
        parent = self.start_addendum()
        addon_input = copy.deepcopy(self.raw)
        self.run_import(apply=True)
        records = [json.loads(line) for line in self.public.read_text().splitlines()]
        addon = next(row for row in records if row['review_id'] != parent['review_id'])
        raw_review = self.raw['reviews'][0]
        expected = 'hardware-section-review:' + fingerprint(['addendum', parent['review_id'], raw_review['reviewed_at'],
                    source_key(raw_review, review=True), parent['source_observation_id']])[:24]
        self.assertEqual(addon['review_id'], expected)
        paths = [*self.directory.glob('*.jsonl'), self.public]
        before = {path: path.read_bytes() for path in paths}
        repeat = self.run_import(apply=True)
        self.assertEqual(set(repeat['added'].values()), {0})
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.assertEqual(self.raw, addon_input)

    def test_addendum_keeps_old_no_explicit_scope_and_decision(self):
        parent = self.start_addendum(negative_parent=True)
        self.run_import(apply=True)
        records = {row['review_id']: row for row in map(json.loads, self.public.read_text().splitlines())}
        self.assertEqual(records[parent['review_id']], parent)
        self.assertEqual(parent['decision'], 'no_explicit_named_usage_in_reviewed_sections')
        self.assertEqual(parent['reviewed_sections'], ['S4'])
        self.assertEqual(parent['usage_ids'], [])
        addon = next(row for row in records.values() if row['review_id'] != parent['review_id'])
        self.assertEqual(addon['reviewed_sections'], ['A1'])
        self.assertEqual(addon['decision'], 'verified_use')
        self.assertFalse(addon['whole_paper_hardware_absence_conclusion'])

    def test_addendum_unknown_or_empty_parent_fails_before_writes(self):
        self.start_addendum()
        for parent in ('hardware-section-review:missing', '', None):
            with self.subTest(parent=parent), patch('import_hardware_source_reviews.write_if_changed') as writer:
                self.raw['reviews'][0]['extends_review_id'] = parent
                with self.assertRaisesRegex(ValueError, 'extends_review_id|parent_not_found'):
                    self.run_import(apply=True)
                writer.assert_not_called()

    def test_addendum_parent_source_tuple_must_match_exactly(self):
        self.start_addendum()
        original = copy.deepcopy(self.raw)
        for field, value in [('work_id', 'arxiv:2608.99999'), ('source_url', 'https://arxiv.org/html/2608.99999v1'),
                             ('source_version', 'v2'), ('raw_sha256', 'a' * 64), ('text_sha256', 'b' * 64),
                             ('observed_at', '2026-09-14T01:01:00Z')]:
            self.raw = copy.deepcopy(original)
            self.raw['reviews'][0][field] = value
            with self.subTest(field=field), patch('import_hardware_source_reviews.write_if_changed') as writer:
                with self.assertRaisesRegex(ValueError, 'addendum_parent_source_mismatch'):
                    self.run_import(apply=True)
                writer.assert_not_called()

    def test_addendum_binds_parent_observation_not_a_new_or_fabricated_fetch(self):
        self.start_addendum()
        self.raw['reviews'][0]['source_observation_id'] = 'source:fabricated'
        with self.assertRaisesRegex(ValueError, 'addendum_parent_observation_mismatch'):
            self.run_import()
        self.raw['reviews'][0].pop('source_observation_id')
        source = json.loads(self.observations.read_text())
        source['observation_id'] = 'source:new-observation-same-text'
        self.observations.write_text(encode(source) + '\n')
        with self.assertRaisesRegex(ValueError, 'addendum_parent_observation_mismatch'):
            self.run_import()

    def test_addendum_time_must_be_strictly_after_parent(self):
        parent = self.start_addendum()
        for value in (parent['reviewed_at'], '2026-09-14T01:30:00Z'):
            with self.subTest(value=value):
                self.raw['reviews'][0]['reviewed_at'] = value
                with self.assertRaisesRegex(ValueError, 'addendum_review_not_strictly_later'):
                    self.run_import()

    def test_addendum_only_allows_new_positive_usage_assertions(self):
        self.start_addendum()
        for decision in ('ambiguous', 'no_explicit_named_usage_in_reviewed_sections'):
            with self.subTest(decision=decision):
                self.raw['reviews'][0].update(decision=decision, devices=[])
                with self.assertRaisesRegex(ValueError, 'addendum_new_usage_assertions_required'):
                    self.run_import()

    def test_addendum_duplicate_semantics_cannot_be_hidden_by_changed_text_or_locator_order(self):
        self.start_addendum()
        row = self.raw['reviews'][0]
        row['reviewed_sections'] = ['A1', 'S4']
        row['devices'][0].update(usage_scope='study', source_locator='A1; S4',
                                 statement_zh='改写说明不构成新的使用语义。', configuration='Changed configuration')
        with patch('import_hardware_source_reviews.write_if_changed') as writer:
            with self.assertRaisesRegex(ValueError, 'addendum_duplicate_semantic_usage_conflict'):
                self.run_import(apply=True)
            writer.assert_not_called()

    def test_addendum_locator_subset_cannot_duplicate_an_existing_use(self):
        original = copy.deepcopy(self.raw['reviews'][0]['devices'][0])
        self.start_addendum()
        row = self.raw['reviews'][0]
        row['devices'] = [{**original, 'source_locator': 'A1'}]
        with patch('import_hardware_source_reviews.write_if_changed') as writer:
            with self.assertRaisesRegex(ValueError, 'addendum_duplicate_semantic_usage_conflict'):
                self.run_import(apply=True)
            writer.assert_not_called()

    def test_addendum_new_locator_or_configuration_is_not_a_new_use(self):
        self.raw['reviews'][0]['devices'][0]['source_locator'] = 'S4'
        self.start_addendum()
        row = self.raw['reviews'][0]
        row['reviewed_sections'] = ['S4', 'A1']
        for locator in ('S4; A1', 'A1'):
            row['devices'][0].update(usage_scope='study', source_locator=locator,
                                    configuration='Different configuration requires an explicit revision model',
                                    statement_zh='新增定位或不同配置不构成另一条使用语义。')
            with self.subTest(locator=locator), patch('import_hardware_source_reviews.write_if_changed') as writer:
                with self.assertRaisesRegex(ValueError, 'addendum_duplicate_semantic_usage_conflict'):
                    self.run_import(apply=True)
                writer.assert_not_called()

    def test_legacy_nonaddendum_still_preserves_distinct_locator_evidence(self):
        original = copy.deepcopy(self.raw['reviews'][0]['devices'][0])
        self.raw['reviews'][0]['devices'] = [{**original, 'source_locator': 'S4'},
                                           {**original, 'source_locator': 'A1'}]
        result = self.run_import(apply=True)
        self.assertEqual(result['added']['usage-evidence'], 2)
        records = [json.loads(line) for line in self.public.read_text().splitlines()]
        self.assertEqual(records[0]['assertion_count'], 2)
        self.assertNotIn('extends_review_id', records[0])

    def test_addendum_replay_cannot_silently_change_old_assertion_or_add_devices_to_same_id(self):
        self.start_addendum()
        self.run_import(apply=True)
        self.raw['reviews'][0]['devices'][0]['statement_zh'] = '尝试覆盖旧说明。'
        with self.assertRaisesRegex(ValueError, 'addendum_duplicate_semantic_usage_conflict'):
            self.run_import(apply=True)

    def test_addendum_can_extend_existing_addendum_but_cycles_fail_closed(self):
        parent = self.start_addendum()
        self.run_import(apply=True)
        records = [json.loads(line) for line in self.public.read_text().splitlines()]
        first = next(row for row in records if row['review_id'] != parent['review_id'])
        self.raw['reviews'][0].update(extends_review_id=first['review_id'], reviewed_at='2026-09-14T04:00:00Z')
        self.raw['reviews'][0]['devices'][0]['usage_scope'] = 'baseline'
        self.assertEqual(self.run_import(apply=True)['public_section_review_count'], 3)
        records = [json.loads(line) for line in self.public.read_text().splitlines()]
        root = next(row for row in records if row['review_id'] == parent['review_id'])
        root['extends_review_id'] = first['review_id']
        self.public.write_text(''.join(encode(row) + '\n' for row in records))
        with patch('import_hardware_source_reviews.write_if_changed') as writer:
            with self.assertRaisesRegex(ValueError, 'addendum_ancestry_cycle'):
                self.run_import(apply=True)
            writer.assert_not_called()

    def test_self_cycle_and_missing_ancestor_in_public_ledger_are_rejected(self):
        parent = self.start_addendum()
        for ancestor in (parent['review_id'], 'hardware-section-review:not-present'):
            row = {**parent, 'extends_review_id': ancestor}
            self.public.write_text(encode(row) + '\n')
            with self.subTest(ancestor=ancestor), self.assertRaisesRegex(ValueError, 'cycle|parent_not_found'):
                self.run_import()

    def public_addendum_fixture(self):
        self.start_addendum()
        self.run_import(apply=True)
        records = [json.loads(line) for line in self.public.read_text().splitlines()]
        uses = [json.loads(line) for line in (self.directory / 'usage-evidence.jsonl').read_text().splitlines()]
        observations = [json.loads(line) for line in self.observations.read_text().splitlines()]
        return records, uses, observations

    def test_public_addendum_audit_is_metadata_only_and_preserves_legacy_reviews(self):
        records, uses, observations = self.public_addendum_fixture()
        original = copy.deepcopy((records, uses, observations))
        with patch('import_hardware_source_reviews.private_file', side_effect=AssertionError('No private reads in public audit')):
            result = audit_addenda_lineage(records, uses, observations)
        self.assertEqual((records, uses, observations), original)
        self.assertEqual(result['addendum_review_count'], 1)
        self.assertEqual(result['addendum_usage_count'], 1)
        self.assertFalse(result['private_source_reverified'])
        self.assertTrue(result['public_source_bindings_checked'])
        legacy = [row for row in records if 'extends_review_id' not in row]
        legacy_uses = [row for row in uses if 'extends_review_id' not in row]
        self.assertEqual(audit_addenda_lineage(legacy, legacy_uses, [])['addendum_review_count'], 0)
        self.assertFalse(audit_addenda_lineage(records, uses)['public_source_bindings_checked'])

    def test_public_audit_recomputes_id_and_rejects_changed_parent_graph(self):
        records, uses, observations = self.public_addendum_fixture()
        for field, value in [('review_id', 'hardware-section-review:forged'),
                             ('extends_review_id', 'hardware-section-review:unknown'),
                             ('reviewed_at', '2026-09-14T02:00:00Z'), ('raw_sha256', 'f' * 64),
                             ('text_sha256', 'f' * 64), ('source_observation_id', 'source:forged')]:
            changed = copy.deepcopy(records)
            addon = next(row for row in changed if 'extends_review_id' in row)
            addon[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'addendum_'):
                audit_addenda_lineage(changed, uses, observations)

    def test_public_audit_binds_raw_and_body_hashes_and_transport_to_actual_public_observation(self):
        records, uses, observations = self.public_addendum_fixture()
        for field, value in [('raw_sha256', 'f' * 64), ('text_sha256', 'a' * 64),
                             ('observation_id', 'source:unknown'), ('status', 'partial_text'),
                             ('transport_complete', False), ('transport_returncode', 28)]:
            changed = copy.deepcopy(observations)
            changed[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'public_source_observation_mismatch'):
                audit_addenda_lineage(records, uses, changed)

    def test_public_audit_rejects_changed_usage_parent_proof_and_orphans(self):
        records, uses, observations = self.public_addendum_fixture()
        for field, value in [('extends_review_id', 'hardware-section-review:wrong-parent'),
                             ('section_review_id', 'hardware-section-review:wrong-child'),
                             ('source_observation_id', 'source:wrong'), ('review_input_hash', 'a' * 64),
                             ('reviewed_at', '2026-09-14T05:00:00Z'), ('text_sha256', 'a' * 64),
                             ('source_section_ids', ['S4'])]:
            changed = copy.deepcopy(uses)
            addon_use = next(row for row in changed if 'extends_review_id' in row)
            addon_use[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'addendum_'):
                audit_addenda_lineage(records, changed, observations)
        changed = copy.deepcopy(uses)
        orphan = copy.deepcopy(next(row for row in uses if 'extends_review_id' in row))
        orphan.update(usage_id='usage:orphan', usage_scope='baseline')
        changed.append(orphan)
        with self.assertRaisesRegex(ValueError, 'addendum_orphan_usage_proof'):
            audit_addenda_lineage(records, changed, observations)

    def test_public_audit_rejects_ancestor_usage_reuse_counts_and_semantic_duplicates(self):
        records, uses, observations = self.public_addendum_fixture()
        changed = copy.deepcopy(records)
        parent = next(row for row in changed if 'extends_review_id' not in row)
        addon = next(row for row in changed if 'extends_review_id' in row)
        addon['usage_ids'] = parent['usage_ids'][:]
        with self.assertRaisesRegex(ValueError, 'addendum_usage_reused_by_another_review'):
            audit_addenda_lineage(changed, uses, observations)
        changed = copy.deepcopy(records)
        next(row for row in changed if 'extends_review_id' in row)['assertion_count'] = 100
        with self.assertRaisesRegex(ValueError, 'assertion_count_invalid'):
            audit_addenda_lineage(changed, uses, observations)
        duplicate = copy.deepcopy(next(row for row in uses if 'extends_review_id' in row))
        duplicate['usage_id'] = 'usage:duplicate-semantic'
        with self.assertRaisesRegex(ValueError, 'duplicate_semantic_usage_conflict'):
            audit_addenda_lineage(records, [*uses, duplicate], observations)

    def test_public_audit_detects_same_use_despite_different_locator_or_configuration(self):
        records, uses, observations = self.public_addendum_fixture()
        addon = next(row for row in uses if 'extends_review_id' in row)
        duplicate = {**addon, 'usage_id': 'usage:changed-locator-and-configuration',
                     'source_locator': 'S4', 'source_section_ids': ['S4'],
                     'configuration': 'A changed configuration is not a new use'}
        with self.assertRaisesRegex(ValueError, 'addendum_duplicate_semantic_usage_conflict'):
            audit_addenda_lineage(records, [*uses, duplicate], observations)


if __name__ == "__main__":
    unittest.main()
