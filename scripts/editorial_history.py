"""Immutable monthly-editorial history and exact input packets.

``output`` is the persistent editorial directory, NOT a generated public API.
Each file is published atomically without replacing an existing path. The
original JSON object is preserved; hashes canonicalize formatting/key order,
not values. No timestamps, fields, provenance or approval are invented.

Packet reference: {input_digest, packet_digest, path}; path is relative to
output. History references have exactly six public fields. A missing explicit
packet reference means missing_before_archive_feature, even when a newly
saved packet happens to share the old logical input digest. A claimed but
missing/corrupt reference is an error, never an available input.

load_editorial_history returns [{artifact, reference}], sorted by content
digest (not timestamp text). editorial_history_reference is read-only and
also supports unarchived stale-current artifacts for derived virtual exports.
There is no network, model invocation, or cross-file transaction in this
module. A completed atomic file can safely be reused after an interrupted run.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import sys
import uuid
from datetime import datetime
from pathlib import Path

HASH = re.compile(r'[0-9a-f]{64}\Z')
MONTH = re.compile(r'[0-9]{4}-(?:0[1-9]|1[0-2])\Z')
STAMP = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z')
MAX_JSON_BYTES = 256 * 1024 * 1024


class EditorialHistoryError(ValueError):
    """Only fixed reason codes; never include paths or artifact text."""


def _require(condition, code):
    if not condition:
        raise EditorialHistoryError(code)


def _validate_json_types(value):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        _require(math.isfinite(value), 'editorial_history_nonfinite_json')
        return
    if type(value) is list:
        for item in value:
            _validate_json_types(item)
        return
    if type(value) is dict:
        _require(all(type(key) is str for key in value), 'editorial_history_nonstring_json_key')
        for item in value.values():
            _validate_json_types(item)
        return
    raise EditorialHistoryError('editorial_history_nonjson_value')


def canonical_json(value):
    """Same finite-JSON digest convention as the existing editorial layer."""
    try:
        _validate_json_types(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except EditorialHistoryError:
        raise
    except (TypeError, ValueError, RecursionError):
        raise EditorialHistoryError('editorial_history_invalid_json') from None


def digest(value):
    try:
        return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()
    except UnicodeError:
        raise EditorialHistoryError('editorial_history_invalid_unicode') from None


def _decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, 'editorial_history_duplicate_json_key')
            result[key] = value
        return result
    def constant(_):
        raise EditorialHistoryError('editorial_history_nonfinite_json')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except EditorialHistoryError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise EditorialHistoryError('editorial_history_invalid_json') from None


def _snapshot(value):
    try:
        raw = canonical_json(value).encode('utf-8')
    except UnicodeError:
        raise EditorialHistoryError('editorial_history_invalid_unicode') from None
    _require(len(raw) <= MAX_JSON_BYTES, 'editorial_history_json_too_large')
    return _decode(raw), raw


def _hash(value, code='editorial_history_invalid_digest'):
    _require(isinstance(value, str) and HASH.fullmatch(value), code)
    return value


def _month(value):
    _require(isinstance(value, str) and MONTH.fullmatch(value) and value[:4] != '0000',
             'editorial_history_invalid_month')
    return value


def _root_path(output):
    try:
        path = Path(output).absolute()
    except (TypeError, ValueError, OSError):
        raise EditorialHistoryError('editorial_history_unsafe_path') from None
    _require(path != Path(path.anchor) and '..' not in path.parts, 'editorial_history_unsafe_path')
    try:
        physical = path
        for item in (path, *path.parents):
            if not item.is_symlink():
                continue
            # macOS's system temp aliases are fixed OS paths, not caller-owned
            # symlink traversal. Custom symlink roots/ancestors remain forbidden.
            system_alias = (sys.platform == 'darwin' and item in (Path('/var'), Path('/tmp')) and
                            item.resolve(strict=True) == Path('/private') / item.name)
            _require(system_alias, 'editorial_history_unsafe_path')
            physical = Path('/private') / item.name / path.relative_to(item)
        # Do not resolve caller-owned ancestors after checking them; subsequent
        # descriptor traversal must still reject a concurrently swapped symlink.
        return physical
    except EditorialHistoryError:
        raise
    except (OSError, RuntimeError, ValueError):
        raise EditorialHistoryError('editorial_history_unsafe_path') from None


def _open_directory(path, *, create=False, optional=False):
    """Descriptor-bound O_NOFOLLOW traversal, including every parent."""
    descriptor = None
    try:
        descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for name in path.parts[1:]:
            try:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    if optional:
                        os.close(descriptor)
                        return None
                    raise EditorialHistoryError('editorial_history_input_missing') from None
                try:
                    os.mkdir(name, mode=0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except EditorialHistoryError:
        if descriptor is not None:
            os.close(descriptor)
        raise
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        raise EditorialHistoryError('editorial_history_unsafe_path_or_io') from None


def _read_at(directory, name, *, optional=False):
    try:
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except FileNotFoundError:
        if optional:
            return None
        raise EditorialHistoryError('editorial_history_input_missing') from None
    except OSError:
        raise EditorialHistoryError('editorial_history_unsafe_file') from None
    try:
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_JSON_BYTES,
                 'editorial_history_not_bounded_regular_file')
        chunks, remaining = [], before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            _require(bool(chunk), 'editorial_history_file_changed_during_read')
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        _require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                 (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'editorial_history_file_changed_during_read')
        return b''.join(chunks)
    except OSError:
        raise EditorialHistoryError('editorial_history_read_failed') from None
    finally:
        os.close(descriptor)


def _same_existing(raw, expected_raw):
    try:
        return canonical_json(_decode(raw)).encode('utf-8') == expected_raw
    except (EditorialHistoryError, UnicodeError):
        return False


def _immutable_write(root, relative, raw):
    """Atomic create-if-absent; os.replace must never overwrite an archive."""
    directory = _open_directory(root / relative.parent, create=True)
    temporary = None
    descriptor = None
    try:
        old = _read_at(directory, relative.name, optional=True)
        if old is not None:
            _require(_same_existing(old, raw), 'editorial_history_immutable_content_conflict')
            return
        temporary = '.editorial-history-' + uuid.uuid4().hex + '.tmp'
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=directory)
        contents = memoryview(raw + b'\n')
        while contents:
            written = os.write(descriptor, contents)
            _require(written > 0, 'editorial_history_write_failed')
            contents = contents[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            # Publishing a complete temporary inode with link(2) is atomic and
            # fails on an existing destination instead of replacing history.
            os.link(temporary, relative.name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        except FileExistsError:
            _require(_same_existing(_read_at(directory, relative.name), raw),
                     'editorial_history_immutable_content_conflict')
        os.fsync(directory)
    except EditorialHistoryError:
        raise
    except OSError:
        raise EditorialHistoryError('editorial_history_write_failed') from None
    finally:
        cleanup_failed = False
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                cleanup_failed = True
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass
            except OSError:
                cleanup_failed = True
        try:
            os.close(directory)
        except OSError:
            cleanup_failed = True
        if cleanup_failed:
            raise EditorialHistoryError('editorial_history_cleanup_failed') from None


def _logical_input_digest(packet):
    # Import only when called: generate_v3_editorial may itself import us.
    # Keep one source of truth for translation-cache exclusions.
    try:
        from generate_v3_editorial import editorial_input_digest
    except ModuleNotFoundError:
        from scripts.generate_v3_editorial import editorial_input_digest
    try:
        return editorial_input_digest(packet)
    except (ValueError, TypeError, AttributeError, KeyError, RecursionError):
        raise EditorialHistoryError('editorial_history_invalid_evidence_packet') from None


def persist_evidence_packet(output, packet, input_digest):
    """Persist the EXACT packet, preserving multiple translation variants."""
    root = _root_path(output)
    value, raw = _snapshot(packet)
    _require(isinstance(value, dict), 'editorial_history_invalid_evidence_packet')
    _month(value.get('month'))
    _hash(input_digest)
    _require(_logical_input_digest(value) == input_digest, 'editorial_history_input_digest_mismatch')
    exact = hashlib.sha256(raw).hexdigest()
    relative = Path('evidence-packets') / input_digest / (exact + '.json')
    _immutable_write(root, relative, raw)
    return {'input_digest': input_digest, 'packet_digest': exact, 'path': relative.as_posix()}


def _validate_artifact(artifact):
    _require(isinstance(artifact, dict) and artifact.get('schema_version') == '3' and artifact.get('status') == 'complete',
             'editorial_history_complete_schema3_artifact_required')
    _month(artifact.get('month'))
    generated = artifact.get('generated_at')
    if generated is not None:
        _require(isinstance(generated, str) and STAMP.fullmatch(generated), 'editorial_history_invalid_generated_at')
        try:
            datetime.fromisoformat(generated.replace('Z', '+00:00'))
        except ValueError:
            raise EditorialHistoryError('editorial_history_invalid_generated_at') from None
    model = artifact.get('model')
    if model is not None:
        _require(isinstance(model, str) and 0 < len(model) <= 200 and not model.startswith(('/', '~', 'file:')) and
                 not re.match(r'^[A-Za-z]:[\\/]', model) and not any(ord(char) < 32 for char in model),
                 'editorial_history_invalid_model')
    if artifact.get('input_digest') is not None:
        _hash(artifact['input_digest'])


def _packet_status(root, artifact):
    if 'evidence_packet_ref' not in artifact:
        return 'missing_before_archive_feature'
    reference = artifact['evidence_packet_ref']
    _require(isinstance(reference, dict) and set(reference) == {'input_digest', 'packet_digest', 'path'},
             'editorial_history_invalid_packet_reference')
    input_id = _hash(reference.get('input_digest'))
    packet_id = _hash(reference.get('packet_digest'))
    _require(artifact.get('input_digest') == input_id, 'editorial_history_packet_reference_input_mismatch')
    expected = Path('evidence-packets') / input_id / (packet_id + '.json')
    _require(reference.get('path') == expected.as_posix(), 'editorial_history_unsafe_packet_reference_path')
    directory = _open_directory(root / expected.parent, optional=True)
    _require(directory is not None, 'editorial_history_referenced_packet_missing')
    try:
        raw = _read_at(directory, expected.name, optional=True)
    finally:
        os.close(directory)
    _require(raw is not None, 'editorial_history_referenced_packet_missing')
    packet = _decode(raw)
    _require(isinstance(packet, dict) and digest(packet) == packet_id, 'editorial_history_packet_digest_mismatch')
    _require(_logical_input_digest(packet) == input_id, 'editorial_history_input_digest_mismatch')
    _require(packet.get('month') == artifact['month'], 'editorial_history_packet_month_mismatch')
    return 'available'


def editorial_history_reference(output, artifact):
    """Read-only six-field reference for archived OR virtual stale history.

    Missing legacy metadata is returned as None, not inserted into the artifact.
    The computed public URL does not claim that a file was persisted locally.
    """
    root = _root_path(output)
    value, _ = _snapshot(artifact)
    _validate_artifact(value)
    artifact_digest = digest(value)
    return {'artifact_digest': artifact_digest, 'generated_at': value.get('generated_at'), 'model': value.get('model'),
            'input_digest': value.get('input_digest'),
            'archive_url': '/api/v1/editorial-history/' + value['month'] + '/' + artifact_digest + '.json',
            'input_packet_status': _packet_status(root, value)}


def archive_editorial(output, artifact):
    """Save one complete artifact without modifying it or existing history."""
    root = _root_path(output)
    value, raw = _snapshot(artifact)
    reference = editorial_history_reference(root, value)
    relative = Path('monthly-history') / value['month'] / (reference['artifact_digest'] + '.json')
    _immutable_write(root, relative, raw)
    return reference


def load_editorial_history(output, month):
    """Return validated [{artifact, reference}], in artifact-digest order.

    Absent history returns []; invalid filenames, altered artifacts, invalid
    month bindings, and corrupt explicit packet references fail closed.
    """
    root = _root_path(output)
    month = _month(month)
    directory = _open_directory(root / 'monthly-history' / month, optional=True)
    if directory is None:
        return []
    result = []
    try:
        for name in sorted(os.listdir(directory)):
            if not name.endswith('.json'):
                continue
            expected = name[:-5]
            _hash(expected, 'editorial_history_invalid_archive_filename')
            value = _decode(_read_at(directory, name))
            _validate_artifact(value)
            _require(value['month'] == month, 'editorial_history_archive_month_mismatch')
            _require(digest(value) == expected, 'editorial_history_artifact_digest_mismatch')
            result.append({'artifact': value, 'reference': editorial_history_reference(root, value)})
        return result
    except OSError:
        raise EditorialHistoryError('editorial_history_read_failed') from None
    finally:
        os.close(directory)
