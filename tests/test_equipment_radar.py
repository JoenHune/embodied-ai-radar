import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from catalog_store import encode
from equipment_radar import (CATEGORIES, TABLES, audit_equipment, build_equipment_bundle,
                             equipment_sqlite, export_equipment,
                             load_equipment_authority, validate_equipment)

OBSERVED = '2026-09-14T01:00:00Z'


def make_work(number=1, status='included', month='2026-08', precision='day'):
    wid = f'arxiv:2608.{number:05d}'
    return {'work_id': wid, 'identifiers': {'arxiv': wid[6:]}, 'aliases': [],
            'title': 'Whole-body manipulation ' + str(number), 'abstract': 'Robot G1 experiments.',
            'relevance': {'status': status}, 'first_public_date': month + '-10',
            'first_public_date_precision': precision}


def source(work, **values):
    return {'work_id': work['work_id'], 'work_url': 'https://arxiv.org/abs/' + work['work_id'][6:],
            'source_url': 'https://arxiv.org/html/' + work['work_id'][6:] + 'v1',
            'source_locator': 'Section 4 Experimental setup', 'source_kind': 'paper',
            'statement': '正文明确机器人与物体接触并协调身体运动。',
            'observed_at': OBSERVED, 'review_status': 'verified', **values}


def fixture():
    w = make_work()
    payload = {'works': [w], 'manifestations': [], 'work-aliases': []}
    authority = {'devices': [{'hardware_id': 'hardware:unitree-g1', 'slug': 'unitree-g1',
                             'name': 'Unitree G1', 'vendor': 'Unitree', 'category': 'robot_platform',
                             'identity_level': 'model_specified', 'official_url': 'https://www.unitree.com/g1', 'aliases': ['G1']}],
                 'usage-evidence': [source(w, usage_id='usage:1', hardware_id='hardware:unitree-g1', role='real_robot', setting='real', usage_scope='study')],
                 'loco-reviews': [source(w, review_id='loco:1', scope='core', coordination='joint', validation='closed_loop_real')],
                 'loco-observations': [{'claim_id': 'claim:1', 'title': '接触协调', 'summary': '需要逐项核验。',
                                       'supporting_ids': [w['work_id']], 'counterevidence_ids': [],
                                       'source_urls': ['https://arxiv.org/abs/2608.00001'], 'observed_at': OBSERVED}]}
    manifest = {'dataset_version': 'test-v1', 'data_through': '2026-09-14',
                'complete_months': ['2026-07', '2026-08'], 'provisional_month': '2026-09'}
    return payload, authority, manifest


class EquipmentRadarTests(unittest.TestCase):
    def test_inertial_sensor_unit_retains_evidence_category_and_sql_roundtrip(self):
        payload, authority, manifest = fixture()
        device = authority['devices'][0]
        device.update(hardware_id='hardware:transducerm-tm171', slug='transducerm-tm171',
                      name='TransducerM TM171', vendor='TransducerM',
                      category='inertial_sensor', aliases=['TM171 AHRS unit'])
        authority['usage-evidence'][0].update(hardware_id=device['hardware_id'], role='sensing',
                                             statement='本文明确使用具名IMU提供运动状态反馈。')
        before = copy.deepcopy(authority)
        bundle = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual(authority, before)
        category = next(row for row in bundle['index']['categories'] if row['code'] == 'inertial_sensor')
        self.assertEqual(category, {'code': 'inertial_sensor', 'label': '惯性传感器', 'devices': 1, 'works': 1})
        self.assertEqual(bundle['usage']['by_work'][payload['works'][0]['work_id']][0]['role'], 'sensing')
        with tempfile.TemporaryDirectory() as tmp, closing(sqlite3.connect(':memory:')) as connection:
            api, downloads = Path(tmp) / 'api', Path(tmp) / 'downloads'
            export_equipment(bundle, api, downloads)
            equipment_sqlite(connection, bundle)
            audit_equipment(bundle, api, downloads, connection)
            saved = json.loads(connection.execute('SELECT payload_json FROM equipment_devices').fetchone()[0])
            self.assertEqual(saved['category'], 'inertial_sensor')
            self.assertEqual(saved['name'], 'TransducerM TM171')

    def test_inertial_category_does_not_admit_bare_chips_or_other_excluded_components(self):
        for name in ['IMU chip', 'AHRS IC', 'IMU integrated circuit', 'bare die', 'MEMS裸片',
                     '惯性芯片', 'IMU PCB', 'IMU电路板', 'joint module', 'servo motor', 'driver chip']:
            for field in ['name', 'aliases']:
                with self.subTest(name=name, field=field):
                    payload, authority, _ = fixture()
                    device = authority['devices'][0]
                    device.update(category='inertial_sensor', name='Packaged IMU', aliases=[])
                    device[field] = name if field == 'name' else [name]
                    with self.assertRaisesRegex(ValueError, 'equipment_out_of_scope_component'):
                        validate_equipment(payload, authority)

    def test_inertial_addition_preserves_all_existing_category_labels(self):
        self.assertEqual({key: value for key, value in CATEGORIES.items() if key != 'inertial_sensor'}, {
            'robot_platform': '人形与移动机器人', 'robot_arm': '机械臂', 'dexterous_hand': '灵巧手',
            'gripper': '夹爪', 'compute_platform': '算力平台', 'data_collection': '数采与遥操作设备',
            'tactile_sensor': '触觉传感器', 'force_sensor': '力与力矩传感器', 'vision_sensor': '视觉与空间传感器'})

    def test_build_is_pure_and_verified_use_requires_explicit_evidence(self):
        payload, authority, manifest = fixture()
        before = copy.deepcopy((payload, authority, manifest))
        result = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual((payload, authority, manifest), before)
        self.assertEqual(result['index']['counts']['works'], 1)
        self.assertEqual(result['loco-manip']['monthly'][1]['core'], 1)

    def test_missing_authority_fails_closed_but_import_can_start_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'equipment_authority_missing'):
                load_equipment_authority(temp)
            self.assertEqual(load_equipment_authority(temp, allow_missing=True), {key: [] for key in TABLES})

    def test_components_and_simulation_software_are_not_devices(self):
        for name in ['Motor', 'servo motors', 'joint-module', 'joint modules', '关节模组', 'PCB',
                     'driver chip', 'Isaac Lab', 'NVIDIA Isaac Lab simulator', 'MuJoCo 3.3',
                     'ROS 2', 'Genesis simulator', 'PyTorch', 'PyBullet']:
            with self.subTest(name=name):
                payload, authority, _ = fixture()
                authority['devices'][0]['name'] = name
                with self.assertRaisesRegex(ValueError, 'equipment_out_of_scope_component'):
                    validate_equipment(payload, authority)

    def test_mentioned_cannot_be_certified_use(self):
        payload, authority, manifest = fixture()
        authority['usage-evidence'][0]['role'] = 'mentioned'
        with self.assertRaisesRegex(ValueError, 'equipment_mention_cannot_be_verified_use'):
            validate_equipment(payload, authority)
        authority['usage-evidence'][0]['review_status'] = 'candidate'
        result = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual(result['index']['counts']['works'], 0)
        self.assertEqual(result['usage']['by_work'], {})
        self.assertEqual(result['usage']['candidates'][0]['status'], 'mention_only_not_verified_usage')

    def test_device_names_aliases_and_reported_roles_have_explicit_types(self):
        for field, value in [('name', '  '), ('name', 12), ('aliases', ['']), ('aliases', [12])]:
            payload, authority, _ = fixture()
            authority['devices'][0][field] = value
            with self.assertRaises(ValueError):
                validate_equipment(payload, authority)
        payload, authority, _ = fixture()
        authority['usage-evidence'][0]['reported_roles'] = 'sensor_calibration'
        with self.assertRaisesRegex(ValueError, 'reported_roles_invalid'):
            validate_equipment(payload, authority)

    def test_name_mentions_only_add_candidates_even_for_known_devices(self):
        payload, authority, manifest = fixture()
        payload['works'].append(make_work(2))
        result = build_equipment_bundle(payload, authority, manifest)
        self.assertNotIn('arxiv:2608.00002', result['usage']['by_work'])
        self.assertIn('arxiv:2608.00002', [r['work_id'] for r in result['usage']['candidates']])

    def test_paper_local_unknown_names_preserve_clues_without_cross_work_ids(self):
        payload, authority, manifest = fixture()
        other = make_work(2)
        other['abstract'] = 'A Humanoid robot was used.'
        payload['works'].append(other)
        for number, level in enumerate(['unspecified', 'family_only'], 1):
            authority['devices'].append({
                'hardware_id': f'hardware:unknown-humanoid-{number}', 'slug': f'unknown-humanoid-{number}',
                'name': 'Humanoid robot', 'vendor': 'unknown', 'category': 'robot_platform',
                'identity_level': level, 'identity_context_work_id': payload['works'][0]['work_id'],
                'official_url': 'https://arxiv.org/html/2608.00001v1', 'aliases': [],
            })
        before = copy.deepcopy((payload, authority, manifest))
        result = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual((payload, authority, manifest), before)
        self.assertFalse(any(r['hardware_id'].startswith('hardware:unknown-humanoid')
                             for r in result['usage']['candidates']))
        clues = result['usage']['unresolved_mentions']
        self.assertEqual(len(clues), 1, 'Same unbound name must not multiply with local device IDs')
        self.assertEqual(clues[0]['work_id'], other['work_id'])
        self.assertEqual(clues[0]['matched_term'], 'Humanoid robot')
        self.assertNotIn('hardware_id', clues[0])
        self.assertEqual(result['index']['counts']['unresolved_name_mentions'], 1)
        self.assertEqual(result['index']['counts']['usage_links'], 1)

    def test_local_and_legacy_family_discovery_stays_with_its_explicit_work(self):
        for context in [True, False]:
            with self.subTest(explicit_context=context):
                payload, authority, manifest = fixture()
                device = authority['devices'][0]
                device['identity_level'] = 'family_only'
                if context:
                    device['identity_context_work_id'] = payload['works'][0]['work_id']
                authority['usage-evidence'][0]['review_status'] = 'candidate'
                payload['works'].append(make_work(2))
                result = build_equipment_bundle(payload, authority, manifest)
                self.assertEqual([r['work_id'] for r in result['usage']['candidates']],
                                 [payload['works'][0]['work_id']])
                self.assertEqual([r['work_id'] for r in result['usage']['unresolved_mentions']],
                                 [payload['works'][1]['work_id']])
                self.assertEqual(result['usage']['by_work'], {})

    def test_model_discovery_keeps_word_boundaries_alias_order_and_case(self):
        payload, authority, manifest = fixture()
        for number, wording in enumerate(['G10 G1_extra', 'g1', 'unitree g1'], 2):
            work = make_work(number)
            work['abstract'] = wording
            payload['works'].append(work)
        result = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual([(r['work_id'], r['matched_term']) for r in result['usage']['candidates']],
                         [('arxiv:2608.00003', 'G1'), ('arxiv:2608.00004', 'Unitree G1')])
        self.assertEqual(result['usage']['unresolved_mentions'], [])

    def test_real_and_simulation_roles_cannot_swap_settings(self):
        for role, setting in [('real_robot', 'simulation'), ('simulated_robot', 'real')]:
            payload, authority, _ = fixture()
            authority['usage-evidence'][0].update(role=role, setting=setting)
            with self.assertRaisesRegex(ValueError, 'setting_conflict'):
                validate_equipment(payload, authority)

    def test_scopes_keep_study_baseline_and_calibration_separate(self):
        payload, authority, manifest = fixture()
        row = authority['usage-evidence'][0]
        row.update(role='sensing')
        for n, scope in enumerate(['baseline', 'calibration'], 2):
            authority['usage-evidence'].append({**row, 'usage_id': 'usage:' + str(n),
                                               'usage_scope': scope, 'configuration': scope})
        result = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual({r['usage_scope'] for r in result['usage']['by_work'][row['work_id']]}, {'study', 'baseline', 'calibration'})
        authority['usage-evidence'][1]['configuration'] = ''
        with self.assertRaisesRegex(ValueError, 'nonstudy_configuration'):
            validate_equipment(payload, authority)

    def test_calibration_and_baseline_reported_roles_require_correct_scope(self):
        for reported, code in [('sensor_calibration', 'calibration'), ('baseline_sensing', 'baseline')]:
            payload, authority, _ = fixture()
            authority['usage-evidence'][0].update(reported_role=reported)
            with self.assertRaisesRegex(ValueError, 'equipment_' + code + '_scope_required'):
                validate_equipment(payload, authority)

    def test_unknown_device_identity_cannot_span_unrelated_works(self):
        payload, authority, _ = fixture()
        w2 = make_work(2)
        payload['works'].append(w2)
        authority['devices'][0]['identity_level'] = 'unspecified'
        authority['usage-evidence'].append(source(w2, usage_id='usage:2', hardware_id='hardware:unitree-g1', role='real_robot', setting='real'))
        with self.assertRaisesRegex(ValueError, 'unspecified_identity_shared'):
            validate_equipment(payload, authority)

    def test_wrong_work_link_and_unrelated_paper_source_fail(self):
        for field in ['work_url', 'source_url']:
            payload, authority, _ = fixture()
            authority['usage-evidence'][0][field] = 'https://arxiv.org/abs/2608.99999'
            with self.assertRaisesRegex(ValueError, 'equipment_work_source_mismatch'):
                validate_equipment(payload, authority)

    def test_shared_project_homepage_is_not_unique_work_identity(self):
        payload, authority, _ = fixture()
        payload['works'].append(make_work(2))
        for w in payload['works']:
            w['project_url'] = 'https://lab.example/projects'
        authority['usage-evidence'][0].update(source_kind='project', source_url='https://lab.example/projects', work_url='https://lab.example/projects')
        with self.assertRaisesRegex(ValueError, 'equipment_work_source_mismatch'):
            validate_equipment(payload, authority)

    def test_canonical_alias_resolves_without_mutating_authority(self):
        payload, authority, _ = fixture()
        old = payload['works'][0]['work_id']
        payload['works'][0].update(work_id='doi:10.1234/g1', aliases=[old])
        result = validate_equipment(payload, authority)
        self.assertEqual(result['usage-evidence'][0]['work_id'], 'doi:10.1234/g1')
        self.assertEqual(authority['usage-evidence'][0]['work_id'], old)

    def test_ambiguous_work_alias_and_empty_source_context_fail(self):
        payload, authority, _ = fixture()
        payload['works'].append({**make_work(2), 'aliases': ['arxiv:2608.00001']})
        with self.assertRaisesRegex(ValueError, 'unknown_or_ambiguous'):
            validate_equipment(payload, authority)
        payload, authority, _ = fixture()
        authority['usage-evidence'][0]['statement'] = '  '
        with self.assertRaisesRegex(ValueError, 'source_context_required'):
            validate_equipment(payload, authority)

    def test_private_or_credentialed_evidence_urls_fail(self):
        for url in ['http://localhost/x', 'http://172.16.2.3/x', 'http://[::1]/x', 'http://192.168.0.1/x', 'https://user:secret@site.example/x', 'https://host.local/x']:
            payload, authority, _ = fixture()
            authority['usage-evidence'][0]['source_url'] = url
            with self.assertRaises(ValueError):
                validate_equipment(payload, authority)

    def test_utc_and_unique_semantic_records_required(self):
        payload, authority, _ = fixture()
        authority['usage-evidence'][0]['observed_at'] = '2026-09-14T09:00:00+08:00'
        with self.assertRaisesRegex(ValueError, 'utc_observation'):
            validate_equipment(payload, authority)
        payload, authority, _ = fixture()
        authority['usage-evidence'].append({**authority['usage-evidence'][0], 'usage_id': 'usage:other'})
        with self.assertRaisesRegex(ValueError, 'duplicate_usage_evidence'):
            validate_equipment(payload, authority)

    def test_nonincluded_observation_dependency_is_candidate_with_fetchable_detail_id(self):
        payload, authority, manifest = fixture()
        w2 = make_work(2, status='manual_review', month='2026-09')
        payload['works'].append(w2)
        authority['loco-reviews'].append(source(w2, review_id='loco:2', scope='core', coordination='joint', validation='closed_loop_real'))
        authority['loco-observations'][0]['supporting_ids'].append(w2['work_id'])
        original = copy.deepcopy(payload)
        result = build_equipment_bundle(payload, authority, manifest)
        loco = result['loco-manip']
        self.assertEqual(payload, original)
        self.assertIn(w2['work_id'], loco['work_ids']['candidates'])
        self.assertNotIn(w2['work_id'], loco['work_ids']['core'])
        self.assertEqual(loco['observations'][0]['review_status'], 'candidate')
        self.assertEqual(loco['observations'][0]['candidate_work_ids'], [w2['work_id']])
        self.assertEqual(loco['observations'][0]['supporting_work_status'][w2['work_id']]['relevance_status'], 'manual_review')
        self.assertEqual(loco['monthly'][-1]['candidates'], 0)
        self.assertEqual(next(r for r in loco['reviews'] if r['work_id'] == w2['work_id'])['candidate_reason'], 'catalog_not_included')
        # The existing cards builder obtains every lane ID, not just core IDs.
        detail_ids = set(result['usage']['by_work']) | {wid for lane in loco['work_ids'].values() for wid in lane}
        self.assertTrue(set(loco['observations'][0]['supporting_ids']).issubset(detail_ids))

    def test_candidate_review_is_visible_but_not_in_core_or_hardware_totals(self):
        payload, authority, manifest = fixture()
        authority['usage-evidence'][0]['review_status'] = 'candidate'
        authority['loco-reviews'][0]['review_status'] = 'candidate'
        result = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual(result['index']['counts']['usage_links'], 0)
        self.assertEqual(result['loco-manip']['work_ids']['core'], [])
        self.assertEqual(result['loco-manip']['counts']['candidates'], 1)
        self.assertEqual(result['loco-manip']['observations'][0]['review_status'], 'candidate')

    def test_only_precisely_dated_included_works_enter_monthly_trends(self):
        for status, precision in [('manual_review', 'day'), ('excluded', 'day'), ('included', 'year'), ('included', 'unknown')]:
            payload, authority, manifest = fixture()
            payload['works'][0].update(relevance={'status': status}, first_public_date_precision=precision)
            result = build_equipment_bundle(payload, authority, manifest)
            self.assertEqual(sum(r['core'] + r['support'] + r['candidates'] for r in result['loco-manip']['monthly']), 0)

    def test_api_downloads_sqlite_roundtrip_and_tamper_detection(self):
        payload, authority, manifest = fixture()
        bundle = build_equipment_bundle(payload, authority, manifest)
        for tamper in ['none', 'api', 'sql_api', 'sql_extra', 'sql_work_id', 'download_duplicate']:
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as tmp, closing(sqlite3.connect(':memory:')) as connection:
                api, downloads = Path(tmp) / 'api', Path(tmp) / 'downloads'
                export_equipment(bundle, api, downloads)
                equipment_sqlite(connection, bundle)
                if tamper == 'api':
                    (api / 'index.json').write_text('{}')
                elif tamper == 'sql_api':
                    connection.execute("UPDATE equipment_api SET payload_json='{}' WHERE path='usage'")
                elif tamper == 'sql_extra':
                    connection.execute("INSERT INTO equipment_api VALUES ('extra', '{}')")
                elif tamper == 'sql_work_id':
                    connection.execute("UPDATE equipment_usage_evidence SET work_id='wrong'")
                elif tamper == 'download_duplicate':
                    f = downloads / 'usage-evidence.jsonl'
                    f.write_text(f.read_text() * 2)
                if tamper == 'none':
                    audit_equipment(bundle, api, downloads, connection)
                else:
                    with self.assertRaisesRegex(ValueError, 'mismatch'):
                        audit_equipment(bundle, api, downloads, connection)


if __name__ == '__main__':
    unittest.main()
