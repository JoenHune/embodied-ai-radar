#!/usr/bin/env python3
"""Validate/import explicit AI reading declarations; default is DRY RUN.

Input: {"schema_version": "1", "readings": [{...}]} with reading_status
"completed", reader_kind "AI", text_scope "complete_available_article_text",
article_normalization "article-get-text-v1", official versioned source_url,
version, raw_sha256, observed_at, read_completed_at, article_chars,
article_text_sha256, read_ranges [{"start": 0, "end": article_chars}],
checked_table_ids, math_source_note_zh, images_inspected false,
supplementary_materials_inspected false, and findings_zh / limitations_zh
[{"text_zh": "简短判断", "source_locator": "S4"}].

article-get-text-v1 removes ONLY script/style/nav from the selected article,
then uses article.get_text(' ', strip=True), without a further whitespace or
math rewrite. Offsets are zero-based, half-open Python Unicode character
indices, NOT packet segment indices, UTF-8 byte offsets or token positions.
Abstracts, related work, appendices, references, captions and duplicate
MathML/TeX representations remain in this canonical text.

The checks prove source/range/locator consistency, not that an AI understood
the text. Only a reader's explicit declaration can create a receipt; preparing
or displaying a packet cannot. Public receipts say
self_attested_AI_reading_not_human_review, and never modify device authority.

Legacy observations may have an unversioned official source_url. They are
accepted only with an explicit version proven by the cached HTML identity.
The observed URL is retained for provenance; versioned_source_url pins reader
links to that exact version without fabricating another acquisition event.

Readers of the complete structured packet may explicitly declare
article_normalization "reading-packet-blocks-v1" instead. Its character
projection is all block texts joined with two newlines, including tables,
math alternatives, captions, appendices and references. Import reconstructs
the exact packet from original bytes and verifies its hash; it never converts
a prepared packet or a model ACK into a reading declaration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from catalog_store import encode, fingerprint, load_catalog, write_if_changed
from collect_hardware_sources import arxiv_identity, page_identity, transport_incomplete, normalized_heading

ROOT = Path(__file__).resolve().parents[1]
NORMALIZATION = 'article-get-text-v1'
PACKET_NORMALIZATION = 'reading-packet-blocks-v1'
ASSURANCE = 'self_attested_AI_reading_not_human_review'
TEXT_SCOPE = 'complete_available_article_text'
HASH = re.compile(r'^[0-9a-f]{64}$')
PRIVATE = re.compile(r'file://|/Users/|/home/|/private/|\.research/|[A-Za-z]:\\')
SECTION = 'section,.ltx_section,.ltx_subsection,.ltx_subsubsection,.ltx_appendix'
TABLE = 'table,.ltx_tabular,[role=table],[role=grid]'


def fail(reason):
    raise ValueError('fulltext_reading_review:' + reason)


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def required_text(row, key, limit=1000, *, chinese=False):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        fail('invalid_' + key)
    if PRIVATE.search(value) or any(ord(c) < 32 and c not in '\n\t' for c in value):
        fail('private_path_or_control_character_in_' + key)
    if chinese and not re.search(r'[\u3400-\u9fff]', value):
        fail('chinese_judgment_required:' + key)
    return value


def timestamp(value):
    if not isinstance(value, str) or not value.endswith('Z'):
        fail('utc_timestamp_required')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        fail('utc_timestamp_required')
    return result


def jsonl(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()] if path.exists() else []


def official_source(value, version=None):
    parsed = urlsplit(str(value or ''))
    if (parsed.scheme != 'https' or parsed.hostname not in {'arxiv.org', 'www.arxiv.org'} or
            parsed.username or parsed.password or parsed.port not in {None, 443} or parsed.query or parsed.fragment or
            not parsed.path.startswith('/html/')):
        fail('versioned_official_html_url_required')
    identity = arxiv_identity(value)
    if not identity or (version is not None and identity[1] not in {None, version}):
        fail('source_version_or_identity_mismatch')
    return identity


def versioned_read_url(source_url, version):
    aid, url_version = official_source(source_url, version)
    return source_url if url_version else f'https://arxiv.org/html/{aid}{version}'


def private_bytes(reference, cache_root):
    if not isinstance(reference, str) or not reference:
        fail('private_cache_reference_required')
    original = Path(reference).absolute()
    root = Path(cache_root).resolve()
    if original.is_symlink():
        fail('unsafe_cache_symlink')
    resolved = original.resolve()
    if not resolved.is_relative_to(root / 'objects'):
        fail('private_cache_outside_objects')
    for parent in original.parents:
        if parent.resolve() == root:
            break
        if parent.is_symlink():
            fail('unsafe_cache_symlink')
    if not stat.S_ISREG(original.lstat().st_mode):
        fail('private_cache_not_regular_file')
    # Refuse a final-component symlink introduced between validation and open.
    fd = os.open(original, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            fail('private_cache_not_regular_file')
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            raw = handle.read(30_000_001)
    finally:
        os.close(fd)
    if len(raw) > 30_000_000:
        fail('private_cache_too_large')
    return raw


def _article(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    article = soup.select_one('article.ltx_document,.ltx_document,article')
    if article is None:
        fail('complete_article_element_required')
    for node in list(article.select('script,style,nav')):
        if node.parent is not None:
            node.decompose()
    return soup, article


def article_text(raw):
    """Exact canonical string; exposing this helper does not attest reading."""
    return _article(raw)[1].get_text(' ', strip=True)


def _material(raw):
    soup, article = _article(raw)
    text = article.get_text(' ', strip=True)
    # A correctly hashed abstract-only page is still not a complete article.
    def body_section(node):
        heading = node.find(re.compile('^h[1-6]$'))
        title = heading.get_text(' ', strip=True) if heading else node.get_text(' ', strip=True)
        return (not node.find_parent(class_='ltx_abstract') and 'ltx_abstract' not in node.get('class', []) and
                not re.match(r'^(?:abstract|references|bibliography)\b', normalized_heading(title), re.I))
    body_sections = [node for node in article.select(SECTION) if body_section(node)]
    if not text or not any(node.get_text(' ', strip=True) for node in body_sections):
        fail('only_abstract_or_no_article_body')
    locators, ambiguous = {}, set()
    for node in [article, *article.select('[id]')]:
        sid = node.get('id')
        if not sid:
            continue
        if sid in locators:
            ambiguous.add(sid)
        locators[sid] = sha256(node.get_text(' ', strip=True).encode('utf-8'))
    table_ids = set()
    for node in article.select(TABLE):
        if 'ltx_eqn_table' in node.get('class', []):
            continue
        if node.get('id'):
            table_ids.add(node['id'])
        container = node.find_parent(class_='ltx_table')
        if container and container.get('id'):
            table_ids.add(container['id'])
    return soup, article, text, locators, ambiguous, table_ids


def validate_ranges(value, size):
    if not isinstance(value, list) or not value or len(value) > 10000:
        fail('explicit_complete_read_ranges_required')
    ranges = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {'start', 'end'}:
            fail('read_range_start_end_required')
        start, end = item['start'], item['end']
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= size:
            fail('read_range_out_of_bounds')
        ranges.append({'start': start, 'end': end})
    ranges.sort(key=lambda row: (row['start'], row['end']))
    cursor = 0
    for item in ranges:
        if item['start'] != cursor:
            fail('read_ranges_gap_or_overlap')
        cursor = item['end']
    if cursor != size:
        fail('read_ranges_incomplete')
    return ranges


def _judgments(value, locators, ambiguous, source_url):
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        fail('brief_bound_judgments_required')
    result = []
    for row in value:
        if not isinstance(row, dict):
            fail('judgment_object_required')
        text = required_text(row, 'text_zh', chinese=True)
        locator = required_text(row, 'source_locator', limit=500)
        if '://' in locator:
            base, sep, locator = locator.partition('#')
            if base != source_url or not sep:
                fail('judgment_source_url_mismatch')
        ids = [sid.strip() for sid in locator.split(';')]
        if not all(ids) or len(ids) != len(set(ids)) or any(sid not in locators or sid in ambiguous for sid in ids):
            fail('unknown_or_ambiguous_judgment_locator')
        result.append({'text_zh': text, 'source_locator': '; '.join(ids),
                       'locator_text_sha256': {sid: locators[sid] for sid in ids}})
    return result


def validate_readings(declarations, payload, observations, cache_root):
    if declarations.get('schema_version') != '1' or not isinstance(declarations.get('readings'), list):
        fail('explicit_reading_declaration_schema_required')
    works = {work['work_id']: work for work in payload['works']}
    if len(works) != len(payload['works']):
        fail('duplicate_canonical_work')
    source_owners = {}
    for wid, work in works.items():
        aid = arxiv_identity(work.get('identifiers', {}).get('arxiv'))
        if aid:
            source_owners.setdefault(aid[0], set()).add(wid)
    receipts, seen = [], set()
    for declaration in declarations['readings']:
        if not isinstance(declaration, dict):
            fail('reading_declaration_object_required')
        if (declaration.get('reading_status') != 'completed' or declaration.get('preparation_status') is not None or
                declaration.get('reader_kind') != 'AI' or declaration.get('text_scope') != TEXT_SCOPE or
                declaration.get('article_normalization') not in {NORMALIZATION, PACKET_NORMALIZATION}):
            fail('explicit_completed_AI_article_declaration_required')
        if declaration.get('images_inspected') is not False or declaration.get('supplementary_materials_inspected') is not False:
            fail('explicit_uninspected_external_media_required')
        wid = required_text(declaration, 'work_id', limit=300)
        if wid not in works:
            fail('unknown_canonical_work')
        version = required_text(declaration, 'version', limit=20)
        if not re.fullmatch(r'v[1-9]\d*', version):
            fail('version_required')
        source_url = required_text(declaration, 'source_url', limit=1000)
        aid, _ = official_source(source_url, version)
        if source_owners.get(aid) != {wid}:
            fail('unknown_or_ambiguous_canonical_source_identity')
        for key in ('raw_sha256', 'article_text_sha256'):
            if not HASH.fullmatch(str(declaration.get(key, ''))):
                fail('invalid_' + key)
        observed = timestamp(declaration.get('observed_at'))
        completed = timestamp(declaration.get('read_completed_at'))
        if completed < observed:
            fail('reading_precedes_source_observation')
        keys = ('work_id', 'source_url', 'version', 'raw_sha256', 'observed_at')
        matches = [row for row in observations if all(row.get(key) == declaration.get(key) for key in keys)
                   and row.get('status') in {'full_text_available', 'partial_text'}]
        if not matches:
            fail('matching_available_source_observation_required')
        observation = matches[-1]
        if transport_incomplete(observation):
            fail('known_incomplete_source_transport')
        raw = private_bytes(observation.get('cache_ref'), cache_root)
        if sha256(raw) != declaration['raw_sha256']:
            fail('raw_cache_hash_mismatch')
        soup, article, text, locators, ambiguous, table_ids = _material(raw)
        effective_url = observation.get('effective_url') or source_url
        effective_id, _ = official_source(effective_url, version)
        if effective_id != aid:
            fail('raw_page_identity_or_version_mismatch:effective_url_identity_mismatch')
        # A legacy unversioned observation needs the version in the HTML
        # identity proofs, not just an asserted/redirected effective URL.
        identity_url = source_url if official_source(source_url)[1] is None else effective_url
        valid, resolved_version, _, reason = page_identity(soup, identity_url, aid, version)
        if not valid or resolved_version != version:
            fail('raw_page_identity_or_version_mismatch:' + str(reason))
        pinned_url = versioned_read_url(source_url, version)
        if ('versioned_source_url' in declaration and
                declaration['versioned_source_url'] != pinned_url):
            fail('declared_versioned_source_url_mismatch')
        url_metadata = {'versioned_source_url': pinned_url} if pinned_url != source_url else {}
        normalization = declaration['article_normalization']
        packet_metadata = {}
        if normalization == PACKET_NORMALIZATION:
            from prepare_fulltext_reading import build_reading_packet
            segment_chars = declaration.get('reading_packet_segment_chars')
            if type(segment_chars) is not int or not 200 <= segment_chars <= 20000:
                fail('reading_packet_segment_chars_required')
            packet = build_reading_packet(raw, observation, works[wid], segment_chars=segment_chars)
            if packet['packet_sha256'] != declaration.get('reading_packet_sha256'):
                fail('reading_packet_hash_mismatch')
            text = '\n\n'.join(block['text'] for block in packet['blocks'])
            packet_metadata = {'reading_packet_sha256': packet['packet_sha256'],
                               'reading_packet_segment_chars': segment_chars}
        elif any(key in declaration for key in ('reading_packet_sha256', 'reading_packet_segment_chars')):
            fail('packet_metadata_requires_packet_normalization')
        size = declaration.get('article_chars')
        if type(size) is not int or size != len(text) or sha256(text.encode('utf-8')) != declaration['article_text_sha256']:
            fail('article_text_hash_or_character_count_mismatch')
        ranges = validate_ranges(declaration.get('read_ranges'), size)
        if observation.get('blocks_ref'):
            blocks = json.loads(private_bytes(observation['blocks_ref'], cache_root))
            if not isinstance(blocks, list) or not all(isinstance(b, dict) and isinstance(b.get('text'), str) for b in blocks):
                fail('invalid_original_body_blocks')
            if sha256('\n\n'.join(b['text'] for b in blocks).encode('utf-8')) != observation.get('text_sha256'):
                fail('original_body_blocks_hash_mismatch')
            block_ids = set()
            for block in blocks:
                sid = block.get('section_id')
                if not isinstance(sid, str) or not sid:
                    fail('original_body_block_id_required')
                if sid in block_ids:
                    ambiguous.add(sid)
                block_ids.add(sid)
                locators.setdefault(sid, sha256(block['text'].encode('utf-8')))
        checked = declaration.get('checked_table_ids')
        if (not isinstance(checked, list) or any(not isinstance(sid, str) for sid in checked) or
                len(checked) != len(set(checked)) or any(sid not in table_ids or sid in ambiguous for sid in checked)):
            fail('unknown_or_ambiguous_checked_table_id')
        math_note = required_text(declaration, 'math_source_note_zh', chinese=True)
        findings = _judgments(declaration.get('findings_zh'), locators, ambiguous, source_url)
        limitations = _judgments(declaration.get('limitations_zh'), locators, ambiguous, source_url)
        identity = [wid, source_url, version, declaration['raw_sha256'], declaration['article_text_sha256'], TEXT_SCOPE, normalization]
        if packet_metadata:
            identity += [packet_metadata['reading_packet_sha256'], packet_metadata['reading_packet_segment_chars']]
        receipt_id = 'fulltext-reading:' + fingerprint(identity)[:24]
        if receipt_id in seen:
            fail('duplicate_reading_declaration')
        seen.add(receipt_id)
        receipt = {'schema_version': '1', 'reading_id': receipt_id, 'work_id': wid, 'source_url': source_url, **url_metadata,
                   'version': version, 'raw_sha256': declaration['raw_sha256'], 'observed_at': declaration['observed_at'],
                   'read_completed_at': declaration['read_completed_at'], 'reader_kind': 'AI', 'reading_status': 'completed',
                   'assurance': ASSURANCE, 'human_reviewed': False, 'understanding_verified': False,
                   'verification_scope': 'source_identity_hash_ranges_and_locators_only',
                   'text_scope': TEXT_SCOPE, 'article_normalization': normalization, **packet_metadata,
                   'article_chars': size, 'article_text_sha256': declaration['article_text_sha256'], 'read_ranges': ranges,
                   'range_units': 'python_unicode_characters_zero_based_half_open',
                   'checked_table_ids': checked, 'checked_table_count': len(checked), 'tables_exhaustive': False,
                   'checked_table_text_sha256': {sid: locators[sid] for sid in checked},
                   'math_source_note_zh': math_note, 'images_inspected': False, 'supplementary_materials_inspected': False,
                   'supplementary_scope_note': 'external_media_only; embedded_appendix_text_is_within_article_scope',
                   'source_availability_status': observation['status'],
                   'transport_verification': observation.get('transport_verification', 'legacy_unrecorded'),
                   'publisher_fulltext_or_media_completeness_verified': False,
                   'findings_zh': findings, 'limitations_zh': limitations,
                   'declaration_sha256': fingerprint(declaration)}
        if 'range_basis' in declaration:
            receipt['range_basis'] = required_text(declaration, 'range_basis', limit=200)
        receipts.append(receipt)
    return receipts


def public_audit(records, payload, public_observations, as_of):
    """CI-only consistency audit: no cache, fetching, re-reading or promotion.

This checks declared metadata and source-observation lineage. DOM membership,
article hashes and cognitive reading are NOT reverified by this public audit.
Future-dated receipts remain valid history but are omitted from the as_of view.
"""
    allowed = {'schema_version', 'reading_id', 'work_id', 'source_url', 'version', 'raw_sha256', 'observed_at',
               'read_completed_at', 'reader_kind', 'reading_status', 'assurance', 'human_reviewed',
               'understanding_verified', 'verification_scope', 'text_scope', 'article_normalization',
               'article_chars', 'article_text_sha256', 'read_ranges', 'range_units', 'checked_table_ids',
               'checked_table_count', 'tables_exhaustive', 'checked_table_text_sha256', 'math_source_note_zh',
               'images_inspected', 'supplementary_materials_inspected', 'supplementary_scope_note',
               'source_availability_status', 'transport_verification', 'publisher_fulltext_or_media_completeness_verified',
               'findings_zh', 'limitations_zh', 'declaration_sha256', 'range_basis',
               'reading_packet_sha256', 'reading_packet_segment_chars', 'versioned_source_url'}
    if not isinstance(records, list):
        fail('public_reading_records_required')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(as_of)):
        timestamp(as_of + 'T00:00:00Z')
        visible = lambda value: value[:10] <= as_of
    else:
        cutoff = timestamp(as_of)
        visible = lambda value: timestamp(value) <= cutoff
    works = {work['work_id']: work for work in payload['works']}
    owners = {}
    for wid, work in works.items():
        aid = arxiv_identity(work.get('identifiers', {}).get('arxiv'))
        if aid:
            owners.setdefault(aid[0], set()).add(wid)
    valid, seen = [], set()
    for row in records:
        if not isinstance(row, dict) or set(row) - allowed:
            fail('unknown_or_private_public_reading_fields')
        constants = {'schema_version': '1', 'reader_kind': 'AI', 'reading_status': 'completed', 'assurance': ASSURANCE,
                     'verification_scope': 'source_identity_hash_ranges_and_locators_only', 'text_scope': TEXT_SCOPE,
                     'range_units': 'python_unicode_characters_zero_based_half_open'}
        if any(row.get(key) != value for key, value in constants.items()):
            fail('public_AI_self_attestation_schema_invalid')
        normalization = row.get('article_normalization')
        if normalization not in {NORMALIZATION, PACKET_NORMALIZATION}:
            fail('public_reading_normalization_invalid')
        if normalization == PACKET_NORMALIZATION:
            if (not HASH.fullmatch(str(row.get('reading_packet_sha256', ''))) or
                    type(row.get('reading_packet_segment_chars')) is not int or
                    not 200 <= row['reading_packet_segment_chars'] <= 20000):
                fail('public_reading_packet_metadata_invalid')
        elif any(key in row for key in ('reading_packet_sha256', 'reading_packet_segment_chars')):
            fail('public_packet_metadata_requires_packet_normalization')
        if any(row.get(key) is not False for key in ('human_reviewed', 'understanding_verified', 'images_inspected',
                'supplementary_materials_inspected', 'tables_exhaustive', 'publisher_fulltext_or_media_completeness_verified')):
            fail('public_reading_overclaims_verification')
        if PRIVATE.search(encode(row)):
            fail('private_path_in_public_reading')
        wid, version = row.get('work_id'), row.get('version')
        if wid not in works or not isinstance(version, str) or not re.fullmatch(r'v[1-9]\d*', version):
            fail('public_canonical_work_or_version_invalid')
        aid, _ = official_source(row.get('source_url'), version)
        pinned_url = versioned_read_url(row['source_url'], version)
        if ((pinned_url != row['source_url'] and row.get('versioned_source_url') != pinned_url) or
                (pinned_url == row['source_url'] and 'versioned_source_url' in row)):
            fail('public_versioned_source_url_mismatch')
        if owners.get(aid) != {wid}:
            fail('public_canonical_source_identity_mismatch')
        if timestamp(row.get('read_completed_at')) < timestamp(row.get('observed_at')):
            fail('public_reading_precedes_source')
        for key in ('raw_sha256', 'article_text_sha256', 'declaration_sha256'):
            if not HASH.fullmatch(str(row.get(key, ''))):
                fail('public_reading_hash_invalid')
        identity = [wid, row['source_url'], version, row['raw_sha256'], row['article_text_sha256'], TEXT_SCOPE, normalization]
        if normalization == PACKET_NORMALIZATION:
            identity += [row['reading_packet_sha256'], row['reading_packet_segment_chars']]
        rid = 'fulltext-reading:' + fingerprint(identity)[:24]
        if row.get('reading_id') != rid or rid in seen:
            fail('public_reading_id_mismatch_or_duplicate')
        seen.add(rid)
        keys = ('work_id', 'source_url', 'version', 'raw_sha256', 'observed_at')
        sources = [source for source in public_observations if all(source.get(key) == row.get(key) for key in keys)
                   and source.get('status') == row.get('source_availability_status')
                   and source.get('status') in {'full_text_available', 'partial_text'}]
        if not sources or all(transport_incomplete(source) for source in sources):
            fail('public_reading_source_observation_mismatch')
        if row.get('transport_verification') not in {source.get('transport_verification', 'legacy_unrecorded') for source in sources}:
            fail('public_transport_lineage_mismatch')
        if type(row.get('article_chars')) is not int or row['article_chars'] <= 0:
            fail('public_article_character_count_invalid')
        validate_ranges(row.get('read_ranges'), row['article_chars'])
        checked, hashes = row.get('checked_table_ids'), row.get('checked_table_text_sha256')
        if (not isinstance(checked, list) or any(not isinstance(sid, str) or not sid for sid in checked) or
                len(checked) != len(set(checked)) or not isinstance(hashes, dict) or set(hashes) != set(checked) or
                type(row.get('checked_table_count')) is not int or row['checked_table_count'] != len(checked) or
                any(not HASH.fullmatch(str(value)) for value in hashes.values())):
            fail('public_checked_table_metadata_invalid')
        required_text(row, 'math_source_note_zh', chinese=True)
        for kind in ('findings_zh', 'limitations_zh'):
            judgments = row.get(kind)
            if not isinstance(judgments, list) or not 1 <= len(judgments) <= 20:
                fail('public_bound_judgments_required')
            for judgment in judgments:
                if not isinstance(judgment, dict) or set(judgment) != {'text_zh', 'source_locator', 'locator_text_sha256'}:
                    fail('public_judgment_schema_invalid')
                required_text(judgment, 'text_zh', chinese=True)
                locator = required_text(judgment, 'source_locator', limit=500)
                ids, bound = [part.strip() for part in locator.split(';')], judgment['locator_text_sha256']
                if (not all(ids) or len(ids) != len(set(ids)) or not isinstance(bound, dict) or set(bound) != set(ids)
                        or any(not HASH.fullmatch(str(value)) for value in bound.values())):
                    fail('public_judgment_locator_hash_invalid')
        if visible(row['read_completed_at']):
            valid.append(row)
    return {'records': valid, 'counts': {'reading_receipt_count': len(valid),
            'AI_read_work_count': len({row['work_id'] for row in valid}), 'as_of': as_of},
            'assurance': ASSURANCE, 'verification_scope': 'public_metadata_consistency_only_not_re_reading',
            'private_source_reverified': False, 'understanding_verified': False}


def import_readings(declarations, payload, observation_path, output, *, cache_root=None, apply=False):
    observations = jsonl(observation_path)
    receipts = validate_readings(declarations, payload, observations, cache_root or Path(observation_path).parent)
    ledger = {}
    old = jsonl(output)
    for row in [*old, *receipts]:
        rid = row.get('reading_id')
        if not rid or (rid in ledger and ledger[rid] != row):
            fail('existing_reading_receipt_conflict')
        ledger[rid] = row
    # Do not re-export a pre-existing malformed/private-bearing ledger row.
    public_audit(list(ledger.values()), payload, observations, '9999-12-31')
    if apply:
        target = Path(output)
        if target.is_symlink() or target.resolve() == Path(observation_path).resolve():
            fail('unsafe_public_ledger_target')
        write_if_changed(target, ''.join(encode(ledger[rid]) + '\n' for rid in sorted(ledger)))
    return {'applied': apply, 'reading_batch_count': len(receipts), 'added': len(ledger) - len(old),
            'public_reading_count': len(ledger), 'assurance': ASSURANCE, 'human_reviewed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'data/catalog')
    parser.add_argument('--observations', type=Path, default=ROOT / '.research/hardware-fulltext/observations.jsonl')
    parser.add_argument('--cache-root', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/hardware-review/fulltext-readings.jsonl')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        payload, _ = load_catalog(args.catalog)
        result = import_readings(json.loads(args.input.read_text(encoding='utf-8')), payload, args.observations,
                                 args.output, cache_root=args.cache_root, apply=args.apply)
        print(encode(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, 'Fulltext reading import failed: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
