import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect_group_sources as collector

NOW = datetime(2026, 10, 13, 4, 0, tzinfo=timezone.utc)
BEFORE = '2026-10-13T00:00:00+00:00'
PAGE = 'https://lab.example/publications'
PAPER = 'https://arxiv.org/abs/2610.00001'
BODY = ('<html><a href="' + PAPER + '">New robot paper</a></html>').encode()


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz else NOW.replace(tzinfo=None)


class GroupSourceFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        (self.root / 'data').mkdir()
        self.org = {'organization_id': 'org:test-lab', 'display_name': 'Test Lab', 'tier': 'T0',
                    'official_urls': {'publications': PAGE}}
        (self.root / 'config/organizations.json').write_text(json.dumps({'organizations': [self.org]}))
        self.sid = collector.source_id(self.org['organization_id'], 'publications', PAGE)
        self.state = self.root / 'data/group-source-status.json'
        self.candidates = self.root / 'data/group-update-candidates.json'
        self.raw = self.root / 'data/raw/organizations/test-lab' / (self.sid.removeprefix('source:') + '-2026-10-13.html')
        self.prior = {'source_id': self.sid, 'organization_id': self.org['organization_id'], 'kind': 'publications',
                      'url': PAGE, 'last_checked': BEFORE, 'last_success': BEFORE, 'consecutive_failures': 0,
                      'known_links': [PAPER], 'status': 'healthy'}

    def write_prior(self):
        self.state.write_text(json.dumps({'sources': [self.prior]}))

    def write_cache(self, body=BODY):
        self.raw.parent.mkdir(parents=True, exist_ok=True)
        self.raw.write_bytes(body)

    def run_collector(self, fetch=None, *args):
        replacements = {'ROOT': self.root, 'ORGS': self.root / 'config/organizations.json',
                        'STATE': self.state, 'CANDIDATES': self.candidates,
                        'RAW': self.root / 'data/raw/organizations', 'WORKS': self.root / 'data/works.json'}
        fetch = fetch or (lambda *args: self.fail('Unexpected network request'))
        with patch.multiple(collector, **replacements), patch.object(collector, 'read_table', return_value=[]), \
                patch.object(collector, 'datetime', FrozenDatetime), patch.object(collector, 'fetch', side_effect=fetch), \
                patch.object(sys, 'argv', ['collector', '--as-of', '2026-10-13', *args]), \
                contextlib.redirect_stdout(io.StringIO()):
            collector.main()
        return json.loads(self.state.read_text())['sources'][0] if self.state.exists() else None

    def test_cached_success_preserves_actual_network_times(self):
        self.write_prior()
        self.write_cache()
        row = self.run_collector()
        self.assertEqual(row['last_checked'], BEFORE)
        self.assertEqual(row['last_success'], BEFORE)
        self.assertEqual(row['last_processed_at'], NOW.isoformat())
        self.assertEqual(row['fetch_mode'], 'cache')
        self.assertEqual(row['status'], 'healthy')

    def test_cache_without_timestamp_history_does_not_invent_network_check(self):
        self.write_cache()
        row = self.run_collector()
        self.assertIsNone(row['last_checked'])
        self.assertIsNone(row['last_success'])
        self.assertEqual(row['fetch_mode'], 'cache')
        self.assertEqual(row['status'], 'partial')
        self.assertEqual(json.loads(self.candidates.read_text())['candidates'][0]['url'], PAPER)

    def test_cached_success_does_not_clear_previous_network_failure(self):
        self.write_cache()
        for failures, status in ((1, 'partial'), (2, 'stale')):
            with self.subTest(failures=failures):
                self.prior.update(consecutive_failures=failures, status=status,
                                  last_failure_date='2026-10-13', error='TimeoutError: prior failure')
                self.write_prior()
                row = self.run_collector()
                for key in ('last_checked', 'last_success', 'consecutive_failures', 'status',
                            'last_failure_date', 'error'):
                    self.assertEqual(row[key], self.prior[key])
                self.assertEqual(row['fetch_mode'], 'cache')
                self.assertNotEqual(row['parser_status'], 'partial')

    def test_cached_healthy_state_without_check_history_remains_partial(self):
        self.prior.update(last_checked=None, last_success=None)
        self.write_prior()
        self.write_cache()
        self.assertEqual(self.run_collector()['status'], 'partial')

    def test_actual_network_request_advances_check_and_success(self):
        self.write_prior()
        row = self.run_collector(lambda *_: (BODY, 'text/html'))
        self.assertEqual(row['last_checked'], NOW.isoformat())
        self.assertEqual(row['last_success'], NOW.isoformat())
        self.assertEqual(row['fetch_mode'], 'network')
        self.assertEqual(row['status'], 'healthy')

    def test_actual_network_success_clears_previous_failure(self):
        self.prior.update(consecutive_failures=2, status='stale', last_failure_date='2026-10-12',
                          error='TimeoutError: prior failure')
        self.write_prior()
        row = self.run_collector(lambda *_: (BODY, 'text/html'))
        self.assertEqual(row['status'], 'healthy')
        self.assertEqual(row['consecutive_failures'], 0)
        self.assertIsNone(row['last_failure_date'])
        self.assertIsNone(row['error'])
        self.assertEqual(row['last_success'], NOW.isoformat())

    def test_network_failure_updates_attempt_time_and_retains_previous_success(self):
        self.write_prior()
        def fail(*args):
            raise TimeoutError('fixture timeout')
        row = self.run_collector(fail)
        self.assertEqual(row['last_checked'], NOW.isoformat())
        self.assertEqual(row['last_success'], BEFORE)
        self.assertEqual(row['status'], 'partial')
        self.assertEqual(row['known_links'], [PAPER])

    def test_empty_ordinary_html_is_partial_and_preserves_historical_links(self):
        self.write_prior()
        for body in (b'<html></html>', b'<html><h1>Publications</h1></html>', b''):
            with self.subTest(body=body):
                self.write_cache(body)
                row = self.run_collector()
                self.assertEqual(row['parser_status'], 'partial')
                self.assertEqual(row['content_state'], 'no_verified_research_links')
                self.assertEqual(row['status'], 'partial')
                self.assertFalse(row['empty_verified'])
                self.assertEqual(row['known_links'], [PAPER])
                self.assertEqual(row['last_checked'], BEFORE)

    def test_fresh_empty_http_success_is_not_complete_source_coverage(self):
        row = self.run_collector(lambda *_: (b'<html></html>', 'text/html'))
        self.assertEqual(row['fetch_mode'], 'network')
        self.assertEqual(row['last_checked'], NOW.isoformat())
        self.assertEqual(row['status'], 'partial')
        self.assertEqual(row['parser_status'], 'partial')

    def test_explicit_verified_empty_result_is_not_reinterpreted_as_failure(self):
        self.write_prior()
        self.write_cache(b'<html></html>')
        verified = {'applicable': False, 'links': [], 'parser_status': 'not_applicable',
                    'content_state': 'verified_empty', 'empty_verified': True}
        with patch.object(collector, 'adapt_group_publications', return_value=verified):
            row = self.run_collector()
        self.assertTrue(row['empty_verified'])
        self.assertEqual(row['status'], 'healthy')

    def test_verified_empty_cache_without_network_history_remains_partial(self):
        self.write_cache(b'<html></html>')
        verified = {'applicable': False, 'links': [], 'parser_status': 'not_applicable',
                    'content_state': 'verified_empty', 'empty_verified': True}
        with patch.object(collector, 'adapt_group_publications', return_value=verified):
            row = self.run_collector()
        self.assertTrue(row['empty_verified'])
        self.assertEqual(row['status'], 'partial')
        self.assertIsNone(row['last_checked'])

    def test_dry_run_does_not_create_state_cache_or_candidates(self):
        before = {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.run_collector(None, '--dry-run')
        after = {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
