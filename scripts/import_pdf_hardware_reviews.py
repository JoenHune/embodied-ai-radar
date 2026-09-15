#!/usr/bin/env python3
"""Offline, page-bound AI hardware assertions backed by complete PDF readings.

No PDF/cache access, downloads, model calls, new device identities or clock writes.
Input is {schema_version: "1", reviews: [flat assertions]}; each assertion has
REVIEW_KEYS below. Existing hardware_id/name (or a registered alias) is required.
source_pages are one-based PDF file pages, never printed page labels. Their hash
map must exactly match both the public source and the complete reading receipt.

The CLI obtains its cutoff from the configured, eight-ledger-bound approved
source clock (no --as-of/current-time fallback). It writes usage-evidence ONLY,
and ONLY with --apply. After a changed write the owner must reapprove the source
clock's ledger hashes by the normal process; this importer never does so.

Public audit verifies metadata/declaration consistency, not that an AI assertion
is scientifically true, all experiments were checked, or experiments reproduced.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import stat
import tempfile
from pathlib import Path
from urllib.parse import urljoin

from catalog_store import encode, fingerprint, load_catalog
from equipment_radar import TABLES, validate_equipment
from import_hardware_source_reviews import usage_semantics, normalized
from pdf_reading_reviews import public_audit as audit_pdf_readings, timestamp, digest
from source_review_clock import resolve_source_review_clock, utc_cutoff

ROOT = Path(__file__).resolve().parents[1]
ASSURANCE = 'self_attested_AI_page_hardware_usage_not_independent_verification'
SCOPE = 'pdf_page_hardware_use_assertions_only'
REVIEW_KEYS = set('work_id hardware_id reported_device_name role setting usage_scope configuration '
                  'validation_context statement_zh source_observation_id reading_id manifestation_id '
                  'source_url source_version pdf_sha256 observed_at reviewed_at source_pages '
                  'page_text_sha256 reviewer_kind review_scope'.split())
PROOF_KEYS = set('schema_version source_observation_id reading_id manifestation_id pdf_sha256 '
                 'document_text_sha256 extractor_version source_pages page_text_sha256 '
                 'reading_completed_at source_metadata_sha256 reading_declaration_sha256 assertion_sha256'.split())
ROW_KEYS = set('usage_id work_id hardware_id reported_device_name role reported_role reported_roles setting '
               'usage_scope configuration validation_context statement source_url source_version source_locator '
               'source_kind review_status work_url observed_at reviewed_at source_format pdf_evidence '
               'reviewer_kind review_scope assurance human_reviewed independently_verified '
               'full_experiment_verified'.split())
PRIVATE = re.compile(r'\bfile:(?=\S)|/(?:Users|home|private|tmp|var|etc|Volumes|mnt|root)/|'
                     r'\.research(?:/|\\)|(?<![A-Za-z0-9_])[A-Za-z]:[\\/]|\\\\[^\\]+\\|~/|\$\{?HOME\}?/', re.I)
MAX_BYTES = 256 * 1024 * 1024


def fail(code):
    raise ValueError('pdf_hardware_review:' + code)


def _fields(value, keys, optional=()):
    if not isinstance(value, dict) or set(value) - keys - set(optional) or keys - set(value):
        fail('unknown_or_missing_fields')


def _public(value):
    """Reject private text even in nested fields that would not be exported."""
    if isinstance(value, str):
        if (PRIVATE.search(value) or value.startswith('/') or
                any(ord(char) < 32 or ord(char) == 127 for char in value)):
            fail('private_path_or_control_character')
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                fail('string_keys_required')
            _public(key)
            _public(item)
    elif isinstance(value, list):
        for item in value:
            _public(item)
    elif isinstance(value, float) and not math.isfinite(value):
        fail('nonfinite_json')
    elif value is not None and type(value) not in {int, float, bool}:
        fail('invalid_json_value')


def _text(value, label, *, chinese=False, limit=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        fail('invalid_' + label)
    _public(value)
    if chinese and not re.search(r'[\u3400-\u9fff]', value):
        fail('chinese_statement_required')
    return value


def cross_source_semantics(row):
    # Reuse the HTML semantic definition but deliberately omit its URL member.
    # A second PDF/HTML citation, page, version or configuration is not a new use.
    return usage_semantics(row)[:-1]


def _is_pdf_usage(row):
    return (row.get('source_format') == 'pdf' or 'pdf_evidence' in row or
            row.get('review_scope') == SCOPE or str(row.get('usage_id', '')).startswith('usage:pdf:'))


def _indexes(payload, public_pdf_sources, public_pdf_readings):
    # Validate complete history before selecting a referenced receipt. Unrelated
    # later valid readings are permitted, but cannot support an earlier usage.
    checked = audit_pdf_readings(public_pdf_readings, payload, public_pdf_sources,
                                '9999-12-31T23:59:59Z')
    for source in checked['sources']:
        # The existing PDF audit has validated the complete original metadata,
        # including its hash and landing -> target link. A root-relative web
        # href (e.g. /pdf/2409.11952v1) is not a filesystem path in THIS field.
        # Inspect a temporary projection with only that validated href resolved;
        # never mutate/re-hash the source or return the projection as evidence.
        link = source['pdf_link_evidence']
        href = link['anchor_href']
        projection = source
        if href is not None:
            if PRIVATE.search(href) or any(ord(char) < 32 or ord(char) == 127 for char in href):
                fail('private_path_or_control_character')
            target = urljoin(source['landing_url'], href)
            if target != source['source_url']:
                fail('PDF_anchor_binding_mismatch')
            projection = {**source, 'pdf_link_evidence': {**link, 'anchor_href': target}}
        _public(projection)
    _public(checked['records'])
    return ({row['source_observation_id']: row for row in checked['sources']},
            {row['reading_id']: row for row in checked['records']})


def _make_usage(review, payload, devices, sources, readings, source_review_as_of):
    _fields(review, REVIEW_KEYS)
    _public(review)
    if review['reviewer_kind'] != 'AI' or review['review_scope'] != 'hardware_use_assertions_only':
        fail('explicit_AI_usage_declaration_required')
    for key in ('work_id', 'hardware_id', 'reported_device_name', 'role', 'setting', 'usage_scope',
                'configuration', 'validation_context', 'source_observation_id', 'reading_id', 'manifestation_id',
                'source_url'):
        _text(review[key], key)
    _text(review['statement_zh'], 'statement', chinese=True)
    source, reading = sources.get(review['source_observation_id']), readings.get(review['reading_id'])
    if source is None or reading is None or reading['source_observation_id'] != source['source_observation_id']:
        fail('complete_reading_and_source_required')
    bindings = {'work_id': 'work_id', 'manifestation_id': 'manifestation_id', 'source_url': 'source_url',
                'source_version': 'version', 'pdf_sha256': 'pdf_sha256', 'observed_at': 'observed_at'}
    if any(review[key] != source[field] or review[key] != reading[field] for key, field in bindings.items()):
        fail('work_version_or_source_binding_mismatch')
    digest(review['pdf_sha256'])
    when = timestamp(review['reviewed_at'])
    if not timestamp(reading['read_completed_at']) <= when <= utc_cutoff(source_review_as_of):
        fail('review_before_reading_or_after_approved_clock')
    pages, hashes = review['source_pages'], review['page_text_sha256']
    if (not isinstance(pages, list) or not pages or any(type(page) is not int or
            not 1 <= page <= source['page_count'] for page in pages) or pages != sorted(set(pages))):
        fail('invalid_or_duplicate_pdf_pages')
    if not isinstance(hashes, dict) or set(hashes) != {str(page) for page in pages}:
        fail('exact_page_hash_keys_required')
    for page in pages:
        key = str(page)
        digest(hashes[key])
        if (page not in reading['read_pages'] or hashes[key] != source['page_text_sha256'][key]
                or hashes[key] != reading['page_text_sha256'][key]):
            fail('page_hash_or_reading_coverage_mismatch')
    device = devices.get(review['hardware_id'])
    if device is None:
        fail('existing_hardware_id_required')
    labels = [device['name'], *device.get('aliases', [])]
    if normalized(review['reported_device_name']) not in {normalized(label) for label in labels}:
        fail('hardware_name_or_alias_mismatch')
    if device['identity_level'] != 'model_specified' and device.get('identity_context_work_id') != review['work_id']:
        fail('uncertain_hardware_identity_cross_work')
    if review['role'] in {'mentioned', 'dataset_source'}:
        fail('explicit_equipment_use_role_required')
    work = next(row for row in payload['works'] if row['work_id'] == review['work_id'])
    identifiers = work.get('identifiers', {})
    work_url = ('https://doi.org/' + identifiers['doi'] if identifiers.get('doi') else
                'https://arxiv.org/abs/' + identifiers['arxiv'] if identifiers.get('arxiv') else source['landing_url'])
    proof = {
        'schema_version': '1', 'source_observation_id': source['source_observation_id'],
        'reading_id': reading['reading_id'], 'manifestation_id': source['manifestation_id'],
        'pdf_sha256': source['pdf_sha256'], 'document_text_sha256': source['document_text_sha256'],
        'extractor_version': source['extractor_version'], 'source_pages': copy.deepcopy(pages),
        'page_text_sha256': copy.deepcopy(hashes), 'reading_completed_at': reading['read_completed_at'],
        'source_metadata_sha256': source['metadata_sha256'],
        'reading_declaration_sha256': reading['declaration_sha256'], 'assertion_sha256': fingerprint(review),
    }
    result = {key: review[key] for key in ('work_id', 'hardware_id', 'reported_device_name', 'role', 'setting',
        'usage_scope', 'configuration', 'validation_context', 'source_url', 'source_version', 'observed_at', 'reviewed_at')}
    result.update(reported_role=review['role'], reported_roles=[review['role']], statement=review['statement_zh'],
                  source_locator='PDF pages ' + ', '.join(map(str, pages)), source_kind='paper', review_status='verified',
                  work_url=work_url, source_format='pdf', pdf_evidence=proof, reviewer_kind='AI', review_scope=SCOPE,
                  assurance=ASSURANCE, human_reviewed=False, independently_verified=False, full_experiment_verified=False)
    result['usage_id'] = 'usage:pdf:' + fingerprint(cross_source_semantics(result))[:24]
    return result


def _declaration_from_usage(row):
    _fields(row, ROW_KEYS, {'submitted_work_id'})
    _fields(row['pdf_evidence'], PROOF_KEYS)
    if 'submitted_work_id' in row and row['submitted_work_id'] != row['work_id']:
        fail('PDF_usage_must_use_canonical_work_id')
    proof = row['pdf_evidence']
    value = {key: row[key] for key in ('work_id', 'hardware_id', 'reported_device_name', 'role', 'setting',
        'usage_scope', 'configuration', 'validation_context', 'source_url', 'source_version', 'observed_at', 'reviewed_at')}
    value.update({key: proof[key] for key in ('source_observation_id', 'reading_id', 'manifestation_id',
                                             'pdf_sha256', 'source_pages', 'page_text_sha256')})
    value.update(statement_zh=row['statement'], reviewer_kind='AI', review_scope='hardware_use_assertions_only')
    return value


def audit_pdf_hardware_usage(payload, authority, public_pdf_sources, public_pdf_readings, source_review_as_of):
    """Public metadata only; all inputs are supplied, never read from private cache."""
    utc_cutoff(source_review_as_of)  # mandatory explicit clock, never wall time
    canonical = validate_equipment(payload, authority)
    sources, readings = _indexes(payload, public_pdf_sources, public_pdf_readings)
    devices = {row['hardware_id']: row for row in canonical['devices']}
    semantic = {}
    for row in canonical['usage-evidence']:
        semantic.setdefault(cross_source_semantics(row), []).append(row)
    checked = 0
    for row in canonical['usage-evidence']:
        if not _is_pdf_usage(row):
            continue  # Preserve legacy/HTML metadata and per-locator behavior.
        _public(row)
        expected = _make_usage(_declaration_from_usage(row), payload, devices, sources, readings, source_review_as_of)
        actual = {key: value for key, value in row.items() if key != 'submitted_work_id'}
        # encode distinguishes JSON true from 1 (Python dict equality does not).
        if encode(actual) != encode(expected):
            fail('public_PDF_usage_proof_or_declaration_mismatch')
        if len(semantic[cross_source_semantics(row)]) != 1:
            fail('duplicate_cross_source_semantic_usage')
        checked += 1
    return {'status': 'passed', 'pdf_usage_count': checked, 'assurance': ASSURANCE,
            'verification_scope': 'public_PDF_source_reading_page_and_AI_assertion_consistency_only',
            'private_source_reverified': False, 'independent_reproduction_verified': False}


def prepare_reviews(declarations, payload, authority, public_pdf_sources, public_pdf_readings, source_review_as_of):
    _fields(declarations, {'schema_version', 'reviews'})
    _public(declarations)
    if declarations['schema_version'] != '1' or not isinstance(declarations['reviews'], list) or not declarations['reviews']:
        fail('nonempty_explicit_review_list_required')
    canonical = validate_equipment(payload, authority)
    sources, readings = _indexes(payload, public_pdf_sources, public_pdf_readings)
    devices = {row['hardware_id']: row for row in canonical['devices']}
    proposed = [_make_usage(row, payload, devices, sources, readings, source_review_as_of)
                for row in declarations['reviews']]
    if len({row['usage_id'] for row in proposed}) != len(proposed):
        fail('duplicate_cross_source_semantic_usage')
    merged = copy.deepcopy(authority)
    known = {row['usage_id']: row for row in merged['usage-evidence']}
    added = 0
    for row in proposed:
        previous = known.get(row['usage_id'])
        if previous is not None:
            stripped = {key: val for key, val in previous.items() if key != 'submitted_work_id'}
            if encode(stripped) != encode(row):
                fail('existing_PDF_usage_conflict')
        else:
            known[row['usage_id']] = row
            added += 1
    merged['usage-evidence'] = [known[key] for key in sorted(known)]
    audit = audit_pdf_hardware_usage(payload, merged, public_pdf_sources, public_pdf_readings, source_review_as_of)
    return merged, {'applied': False, 'added': {'usage-evidence': added}, 'devices_created': 0,
                    'assertion_count': len(proposed), 'audit': audit}


def _safe_file(path):
    path = Path(path).absolute()
    if '..' in path.parts or any(part.is_symlink() for part in (path, *path.parents)):
        fail('unsafe_file_symlink_or_path')
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        fail('bounded_regular_file_required')
    return path


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail('duplicate_json_key')
            result[key] = value
        return result
    def nonfinite(_):
        fail('nonfinite_json')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def read_public_jsonl(path):
    return [strict_json(line) for line in _safe_file(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def _catalog_snapshot(root, payload, metadata):
    """Pin actual logical rows AND the catalog manifest, not its claimed hash.

    A canonical merge or direct table edit may occur before a new manifest hash
    is written. Compute our own table digests, so the source clock alone cannot
    accidentally bless a different work/manifestation mapping at commit time.
    """
    path = _safe_file(Path(root) / 'data/catalog/manifest.json')
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if identity(before) != identity(after) or encode(strict_json(raw)) != encode(metadata):
        fail('catalog_manifest_changed_during_read')
    return (fingerprint({'tables': {name: fingerprint(rows) for name, rows in payload.items()},
                         'manifest': metadata}), identity(after), hashlib.sha256(raw).hexdigest())


def import_reviews(declarations, payload, directory, public_pdf_sources, public_pdf_readings,
                   source_review_as_of, *, apply=False, before_write=None):
    """Only usage-evidence is writable. Caller supplies an approved cutoff.

    The CLI verifies the actual bound clock immediately before import and again
    before a write. Programmatic callers must obtain their cutoff the same way.
    """
    directory = Path(directory)
    paths = {name: _safe_file(directory / (name + '.jsonl')) for name in TABLES}
    before = {name: path.read_bytes() for name, path in paths.items()}
    authority = {name: [strict_json(line) for line in raw.splitlines() if line.strip()]
                 for name, raw in before.items()}
    merged, report = prepare_reviews(declarations, payload, authority, public_pdf_sources,
                                     public_pdf_readings, source_review_as_of)
    def guard_authority():
        if before_write is not None:
            before_write()
        if any(_safe_file(paths[name]).read_bytes() != raw for name, raw in before.items()):
            fail('authority_changed_during_import')
    if apply and report['added']['usage-evidence']:
        guard_authority()
        target = paths['usage-evidence']
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory,
                                             prefix='.pdf-hardware-', suffix='.tmp', delete=False) as output:
                temporary = Path(output.name)
                output.write(''.join(encode(row) + '\n' for row in merged['usage-evidence']))
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temporary, stat.S_IMODE(target.stat().st_mode))
            # Temp-file writing can take time. Do not overwrite an ordinary
            # concurrent edit to catalog/equipment while that write ran.
            guard_authority()
            os.replace(temporary, target)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return {**report, 'applied': apply}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--clock-config', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = args.root.absolute()
        if args.apply and args.clock_config is not None:
            chosen = args.clock_config if args.clock_config.is_absolute() else root / args.clock_config
            if chosen != root / 'config/source-review-clock.json':
                fail('apply_requires_default_approved_clock')
        payload, metadata = load_catalog(root / 'data/catalog')
        catalog_snapshot = _catalog_snapshot(root, payload, metadata)
        clock = resolve_source_review_clock(root, metadata['data_through'], args.clock_config)
        if clock['source_review_clock_digest'] is None or clock['source_review_clock']['basis'] != 'configured_bound_ledger':
            fail('configured_approved_source_clock_required')
        declarations = strict_json(_safe_file(args.input).read_bytes())
        sources = read_public_jsonl(root / 'data/hardware-review/pdf-source-observations.jsonl')
        readings = read_public_jsonl(root / 'data/hardware-review/pdf-readings.jsonl')
        def recheck_inputs():
            fresh_payload, fresh_metadata = load_catalog(root / 'data/catalog')
            if _catalog_snapshot(root, fresh_payload, fresh_metadata) != catalog_snapshot:
                fail('catalog_changed_during_import')
            if resolve_source_review_clock(root, metadata['data_through'], args.clock_config) != clock:
                fail('approved_clock_changed_during_import')
        recheck_inputs()
        result = import_reviews(declarations, payload, root / 'data/equipment', sources, readings,
                                clock['source_review_as_of'], apply=args.apply, before_write=recheck_inputs)
        print(encode(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Do not include OS filenames, raw declarations or credentials in errors.
        message = str(error) if isinstance(error, ValueError) and str(error).startswith(
            ('pdf_hardware_review:', 'pdf_reading_review:', 'source_review_clock:', 'equipment_')) else 'invalid_input_or_io'
        parser.exit(2, 'PDF hardware import failed: ' + message + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
