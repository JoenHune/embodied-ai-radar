#!/usr/bin/env python3
"""Plan bounded recovery of transient source failures; default is read-only.

Only --apply retries original requests. Extraction rules, published receipts,
authoritative facts and automatic scheduling remain unchanged.
"""
from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import math
import re
import shutil
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from collect_hardware_sources import (
    Collector, PARSER_VERSION, arxiv_identity, atomic_write, digest, encode,
    fetch_html_curl, table_rows,
)
from prepare_fulltext_reading import latest_observations, read_regular
from token_free_research import locked, read_log, relevance

ROOT = Path(__file__).resolve().parents[1]
MAX_ATTEMPTS = 3
MAX_BATCH = 200
MAX_RUN_SECONDS = 5 * 60
TARGET_FIELDS = ('work_id', 'arxiv_id', 'version', 'version_basis', 'source_url')


def runtime_resource_check(repository):
    path = repository / 'scripts/radar_resource_guard.py'
    if not path.is_file() or path.is_symlink():
        raise ValueError('apply_requires_deployed_radar_resource_guard_use_dry_run_or_explicit_repository')
    spec = importlib.util.spec_from_file_location('recovery_runtime_guard', path)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)

    def check():
        if shutil.disk_usage(repository).free < 6 * 1024 ** 3:
            return 'low_disk_space'
        return guard.reason(guard.snapshot())

    return check


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return parsed.timestamp() if parsed.tzinfo is not None else None
    except (ValueError, OverflowError, OSError):
        return None


def request_path(cache, source):
    key = digest(encode([source['work_id'], source['source_url'], PARSER_VERSION, 1500, 2]).encode())
    return cache / 'requests' / (key + '.json')


def read_request(cache, source):
    path = request_path(cache, source)
    if path.is_symlink():
        raise ValueError('symlink_request_forbidden')
    return json.loads(read_regular(path, maximum=1024 * 1024))


def valid_target(source, work):
    canonical = arxiv_identity(work.get('identifiers', {}).get('arxiv'))
    recorded = arxiv_identity(source.get('arxiv_id'))
    match = re.fullmatch(r'https://arxiv\.org/html/(\d{4}\.\d{4,5})(v\d+)?', str(source.get('source_url') or ''))
    if not canonical or not recorded or not match:
        return False
    if canonical[0] != recorded[0] or canonical[0] != match.group(1):
        return False
    # The retry uses the observed request verbatim, including an unversioned URL.
    return not match.group(2) or match.group(2) == source.get('version')


def transient_reason(source):
    code, state = source.get('http_status'), source.get('status')
    if state == 'blocked':
        return 'rate_limited' if code == 429 else 'access_block_requires_review'
    if state != 'unavailable':
        return 'already_available' if state in {'full_text_available', 'partial_text'} else 'source_review_required'
    if source.get('resolution_error'):
        return 'identity_review_required'
    if type(code) is int and 500 <= code <= 599:
        return 'server_error'
    if code in {None, 200} and source.get('transport_returncode') in {6, 7, 18, 28, 35, 52, 55, 56}:
        return 'transport_failure'
    return 'source_review_required'


def plan_recovery(catalog, cache, *, limit=8, now=None):
    if not 1 <= limit <= MAX_BATCH:
        raise ValueError('limit_must_be_between_1_and_200')
    now = time.time() if now is None else now
    observations, partial = read_log(cache / 'observations.jsonl')
    sources = latest_observations(observations)
    works = {}
    for work in table_rows(catalog, 'works'):
        if work['work_id'] in works:
            raise ValueError('duplicate_canonical_work')
        works[work['work_id']] = work
    pacing_path = cache / 'pacing.json'
    pacing = json.loads(read_regular(pacing_path, maximum=1024 * 1024)) if pacing_path.exists() else {}
    pacing_until = pacing.get('next_request_at', 0)
    if type(pacing_until) not in {int, float} or not math.isfinite(pacing_until) or pacing_until < 0:
        raise ValueError('invalid_persistent_pacing')
    blocked = sorted(wid for wid, source in sources.items()
                     if source.get('status') == 'blocked' and source.get('http_status') != 429)
    rate_limits = [source for source in sources.values()
                   if source.get('status') == 'blocked' and source.get('http_status') == 429]
    rate_limit_times = [timestamp(source.get('next_retry_at')) for source in rate_limits]
    global_reason = ('access_block_requires_review' if blocked else
                     'rate_limit_deadline_unknown' if any(value is None for value in rate_limit_times) else
                     'global_cooldown' if max([pacing_until, *rate_limit_times]) > now else None)
    rows = []
    for wid, source in sources.items():
        work = works.get(wid, {})
        kind = transient_reason(source)
        attempt = source.get('attempt')
        retry_at = timestamp(source.get('next_retry_at'))
        row = {'work_id': wid, 'title': work.get('title'), 'first_public_date': work.get('first_public_date'),
               'relevance': relevance(work), 'source_state': source.get('status'), 'http_status': source.get('http_status'),
               'observation_id': source.get('observation_id'), 'source_url': source.get('source_url'),
               'attempt': attempt, 'next_retry_at': source.get('next_retry_at'),
               'failure_kind': kind, 'eligible': False, 'selected': False, 'reason': kind}
        if kind in {'rate_limited', 'server_error', 'transport_failure'}:
            if not work or not valid_target(source, work):
                row['reason'] = 'identity_review_required'
            elif type(attempt) is not int or attempt < 1:
                row['reason'] = 'attempt_history_unknown'
            elif attempt >= MAX_ATTEMPTS:
                row['reason'] = 'retry_budget_exhausted'
            elif retry_at is None:
                row['reason'] = 'retry_deadline_unknown'
            elif global_reason:
                row['reason'] = global_reason
            elif retry_at > now:
                row['reason'] = 'target_cooldown'
            else:
                try:
                    saved = read_request(cache, source)
                    same = source.get('observation_id') and saved == source and saved.get('parser_version') == PARSER_VERSION
                    row.update(eligible=bool(same), reason='ready' if same else 'request_binding_changed')
                except (OSError, ValueError, KeyError):
                    row['reason'] = 'request_state_unavailable'
        rows.append(row)
    rows.sort(key=lambda row: (row['failure_kind'] != 'rate_limited', row['relevance'] != 'included',
                              -(int(re.sub(r'\D', '', row.get('first_public_date') or '')[:8] or 0)), row['work_id']))
    eligible = [row for row in rows if row['eligible']]
    # An expired 429 allows one same-request probe, never a batch of new targets.
    selected = ([row for row in eligible if row['failure_kind'] == 'rate_limited'][:1]
                if rate_limits else eligible[:limit])
    chosen = {row['work_id'] for row in selected}
    for row in rows:
        row['selected'] = row['work_id'] in chosen
    return {'schema_version': '1', 'mode': 'dry_run', 'generated_at': datetime.fromtimestamp(now, timezone.utc).isoformat(),
            'network_requests': 0, 'observation_tail_ignored': partial, 'total_observed_works': len(rows),
            'scope': 'previously_observed_sources_only', 'catalog_work_count': len(works),
            'never_observed_work_count': len(works.keys() - sources.keys()),
            'failure_counts': dict(Counter(row['failure_kind'] for row in rows)),
            'reason_counts': dict(Counter(row['reason'] for row in rows)),
            'eligible_count': len(eligible), 'selected_count': len(selected), 'max_attempts': MAX_ATTEMPTS,
            'max_run_seconds': MAX_RUN_SECONDS,
            'global_pause_reason': global_reason, 'blocked_work_ids': blocked,
            'global_next_request_at': pacing_until, 'rate_limit_probe_only': bool(rate_limits),
            'queue': rows}, sources


class RecoveryCollector(Collector):
    def __init__(self, cache_dir, observations, *, expected, rate_limits, resource_check=lambda: None, **kwargs):
        self.cache = Path(cache_dir).resolve()
        self.initialization = (cache_dir, observations, kwargs)
        self.expected = expected
        self.rate_limits = rate_limits
        self.checked_live_state = False
        self.resource_check = resource_check

    def run(self, targets, *, limit=8, retry_failed=True):
        # Base initialization can repair a partial observation tail. Protect it
        # with the same lock as requests, then reuse the base collect method.
        with (self.cache / 'collector.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError('Another collector owns this cache') from error
            pressure = self.resource_check()
            if pressure:
                return {'attempted': 0, 'resumed': 0, 'statuses': {}, 'status': 'paused_resource_pressure', 'reason': pressure}
            cache, observations, options = self.initialization
            super().__init__(cache, observations, **options)
            started, pause, counts, attempted, resumed = time.monotonic(), {}, Counter(), 0, 0
            for target in targets:
                if attempted >= limit:
                    break
                pressure = self.resource_check()
                if pressure:
                    pause.update(status='paused_resource_pressure', reason=pressure)
                    break
                deadline = self._pacing_state().get('next_request_at', 0)
                if deadline - self.clock() > self.interval + 1:
                    pause.update(status='paused_global_backoff', next_request_at=deadline)
                    break
                if time.monotonic() - started >= MAX_RUN_SECONDS:
                    pause.update(status='paused_time_budget')
                    break
                row, fresh = self.collect(target, retry_failed=True)
                attempted += int(fresh)
                resumed += int(not fresh)
                counts[row['status']] += 1
                if fresh and row['status'] == 'blocked':
                    break
            return {'attempted': attempted, 'resumed': resumed, 'statuses': dict(counts),
                    'observations': str(self.observations), 'manual_reviewed': False, **pause}

    def collect(self, target, *, retry_failed=False):
        # run holds collector.lock here; reject a plan changed since planning.
        if not self.checked_live_state:
            live = latest_observations(read_log(self.observations)[0])
            if any(source.get('status') == 'blocked' and source.get('http_status') != 429
                   for source in live.values()):
                raise ValueError('access_block_requires_review')
            rate_limits = {wid: source for wid, source in live.items()
                           if source.get('status') == 'blocked' and source.get('http_status') == 429}
            if rate_limits != self.rate_limits:
                raise ValueError('rate_limit_state_changed_since_plan')
            if any(live.get(wid) != source for wid, source in self.expected.items()):
                raise ValueError('observation_binding_changed_since_plan')
            self.checked_live_state = True
        saved = read_request(self.cache, target)
        if saved != self.expected[target['work_id']]:
            raise ValueError('request_binding_changed_since_plan')
        return super().collect(target, retry_failed=True)


def apply_recovery(catalog, cache, output, *, limit=8, fetcher=fetch_html_curl, resource_check=None):
    resource_check = resource_check or runtime_resource_check(catalog.parent.parent)
    pressure = resource_check()
    if pressure:
        return {'schema_version': '1', 'mode': 'apply', 'status': 'paused_resource_pressure',
                'reason': pressure, 'network_requests': 0, 'queue': []}
    with locked(output):
        plan, sources = plan_recovery(catalog, cache, limit=limit)
        selected = [row for row in plan['queue'] if row['selected']]
        if not selected:
            return {**plan, 'mode': 'apply', 'status': 'nothing_eligible'}
        expected = {row['work_id']: sources[row['work_id']] for row in selected}
        targets = [{key: source.get(key) for key in TARGET_FIELDS} for source in expected.values()]
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12]
        audit_path = output / 'recovery-runs' / (run_id + '.json')
        if audit_path.parent.is_symlink():
            raise ValueError('symlink_recovery_audit_forbidden')
        audit = {'schema_version': '1', 'run_id': run_id, 'started_at': plan['generated_at'], 'status': 'started',
                 'selected': selected, 'rate_limit_probe_only': plan['rate_limit_probe_only'],
                 'authority_modified': False, 'extraction_rules_modified': False}
        atomic_write(audit_path, (encode(audit) + '\n').encode())
        try:
            collector = RecoveryCollector(cache, cache / 'observations.jsonl', interval=15,
                                          expected=expected, fetcher=fetcher,
                                          resource_check=resource_check,
                                          rate_limits={wid: source for wid, source in sources.items()
                                                       if source.get('status') == 'blocked' and source.get('http_status') == 429})
            result = collector.run(targets, limit=len(targets), retry_failed=True)
            audit.update(status=result.get('status', 'completed'), result=result)
        except Exception as error:
            audit.update(status='failed', error_type=type(error).__name__)
            raise
        finally:
            audit['finished_at'] = datetime.now(timezone.utc).isoformat()
            atomic_write(audit_path, (encode(audit) + '\n').encode())
        return {**plan, 'mode': 'apply', 'status': audit['status'], 'network_requests': result['attempted'],
                'run_id': run_id, 'result': result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', help='Read-only recovery plan (default)')
    mode.add_argument('--apply', action='store_true', help='Retry bounded transient failures at their exact original URLs')
    parser.add_argument('--max-records', type=int, default=8)
    parser.add_argument('--repository', type=Path, default=ROOT, help='Explicit repository whose catalog and private cache to inspect')
    parser.add_argument('--summary', action='store_true', help='Print aggregate counts and selected requests only')
    args = parser.parse_args(argv)
    if not 1 <= args.max_records <= MAX_BATCH:
        parser.error('max-records must be between 1 and 200')
    repository = args.repository.absolute()
    catalog, cache, output = repository / 'data/catalog', repository / '.research/hardware-fulltext', repository / '.research/token-free-research'
    result = (apply_recovery(catalog, cache, output, limit=args.max_records) if args.apply else
              plan_recovery(catalog, cache, limit=args.max_records)[0])
    if args.summary:
        result['selected'] = [row for row in result.pop('queue') if row['selected']]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
