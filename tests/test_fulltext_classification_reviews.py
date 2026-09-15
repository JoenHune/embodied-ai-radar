"""Bounded AI classification review; synthetic receipts, no real data writes."""
import argparse
import copy
import hashlib
import json
import socket
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
from catalog_store import TABLES, fingerprint, encode, save_catalog, load_catalog
from catalog_enrichment import ingest_delta, finalize_facts, MANAGED_FIELDS
from fulltext_classification_reviews import (FIELDS, POINTER_FIELD, SOURCE_TYPE, REVIEW_VERSION,
    apply_classification_reviews, audit_classification_reviews, review_state, review_source_id,
    active_bindings, taxonomy_projection)
from import_fulltext_classification_reviews import import_file
from merge_reviewed_identities import merge_reviewed_identities
from source_content_conflicts import conflict_id_for
from source_review_clock import LEDGER_PATHS
import test_source_review_clock_integration as clock_fixtures
from test_sqlite_catalog_fidelity import database, restored
from sqlite_catalog_fidelity import build_catalog_fidelity, audit_catalog_fidelity

DATA_THROUGH = '2026-09-14'
CLOCK = '2026-09-15T00:20:00Z'


def fixture():
    prior = clock_fixtures.SourceReviewClockIntegrationTests()
    prior.setUp()
    payload = {key: copy.deepcopy(prior.catalog.get(key, [])) for key in TABLES}
    for item in payload['works']:
        item['relevance'].setdefault('classifier_version', '3.0')
        item['relevance'].setdefault('score', 1.0)
    for number, version in enumerate(payload['manifestations']):
        version.setdefault('manifestation_id', f'fixture:manifestation:{number}')
    work = payload['works'][0]
    work.update(primary_direction='D1', directions=['D1', 'D4'], questions=[],
                classification_state='low_confidence_review', first_public_date_precision='day',
                facets={'methods': ['planning_reasoning'], 'embodiments': ['robot_arm']},
                evidence_grade='E0', strict_peer_reviewed=False, curated=False)
    work['relevance'].update(status='candidate', score=1.0, classifier_version='3.0')
    work['_managed_field_hashes'] = {field: fingerprint(work.get(field)) for field in MANAGED_FIELDS}
    payload['taxonomy-assignments'] = taxonomy_projection(payload)
    receipt, observation = copy.deepcopy(prior.receipt), copy.deepcopy(prior.observation)
    text = payload['text-snapshots'][0]
    before = review_state(work)
    row = {'review_id': 'classification:test:r1', 'work_id': work['work_id'], 'reviewer_kind': 'AI',
        'reviewed_at': '2026-09-15T00:10:00Z', 'supersedes_review_id': None,
        'before': before, 'before_state_hash': fingerprint(before),
        'after': {**before, 'relevance.status': 'included', 'primary_direction': 'D2', 'directions': ['D2', 'D1'],
                  'questions': ['Q6'], 'classification_state': 'ai_fulltext_reviewed'},
        'proof': {'reading_id': receipt['reading_id'], 'receipt_sha256': fingerprint(receipt),
                  'version': receipt['version'], 'source_url': receipt['source_url'], 'raw_sha256': receipt['raw_sha256'],
                  'text_snapshot_id': text['snapshot_id'], 'text_snapshot_sha256': fingerprint(text)},
        'rationales': {field: {'reason_zh': '合成测试：依据已读原文判定研究范围和主要贡献，不代表真实论文判断。',
                        'locators': copy.deepcopy(receipt['findings_zh'][0]['locator_text_sha256'])} for field in FIELDS}}
    return payload, {'schema_version': '1', 'reviews': [row]}, [receipt], [observation]


def apply(parts, *, conflicts=None, **kwargs):
    return apply_classification_reviews(*parts, data_through=kwargs.get('data_through', DATA_THROUGH),
        source_review_as_of=kwargs.get('source_review_as_of', CLOCK), conflicts=conflicts or [])


class ClassificationReviewTests(unittest.TestCase):
    def setUp(self):
        self.parts = fixture()
        self.guard = patch.object(socket, 'socket', side_effect=AssertionError('No network'))
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def test_only_allowed_fields_change_and_machine_metadata_and_dates_stay(self):
        original = copy.deepcopy(self.parts)
        result = apply(self.parts)
        self.assertEqual(self.parts, original)
        before, after = self.parts[0]['works'][0], result['works'][0]
        self.assertEqual(review_state(after), self.parts[1]['reviews'][0]['after'])
        editable = set(FIELDS[1:]) | {'relevance', 'source_record_ids', POINTER_FIELD}
        self.assertEqual({k: v for k, v in before.items() if k not in editable},
                         {k: v for k, v in after.items() if k not in editable})
        self.assertEqual({k: v for k, v in before['relevance'].items() if k != 'status'},
                         {k: v for k, v in after['relevance'].items() if k != 'status'})
        self.assertEqual(after['_managed_field_hashes'], before['_managed_field_hashes'])
        self.assertEqual(len(result['source-records']), len(self.parts[0]['source-records']) + 1)
        self.assertEqual(len(result['field-provenance']), len(self.parts[0]['field-provenance']) + 5)

    def test_exact_rerun_noop_and_same_id_changed_payload_rejected(self):
        result = apply(self.parts)
        self.assertEqual(apply((result, *self.parts[1:])), result)
        doc = copy.deepcopy(self.parts[1]); doc['reviews'][0]['rationales']['directions']['reason_zh'] += '修改内容。'
        with self.assertRaisesRegex(ValueError, 'review_id_content_conflict'):
            apply((result, doc, *self.parts[2:]))

    def test_before_hash_and_before_state_drift_rejected(self):
        for change in ('hash', 'work'):
            parts = copy.deepcopy(self.parts)
            if change == 'hash': parts[1]['reviews'][0]['before_state_hash'] = 'a' * 64
            else: parts[0]['works'][0]['questions'] = ['Q1']
            with self.assertRaisesRegex(ValueError, 'before_state'):
                apply(parts)

    def test_forbidden_grade_date_score_and_unknown_fields_cannot_enter_patch(self):
        for field in ('evidence_grade', 'strict_peer_reviewed', 'first_public_date', 'relevance.score', 'facets', 'identifiers'):
            parts = copy.deepcopy(self.parts); parts[1]['reviews'][0]['after'][field] = 'injected'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'classification_state_fields_invalid'):
                apply(parts)

    def test_AI_only_complete_reasons_and_single_primary(self):
        mutations = [lambda r: r.update(reviewer_kind='human'),
                     lambda r: r['rationales'].pop('questions'),
                     lambda r: r['after'].update(primary_direction=None),
                     lambda r: r['after'].update(primary_direction='D3'),
                     lambda r: r['after'].update(directions=['D2', 'D2']),
                     lambda r: r['after'].update(classification_state='human_reviewed')]
        for mutation in mutations:
            parts = copy.deepcopy(self.parts); mutation(parts[1]['reviews'][0])
            with self.assertRaises(ValueError): apply(parts)

    def test_missing_other_work_version_raw_hash_receipt_hash_and_locators_fail(self):
        updates = [('reading_id', 'missing'), ('receipt_sha256', 'a' * 64), ('version', 'v2'),
                   ('raw_sha256', 'a' * 64), ('source_url', 'https://arxiv.org/html/2608.99999v1'),
                   ('source_url', 'https://foreign.test/html/2608.00404v1'),
                   ('text_snapshot_id', 'missing'), ('text_snapshot_sha256', 'b' * 64)]
        for key, value in updates:
            parts = copy.deepcopy(self.parts); parts[1]['reviews'][0]['proof'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): apply(parts)
        parts = copy.deepcopy(self.parts)
        parts[1]['reviews'][0]['rationales']['directions']['locators'] = {'unread': 'a' * 64}
        with self.assertRaisesRegex(ValueError, 'locator_not_bound'): apply(parts)

    def test_future_review_reading_and_version_public_date_are_separate(self):
        parts = copy.deepcopy(self.parts); parts[1]['reviews'][0]['reviewed_at'] = '2026-09-16T00:00:00Z'
        with self.assertRaisesRegex(ValueError, 'review_after_approved_clock'): apply(parts)
        parts = copy.deepcopy(self.parts); parts[1]['reviews'][0]['reviewed_at'] = '2026-09-15T00:01:00Z'
        with self.assertRaisesRegex(ValueError, 'review_precedes_reading'): apply(parts)
        with self.assertRaisesRegex(ValueError, 'version_not_public_by_catalog_cutoff'):
            apply(self.parts, data_through='2026-07-31')
        result = apply(self.parts)
        self.assertEqual(result['works'][0]['first_public_date'], self.parts[0]['works'][0]['first_public_date'])

    def test_open_source_hold_blocks_new_approval(self):
        payload, _, readings, _ = self.parts
        text, receipt = payload['text-snapshots'][0], readings[0]
        conflict = {'schema_version': '1', 'work_id': receipt['work_id'], 'version': 'v1',
            'detected_at': '2026-09-15T00:05:00Z', 'reviewer_kind': 'AI', 'issue_types': ['abstract_body_divergence'],
            'summary_zh': '合成来源冲突测试。', 'limitations_zh': ['不代表真实研究。'],
            'metadata_sources': [{'snapshot_id': text['snapshot_id'], 'content_digest': text['content_digest']}],
            'reading_sources': [{'reading_id': receipt['reading_id'], 'reading_digest': fingerprint(receipt)}],
            'status': 'open', 'resolution': None}
        conflict['conflict_id'] = conflict_id_for(conflict)
        with self.assertRaisesRegex(ValueError, 'unresolved_source_hold'): apply(self.parts, conflicts=[conflict])

    def test_explicit_supersession_and_replaying_old_decision_do_not_rollback(self):
        first = apply(self.parts)
        row = copy.deepcopy(self.parts[1]['reviews'][0])
        row.update(review_id='classification:test:r2', reviewed_at='2026-09-15T00:12:00Z',
                   supersedes_review_id=row['review_id'], before=review_state(first['works'][0]))
        row['before_state_hash'] = fingerprint(row['before']); row['after']['questions'] = []
        doc = {'schema_version': '1', 'reviews': [row]}
        second = apply((first, doc, *self.parts[2:]))
        self.assertEqual(second['works'][0]['questions'], [])
        self.assertEqual(apply((second, self.parts[1], *self.parts[2:])), second)
        self.assertEqual(len(active_bindings(second)[row['work_id']]['chain']), 2)
        bad = copy.deepcopy(doc); bad['reviews'][0]['supersedes_review_id'] = None
        with self.assertRaisesRegex(ValueError, 'explicit_active_supersession_required'):
            apply((first, bad, *self.parts[2:]))

    def test_drifted_manual_edit_is_not_silently_overwritten_on_replay_or_ingest(self):
        result = apply(self.parts); result['works'][0]['questions'] = ['Q10']
        with self.assertRaisesRegex(ValueError, 'active_review_result_drift'):
            apply((result, *self.parts[1:]))
        with self.assertRaisesRegex(ValueError, 'active_review_result_drift'):
            ingest_delta(result, {key: [] for key in TABLES})

    def test_unknown_work_alias_cannot_retarget_review(self):
        parts = copy.deepcopy(self.parts)
        wid = parts[0]['works'][0]['work_id']
        parts[0]['work-aliases'].append({'alias': 'arxiv:2608.99999', 'work_id': wid})
        parts[1]['reviews'][0]['work_id'] = 'arxiv:2608.99999'
        with self.assertRaisesRegex(ValueError, 'unknown_canonical_work_no_alias_transfer'): apply(parts)

    def test_another_existing_work_cannot_borrow_the_receipt(self):
        parts = copy.deepcopy(self.parts)
        other = copy.deepcopy(parts[0]['works'][0])
        other.update(work_id='arxiv:2608.99999', identifiers={'arxiv': '2608.99999'}, aliases=[])
        parts[0]['works'].append(other)
        parts[1]['reviews'][0]['work_id'] = other['work_id']
        with self.assertRaisesRegex(ValueError, 'reading_work_version_or_source_mismatch'): apply(parts)

    def test_two_ingest_finalize_rounds_protect_empty_and_confirmed_unchanged_values(self):
        parts = copy.deepcopy(self.parts)
        row = parts[1]['reviews'][0]
        row['after'].update(primary_direction='D1', directions=['D1', 'D4'], questions=[])
        result = apply(parts)
        before = review_state(result['works'][0])
        for number in range(2):
            incoming = {key: [] for key in TABLES}
            new_work = copy.deepcopy(parts[0]['works'][0]); new_work.update(primary_direction='D3', directions=['D3'], questions=['Q9'])
            sid = f'source:unseen:{number}'
            new_work['source_record_ids'] = [sid]
            incoming['works'] = [new_work]; incoming['source-records'] = [{'source_record_id': sid}]
            incoming['reconciliation'] = [{'source_record_id': sid, 'work_id': new_work['work_id']}]
            result = finalize_facts(ingest_delta(result, incoming), DATA_THROUGH)
            self.assertEqual(review_state(result['works'][0]), before)
            self.assertEqual(audit_classification_reviews(result, parts[2], parts[3], data_through=DATA_THROUGH,
                             source_review_as_of=CLOCK, conflicts=[])['status'], 'passed')

    def test_taxonomy_DQ_provenance_survives_finalize_without_AI_claim_on_facets(self):
        facet = next(row for row in self.parts[0]['taxonomy-assignments'] if row['axis'] == 'methods')
        facet['unrelated_provenance'] = {'note': 'Existing user-owned facet annotation', 'source_ids': ['old:source']}
        result = finalize_facts(apply(self.parts), DATA_THROUGH)
        self.assertIn(facet, result['taxonomy-assignments'])
        for row in result['taxonomy-assignments']:
            if row['work_id'] != self.parts[0]['works'][0]['work_id']:
                continue
            if row['axis'] in {'direction', 'question'}:
                self.assertEqual(row['classifier_version'], REVIEW_VERSION)
                self.assertEqual(row['reviewer_kind'], 'AI')
                self.assertEqual(row['source_record_ids'], [review_source_id('classification:test:r1')])
            else:
                self.assertEqual(row['classifier_version'], '3.0')
                self.assertEqual(row['confidence'], 'low_confidence_review')
                self.assertNotIn('reviewer_kind', row)

    def test_only_existing_derived_events_change_classification_not_dates_or_review_flags(self):
        parts = copy.deepcopy(self.parts); wid = parts[0]['works'][0]['work_id']
        parts[0]['evidence-events'] = [{'event_id': 'canonical', 'work_id': wid, 'source_type': 'official_peer_review',
            'event_type': 'accepted', 'published_at': '2026-08-01', 'date_precision': 'day', 'review_required': True,
            'review_reason': 'another unresolved source issue', 'research_eligible': False}]
        before = copy.deepcopy(parts[0]['evidence-events'][0]); after = apply(parts)['evidence-events'][0]
        self.assertTrue(after['research_eligible']); self.assertEqual(after['direction_codes'], ['D2', 'D1'])
        for key, value in before.items():
            if key != 'research_eligible': self.assertEqual(after[key], value)

    def test_identity_merge_refuses_active_review_on_target_or_old_work(self):
        result = apply(self.parts); wid = result['works'][0]['work_id']
        other = copy.deepcopy(self.parts[0]['works'][0]); other['work_id'] = 'arxiv:2608.99999'
        result['works'].append(other)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'identity-reviews.jsonl'
            for target in (wid, other['work_id']):
                p.write_text(encode({'review_id': 'merge:1', 'review_status': 'verified', 'canonical_work_id': target,
                                     'work_ids': [wid, other['work_id']]}) + '\n')
                with self.assertRaisesRegex(ValueError, 'classification review identity merge'):
                    merge_reviewed_identities(copy.deepcopy(result), Path(directory))

    def test_pointer_source_or_provenance_tampering_fails(self):
        first = apply(self.parts)
        mutations = [lambda p: p['works'][0][POINTER_FIELD]['locked_fields'].pop(),
                     lambda p: p['source-records'][-1].update(payload_hash='a' * 64),
                     lambda p: p['field-provenance'].pop(),
                     lambda p: p['source-records'][-1].update(source_type='official-proceedings'),
                     lambda p: p['source-records'][-1].update(published_at='2026-09-15'),
                     lambda p: p['works'][0]['source_record_ids'].remove(p['source-records'][-1]['source_record_id'])]
        for mutation in mutations:
            changed = copy.deepcopy(first); mutation(changed)
            with self.assertRaises(ValueError): active_bindings(changed)

    def test_preserved_machine_metadata_is_audited_not_just_advertised(self):
        first = apply(self.parts)
        for key, changed_value in [('score', 2.0), ('classifier_version', 'new-version')]:
            changed = copy.deepcopy(first)
            changed['works'][0]['relevance'][key] = changed_value
            with self.assertRaisesRegex(ValueError, 'machine_relevance_metadata_changed'):
                audit_classification_reviews(changed, self.parts[2], self.parts[3],
                    data_through=DATA_THROUGH, source_review_as_of=CLOCK, conflicts=[])
            changed = copy.deepcopy(first)
            next(r for r in changed['source-records'] if r.get('source_type') == SOURCE_TYPE)[
                'preserved_machine_relevance_metadata'][key] = changed_value
            with self.assertRaisesRegex(ValueError, 'machine_relevance_metadata_changed'):
                active_bindings(changed)

    def test_supersession_cannot_legitimize_prior_machine_score_or_version_edits(self):
        first = apply(self.parts)
        row = copy.deepcopy(self.parts[1]['reviews'][0])
        row.update(review_id='classification:test:r2', reviewed_at='2026-09-15T00:12:00Z',
                   supersedes_review_id=row['review_id'], before=review_state(first['works'][0]))
        row['before_state_hash'] = fingerprint(row['before'])
        for field, value in [('score', 3.0), ('classifier_version', '4.0')]:
            changed = copy.deepcopy(first); changed['works'][0]['relevance'][field] = value
            with self.assertRaisesRegex(ValueError, 'machine_relevance_metadata_changed'):
                apply((changed, {'schema_version': '1', 'reviews': [row]}, *self.parts[2:]))

    def test_SQLite_full_restore_keeps_review_provenance_pointer_and_extra_taxonomy(self):
        result = apply(self.parts)
        connection = database(result)
        self.addCleanup(connection.close)
        build_catalog_fidelity(connection, result)
        self.assertEqual(audit_catalog_fidelity(connection, result)['status'], 'passed')
        for table in ('works', 'source-records', 'field-provenance', 'taxonomy-assignments'):
            self.assertEqual(sorted(restored(connection, table), key=fingerprint), sorted(result[table], key=fingerprint))

    def test_duplicate_batch_is_rejected_without_mutating_input(self):
        parts = copy.deepcopy(self.parts); parts[1]['reviews'].append(copy.deepcopy(parts[1]['reviews'][0]))
        before = copy.deepcopy(parts)
        with self.assertRaisesRegex(ValueError, 'duplicate_input_review_id'): apply(parts)
        self.assertEqual(parts, before)

    def test_second_invalid_review_does_not_partially_apply_first(self):
        parts = copy.deepcopy(self.parts)
        bad = copy.deepcopy(parts[1]['reviews'][0]); bad['review_id'] = 'classification:bad-second'
        parts[1]['reviews'].append(bad)
        before = copy.deepcopy(parts)
        with self.assertRaisesRegex(ValueError, 'before_state_drift'): apply(parts)
        self.assertEqual(parts, before)

    def test_no_review_ingest_retains_legacy_source_dedup_behavior(self):
        payload = copy.deepcopy(self.parts[0])
        payload['source-records'].append(copy.deepcopy(payload['source-records'][0]))
        finalized = finalize_facts(payload, DATA_THROUGH)
        ids = [row['source_record_id'] for row in finalized['source-records']]
        self.assertEqual(len(ids), len(set(ids)))

    def test_active_review_allows_ordinary_ingest_sources_to_finalize_dedup(self):
        payload = apply(self.parts)
        payload['source-records'].append(copy.deepcopy(payload['source-records'][0]))
        result = finalize_facts(payload, DATA_THROUGH)
        self.assertEqual(audit_classification_reviews(result, self.parts[2], self.parts[3],
            data_through=DATA_THROUGH, source_review_as_of=CLOCK, conflicts=[])['status'], 'passed')
        source = next(r for r in result['source-records'] if r.get('source_type') == SOURCE_TYPE)
        result['source-records'].append(copy.deepcopy(source))
        with self.assertRaisesRegex(ValueError, 'duplicate_classification_source_record_id'):
            finalize_facts(result, DATA_THROUGH)


class ImportCliTests(unittest.TestCase):
    def test_dryrun_no_write_and_apply_approved_temp_catalog_only(self):
        payload, doc, readings, observations = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); catalog = root / 'data/catalog'
            save_catalog(catalog, payload, {'data_through': DATA_THROUGH})
            paths = {rel: root / rel for rel in LEDGER_PATHS}
            for path in paths.values(): path.parent.mkdir(parents=True, exist_ok=True); path.write_text('')
            reading_path = root / 'data/hardware-review/fulltext-readings.jsonl'
            observation_path = root / 'data/hardware-review/source-observations.jsonl'
            reading_path.write_text(''.join(encode(r) + '\n' for r in readings))
            observation_path.write_text(''.join(encode(r) + '\n' for r in observations))
            config = root / 'config/source-review-clock.json'; config.parent.mkdir()
            config.write_text(encode({'schema_version': '1', 'source_review_as_of': CLOCK,
                'ledger_sha256': {rel: hashlib.sha256(path.read_bytes()).hexdigest() for rel, path in paths.items()}}))
            source = root / 'review.json'; source.write_text(encode(doc))
            args = argparse.Namespace(input=source, catalog=catalog, readings=reading_path, observations=observation_path,
                conflicts=root / 'data/editorial/source-content-conflicts.jsonl', data_through=None,
                source_review_as_of=None, apply=False)
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            report = import_file(args)
            self.assertFalse(report['applied']); self.assertEqual(report['added_review_records'], 1)
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})
            args.apply = True
            self.assertTrue(import_file(args)['applied'])
            self.assertEqual(load_catalog(catalog)[0]['works'][0]['relevance']['status'], 'included')
            after = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.assertEqual(import_file(args)['added_review_records'], 0)
            self.assertEqual(after, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})
            args.source_review_as_of = '2026-09-15T00:21:00Z'
            with self.assertRaisesRegex(ValueError, 'apply_requires_approved_clock'): import_file(args)


if __name__ == '__main__':
    unittest.main()
