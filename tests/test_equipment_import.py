import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from equipment_radar import TABLES, build_equipment_bundle, validate_equipment
from import_equipment_reviews import import_reviews, merge_equipment_reviews, normalize
from test_equipment_radar import OBSERVED, fixture, make_work


def raw_work(number=1, name='Unitree G1', specificity='exact', roles=None, validation='real_robot_closed_loop'):
    work = make_work(number)
    url = 'https://arxiv.org/html/' + work['work_id'][6:] + 'v1'
    return {'work_id': work['work_id'], 'arxiv_id': work['work_id'][6:], 'title': work['title'],
            'source_url': url, 'source_version': 'v1', 'verification_status': 'verified',
            'devices': [{'device_name': name, 'vendor': 'Unitree', 'category': 'robot_platform',
                         'model_specificity': specificity, 'usage_roles': roles or ['real_robot'],
                         'validation_level': validation, 'verification_status': 'verified',
                         'source_url': url, 'source_section': 'Section 4 Setup',
                         'evidence_paraphrase_zh': '正文明确本设备的实验用途。', 'observed_at': OBSERVED}],
            'loco_manipulation': {'scope': 'core/coordinated', 'control_class': 'whole_body_contact',
                                 'validation_level': validation, 'source_url': url,
                                 'source_section': 'Section 4 Setup', 'observed_at': OBSERVED,
                                 'evidence_paraphrase_zh': '实验协调接触与身体运动。'}}


def raw_fixture(works=None):
    return {'works': works or [raw_work()], 'observed_at': OBSERVED, 'observations': []}


class EquipmentImportTests(unittest.TestCase):
    def test_normalization_is_deterministic_and_does_not_mutate_raw_input(self):
        raw = raw_fixture()
        before = copy.deepcopy(raw)
        first = normalize(raw)
        self.assertEqual(first, normalize(raw))
        self.assertEqual(raw, before)

    def test_known_exact_model_aliases_share_identity_but_settings_are_distinct(self):
        works = [raw_work(1, roles=['real_robot']), raw_work(2, name='Unitree G1 model', roles=['simulated_robot'], validation='simulation_only')]
        normalized = normalize(raw_fixture(works))
        self.assertEqual(len(normalized['devices']), 1)
        self.assertEqual(normalized['devices'][0]['name'], 'Unitree G1')
        self.assertEqual({r['setting'] for r in normalized['usage-evidence']}, {'real', 'simulation'})

    def test_unspecified_and_family_devices_do_not_merge_across_works(self):
        for specificity in ['unknown', 'family']:
            with self.subTest(specificity=specificity):
                normalized = normalize(raw_fixture([raw_work(1, name='RGB camera', specificity=specificity),
                                                   raw_work(2, name='RGB camera', specificity=specificity)]))
                self.assertEqual(len(normalized['devices']), 2)
                self.assertEqual(len({r['hardware_id'] for r in normalized['usage-evidence']}), 2)

    def test_unknown_family_and_exact_same_name_cannot_upgrade_by_input_order(self):
        works = [raw_work(1, specificity='family'), raw_work(2, specificity='exact')]
        first, second = normalize(raw_fixture(works)), normalize(raw_fixture(list(reversed(works))))
        self.assertEqual(len(first['devices']), 2)
        self.assertEqual({r['hardware_id']: r['identity_level'] for r in first['devices']},
                         {r['hardware_id']: r['identity_level'] for r in second['devices']})

    def test_category_or_vendor_conflicts_fail_without_last_row_wins(self):
        for field, value, error in [('category', 'robot_arm', 'category_conflict'), ('vendor', 'Other Maker', 'identity_conflict')]:
            works = [raw_work(1), raw_work(2)]
            works[1]['devices'][0][field] = value
            with self.assertRaisesRegex(ValueError, error):
                normalize(raw_fixture(works))

    def test_baseline_study_calibration_roles_keep_separate_ids(self):
        raw = raw_fixture([raw_work(roles=['sensing', 'baseline_sensing', 'sensor_calibration'])])
        normalized = normalize(raw)
        rows = normalized['usage-evidence']
        self.assertEqual(len(rows), 3)
        self.assertEqual({r['usage_scope'] for r in rows}, {'study', 'baseline', 'calibration'})
        calibration = next(r for r in rows if r['usage_scope'] == 'calibration')
        self.assertEqual(calibration['role'], 'sensing')
        self.assertEqual(calibration['setting'], 'real')
        self.assertIn('校准', calibration['configuration'])
        self.assertIn('不代表策略部署', calibration['configuration'])
        validate_equipment({'works': [make_work()]}, normalized)

    def test_explicit_baseline_only_marker_is_retained(self):
        raw = raw_fixture([raw_work(roles=['sensing'])])
        raw['works'][0]['devices'][0]['method_role'] = 'baseline_only'
        row = normalize(raw)['usage-evidence'][0]
        self.assertEqual(row['usage_scope'], 'baseline')
        self.assertIn('对照基线', row['configuration'])

    def test_synonymous_roles_deduplicate_without_losing_original_roles(self):
        normalized = normalize(raw_fixture([raw_work(roles=['teleoperation', 'data_collection'])]))
        self.assertEqual(len(normalized['usage-evidence']), 1)
        self.assertEqual(normalized['usage-evidence'][0]['reported_roles'], ['data_collection', 'teleoperation'])

    def test_compute_allocation_does_not_infer_physical_robot_trial(self):
        raw = raw_fixture([raw_work(name='8 × NVIDIA H100 GPUs', roles=['training_compute'])])
        raw['works'][0]['devices'][0].update(category='compute_platform', vendor='NVIDIA')
        normalized = normalize(raw)
        self.assertEqual(normalized['devices'][0]['name'], 'NVIDIA H100')
        row = normalized['usage-evidence'][0]
        self.assertEqual(row['setting'], 'unknown')
        self.assertIn('8 ×', row['configuration'])

    def test_simulation_data_and_dataset_source_are_not_real_trials(self):
        rows = normalize(raw_fixture([raw_work(roles=['simulation_data_generation', 'dataset_source'])]))['usage-evidence']
        self.assertEqual({r['setting'] for r in rows}, {'simulation', 'dataset'})

    def test_simulation_replay_and_closed_loop_validations_remain_separate(self):
        raw = raw_fixture([raw_work(1, validation='simulation_only'),
                           raw_work(2, validation='simulation_and_real_trajectory_replay'),
                           raw_work(3, validation='real_robot_closed_loop_offline_reference')])
        rows = normalize(raw)['loco-reviews']
        self.assertEqual({r['validation'] for r in rows}, {'simulation_only', 'replay_only_real', 'closed_loop_real'})
        self.assertTrue(any(r['validation_context'] == 'real_robot_closed_loop_offline_reference' for r in rows))

    def test_mentioned_is_not_automatically_promoted(self):
        raw = raw_fixture([raw_work(roles=['mentioned'])])
        with self.assertRaisesRegex(ValueError, 'mention_cannot_be_verified'):
            validate_equipment({'works': [make_work()]}, normalize(raw))
        raw['works'][0]['devices'][0]['verification_status'] = 'candidate'
        normalized = normalize(raw)
        validate_equipment({'works': [make_work()]}, normalized)
        self.assertEqual(normalized['usage-evidence'][0]['review_status'], 'candidate')

    def test_input_duplicate_with_conflicting_evidence_is_rejected(self):
        one, two = raw_work(), raw_work()
        two['devices'][0]['evidence_paraphrase_zh'] = '不同证据，不可静默覆盖。'
        with self.assertRaisesRegex(ValueError, 'normalization_conflict'):
            normalize(raw_fixture([one, two]))

    def test_merge_validates_full_graph_and_is_idempotent(self):
        payload, _, _ = fixture()
        proposed = normalize(raw_fixture())
        blank = {key: [] for key in TABLES}
        merged = merge_equipment_reviews(payload, blank, proposed)
        self.assertEqual(merged, merge_equipment_reviews(payload, merged, proposed))
        self.assertEqual(blank, {key: [] for key in TABLES})
        self.assertEqual(proposed, normalize(raw_fixture()))

    def test_merge_accepts_new_rows_referencing_existing_device(self):
        payload, authority, _ = fixture()
        proposed = {key: [] for key in TABLES}
        proposed['usage-evidence'] = [{**authority['usage-evidence'][0], 'usage_id': 'usage:baseline',
                                      'usage_scope': 'baseline', 'configuration': '仅用于对照基线'}]
        merged = merge_equipment_reviews(payload, authority, proposed)
        self.assertEqual(len(merged['usage-evidence']), 2)

    def test_late_table_conflict_causes_zero_writes(self):
        payload, _, _ = fixture()
        raw = raw_fixture()
        raw['observations'] = [{'id': 'claim', 'text': '新判断', 'works': ['arxiv:2608.00001']}]
        old = normalize(raw)
        old['loco-observations'][0]['summary'] = '已有判断'
        with patch('import_equipment_reviews.load_equipment_authority', return_value=old), patch('import_equipment_reviews.write_if_changed') as writer:
            with self.assertRaisesRegex(ValueError, 'existing_authority_conflict'):
                import_reviews(raw, payload, '/unused-test-authority', apply=True)
            writer.assert_not_called()

    def test_cross_table_validation_failure_causes_zero_writes(self):
        payload, _, _ = fixture()
        old = normalize(raw_fixture())
        old['usage-evidence'].append({**old['usage-evidence'][0], 'usage_id': 'usage:duplicate-semantic'})
        with patch('import_equipment_reviews.load_equipment_authority', return_value=old), patch('import_equipment_reviews.write_if_changed') as writer:
            with self.assertRaisesRegex(ValueError, 'duplicate_usage_evidence'):
                import_reviews(raw_fixture(), payload, '/unused-test-authority', apply=True)
            writer.assert_not_called()

    def test_dry_run_never_creates_authority_directory(self):
        payload, _, _ = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'not-created'
            result = import_reviews(raw_fixture(), payload, directory)
            self.assertFalse(result['applied'])
            self.assertFalse(directory.exists())

    def test_manual_review_work_is_not_promoted_by_equipment_or_observation(self):
        payload, _, manifest = fixture()
        payload['works'][0]['relevance'] = {'status': 'manual_review'}
        raw = raw_fixture()
        raw['observations'] = [{'id': 'm3', 'text': 'M3-Tele来源观察', 'works': ['arxiv:2608.00001']}]
        bundle = build_equipment_bundle(payload, normalize(raw), manifest)
        self.assertEqual(payload['works'][0]['relevance']['status'], 'manual_review')
        self.assertEqual(bundle['index']['counts']['works'], 0)
        self.assertEqual(bundle['loco-manip']['counts']['core'], 0)
        self.assertEqual(bundle['loco-manip']['counts']['candidates'], 1)
        self.assertEqual(bundle['loco-manip']['observations'][0]['review_status'], 'candidate')


if __name__ == '__main__':
    unittest.main()
