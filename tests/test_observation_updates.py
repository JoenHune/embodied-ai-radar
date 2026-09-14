"""Official context updates remain observations, never paper-count inflation."""
import argparse
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_v3_catalog as builder
from catalog_enrichment import finalize_facts, ingest_delta
from catalog_store import fingerprint
from import_observation_updates import merge, normalize
from prepare_catalog import OBSERVATION_UPDATE_TYPES, SOURCE_TABLES, audit_source_reconciliation, reconcile
from test_catalog_rules import empty_payload

TYPES = ('strategic_partnership', 'research_explainer', 'deployment_update',
         'technology_deployment_update', 'code_release')
OBSERVED = '2026-09-14T01:00:00Z'
WORK_ID = 'arxiv:2605.00001'


def event(kind='research_explainer', number=1, *, linked=False):
    url = f'https://robot-lab.example/updates/{number}'
    return {'event_id': f'context:{number}', 'event_type': kind, 'title': f'Context update {number}',
            'summary_zh': '有明确原文和日期依据的上下文动态，不是新论文或模型。',
            'url': url, 'official_source_url': url, 'organization_id': 'org:fixture',
            'attribution_grade': 'G1', 'attribution_relation': 'official_source',
            'organization_evidence': [{'url': 'https://robot-lab.example/about', 'statement': '官方身份页。'}],
            'date_evidence': [{'url': url, 'statement': '页面日期。'}],
            'published_at': '2026-09-03', 'observed_at': OBSERVED, 'date_precision': 'day',
            'counts_as_new_paper': False, 'counts_as_new_model': False,
            'research_eligible': True, 'work_id': WORK_ID if linked else None,
            'limitations_zh': ['仅为上下文事件，不替代论文实验核验。']}


def six_updates(*, linked=False):
    # The reviewed release batch contains six records across five types;
    # two different code-release versions must remain two context events.
    return [event(kind, n, linked=linked) for n, kind in enumerate((*TYPES, 'code_release'), 1)]


def seed(root, rows, *, with_work=False):
    data = root / 'data'
    data.mkdir()
    config = root / 'config'
    config.mkdir()
    for name, field in SOURCE_TABLES:
        (data / (name + '.json')).write_text(json.dumps({field: []} if field else []))
    (config / 'taxonomy-v2.json').write_text(json.dumps({'categories': {'policy_learning': {'code': 'D1', 'label': 'Policy'}}}))
    (config / 'organizations.json').write_text(json.dumps({'organizations': [{'organization_id': 'org:fixture', 'name': 'Fixture Lab', 'tracking_unit': True}]}))
    (data / 'group-updates.json').write_text(json.dumps({'updates': rows}))
    if with_work:
        w = {'work_id': WORK_ID, 'title': 'Original robot policy', 'authors': ['Ada Researcher'],
             'arxiv_id': '2605.00001', 'first_public_date': '2026-05-01',
             'first_public_date_precision': 'day', 'primary_topic': 'policy_learning',
             'topics': ['policy_learning'], 'relevance': {'status': 'included', 'score': 3},
             'versions': [{'kind': 'preprint', 'url': 'https://arxiv.org/abs/2605.00001',
                           'date': '2026-05-01', 'status': 'preprint'}]}
        (data / 'works.json').write_text(json.dumps([w]))
        (data / 'work-organization-links.json').write_text(json.dumps({'links': [{
            'work_id': WORK_ID, 'organization_id': 'org:fixture', 'evidence_grade': 'G1',
            'evidence_url': 'https://robot-lab.example/publications'}]}))
    return data


def migrate(root, data):
    with patch.multiple(builder, ROOT=root, DATA=data):
        return builder.migrate_legacy(argparse.Namespace(as_of='2026-09-14'))


class ObservationUpdateTests(unittest.TestCase):
    def test_all_five_types_and_six_reviewed_events_are_explicitly_noncounting(self):
        self.assertEqual(OBSERVATION_UPDATE_TYPES, set(TYPES))
        rows = six_updates()
        before = copy.deepcopy(rows)
        normalized = normalize(rows)
        self.assertEqual(rows, before)
        self.assertEqual(len(normalized), 6)
        for row in normalized:
            self.assertEqual(row['evidence_layer'], 'S')
            self.assertFalse(row['research_eligible'])
            self.assertFalse(row['counts_as_new_paper'])
            self.assertFalse(row['counts_as_new_model'])
            self.assertEqual(row['published_at'], '2026-09-03')
            self.assertEqual(row['observed_at'], OBSERVED)

    def test_raw_import_is_idempotent_and_preserves_existing_records(self):
        raw = six_updates()
        old = {'update_id': 'old', 'url': 'https://robot-lab.example/older', 'title': 'Prior update'}
        existing = [old]
        once = merge(existing, raw)
        self.assertEqual(existing, [old])
        self.assertEqual(once, merge(once, raw))
        self.assertEqual(once[0], old)

    def test_normalizing_normalized_rows_preserves_original_eligibility_provenance(self):
        once = normalize(six_updates())
        self.assertEqual(normalize(once), once)

    def test_conflicting_reimport_requires_explicit_revision_without_mutation(self):
        existing = merge([], six_updates())
        before = copy.deepcopy(existing)
        changed = six_updates()
        changed[0]['summary_zh'] = 'Changed statement'
        with self.assertRaisesRegex(ValueError, 'explicit revision'):
            merge(existing, changed)
        self.assertEqual(existing, before)

    def test_duplicate_id_and_same_source_date_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unique event ID'):
            normalize([event(), event()])
        existing = merge([], [event()])
        other = event(number=2)
        other['url'] = existing[0]['url']
        with self.assertRaisesRegex(ValueError, 'Same source/date'):
            merge(existing, [other])

    def test_noncount_flags_identity_and_date_proofs_cannot_be_omitted(self):
        for change in [{'counts_as_new_paper': True}, {'counts_as_new_model': True},
                       {'counts_as_new_paper': 0}, {'event_type': 'model_release'},
                       {'attribution_grade': 'G2'}, {'organization_evidence': []},
                       {'date_evidence': []}, {'date_precision': 'year'},
                       {'published_at': '2026-10-01'}, {'url': 'file:///private/document'}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize([{**event(), **change}])

    def test_unlinked_contexts_never_create_canonical_works_or_manifestations(self):
        for kind in TYPES:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                data = seed(root, normalize([event(kind)]))
                payload = migrate(root, data)
                self.assertEqual(payload['works'], [])
                self.assertEqual(payload['manifestations'], [])
                payload = reconcile(payload, data, '2026-09-14')
                self.assertEqual(payload['works'], [])
                self.assertEqual(payload['manifestations'], [])
                self.assertEqual(payload['reconciliation'][0]['status'], 'event_only')
                final = finalize_facts(payload, '2026-09-14')
                self.assertEqual(len(final['evidence-events']), 1)
                self.assertEqual(final['evidence-events'][0]['evidence_layer'], 'S')
                self.assertFalse(final['evidence-events'][0]['research_eligible'])

    def test_linked_contexts_do_not_create_versions_or_move_original_date(self):
        for kind in TYPES:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                row = event(kind, linked=True)
                row['published_at'] = '2025-01-01'  # Must not backdate its 2026 paper.
                data = seed(root, normalize([row]), with_work=True)
                migrated = migrate(root, data)
                self.assertEqual(len(migrated['works']), 1)
                self.assertEqual(len(migrated['manifestations']), 1)
                final = finalize_facts(reconcile(migrated, data, '2026-09-14'), '2026-09-14')
                self.assertEqual(len(final['works']), 1)
                self.assertEqual(len(final['manifestations']), 1)
                self.assertEqual(final['works'][0]['first_public_date'], '2026-05-01')
                self.assertEqual(final['works'][0]['first_public_date_precision'], 'day')
                context = next(e for e in final['evidence-events'] if e['event_type'] == kind)
                self.assertEqual(context['work_id'], WORK_ID)
                self.assertEqual(context['published_at'], '2025-01-01')
                self.assertEqual(context['evidence_layer'], 'S')
                self.assertFalse(context['research_eligible'])
                self.assertEqual(final['works'][0]['relevance']['status'], 'included')
                # Source reconciliation can retain the explanation link without
                # turning that explanation into a publication manifestation.
                source_id = 'source:group-updates:' + fingerprint(normalize([row])[0])[:24]
                self.assertIn(source_id, final['works'][0]['source_record_ids'])

    def test_builder_preserves_explicit_noncount_markers_in_event_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = seed(root, normalize(six_updates()))
            events = migrate(root, data)['evidence-events']
            self.assertEqual(len(events), 6)
            for row in events:
                self.assertIs(row.get('counts_as_new_paper'), False)
                self.assertIs(row.get('counts_as_new_model'), False)

    def test_six_event_pipeline_reconciliation_and_finalize_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = seed(root, normalize(six_updates(linked=True)), with_work=True)
            first = finalize_facts(reconcile(migrate(root, data), data, '2026-09-14'), '2026-09-14')
            incoming = reconcile(migrate(root, data), data, '2026-09-14')
            second = finalize_facts(ingest_delta(copy.deepcopy(first), incoming), '2026-09-14')
            self.assertEqual({w['work_id'] for w in first['works']}, {w['work_id'] for w in second['works']})
            self.assertEqual({m['manifestation_id'] for m in first['manifestations']}, {m['manifestation_id'] for m in second['manifestations']})
            self.assertEqual({e['event_id'] for e in first['evidence-events']}, {e['event_id'] for e in second['evidence-events']})
            contexts = [e for e in second['evidence-events'] if e['event_type'] in OBSERVATION_UPDATE_TYPES]
            self.assertEqual(len(contexts), 6)
            self.assertTrue(all(e['evidence_layer'] == 'S' and not e['research_eligible'] for e in contexts))
            self.assertEqual(second['works'][0]['first_public_date'], '2026-05-01')
            audit = audit_source_reconciliation(data, second['source-records'], second['reconciliation'], {WORK_ID})
            self.assertEqual(audit['status'], 'ok')

    def test_cold_incremental_import_keeps_all_unlinked_context_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            normalized = normalize(six_updates())
            data = seed(root, normalized)
            incoming = reconcile(migrate(root, data), data, '2026-09-14')
            expected_sources = {'source:group-updates:' + fingerprint(row)[:24] for row in normalized}
            self.assertEqual({e['source_record_id'] for e in incoming['evidence-events']}, expected_sources)
            final = finalize_facts(ingest_delta(empty_payload(), incoming), '2026-09-14')
            self.assertEqual(final['works'], [])
            self.assertEqual(final['manifestations'], [])
            self.assertEqual(len(final['evidence-events']), 6)
            self.assertTrue(all(e['work_id'] is None and e['evidence_layer'] == 'S'
                                and not e['research_eligible'] for e in final['evidence-events']))
            self.assertEqual({e['source_record_id'] for e in final['evidence-events']}, expected_sources)
            self.assertEqual(audit_source_reconciliation(data, final['source-records'], final['reconciliation'], set())['status'], 'ok')

    def test_replay_recovers_dropped_unlinked_events_from_exact_owned_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = seed(root, normalize(six_updates()))
            incoming = reconcile(migrate(root, data), data, '2026-09-14')
            previous = copy.deepcopy(incoming)
            previous['evidence-events'] = []  # Model the previously dropped events.
            previous_sources = copy.deepcopy(previous['source-records'])
            repaired = finalize_facts(ingest_delta(previous, incoming), '2026-09-14')
            self.assertEqual(len(repaired['evidence-events']), 6)
            self.assertEqual(repaired['source-records'], previous_sources)
            self.assertEqual(repaired['works'], [])
            self.assertEqual(repaired['manifestations'], [])
            second = finalize_facts(ingest_delta(copy.deepcopy(repaired), incoming), '2026-09-14')
            self.assertEqual(second['evidence-events'], repaired['evidence-events'])

    def test_recovery_rejects_unverified_noncontext_or_unowned_source_events(self):
        for problem in ['unverified', 'noncontext', 'wrong_hash', 'missing_hash', 'unowned_source']:
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                data = seed(root, normalize([event()]))
                incoming = reconcile(migrate(root, data), data, '2026-09-14')
                previous = copy.deepcopy(incoming)
                previous['evidence-events'] = []
                if problem == 'unverified':
                    incoming['evidence-events'][0]['review_status'] = 'candidate'
                elif problem == 'noncontext':
                    incoming['evidence-events'][0]['evidence_layer'] = 'E'
                elif problem == 'wrong_hash':
                    previous['source-records'][0]['payload_hash'] = 'different-source-payload'
                elif problem == 'missing_hash':
                    previous['source-records'][0].pop('payload_hash')
                    incoming['source-records'][0].pop('payload_hash')
                else:
                    incoming['evidence-events'][0]['source_record_id'] = 'source:not-owned-or-registered'
                repaired = ingest_delta(previous, incoming)
                self.assertEqual(repaired['evidence-events'], [])
                self.assertEqual(repaired['works'], [])
                self.assertEqual(repaired['manifestations'], [])

    def test_existing_context_gets_only_missing_provenance_not_content_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = seed(root, normalize([event()]))
            incoming = reconcile(migrate(root, data), data, '2026-09-14')
            previous = copy.deepcopy(incoming)
            existing = previous['evidence-events'][0]
            fill = ('source_record_id', 'counts_as_new_paper', 'counts_as_new_model', 'original_research_eligible')
            for key in fill:
                existing.pop(key)
            existing.update(title='人工核对的标题', summary_zh='保留人工审阅说明', published_at='2026-09-02')
            repaired = ingest_delta(previous, incoming)
            saved = repaired['evidence-events'][0]
            for key in fill:
                self.assertEqual(saved[key], incoming['evidence-events'][0][key])
            self.assertEqual(saved['title'], '人工核对的标题')
            self.assertEqual(saved['summary_zh'], '保留人工审阅说明')
            self.assertEqual(saved['published_at'], '2026-09-02')
            self.assertEqual(len(repaired['evidence-events']), 1)

    def test_unverified_replay_does_not_enrich_existing_verified_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = seed(root, normalize([event()]))
            incoming = reconcile(migrate(root, data), data, '2026-09-14')
            previous = copy.deepcopy(incoming)
            previous['evidence-events'][0].pop('source_record_id')
            incoming['evidence-events'][0]['review_status'] = 'candidate'
            result = ingest_delta(previous, incoming)
            self.assertNotIn('source_record_id', result['evidence-events'][0])


if __name__ == '__main__':
    unittest.main()
