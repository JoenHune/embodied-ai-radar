import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_hardware_sources import Collector, PARSER_VERSION, assess_html, digest
from refresh_hardware_source_scans import scan, scan_registered, trusted_path, read_rows, PUBLIC_FIELDS


TARGET = {'work_id': 'arxiv:2407.02648', 'arxiv_id': '2407.02648', 'version': 'v1',
          'source_url': 'https://arxiv.org/html/2407.02648v1'}
STAMP = '2026-09-14T10:00:00Z'
DICTIONARY = {'schema_version': '1', 'version': '1', 'entries': [
    {'dictionary_id': 'model:franka-panda', 'name': 'Franka Panda', 'category': 'robot_arm',
     'identity_level': 'model_specified', 'aliases': ['Franka Panda'], 'hardware_ids': [],
     'source_urls': ['https://example.org/fixture']}]}


def seed(cache, observations, *, parser=PARSER_VERSION, stamp=STAMP, suffix='', **updates):
    phrase = 'Franka Panda robot manipulates objects. PRIVATE_UNMATCHED_BODY ' + suffix
    raw = ('<html><meta name="citation_arxiv_id" content="2407.02648v1"><article class="ltx_document">'
           '<div class="ltx_abstract">PRIVATE_ABSTRACT_GPU</div>'
           '<section id="S1"><h2>1 Methods</h2><p>' + phrase * 20 + '</p></section>'
           '<section id="S2"><h2>2 Experiments</h2><p>' + phrase * 20 + '</p></section>'
           '<section id="S3"><h2>3 Related Works</h2><p>PRIVATE_RELATED_GPU</p></section>'
           '</article></html>').encode()
    assessment, blocks = assess_html(raw, TARGET, TARGET['source_url'])
    if parser != PARSER_VERSION:
        blocks.insert(0, {'section_id': 'abstract', 'section_title': 'Abstract', 'text': 'PRIVATE_ABSTRACT_GPU'})
    body = '\n\n'.join(block['text'] for block in blocks).encode()
    objects = cache / 'objects'
    objects.mkdir(parents=True, exist_ok=True)
    raw_path, blocks_path = objects / (digest(raw) + '.html'), objects / (digest(raw) + '.' + parser + '.blocks.json')
    raw_path.write_bytes(raw)
    blocks_path.write_text(json.dumps(blocks))
    row = {**TARGET, **assessment, 'observed_at': stamp, 'effective_url': TARGET['source_url'], 'http_status': 200,
           'parser_version': parser, 'raw_sha256': digest(raw), 'text_sha256': digest(body),
           'cache_ref': str(raw_path), 'blocks_ref': str(blocks_path), 'body_cache_ref': str(objects / 'private-body.txt'),
           'observation_id': 'hardware-source:' + digest((stamp + parser + suffix).encode())[:32], **updates}
    with observations.open('a') as handle:
        handle.write(json.dumps(row) + '\n')
    return row


class RefreshHardwareSourceTests(unittest.TestCase):
    def test_registered_scan_uses_frozen_ids_and_never_changes_cache_or_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
            original = seed(cache, observations)
            scan(cache, observations, DICTIONARY, output)
            source_before = (output / 'source-observations.jsonl').read_bytes()
            seed(cache, observations, stamp='2026-09-14T11:00:00Z', suffix='NEW_UNPUBLISHED')
            private_before = observations.read_bytes()
            cache_before = {str(p.relative_to(cache)): p.read_bytes() for p in cache.rglob('*') if p.is_file()}
            changed = {**DICTIONARY, 'version': '2'}
            with (patch('refresh_hardware_source_scans.prepare_private_cache', side_effect=AssertionError('No reparse')),
                  patch('refresh_hardware_source_scans.atomic_write', side_effect=AssertionError('No cache write'))):
                result = scan_registered(cache, observations, changed, output)
            self.assertEqual(result['body_scanned'], 1)
            self.assertEqual(result['network_requests'], 0)
            self.assertEqual((output / 'source-observations.jsonl').read_bytes(), source_before)
            self.assertEqual(observations.read_bytes(), private_before)
            self.assertEqual({str(p.relative_to(cache)): p.read_bytes() for p in cache.rglob('*') if p.is_file()}, cache_before)
            current = read_rows(output / 'source-scans.jsonl')[-1]
            self.assertEqual(current['content_hash'], original['text_sha256'])
            scan_before = (output / 'source-scans.jsonl').read_bytes()
            scan_registered(cache, observations, changed, output)
            self.assertEqual((output / 'source-scans.jsonl').read_bytes(), scan_before)

    def test_registered_scan_tolerates_only_an_incomplete_final_private_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
            seed(cache, observations)
            scan(cache, observations, DICTIONARY, output)
            original = observations.read_bytes()
            observations.write_bytes(original + b'{"work_id": "new')
            result = scan_registered(cache, observations, DICTIONARY, output)
            self.assertTrue(result['incomplete_private_tail_ignored'])
            self.assertEqual(result['body_scanned'], 1)
            observations.write_bytes(original + b'{"work_id": "new\n')
            with self.assertRaisesRegex(ValueError, 'log_corrupt'):
                scan_registered(cache, observations, DICTIONARY, output)

    def test_registered_scan_keeps_historical_parser_and_transport_lineage_but_scans_latest(self):
        for updates in ({'parser': 'arxiv-html-body-v1'}, {'transport_returncode': 18}):
            with self.subTest(updates=updates), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
                seed(cache, observations, **updates)
                with patch('refresh_hardware_source_scans.utc_now', return_value='2026-09-14T11:00:00Z'):
                    scan(cache, observations, DICTIONARY, output)
                before = (output / 'source-observations.jsonl').read_bytes()
                with patch('refresh_hardware_source_scans.prepare_private_cache', side_effect=AssertionError('No reparse')):
                    result = scan_registered(cache, observations, {**DICTIONARY, 'version': '2'}, output)
                self.assertEqual(result['observations'], 2)
                self.assertEqual(result['body_scanned'], 1)
                self.assertEqual((output / 'source-observations.jsonl').read_bytes(), before)

    def test_registered_scan_missing_conflicting_or_mismatched_observation_fails_without_writes(self):
        for scenario in ('missing', 'conflict', 'mismatch', 'duplicate_public'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
                row = seed(cache, observations)
                scan(cache, observations, DICTIONARY, output)
                if scenario == 'missing':
                    observations.write_text('')
                elif scenario == 'conflict':
                    with observations.open('a') as handle:
                        handle.write(json.dumps({**row, 'text_sha256': 'changed'}) + '\n')
                else:
                    rows = read_rows(output / 'source-observations.jsonl')
                    if scenario == 'mismatch':
                        rows[0]['work_id'] = 'different-work'
                    else:
                        rows += rows
                    (output / 'source-observations.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
                before = {p.name: p.read_bytes() for p in output.iterdir()}
                with self.assertRaises(ValueError):
                    scan_registered(cache, observations, {**DICTIONARY, 'version': '2'}, output)
                self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, before)

    def test_registered_scan_refuses_reclassification_or_old_parser_without_doing_it(self):
        for values, error in (({'transport_complete': False}, 'transport_reclassification'),
                              ({'parser': 'arxiv-html-body-v1'}, 'parser_refresh')):
            with self.subTest(values=values), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
                row = seed(cache, observations, **values)
                output.mkdir()
                public = {key: value for key, value in row.items() if key in PUBLIC_FIELDS}
                (output / 'source-observations.jsonl').write_text(json.dumps(public)+'\n')
                with self.assertRaisesRegex(ValueError, error):
                    scan_registered(cache, observations, DICTIONARY, output)
                self.assertFalse((output / 'source-scans.jsonl').exists())

    def test_private_paths_reject_final_parent_and_broken_symlinks_before_resolve(self):
        with tempfile.TemporaryDirectory() as directory:
            root, cache = Path(directory), Path(directory) / 'cache'
            objects = cache / 'objects'
            objects.mkdir(parents=True)
            valid = objects / 'raw.html'
            valid.write_bytes(b'private')
            self.assertEqual(trusted_path(valid, cache), valid.resolve())
            outside = root / 'outside.html'
            outside.write_bytes(b'outside')
            for path in (outside, objects / '..' / '..' / 'outside.html'):
                with self.assertRaisesRegex(ValueError, 'outside_objects'):
                    trusted_path(path, cache)
            for name, destination in [('within.html', valid), ('outside.html', outside), ('broken.html', objects / 'missing')]:
                link = objects / name
                link.symlink_to(destination)
                with self.assertRaisesRegex(ValueError, 'is_symlink'):
                    trusted_path(link, cache)
            real = objects / 'real'
            real.mkdir()
            (real / 'raw.html').write_bytes(b'private')
            (objects / 'linked').symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'is_symlink'):
                trusted_path(objects / 'linked' / 'raw.html', cache)

    def test_scan_is_excerpt_free_idempotent_and_restores_current_parser_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
            row = seed(cache, observations)
            with patch.object(Collector, 'collect', side_effect=AssertionError('No network acquisition')):
                result = scan(cache, observations, DICTIONARY, output)
                before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
                with patch('refresh_hardware_source_scans.utc_now', return_value='2030-01-01T00:00:00Z'):
                    self.assertEqual(scan(cache, observations, DICTIONARY, output), result)
            self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})
            self.assertEqual(result['body_scanned'], 1)
            self.assertEqual(len(read_rows(observations)), 1)
            public = read_rows(output / 'source-observations.jsonl')[0]
            self.assertEqual(public['transport_verification'], 'legacy_unrecorded')
            self.assertNotIn('transport_returncode', public)
            self.assertEqual(public['status'], 'full_text_available')
            for name, (raw, _) in before.items():
                for secret in (str(root), 'PRIVATE_UNMATCHED_BODY', 'PRIVATE_ABSTRACT_GPU', 'PRIVATE_RELATED_GPU', 'cache_ref', 'blocks_ref', 'excerpt'):
                    self.assertNotIn(secret, raw.decode(), (name, secret))
            state = Collector(cache, observations).state_path(TARGET)
            self.assertEqual(json.loads(state.read_text())['observation_id'], row['observation_id'])

    def test_reparse_same_timestamp_is_idempotent_and_preserves_fetch_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
            prior = seed(cache, observations, parser='arxiv-html-body-v1')
            with patch.object(Collector, 'collect', side_effect=AssertionError('No network acquisition')):
                with patch('refresh_hardware_source_scans.utc_now', return_value=STAMP):
                    scan(cache, observations, DICTIONARY, output)
                    snapshot = observations.read_bytes()
                    scan(cache, observations, DICTIONARY, output)
            self.assertEqual(observations.read_bytes(), snapshot)
            rows = read_rows(observations)
            self.assertEqual(len(rows), 2)
            current = rows[-1]
            self.assertEqual(current['parser_version'], PARSER_VERSION)
            self.assertEqual(current['fetched_at'], prior['observed_at'])
            self.assertEqual(current['parent_observation_id'], prior['observation_id'])
            self.assertEqual(current['processing_basis'], 'cached_raw_reparse_no_network')
            self.assertEqual(current['raw_sha256'], prior['raw_sha256'])
            self.assertNotEqual(current['text_sha256'], prior['text_sha256'])
            self.assertNotIn('PRIVATE_ABSTRACT_GPU', Path(current['body_cache_ref']).read_text())
            self.assertEqual(read_rows(output / 'source-scans.jsonl')[0]['content_hash'], current['text_sha256'])

    def test_known_incomplete_cached_transfer_is_never_promoted_by_reparse(self):
        for parser in (PARSER_VERSION, 'arxiv-html-body-v1'):
            for marker in ({'transport_complete': False}, {'transport_truncated': True},
                           {'curl_exit_code': 18}, {'transport_returncode': 28}):
                with self.subTest(parser=parser, marker=marker), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
                    seed(cache, observations, parser=parser, **marker)
                    with patch('refresh_hardware_source_scans.utc_now', return_value=STAMP):
                        scan(cache, observations, DICTIONARY, output)
                        scan(cache, observations, DICTIONARY, output)
                    rows = read_rows(observations)
                    self.assertEqual(len(rows), 2)
                    self.assertEqual(rows[-1]['status'], 'partial_text')
                    self.assertIn('incomplete_transport', rows[-1]['error'])
                    self.assertEqual(read_rows(output / 'source-observations.jsonl')[-1]['transport_verification'], 'incomplete')

    def test_changed_dictionary_and_body_hash_append_scans_without_overwriting_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
            seed(cache, observations)
            first = scan(cache, observations, DICTIONARY, output)
            original = read_rows(output / 'source-scans.jsonl')[0]
            changed = {**DICTIONARY, 'version': '2'}
            second = scan(cache, observations, changed, output)
            self.assertNotEqual(first['dictionary_hash'], second['dictionary_hash'])
            self.assertEqual(len(read_rows(output / 'source-scans.jsonl')), 2)
            seed(cache, observations, stamp='2026-09-14T11:00:00Z', suffix='new content')
            scan(cache, observations, changed, output)
            rows = read_rows(output / 'source-scans.jsonl')
            self.assertEqual(len(rows), 3)
            self.assertIn(original, rows)
            self.assertEqual(len({row['content_hash'] for row in rows}), 2)
            scan(cache, observations, changed, output)
            self.assertEqual(read_rows(output / 'source-scans.jsonl'), rows)

    def test_missing_raw_still_downgrades_known_incomplete_and_corrects_resume_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
            prior = seed(cache, observations, cache_ref=None, transport_truncated=True, transport_verification='complete')
            state = Collector(cache, observations).state_path(TARGET)
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps(prior))
            with patch('refresh_hardware_source_scans.utc_now', return_value=STAMP):
                scan(cache, observations, DICTIONARY, output)
                scan(cache, observations, DICTIONARY, output)
            current = read_rows(observations)[-1]
            self.assertEqual(len(read_rows(observations)), 2)
            self.assertEqual(current['status'], 'partial_text')
            self.assertEqual(current['processing_basis'], 'cached_transport_reclassification_no_network')
            self.assertEqual(json.loads(state.read_text())['observation_id'], current['observation_id'])
            self.assertEqual(read_rows(output / 'source-observations.jsonl')[-1]['transport_verification'], 'incomplete')

    def test_hash_mismatch_and_untrusted_paths_fail_before_public_export(self):
        for scenario in ('raw', 'body', 'outside', 'symlink'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
                row = seed(cache, observations, parser='arxiv-html-body-v1' if scenario == 'raw' else PARSER_VERSION)
                if scenario == 'raw':
                    Path(row['cache_ref']).write_bytes(b'changed raw')
                elif scenario == 'body':
                    Path(row['blocks_ref']).write_text('[{"section_id":"S1","section_title":"Methods","text":"tampered"}]')
                else:
                    if scenario == 'outside':
                        row['blocks_ref'] = str(root / 'outside.json')
                        Path(row['blocks_ref']).write_text('[]')
                    else:
                        link = cache / 'objects' / 'link.blocks.json'
                        link.symlink_to(row['blocks_ref'])
                        row['blocks_ref'] = str(link)
                    observations.write_text(json.dumps(row) + '\n')
                with self.assertRaises(ValueError):
                    scan(cache, observations, DICTIONARY, output)
                self.assertFalse(output.exists())

    def test_failures_do_not_retry_and_public_error_does_not_claim_http_200_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, observations, output = root / 'cache', root / 'observations.jsonl', root / 'public'
            seed(cache, observations, parser='arxiv-html-body-v1', status='unavailable',
                 error='curl_transport_error:18 /PRIVATE_PATH', transport_returncode=18)
            with patch.object(Collector, 'collect', side_effect=AssertionError('No retry')):
                result = scan(cache, observations, DICTIONARY, output)
            self.assertEqual(len(read_rows(observations)), 1)
            self.assertEqual(result['body_scanned'], 0)
            public = read_rows(output / 'source-observations.jsonl')[0]
            self.assertEqual(public['error'], 'transport_or_identity_error')
            self.assertEqual(public['transport_verification'], 'incomplete')
            self.assertNotIn('PRIVATE_PATH', json.dumps(public))


if __name__ == '__main__':
    unittest.main()
