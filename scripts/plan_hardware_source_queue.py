#!/usr/bin/env python3
"""Offline, lossless inventory planning and bounded first-fetch queues.

Never instantiate Collector. Never fetch, repair a log, change relevance or
retry state. --dry-run is wholly read-only; otherwise --output-dir must be new.
The inventory is NOT executable: only first-fetch.json excludes all hold lanes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import sys
from collections import Counter, defaultdict, deque
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True
from catalog_store import TABLES, encode, fingerprint
from collect_hardware_sources import PARSER_VERSION, arxiv_identity, load_targets, transport_incomplete
from organization_coverage import attribution_valid
from refresh_hardware_source_scans import trusted_path
from snapshot_hardware_sources import (MAX_LOG_BYTES, MAX_OBJECT_BYTES, STATUSES,
    _incomplete_object_prefix, strict_json, safe_url, timestamp)

PRIORITIES = ['P0_current_month_selected', 'P2_current_month_topic_review',
    'P1_window_T0_topic_review', 'P3_window_monthly_selected', 'P4_window_included',
    'P5_window_topic_review', 'P6_window_scope_review', 'P7_older_included',
    'P8_older_scope_review', 'P9_excluded_retained']
HOLDS = ['R0_attempted_needs_repair_or_retry', 'Z0_same_version_full_or_read',
    'Z2_cache_or_read_without_success_state', 'Z1_other_version_full_or_read',
    'H0_unknown_target_version', 'H1_historical_version_review', 'H2_future_date']
HINT = re.compile(r'robot|embodied|humanoid|loco|manipulat|tactile|\bVLA\b|world.model|grasp|teleoperat|dexter|policy|control|real2sim|bimanual', re.I)
VERSION = re.compile(r'v[1-9]\d*\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')


class PlanError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise PlanError(reason)


def day(value):
    require(isinstance(value, str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)), 'invalid_date')
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise PlanError('invalid_date') from None


def month_window(as_of):
    when = day(as_of)
    number = when.year * 12 + when.month - 1
    return [f'{n // 12:04d}-{n % 12 + 1:02d}' for n in range(number - 12, number + 1)]


def work_month(work):
    precision, value = work.get('first_public_date_precision'), work.get('first_public_date')
    require(precision in {'day', 'month', 'year', 'unknown'}, 'invalid_work_date_precision')
    if value is None:
        require(precision == 'unknown', 'missing_work_date')
        return None
    if precision == 'month' and isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}', value):
        day(value + '-01')  # Validate a declared month, not an inferred day.
        return value
    if precision == 'year' and isinstance(value, str) and re.fullmatch(r'\d{4}', value):
        day(value + '-01-01')
        return None
    day(value)  # Do not silently turn a damaged date into an unknown month.
    return value[:7] if precision in {'day', 'month'} else None


class Inputs:
    """Stable small inputs are hashed; HTML bytes are deliberately not read."""
    def __init__(self):
        self.files = {}

    def raw(self, path):
        path = Path(path)
        require(not path.is_symlink() and path.is_file(), 'input_not_regular_file')
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        require(signature(before) == signature(after), 'input_changed_during_read')
        self.files[str(path.resolve())] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        return data

    def json(self, path):
        return strict_json(self.raw(path))

    def jsonl(self, path):
        for line in self.raw(path).splitlines():
            if line.strip():
                row = strict_json(line)
                require(isinstance(row, dict), 'jsonl_record_not_object')
                yield row


def read_catalog(path, inputs):
    metadata = inputs.json(path / 'manifest.json')
    payload = {}
    for table, key in TABLES.items():
        directory = path / table
        paths = sorted(directory.glob('*.jsonl')) if directory.is_dir() else [path / f'{table}.jsonl']
        required = table in {'works', 'text-snapshots', 'organizations', 'work-organization-links',
                             'manifestations', 'source-records', 'evidence-events'}
        if not required and len(paths) == 1 and not paths[0].exists():
            payload[table] = []
            continue
        require(bool(paths) and all(p.is_file() for p in paths), 'catalog_table_missing:' + table)
        rows = [row for file in paths for row in inputs.jsonl(file)]
        if key:
            ids = [row.get(key) for row in rows]
            require(all(isinstance(value, str) and value for value in ids) and len(set(ids)) == len(ids),
                    'catalog_identity_missing_or_duplicate:' + table)
        payload[table] = rows
    return payload, metadata


def log_snapshot(path, consume):
    """Parse one descriptor-bound fixed prefix incrementally; no tail repair."""
    path = Path(path)
    require(not path.is_symlink(), 'observation_log_is_symlink')
    digest, count, ignored = hashlib.sha256(), 0, False
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_LOG_BYTES, 'invalid_observation_log')
        remaining = before.st_size
        while remaining:
            line = stream.readline(min(remaining, MAX_OBJECT_BYTES + 1))
            require(bool(line) and len(line) <= MAX_OBJECT_BYTES, 'log_truncated_or_record_too_large')
            remaining -= len(line)
            digest.update(line)
            if not line.strip():
                continue
            try:
                row = strict_json(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                if not remaining and not line.endswith(b'\n') and _incomplete_object_prefix(line):
                    ignored = True
                    continue
                raise PlanError('observation_log_corrupt') from None
            require(isinstance(row, dict), 'observation_not_object')
            consume(row)
            count += 1
        after, current = os.fstat(stream.fileno()), path.stat()
        require(after.st_size >= before.st_size and (before.st_dev, before.st_ino) ==
                (current.st_dev, current.st_ino), 'observation_log_replaced_or_truncated')
    return {'bytes': before.st_size, 'sha256': digest.hexdigest(), 'records': count,
            'incomplete_tail_ignored': ignored, 'path': str(path.resolve())}


def source_record(row, works):
    wid = row.get('work_id')
    require(wid in works, 'source_unknown_work_id')
    require(row.get('status') in STATUSES, 'invalid_source_status')
    canonical = arxiv_identity(works[wid].get('identifiers', {}).get('arxiv'))
    require(row.get('arxiv_id') == (canonical[0] if canonical else None), 'source_identity_mismatch')
    version = row.get('version')
    require(version is None or isinstance(version, str) and VERSION.fullmatch(version), 'invalid_source_version')
    for key in ('source_url', 'effective_url'):
        url = row.get(key)
        require(safe_url(url), 'invalid_source_url')
        if url:
            identity = arxiv_identity(url)
            if key == 'source_url' or row['status'] == 'full_text_available':
                require(canonical and identity and identity[0] == canonical[0], 'source_identity_mismatch')
                if row['status'] == 'full_text_available':
                    require(not identity[1] or identity[1] == version, 'source_identity_mismatch')
    if row.get('source_url') is None:
        require(not canonical and row['status'] == 'unavailable', 'source_url_missing')
    for key in ('observed_at', 'next_retry_at'):
        if row.get(key) is not None:
            timestamp(row[key])
    require(row.get('observed_at') is not None, 'source_observation_date_missing')


def cache_index(cache, observations, readings_path, works, inputs, min_body, min_sections):
    full, read, attempted = defaultdict(set), defaultdict(set), defaultdict(list)
    states, cache_issues, legacy_states, carried_failures = {}, [], [], []
    log_record_digests = set()
    checked_refs = {}

    def consume(row):
        source_record(row, works)
        wid = row['work_id']
        attempted[wid].append({'source_url': row.get('source_url'), 'version': row.get('version'),
                               'status': row['status'], 'observed_at': row['observed_at']})
        ref = row.get('cache_ref')
        if row['status'] != 'full_text_available' or transport_incomplete(row) or row.get('transport_verification') == 'incomplete':
            return
        require(isinstance(row.get('raw_sha256'), str) and HASH.fullmatch(row['raw_sha256']), 'full_source_hash_missing')
        if not ref:
            cache_issues.append({'work_id': wid, 'reason': 'full_observation_without_cache_reference'})
            return
        if ref not in checked_refs:
            resolved = trusted_path(ref, cache)
            require(not cache.is_symlink(), 'cache_root_is_symlink')
            exists = resolved.is_file()
            if exists:
                require(resolved.stat().st_size > 0 and resolved.stat().st_size <= MAX_OBJECT_BYTES, 'invalid_cached_object_size')
            checked_refs[ref] = exists
        if checked_refs[ref]:
            full[wid].add(row.get('version'))
        else:
            cache_issues.append({'work_id': wid, 'reason': 'cached_object_missing'})

    def consume_log(row):
        consume(row)
        log_record_digests.add(fingerprint(row))

    log = log_snapshot(observations, consume_log)
    requests = cache / 'requests'
    require(requests.is_dir() and not requests.is_symlink(), 'request_state_directory_missing_or_symlink')
    for path in sorted(requests.glob('*.json')):
        row = inputs.json(path)
        require(isinstance(row, dict), 'request_state_not_object')
        source_record(row, works)
        thresholds = row.get('thresholds')
        if thresholds is None:
            # Network / HTTP failures happen before assess_html adds thresholds.
            # Only the explicitly supplied planning parameters may prove this
            # saved key. Do not guess other parameters or rewrite the state.
            body, sections = min_body, min_sections
            legacy_states.append({'work_id': row['work_id'], 'state_file': path.name,
                                  'binding': 'filename_verified_with_explicit_planner_parameters'})
        else:
            require(isinstance(thresholds, dict), 'request_state_parameters_invalid')
            body, sections = thresholds.get('min_body_characters'), thresholds.get('min_sections')
        require(type(body) is int and body >= 0 and type(sections) is int and sections >= 0 and
                isinstance(row.get('parser_version'), str), 'request_state_parameters_invalid')
        key = fingerprint([row['work_id'], row.get('source_url'), row['parser_version'], body, sections])
        current_key = fingerprint([row['work_id'], row.get('source_url'), PARSER_VERSION, min_body, min_sections])
        # prepare_private_cache copies unchanged failed observations into the
        # current parser's key so a parser upgrade does not trigger a retry.
        # Bind both the exact existing log record and current key; never treat
        # this legacy carry-forward as a fresh parse or a successful request.
        carried = (path.stem != key and row['status'] in {'unavailable', 'blocked', 'identity_mismatch'} and
                   row['parser_version'] != PARSER_VERSION and path.stem == current_key and
                   fingerprint(row) in log_record_digests)
        require(path.stem == key or carried, 'request_state_identity_mismatch')
        if carried:
            carried_failures.append({'work_id': row['work_id'], 'state_file': path.name,
                'observation_parser': row['parser_version'], 'state_key_parser': PARSER_VERSION,
                'binding': 'exact_existing_failed_log_record_and_current_parameter_key'})
        consume(row)
        if carried or row['parser_version'] == PARSER_VERSION and body == min_body and sections == min_sections:
            states[(row['work_id'], row.get('source_url'))] = row
    reading_ids = set()
    for row in inputs.jsonl(readings_path):
        wid, version, rid = row.get('work_id'), row.get('version'), row.get('reading_id')
        require(wid in works and isinstance(rid, str) and rid not in reading_ids, 'reading_identity_unknown_or_duplicate')
        reading_ids.add(rid)
        require(row.get('reading_status') in {'completed', 'prepared', 'in_progress'}, 'invalid_reading_status')
        if row['reading_status'] != 'completed':
            continue
        require(isinstance(version, str) and VERSION.fullmatch(version), 'completed_reading_version_missing')
        identity, canonical = arxiv_identity(row.get('source_url')), arxiv_identity(works[wid].get('identifiers', {}).get('arxiv'))
        require(safe_url(row.get('source_url')) and identity and canonical and identity[0] == canonical[0] and
                (not identity[1] or identity[1] == version), 'reading_source_identity_mismatch')
        timestamp(row.get('read_completed_at'))
        read[wid].add(version)
    return {'full': full, 'read': read, 'attempted': attempted, 'states': states,
            'cache_issues': cache_issues, 'log': log, 'checked_cache_references': len(checked_refs),
            'legacy_states_without_thresholds': legacy_states, 'legacy_carried_failures': carried_failures}


def monthly_selection(directory, months, payload, inputs, as_of):
    # Rebuild using today's catalog and existing snapshot facts, not an assertion
    # that the saved monthly output is fresh. No LLM/request function is called.
    from generate_v3_editorial import build_evidence_packet
    cards, provenance = [], []
    for month in months:
        path = directory / f'{month}.json'
        if not path.exists():
            provenance.append({'month': month, 'status': 'missing_local_snapshot'})
            continue
        snapshot = inputs.json(path)
        require(snapshot.get('month') == month, 'monthly_snapshot_month_mismatch')
        cutoff = snapshot.get('data_through')
        if cutoff:
            require(day(cutoff) <= day(as_of), 'monthly_snapshot_after_plan_date')
        packet = build_evidence_packet(snapshot, payload)
        require(packet.get('month') == month, 'monthly_packet_month_mismatch')
        linked_cards, unlinked_events = [], 0
        for row in packet['evidence_cards']:
            if row.get('work_id') is None and row.get('kind') == 'event':
                unlinked_events += 1
            else:
                require(isinstance(row.get('work_id'), str), 'monthly_work_card_missing_identity')
                linked_cards.append({**row, 'selected_month': month})
        cards.extend(linked_cards)
        provenance.append({'month': month, 'status': 'rebuilt_from_local_snapshot_and_current_catalog',
            'path': str(path.resolve()), 'snapshot_sha256': inputs.files[str(path.resolve())]['sha256'],
            'snapshot_data_through': cutoff, 'revision': snapshot.get('revision'),
            'evidence_as_of': snapshot.get('evidence_as_of'), 'packet_sha256': fingerprint(packet),
            'work_cards': sum(row.get('kind') == 'work' for row in packet['evidence_cards']),
            'cards': len(packet['evidence_cards']), 'events_without_work_not_queued': unlinked_events,
            'not_claimed_latest_selected': True})
    return cards, provenance


def arrange(records):
    groups = defaultdict(list)
    for row in records:
        groups[row['bucket']].append(row)
    for rows in groups.values():
        rows.sort(key=lambda row: (-int((row['month'] or '0000-00').replace('-', '')),
            {'included': 0, 'manual_review': 1, 'candidate': 2, 'excluded': 3}[row['relevance']], row['original_rank']))
    result = list(groups[PRIORITIES[0]])
    queues = [deque(groups[key]) for key in PRIORITIES[1:3]]
    while any(queues):
        for queue in queues:
            if queue:
                result.append(queue.popleft())
    for bucket in PRIORITIES[3:] + HOLDS:
        result.extend(groups[bucket])
    return result


def plan(queue, payload, targets, index, cards, *, as_of, limit):
    require(type(limit) is int and limit > 0, 'limit_must_be_positive_integer')
    require(isinstance(queue, dict) and isinstance(queue.get('queue'), list), 'queue_object_required')
    original = queue['queue']
    require(all(isinstance(row, dict) and isinstance(row.get('work_id'), str) for row in original), 'job_object_required')
    ids = [row['work_id'] for row in original]
    require(len(set(ids)) == len(ids), 'duplicate_queue_id')
    works = {row['work_id']: row for row in payload['works']}
    require(len(works) == len(payload['works']), 'duplicate_canonical_id')
    require(set(ids) <= works.keys(), 'unknown_queue_id')
    require(set(targets) == set(ids), 'resolved_target_set_mismatch')
    months, current = month_window(as_of), as_of[:7]
    organizations = {row['organization_id']: row for row in payload['organizations']}
    t0, selected, historical = defaultdict(list), defaultdict(set), []
    for work in works.values():
        work_month(work)
        require(work.get('relevance', {}).get('status') in {'included', 'candidate', 'manual_review', 'excluded'}, 'invalid_relevance_status')
    for link in payload['work-organization-links']:
        wid, oid = link.get('work_id'), link.get('organization_id')
        require(wid in works and oid in organizations, 'unknown_organization_link_identity')
        org = organizations[oid]
        if org.get('tier') == 'T0' and attribution_valid(link, works[wid], org):
            t0[wid].append({key: link.get(key) for key in ('organization_id', 'evidence_grade', 'evidence_url')})
    seen = set()
    for card in cards:
        wid, month, version = card.get('work_id'), card.get('selected_month'), card.get('text_version')
        require(wid in works and month in months, 'monthly_card_identity_or_month_invalid')
        require(version is None or isinstance(version, str) and VERSION.fullmatch(version), 'monthly_card_version_invalid')
        selected[wid].add(month)
        if wid not in targets or (wid, month, version) in seen:
            continue
        seen.add((wid, month, version))
        available = index['full'].get(wid, set()) | index['read'].get(wid, set())
        if not version or version != targets[wid]['version'] and version not in available:
            historical.append({'work_id': wid, 'month': month, 'required_version': version,
                'current_target_version': targets[wid]['version'], 'text_snapshot_ids': card.get('text_snapshot_ids', []),
                'action': 'resolve_historical_metadata_before_fetch' if not version else 'separate_explicit_version_job_after_review'})
    historical_ids = {row['work_id'] for row in historical}
    records = []
    for rank, job in enumerate(original, 1):
        wid, work, target = job['work_id'], works[job['work_id']], targets[job['work_id']]
        require(not target.get('resolution_error') and target.get('arxiv_id'), 'queue_without_canonical_arxiv_identity')
        # Collector ignores source_url in jobs. Reject contradictions instead of
        # preserving a misleading field while scheduling a different URL.
        if job.get('source_url') is not None:
            require(job['source_url'] == target['source_url'], 'job_source_url_resolution_mismatch')
        month, relevance = work_month(work), work['relevance']['status']
        full, read = index['full'].get(wid, set()), index['read'].get(wid, set())
        state = index['states'].get((wid, target['source_url']))
        version, hint = target['version'], bool(HINT.search(work.get('title', '')))
        same = bool(version and version in full | read)
        recent = month in months
        if same:
            bucket = 'Z0_same_version_full_or_read' if state and state['status'] == 'full_text_available' else 'Z2_cache_or_read_without_success_state'
            reason = '同版已有缓存或已完成阅读；不重复获取，缺成功请求状态时单列修复。'
        elif full or read:
            bucket, reason = 'Z1_other_version_full_or_read', '其他或未明确版本已有全文/阅读；不能代替本版，也不自动重抓。'
        elif index['attempted'].get(wid) or state:
            bucket, reason = 'R0_attempted_needs_repair_or_retry', '已有来源尝试；修复与失败重试单列，保持原冷却规则。'
        elif not version:
            bucket, reason = 'H0_unknown_target_version', '目标版本未明确，暂不进入首次取文子队列；未猜测版本。'
        elif wid in historical_ids:
            bucket, reason = 'H1_historical_version_review', '月报历史版本未知或与当前目标不同；先核验，不改版本绕过状态。'
        elif month and work['first_public_date'] > as_of:
            bucket, reason = 'H2_future_date', '已存日期晚于规划日期；保留，不在本次范围内获取。'
        elif relevance == 'excluded':
            bucket, reason = 'P9_excluded_retained', '保留原队列范围内的已排除工作；取文不改变相关性。'
        elif current in selected[wid]:
            bucket, reason = 'P0_current_month_selected', '本地当月证据包已选且尚未尝试获取。'
        elif recent and t0[wid] and hint:
            bucket, reason = 'P1_window_T0_topic_review', '近窗可靠T0归属并有机器人主题线索，优先取文复核。'
        elif month == current and hint:
            bucket, reason = 'P2_current_month_topic_review', '当月机器人主题线索，优先复核而非自动纳入。'
        elif recent and selected[wid]:
            bucket, reason = 'P3_window_monthly_selected', '最近完整月份的本地证据包已选，优先补正文。'
        elif recent and relevance == 'included':
            bucket, reason = 'P4_window_included', '近窗已纳入工作完整覆盖。'
        elif recent and hint:
            bucket, reason = 'P5_window_topic_review', '近窗主题线索，保持原相关性状态。'
        elif recent:
            bucket, reason = 'P6_window_scope_review', '近窗范围复核，仅同组并不保证机器人相关。'
        elif relevance == 'included':
            bucket, reason = 'P7_older_included', '历史或日期不明的已纳入工作仍保留回填。'
        else:
            bucket, reason = 'P8_older_scope_review', '历史或日期不明的其他工作保留全量。'
        records.append({'work_id': wid, 'title': work.get('title'), 'bucket': bucket, 'reason': reason,
            'original_rank': rank, 'month': month, 'date': work.get('first_public_date'),
            'date_precision': work.get('first_public_date_precision'), 'relevance': relevance,
            'primary_direction': work.get('primary_direction'), 'T0': t0[wid], 'title_topic_hint_only': hint,
            'T0_priority_guaranteed': bucket == 'P1_window_T0_topic_review', 'monthly_selected': sorted(selected[wid]),
            'target': copy.deepcopy(target), 'cached_full_versions': sorted(full, key=lambda v: v or ''),
            'completed_read_versions': sorted(read), 'request_status': state.get('status') if state else None,
            'next_retry_at': state.get('next_retry_at') if state else None})
    ordered = arrange(records)
    by_id = {row['work_id']: row for row in original}
    inventory = copy.deepcopy(queue)
    inventory['queue'] = [copy.deepcopy(by_id[row['work_id']]) for row in ordered]
    candidates = [row for row in ordered if row['bucket'] in PRIORITIES]
    executable = candidates[:limit]
    selected_ids = {row['work_id'] for row in executable}
    first_fetch = {'schema_version': queue.get('schema_version', '1'), 'queue_mode': 'bounded_first_fetch',
        'scope': queue.get('scope'), 'queue': [copy.deepcopy(by_id[row['work_id']]) for row in executable],
        'source_scope': queue.get('scope'), 'research_eligibility_unchanged': True}
    require(len(inventory['queue']) == len(original) and set(by_id) == {row['work_id'] for row in inventory['queue']}, 'inventory_reconciliation_failed')
    require(all(row == by_id[row['work_id']] for row in inventory['queue']) and selected_ids <= set(by_id), 'job_fields_changed')
    current_rows = [row for row in ordered if row['month'] == current]
    current_unattempted = [row for row in current_rows if not index['attempted'].get(row['work_id']) and
                           not index['full'].get(row['work_id']) and not index['read'].get(row['work_id'])]
    known = sum(bool(row['target'].get('version')) for row in current_unattempted)
    report = {'schema_version': '1', 'policy_version': 'first-fetch-v3', 'status': 'planned_not_activated',
        'as_of': as_of, 'complete_months': months[:-1], 'provisional_month': current, 'limit': limit,
        'source_scope': queue.get('scope'), 'catalog_work_count': len(works), 'original_jobs': len(original),
        'inventory_jobs': len(ordered), 'first_fetch_eligible': len(candidates), 'first_fetch_jobs': len(executable),
        'deferred_by_limit': len(candidates) - len(executable), 'hold_jobs': len(ordered) - len(candidates),
        'missing_ids': 0, 'added_ids': 0, 'duplicate_ids': 0, 'all_original_job_fields_preserved': True,
        'work_id_set_sha256': fingerprint(sorted(by_id)), 'bucket_counts': dict(Counter(row['bucket'] for row in ordered)),
        'unknown_target_version_count': sum(not row['target'].get('version') for row in ordered),
        'current_month_version_coverage': {'month': current, 'unattempted_without_full_or_read': len(current_unattempted),
            'known_target_version': known, 'unknown_target_version': len(current_unattempted) - known,
            'known_ratio': known / len(current_unattempted) if current_unattempted else None,
            'first_fetch_selected': sum(row['month'] == current for row in executable)},
        'coverage_by_month_relevance': dict(Counter(f"{row['month'] or 'unknown'}|{row['relevance']}|{row['bucket']}" for row in ordered)),
        'first20': executable[:20], 'historical_version_task_count': len(historical),
        'historical_actions': dict(Counter(row['action'] for row in historical)),
        'priority_is_not_relevance_approval': True, 'planning_is_not_fulltext_verification': True,
        'requires_fresh_replan_before_execution': True, 'collector_started': False,
        'retry_policy': 'No retries scheduled; existing backoff and next_retry_at unchanged.',
        'inventory_warning': 'Inventory includes holds. Never pass inventory.json to Collector; use only first-fetch.json after current batch ends and inputs are rechecked.'}
    inventory['source_queue_plan'] = {'policy_version': 'first-fetch-v3', 'executable': False, 'as_of': as_of,
                                     'work_id_set_sha256': report['work_id_set_sha256']}
    holds = {'schema_version': '1', 'executable': False,
        'records': [row for row in ordered if row['bucket'] in HOLDS], 'historical_version_tasks': historical,
        'cache_issues': index['cache_issues']}
    return {'inventory.json': inventory, 'first-fetch.json': first_fetch, 'report.json': report, 'holds.json': holds,
            'ordering.json': {'schema_version': '1', 'records': ordered}}


def create_plan(args):
    as_of, inputs = day(args.as_of).isoformat(), Inputs()
    output = args.output_dir.resolve()
    require(not args.output_dir.exists() and not args.output_dir.is_symlink(), 'output_directory_must_be_new')
    for source in (args.queue, args.catalog, args.cache_dir, args.observations, args.readings, args.monthly_dir):
        require(output != source.resolve() and not output.is_relative_to(source.resolve()) and
                not source.resolve().is_relative_to(output), 'output_overlaps_input')
    queue = inputs.json(args.queue)
    require(isinstance(queue, dict) and isinstance(queue.get('queue'), list), 'queue_object_required')
    ids = [row.get('work_id') if isinstance(row, dict) else None for row in queue['queue']]
    require(all(isinstance(wid, str) and wid for wid in ids) and len(set(ids)) == len(ids), 'queue_identity_missing_or_duplicate')
    payload, metadata = read_catalog(args.catalog, inputs)
    works = {row['work_id']: row for row in payload['works']}
    require(set(ids) <= works.keys(), 'unknown_queue_id')
    targets = {row['work_id']: row for row in load_targets(args.catalog, queue['queue'])}
    index = cache_index(args.cache_dir, args.observations, args.readings, works, inputs, args.min_body_characters, args.min_sections)
    cards, month_sources = monthly_selection(args.monthly_dir, month_window(as_of), payload, inputs, as_of)
    result = plan(queue, payload, targets, index, cards, as_of=as_of, limit=args.limit)
    require({row['work_id']: row for row in load_targets(args.catalog, result['inventory.json']['queue'])} == targets,
            'source_targets_changed_during_planning')
    # The running collector can append; this is a planning snapshot, not a lock
    # or reservation. Do not reread its log or mutate its request state.
    require(hashlib.sha256(args.queue.read_bytes()).hexdigest() == inputs.files[str(args.queue.resolve())]['sha256'], 'source_queue_changed')
    result['report.json'].update({'baseline': {'source_queue': str(args.queue.resolve()),
        'source_queue_sha256': inputs.files[str(args.queue.resolve())]['sha256'], 'catalog_hash': metadata.get('catalog_hash'),
        'catalog_work_set_sha256': fingerprint(sorted(works)), 'input_files': inputs.files,
        'log_snapshot': index['log'], 'resolved_targets_sha256': fingerprint(targets)},
        'monthpackage_sources': month_sources, 'cache_references_stat_checked_not_hashed': index['checked_cache_references'],
        'legacy_states_without_thresholds': index['legacy_states_without_thresholds'],
        'legacy_carried_failures': index['legacy_carried_failures'],
        'collector_parameters': {'parser_version': PARSER_VERSION, 'min_body_characters': args.min_body_characters, 'min_sections': args.min_sections}})
    for name in ('inventory.json', 'first-fetch.json'):
        result[name]['source_queue_plan'] = {**result[name].get('source_queue_plan', {}),
            'policy_version': 'first-fetch-v3', 'executable': name == 'first-fetch.json', 'as_of': as_of,
            'source_queue_sha256': inputs.files[str(args.queue.resolve())]['sha256'], 'resolved_targets_sha256': fingerprint(targets)}
    if not args.dry_run:
        # A new directory is never overwritten; an interrupted write lacks the
        # completion marker. Consumers must reject such an incomplete plan.
        args.output_dir.mkdir(parents=True, exist_ok=False)
        output_hashes = {}
        for name, value in result.items():
            raw = (encode(value) + '\n').encode()
            with (args.output_dir / name).open('xb') as stream:
                stream.write(raw)
            output_hashes[name] = hashlib.sha256(raw).hexdigest()
        with (args.output_dir / 'plan-complete.json').open('x') as stream:
            json.dump({'status': 'complete_not_activated', 'files_sha256': output_hashes}, stream, sort_keys=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('queue', 'catalog', 'cache-dir', 'observations', 'readings', 'monthly-dir', 'output-dir'):
        parser.add_argument('--' + option, type=Path, required=True)
    parser.add_argument('--as-of', required=True, help='YYYY-MM-DD; priority window, not a historical cache snapshot')
    parser.add_argument('--limit', required=True, type=int, help='Maximum first-fetch jobs, not an extra collector attempt budget')
    parser.add_argument('--min-body-characters', type=int, default=1500)
    parser.add_argument('--min-sections', type=int, default=2)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        require(args.min_body_characters >= 0 and args.min_sections >= 0, 'invalid_collector_thresholds')
        result = create_plan(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, 'Queue planning failed: ' + str(error) + '\n')
    report = result['report.json']
    print(encode({key: report[key] for key in ('status', 'as_of', 'original_jobs', 'inventory_jobs', 'first_fetch_jobs',
        'hold_jobs', 'bucket_counts', 'unknown_target_version_count', 'current_month_version_coverage', 'historical_actions', 'first20')}))


if __name__ == '__main__':
    main()
