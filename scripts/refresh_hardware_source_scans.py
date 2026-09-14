"""Reparse our private cached sources and persist public, excerpt-free scans."""
import argparse
import json
from pathlib import Path
from catalog_store import encode, fingerprint, write_if_changed
from hardware_census import detect_mentions, dictionary_hash
from collect_hardware_sources import (Collector, PARSER_VERSION, assess_html, digest, atomic_write, utc_now,
                                      constrain_transport, transport_incomplete)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FIELDS = {'work_id', 'arxiv_id', 'version', 'source_url', 'effective_url', 'observed_at', 'fetched_at', 'status',
                 'raw_sha256', 'text_sha256', 'body_characters', 'section_count', 'parser_version', 'scope', 'text_scope',
                 'http_status', 'images_not_inspected', 'supplementary_materials_not_inspected', 'processing_basis',
                 'parent_observation_id', 'observation_id', 'next_retry_at', 'manual_reviewed', 'excluded_sections', 'thresholds',
                 'transport_complete', 'transport_returncode', 'transport_truncated', 'curl_exit_code', 'transport_verification'}


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def trusted_path(value, cache):
    original = Path(value)
    # resolve() erases a final symlink's identity, including links that point
    # back inside objects/. Inspect the supplied path before following it.
    if original.is_symlink():
        raise ValueError('hardware_cache_reference_is_symlink')
    cache_root = cache.resolve()
    path = original.resolve()
    if not path.is_relative_to(cache_root / 'objects'):
        raise ValueError('hardware_cache_reference_outside_objects')
    # Reject symlinked directories within this cache as well. Stop at the
    # chosen cache root so system aliases such as macOS /var remain valid.
    for parent in original.parents:
        if parent.resolve() == cache_root:
            break
        if parent.is_symlink():
            raise ValueError('hardware_cache_reference_is_symlink')
    return path


def prepare_private_cache(cache, observations):
    collector = Collector(cache, observations)
    latest = {}
    for row in read_rows(observations):
        key = row['work_id'], row.get('source_url')
        if key not in latest or row['observed_at'] >= latest[key]['observed_at']:
            latest[key] = row
    for prior in list(latest.values()):
        target = {key: prior.get(key) for key in ('work_id', 'arxiv_id', 'version', 'source_url', 'version_basis')}
        if ((prior.get('parser_version') != PARSER_VERSION or
             (prior['status'] == 'full_text_available' and transport_incomplete(prior))) and
                prior['status'] in {'full_text_available', 'partial_text'} and prior.get('cache_ref')):
            raw = trusted_path(prior['cache_ref'], cache).read_bytes()
            if digest(raw) != prior['raw_sha256']:
                raise ValueError('hardware_cached_raw_hash_mismatch')
            assessment, blocks = assess_html(raw, target, prior['effective_url'])
            assessment = constrain_transport(assessment, prior)
            body = '\n\n'.join(block['text'] for block in blocks).encode()
            row = {**prior, **assessment, 'fetched_at': prior.get('fetched_at', prior['observed_at']), 'observed_at': utc_now(),
                   'processing_basis': 'cached_raw_reparse_no_network', 'parent_observation_id': prior['observation_id'],
                   'text_sha256': digest(body)}
            blockpath = cache / 'objects' / f"{row['raw_sha256']}.{PARSER_VERSION}.blocks.json"
            textpath = cache / 'objects' / f"{row['text_sha256']}.txt"
            atomic_write(blockpath, (encode(blocks) + '\n').encode())
            atomic_write(textpath, body)
            row.update(blocks_ref=str(blockpath.resolve()), body_cache_ref=str(textpath.resolve()))
            row.pop('observation_id', None)
            row['observation_id'] = 'hardware-source:' + fingerprint(row)[:32]
            collector.export(row)
        elif prior['status'] == 'full_text_available' and transport_incomplete(prior):
            # A missing raw reference must not hide an explicit transport
            # failure. Preserve any existing text hash/blocks as partial
            # evidence without pretending that bytes were reparsed.
            row = {**constrain_transport(prior, prior), 'observed_at': utc_now(),
                   'fetched_at': prior.get('fetched_at', prior['observed_at']),
                   'processing_basis': 'cached_transport_reclassification_no_network',
                   'parent_observation_id': prior['observation_id']}
            row.pop('observation_id', None)
            row['observation_id'] = 'hardware-source:' + fingerprint(row)[:32]
            collector.export(row)
        else:
            # Failure/denial is not reparsed or retried just because code changed.
            row = prior
        state = collector.state_path(target)
        if not state.exists() or row is not prior:
            atomic_write(state, (encode(row) + '\n').encode())


def _latest_source_rows(all_rows):
    latest = {}
    for row in all_rows:
        key = row['work_id'], row.get('source_url')
        if key not in latest or row['observed_at'] >= latest[key]['observed_at']:
            latest[key] = row
    return list(latest.values())


def _scan_cached_rows(cache, all_rows, dictionary):
    dhash = dictionary_hash(dictionary)
    scans = []
    for row in _latest_source_rows(all_rows):
        if row['status'] not in {'full_text_available', 'partial_text'} or not row.get('blocks_ref'):
            continue
        blocks = json.loads(trusted_path(row['blocks_ref'], cache).read_text())
        body = '\n\n'.join(block['text'] for block in blocks)
        if digest(body.encode()) != row['text_sha256']:
            raise ValueError('hardware_cached_body_hash_mismatch')
        matches, offset = [], 0
        for block in blocks:
            section = f"{block['section_id']} · {block['section_title']}"
            for match in detect_mentions(block['text'], dictionary, section):
                match.pop('excerpt', None)
                match.update(start=match['start'] + offset, end=match['end'] + offset)
                matches.append(match)
            offset += len(block['text']) + 2
        scans.append({'work_id': row['work_id'], 'source_url': row['source_url'], 'observed_at': utc_now(),
                      'scope': 'body', 'status': 'scanned', 'dictionary_hash': dhash, 'content_hash': row['text_sha256'],
                      'source_observation_hash': row['raw_sha256'], 'parser_version': row['parser_version'],
                      'matches': matches, 'review_status': 'unverified_machine_mentions'})
    return scans


def _persist_scan_history(output, scans):
    previous = read_rows(output / 'source-scans.jsonl')
    keys = {(r['work_id'], r['source_url'], r['dictionary_hash'], r['content_hash']): r for r in previous}
    for row in scans:
        keys.setdefault((row['work_id'], row['source_url'], row['dictionary_hash'], row['content_hash']), row)
    write_if_changed(output / 'source-scans.jsonl', ''.join(encode(row)+'\n' for row in sorted(keys.values(), key=lambda r: (r['work_id'], r['observed_at']))))


def scan(cache, observations, dictionary, output):
    prepare_private_cache(cache, observations)
    all_rows = read_rows(observations)
    scans = _scan_cached_rows(cache, all_rows, dictionary)
    dhash = dictionary_hash(dictionary)
    public = []
    for row in all_rows:
        value = {key: row[key] for key in PUBLIC_FIELDS if key in row}
        # Legacy records did not save curl exit codes. A structured HTML body
        # remains text-available, not retrospectively transport-audited. Never
        # fabricate a successful exit code from a closing </html> tag.
        if transport_incomplete(row):
            value['transport_verification'] = 'incomplete'
        else:
            value.setdefault('transport_verification', 'complete' if row.get('transport_complete') is True else 'legacy_unrecorded')
        if row.get('error'):
            value['error'] = (f"http_{row['http_status']}" if row.get('http_status') and row['http_status'] != 200
                              else 'transport_or_identity_error')
        public.append(value)
    output.mkdir(parents=True, exist_ok=True)
    write_if_changed(output / 'source-observations.jsonl', ''.join(encode(row)+'\n' for row in public))
    # Keep prior dictionary scans for lineage. An identical current text/dict
    # replay is idempotent and does not manufacture a new check timestamp.
    _persist_scan_history(output, scans)
    return {'observations': len(public), 'body_scanned': len(scans), 'body_mentions': sum(len(row['matches']) for row in scans), 'dictionary_hash': dhash}


def scan_registered(cache, observations, dictionary, output):
    """Rescan the published source snapshot without touching an active collector.

    Read its append-only private log once, tolerate only a currently incomplete
    final line, and select exactly the already published observation IDs.
    Never fetch, reparse, rewrite sources, or change private cache/state files.
    """
    registered_path = output / 'source-observations.jsonl'
    if not registered_path.is_file():
        raise ValueError('registered_source_snapshot_required')
    registered = read_rows(registered_path)
    wanted = {row.get('observation_id') for row in registered}
    if None in wanted or len(wanted) != len(registered):
        raise ValueError('registered_source_ids_missing_or_duplicate')
    selected = {}
    incomplete_tail = False
    lines = observations.read_bytes().splitlines(keepends=True)
    for number, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            if number == len(lines) - 1 and not line.endswith(b'\n'):
                incomplete_tail = True
                continue
            raise ValueError('private_observation_log_corrupt') from None
        oid = row.get('observation_id')
        if oid not in wanted:
            continue
        if oid in selected and selected[oid] != row:
            raise ValueError('conflicting_private_source_observation')
        selected[oid] = row
    if set(selected) != wanted:
        raise ValueError('registered_source_missing_from_private_log')
    source_keys = ('work_id', 'source_url', 'version', 'raw_sha256', 'text_sha256', 'observed_at', 'status')
    private_rows = []
    for public in registered:
        row = selected[public['observation_id']]
        if any(row.get(key) != public.get(key) for key in source_keys):
            raise ValueError('registered_private_source_binding_mismatch')
        private_rows.append(row)
    for row in _latest_source_rows(private_rows):
        if row['status'] == 'full_text_available' and transport_incomplete(row):
            raise ValueError('registered_source_requires_transport_reclassification')
        if row['status'] in {'full_text_available', 'partial_text'} and row.get('parser_version') != PARSER_VERSION:
            raise ValueError('registered_source_requires_parser_refresh')
    scans = _scan_cached_rows(cache, private_rows, dictionary)
    _persist_scan_history(output, scans)
    return {'mode': 'registered_sources_read_only', 'observations': len(registered),
            'body_scanned': len(scans), 'body_mentions': sum(len(row['matches']) for row in scans),
            'dictionary_hash': dictionary_hash(dictionary), 'incomplete_private_tail_ignored': incomplete_tail,
            'source_snapshot_modified': False, 'private_cache_modified': False, 'network_requests': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / '.research/hardware-fulltext')
    parser.add_argument('--observations', type=Path, default=ROOT / '.research/hardware-fulltext/observations.jsonl')
    parser.add_argument('--dictionary', type=Path, default=ROOT / 'config/hardware-dictionary.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/hardware-review')
    parser.add_argument('--registered-only', action='store_true', help='Rescan only published source IDs; never mutate cache/sources or include in-progress collection')
    args = parser.parse_args()
    operation = scan_registered if args.registered_only else scan
    print(json.dumps(operation(args.cache.resolve(), args.observations, json.loads(args.dictionary.read_text()), args.output)))


if __name__ == '__main__':
    main()
