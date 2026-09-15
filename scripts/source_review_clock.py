"""Fixed, source-bound visibility clock, separate from corpus/publication dates.

No current-time fallback, collection, or writes. A configured watermark binds
exactly the approved public ledgers below; private caches are never read.
Legacy callers without configuration retain their corpus cutoff (UTC day-end
for date inputs). Visibility is not a claim of complete acquisition or review.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

LEDGER_PATHS = (
    'data/hardware-review/source-observations.jsonl',
    'data/hardware-review/source-scans.jsonl',
    'data/hardware-review/fulltext-readings.jsonl',
    'data/hardware-review/pdf-source-observations.jsonl',
    'data/hardware-review/pdf-readings.jsonl',
    'data/hardware-review/section-reviews.jsonl',
    'data/editorial/source-content-conflicts.jsonl',
    'data/equipment/usage-evidence.jsonl',
)
HASH = re.compile(r'[0-9a-f]{64}\Z')
DAY = re.compile(r'\d{4}-\d{2}-\d{2}\Z')
STAMP = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z')
MAX_CONFIG_BYTES = 64 * 1024
MAX_LEDGER_BYTES = 256 * 1024 * 1024


class SourceReviewClockError(ValueError):
    """Fixed codes only; do not echo configuration, paths, or source content."""


def _require(condition, reason):
    if not condition:
        raise SourceReviewClockError('source_review_clock:' + reason)


def utc_cutoff(value):
    """Parse a UTC timestamp or inclusive UTC calendar-day cutoff, never now."""
    if isinstance(value, datetime):
        _require(value.tzinfo is not None and value.utcoffset() is not None, 'utc_cutoff_required')
        return value.astimezone(timezone.utc)
    _require(isinstance(value, str), 'utc_cutoff_required')
    try:
        if DAY.fullmatch(value):
            return datetime.combine(date.fromisoformat(value), time.max, timezone.utc)
        _require(bool(STAMP.fullmatch(value)), 'utc_cutoff_required')
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        if isinstance(error, SourceReviewClockError):
            raise
        raise SourceReviewClockError('source_review_clock:utc_cutoff_required') from None


def visible(value, cutoff):
    """Inclusive exact comparison; date-only values mean UTC day-end."""
    return utc_cutoff(value) <= utc_cutoff(cutoff)


def usage_visible(record, cutoff):
    """Acquisition is not review completion; legacy rows may lack reviewed_at."""
    observed = utc_cutoff(record.get('observed_at'))
    reviewed = utc_cutoff(record['reviewed_at']) if record.get('reviewed_at') is not None else None
    boundary = utc_cutoff(cutoff)
    return observed <= boundary and (reviewed is None or reviewed <= boundary)


def _stamp(value):
    return utc_cutoff(value).isoformat().replace('+00:00', 'Z')


def manifest_source_review_clock(manifest):
    """Read only manifest fields, never configuration or original sources.

    Both explicit fields are mandatory together. A null digest is reserved
    for the exact legacy data_through cutoff, not an unbound arbitrary clock.
    """
    _require(isinstance(manifest, dict), 'manifest_required')
    legacy = _stamp(manifest.get('data_through'))
    fields = {'source_review_as_of', 'source_review_clock_digest'}
    present = fields & manifest.keys()
    if not present:
        return {'source_review_as_of': legacy, 'source_review_clock_digest': None}
    _require(present == fields, 'incomplete_manifest_clock')
    value, digest = manifest['source_review_as_of'], manifest['source_review_clock_digest']
    _require(isinstance(value, str) and bool(STAMP.fullmatch(value)), 'manifest_timestamp_required')
    utc_cutoff(value)
    _require(digest is None and value == legacy or isinstance(digest, str) and bool(HASH.fullmatch(digest)),
             'invalid_manifest_clock_digest')
    return {'source_review_as_of': value, 'source_review_clock_digest': digest}


def _absolute_path(value):
    try:
        path = Path(value).absolute()
        _require(path != Path(path.anchor) and '..' not in path.parts, 'unsafe_path')
        physical = path
        for part in (path, *path.parents):
            if part.is_symlink():
                system_alias = (sys.platform == 'darwin' and part in (Path('/var'), Path('/tmp')) and
                                part.resolve(strict=True) == Path('/private') / part.name)
                _require(system_alias, 'unsafe_path')
                physical = Path('/private') / part.name / path.relative_to(part)
        return physical
    except SourceReviewClockError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError):
        raise SourceReviewClockError('source_review_clock:unsafe_path') from None


def _open_root(path):
    descriptor = None
    try:
        descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        raise SourceReviewClockError('source_review_clock:unsafe_root') from None


def _read_relative(root, relative, *, optional=False, hash_only=False):
    directory, descriptor = os.dup(root), None
    try:
        parts = Path(relative).parts
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        before = os.fstat(descriptor)
        limit = MAX_LEDGER_BYTES if hash_only else MAX_CONFIG_BYTES
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'not_bounded_regular_file')
        remaining, chunks, digest = before.st_size, [], hashlib.sha256()
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            _require(bool(chunk), 'input_changed_during_read')
            remaining -= len(chunk)
            if hash_only:
                digest.update(chunk)
            else:
                chunks.append(chunk)
        after = os.fstat(descriptor)
        identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        _require(identity(before) == identity(after), 'input_changed_during_read')
        return digest.hexdigest() if hash_only else b''.join(chunks)
    except FileNotFoundError:
        if optional:
            return None
        raise SourceReviewClockError('source_review_clock:bound_ledger_missing') from None
    except OSError:
        raise SourceReviewClockError('source_review_clock:unsafe_file_or_io') from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory)


def _decode_config(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    def constant(_):
        raise SourceReviewClockError('source_review_clock:nonfinite_json')
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except SourceReviewClockError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise SourceReviewClockError('source_review_clock:invalid_json') from None
    _require(isinstance(value, dict) and set(value) == {'schema_version', 'source_review_as_of', 'ledger_sha256'} and
             value['schema_version'] == '1', 'config_schema_invalid')
    _require(isinstance(value['source_review_as_of'], str) and bool(STAMP.fullmatch(value['source_review_as_of'])),
             'config_timestamp_required')
    utc_cutoff(value['source_review_as_of'])
    ledgers = value['ledger_sha256']
    _require(isinstance(ledgers, dict) and set(ledgers) == set(LEDGER_PATHS), 'ledger_path_set_invalid')
    _require(all(isinstance(digest, str) and HASH.fullmatch(digest) for digest in ledgers.values()), 'ledger_hash_invalid')
    return value


def resolve_source_review_clock(root, data_through, config_path=None):
    """Verify a fixed watermark against eight public ledgers without writes.

    config_path may override the default with another JSON file inside the
    root's config directory. Only a missing DEFAULT config permits legacy mode;
    an existing malformed config, missing ledger, or mismatch never does.
    """
    legacy = _stamp(data_through)
    root = _absolute_path(root)
    try:
        chosen = Path('config/source-review-clock.json') if config_path is None else Path(config_path)
    except (TypeError, ValueError):
        raise SourceReviewClockError('source_review_clock:unsafe_config_path') from None
    if chosen.is_absolute():
        try:
            chosen = _absolute_path(chosen).relative_to(root)
        except ValueError:
            raise SourceReviewClockError('source_review_clock:unsafe_config_path') from None
    _require(len(chosen.parts) >= 2 and chosen.parts[0] == 'config' and chosen.suffix == '.json' and
             '..' not in chosen.parts and all(part not in {'.', ''} and part.isprintable() for part in chosen.parts),
             'unsafe_config_path')
    descriptor = _open_root(root)
    try:
        raw = _read_relative(descriptor, chosen, optional=True)
        if raw is None:
            _require(config_path is None, 'explicit_config_missing')
            return {'source_review_as_of': legacy, 'source_review_clock_digest': None,
                    'source_review_clock': {'schema_version': '1', 'basis': 'legacy_data_through', 'ledger_sha256': {}}}
        config = _decode_config(raw)
        for path in LEDGER_PATHS:
            actual = _read_relative(descriptor, path, hash_only=True)
            _require(actual == config['ledger_sha256'][path], 'ledger_hash_mismatch')
        # Recheck the config commit marker; a concurrent replacement must not
        # silently mix a newly edited watermark with the ledgers just read.
        _require(_read_relative(descriptor, chosen) == raw, 'config_changed_during_validation')
        canonical = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return {'source_review_as_of': config['source_review_as_of'],
                'source_review_clock_digest': hashlib.sha256(canonical.encode()).hexdigest(),
                'source_review_clock': {'schema_version': '1', 'basis': 'configured_bound_ledger',
                                        'ledger_sha256': dict(config['ledger_sha256'])}}
    finally:
        os.close(descriptor)
