#!/usr/bin/env python3
"""Dry-run explicit AI classification reviews; --apply is the only write path.

No acquisition, model requests, broad finalize_facts or clock updates. A dry
run may preview an explicit later review clock. Applying requires that clock
already match the repository's approved, ledger-bound configuration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from catalog_store import load_catalog, save_catalog, fingerprint
from fulltext_classification_reviews import apply_classification_reviews, audit_classification_reviews, SOURCE_TYPE
from source_review_clock import resolve_source_review_clock

ROOT = Path(__file__).resolve().parents[1]


def _json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    def constant(_):
        raise ValueError('nonfinite_json_number')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def _read(path, *, jsonl=False):
    if path.is_symlink() or not path.is_file():
        raise ValueError('regular_input_file_required')
    raw = path.read_bytes()
    return ([_json(line) for line in raw.splitlines() if line.strip()] if jsonl else _json(raw)), hashlib.sha256(raw).hexdigest()


def import_file(args):
    catalog = args.catalog.absolute()
    if catalog.is_symlink() or not catalog.is_dir():
        raise ValueError('regular_catalog_directory_required')
    payload, metadata = load_catalog(catalog)
    original_digest = fingerprint(payload)
    data_through = args.data_through or metadata['data_through']
    root = catalog.parent.parent
    document, input_hash = _read(args.input)
    readings, readings_hash = _read(args.readings, jsonl=True)
    observations, observations_hash = _read(args.observations, jsonl=True)
    conflicts, conflicts_hash = _read(args.conflicts, jsonl=True)
    clock = resolve_source_review_clock(root, data_through)
    review_as_of = args.source_review_as_of or clock['source_review_as_of']
    result = apply_classification_reviews(payload, document, readings, observations, data_through=data_through,
                                          source_review_as_of=review_as_of, conflicts=conflicts)
    audit = audit_classification_reviews(result, readings, observations, data_through=data_through,
                                        source_review_as_of=review_as_of, conflicts=conflicts)
    old_reviews = sum(r.get('source_type') == SOURCE_TYPE for r in payload['source-records'])
    new_reviews = sum(r.get('source_type') == SOURCE_TYPE for r in result['source-records'])
    if args.apply:
        if review_as_of != clock['source_review_as_of'] or data_through != metadata['data_through']:
            raise ValueError('apply_requires_approved_clock_and_unchanged_catalog_cutoff')
        # Custom public ledger paths are useful for dry-run fixtures, but must
        # not substitute unbound proof for an authoritative apply.
        expected = {'readings': root / 'data/hardware-review/fulltext-readings.jsonl',
                    'observations': root / 'data/hardware-review/source-observations.jsonl',
                    'conflicts': root / 'data/editorial/source-content-conflicts.jsonl'}
        if any(getattr(args, key).resolve() != path.resolve() for key, path in expected.items()):
            raise ValueError('apply_requires_bound_public_ledger_paths')
        if fingerprint(load_catalog(catalog)[0]) != original_digest or resolve_source_review_clock(root, data_through) != clock:
            raise ValueError('catalog_or_clock_changed_before_apply')
        for path, digest in ((args.input, input_hash), (args.readings, readings_hash),
                             (args.observations, observations_hash), (args.conflicts, conflicts_hash)):
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('review_input_changed_before_apply')
        if result != payload:
            save_catalog(catalog, result, metadata)
    return {**audit, 'applied': bool(args.apply), 'dry_run': not args.apply,
            'added_review_records': new_reviews - old_reviews, 'catalog_work_count': len(result['works']),
            'work_id_set_unchanged': {w['work_id'] for w in result['works']} == {w['work_id'] for w in payload['works']},
            'preview_clock_matches_approved': review_as_of == clock['source_review_as_of'],
            'input_sha256': input_hash, 'result_catalog_payload_hash': fingerprint(result)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'data/catalog')
    parser.add_argument('--readings', type=Path, default=ROOT / 'data/hardware-review/fulltext-readings.jsonl')
    parser.add_argument('--observations', type=Path, default=ROOT / 'data/hardware-review/source-observations.jsonl')
    parser.add_argument('--conflicts', type=Path, default=ROOT / 'data/editorial/source-content-conflicts.jsonl')
    parser.add_argument('--data-through')
    parser.add_argument('--source-review-as-of', help='Explicit preview watermark; apply must match approved configuration')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = import_file(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, 'Fulltext classification import failed: ' + str(error) + '\n')
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
