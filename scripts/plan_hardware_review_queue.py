"""Deterministic, direction-stratified hardware source queue over the whole catalog.

Every record stays in the inventory. The first HTML batch is a processing
order, never an estimate of population hardware frequency or full coverage.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from catalog_store import load_catalog, read_table, write_if_changed, encode, fingerprint

ROOT = Path(__file__).resolve().parents[1]


def plan(payload, reviewed_ids=(), per_direction=8, controls=12, *, all_arxiv=False):
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (per_direction, controls)):
        raise ValueError('hardware_queue_limits_must_be_nonnegative_integers')
    works = payload['works']
    if len({w['work_id'] for w in works}) != len(works):
        raise ValueError('duplicate_work_identity')
    reviewed = set(reviewed_ids)
    seed = lambda w: hashlib.sha256(('hardware-census-v1|' + w['work_id']).encode()).hexdigest()
    buckets = defaultdict(list)
    for work in works:
        if not work.get('identifiers', {}).get('arxiv') or work['work_id'] in reviewed:
            continue
        buckets[(work.get('relevance', {}).get('status', 'unknown'), work.get('primary_direction') or 'unassigned')].append(work)
    picked, ids = [], set()
    def take(work, reason):
        if work['work_id'] in ids:
            return
        ids.add(work['work_id'])
        picked.append({'work_id': work['work_id'], 'title': work['title'], 'arxiv_id': work['identifiers']['arxiv'],
                       'relevance_status': work.get('relevance', {}).get('status'), 'primary_direction': work.get('primary_direction'),
                       'first_public_date': work.get('first_public_date'), 'selection_reason': reason})
    # Both recent and deterministic spread samples in every primary direction,
    # irrespective of whether a known model appears in the abstract.
    selections = {}
    directions = [f'D{i}' for i in range(1, 16)]
    directions += sorted({direction for state, direction in buckets if state == 'included'} - set(directions))
    for direction in directions:
        group = buckets.get(('included', direction), [])
        latest = sorted(group, key=lambda w: (w.get('first_public_date') or '', w['work_id']), reverse=True)
        spread = sorted(group, key=seed)
        chosen = latest[:per_direction // 2]
        chosen_ids = {w['work_id'] for w in chosen}
        chosen += [w for w in spread if w['work_id'] not in chosen_ids][:per_direction-len(chosen)]
        selections[direction] = chosen
    for offset in range(per_direction):
        for direction, values in selections.items():
            if offset < len(values):
                take(values[offset], f'direction_stratified:{direction}:' + ('recent' if offset < per_direction // 2 else 'stable_spread'))
    states = ['candidate', 'manual_review', 'excluded']
    states += sorted({state for state, _ in buckets if state != 'included'} - set(states))
    for relevance in states:
        values = [w for (state, _), group in buckets.items() if state == relevance for w in group]
        for work in sorted(values, key=seed)[:controls]:
            take(work, 'relevance_control:' + relevance)
    if all_arxiv:
        # The stratified batch is only a useful processing prefix. A prior
        # verified device relationship is not proof of whole-paper coverage,
        # so every arXiv-backed work joins the resumable backlog, including
        # works omitted from that prefix because they had prior usage evidence.
        for work in sorted(works, key=lambda work: work['work_id']):
            if work.get('identifiers', {}).get('arxiv'):
                take(work, 'full_arxiv_backlog')
    return {'schema_version': '1', 'policy_version': '1', 'catalog_work_count': len(works),
            'work_set_hash': fingerprint(sorted(w['work_id'] for w in works)),
            'scope': ('full_canonical_arxiv_processing_queue_not_fulltext_coverage' if all_arxiv else
                      'initial_processing_batch_not_full_coverage_or_population_sample'),
            'queue_mode': 'all_arxiv' if all_arxiv else 'stratified_initial_batch',
            'arxiv_eligible_work_count': sum(bool(w.get('identifiers', {}).get('arxiv')) for w in works),
            'non_arxiv_work_count': sum(not w.get('identifiers', {}).get('arxiv') for w in works),
            'note': '正文获取次序，不以热门型号/摘要命中作唯一入口；非arxiv来源仍在全库覆盖账本待处理。',
            'already_had_verified_usage': len(reviewed), 'queue': picked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--per-direction', type=int, default=8)
    parser.add_argument('--controls', type=int, default=12)
    parser.add_argument('--all-arxiv', action='store_true', help='Append every canonical arXiv work after the stratified prefix; does not fetch sources')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    payload, _ = load_catalog(ROOT / 'data/catalog')
    verified = {r['work_id'] for r in read_table(ROOT / 'data/equipment', 'usage-evidence') if r.get('review_status') == 'verified'}
    result = plan(payload, verified, args.per_direction, args.controls, all_arxiv=args.all_arxiv)
    write_if_changed(args.output, encode(result) + '\n')
    print(json.dumps({'queue': len(result['queue']), 'catalog_works': result['catalog_work_count'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
