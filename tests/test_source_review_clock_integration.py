"""A later review watermark must not become a later research/publication date."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]

from catalog_store import fingerprint
from editorial_history import persist_evidence_packet
from editorial_readings import build_reading_index
from generate_v3_editorial import build_evidence_packet, editorial_input_digest
from source_content_conflicts import build_source_conflicts, conflict_id_for
from test_hardware_coverage_export import public_reading_fixture
from test_v3_editorial import version_fixture
from test_equipment_radar import fixture as equipment_fixture
from equipment_radar import build_equipment_bundle
from hardware_census import build_census
from test_hardware_census import dictionary_fixture
from source_review_clock import usage_visible


class SourceReviewClockIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.month, self.catalog = version_fixture()
        self.work = self.catalog['works'][0]
        # The small editor fixture omits archival proof fields; this integration
        # also exercises the stricter source-comparison validator.
        for snapshot in self.catalog['text-snapshots']:
            source = next(row for row in self.catalog['source-records']
                          if row['source_record_id'] == snapshot['source_record_id'])
            source.update(version=snapshot['version'], payload_hash=fingerprint(snapshot),
                          text_content_digest=fingerprint({key: snapshot[key] for key in ('title', 'abstract')}))
        self.receipt, self.observation = public_reading_fixture(self.work)
        self.receipt['observed_at'] = self.observation['observed_at'] = '2026-09-15T00:01:00Z'
        self.receipt['read_completed_at'] = '2026-09-15T00:02:00Z'

    def packet(self, cutoff, *, conflicts=None, receipt=None, observation=None):
        reading = self.receipt if receipt is None else receipt
        source = self.observation if observation is None else observation
        index = build_reading_index(self.catalog, [reading], [source], cutoff)
        return build_evidence_packet(self.month, self.catalog, reading_index=index,
                                     source_conflicts=conflicts, source_review_as_of=cutoff)

    def card(self, packet):
        return next(row for row in packet['evidence_cards'] if row['work_id'] == self.work['work_id'])

    def test_cross_day_review_changes_context_not_research_dates_counts_or_versions(self):
        before = copy.deepcopy((self.catalog, self.month, self.receipt, self.observation))
        old = self.packet('2026-09-14T23:59:59Z')
        before_completion = self.packet('2026-09-15T00:01:59Z')
        new = self.packet('2026-09-15T00:03:00Z')
        self.assertNotIn('reading_annotations', self.card(old))
        self.assertNotIn('reading_annotations', self.card(before_completion))
        annotation = self.card(new)['reading_annotations'][0]
        self.assertEqual(annotation['version'], 'v1')
        self.assertEqual(annotation['read_completed_at'], '2026-09-15T00:02:00Z')
        for key in ('month', 'evidence_as_of', 'facts', 'coverage', 'sampling', 'directions', 'questions'):
            self.assertEqual(old[key], new[key], key)
        self.assertNotIn('Future experiment', self.card(new)['abstract'])
        self.assertNotEqual(editorial_input_digest(old), editorial_input_digest(new))
        self.assertEqual(before, (self.catalog, self.month, self.receipt, self.observation))

    def test_newer_read_version_never_replaces_older_historical_version(self):
        receipt, observation = public_reading_fixture(self.work, 'v2')
        receipt['observed_at'] = observation['observed_at'] = '2026-09-15T00:01:00Z'
        receipt['read_completed_at'] = '2026-09-15T00:02:00Z'
        packet = self.packet('2026-09-15T00:03:00Z', receipt=receipt, observation=observation)
        self.assertNotIn('reading_annotations', self.card(packet))
        self.assertEqual(self.card(packet)['text_version'], 'v1')

    def test_clock_only_advance_preserves_logical_input_but_archives_exact_clock(self):
        first = self.packet('2026-09-15T00:03:00Z')
        second = self.packet('2026-09-15T00:04:00Z')
        logical = editorial_input_digest(first)
        self.assertEqual(logical, editorial_input_digest(second))
        self.assertNotEqual(fingerprint(first), fingerprint(second))
        with tempfile.TemporaryDirectory() as directory:
            a = persist_evidence_packet(Path(directory), first, logical)
            b = persist_evidence_packet(Path(directory), second, logical)
            self.assertEqual(a['input_digest'], b['input_digest'])
            self.assertNotEqual(a['packet_digest'], b['packet_digest'])
            self.assertNotEqual(a['path'], b['path'])

    def test_equipment_usage_clock_does_not_expose_later_same_day_records(self):
        payload, authority, manifest = equipment_fixture()
        original = copy.deepcopy((payload, authority))
        for row in authority['usage-evidence']:
            row['observed_at'] = '2026-09-15T00:04:00Z'
        approved = copy.deepcopy(authority)
        manifest.update(source_review_as_of='2026-09-15T00:03:00Z', source_review_clock_digest='a' * 64)
        early = build_equipment_bundle(payload, authority, manifest)
        self.assertEqual(early['index']['counts']['usage_links'], 0)
        manifest['source_review_as_of'] = '2026-09-15T00:04:00Z'
        later = build_equipment_bundle(payload, authority, manifest)
        self.assertGreater(later['index']['counts']['usage_links'], 0)
        self.assertEqual(early['index']['data_through'], later['index']['data_through'])
        self.assertEqual(early['index']['window'], later['index']['window'])
        self.assertEqual(payload, original[0])
        self.assertEqual(authority, approved)

    def test_acquisition_before_cutoff_does_not_backdate_later_usage_review(self):
        payload, authority, manifest = equipment_fixture()
        for row in authority['usage-evidence']:
            row.update(observed_at='2026-09-14T10:00:00Z', reviewed_at='2026-09-15T00:04:00Z')
        before = copy.deepcopy(authority)
        manifest.update(source_review_as_of='2026-09-15T00:03:00Z', source_review_clock_digest='a' * 64)
        self.assertEqual(build_equipment_bundle(payload, authority, manifest)['index']['counts']['usage_links'], 0)
        early = build_census(payload, authority, dictionary_fixture(), [], [], manifest['source_review_as_of'])
        self.assertEqual(early['summary']['all_works']['verified_usage_relationship_count'], 0)
        manifest['source_review_as_of'] = '2026-09-15T00:04:00Z'
        self.assertGreater(build_equipment_bundle(payload, authority, manifest)['index']['counts']['usage_links'], 0)
        later = build_census(payload, authority, dictionary_fixture(), [], [], manifest['source_review_as_of'])
        self.assertGreater(later['summary']['all_works']['verified_usage_relationship_count'], 0)
        self.assertEqual(authority, before)

    def test_bad_review_time_is_not_silently_ignored_for_future_acquisition(self):
        with self.assertRaises(ValueError):
            usage_visible({'observed_at': '2026-09-16T00:00:00Z', 'reviewed_at': 'bad-date'},
                          '2026-09-15T00:00:00Z')

    def test_newly_visible_source_hold_cannot_be_bypassed_by_new_reading(self):
        snapshot = self.catalog['text-snapshots'][0]
        row = {'schema_version': '1', 'work_id': self.work['work_id'], 'version': 'v1',
               'detected_at': '2026-09-15T00:04:00Z', 'reviewer_kind': 'AI',
               'issue_types': ['abstract_body_divergence'], 'summary_zh': '合成测试来源差异，等待复核。',
               'limitations_zh': ['测试不代表真实研究存在错误。'],
               'metadata_sources': [{'snapshot_id': snapshot['snapshot_id'], 'content_digest': snapshot['content_digest']}],
               'reading_sources': [{'reading_id': self.receipt['reading_id'], 'reading_digest': fingerprint(self.receipt)}],
               'status': 'open', 'resolution': None}
        row['conflict_id'] = conflict_id_for(row)
        before = build_source_conflicts([row], self.catalog, [self.receipt], [self.observation], '2026-09-15T00:03:00Z')
        after = build_source_conflicts([row], self.catalog, [self.receipt], [self.observation], '2026-09-15T00:04:00Z')
        self.assertEqual(before, [])
        self.assertEqual(after[0]['experimental_use'], 'hold')
        normal = self.packet('2026-09-15T00:03:00Z', conflicts=before)
        held = self.packet('2026-09-15T00:04:00Z', conflicts=after)
        self.assertIn('reading_annotations', self.card(normal))
        self.assertNotIn('reading_annotations', self.card(held))
        self.assertFalse(self.card(held)['experimental_text_available'])
        self.assertEqual(normal['facts'], held['facts'])
        self.assertNotEqual(editorial_input_digest(normal), editorial_input_digest(held))


if __name__ == '__main__':
    unittest.main()
