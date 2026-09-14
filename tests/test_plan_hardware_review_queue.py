import copy
import random
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from plan_hardware_review_queue import plan
from catalog_store import fingerprint


def work(number, *, direction='D1', status='included', arxiv=True, date='2026-01-01'):
    aid = f'2601.{number:05d}'
    return {'work_id': 'arxiv:' + aid if arxiv else f'doi:10.1234/{number}',
            'title': f'Hardware-agnostic research {number}', 'primary_direction': direction,
            'relevance': {'status': status}, 'first_public_date': date,
            'identifiers': {'arxiv': aid} if arxiv else {'doi': f'10.1234/{number}'}}


class HardwareReviewQueueTests(unittest.TestCase):
    def test_initial_batch_spans_directions_and_relevance_without_abstract_hits(self):
        works = [work(direction * 100 + offset, direction=f'D{direction}', date=f'2026-01-{offset + 1:02d}')
                 for direction in range(1, 16) for offset in range(8)]
        works += [work(2000 + index * 10 + offset, status=state)
                  for index, state in enumerate(('candidate', 'manual_review', 'excluded')) for offset in range(5)]
        works += [work(3000, arxiv=False), work(3001, arxiv=False, status='excluded')]
        payload = {'works': works}
        snapshot = copy.deepcopy(payload)
        result = plan(payload, per_direction=4, controls=2)
        self.assertEqual(result['catalog_work_count'], 137)
        self.assertEqual(result['arxiv_eligible_work_count'], 135)
        self.assertEqual(result['non_arxiv_work_count'], 2)
        self.assertEqual(len(result['queue']), 66)
        included = [row for row in result['queue'] if row['relevance_status'] == 'included']
        self.assertEqual(Counter(row['primary_direction'] for row in included), {f'D{i}': 4 for i in range(1, 16)})
        self.assertEqual([row['primary_direction'] for row in included[:15]], [f'D{i}' for i in range(1, 16)])
        for direction in range(1, 16):
            chosen = [row for row in included if row['primary_direction'] == f'D{direction}']
            self.assertEqual([row['first_public_date'] for row in chosen[:2]], ['2026-01-08', '2026-01-07'])
        self.assertEqual(Counter(row['relevance_status'] for row in result['queue']),
                         {'included': 60, 'candidate': 2, 'manual_review': 2, 'excluded': 2})
        self.assertEqual(payload, snapshot)
        self.assertNotIn('population_sample', result.get('queue_mode', ''))
        self.assertTrue(all('source_url' not in row for row in result['queue']))

    def test_plan_is_deterministic_under_catalog_order_and_duplicate_reviewed_ids(self):
        works = [work(i, direction=f'D{i % 3 + 1}') for i in range(30)]
        reviewed = [works[3]['work_id'], works[3]['work_id'], works[7]['work_id']]
        expected = plan({'works': works}, reviewed, per_direction=5, controls=1)
        random.Random(0).shuffle(works)
        self.assertEqual(plan({'works': works}, reversed(reviewed), per_direction=5, controls=1), expected)
        ids = [row['work_id'] for row in expected['queue']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(ids).isdisjoint(reviewed))
        self.assertEqual(expected['already_had_verified_usage'], 2)

    def test_unassigned_future_directions_and_other_relevance_states_get_samples(self):
        result = plan({'works': [work(1, direction=None), work(2, direction='D16'),
                                 work(3, status='new_state'), work(4, status='unknown'),
                                 work(5, arxiv=False)]}, per_direction=1, controls=1)
        self.assertEqual({row['work_id'] for row in result['queue']}, {'arxiv:2601.00001', 'arxiv:2601.00002',
                                                                    'arxiv:2601.00003', 'arxiv:2601.00004'})
        self.assertEqual(result['catalog_work_count'], 5)
        self.assertTrue(any('unassigned' in row['selection_reason'] for row in result['queue']))

    def test_all_arxiv_queue_is_exact_full_set_with_identical_stratified_prefix(self):
        works = [work(i, direction=f'D{i % 15 + 1}', status=('included', 'candidate', 'excluded', 'manual_review')[i % 4])
                 for i in range(150)]
        works += [work(1000, direction=None), work(1001, status='unknown'), work(1002, arxiv=False)]
        reviewed = [works[i]['work_id'] for i in range(0, 150, 10)]
        initial = plan({'works': works}, reviewed, per_direction=2, controls=2)
        complete = plan({'works': works}, reviewed, per_direction=2, controls=2, all_arxiv=True)
        self.assertEqual(complete['queue'][:len(initial['queue'])], initial['queue'])
        expected = {row['work_id'] for row in works if row['identifiers'].get('arxiv')}
        queued = [row['work_id'] for row in complete['queue']]
        self.assertEqual(set(queued), expected)
        self.assertEqual(len(queued), len(expected))
        self.assertTrue(set(reviewed).issubset(queued))
        self.assertEqual(complete['queue_mode'], 'all_arxiv')
        self.assertEqual(complete['catalog_work_count'], 153)
        self.assertEqual(complete['arxiv_eligible_work_count'], 152)
        self.assertEqual(complete['non_arxiv_work_count'], 1)
        self.assertTrue(all('source_url' not in row for row in complete['queue']))
        self.assertEqual(plan({'works': list(reversed(works))}, reviewed, per_direction=2, controls=2, all_arxiv=True), complete)

    def test_prior_usage_does_not_remove_work_from_all_arxiv_backlog(self):
        row = work(1)
        self.assertEqual(plan({'works': [row]}, [row['work_id']])['queue'], [])
        complete = plan({'works': [row]}, [row['work_id']], all_arxiv=True)
        self.assertEqual([r['work_id'] for r in complete['queue']], [row['work_id']])
        self.assertEqual(complete['queue'][0]['selection_reason'], 'full_arxiv_backlog')

    def test_v2_keeps_the_v1_stratified_prefix_byte_equivalent(self):
        works = [work(i, direction=f'D{i % 3 + 1}',
                      status=('included', 'included', 'candidate', 'manual_review', 'excluded')[i % 5],
                      date=f'2026-01-{i % 28 + 1:02d}') for i in range(45)]
        reviewed = [works[3]['work_id'], works[9]['work_id']]
        initial = plan({'works': works}, reviewed, per_direction=4, controls=2)
        # Captured from policy v1 before the full-tail ordering change.
        self.assertEqual(fingerprint(initial['queue']), '6933178785fe76ec36529b41828a1a5ec72714af03c308df2b39546d5ecafa57')
        complete = plan({'works': works}, reviewed, per_direction=4, controls=2, all_arxiv=True)
        self.assertEqual(complete['queue'][:len(initial['queue'])], initial['queue'])
        self.assertEqual(initial['policy_version'], '1')
        self.assertNotIn('full_tail_policy', initial)
        self.assertEqual(complete['policy_version'], '2')
        self.assertEqual(complete['stratified_prefix_count'], len(initial['queue']))
        self.assertEqual(complete['full_tail_count'], len(works) - len(initial['queue']))
        self.assertEqual(complete['full_tail_policy']['scope'], 'processing_order_not_quality_ranking')

    def test_full_tail_prioritizes_recent_included_then_review_candidate_and_other(self):
        works = [work(1, date='2024-01-01'), work(2, date='2026-09-14'),
                 work(3, status='manual_review', date='2026-09-15'),
                 work(4, status='candidate', date='2026-09-16'),
                 work(5, status='excluded', date='2026-09-17'),
                 work(6, status='unknown', date='2026-09-18'),
                 work(7, status='new_state', date='2026-09-19'),
                 work(8, status='manual_review', date='2025-01-01'),
                 work(9, date='2026-09-14')]
        # Force all arXiv records into the tail, including prior-reviewed work.
        result = plan({'works': works}, [works[1]['work_id']], per_direction=0, controls=0, all_arxiv=True)
        self.assertEqual([r['work_id'] for r in result['queue']],
                         [works[i - 1]['work_id'] for i in (2, 9, 1, 3, 8, 4, 7, 6, 5)])
        self.assertEqual({r['work_id'] for r in result['queue']}, {r['work_id'] for r in works})
        self.assertEqual(plan({'works': list(reversed(works))}, [works[1]['work_id']],
                              per_direction=0, controls=0, all_arxiv=True), result)

    def test_full_tail_unknown_dates_stay_last_and_are_never_filled_from_ids(self):
        works = [work(1, date=None), work(2, date=''), work(3, date='invalid'),
                 work(4, date='2026-99-99'), work(5, date='2024-01-01'),
                 work(6, date='2026-09-14'), work(7, status='manual_review', date=None),
                 work(8, status='manual_review', date='2020-01-01')]
        snapshot = copy.deepcopy(works)
        result = plan({'works': works}, per_direction=0, controls=0, all_arxiv=True)
        self.assertEqual([r['work_id'] for r in result['queue']],
                         [works[i - 1]['work_id'] for i in (6, 5, 1, 2, 3, 4, 8, 7)])
        self.assertEqual(works, snapshot)
        dates = {r['work_id']: r['first_public_date'] for r in result['queue']}
        self.assertEqual(dates, {r['work_id']: r['first_public_date'] for r in works})

    def test_duplicate_work_ids_and_invalid_limits_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_work_identity'):
            plan({'works': [work(1), work(1)]})
        for limit in (-1, 1.5, True):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ValueError, 'nonnegative_integers'):
                    plan({'works': [work(1)]}, per_direction=limit)
                with self.assertRaisesRegex(ValueError, 'nonnegative_integers'):
                    plan({'works': [work(1)]}, controls=limit)
        self.assertEqual(plan({'works': [work(1)]}, per_direction=0, controls=0)['queue'], [])
        self.assertEqual(len(plan({'works': [work(1)]}, per_direction=0, controls=0, all_arxiv=True)['queue']), 1)


if __name__ == '__main__':
    unittest.main()
