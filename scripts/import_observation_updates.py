"""Import reviewed official context updates without inventing research works."""
from __future__ import annotations
import argparse
import copy
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from catalog_store import fingerprint, write_if_changed
from prepare_catalog import OBSERVATION_UPDATE_TYPES

ROOT = Path(__file__).resolve().parents[1]


def normalize(rows):
    result = []
    seen = set()
    for original in rows:
        row = copy.deepcopy(original)
        if row.get('event_type') not in OBSERVATION_UPDATE_TYPES or row.get('counts_as_new_paper') is not False or row.get('counts_as_new_model') is not False:
            raise ValueError('Only explicit non-counting observation updates are allowed')
        if row.get('attribution_grade') != 'G1' or not row.get('organization_evidence') or not row.get('date_evidence'):
            raise ValueError('Official identity and publication-date proofs are required')
        for value in [row.get('url'), row.get('official_source_url'), *[x.get('url') for x in row['organization_evidence']], *[x.get('url') for x in row['date_evidence']]]:
            parsed = urlsplit(value or '')
            if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Public evidence URLs required')
        published = date.fromisoformat(row['published_at'][:10])
        observed = date.fromisoformat(row['observed_at'][:10])
        if row.get('date_precision') != 'day' or published > observed:
            raise ValueError('Invalid publication date')
        if not row.get('event_id') or row['event_id'] in seen or not row.get('title') or not row.get('summary_zh'):
            raise ValueError('Unique event ID, title and summary required')
        seen.add(row['event_id'])
        row.update(update_id=row['event_id'], update_type=row['event_type'], evidence_grade='G1',
                   evidence_layer='S', review_status='verified', curated=True,
                   original_research_eligible=row.get('original_research_eligible', row.get('research_eligible')), research_eligible=False,
                   observed_at_precision='day', first_seen_at=row['observed_at'],
                   strict_peer_reviewed=False, counts_as_new_paper=False, counts_as_new_model=False)
        result.append(row)
    return result


def merge(existing, rows):
    result = copy.deepcopy(existing)
    by_id = {r['update_id']: r for r in result}
    for row in normalize(rows):
        old = by_id.get(row['update_id'])
        if old and fingerprint(old) != fingerprint(row):
            raise ValueError('Existing observation differs; explicit revision required')
        collisions = [r for r in result if r.get('url') == row['url'] and r.get('published_at') == row['published_at'] and r['update_id'] != row['update_id']]
        if collisions:
            raise ValueError('Same source/date already registered; review before merging')
        if not old:
            result.append(row)
            by_id[row['update_id']] = row
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'data/group-updates.json'
    before = path.read_text()
    payload = json.loads(before)
    incoming = json.loads(args.input.read_text())['records']
    merged = merge(payload['updates'], incoming)
    count = len(merged) - len(payload['updates'])
    payload['updates'] = merged
    if args.apply:
        if path.read_text() != before:
            raise RuntimeError('Concurrent change to group updates')
        write_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'applied': args.apply, 'added_observations': count, 'new_papers': 0, 'new_models': 0}))


if __name__ == '__main__':
    main()
