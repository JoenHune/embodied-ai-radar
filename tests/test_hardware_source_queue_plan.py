"""Read-only planning: inventory retention is distinct from fetch eligibility."""
import argparse
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import plan_hardware_source_queue as planner
from catalog_store import TABLES, encode, fingerprint
from collect_hardware_sources import load_targets, PARSER_VERSION


def work(number=1, *, when='2026-09-01', status='manual_review', title='Robot manipulation', version='v1'):
    aid = f'2609.{number:05d}'
    return {'work_id': 'arxiv:' + aid, 'title': title, 'authors': ['Test Author'],
            'identifiers': {'arxiv': aid + (version or '')}, 'first_public_date': when,
            'first_public_date_precision': 'day' if when else 'unknown', 'relevance': {'status': status},
            'directions': ['D4'], 'questions': ['Q0'], 'source_record_ids': [], 'evidence_flags': {}}


def fixture(works=None):
    works = works or [work()]
    payload = {table: [] for table in TABLES}
    payload['works'] = works
    queue = {'schema_version': '1', 'queue_mode': 'all_arxiv', 'scope': 'full_canonical_arxiv_processing_queue_not_fulltext_coverage',
             'opaque_top': {'keep': [1, 2]}, 'queue': [{'work_id': row['work_id'], 'title': row['title'],
             'arxiv_id': row['identifiers']['arxiv'], 'opaque': {'source': ['unchanged']}} for row in works]}
    targets = {}
    for row in works:
        aid, version = planner.arxiv_identity(row['identifiers']['arxiv'])
        targets[row['work_id']] = {'work_id': row['work_id'], 'arxiv_id': aid, 'version': version,
                                   'source_url': f'https://arxiv.org/html/{aid}{version or ""}'}
    index = {'full': defaultdict(set), 'read': defaultdict(set), 'attempted': defaultdict(list),
             'states': {}, 'cache_issues': []}
    return queue, payload, targets, index


def apply(parts, cards=(), limit=100, as_of='2026-09-15'):
    return planner.plan(*parts, list(cards), as_of=as_of, limit=limit)


class PlanningTests(unittest.TestCase):
    def test_all_ids_fields_and_scope_retained_with_bounded_subset(self):
        parts = fixture([work(1), work(2, status='excluded'), work(3, when='2024-01-01', status='included')])
        before = copy.deepcopy(parts)
        result = apply(parts, limit=1)
        original = {row['work_id']: row for row in parts[0]['queue']}
        self.assertEqual(len(result['inventory.json']['queue']), 3)
        self.assertEqual({row['work_id']: row for row in result['inventory.json']['queue']}, original)
        self.assertEqual(result['first-fetch.json']['queue'], [original['arxiv:2609.00001']])
        self.assertEqual(result['first-fetch.json']['scope'], parts[0]['scope'])
        self.assertEqual(parts, before)
        self.assertEqual(result['report.json']['missing_ids'], 0)

    def test_exact_35118_inventory_regression_no_fixed_production_total(self):
        parts = fixture([work(i) for i in range(1, 35119)])
        result = apply(parts, limit=20)
        self.assertEqual(len(result['inventory.json']['queue']), 35118)
        self.assertEqual(len({row['work_id'] for row in result['inventory.json']['queue']}), 35118)
        self.assertEqual(len(result['first-fetch.json']['queue']), 20)

    def test_duplicate_and_unknown_ids_rejected_before_deduplication(self):
        parts = fixture()
        parts[0]['queue'].append(copy.deepcopy(parts[0]['queue'][0]))
        with self.assertRaisesRegex(planner.PlanError, 'duplicate_queue_id'):
            apply(parts)
        parts = fixture()
        parts[0]['queue'][0]['work_id'] = 'arxiv:9999.00001'
        with self.assertRaisesRegex(planner.PlanError, 'unknown_queue_id'):
            apply(parts)

    def test_same_version_cached_and_read_are_not_fetched(self):
        parts = fixture([work(1), work(2)])
        queue, payload, targets, index = parts
        index['full']['arxiv:2609.00001'].add('v1')
        index['states'][('arxiv:2609.00001', targets['arxiv:2609.00001']['source_url'])] = {'status': 'full_text_available'}
        index['read']['arxiv:2609.00002'].add('v1')
        result = apply(parts)
        self.assertEqual(result['first-fetch.json']['queue'], [])
        self.assertEqual(result['report.json']['bucket_counts'], {'Z0_same_version_full_or_read': 1, 'Z2_cache_or_read_without_success_state': 1})

    def test_other_or_unknown_cached_version_held_not_retargeted(self):
        for cached in ('v2', None):
            parts = fixture()
            parts[3]['full']['arxiv:2609.00001'].add(cached)
            result = apply(parts)
            self.assertEqual(result['first-fetch.json']['queue'], [])
            self.assertEqual(result['ordering.json']['records'][0]['bucket'], 'Z1_other_version_full_or_read')
            self.assertEqual(result['ordering.json']['records'][0]['target']['version'], 'v1')

    def test_failures_and_other_parser_attempts_stay_in_r0(self):
        parts = fixture()
        parts[3]['attempted']['arxiv:2609.00001'] = [{'status': 'blocked', 'version': 'v1'}]
        parts[3]['states'][('arxiv:2609.00001', parts[2]['arxiv:2609.00001']['source_url'])] = {
            'status': 'blocked', 'next_retry_at': '2026-09-16T00:00:00Z'}
        result = apply(parts)
        self.assertEqual(result['first-fetch.json']['queue'], [])
        hold = result['holds.json']['records'][0]
        self.assertEqual(hold['bucket'], 'R0_attempted_needs_repair_or_retry')
        self.assertEqual(hold['next_retry_at'], '2026-09-16T00:00:00Z')

    def test_unknown_target_version_count_and_current_month_ratio(self):
        result = apply(fixture([work(1, version=None), work(2)]))
        self.assertEqual(result['report.json']['unknown_target_version_count'], 1)
        self.assertEqual(result['report.json']['current_month_version_coverage']['known_ratio'], .5)
        self.assertEqual(result['report.json']['bucket_counts']['H0_unknown_target_version'], 1)

    def test_historical_unknown_and_other_requested_version_hold(self):
        for required in (None, 'v2'):
            parts = fixture()
            result = apply(parts, [{'work_id': 'arxiv:2609.00001', 'selected_month': '2026-08', 'text_version': required}])
            self.assertEqual(result['first-fetch.json']['queue'], [])
            self.assertEqual(result['report.json']['bucket_counts']['H1_historical_version_review'], 1)
            self.assertEqual(result['holds.json']['historical_version_tasks'][0]['required_version'], required)

    def test_current_month_and_t0_review_outweigh_old_included_without_promotion(self):
        parts = fixture([work(1, when='2024-01-01', status='included'), work(2), work(3, when='2026-06-01', status='candidate')])
        parts[1]['organizations'] = [{'organization_id': 'org:lab', 'tier': 'T0'}]
        parts[1]['work-organization-links'] = [{'work_id': 'arxiv:2609.00003', 'organization_id': 'org:lab',
            'evidence_grade': 'G1', 'evidence_url': 'https://lab.example/paper'}]
        result = apply(parts)
        self.assertEqual([row['work_id'] for row in result['first-fetch.json']['queue']],
                         ['arxiv:2609.00002', 'arxiv:2609.00003', 'arxiv:2609.00001'])
        self.assertEqual(result['ordering.json']['records'][1]['relevance'], 'candidate')

    def test_famous_group_non_robotics_does_not_gain_T0_priority(self):
        parts = fixture([work(title='A Physics Olympiad Solution', when='2026-06-01')])
        parts[1]['organizations'] = [{'organization_id': 'org:lab', 'tier': 'T0'}]
        parts[1]['work-organization-links'] = [{'work_id': 'arxiv:2609.00001', 'organization_id': 'org:lab',
            'evidence_grade': 'G1', 'evidence_url': 'https://lab.example/paper'}]
        record = apply(parts)['ordering.json']['records'][0]
        self.assertFalse(record['T0_priority_guaranteed'])
        self.assertEqual(record['bucket'], 'P6_window_scope_review')

    def test_g2_time_mismatch_not_promoted(self):
        parts = fixture([work(when='2026-06-01')])
        parts[1]['organizations'] = [{'organization_id': 'org:lab', 'tier': 'T0'}]
        parts[1]['work-organization-links'] = [{'work_id': 'arxiv:2609.00001', 'organization_id': 'org:lab',
            'evidence_grade': 'G2', 'evidence_url': 'https://lab.example/paper',
            'membership_evidence': {'author': 'Test Author', 'valid_from': '2026-07-01', 'source_url': 'https://lab.example/people'}}]
        self.assertEqual(apply(parts)['ordering.json']['records'][0]['T0'], [])

    def test_current_selected_is_first_and_selection_does_not_expand_queue(self):
        parts = fixture([work(1), work(2, title='Some scope review')])
        parts[1]['works'].append(work(3))
        cards = [{'work_id': f'arxiv:2609.{n:05d}', 'text_version': 'v1', 'selected_month': '2026-09'} for n in (2, 3)]
        result = apply(parts, cards)
        self.assertEqual(result['first-fetch.json']['queue'][0]['work_id'], 'arxiv:2609.00002')
        self.assertEqual(len(result['inventory.json']['queue']), 2)

    def test_month_window_year_boundary_and_unknown_date_preserved(self):
        self.assertEqual(planner.month_window('2026-01-03'), [f'2025-{i:02d}' for i in range(1, 13)] + ['2026-01'])
        parts = fixture([work(1, when='2025-09-01', status='included'), work(2, when='2025-08-31', status='included'),
                         work(3, when=None, status='included'), work(4, when='2026-09-30')])
        records = {row['work_id']: row for row in apply(parts)['ordering.json']['records']}
        self.assertEqual(records['arxiv:2609.00001']['bucket'], 'P4_window_included')
        self.assertEqual(records['arxiv:2609.00002']['bucket'], 'P7_older_included')
        self.assertIsNone(records['arxiv:2609.00003']['month'])
        self.assertEqual(records['arxiv:2609.00004']['bucket'], 'H2_future_date')

    def test_bad_dates_versions_and_source_urls_fail_closed(self):
        for bad in ('2026-02-30', '2026-9-01', 'garbage'):
            with self.assertRaisesRegex(planner.PlanError, 'invalid_date'):
                apply(fixture([work(when=bad)]))
        parts = fixture()
        parts[0]['queue'][0]['source_url'] = 'https://arxiv.org/html/2609.00001v2'
        with self.assertRaisesRegex(planner.PlanError, 'job_source_url_resolution_mismatch'):
            apply(parts)
        with self.assertRaisesRegex(planner.PlanError, 'monthly_card_version_invalid'):
            apply(fixture(), [{'work_id': 'arxiv:2609.00001', 'selected_month': '2026-09', 'text_version': 'latest'}])

    def test_declared_month_and_year_precision_are_valid_not_guessed_days(self):
        row = work(when='2026-08')
        row['first_public_date_precision'] = 'month'
        result = apply(fixture([row]))
        self.assertEqual(result['ordering.json']['records'][0]['month'], '2026-08')
        self.assertEqual(result['ordering.json']['records'][0]['date'], '2026-08')
        row.update(first_public_date='2026', first_public_date_precision='year')
        self.assertIsNone(apply(fixture([row]))['ordering.json']['records'][0]['month'])
        row.update(first_public_date='2026-13', first_public_date_precision='month')
        with self.assertRaisesRegex(planner.PlanError, 'invalid_date'):
            apply(fixture([row]))


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.parts = fixture()
        self.args = argparse.Namespace(queue=self.root / 'queue.json', catalog=self.root / 'catalog',
            cache_dir=self.root / 'cache', observations=self.root / 'observations.jsonl', readings=self.root / 'readings.jsonl',
            monthly_dir=self.root / 'monthly', output_dir=self.root / 'out', as_of='2026-09-15', limit=10,
            min_body_characters=1500, min_sections=2, dry_run=True)
        self.args.catalog.mkdir()
        self.args.monthly_dir.mkdir()
        (self.args.cache_dir / 'requests').mkdir(parents=True)
        (self.args.cache_dir / 'objects').mkdir()
        self.args.queue.write_text(encode(self.parts[0]))
        (self.args.catalog / 'manifest.json').write_text('{}')
        for table, rows in self.parts[1].items():
            (self.args.catalog / f'{table}.jsonl').write_text(''.join(encode(row) + '\n' for row in rows))
        self.args.observations.write_text('')
        self.args.readings.write_text('')

    def disk_snapshot(self):
        return {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.root.rglob('*') if path.is_file() and not path.is_relative_to(self.args.output_dir)}

    def observation(self, *, status='full_text_available', version='v1'):
        target = dict(self.parts[2]['arxiv:2609.00001'])
        target.update(version=version, source_url='https://arxiv.org/html/2609.00001' + version)
        raw = b'original cached body is not parsed or rehashed by planner'
        raw_sha = hashlib.sha256(raw).hexdigest()
        obj = self.args.cache_dir / 'objects' / f'{raw_sha}.html'
        obj.write_bytes(raw)
        return {**target, 'effective_url': target['source_url'], 'status': status,
            'observed_at': '2026-09-14T01:00:00Z', 'raw_sha256': raw_sha, 'cache_ref': str(obj),
            'parser_version': PARSER_VERSION, 'thresholds': {'min_body_characters': 1500, 'min_sections': 2}}

    def state(self, row):
        key = fingerprint([row['work_id'], row['source_url'], row['parser_version'], 1500, 2])
        path = self.args.cache_dir / 'requests' / f'{key}.json'
        path.write_text(encode(row))
        return path

    def test_dry_run_has_no_writes_or_collector_creation(self):
        before = self.disk_snapshot()
        with patch('collect_hardware_sources.Collector', side_effect=AssertionError('must not instantiate')):
            result = planner.create_plan(self.args)
        self.assertFalse(self.args.output_dir.exists())
        self.assertEqual(self.disk_snapshot(), before)
        self.assertEqual(result['report.json']['first_fetch_jobs'], 1)
        self.assertEqual(len(result['report.json']['monthpackage_sources']), 13)

    def test_explicit_new_output_is_complete_and_input_readonly(self):
        before = self.disk_snapshot()
        self.args.dry_run = False
        result = planner.create_plan(self.args)
        complete = json.loads((self.args.output_dir / 'plan-complete.json').read_text())
        self.assertEqual(self.disk_snapshot(), before)
        for name, digest in complete['files_sha256'].items():
            self.assertEqual(hashlib.sha256((self.args.output_dir / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(load_targets(self.args.catalog, result['first-fetch.json']['queue']),
                         load_targets(self.args.catalog, self.parts[0]['queue']))
        with self.assertRaisesRegex(planner.PlanError, 'output_directory_must_be_new'):
            planner.create_plan(self.args)

    def test_source_or_nested_output_cannot_be_overwritten(self):
        for path in (self.args.queue, self.args.catalog / 'new-output', self.args.cache_dir / 'out'):
            self.args.output_dir = path
            with self.assertRaises(planner.PlanError):
                planner.create_plan(self.args)

    def test_request_state_identity_mismatch_rejected(self):
        row = self.observation(status='blocked')
        path = self.state(row)
        row['source_url'] = 'https://arxiv.org/html/2609.00001v2'
        row['version'] = 'v2'
        path.write_text(encode(row))
        with self.assertRaisesRegex(planner.PlanError, 'request_state_identity_mismatch'):
            planner.create_plan(self.args)
        self.assertFalse(self.args.output_dir.exists())

    def test_legitimate_failed_effective_identity_is_isolated_not_corrupt(self):
        for status in ('identity_mismatch', 'partial_text', 'unavailable'):
            row = self.observation(status=status)
            row['effective_url'] = 'https://arxiv.org/html/2609.99999v5'
            self.args.observations.write_text(encode(row) + '\n')
            result = planner.create_plan(self.args)
            self.assertEqual(result['report.json']['bucket_counts'], {'R0_attempted_needs_repair_or_retry': 1})
            self.assertEqual(result['first-fetch.json']['queue'], [])

    def test_pre_assessment_failure_without_thresholds_uses_only_matching_key(self):
        row = self.observation(status='blocked')
        row.pop('thresholds')
        self.state(row)
        result = planner.create_plan(self.args)
        self.assertEqual(len(result['report.json']['legacy_states_without_thresholds']), 1)
        self.assertEqual(result['first-fetch.json']['queue'], [])
        self.args.min_sections = 3
        with self.assertRaisesRegex(planner.PlanError, 'request_state_identity_mismatch'):
            planner.create_plan(self.args)

    def test_legacy_failed_row_carried_to_current_key_requires_exact_log_record(self):
        row = self.observation(status='unavailable')
        row['parser_version'] = 'arxiv-html-body-v1'
        row.pop('thresholds')
        self.args.observations.write_text(encode(row) + '\n')
        key = fingerprint([row['work_id'], row['source_url'], PARSER_VERSION, 1500, 2])
        path = self.args.cache_dir / 'requests' / f'{key}.json'
        path.write_text(encode(row))
        result = planner.create_plan(self.args)
        self.assertEqual(result['report.json']['bucket_counts'], {'R0_attempted_needs_repair_or_retry': 1})
        self.assertEqual(len(result['report.json']['legacy_carried_failures']), 1)
        self.args.observations.write_text('')
        with self.assertRaisesRegex(planner.PlanError, 'request_state_identity_mismatch'):
            planner.create_plan(self.args)

    def test_unlinked_monthly_event_counted_but_not_a_work(self):
        (self.args.monthly_dir / '2026-09.json').write_text(encode({'month': '2026-09'}))
        with patch('generate_v3_editorial.build_evidence_packet', return_value={'month': '2026-09',
                   'evidence_cards': [{'kind': 'event', 'event_id': 'org:change'}]}):
            result = planner.create_plan(self.args)
        self.assertEqual(result['report.json']['monthpackage_sources'][-1]['events_without_work_not_queued'], 1)
        self.assertEqual(len(result['inventory.json']['queue']), 1)

    def test_log_unknown_identity_and_malformed_json_rejected(self):
        row = self.observation()
        row['work_id'] = 'arxiv:2609.99999'
        self.args.observations.write_text(encode(row) + '\n')
        with self.assertRaisesRegex(planner.PlanError, 'source_unknown_work_id'):
            planner.create_plan(self.args)
        self.args.observations.write_text('{not json')
        with self.assertRaisesRegex(planner.PlanError, 'observation_log_corrupt'):
            planner.create_plan(self.args)

    def test_trailing_incomplete_active_object_explicitly_reported_not_repaired(self):
        self.args.observations.write_text('{"work_id":')
        before = self.args.observations.read_bytes()
        result = planner.create_plan(self.args)
        self.assertTrue(result['report.json']['baseline']['log_snapshot']['incomplete_tail_ignored'])
        self.assertEqual(self.args.observations.read_bytes(), before)

    def test_cached_without_state_and_state_without_log_never_redownload(self):
        row = self.observation()
        self.args.observations.write_text(encode(row) + '\n')
        result = planner.create_plan(self.args)
        self.assertEqual(result['report.json']['bucket_counts'], {'Z2_cache_or_read_without_success_state': 1})
        self.args.observations.write_text('')
        self.state(row)
        result = planner.create_plan(self.args)
        self.assertEqual(result['report.json']['bucket_counts'], {'Z0_same_version_full_or_read': 1})
        self.assertEqual(result['first-fetch.json']['queue'], [])

    def test_cached_source_stat_only_and_unsafe_path_rejected(self):
        row = self.observation()
        self.args.observations.write_text(encode(row) + '\n')
        original = Path.read_bytes
        def guarded(path):
            if path.suffix == '.html':
                raise AssertionError('Must not rehash raw HTML during planning')
            return original(path)
        with patch.object(Path, 'read_bytes', guarded):
            self.assertEqual(planner.create_plan(self.args)['report.json']['first_fetch_jobs'], 0)
        row['cache_ref'] = str(self.args.queue)
        self.args.observations.write_text(encode(row) + '\n')
        with self.assertRaisesRegex(ValueError, 'outside_objects'):
            planner.create_plan(self.args)

    def test_malformed_duplicate_json_keys_and_catalog_ids_rejected(self):
        self.args.queue.write_text('{"queue":[],"queue":[]}')
        with self.assertRaisesRegex(ValueError, 'duplicate_json_key'):
            planner.create_plan(self.args)
        self.args.queue.write_text(encode(self.parts[0]))
        row = self.parts[1]['works'][0]
        (self.args.catalog / 'works.jsonl').write_text(encode(row) + '\n' + encode(row) + '\n')
        with self.assertRaisesRegex(planner.PlanError, 'catalog_identity_missing_or_duplicate'):
            planner.create_plan(self.args)

    def test_local_month_snapshot_provenance_is_not_claimed_current(self):
        snapshot = {'month': '2026-09', 'data_through': '2026-09-02', 'revision': 1}
        (self.args.monthly_dir / '2026-09.json').write_text(encode(snapshot))
        result = planner.create_plan(self.args)
        source = result['report.json']['monthpackage_sources'][-1]
        self.assertEqual(source['snapshot_data_through'], '2026-09-02')
        self.assertTrue(source['not_claimed_latest_selected'])
        self.assertRegex(source['packet_sha256'], '[0-9a-f]{64}')
        snapshot['data_through'] = '2026-09-30'
        (self.args.monthly_dir / '2026-09.json').write_text(encode(snapshot))
        with self.assertRaisesRegex(planner.PlanError, 'monthly_snapshot_after_plan_date'):
            planner.create_plan(self.args)


if __name__ == '__main__':
    unittest.main()
