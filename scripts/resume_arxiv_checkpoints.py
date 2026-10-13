"""Validate exact cutoff/query checkpoints against cached Atom before merging."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import date
from pathlib import Path

from radar_common import ROOT
from weekly_runtime import owned_resume
from run_weekly_v3 import STAGED_PATHS, collection_months, merge_records, read_json, write_json, _query_window


def validated_checkpoint_records(root, cutoff, collector):
    registry = read_json(root / 'config/source-registry.json')
    scope = hashlib.sha256(json.dumps(registry['arxiv_sources'], sort_keys=True).encode()).hexdigest()[:16]
    folder = root / 'data/raw/arxiv-v2/weekly' / (cutoff.isoformat() + '-' + scope)
    expected, verified, evidence = {}, {}, []
    for month in collection_months(cutoff):
        for query in registry['arxiv_sources']['queries']:
            identity = hashlib.sha256(json.dumps({'query': query, 'month': month, 'cutoff': cutoff.isoformat(), 'schema': 1}, sort_keys=True).encode()).hexdigest()
            expected[identity] = (month, query)
    for path in sorted(folder.glob('*.checkpoint.json')):
        identity = path.name.removesuffix('.checkpoint.json')
        if path.is_symlink() or identity not in expected:
            raise ValueError('Unknown or nonregular checkpoint query identity')
        checkpoint = read_json(path)
        if checkpoint.get('identity') != identity:
            raise ValueError('Checkpoint identity mismatch')
        month, query = expected[identity]
        records, offset, total = checkpoint['records'], checkpoint['offset'], checkpoint['total']
        if type(offset) is not int or offset != len(records) or (records and (type(total) is not int or offset > total)):
            raise ValueError('Checkpoint pagination mismatch')
        if not records:
            continue
        raw, raw_hashes = {}, []
        window = _query_window(month, cutoff)
        cache_until = window['until'].replace('-', '')
        for xml in sorted(folder.glob(f"{month}-{query['id']}-*-to-{cache_until}.xml")):
            if xml.is_symlink():
                raise ValueError('Nonregular Atom cache')
            body = xml.read_text()
            advertised, parsed = collector.parse_feed(body)
            if advertised != total:
                raise ValueError('Atom total conflicts with checkpoint')
            for row in parsed:
                if row['arxiv_id'] in raw:
                    raise ValueError('Duplicate Atom pagination identity')
                raw[row['arxiv_id']] = row
            raw_hashes.append({'file': str(xml.relative_to(root)), 'sha256': hashlib.sha256(body.encode()).hexdigest()})
        ids = set()
        for row in records:
            key = row.get('arxiv_id')
            if key in ids or key not in raw or any(row.get(field) != value for field, value in raw[key].items()):
                raise ValueError('Checkpoint source metadata or identity conflicts with Atom')
            if not window['from'] <= row['first_submitted'] <= window['until']:
                raise ValueError('Checkpoint record is outside its submitted-date query window')
            if query['id'] == 'cs_ro' and 'cs.RO' not in row['categories']:
                raise ValueError('Core robotics query has an incompatible category')
            if query['id'] != 'cs_ro' and not set(row['categories']) & {'cs.AI', 'cs.CV', 'cs.LG'}:
                raise ValueError('Cross-list query has incompatible categories')
            ids.add(key)
            verified[key] = collector.merge_record(verified.get(key, {}), copy.deepcopy(row), query['id'])
        evidence.append({'query_id': query['id'], 'month': month, 'offset': offset, 'expected_records': total,
                         'checkpoint_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'raw': raw_hashes})
    return verified, evidence


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--as-of', type=date.fromisoformat, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    import collect_arxiv_v2 as collector
    if not owned_resume(ROOT, STAGED_PATHS):
        raise SystemExit('Recorded source inputs changed; refusing checkpoint merge')
    incoming, evidence = validated_checkpoint_records(ROOT, args.as_of, collector)
    existing = read_json(ROOT / 'data/preprints.json', [])
    previous_ids = {row['arxiv_id'] for row in existing}
    collector.classify(list(incoming.values()))
    merged = merge_records(existing, list(incoming.values()), 'arxiv_id')
    summary = {'status': 'validated', 'cutoff': args.as_of.isoformat(), 'unique_checkpoint_records': len(incoming),
               'added_unique': len(set(incoming) - previous_ids), 'before': len(existing), 'after': len(merged),
               'last_first_submitted': max((row['first_submitted'] for row in incoming.values()), default=None),
               'registered_scope_complete': False, 'evidence': evidence}
    if args.apply:
        backup = ROOT / '.research/weekly-v3' / args.as_of.isoformat() / 'before-checkpoint-merge'
        backup.mkdir(exist_ok=False)
        for name in ['data/preprints.json', '.research/weekly-v3/owned-resume.json']:
            (backup / Path(name).name).write_bytes((ROOT / name).read_bytes())
        write_json(ROOT / 'data/preprints.json', merged, compact=True)
        if not owned_resume(ROOT, STAGED_PATHS, save=True):
            raise RuntimeError('Cannot record merged source ownership')
        summary['status'] = 'merged'
        write_json(backup / 'merge-receipt.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
