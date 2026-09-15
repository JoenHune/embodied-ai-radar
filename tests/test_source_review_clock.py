"""Offline temporary-ledger fixtures for the source-review visibility clock."""
import copy
import hashlib
import json
import os
import socket
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import source_review_clock as clock


class SourceReviewClockTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='review-clock-fixture-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config_path = self.root / 'config/source-review-clock.json'
        self.config_path.parent.mkdir()
        hashes = {}
        for relative in clock.LEDGER_PATHS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = b'{"synthetic_metadata":true}\n'
            path.write_bytes(raw)
            hashes[relative] = hashlib.sha256(raw).hexdigest()
        self.config = {'schema_version': '1', 'source_review_as_of': '2026-09-15T00:05:00.123456Z',
                       'ledger_sha256': hashes}
        guard = patch.object(socket, 'socket', side_effect=AssertionError('No network'))
        guard.start()
        self.addCleanup(guard.stop)

    def write_config(self, value=None):
        self.config_path.write_text(json.dumps(self.config if value is None else value, ensure_ascii=False))

    def resolve(self, **kwargs):
        return clock.resolve_source_review_clock(self.root, '2026-09-14', **kwargs)

    def files(self):
        return {str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.root.rglob('*') if path.is_file()}

    def test_missing_config_uses_fixed_utc_day_end_without_writes(self):
        before = self.files()
        result = self.resolve()
        self.assertEqual(result, {'source_review_as_of': '2026-09-14T23:59:59.999999Z',
                                 'source_review_clock_digest': None,
                                 'source_review_clock': {'schema_version': '1', 'basis': 'legacy_data_through', 'ledger_sha256': {}}})
        self.assertEqual(before, self.files())

    def test_config_binds_exact_eight_public_ledgers_and_preserves_inputs(self):
        self.write_config()
        before, original = self.files(), copy.deepcopy(self.config)
        result = self.resolve()
        self.assertEqual(result['source_review_as_of'], self.config['source_review_as_of'])
        canonical = json.dumps(self.config, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(result['source_review_clock_digest'], hashlib.sha256(canonical).hexdigest())
        self.assertEqual(result['source_review_clock']['ledger_sha256'], self.config['ledger_sha256'])
        self.assertEqual(result['source_review_clock']['basis'], 'configured_bound_ledger')
        self.assertEqual(len(clock.LEDGER_PATHS), 8)
        self.assertEqual(before, self.files())
        self.assertEqual(original, self.config)
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_config_digest_is_canonical_json_not_whitespace_or_key_order(self):
        self.write_config()
        first = self.resolve()
        other = dict(reversed(list(self.config.items())))
        other['ledger_sha256'] = dict(reversed(list(other['ledger_sha256'].items())))
        self.config_path.write_text(json.dumps(other, indent=2) + '\n')
        self.assertEqual(self.resolve(), first)

    def test_machine_date_timezone_and_future_ledger_values_do_not_supply_clock(self):
        class NoNow(datetime):
            @classmethod
            def now(cls, *args, **kwargs):
                raise AssertionError('No machine clock')
            @classmethod
            def today(cls):
                raise AssertionError('No machine date')
        relative = clock.LEDGER_PATHS[0]
        raw = b'{"observed_at":"2099-12-31T23:59:59Z"}\n'
        (self.root / relative).write_bytes(raw)
        self.config['ledger_sha256'][relative] = hashlib.sha256(raw).hexdigest()
        self.write_config()
        with patch.object(clock, 'datetime', NoNow), patch.dict(os.environ, {'TZ': 'Pacific/Honolulu'}):
            first = self.resolve()
        with patch.object(clock, 'datetime', NoNow), patch.dict(os.environ, {'TZ': 'Asia/Shanghai'}):
            self.assertEqual(self.resolve(), first)
        self.assertEqual(first['source_review_as_of'], self.config['source_review_as_of'])

    def test_all_bound_hash_mismatches_fail_without_legacy_fallback(self):
        self.write_config()
        for relative in clock.LEDGER_PATHS:
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                with self.assertRaisesRegex(ValueError, '^source_review_clock:ledger_hash_mismatch$'):
                    self.resolve()
                path.write_bytes(original)

    def test_missing_bound_file_and_missing_or_unknown_hash_keys_fail(self):
        self.write_config()
        (self.root / clock.LEDGER_PATHS[0]).unlink()
        with self.assertRaisesRegex(ValueError, 'bound_ledger_missing'): self.resolve()
        for key in (None, '.research/observations.jsonl', '/Users/private/source.jsonl',
                    '../data/secret.jsonl', 'data/unknown.jsonl', 'data/hardware-review/./source-scans.jsonl'):
            with self.subTest(key=key):
                value = copy.deepcopy(self.config)
                value['ledger_sha256'].pop(clock.LEDGER_PATHS[0])
                if key is not None: value['ledger_sha256'][key] = 'a' * 64
                self.write_config(value)
                with self.assertRaisesRegex(ValueError, 'ledger_path_set_invalid'): self.resolve()

    def test_invalid_schema_controls_dates_hashes_and_unknown_fields_fail(self):
        cases = [None, [], {'schema_version': '1'}, {**self.config, 'private_path': '/Users/secret'},
                 {**self.config, 'schema_version': 1}, {**self.config, 'source_review_as_of': None},
                 {**self.config, 'source_review_as_of': '2026-09-15'},
                 {**self.config, 'source_review_as_of': '2026-09-15T00:00:00+00:00'},
                 {**self.config, 'source_review_as_of': '2026-02-30T00:00:00Z'},
                 {**self.config, 'source_review_as_of': '2026-09-15T00:00:00Z\x00'}]
        for value in cases:
            with self.subTest(value=value):
                self.config_path.write_text(json.dumps(value))
                with self.assertRaises(clock.SourceReviewClockError): self.resolve()
        for bad in (None, 1, 'f' * 63, 'F' * 64, 'a' * 64 + '\n'):
            value = copy.deepcopy(self.config)
            value['ledger_sha256'][clock.LEDGER_PATHS[0]] = bad
            self.write_config(value)
            with self.assertRaisesRegex(ValueError, 'ledger_hash_invalid'): self.resolve()

    def test_duplicate_keys_nan_and_corrupt_json_are_rejected(self):
        self.write_config()
        raw = self.config_path.read_text()
        for changed in (raw.replace('"schema_version": "1"', '"schema_version": "1", "schema_version": "1"'),
                        raw.replace('"ledger_sha256": {', '"ledger_sha256": {"' + clock.LEDGER_PATHS[0] + '": "' + 'a' * 64 + '",'),
                        '{"source_review_as_of":NaN}', '{bad JSON'):
            self.config_path.write_text(changed)
            with self.assertRaises(clock.SourceReviewClockError): self.resolve()

    def test_symlink_config_ledger_parent_and_custom_root_are_rejected(self):
        self.write_config()
        target = self.root / 'config/real.json'
        self.config_path.rename(target)
        self.config_path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'unsafe'): self.resolve()
        self.config_path.unlink()
        target.rename(self.config_path)
        path = self.root / clock.LEDGER_PATHS[0]
        copy_path = self.root / 'separate.jsonl'
        path.rename(copy_path)
        path.symlink_to(copy_path)
        with self.assertRaisesRegex(ValueError, 'unsafe'): self.resolve()
        path.unlink()
        copy_path.rename(path)
        parent = path.parent
        alternate = parent.with_name('moved-review')
        parent.rename(alternate)
        parent.symlink_to(alternate, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe'): self.resolve()
        alias = self.root / 'alias-root'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            clock.resolve_source_review_clock(alias, '2026-09-14')

    def test_dangling_config_symlink_is_not_missing_configuration(self):
        self.config_path.symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'unsafe'): self.resolve()

    def test_explicit_config_override_is_root_config_scoped(self):
        self.write_config()
        alternate = self.root / 'config/alternate.json'
        self.config_path.rename(alternate)
        self.assertEqual(self.resolve(config_path=alternate)['source_review_as_of'], self.config['source_review_as_of'])
        for path in ('../secret.json', '.research/secret.json', '/etc/config.json', 'config/../secret.json',
                     'config/secret\x00.json', 'config/secret\x7f.json', 42):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'unsafe'):
                self.resolve(config_path=path)

    def test_explicit_missing_config_does_not_silently_use_legacy(self):
        with self.assertRaisesRegex(ValueError, 'explicit_config_missing'):
            self.resolve(config_path='config/typo.json')

    def test_oversized_or_nonregular_config_is_rejected(self):
        self.write_config()
        with patch.object(clock, 'MAX_CONFIG_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'not_bounded_regular_file'): self.resolve()
        self.config_path.unlink()
        self.config_path.mkdir()
        with self.assertRaisesRegex(ValueError, 'not_bounded_regular_file'): self.resolve()

    def test_manifest_clock_requires_complete_bound_pair_and_no_file_reads(self):
        base = {'data_through': '2026-09-14'}
        legacy = clock.manifest_source_review_clock(base)
        self.assertEqual(legacy['source_review_as_of'], '2026-09-14T23:59:59.999999Z')
        self.assertIsNone(legacy['source_review_clock_digest'])
        explicit = {**base, 'source_review_as_of': '2026-09-15T00:00:00Z', 'source_review_clock_digest': 'a' * 64}
        with patch.object(clock.os, 'open', side_effect=AssertionError('Manifest helper does not read config')):
            self.assertEqual(clock.manifest_source_review_clock(explicit), {key: explicit[key] for key in legacy})
            self.assertEqual(clock.manifest_source_review_clock({**base, **legacy}), legacy)
        for update in ({'source_review_as_of': explicit['source_review_as_of']}, {'source_review_clock_digest': 'a' * 64},
                       {'source_review_as_of': None, 'source_review_clock_digest': None},
                       {'source_review_as_of': explicit['source_review_as_of'], 'source_review_clock_digest': None},
                       {'source_review_as_of': '2026-09-15', 'source_review_clock_digest': 'a' * 64}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                clock.manifest_source_review_clock({**base, **update})

    def test_utc_cutoff_and_visibility_are_inclusive_exact_and_date_compatible(self):
        self.assertEqual(clock.utc_cutoff('2026-09-14'), datetime(2026,9,14,23,59,59,999999,tzinfo=timezone.utc))
        self.assertTrue(clock.visible('2026-09-14T23:59:59.999999Z', '2026-09-14'))
        self.assertFalse(clock.visible('2026-09-15T00:00:00Z', '2026-09-14'))
        self.assertTrue(clock.visible('2026-09-15T00:00:00.001Z', '2026-09-15T00:00:00.001Z'))
        self.assertFalse(clock.visible('2026-09-15T00:00:00.002Z', '2026-09-15T00:00:00.001Z'))
        for value in (None, 0, '2026-02-30', '2026-09', 'now', '2026-09-15T00:00:00', datetime(2026,9,15)):
            with self.subTest(value=value), self.assertRaises(ValueError): clock.utc_cutoff(value)


if __name__ == '__main__':
    unittest.main()
