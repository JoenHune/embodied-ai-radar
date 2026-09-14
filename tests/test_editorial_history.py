"""Offline temporary fixtures for immutable exact-packet/editorial history."""
import copy
import json
import os
import socket
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import editorial_history as history
from generate_v3_editorial import editorial_input_digest

MONTH = '2026-08'
STAMP = '2026-09-05T12:00:00Z'


def tree(root):
    return {str(path.relative_to(root)): (path.is_dir(), path.stat().st_mtime_ns,
                                        None if path.is_dir() else path.read_bytes())
            for path in [root, *root.rglob('*')]}


class EditorialHistoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='editorial-history-fixture-')
        self.addCleanup(temporary.cleanup)
        # Keep the standard macOS /var temp alias in the caller path: callers
        # need not rewrite OS-owned aliases, while custom links are forbidden.
        self.root = Path(temporary.name)
        self.output = self.root / 'editorial'
        self.packet = {'schema_version': '3', 'month': MONTH,
                       'facts': {'included': 1}, 'required_localization_ids': ['arxiv:2608.00001'],
                       'evidence_cards': [{'evidence_id': 'arxiv:2608.00001', 'title': 'Original source title',
                                           'abstract': 'Original source text.', 'localization_required': True,
                                           'title_zh': None, 'summary_zh': '', 'translation_context': None}]}
        self.input_digest = editorial_input_digest(self.packet)
        self.artifact = {'schema_version': '3', 'status': 'complete', 'month': MONTH,
                         'generated_at': STAMP, 'model': 'fixture-model', 'input_digest': self.input_digest,
                         'claims': [{'title': '完整保留判断', 'supporting_ids': ['arxiv:2608.00001']}],
                         'future_fields': {'large_integer': 9007199254740995, 'boolean': True, 'none': None,
                                           'array': [1.0, False, '☃'], 'pathlike_key': 'value'}}
        guard = patch.object(socket, 'socket', side_effect=AssertionError('Offline fixture; no network'))
        guard.start()
        self.addCleanup(guard.stop)

    def packet_reference(self, packet=None):
        return history.persist_evidence_packet(self.output, self.packet if packet is None else packet, self.input_digest)

    def bound_artifact(self):
        return {**copy.deepcopy(self.artifact), 'evidence_packet_ref': self.packet_reference()}

    def archived_path(self, artifact):
        return self.output / 'monthly-history' / artifact['month'] / (history.digest(artifact) + '.json')

    def test_persist_exact_packet_with_relative_reference_without_mutation(self):
        before = copy.deepcopy(self.packet)
        reference = self.packet_reference()
        self.assertEqual(set(reference), {'input_digest', 'packet_digest', 'path'})
        expected = 'evidence-packets/' + self.input_digest + '/' + history.digest(self.packet) + '.json'
        self.assertEqual(reference['path'], expected)
        self.assertFalse(Path(reference['path']).is_absolute())
        self.assertEqual(json.loads((self.output / expected).read_bytes()), before)
        self.assertEqual(self.packet, before)

    def test_identical_packet_and_changed_key_order_are_idempotent(self):
        first = self.packet_reference()
        before = tree(self.root)
        reversed_packet = dict(reversed(list(self.packet.items())))
        self.assertEqual(self.packet_reference(reversed_packet), first)
        self.assertEqual(tree(self.root), before)

    def test_translation_cache_variants_share_input_but_keep_both_exact_packets(self):
        first = self.packet_reference()
        translated = copy.deepcopy(self.packet)
        translated['required_localization_ids'] = []
        translated['evidence_cards'][0].update(localization_required=False, title_zh='原始标题',
                                              summary_zh='已有中文摘要', translation_context={'status': 'current'})
        self.assertEqual(editorial_input_digest(translated), self.input_digest)
        second = self.packet_reference(translated)
        self.assertNotEqual(first['packet_digest'], second['packet_digest'])
        self.assertEqual(Path(first['path']).parent, Path(second['path']).parent)
        self.assertEqual(json.loads((self.output / first['path']).read_bytes()), self.packet)
        self.assertEqual(json.loads((self.output / second['path']).read_bytes()), translated)
        self.assertEqual(len(list((self.output / 'evidence-packets' / self.input_digest).glob('*.json'))), 2)

    def test_wrong_logical_input_digest_fails_before_creating_output(self):
        with self.assertRaisesRegex(ValueError, 'input_digest_mismatch'):
            history.persist_evidence_packet(self.output, self.packet, '0' * 64)
        self.assertFalse(self.output.exists())

    def test_invalid_json_values_are_not_silently_coerced(self):
        for bad in ({1: 'integer key'}, {'bad': (1, 2)}, {'bad': float('nan')}, {'bad': float('inf')}):
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                history.persist_evidence_packet(self.output, bad, self.input_digest)
        self.assertFalse(self.output.exists())

    def test_packet_collision_never_overwrites_corrupt_existing_file(self):
        reference = self.packet_reference()
        path = self.output / reference['path']
        path.write_text('{"tampered":true}')
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'immutable_content_conflict'):
            self.packet_reference()
        self.assertEqual(tree(self.root), before)

    def test_atomic_publish_failure_leaves_no_partial_archive_or_temp(self):
        before = copy.deepcopy(self.artifact)
        with patch.object(history.os, 'link', side_effect=OSError('PRIVATE/path failure')):
            with self.assertRaisesRegex(ValueError, '^editorial_history_write_failed$'):
                history.archive_editorial(self.output, self.artifact)
        self.assertFalse(self.archived_path(self.artifact).exists())
        self.assertFalse(list(self.output.rglob('*.tmp')))
        self.assertEqual(self.artifact, before)

    def test_new_archive_failure_cannot_replace_or_modify_an_older_valid_archive(self):
        history.archive_editorial(self.output, self.artifact)
        old = self.archived_path(self.artifact)
        before = (old.read_bytes(), old.stat().st_mtime_ns)
        newer = {**copy.deepcopy(self.artifact), 'generated_at': '2026-09-06T12:00:00Z', 'model': 'new-fixture-model'}
        with patch.object(history.os, 'link', side_effect=OSError('simulated publish failure')):
            with self.assertRaisesRegex(ValueError, 'editorial_history_write_failed'):
                history.archive_editorial(self.output, newer)
        self.assertEqual((old.read_bytes(), old.stat().st_mtime_ns), before)
        self.assertFalse(self.archived_path(newer).exists())
        self.assertEqual(len(history.load_editorial_history(self.output, MONTH)), 1)

    def test_concurrent_identical_publish_is_atomic_and_idempotent(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            references = list(pool.map(lambda _: self.packet_reference(), range(6)))
        self.assertTrue(all(reference == references[0] for reference in references))
        self.assertEqual(len(list(self.output.rglob('*.json'))), 1)
        self.assertFalse(list(self.output.rglob('*.tmp')))

    def test_losing_publisher_reads_while_winner_unlinks_its_temporary_hardlink(self):
        # Both publishers first observe no destination. The loser then reads
        # the published inode across the winner's final hardlink cleanup.
        ready_to_link = threading.Barrier(2)
        published = threading.Event()
        read_started = threading.Event()
        cleanup_done = threading.Event()
        roles_lock = threading.Lock()
        local = threading.local()
        assigned = []
        observed = {}
        real_link, real_unlink, real_read = os.link, os.unlink, os.read

        def publish(source, target, **kwargs):
            with roles_lock:
                local.winner = not assigned
                assigned.append(source)
            local.temporary = source
            ready_to_link.wait(timeout=5)
            if local.winner:
                result = real_link(source, target, **kwargs)
                published.set()
                return result
            self.assertTrue(published.wait(timeout=5))
            return real_link(source, target, **kwargs)  # FileExistsError.

        def cleanup(name, **kwargs):
            if getattr(local, 'winner', False) and name == local.temporary:
                self.assertTrue(read_started.wait(timeout=5))
                try:
                    return real_unlink(name, **kwargs)
                finally:
                    cleanup_done.set()
            return real_unlink(name, **kwargs)

        def read(descriptor, size):
            result = real_read(descriptor, size)
            if getattr(local, 'winner', None) is False and not read_started.is_set():
                observed['before'] = os.fstat(descriptor)
                read_started.set()
                self.assertTrue(cleanup_done.wait(timeout=5))
                observed['after'] = os.fstat(descriptor)
            return result

        with (patch.object(history.os, 'link', side_effect=publish),
              patch.object(history.os, 'unlink', side_effect=cleanup),
              patch.object(history.os, 'read', side_effect=read),
              ThreadPoolExecutor(max_workers=2) as pool):
            references = list(pool.map(lambda _: self.packet_reference(), range(2)))
        self.assertEqual(references[0], references[1])
        self.assertEqual((observed['before'].st_nlink, observed['after'].st_nlink), (2, 1))
        self.assertEqual(observed['before'].st_mtime_ns, observed['after'].st_mtime_ns)
        self.assertEqual(json.loads((self.output / references[0]['path']).read_bytes()), self.packet)
        self.assertFalse(list(self.output.rglob('*.tmp')))

    def _read_fixture_with_interleaving(self, after_read, *, linked=False):
        path = self.root / 'read-fixture.json'
        path.write_bytes(b'{"value":"old"}')
        temporary = self.root / 'publisher-temporary'
        if linked:
            os.link(path, temporary)
        before = path.stat()
        directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        real_read = os.read
        descriptors = []

        def read(descriptor, size):
            result = real_read(descriptor, size)
            descriptors.append(descriptor)
            after_read(len(descriptors), path, temporary, before)
            return result

        try:
            with patch.object(history.os, 'read', side_effect=read):
                result = history._read_at(directory, path.name)
            return result, descriptors
        finally:
            os.close(directory)

    def test_unchanged_file_uses_one_read_and_publish_cleanup_uses_one_same_fd_verification(self):
        def cleanup(call, path, temporary, before):
            if call == 1:
                temporary.unlink()
        raw, descriptors = self._read_fixture_with_interleaving(cleanup, linked=True)
        self.assertEqual(raw, b'{"value":"old"}')
        self.assertEqual(len(descriptors), 2)
        self.assertEqual(descriptors[0], descriptors[1])
        # Once the temporary name is gone, the ordinary read needs no retry.
        raw, descriptors = self._read_fixture_with_interleaving(lambda *_: None)
        self.assertEqual(raw, b'{"value":"old"}')
        self.assertEqual(len(descriptors), 1)

    def test_actual_same_size_content_change_is_not_retried(self):
        calls = []
        def change(call, path, temporary, before):
            calls.append(call)
            if call == 1:
                path.write_bytes(b'{"value":"new"}')
                # An explicit distinct mtime avoids filesystem-clock timing
                # assumptions; this is an actual byte mutation, not fake stat.
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
        with self.assertRaisesRegex(ValueError, '^editorial_history_file_changed_during_read$'):
            self._read_fixture_with_interleaving(change)
        self.assertEqual(calls, [1])

    def test_link_cleanup_cannot_mask_changed_bytes_even_with_restored_mtime(self):
        calls = []
        def change_and_cleanup(call, path, temporary, before):
            calls.append(call)
            if call == 1:
                path.write_bytes(b'{"value":"new"}')
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                temporary.unlink()
                self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
                self.assertEqual(path.stat().st_nlink, 1)
        with self.assertRaisesRegex(ValueError, '^editorial_history_file_changed_during_read$'):
            self._read_fixture_with_interleaving(change_and_cleanup, linked=True)
        # The metadata-only exception was considered, but byte verification
        # rejected it; there must not be a third attempt that accepts new data.
        self.assertEqual(calls, [1, 2])

    def test_second_pass_content_change_fails_instead_of_waiting_for_stability(self):
        calls = []
        def change_during_verification(call, path, temporary, before):
            calls.append(call)
            if call == 1:
                temporary.unlink()
            elif call == 2:
                path.write_bytes(b'{"value":"new"}')
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
        with self.assertRaisesRegex(ValueError, '^editorial_history_file_changed_during_read$'):
            self._read_fixture_with_interleaving(change_during_verification, linked=True)
        self.assertEqual(calls, [1, 2])

    def test_destination_unlink_or_replacement_is_not_temporary_link_cleanup(self):
        for replacement in (False, True):
            with self.subTest(replacement=replacement):
                def remove_destination(call, path, temporary, before):
                    if call == 1:
                        path.unlink()  # Same 2->1 shape, but the wrong name.
                        if replacement:
                            path.write_bytes(b'{"value":"new"}')
                with self.assertRaisesRegex(ValueError, '^editorial_history_file_changed_during_read$'):
                    self._read_fixture_with_interleaving(remove_destination, linked=True)
                (self.root / 'publisher-temporary').unlink()

    def test_ctime_only_change_without_publication_cleanup_is_rejected(self):
        calls = []
        def touch_metadata(call, path, temporary, before):
            calls.append(call)
            if call == 1:
                os.chmod(path, 0o600)
                os.chmod(path, before.st_mode & 0o7777)
                self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
                self.assertNotEqual(path.stat().st_ctime_ns, before.st_ctime_ns)
        with self.assertRaisesRegex(ValueError, '^editorial_history_file_changed_during_read$'):
            self._read_fixture_with_interleaving(touch_metadata)
        self.assertEqual(calls, [1])

    def test_other_link_count_changes_are_not_publication_cleanup(self):
        for mutation in ('add_link', 'unlink_last_name'):
            with self.subTest(mutation=mutation):
                def mutate(call, path, temporary, before):
                    if call == 1:
                        if mutation == 'add_link':
                            os.link(path, temporary)
                        else:
                            path.unlink()
                with self.assertRaisesRegex(ValueError, '^editorial_history_file_changed_during_read$'):
                    self._read_fixture_with_interleaving(mutate)
                temporary = self.root / 'publisher-temporary'
                if temporary.exists():
                    temporary.unlink()

    def test_archive_preserves_all_fields_and_returns_exact_six_field_reference(self):
        artifact = self.bound_artifact()
        before = copy.deepcopy(artifact)
        reference = history.archive_editorial(self.output, artifact)
        self.assertEqual(set(reference), {'artifact_digest', 'generated_at', 'model', 'input_digest', 'archive_url', 'input_packet_status'})
        self.assertEqual(reference['input_packet_status'], 'available')
        self.assertEqual(reference['archive_url'], '/api/v1/editorial-history/' + MONTH + '/' + history.digest(artifact) + '.json')
        self.assertEqual(json.loads(self.archived_path(artifact).read_bytes()), artifact)
        self.assertEqual(artifact, before)
        self.assertNotIn('artifact_digest', artifact)
        self.assertNotIn('archive_url', artifact)
        self.assertNotIn(str(self.output), json.dumps(reference))

    def test_identical_archival_preserves_mtime_and_never_duplicates_records(self):
        artifact = self.bound_artifact()
        first = history.archive_editorial(self.output, artifact)
        before = tree(self.root)
        self.assertEqual(history.archive_editorial(self.output, artifact), first)
        self.assertEqual(tree(self.root), before)

    def test_legacy_artifact_without_ref_never_guesses_a_new_packet(self):
        self.packet_reference()
        reference = history.archive_editorial(self.output, self.artifact)
        self.assertEqual(reference['input_packet_status'], 'missing_before_archive_feature')
        self.assertEqual(json.loads(self.archived_path(self.artifact).read_bytes()), self.artifact)

    def test_legacy_missing_metadata_is_none_in_reference_not_added_to_artifact(self):
        legacy = {'schema_version': '3', 'status': 'complete', 'month': MONTH, 'claims': []}
        reference = history.archive_editorial(self.output, legacy)
        for key in ('generated_at', 'model', 'input_digest'):
            self.assertIsNone(reference[key])
            self.assertNotIn(key, legacy)
        self.assertEqual(json.loads(self.archived_path(legacy).read_bytes()), legacy)

    def test_reference_only_method_does_not_write_or_claim_local_archive_exists(self):
        before = tree(self.root)
        reference = history.editorial_history_reference(self.output, self.artifact)
        self.assertEqual(reference['input_packet_status'], 'missing_before_archive_feature')
        self.assertEqual(tree(self.root), before)
        self.assertFalse(self.output.exists())
        artifact = self.bound_artifact()
        before = tree(self.root)
        reference = history.editorial_history_reference(self.output, artifact)
        self.assertEqual(reference['input_packet_status'], 'available')
        self.assertEqual(tree(self.root), before)
        self.assertFalse((self.output / 'monthly-history').exists())

    def test_explicit_reference_with_missing_packet_is_an_error_not_legacy_status(self):
        reference = {'input_digest': self.input_digest, 'packet_digest': history.digest(self.packet),
                     'path': 'evidence-packets/' + self.input_digest + '/' + history.digest(self.packet) + '.json'}
        artifact = {**self.artifact, 'evidence_packet_ref': reference}
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'referenced_packet_missing'):
            history.archive_editorial(self.output, artifact)
        self.assertEqual(tree(self.root), before)

    def test_reference_hash_tampering_is_rejected_without_archive_write(self):
        artifact = self.bound_artifact()
        target = self.output / artifact['evidence_packet_ref']['path']
        changed = copy.deepcopy(self.packet)
        changed['facts']['included'] = 99
        target.write_text(json.dumps(changed))
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'packet_digest_mismatch'):
            history.archive_editorial(self.output, artifact)
        self.assertEqual(tree(self.root), before)

    def test_reference_recomputes_logical_digest_not_just_filename_and_exact_hash(self):
        wrong = '0' * 64
        packet_digest = history.digest(self.packet)
        target = self.output / 'evidence-packets' / wrong / (packet_digest + '.json')
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(self.packet))
        artifact = {**self.artifact, 'input_digest': wrong,
                    'evidence_packet_ref': {'input_digest': wrong, 'packet_digest': packet_digest,
                                            'path': 'evidence-packets/' + wrong + '/' + packet_digest + '.json'}}
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'input_digest_mismatch'):
            history.archive_editorial(self.output, artifact)
        self.assertEqual(tree(self.root), before)

    def test_reference_must_match_artifact_month_and_input(self):
        artifact = self.bound_artifact()
        with self.assertRaisesRegex(ValueError, 'packet_month_mismatch'):
            history.archive_editorial(self.output, {**artifact, 'month': '2026-07'})
        with self.assertRaisesRegex(ValueError, 'packet_reference_input_mismatch'):
            history.archive_editorial(self.output, {**artifact, 'input_digest': '0' * 64})
        self.assertFalse((self.output / 'monthly-history').exists())

    def test_reference_path_is_allowlisted_not_arbitrary_relative_or_absolute_path(self):
        artifact = self.bound_artifact()
        for path in ('../secret.json', '/Users/private/secret.json', 'evidence-packets/../secret.json',
                     artifact['evidence_packet_ref']['path'] + '?secret=1'):
            copy_artifact = copy.deepcopy(artifact)
            copy_artifact['evidence_packet_ref']['path'] = path
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, '^editorial_history_unsafe_packet_reference_path$'):
                history.archive_editorial(self.output, copy_artifact)
        self.assertFalse((self.output / 'monthly-history').exists())

    def test_archive_rejects_invalid_schema_status_month_and_metadata(self):
        changes = [{'schema_version': '2'}, {'schema_version': 3}, {'status': 'data_only'}, {'month': '2026-00'},
                   {'month': '2026-13'}, {'month': '0000-08'}, {'month': '../2026-08'},
                   {'generated_at': '2026-02-30T12:00:00Z'}, {'generated_at': '2026-08-01'},
                   {'model': '/Users/private/model'}, {'input_digest': 'not-a-hash'}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                history.archive_editorial(self.output, {**self.artifact, **change})
        self.assertFalse(self.output.exists())

    def test_loading_preserves_every_artifact_and_sorts_by_digest_not_iso_offset_text(self):
        one = copy.deepcopy(self.artifact)
        two = {**copy.deepcopy(self.artifact), 'generated_at': '2026-09-05T21:00:00+08:00', 'model': 'fixture-model-2'}
        first = history.archive_editorial(self.output, one)
        second = history.archive_editorial(self.output, two)
        before = tree(self.root)
        result = history.load_editorial_history(self.output, MONTH)
        self.assertEqual([row['reference']['artifact_digest'] for row in result], sorted([first['artifact_digest'], second['artifact_digest']]))
        self.assertEqual({row['artifact']['model'] for row in result}, {'fixture-model', 'fixture-model-2'})
        self.assertEqual(tree(self.root), before)

    def test_absent_history_is_an_empty_read_only_result(self):
        before = tree(self.root)
        self.assertEqual(history.load_editorial_history(self.output, MONTH), [])
        self.assertEqual(tree(self.root), before)

    def test_loading_rejects_changed_archive_hash_and_does_not_repair_it(self):
        history.archive_editorial(self.output, self.artifact)
        path = self.archived_path(self.artifact)
        path.write_text(json.dumps({**self.artifact, 'claims': []}))
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'artifact_digest_mismatch'):
            history.load_editorial_history(self.output, MONTH)
        self.assertEqual(tree(self.root), before)
        with self.assertRaisesRegex(ValueError, 'immutable_content_conflict'):
            history.archive_editorial(self.output, self.artifact)
        self.assertEqual(tree(self.root), before)

    def test_loading_rejects_bad_filename_and_archive_month_binding(self):
        directory = self.output / 'monthly-history' / MONTH
        directory.mkdir(parents=True)
        path = directory / 'bad.json'
        path.write_text(json.dumps(self.artifact))
        with self.assertRaisesRegex(ValueError, 'invalid_archive_filename'):
            history.load_editorial_history(self.output, MONTH)
        path.unlink()
        wrong_month = {**self.artifact, 'month': '2026-07'}
        (directory / (history.digest(wrong_month) + '.json')).write_text(json.dumps(wrong_month))
        with self.assertRaisesRegex(ValueError, 'archive_month_mismatch'):
            history.load_editorial_history(self.output, MONTH)

    def test_loading_revalidates_explicit_packet_reference(self):
        artifact = self.bound_artifact()
        history.archive_editorial(self.output, artifact)
        (self.output / artifact['evidence_packet_ref']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'packet_digest_mismatch'):
            history.load_editorial_history(self.output, MONTH)

    def test_duplicate_keys_in_saved_packet_or_archive_are_rejected(self):
        artifact = self.bound_artifact()
        path = self.output / artifact['evidence_packet_ref']['path']
        path.write_text('{"month":"2026-08","month":"2026-08"}')
        with self.assertRaisesRegex(ValueError, 'duplicate_json_key'):
            history.editorial_history_reference(self.output, artifact)
        history.archive_editorial(self.output, self.artifact)
        self.archived_path(self.artifact).write_text('{"month":"2026-08","month":"2026-08"}')
        with self.assertRaisesRegex(ValueError, 'duplicate_json_key'):
            history.load_editorial_history(self.output, MONTH)

    def test_custom_root_parent_directory_and_file_symlinks_are_rejected(self):
        real = self.root / 'real'
        real.mkdir()
        link = self.root / 'linked'
        link.symlink_to(real, target_is_directory=True)
        for target in (link, link / 'editorial'):
            with self.subTest(target=str(target)), self.assertRaisesRegex(ValueError, 'unsafe_path'):
                history.archive_editorial(target, self.artifact)
        reference = self.packet_reference()
        packet_path = self.output / reference['path']
        packet_path.unlink()
        outside = self.root / 'outside.json'
        outside.write_text(json.dumps(self.packet))
        packet_path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'unsafe_file'):
            history.editorial_history_reference(self.output, {**self.artifact, 'evidence_packet_ref': reference})

    def test_symlinked_history_directory_is_not_followed(self):
        self.output.mkdir()
        external = self.root / 'external'
        external.mkdir()
        (self.output / 'monthly-history').symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe_path'):
            history.archive_editorial(self.output, self.artifact)
        self.assertEqual(list(external.iterdir()), [])

    def test_symlinked_archive_file_is_rejected_without_overwriting_its_target(self):
        history.archive_editorial(self.output, self.artifact)
        archived = self.archived_path(self.artifact)
        external = self.root / 'external-artifact.json'
        archived.rename(external)
        archived.symlink_to(external)
        original = external.read_bytes()
        with self.assertRaisesRegex(ValueError, 'unsafe_file'):
            history.archive_editorial(self.output, self.artifact)
        with self.assertRaisesRegex(ValueError, 'unsafe_file'):
            history.load_editorial_history(self.output, MONTH)
        self.assertEqual(external.read_bytes(), original)

    def test_pretty_existing_equivalent_json_is_accepted_without_reserialization(self):
        reference = self.packet_reference()
        path = self.output / reference['path']
        path.write_text(json.dumps(self.packet, ensure_ascii=False, indent=2) + '\n')
        before = tree(self.root)
        self.assertEqual(self.packet_reference(), reference)
        self.assertEqual(tree(self.root), before)


if __name__ == '__main__':
    unittest.main()
