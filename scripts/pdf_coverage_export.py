"""Publish PDF source acquisition and explicit AI reading as separate evidence.

No network or private PDF access occurs here. HTML coverage is unchanged;
the same canonical work can have both HTML and PDF receipts, so counts must
not be added. JSONL remains the editable authority and PDFs stay private.
"""
import json
from pathlib import Path

from catalog_store import encode, write_if_changed
from pdf_reading_reviews import visible_public_audit
from source_review_clock import manifest_source_review_clock

ASSURANCE = 'self_attested_AI_reading_not_human_review'
API = '/api/v1/equipment/coverage-pdf-readings.json'
SOURCE_DOWNLOAD = '/downloads/equipment/pdf-source-observations.jsonl'
READING_DOWNLOAD = '/downloads/equipment/pdf-readings.jsonl'
OVERLAYS = {'title', 'relevance_status'}


def raw_records(records):
    return [{key: value for key, value in row.items() if key not in OVERLAYS} for row in records]


def counts(sources, readings):
    source_works = {row['work_id'] for row in sources}
    reading_works = {row['work_id'] for row in readings}
    return {
        'source_count': len(sources), 'source_work_count': len(source_works),
        'included_source_work_count': len({row['work_id'] for row in sources if row['relevance_status'] == 'included'}),
        'receipt_count': len(readings), 'all_work_count': len(reading_works),
        'included_work_count': len({row['work_id'] for row in readings if row['relevance_status'] == 'included'}),
    }


def build_pdf_coverage(payload, source_observations, reading_reviews, manifest, dictionary_hash):
    if not manifest.get('dataset_version') or not manifest.get('data_through') or not dictionary_hash:
        raise ValueError('pdf_coverage_revision_required')
    works = {row['work_id']: row for row in payload['works']}
    if len(works) != len(payload['works']):
        raise ValueError('pdf_coverage_duplicate_canonical_work')
    clock = manifest_source_review_clock(manifest)
    audited = visible_public_audit(list(reading_reviews), payload, list(source_observations), clock['source_review_as_of'])
    def overlay(rows):
        result = []
        for row in rows:
            if row['work_id'] not in works or OVERLAYS & row.keys():
                raise ValueError('pdf_coverage_unknown_work_or_authority_overlay')
            work = works[row['work_id']]
            result.append({**row, 'title': work.get('title') or '',
                           'relevance_status': work.get('relevance', {}).get('status', 'unknown')})
        return result
    sources = sorted(overlay(audited['sources']), key=lambda row: row['source_observation_id'])
    readings = sorted(overlay(audited['records']), key=lambda row: row['reading_id'])
    computed = counts(sources, readings)
    if any(audited['counts'].get(key) != value for key, value in computed.items()):
        raise ValueError('pdf_coverage_audited_counts_mismatch')
    return {'schema_version': '1', 'source_format': 'pdf', **clock, 'dataset_version': manifest['dataset_version'],
            'data_through': manifest['data_through'], 'dictionary_hash': dictionary_hash,
            'assurance': ASSURANCE, 'private_source_reverified': False, 'human_reviewed': False,
            'understanding_verified': False, 'verification_scope': audited['verification_scope'],
            'counts': computed, 'sources': sources, 'records': readings,
            'downloads': {'sources': SOURCE_DOWNLOAD, 'readings': READING_DOWNLOAD},
            'limits': ['PDF acquisition, page identity checks, AI reading and hardware assertions are separate.',
                       'HTML and PDF receipts may belong to the same canonical work; do not add their work counts.',
                       'Page locators are 1-based PDF file pages, not printed page numbers or HTML DOM IDs.',
                       'AI reading is not human review, complete external-media inspection or independent reproduction.',
                       'Original PDF files, page images and extracted paper text are not redistributed.']}


def pdf_summary(bundle):
    return {**bundle['counts'], 'assurance': ASSURANCE, 'api': API,
            **manifest_source_review_clock(bundle),
            'download': READING_DOWNLOAD, 'source_download': SOURCE_DOWNLOAD,
            'overlap_policy': 'not_additive_with_HTML_work_counts'}


def attach_pdf_coverage(html_bundle, pdf_bundle):
    """Keep HTML metrics distinct while exposing PDF state for the same work ID."""
    if html_bundle['summary'].get('data_through') and (
            manifest_source_review_clock(html_bundle['summary']) != manifest_source_review_clock(pdf_bundle)):
        raise ValueError('pdf_coverage_review_clock_mismatch')
    known = {row['work_id'] for row in html_bundle['rows']}
    by_work = {}
    for key, field in (('sources', 'source_count'), ('records', 'reading_count')):
        for record in pdf_bundle[key]:
            if record['work_id'] not in known:
                raise ValueError('pdf_coverage_work_missing_from_HTML_census')
            counts = by_work.setdefault(record['work_id'], {'source_count': 0, 'reading_count': 0})
            counts[field] += 1
    for row in html_bundle['rows']:
        row.pop('pdf', None)
        if row['work_id'] in by_work:
            row['pdf'] = by_work[row['work_id']]
    html_bundle['summary']['pdf_reading'] = pdf_summary(pdf_bundle)
    html_bundle['summary']['body_source_scope'] = 'arxiv_HTML_only; PDF observations and readings are reported separately'
    html_bundle['summary']['optional_work_projection_fields'] = ['pdf.source_count', 'pdf.reading_count']


def export_pdf_coverage(bundle, api_directory, downloads_directory):
    write_if_changed(Path(api_directory) / 'coverage-pdf-readings.json', encode(bundle) + '\n')
    for filename, key in (('pdf-source-observations.jsonl', 'sources'), ('pdf-readings.jsonl', 'records')):
        write_if_changed(Path(downloads_directory) / filename,
                         ''.join(encode(row) + '\n' for row in raw_records(bundle[key])))


def pdf_coverage_sqlite(connection, bundle):
    connection.executescript('''
        CREATE TABLE pdf_source_observations (
            source_observation_id TEXT PRIMARY KEY, work_id TEXT NOT NULL,
            manifestation_id TEXT NOT NULL, relevance_status TEXT NOT NULL,
            payload_json TEXT NOT NULL);
        CREATE TABLE pdf_reading_receipts (
            reading_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, source_observation_id TEXT NOT NULL,
            relevance_status TEXT NOT NULL, page_count INTEGER NOT NULL CHECK(page_count > 0),
            read_completed_at TEXT NOT NULL, payload_json TEXT NOT NULL);
    ''')
    connection.executemany('INSERT INTO pdf_source_observations VALUES (?,?,?,?,?)',
        ((row['source_observation_id'], row['work_id'], row['manifestation_id'], row['relevance_status'], encode(row))
         for row in bundle['sources']))
    connection.executemany('INSERT INTO pdf_reading_receipts VALUES (?,?,?,?,?,?,?)',
        ((row['reading_id'], row['work_id'], row['source_observation_id'], row['relevance_status'],
          row['page_count'], row['read_completed_at'], encode(row)) for row in bundle['records']))


def audit_pdf_coverage(bundle, payload, api_directory, downloads_directory, connection):
    rebuilt = build_pdf_coverage(payload, raw_records(bundle['sources']), raw_records(bundle['records']),
                                bundle, bundle['dictionary_hash'])
    if rebuilt != bundle:
        raise ValueError('pdf_coverage_bundle_mismatch')
    if json.loads((Path(api_directory) / 'coverage-pdf-readings.json').read_text()) != bundle:
        raise ValueError('pdf_coverage_api_mismatch')
    for filename, key in (('pdf-source-observations.jsonl', 'sources'), ('pdf-readings.jsonl', 'records')):
        rows = [json.loads(line) for line in (Path(downloads_directory) / filename).read_text().splitlines() if line.strip()]
        if rows != raw_records(bundle[key]):
            raise ValueError('pdf_coverage_download_mismatch:' + filename)
    for table, id_key, key in (('pdf_source_observations', 'source_observation_id', 'sources'),
                               ('pdf_reading_receipts', 'reading_id', 'records')):
        rows = [json.loads(row[0]) for row in connection.execute(f'SELECT payload_json FROM {table} ORDER BY {id_key}')]
        if rows != bundle[key]:
            raise ValueError('pdf_coverage_sqlite_payload_mismatch:' + table)
        columns = ('source_observation_id', 'work_id', 'manifestation_id', 'relevance_status') if key == 'sources' else (
            'reading_id', 'work_id', 'source_observation_id', 'relevance_status', 'page_count', 'read_completed_at')
        actual = list(connection.execute(f"SELECT {','.join(columns)} FROM {table} ORDER BY {id_key}"))
        if actual != [tuple(row[column] for column in columns) for row in bundle[key]]:
            raise ValueError('pdf_coverage_sqlite_typed_mismatch:' + table)
    source_count, source_works, included_sources = connection.execute('''SELECT COUNT(*),COUNT(DISTINCT work_id),
        COUNT(DISTINCT CASE WHEN relevance_status='included' THEN work_id END) FROM pdf_source_observations''').fetchone()
    reading_count, reading_works, included_readings = connection.execute('''SELECT COUNT(*),COUNT(DISTINCT work_id),
        COUNT(DISTINCT CASE WHEN relevance_status='included' THEN work_id END) FROM pdf_reading_receipts''').fetchone()
    calculated = {'source_count': source_count, 'source_work_count': source_works,
                  'included_source_work_count': included_sources, 'receipt_count': reading_count,
                  'all_work_count': reading_works, 'included_work_count': included_readings}
    if calculated != bundle['counts']:
        raise ValueError('pdf_coverage_sqlite_count_mismatch')
    return {'status': 'passed', **calculated, 'private_source_reverified': False}
