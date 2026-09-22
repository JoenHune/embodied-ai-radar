#!/usr/bin/env python3
"""Resumable, deterministic original-text research. No LLM, API key or agent.

Default: offline cached HTML -> lossless text cards + SQLite FTS + candidates.
--fetch explicitly enables the existing paced, single-connection arXiv collector.
All results remain private, unverified, and separate from authoritative facts.
"""
from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from collect_hardware_sources import (Collector, arxiv_identity, atomic_write,
    encode, fetch_html_curl, load_targets, table_rows, utc_now)
from hardware_census import _compile_dictionary, _detect
from prepare_fulltext_reading import (MAX_RAW_BYTES, build_reading_packet,
    latest_observations, read_regular, trusted_file)

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'token-free-research-v1'
LIMITS = [
    '零模型调用；不读取密钥，不调用模型反代、付费搜索或子代理。',
    '机器解析/检索不是完整理解、AI精读、人审或实验复现；不创建阅读回执。',
    '设备频次是正文候选提及的去重work数，不是已确认使用、装机量或市场份额。',
    '无命中不代表没有设备；具体型号、实体/仿真与实际用途均待核验。',
    '图片仅保留原始链接/图注，像素、视频与外部补充材料未检查。',
    'HTML缺文及非arXiv来源保留在补缺清单，本脚本不自动抓取PDF或绕过访问限制。',
    '全文和摘录只留本机，不自动发布、改写权威库、生成月度研究结论或提升评审状态。',
    'source_state=full_text_available 表示历史上取得正文；清理缓存后不保证本机仍可读取正文。',
    'published_compacted 表示机器提取记录已上线且本机卡片已清理，仍未精读，不是阅读回执。',
]
TERMS = {'世界模型': ['world model', 'world action'], '大小脑': ['dual system', 'fast slow'],
         '灵巧操作': ['dexterous manipulation'], '视觉语言动作': ['vision language action', 'VLA'],
         '跨本体': ['cross embodiment', 'cross embodiment transfer'], 'π0': ['pi0', 'π0']}
DEVICE_WORDS = re.compile(r'robot|camera|gripper|tactile|sensor|GPU|CPU|Jetson|IMU|motion capture', re.I)
MODEL_WORDS = re.compile(r'\b(?:NVIDIA|Unitree|AgileX|RealSense|VectorNav|Wuji|Franka|Intel|AMD)'
                         r'(?:[ -][A-Za-z0-9][A-Za-z0-9.-]*){1,3}\b', re.I)


def fingerprint(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def read_log(path):
    """Read a fixed in-memory prefix; leave a collector's interrupted tail intact."""
    if not path.exists():
        return [], False
    raw = read_regular(path, maximum=256 * 1024 * 1024)
    rows, partial = [], False
    lines = raw.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except (ValueError, UnicodeDecodeError):
            if index == len(lines) - 1 and not raw.endswith(b'\n'):
                partial = True
            else:
                raise ValueError('corrupt_observation_log') from None
    return rows, partial


def read_published_receipts(output):
    """Index publisher receipts as data, never as processing instructions."""
    path = output / 'published-receipts.jsonl'
    if path.is_symlink():
        raise ValueError('symlink_published_receipts_forbidden')
    if not path.exists():
        return {}
    raw = read_regular(path, maximum=256 * 1024 * 1024)
    if raw and not raw.endswith(b'\n'):
        raise ValueError('incomplete_published_receipt_log')
    receipts = {}
    required = {'work_id', 'observation_id', 'processing_key', 'record_sha256',
                'commit_sha', 'published_at', 'process_state'}
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError('invalid_published_receipt_json') from exc
        if not isinstance(value, dict) or not required <= value.keys():
            raise ValueError('invalid_published_receipt_schema')
        if (any(not isinstance(value[key], str) or not value[key] for key in required) or
                not re.fullmatch(r'[0-9a-f]{64}', value['processing_key']) or
                not re.fullmatch(r'[0-9a-f]{64}', value['record_sha256']) or
                not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value['commit_sha']) or
                value['process_state'] != 'extracted_not_read'):
            raise ValueError('invalid_published_receipt_schema')
        try:
            datetime.strptime(value['published_at'], '%Y-%m-%dT%H:%M:%SZ')
        except ValueError as exc:
            raise ValueError('invalid_published_receipt_schema') from exc
        key = (value['work_id'], value['observation_id'])
        selected = {field: value[field] for field in required}
        variants = receipts.setdefault(key, {})
        previous = variants.get(value['processing_key'])
        if previous is not None and previous != selected:
            raise ValueError('conflicting_published_receipt')
        variants[value['processing_key']] = selected
    return receipts


def receipt_key(work_id, source):
    observation_id = source.get('observation_id') if source else None
    return (work_id, observation_id) if observation_id else None


def prior_receipt_exists(receipts, work_id, source):
    return receipt_key(work_id, source) in receipts


@contextmanager
def locked(output):
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name in ('runner.lock', 'research.sqlite', 'research.sqlite-wal', 'research.sqlite-shm', 'cards',
                 'hardware-candidate-sources.jsonl.tmp', 'published-receipts.jsonl'):
        if (output / name).is_symlink():
            raise ValueError('symlink_output_forbidden')
    with (output / 'runner.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('another_token_free_runner_is_active') from None
        yield


def open_db(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS works (
          work_id TEXT PRIMARY KEY, metadata TEXT NOT NULL, source_key TEXT NOT NULL,
          source_state TEXT NOT NULL, process_state TEXT NOT NULL, processed_key TEXT,
          card_path TEXT, reason TEXT, active INTEGER NOT NULL DEFAULT 1);
        CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(
          work_id UNINDEXED, title, abstract, body, tokenize='unicode61');
        CREATE TABLE IF NOT EXISTS candidates (
          work_id TEXT NOT NULL, dictionary_id TEXT NOT NULL, name TEXT NOT NULL,
          context_only INTEGER NOT NULL, evidence TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS candidates_work ON candidates(work_id);
    ''')
    return db


def initial_state(work, source):
    if source:
        return source.get('status', 'unknown')
    return 'not_fetched' if arxiv_identity(work.get('identifiers', {}).get('arxiv')) else 'external_source_needed'


def relevance(work):
    value = work.get('relevance', 'unknown')
    return value.get('status', 'unknown') if isinstance(value, dict) else value


def pipeline_hash(dictionary):
    files = ['token_free_research.py', 'prepare_fulltext_reading.py',
             'collect_hardware_sources.py', 'hardware_census.py', 'equipment_radar.py']
    return fingerprint([VERSION, dictionary, {f: hashlib.sha256((ROOT / 'scripts' / f).read_bytes()).hexdigest() for f in files}])


def sync_catalog(db, works, sources, rules_hash, receipts=None):
    """All relevance states remain in the denominator; changed sources invalidate results."""
    receipts = receipts or {}
    known = {r['work_id']: r for r in db.execute('SELECT rowid AS search_rowid,* FROM works')}
    db.execute('UPDATE works SET active=0')
    for work in works:
        wid, meta = work['work_id'], encode(work)
        source = sources.get(wid)
        key = fingerprint([rules_hash, source, work.get('identifiers'), work.get('identifier_aliases'), work.get('aliases')])
        old = known.get(wid)
        changed = old is None or old['source_key'] != key
        if changed:
            state = initial_state(work, source)
            process = 'pending' if state in {'full_text_available', 'partial_text'} else 'source_needed'
            if process == 'pending' and prior_receipt_exists(receipts, wid, source):
                process = ('published_compacted' if key in receipts[receipt_key(wid, source)]
                           else 'refresh_needed')
            inserted = db.execute('INSERT OR REPLACE INTO works VALUES (?,?,?,?,?,NULL,NULL,NULL,1)',
                                  (wid, meta, key, state, process))
            db.execute('DELETE FROM candidates WHERE work_id=?', (wid,))
            if old:
                db.execute('DELETE FROM search WHERE rowid=?', (old['search_rowid'],))
            db.execute('INSERT INTO search(rowid,work_id,title,abstract,body) VALUES (?,?,?,?,?)',
                       (inserted.lastrowid, wid, work.get('title', ''), work.get('abstract', ''), ''))
        else:
            db.execute('UPDATE works SET metadata=?,active=1 WHERE work_id=?', (meta, wid))
            if old['metadata'] != meta:
                db.execute('UPDATE search SET title=?,abstract=? WHERE rowid=?',
                           (work.get('title', ''), work.get('abstract', ''), old['search_rowid']))
    db.commit()


def analyse_packet(packet, dictionary):
    entries = {r['dictionary_id']: r for r in dictionary['entries']}
    compiled = _compile_dictionary(encode(dictionary))
    candidates, unknown = [], []
    warnings = list(packet.get('gaps', []))
    for section in packet['sections']:
        sid = section['section_id']
        body = [b for b in packet['blocks'] if b['kind'] != 'heading' and
                any(s['section_id'] == sid for s in b['section_path']) and b.get('text')]
        if not body:
            warnings.append('empty_section:' + sid)
    for issue in packet.get('issues', []):
        warnings.append('extractor:' + issue['code'])
    for block in packet['blocks']:
        text = block['text']
        context = block.get('evidence_role') == 'context_not_usage' or any(
            'abstract' in s.get('title', '').casefold() for s in block['section_path'])
        matches = _detect(text, compiled)
        for match in matches:
            entry = entries[match['dictionary_id']]
            candidates.append({**match, 'name': entry['name'], 'identity_level': entry['identity_level'],
                'category': entry['category'], 'source_locator': block['source_locator'],
                'block_id': block['block_id'], 'context_only': context,
                'status': 'unverified_mention', 'usage_verified': False,
                'simulation_word_present': bool(re.search(r'\bsimulat', text, re.I)),
                'negation_word_present': bool(re.search(r'\b(not|without|never)\b', text, re.I))})
        if not context and DEVICE_WORDS.search(text):
            for match in MODEL_WORDS.finditer(text):
                if any(match.start() < m['end'] and m['start'] < match.end() for m in matches):
                    continue
                unknown.append({'term': match.group(), 'source_locator': block['source_locator'],
                    'excerpt': text[max(0, match.start()-100):match.end()+100],
                    'status': 'heuristic_name_not_verified_not_ranked'})
    return {'work_id': packet['work_id'], 'source': packet['source'],
        'packet_sha256': packet['packet_sha256'], 'extraction_coverage': packet['extraction_coverage'],
        'blocks': packet['blocks'], 'sections': packet['sections'], 'issues': packet.get('issues', []),
        'warnings': sorted(set(warnings)), 'hardware_candidates': candidates,
        'unknown_name_candidates': unknown, 'article_read_complete': False,
        'understanding_verified': False, 'images_inspected': False, 'model_calls': 0,
        'limits': LIMITS}


def process_one(db, work, source, cache, output, dictionary, receipts=None):
    wid = work['work_id']
    receipts = receipts or {}
    row = db.execute('SELECT rowid AS search_rowid,* FROM works WHERE work_id=?', (wid,)).fetchone()
    published = row['source_key'] in receipts.get(receipt_key(wid, source), {})
    if published:
        with db:
            db.execute('UPDATE works SET process_state=?,processed_key=? WHERE work_id=?',
                       ('published_compacted', row['source_key'], wid))
        return 'published_compacted'
    if row['processed_key'] == row['source_key'] and row['card_path'] and (output / row['card_path']).is_file():
        return 'reused'  # No repeated model call, parsing, or byte-reverification claim.
    if row['source_state'] not in {'full_text_available', 'partial_text'}:
        return 'source_needed'
    if row['process_state'] == 'refresh_needed' and prior_receipt_exists(receipts, wid, source):
        ref = source.get('cache_ref') if source else None
        reference = Path(ref) if ref else None
        if reference and not reference.is_absolute():
            reference = cache / reference
        if not reference or not reference.is_file():
            return 'refresh_needed'
    try:
        ref = Path(source['cache_ref'])
        raw = read_regular(trusted_file(ref if ref.is_absolute() else cache / ref, cache / 'objects'), maximum=MAX_RAW_BYTES)
        packet = build_reading_packet(raw, source, work)
        card = analyse_packet(packet, dictionary)
    except (ValueError, OSError, KeyError) as error:
        db.execute('UPDATE works SET process_state=?,reason=? WHERE work_id=?',
                   ('extraction_failed', str(error)[:300], wid))
        db.commit()
        return 'extraction_failed'
    path = Path('cards') / (fingerprint([wid, row['source_key']]) + '.json.gz')
    card['processing_key'] = row['source_key']
    atomic_write(output / path, gzip.compress((encode(card) + '\n').encode(), mtime=0))
    body = '\n\n'.join(b['text'] for b in card['blocks'])
    structural = [w for w in card['warnings'] if w.startswith(('empty_section:', 'extractor:')) or
                  w in {'source_version_unresolved', 'source_observation_not_full_text_available',
                        'transport_completion_not_verified'}]
    with db:
        db.execute('DELETE FROM candidates WHERE work_id=?', (wid,))
        db.executemany('INSERT INTO candidates VALUES (?,?,?,?,?)', [
            (wid, c['dictionary_id'], c['name'], int(c['context_only']), encode(c)) for c in card['hardware_candidates']])
        db.execute('UPDATE search SET body=? WHERE rowid=?', (body, row['search_rowid']))
        db.execute('UPDATE works SET process_state=?,processed_key=?,card_path=?,reason=? WHERE work_id=?',
                   ('extracted_not_read', row['source_key'], str(path), encode(structural) if structural else None, wid))
    return 'extracted_not_read'


def export_reports(db, output, run):
    rows = list(db.execute('SELECT * FROM works WHERE active=1 ORDER BY work_id'))
    coverage, queue, months = [], [], defaultdict(Counter)
    for row in rows:
        work = json.loads(row['metadata'])
        month = (work.get('first_public_date') or '')[:7] if work.get('first_public_date_precision') in {'day','month'} else 'unknown'
        state = row['process_state']
        months[month]['catalog_works'] += 1
        months[month][state] += 1
        item = {k: row[k] for k in ('work_id','source_state','process_state','card_path','reason')}
        item.update(title=work.get('title'), month=month, relevance=relevance(work),
                    primary_direction=work.get('primary_direction'))
        coverage.append(item)
        if state not in {'extracted_not_read', 'published_compacted'} or row['reason']:
            aid = arxiv_identity(work.get('identifiers', {}).get('arxiv'))
            queue.append({**item, 'official_landing_url': f'https://arxiv.org/abs/{aid[0]}' if aid else None,
                          'next_step': ('等待本机提取' if state == 'pending' else
                                        '规则变化，需重新取得原文并提取' if state == 'refresh_needed' else
                                        '补全文或核查公开来源；不得将摘要替代正文')})
    freq = [dict(r) for r in db.execute('''SELECT c.dictionary_id,c.name,
        count(DISTINCT c.work_id) AS candidate_work_count FROM candidates c
        JOIN works w USING(work_id) WHERE w.active=1 AND c.context_only=0
        GROUP BY c.dictionary_id,c.name ORDER BY candidate_work_count DESC,c.name''')]
    summary = {'schema_version':'1', 'generated_at':utc_now(), 'model_calls':0,
        'catalog_work_count':len(rows), 'source_states':dict(Counter(r['source_state'] for r in rows)),
        'processing_states':dict(Counter(r['process_state'] for r in rows)),
        'source_or_structure_warning_works':sum(bool(r['reason']) for r in rows),
        'new_complete_reading_receipts':0, 'new_verified_usage_assertions':0,
        'run':run, 'limits':LIMITS}
    outputs = {'summary.json':summary, 'monthly-coverage.json':dict(sorted(months.items())),
               'hardware-candidate-frequency.json':freq}
    for name, value in outputs.items():
        atomic_write(output / name, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())
    for name, data in [('coverage.jsonl',coverage), ('source-review-queue.jsonl',queue)]:
        atomic_write(output / name, ''.join(encode(r)+'\n' for r in data).encode())
    # Every ranked name has a full source list; no sample truncation.
    with (output / 'hardware-candidate-sources.jsonl.tmp').open('w') as stream:
        for r in db.execute('SELECT c.work_id,c.evidence FROM candidates c JOIN works w USING(work_id) WHERE w.active=1 ORDER BY c.dictionary_id,c.work_id'):
            stream.write(encode({'work_id':r['work_id'], **json.loads(r['evidence'])})+'\n')
    (output / 'hardware-candidate-sources.jsonl.tmp').replace(output / 'hardware-candidate-sources.jsonl')
    report = ['# 零模型调用的原文处理进度', '', f'全库 {len(rows):,} 项；本次模型调用 0。', '',
              '## 处理状态', '', *[f'- {k}: {v:,}' for k,v in summary['processing_states'].items()], '',
              '## 边界', '', *['- '+v for v in LIMITS], '',
              '未清理的 research.sqlite 和 cards/ 可供本机全文检索及检查；已发布清理的条目不保证保留原文。',
              'hardware-candidate-frequency.json 按候选提及的 work 数排序，全部出处见 hardware-candidate-sources.jsonl。',
              'monthly-coverage.json 只统计处理覆盖，不将自动提取包装为研究趋势判断。', '']
    atomic_write(output / 'REPORT.md', '\n'.join(report).encode())
    return summary


def search(db, query):
    expressions = [query, *TERMS.get(query.strip(), [])]
    expression = ' OR '.join('"'+s.replace('"','""')+'"' for s in expressions if s.strip())
    if not expression:
        return []
    return [dict(r) for r in db.execute('''SELECT s.work_id,s.title,
        snippet(search,3,'[',']','…',35) AS excerpt,w.card_path,w.process_state
        FROM search s JOIN works w ON w.work_id=s.work_id
        WHERE search MATCH ? AND w.active=1 ORDER BY bm25(search) LIMIT 30''', (expression,))]


def run(catalog, cache, output, dictionary, *, fetch=False, fetch_limit=200,
        process_limit=0, work_ids=None, status=False, query=None):
    with locked(output), closing(open_db(output / 'research.sqlite')) as db:
        if query is not None:
            return {'results':search(db,query), 'model_calls':0}
        if status:
            return export_reports(db, output, {'status_only':True})
        works = list(table_rows(catalog, 'works'))
        ids = [w['work_id'] for w in works]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate_canonical_work')
        if work_ids and set(work_ids) - set(ids):
            raise ValueError('unknown_work_id')
        rows, partial = read_log(cache / 'observations.jsonl')
        sources = latest_observations(rows)
        receipts = read_published_receipts(output)
        # Recent included works first; every other record remains queued, not dropped.
        works.sort(key=lambda w: (relevance(w) != 'included',
            -(int(re.sub(r'\D','',w.get('first_public_date') or '')[:8] or 0)), w['work_id']))
        selected = [w for w in works if not work_ids or w['work_id'] in work_ids]
        fetch_result = None
        if fetch:
            # Only first-fetch jobs. Failed/blocked targets require deliberate review;
            # switching URL/version must not defeat a previous block or cooldown.
            queue = [w['work_id'] for w in selected if w['work_id'] not in sources and
                     arxiv_identity(w.get('identifiers', {}).get('arxiv'))]
            if any(s.get('status') == 'blocked' for s in sources.values()):
                fetch_result = {'status':'paused_previous_access_block_requires_review','attempted':0}
            elif queue:
                targets = load_targets(catalog, queue)
                collector = Collector(cache, cache/'observations.jsonl', fetcher=fetch_html_curl)
                fetch_result = collector.run(targets, limit=fetch_limit or len(targets))
                rows, partial = read_log(cache / 'observations.jsonl')
                sources = latest_observations(rows)
        sync_catalog(db, works, sources, pipeline_hash(dictionary), receipts)
        counts, processed = Counter(), 0
        try:
            for work in selected:
                result = process_one(db, work, sources.get(work['work_id']), cache, output, dictionary, receipts)
                counts[result] += 1
                if result in {'extracted_not_read','extraction_failed'}:
                    processed += 1
                    print(encode({'work_id':work['work_id'],'state':result,'newly_processed':processed}), flush=True)
                    if process_limit and processed >= process_limit:
                        break
        except KeyboardInterrupt:
            return export_reports(db, output, {'interrupted':True,'counts':dict(counts),'fetch':fetch_result})
        return export_reports(db, output, {'counts':dict(counts),'fetch':fetch_result,
            'observation_tail_ignored':partial, 'cache_reuse_does_not_reverify_bytes':True})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Opt in to official arXiv HTML network collection; never model APIs')
    parser.add_argument('--fetch-limit', type=int, default=200, help='New first-fetch attempts; 0 means all remaining')
    parser.add_argument('--process-limit', type=int, default=0, help='New cached papers to parse; 0 means all available')
    parser.add_argument('--work-ids', nargs='+')
    parser.add_argument('--output', type=Path, default=ROOT/'.research/token-free-research')
    parser.add_argument('--status', action='store_true')
    parser.add_argument('--search')
    args = parser.parse_args(argv)
    output = args.output.absolute()
    private = ROOT/'.research'
    if (args.fetch_limit < 0 or args.process_limit < 0 or '..' in output.parts or
        not output.resolve().is_relative_to(private.resolve()) or output.resolve() == private.resolve() or
        output.resolve().is_relative_to((private/'hardware-fulltext').resolve()) or
        any(p.is_symlink() for p in [output, *output.parents])):
        parser.error('Output must be a private, non-symlink directory outside the source cache; limits must be nonnegative')
    try:
        dictionary = json.loads((ROOT/'config/hardware-dictionary.json').read_text())
        result = run(ROOT/'data/catalog', private/'hardware-fulltext', output, dictionary,
            fetch=args.fetch, fetch_limit=args.fetch_limit, process_limit=args.process_limit,
            work_ids=args.work_ids, status=args.status, query=args.search)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError,OSError,sqlite3.Error) as error:
        print('token-free-research: '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
