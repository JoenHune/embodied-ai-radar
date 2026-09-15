#!/usr/bin/env python3
"""Offline PDF provenance and explicit AI reading receipts; default DRY RUN.

Input {schema_version: '1', sources: [...], readings: [...]} never implies
reading merely because a PDF was downloaded/extracted. sources contain
work_id, manifestation_id, landing/pdf {url, sha256, cache_ref, observed_at,
transport}, and identity_check. A not_checked identity is permitted for a
source-only batch, but cannot back a reading. Identity is an AI declaration,
not an automatic title/PDF Info comparison. See validate_declarations.

PDF page text is pypdf 6.10.0 extract_text(extraction_mode='plain'), with CRLF
and CR normalized to LF only. Page keys are decimal 1-based strings. The
document hash is SHA256 of catalog_store.encode(page_texts), preserving page
boundaries. Text and caches stay private. public_audit imports no PDF library
and checks metadata consistency only; it does not fetch or re-read anything.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from catalog_store import encode, fingerprint, load_catalog, write_if_changed

ROOT = Path(__file__).resolve().parents[1]
ASSURANCE = 'self_attested_AI_reading_not_human_review'
EXTRACTOR_VERSION = 'pypdf-6.10.0/plain-v1'
TEXT_SCOPE = 'complete_available_pdf_text'
HASH = re.compile(r'^[0-9a-f]{64}$')
PRIVATE = re.compile(r'file://|/Users/|/home/|/private/|\.research/|[A-Za-z]:\\')
SOURCE_KEYS = set('schema_version source_observation_id work_id manifestation_id source_record_id source_format source_url landing_url landing_sha256 pdf_sha256 observed_at landing_observed_at landing_transport pdf_transport page_count page_text_sha256 page_text_characters document_text_sha256 extractor_version edition edition_label version identity_check identity_status license_status status metadata_sha256 landing_identity pdf_link_evidence'.split())
READING_KEYS = set('schema_version reading_id source_observation_id work_id manifestation_id source_format source_url pdf_sha256 observed_at edition_label version extractor_version document_text_sha256 page_count page_text_sha256 read_pages read_completed_at reader_kind reading_status assurance human_reviewed understanding_verified verification_scope text_scope checked_table_count tables_exhaustive visual_pages_checked supplementary_materials_inspected publisher_fulltext_or_media_completeness_verified findings_zh limitations_zh declaration_sha256'.split())
TRANSPORT_KEYS = set('http_status returncode complete truncated response_bytes content_length'.split())
IDENTITY_KEYS = set('status reader_kind checked_at source_pages title_checked authors_checked identifier_or_venue_checked differences_zh reason_zh'.split())
READING_DECLARATION_KEYS = set('source_observation_id work_id manifestation_id source_format source_url pdf_sha256 observed_at edition_label version extractor_version document_text_sha256 page_count page_text_sha256 read_pages read_completed_at reader_kind reading_status checked_table_count visual_pages_checked supplementary_materials_inspected human_reviewed findings_zh limitations_zh'.split())


def fail(message):
    raise ValueError('pdf_reading_review:' + message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def fields(row, required, optional=()):
    if not isinstance(row, dict) or set(row) - set(required) - set(optional) or set(required) - set(row):
        fail('unknown_private_or_missing_fields')


def text(value, label, limit=1000, chinese=False):
    if (not isinstance(value, str) or not value.strip() or len(value) > limit or PRIVATE.search(value)
            or any(ord(c) < 32 for c in value)):
        fail('invalid_or_private_' + label)
    if chinese and not re.search(r'[\u3400-\u9fff]', value):
        fail('chinese_judgment_required:' + label)
    return value


def digest(value):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        fail('invalid_sha256')
    return value


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        fail('UTC_timestamp_required')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        fail('invalid_timestamp')


def cutoff(as_of=None):
    if as_of is None:
        return datetime.now(timezone.utc)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(as_of)):
        as_of += 'T23:59:59Z'
    return timestamp(as_of)


def url(value):
    text(value, 'url', 2000)
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.port not in {None, 443} or parsed.query or parsed.fragment):
        fail('clean_https_url_required')
    return value


def arxiv_url(value):
    parsed = urlsplit(str(value or ''))
    if parsed.hostname not in {'arxiv.org', 'www.arxiv.org'}:
        return None
    match = re.fullmatch(r'/(abs|pdf)/(\d{4}\.\d{4,5}|[a-zA-Z.-]+/\d{7})(v[1-9]\d*)?(?:\.pdf)?', parsed.path)
    return match.groups() if match else None


def _catalog(payload):
    result = []
    for table, key in [('works', 'work_id'), ('manifestations', 'manifestation_id'), ('source-records', 'source_record_id')]:
        rows = payload.get(table, [])
        index = {row[key]: row for row in rows}
        if len(index) != len(rows):
            fail('duplicate_catalog_' + table)
        result.append(index)
    versions = {}
    for row in [*payload.get('text-snapshots', []), *payload.get('manifestations', [])]:
        identity = arxiv_url(row.get('source_url') or row.get('url'))
        version = row.get('version') or (identity[2] if identity else None)
        if version and re.fullmatch(r'v[1-9]\d*', version):
            versions.setdefault(row.get('work_id'), {})[version] = row.get('title')
    result.append(versions)
    result.append(payload.get('text-snapshots', []))
    return result


def _arxiv_version_date_provenance(work, arxiv_id, version, catalog):
    """An undated arXiv series is not the publication year of each version.

    Only a source-bound, explicitly dated version snapshot can supply this
    check. Retrieval-only dates, other editions, and conflicting years cannot.
    Keep the original manifestation year unchanged in the edition record.
    """
    from versioned_text import validate_snapshot
    candidates = [row for row in catalog[4] if row.get('work_id') == work['work_id'] and
                  row.get('version') == version and row.get('available_at') is not None]
    if not candidates:
        return None
    proofs, years = [], set()
    for row in candidates:
        identity = arxiv_url(url(row.get('source_url')))
        if (identity != ('abs', arxiv_id, version) or
                validate_snapshot(row, work, catalog[2]) or
                not str(row.get('basis', '')).endswith((':current_metadata_updated_at', ':explicit_v1_published_equals_updated'))):
            fail('arxiv_version_publication_date_provenance_invalid')
        years.add(int(row['available_at'][:4]))
        proofs.append({key: row[key] for key in ('snapshot_id', 'source_record_id', 'source_url',
                                                'available_at', 'date_precision', 'content_digest')})
    if len(years) != 1 or len({row['snapshot_id'] for row in proofs}) != len(proofs):
        fail('arxiv_version_publication_year_ambiguous')
    return {'basis': 'validated_version_text_snapshot_publication_date', 'year': years.pop(),
            'text_snapshot_sources': sorted(proofs, key=lambda row: row['snapshot_id'])}


def _binding(row, catalog):
    works, manifestations, records, versions = catalog[:4]
    wid, mid = row.get('work_id'), row.get('manifestation_id')
    if wid not in works or mid not in manifestations or manifestations[mid].get('work_id') != wid:
        fail('unknown_or_mismatched_manifestation')
    work, manifest = works[wid], manifestations[mid]
    sid = manifest.get('source_record_id')
    if sid not in records:
        fail('missing_manifestation_source_record')
    landing, pdf_url = url(row['landing_url']), url(row['source_url'])
    linked = {manifest.get('url'), records[sid].get('url')}
    aid = arxiv_url(landing)
    version = None
    if aid:
        canonical = str(work.get('identifiers', {}).get('arxiv') or '').removeprefix('arxiv:')
        canonical = re.sub(r'v[1-9]\d*$', '', canonical)
        if '://' in canonical:
            identity = arxiv_url(canonical)
            canonical = identity[1] if identity else ''
        target = arxiv_url(pdf_url)
        if (aid[0] != 'abs' or not aid[2] or aid[1] != canonical or not target
                or target != ('pdf', aid[1], aid[2]) or not any(
                    arxiv_url(entry) and arxiv_url(entry)[:2] == ('abs', aid[1]) for entry in linked)):
            fail('arxiv_manifestation_version_or_link_mismatch')
        version = aid[2]
        if version not in versions.get(wid, {}):
            fail('arxiv_version_not_in_catalog_history')
    elif landing not in linked:
        fail('landing_not_linked_to_manifestation')
    edition = {'kind': manifest.get('kind'), 'venue': manifest.get('venue'), 'year': manifest.get('year'),
               'doi': work.get('identifiers', {}).get('doi'), 'arxiv_version': version}
    if version and edition['kind'] == 'preprint' and edition['year'] is None:
        provenance = _arxiv_version_date_provenance(work, canonical, version, catalog)
        if provenance is not None:
            edition['arxiv_version_date_provenance'] = provenance
    label = f'arXiv {version}' if version else f"{manifest.get('venue')} {manifest.get('year')}"
    return sid, edition, label, version


def private_bytes(reference, cache_root):
    """Open each path component with O_NOFOLLOW; do not execute any cached data."""
    if not isinstance(reference, str) or not reference or '..' in Path(reference).parts:
        fail('unsafe_cache_reference')
    root = Path(cache_root).absolute()
    if root == Path(root.anchor):
        fail('unsafe_cache_root')
    original = Path(reference)
    original = original.absolute() if original.is_absolute() else root / original
    try:
        parts = original.relative_to(root).parts
    except ValueError:
        fail('cache_outside_private_root')
    if not parts or any(parent.is_symlink() for parent in (root, *root.parents)):
        fail('unsafe_cache_symlink')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(root, flags | os.O_DIRECTORY)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, flags | os.O_DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        leaf = os.open(parts[-1], flags | getattr(os, 'O_NONBLOCK', 0), dir_fd=fd)
        try:
            if not stat.S_ISREG(os.fstat(leaf).st_mode):
                fail('cache_not_regular_file')
            with os.fdopen(leaf, 'rb', closefd=False) as handle:
                raw = handle.read(100_000_001)
        finally:
            os.close(leaf)
    finally:
        os.close(fd)
    if len(raw) > 100_000_000:
        fail('cache_too_large')
    return raw


def extract_pdf(raw):
    """Return private text plus deterministic metadata; this never declares reading."""
    import pypdf  # deliberately lazy: public audit does not require this dependency
    if pypdf.__version__ != '6.10.0':
        fail('pypdf_6_10_0_required_for_reproducible_extraction')
    if not raw.startswith(b'%PDF-') or not raw.rstrip().endswith(b'%%EOF'):
        fail('not_pdf_or_truncated')
    try:
        reader = pypdf.PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 2000:
            fail('encrypted_or_invalid_page_count')
        texts = [(page.extract_text(extraction_mode='plain') or '').replace('\r\n', '\n').replace('\r', '\n')
                 for page in reader.pages]
    except Exception as exc:
        fail('PDF_parse_or_extraction_failed:' + type(exc).__name__)
    return {'extractor_version': EXTRACTOR_VERSION, 'page_count': len(texts), 'page_texts': texts,
            'page_text_sha256': {str(i): sha256(value.encode()) for i, value in enumerate(texts, 1)},
            'page_text_characters': {str(i): len(value) for i, value in enumerate(texts, 1)},
            'document_text_sha256': sha256(encode(texts).encode())}


def normalized(value):
    return ''.join(char for char in unicodedata.normalize('NFKC', str(value)).casefold() if char.isalnum())


def _same_pdf_target(citation_url, target):
    a, b = urlsplit(citation_url), urlsplit(target)
    if a.scheme not in {'http', 'https'} or a.username or a.password or a.query or a.fragment:
        return False
    if (a.hostname, a.port, a.path) == (b.hostname, b.port, b.path):
        return True
    ca, cb = arxiv_url(citation_url), arxiv_url(target)
    return bool(ca and cb and ca[:2] == cb[:2] == ('pdf', cb[1]) and ca[2] is None)


def landing_evidence(raw, landing_url, target):
    """Only the page's citation PDF (or its same-resource explicit anchor)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw, 'html.parser')
    def meta(name):
        return [node.get('content', '').strip() for node in soup.select(f'meta[name="{name}"]') if node.get('content', '').strip()]
    citations = meta('citation_pdf_url')
    matching = [value for value in citations if _same_pdf_target(urljoin(landing_url, value), target)]
    anchors = [node for node in soup.select('a[href]') if urljoin(landing_url, node['href']) == target]
    if not matching or (target not in [urljoin(landing_url, value) for value in citations] and not anchors):
        fail('PDF_URL_not_actually_linked_from_landing_citation')
    if not meta('citation_title') or len(set(meta('citation_title'))) != 1 or not meta('citation_author'):
        fail('landing_citation_title_and_authors_required')
    dates = meta('citation_publication_date') or meta('citation_date')
    year = int(dates[0][:4]) if dates and re.match(r'^\d{4}', dates[0]) else None
    dois = meta('citation_doi') or re.findall(r'10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+', soup.get_text(' ', strip=True))
    venues = meta('citation_conference_title') or meta('citation_journal_title') or meta('citation_inbook_title')
    evidence = {'citation_pdf_url': urljoin(landing_url, matching[0]),
                'anchor_href': anchors[0]['href'] if anchors else None}
    identity = {'title': meta('citation_title')[0], 'authors': meta('citation_author'), 'doi_candidates': sorted(set(dois)),
                'venue': venues[0] if venues else None, 'publication_year': year}
    return identity, evidence


def _landing_identity(row, catalog):
    identity, link = row['landing_identity'], row['pdf_link_evidence']
    fields(identity, {'title', 'authors', 'doi_candidates', 'venue', 'publication_year'})
    fields(link, {'citation_pdf_url', 'anchor_href'})
    work = catalog[0][row['work_id']]
    allowed_titles = [work.get('title')]
    if row['version']:
        allowed_titles.append(catalog[3].get(row['work_id'], {}).get(row['version']))
    if normalized(text(identity['title'], 'landing_title')) not in {normalized(v) for v in allowed_titles if v}:
        fail('landing_citation_title_mismatch')
    if not isinstance(identity['authors'], list) or not identity['authors']:
        fail('landing_authors_required')
    for author in identity['authors']:
        text(author, 'landing_author', 300)
    if not isinstance(identity['doi_candidates'], list):
        fail('invalid_landing_DOIs')
    for doi in identity['doi_candidates']:
        text(doi, 'landing_DOI', 300)
    expected_doi = row['edition']['doi']
    if expected_doi and str(expected_doi).casefold() not in {value.rstrip('.,);').casefold() for value in identity['doi_candidates']}:
        fail('landing_DOI_mismatch_or_missing')
    year = identity['publication_year']
    expected_year = row['edition'].get('arxiv_version_date_provenance', {}).get('year', row['edition']['year'])
    if type(year) is not int or year != expected_year:
        fail('landing_publication_year_mismatch_or_missing')
    if not row['version']:
        venue = text(identity['venue'], 'landing_venue', 300)
        expected = normalized(row['edition']['venue'])
        venue_name = {'rss': 'roboticsscienceandsystems', 'corl': 'conferenceonrobotlearning'}.get(expected, expected)
        if venue_name not in normalized(venue):
            fail('landing_venue_mismatch')
    if not _same_pdf_target(link['citation_pdf_url'], row['source_url']):
        fail('citation_PDF_binding_mismatch')
    if link['anchor_href'] is not None:
        text(link['anchor_href'], 'PDF_anchor', 2000)
        if urljoin(row['landing_url'], link['anchor_href']) != row['source_url']:
            fail('PDF_anchor_binding_mismatch')
    elif link['citation_pdf_url'] != row['source_url']:
        fail('actual_anchor_required_for_nonidentical_citation_URL')


def _transport(row, raw=None):
    fields(row, TRANSPORT_KEYS, {'content_type'})
    if 'content_type' in row:
        text(row['content_type'], 'content_type', 200)
    if (type(row['http_status']) is not int or row['http_status'] != 200 or type(row['returncode']) is not int
            or row['returncode'] != 0 or row['complete'] is not True or row['truncated'] is not False
            or type(row['response_bytes']) is not int or row['response_bytes'] <= 0
            or (row['content_length'] is not None and (type(row['content_length']) is not int
                or row['content_length'] != row['response_bytes']))):
        fail('incomplete_or_invalid_transport')
    if raw is not None and row['response_bytes'] != len(raw):
        fail('cached_response_length_mismatch')


def _pages(value, count, *, complete=False, nonempty=False):
    if (not isinstance(value, list) or any(type(item) is not int or not 1 <= item <= count for item in value)
            or value != sorted(set(value)) or (nonempty and not value)
            or (complete and value != list(range(1, count + 1)))):
        fail('invalid_incomplete_or_duplicate_pages')
    return value


def _page_metadata(row):
    count = row.get('page_count')
    if type(count) is not int or not 1 <= count <= 2000 or row.get('extractor_version') != EXTRACTOR_VERSION:
        fail('invalid_page_count_or_extractor')
    hashes = row.get('page_text_sha256')
    if not isinstance(hashes, dict) or set(hashes) != {str(n) for n in range(1, count + 1)}:
        fail('incomplete_page_hashes')
    for value in hashes.values():
        digest(value)
    digest(row.get('document_text_sha256'))
    if 'page_text_characters' in row:
        sizes = row['page_text_characters']
        if (not isinstance(sizes, dict) or set(sizes) != set(hashes)
                or any(type(value) is not int or value < 0 for value in sizes.values())):
            fail('invalid_page_character_counts')


def _identity(identity, count, observed, latest):
    if identity == {'status': 'not_checked'}:
        return
    fields(identity, IDENTITY_KEYS)
    if (identity['status'] != 'same_work_confirmed' or identity['reader_kind'] != 'AI'
            or any(identity[key] is not True for key in ('title_checked', 'authors_checked', 'identifier_or_venue_checked'))):
        fail('explicit_multifactor_AI_identity_check_required')
    when = timestamp(identity['checked_at'])
    if not observed <= when <= latest:
        fail('identity_check_time_invalid')
    _pages(identity['source_pages'], count, nonempty=True)
    for key in ('differences_zh', 'reason_zh'):
        text(identity[key], key, chinese=True)


def source_id(row):
    keys = ('work_id', 'manifestation_id', 'landing_url', 'landing_sha256', 'source_url', 'pdf_sha256', 'observed_at')
    return 'pdf-source:' + fingerprint([row[key] for key in keys])[:24]


def _source(row, catalog, latest):
    fields(row, SOURCE_KEYS)
    if PRIVATE.search(encode(row)):
        fail('private_public_source')
    if (row['schema_version'] != '1' or row['source_format'] != 'pdf' or row['status'] != 'pdf_available'
            or row['license_status'] != 'unknown'):
        fail('invalid_source_schema_or_license_overclaim')
    expected = _binding(row, catalog)
    if (row['source_record_id'], row['edition'], row['edition_label'], row['version']) != expected:
        fail('edition_or_source_record_mismatch')
    digest(row['landing_sha256'])
    digest(row['pdf_sha256'])
    observed = timestamp(row['observed_at'])
    if not timestamp(row['landing_observed_at']) <= observed <= latest:
        fail('source_time_invalid_or_future')
    _transport(row['landing_transport'])
    _transport(row['pdf_transport'])
    _page_metadata(row)
    _landing_identity(row, catalog)
    _identity(row['identity_check'], row['page_count'], observed, latest)
    if row['identity_status'] != row['identity_check']['status']:
        fail('identity_status_mismatch')
    if row['source_observation_id'] != source_id(row):
        fail('source_id_or_hash_binding_mismatch')
    if row['metadata_sha256'] != fingerprint({key: value for key, value in row.items() if key != 'metadata_sha256'}):
        fail('source_metadata_hash_mismatch')


def _judgments(value, count):
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        fail('brief_page_bound_judgments_required')
    for row in value:
        fields(row, {'text_zh', 'source_pages'})
        text(row['text_zh'], 'judgment', chinese=True)
        _pages(row['source_pages'], count, nonempty=True)


def reading_id(source):
    return 'pdf-reading:' + fingerprint([source['source_observation_id'], source['pdf_sha256'],
                source['extractor_version'], source['document_text_sha256'], TEXT_SCOPE])[:24]


def _reading(row, sources, latest):
    fields(row, READING_KEYS)
    if PRIVATE.search(encode(row)):
        fail('private_public_reading')
    source = sources.get(row['source_observation_id'])
    if not source or source['identity_check']['status'] != 'same_work_confirmed':
        fail('reading_requires_explicit_identity_checked_source')
    for key in ('work_id', 'manifestation_id', 'source_format', 'source_url', 'pdf_sha256', 'observed_at',
                'edition_label', 'version', 'extractor_version', 'document_text_sha256', 'page_count', 'page_text_sha256'):
        if row[key] != source[key]:
            fail('reading_source_binding_mismatch:' + key)
    constants = {'schema_version': '1', 'reader_kind': 'AI', 'reading_status': 'completed', 'assurance': ASSURANCE,
                 'verification_scope': 'source_hash_pdf_pages_and_explicit_declaration_only', 'text_scope': TEXT_SCOPE}
    if any(row[key] != value for key, value in constants.items()):
        fail('explicit_completed_AI_reading_required')
    for key in ('human_reviewed', 'understanding_verified', 'tables_exhaustive', 'supplementary_materials_inspected',
                'publisher_fulltext_or_media_completeness_verified'):
        if row[key] is not False:
            fail('reading_overclaims_or_invalid_boolean')
    completed = timestamp(row['read_completed_at'])
    if not timestamp(source['identity_check']['checked_at']) <= completed <= latest:
        fail('reading_time_invalid_or_future')
    _page_metadata(row)
    _pages(row['read_pages'], row['page_count'], complete=True)
    _pages(row['visual_pages_checked'], row['page_count'])
    if any(int(page) not in row['visual_pages_checked'] for page, chars in source['page_text_characters'].items() if chars == 0):
        fail('textless_page_requires_visual_check')
    if type(row['checked_table_count']) is not int or not 0 <= row['checked_table_count'] <= 10000:
        fail('invalid_checked_table_count')
    _judgments(row['findings_zh'], row['page_count'])
    _judgments(row['limitations_zh'], row['page_count'])
    if row['declaration_sha256'] != fingerprint({key: row[key] for key in READING_DECLARATION_KEYS}):
        fail('reading_declaration_hash_mismatch')
    if row['reading_id'] != reading_id(source):
        fail('reading_id_mismatch')


def public_audit(records, payload, public_observations, as_of):
    """Metadata-only consistency, NOT re-reading, PDF parsing or signature verification."""
    if not isinstance(records, list) or not isinstance(public_observations, list):
        fail('public_lists_required')
    catalog, latest = _catalog(payload), cutoff(as_of)
    sources = {}
    for source in public_observations:
        _source(source, catalog, latest)
        sid = source['source_observation_id']
        if sid in sources:
            fail('duplicate_public_source')
        sources[sid] = source
    seen = set()
    for row in records:
        _reading(row, sources, latest)
        if row['reading_id'] in seen:
            fail('duplicate_public_reading')
        seen.add(row['reading_id'])
    works = catalog[0]
    read_works = {row['work_id'] for row in records}
    source_works = {row['work_id'] for row in public_observations}
    included = lambda ids: sum(works[wid].get('relevance', {}).get('status', works[wid].get('relevance_status')) == 'included' for wid in ids)
    return {'records': records, 'sources': public_observations,
            'counts': {'all_work_count': len(read_works), 'included_work_count': included(read_works),
                       'receipt_count': len(records), 'source_count': len(sources), 'source_work_count': len(source_works),
                       'included_source_work_count': included(source_works)},
            'assurance': ASSURANCE, 'verification_scope': 'public_metadata_consistency_only_not_re_reading',
            'private_source_reverified': False, 'understanding_verified': False}


def visible_public_audit(records, payload, public_observations, as_of):
    """Audit all metadata, then expose only observations/readings at this clock.

    No PDF bytes, extraction or network. Invalid future rows must not be hidden
    by filtering. This is shared by PDF coverage and editorial annotations.
    """
    from source_review_clock import visible, utc_cutoff
    history = public_audit(records, payload, public_observations, '9999-12-31T23:59:59Z')
    sources = [row for row in history['sources'] if visible(row['observed_at'], as_of) and
               (row['identity_check']['status'] == 'not_checked' or visible(row['identity_check']['checked_at'], as_of))]
    source_ids = {row['source_observation_id'] for row in sources}
    readings = [row for row in history['records'] if row['source_observation_id'] in source_ids and
                visible(row['read_completed_at'], as_of)]
    # Ledger timestamps have whole-second precision. Filter with the exact
    # caller clock first, then floor only this validator cutoff (not the data).
    audit_cutoff = utc_cutoff(as_of).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    return public_audit(readings, payload, sources, audit_cutoff)


def validate_declarations(declarations, payload, cache_root, *, as_of=None):
    fields(declarations, {'schema_version', 'sources', 'readings'})
    if declarations['schema_version'] != '1' or not all(isinstance(declarations[key], list) for key in ('sources', 'readings')):
        fail('explicit_source_and_reading_lists_required')
    catalog, latest = _catalog(payload), cutoff(as_of)
    sources = []
    for declaration in declarations['sources']:
        fields(declaration, {'work_id', 'manifestation_id', 'landing', 'pdf', 'identity_check'},
               {'page_count', 'page_text_sha256', 'document_text_sha256', 'extractor_version'})
        material = {}
        for kind in ('landing', 'pdf'):
            item = declaration[kind]
            fields(item, {'url', 'sha256', 'cache_ref', 'observed_at', 'transport'})
            url(item['url'])
            digest(item['sha256'])
            raw = private_bytes(item['cache_ref'], cache_root)
            if sha256(raw) != item['sha256']:
                fail(kind + '_cache_hash_mismatch')
            _transport(item['transport'], raw)
            material[kind] = raw
        landing, pdf = declaration['landing'], declaration['pdf']
        landing_identity, link_evidence = landing_evidence(material['landing'], landing['url'], pdf['url'])
        row = {'schema_version': '1', 'work_id': declaration['work_id'], 'manifestation_id': declaration['manifestation_id'],
               'source_format': 'pdf', 'source_url': pdf['url'], 'landing_url': landing['url'],
               'landing_sha256': landing['sha256'], 'pdf_sha256': pdf['sha256'], 'observed_at': pdf['observed_at'],
               'landing_observed_at': landing['observed_at'], 'landing_transport': landing['transport'],
               'pdf_transport': pdf['transport'], 'identity_check': declaration['identity_check'],
               'landing_identity': landing_identity, 'pdf_link_evidence': link_evidence,
               'identity_status': declaration['identity_check'].get('status'), 'license_status': 'unknown', 'status': 'pdf_available'}
        sid, edition, label, version = _binding(row, catalog)
        row.update(source_record_id=sid, edition=edition, edition_label=label, version=version)
        extracted = extract_pdf(material['pdf'])
        extracted.pop('page_texts')
        for key in ('page_count', 'page_text_sha256', 'document_text_sha256', 'extractor_version'):
            if key in declaration and declaration[key] != extracted[key]:
                fail('declared_extraction_hash_mismatch:' + key)
        row.update(extracted)
        row['source_observation_id'] = source_id(row)
        row['metadata_sha256'] = fingerprint(row)
        _source(row, catalog, latest)
        sources.append(row)
    index = {row['source_observation_id']: row for row in sources}
    if len(index) != len(sources):
        fail('duplicate_source_declaration')
    readings = []
    for declaration in declarations['readings']:
        fields(declaration, READING_DECLARATION_KEYS)
        source = index.get(declaration['source_observation_id'])
        if not source:
            fail('reading_requires_privately_revalidated_source_in_batch')
        row = {**declaration, 'schema_version': '1', 'reading_id': reading_id(source), 'assurance': ASSURANCE,
               'understanding_verified': False, 'verification_scope': 'source_hash_pdf_pages_and_explicit_declaration_only',
               'text_scope': TEXT_SCOPE, 'tables_exhaustive': False, 'publisher_fulltext_or_media_completeness_verified': False,
               'declaration_sha256': fingerprint(declaration)}
        _reading(row, index, latest)
        readings.append(row)
    public_audit(readings, payload, sources, as_of or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    return {'sources': sources, 'readings': readings}


def jsonl(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def import_reviews(declarations, payload, source_output, reading_output, *, cache_root, apply=False, as_of=None):
    paths = [Path(source_output), Path(reading_output)]
    if paths[0].absolute() == paths[1].absolute():
        fail('distinct_public_ledgers_required')
    for target in paths:
        if any(part.is_symlink() for part in (target, *target.parents)):
            fail('unsafe_output_symlink')
    batch = validate_declarations(declarations, payload, cache_root, as_of=as_of)
    merged, added = {}, {}
    for kind, key, target in zip(('sources', 'readings'), ('source_observation_id', 'reading_id'), paths):
        old = jsonl(target)
        index = {}
        for row in old:
            if row.get(key) in index:
                fail('duplicate_existing_ledger_record')
            index[row.get(key)] = row
        for row in batch[kind]:
            if row[key] in index and index[row[key]] != row:
                fail('existing_ledger_conflict')
            index[row[key]] = row
        merged[kind] = [index[item] for item in sorted(index)]
        added[kind] = len(index) - len(old)
    audit = public_audit(merged['readings'], payload, merged['sources'],
                         as_of or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    # Both complete merged ledgers have passed validation before the first write.
    if apply:
        for target, kind in zip(paths, ('sources', 'readings')):
            write_if_changed(target, ''.join(encode(row) + '\n' for row in merged[kind]))
    return {'applied': apply, 'added': added, 'counts': audit['counts'], 'assurance': ASSURANCE}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'data/catalog')
    parser.add_argument('--cache-root', type=Path, default=ROOT / '.research')
    parser.add_argument('--source-output', type=Path, default=ROOT / 'data/hardware-review/pdf-source-observations.jsonl')
    parser.add_argument('--reading-output', type=Path, default=ROOT / 'data/hardware-review/pdf-readings.jsonl')
    parser.add_argument('--as-of')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        payload, _ = load_catalog(args.catalog)
        result = import_reviews(json.loads(args.input.read_text()), payload, args.source_output, args.reading_output,
                                cache_root=args.cache_root, apply=args.apply, as_of=args.as_of)
        print(encode(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError) as exc:
        parser.exit(2, 'PDF reading import failed: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
