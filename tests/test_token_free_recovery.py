import contextlib
import fcntl
import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import recover_token_free_sources as recovery


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.catalog, self.cache, self.output = root / 'catalog', root / 'cache', root / 'output'
        self.catalog.mkdir()
        (self.cache / 'requests').mkdir(parents=True)
        self.now = time.time()
        self.works, self.sources = [], []
        self.source = self.add_source('2609.00001')

    def add_source(self, aid, **changes):
        wid = 'arxiv:' + aid
        self.works.append({'work_id': wid, 'identifiers': {'arxiv': aid}, 'title': aid,
                           'relevance': {'status': 'included'}, 'first_public_date': '2026-09-01'})
        source = {'work_id': wid, 'arxiv_id': aid, 'source_url': 'https://arxiv.org/html/' + aid + 'v1',
                  'version': 'v1', 'version_basis': 'canonical_explicit', 'status': 'unavailable',
                  'http_status': 503, 'parser_version': recovery.PARSER_VERSION, 'attempt': 1,
                  'next_retry_at': '2026-01-01T00:00:00Z', 'observed_at': '2025-12-31T00:00:00Z',
                  'observation_id': 'hardware-source:' + aid.replace('.', '')}
        source.update(changes)
        self.sources.append(source)
        self.save()
        return source

    def save(self):
        (self.catalog / 'works.jsonl').write_text(''.join(json.dumps(work) + '\n' for work in self.works))
        (self.cache / 'observations.jsonl').write_text(''.join(json.dumps(source) + '\n' for source in self.sources))
        for source in self.sources:
            recovery.request_path(self.cache, source).write_text(json.dumps(source))

    def plan(self, **kwargs):
        return recovery.plan_recovery(self.catalog, self.cache, now=self.now, **kwargs)[0]

    def apply(self, fetcher, **kwargs):
        kwargs.setdefault('resource_check', lambda: None)
        with contextlib.redirect_stdout(io.StringIO()):
            return recovery.apply_recovery(self.catalog, self.cache, self.output, fetcher=fetcher, **kwargs)

    @staticmethod
    def response(url, **kwargs):
        return {'effective_url': url, 'http_status': 503, 'headers': {'Retry-After': '7200'}, 'raw': b''}

    def test_default_plan_is_read_only_and_never_initializes_collector(self):
        before = {str(path): path.read_bytes() for path in self.temp_path().rglob('*') if path.is_file()}
        with patch.object(recovery, 'Collector', side_effect=AssertionError('network')):
            plan = self.plan()
        after = {str(path): path.read_bytes() for path in self.temp_path().rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(self.output.exists())
        self.assertEqual(plan['network_requests'], 0)
        self.assertEqual(plan['selected_count'], 1)

    def temp_path(self):
        return Path(self.temp.name)

    def test_latest_observation_deduplicates_and_old_failure_does_not_return(self):
        self.sources.append({**self.source, 'status': 'full_text_available', 'observed_at': '2026-01-02T00:00:00Z',
                             'observation_id': 'new-observation'})
        self.save()
        plan = self.plan()
        self.assertEqual(plan['total_observed_works'], 1)
        self.assertEqual(plan['failure_counts'], {'already_available': 1})
        self.assertEqual(plan['selected_count'], 0)

    def test_only_documented_transient_errors_are_eligible(self):
        cases = [({'http_status': 500}, True), ({'http_status': 502}, True),
                 ({'http_status': None, 'transport_returncode': 28}, True),
                 ({'http_status': 200, 'transport_returncode': 18}, True),
                 ({'http_status': 200, 'transport_returncode': 63}, False),
                 ({'http_status': 404}, False), ({'http_status': 401}, False),
                 ({'http_status': None, 'error': 'unclassified_error'}, False),
                 ({'resolution_error': 'no_canonical_arxiv_identity'}, False),
                 ({'status': 'identity_mismatch'}, False), ({'status': 'partial_text'}, False)]
        baseline = dict(self.source)
        for changes, eligible in cases:
            with self.subTest(changes=changes):
                self.source.clear()
                self.source.update(baseline, **changes)
                self.save()
                self.assertEqual(self.plan()['eligible_count'], int(eligible))

    def test_403_or_html_challenge_holds_all_recovery(self):
        for code in (403, 200):
            with self.subTest(code=code):
                if len(self.sources) == 1:
                    self.add_source('2609.00002', status='blocked', http_status=code)
                else:
                    self.sources[1]['http_status'] = code
                    self.save()
                plan = self.plan()
                self.assertEqual(plan['selected_count'], 0)
                self.assertEqual(plan['global_pause_reason'], 'access_block_requires_review')
                with patch.object(recovery, 'RecoveryCollector', side_effect=AssertionError('blocked')):
                    self.assertEqual(self.apply(self.response)['status'], 'nothing_eligible')

    def test_expired_429_selects_only_one_original_probe(self):
        self.add_source('2609.00002', status='blocked', http_status=429)
        self.add_source('2609.00003', status='blocked', http_status=429)
        plan = self.plan(limit=10)
        selected = [row for row in plan['queue'] if row['selected']]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['failure_kind'], 'rate_limited')
        self.assertTrue(plan['rate_limit_probe_only'])
        calls = []
        def fetch(url, **kwargs):
            calls.append(url)
            return self.response(url)
        self.apply(fetch)
        self.assertEqual(calls, [selected[0]['source_url']])

    def test_rate_limit_or_persistent_deadline_holds_entire_host(self):
        self.add_source('2609.00002', status='blocked', http_status=429, next_retry_at='2099-01-01T00:00:00Z')
        self.assertEqual(self.plan()['global_pause_reason'], 'global_cooldown')
        self.sources.pop()
        self.save()
        (self.cache / 'pacing.json').write_text(json.dumps({'next_request_at': self.now + 600}))
        self.assertEqual(self.plan()['selected_count'], 0)
        self.assertEqual(self.plan()['global_pause_reason'], 'global_cooldown')

    def test_missing_or_naive_retry_deadline_never_authorizes_retry(self):
        for value in (None, 'bad-date', '2026-01-01T00:00:00'):
            self.source['next_retry_at'] = value
            self.save()
            self.assertEqual(self.plan()['queue'][0]['reason'], 'retry_deadline_unknown')
        self.source.update(status='blocked', http_status=429)
        self.save()
        self.assertEqual(self.plan()['global_pause_reason'], 'rate_limit_deadline_unknown')

    def test_target_cooldown_does_not_block_unrelated_due_targets(self):
        self.source['next_retry_at'] = '2099-01-01T00:00:00Z'
        self.add_source('2609.00002')
        plan = self.plan()
        self.assertEqual(plan['selected_count'], 1)
        self.assertEqual(plan['reason_counts']['target_cooldown'], 1)

    def test_retry_attempts_are_bounded_and_unknown_history_requires_review(self):
        for attempt in (3, 7, 0, None, True):
            self.source['attempt'] = attempt
            self.save()
            self.assertEqual(self.plan()['selected_count'], 0)

    def test_request_state_must_match_observation_and_parser(self):
        path = recovery.request_path(self.cache, self.source)
        path.write_text(json.dumps({**self.source, 'attempt': 2}))
        self.assertEqual(self.plan()['queue'][0]['reason'], 'request_binding_changed')
        path.unlink()
        self.assertEqual(self.plan()['queue'][0]['reason'], 'request_state_unavailable')
        self.source['parser_version'] = 'old-parser'
        self.save()
        self.assertEqual(self.plan()['selected_count'], 0)

    def test_url_identity_version_or_unknown_catalog_requires_review(self):
        original = self.source['source_url']
        for url in ('https://example.com/html/2609.00001v1', 'https://arxiv.org/html/2609.11111v1',
                    original + '?alternate=1', 'http://arxiv.org/html/2609.00001v1',
                    'https://arxiv.org/html/2609.00001v2'):
            self.source['source_url'] = url
            self.save()
            self.assertEqual(self.plan()['queue'][0]['reason'], 'identity_review_required')
        self.source['source_url'] = original
        self.works = []
        self.save()
        self.assertEqual(self.plan()['selected_count'], 0)

    def test_unversioned_retry_keeps_exact_original_url(self):
        self.source.update(source_url='https://arxiv.org/html/2609.00001', version=None,
                           version_basis='resolve_from_official_html')
        self.save()
        urls = []
        def fetch(url, **kwargs):
            urls.append(url)
            return self.response(url)
        result = self.apply(fetch)
        self.assertEqual(urls, [self.source['source_url']])
        self.assertEqual(result['network_requests'], 1)

    def test_bounded_batch_prioritizes_included_and_recent_work(self):
        self.add_source('2609.00002')
        self.add_source('2609.00003')
        self.works[0]['relevance'] = 'excluded'
        self.works[2]['first_public_date'] = '2026-10-01'
        self.save()
        chosen = [row['work_id'] for row in self.plan(limit=1)['queue'] if row['selected']]
        self.assertEqual(chosen, ['arxiv:2609.00003'])
        for limit in (0, 201):
            with self.assertRaises(ValueError):
                self.plan(limit=limit)

    def test_apply_appends_observation_and_audit_preserving_authority_and_cooldown(self):
        before_catalog = (self.catalog / 'works.jsonl').read_bytes()
        before_log = (self.cache / 'observations.jsonl').read_bytes()
        result = self.apply(self.response)
        self.assertEqual(result['result']['attempted'], 1)
        self.assertEqual((self.catalog / 'works.jsonl').read_bytes(), before_catalog)
        self.assertTrue((self.cache / 'observations.jsonl').read_bytes().startswith(before_log))
        source = recovery.read_request(self.cache, self.source)
        self.assertEqual(source['attempt'], 2)
        self.assertGreater(recovery.timestamp(source['next_retry_at']), self.now + 7100)
        self.assertGreater(json.loads((self.cache / 'pacing.json').read_text())['next_request_at'], self.now + 7100)
        audit = json.loads(next((self.output / 'recovery-runs').glob('*.json')).read_text())
        self.assertEqual(audit['status'], 'completed')
        self.assertFalse(audit['authority_modified'])
        self.assertFalse((self.output / 'research.sqlite').exists())

    def test_changed_request_is_rejected_inside_collector_lock(self):
        original_run = recovery.RecoveryCollector.run
        def change_then_run(collector, targets, **kwargs):
            path = recovery.request_path(self.cache, self.source)
            path.write_text(json.dumps({**self.source, 'status': 'blocked', 'http_status': 403}))
            return original_run(collector, targets, **kwargs)
        with patch.object(recovery.RecoveryCollector, 'run', change_then_run):
            with self.assertRaisesRegex(ValueError, 'binding_changed'):
                self.apply(lambda *args, **kwargs: self.fail('Unexpected request'))
        audit = json.loads(next((self.output / 'recovery-runs').glob('*.json')).read_text())
        self.assertEqual(audit['status'], 'failed')

    def test_new_host_block_after_planning_stops_before_request(self):
        original_run = recovery.RecoveryCollector.run
        for code, message in ((403, 'access_block_requires_review'), (429, 'rate_limit_state_changed')):
            with self.subTest(code=code):
                self.sources = [self.source]
                self.works = [self.works[0]]
                self.save()
                def change_then_run(collector, targets, **kwargs):
                    self.add_source('2609.00002', status='blocked', http_status=code)
                    return original_run(collector, targets, **kwargs)
                with patch.object(recovery.RecoveryCollector, 'run', change_then_run):
                    with self.assertRaisesRegex(ValueError, message):
                        self.apply(lambda *args, **kwargs: self.fail('Unexpected request'))

    def test_existing_runner_and_collector_locks_are_respected(self):
        self.output.mkdir()
        with (self.output / 'runner.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, 'another_token_free_runner'):
                self.apply(lambda *args, **kwargs: self.fail('Unexpected request'))
        with (self.cache / 'collector.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            log = self.cache / 'observations.jsonl'
            log.write_bytes(log.read_bytes() + b'{"partial":')
            before = log.read_bytes()
            with self.assertRaisesRegex(RuntimeError, 'Another collector'):
                self.apply(lambda *args, **kwargs: self.fail('Unexpected request'))
            self.assertEqual(log.read_bytes(), before)
            self.assertEqual(list(self.cache.glob('observations.jsonl.interrupted-tail.*')), [])

    def test_first_429_stops_batch_and_preserves_retry_after(self):
        self.add_source('2609.00002')
        calls = []
        def fetch(url, **kwargs):
            calls.append(url)
            return {'effective_url': url, 'http_status': 429, 'headers': {'Retry-After': '3600'}, 'raw': b''}
        result = self.apply(fetch)
        self.assertEqual(result['result']['attempted'], 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.plan()['global_pause_reason'], 'global_cooldown')

    def test_new_server_backoff_releases_locks_without_waiting_or_next_request(self):
        self.add_source('2609.00002')
        calls = []
        def fetch(url, **kwargs):
            calls.append(url)
            return self.response(url)
        with patch.object(recovery.Collector, '_wait', wraps=None) as wait:
            result = self.apply(fetch)
        self.assertEqual(len(calls), 1)
        self.assertEqual(wait.call_count, 1)
        self.assertEqual(result['status'], 'paused_global_backoff')
        self.assertEqual(result['result']['attempted'], 1)
        audit = json.loads(next((self.output / 'recovery-runs').glob('*.json')).read_text())
        self.assertEqual(audit['status'], 'paused_global_backoff')
        for path in (self.output / 'runner.lock', self.cache / 'collector.lock'):
            with path.open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_batch_time_budget_stops_before_request(self):
        expected = {self.source['work_id']: self.source}
        collector = recovery.RecoveryCollector(self.cache, self.cache / 'observations.jsonl', interval=15,
                                              expected=expected, rate_limits={},
                                              fetcher=lambda *args, **kwargs: self.fail('Unexpected request'))
        target = {key: self.source.get(key) for key in recovery.TARGET_FIELDS}
        with patch.object(recovery.time, 'monotonic', side_effect=[0, recovery.MAX_RUN_SECONDS]):
            result = collector.run([target], limit=1, retry_failed=True)
        self.assertEqual(result['status'], 'paused_time_budget')
        self.assertEqual(result['attempted'], 0)

    def test_apply_requires_existing_runtime_guard_and_initial_pressure_writes_nothing(self):
        with self.assertRaisesRegex(ValueError, 'requires_deployed_radar_resource_guard'):
            recovery.apply_recovery(self.catalog, self.cache, self.output)
        self.assertFalse(self.output.exists())
        result = self.apply(lambda *args, **kwargs: self.fail('Unexpected request'), resource_check=lambda: 'logger_memory_reserve')
        self.assertEqual(result['status'], 'paused_resource_pressure')
        self.assertFalse(self.output.exists())

    def test_resource_pressure_between_requests_stops_batch(self):
        self.add_source('2609.00002')
        checks = iter([None, None, None, 'logger_memory_reserve'])
        result = self.apply(self.response, resource_check=lambda: next(checks))
        self.assertEqual(result['status'], 'paused_resource_pressure')
        self.assertEqual(result['result']['attempted'], 1)

    def test_dry_run_cli_does_not_create_runtime_directories(self):
        with patch.object(recovery, 'ROOT', self.temp_path()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(recovery.main([]), 0)
        self.assertFalse((self.temp_path() / '.research').exists())

    def test_cli_explicit_repository_and_summary_are_read_only(self):
        report = {'queue': [{'work_id': 'a', 'selected': True}, {'work_id': 'b', 'selected': False}],
                  'network_requests': 0}
        buffer = io.StringIO()
        with patch.object(recovery, 'plan_recovery', return_value=(report, {})) as planner, contextlib.redirect_stdout(buffer):
            recovery.main(['--repository', str(self.temp_path()), '--summary'])
        self.assertEqual(planner.call_args.args, (self.temp_path() / 'data/catalog', self.temp_path() / '.research/hardware-fulltext'))
        result = json.loads(buffer.getvalue())
        self.assertNotIn('queue', result)
        self.assertEqual(result['selected'], [{'work_id': 'a', 'selected': True}])


if __name__ == '__main__':
    unittest.main()
