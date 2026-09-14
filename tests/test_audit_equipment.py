"""Equipment audit entrypoint must also check every hardware-coverage export."""
import contextlib
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import audit_equipment as audit_entry
from catalog_store import encode, save_catalog
from equipment_radar import build_equipment_bundle, equipment_sqlite, export_equipment
from hardware_coverage_export import build_coverage, coverage_sqlite, export_coverage
from pdf_coverage_export import build_pdf_coverage, export_pdf_coverage, pdf_coverage_sqlite, attach_pdf_coverage, API, SOURCE_DOWNLOAD, READING_DOWNLOAD
from test_equipment_radar import fixture
from test_hardware_census import dictionary_fixture
from sqlite_download import local_sqlite_path


def publish_fixture_archive(root, manifest):
    raw = local_sqlite_path(root).read_bytes()
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr('radar.sqlite', raw)
    archive = output.getvalue()
    (root / 'docs/public/downloads/radar.sqlite.zip').write_bytes(archive)
    manifest['downloads'].update(sqlite='/downloads/radar.sqlite.zip', sqlite_integrity={
        'encoding': 'zip', 'sha256': hashlib.sha256(raw).hexdigest(),
        'archive_sha256': hashlib.sha256(archive).hexdigest(), 'bytes': len(raw), 'archive_bytes': len(archive)})
    (root / 'docs/public/api/v1/catalog-manifest.json').write_text(encode(manifest))


def install_fixture(root):
    payload, authority, manifest = fixture()
    manifest.update(equipment={'coverage_api': '/api/v1/equipment/coverage-summary.json', 'readings_api': '/api/v1/equipment/coverage-readings.json', 'pdf_readings_api': API},
                    downloads={'hardware_coverage': '/downloads/equipment/hardware-coverage.jsonl.gz', 'fulltext_readings': '/downloads/equipment/fulltext-readings.jsonl', 'pdf_readings': READING_DOWNLOAD, 'pdf_source_observations': SOURCE_DOWNLOAD})
    dictionary = dictionary_fixture()
    api, downloads = root / 'docs/public/api/v1', root / 'docs/public/downloads'
    (root / 'config').mkdir(parents=True)
    (root / 'config/hardware-dictionary.json').write_text(encode(dictionary))
    (root / 'data/equipment').mkdir(parents=True)
    for table, rows in authority.items():
        (root / 'data/equipment' / (table + '.jsonl')).write_text(''.join(encode(row) + '\n' for row in rows))
    save_catalog(root / 'data/catalog', payload, {})
    equipment = build_equipment_bundle(payload, authority, manifest)
    coverage = build_coverage(payload, authority, dictionary, [], [], manifest)
    pdf = build_pdf_coverage(payload, [], [], manifest, coverage['summary']['dictionary_hash'])
    attach_pdf_coverage(coverage, pdf)
    export_equipment(equipment, api / 'equipment', downloads / 'equipment')
    export_coverage(coverage, api / 'equipment', downloads / 'equipment')
    export_pdf_coverage(pdf, api / 'equipment', downloads / 'equipment')
    sqlite_path = local_sqlite_path(root)
    sqlite_path.parent.mkdir(parents=True)
    with contextlib.closing(sqlite3.connect(sqlite_path)) as connection:
        equipment_sqlite(connection, equipment)
        coverage_sqlite(connection, coverage)
        pdf_coverage_sqlite(connection, pdf)
        connection.execute('CREATE TABLE works (work_id TEXT PRIMARY KEY)')
        connection.executemany('INSERT INTO works VALUES (?)', [(row['work_id'],) for row in payload['works']])
        connection.commit()
    publish_fixture_archive(root, manifest)
    return api, downloads


class EquipmentAuditEntrypointTests(unittest.TestCase):
    def test_entrypoint_checks_coverage_and_opens_sqlite_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            api, downloads = install_fixture(root)
            before = hashlib.sha256(local_sqlite_path(root).read_bytes()).hexdigest()
            archive_before = (downloads / 'radar.sqlite.zip').read_bytes()
            output = io.StringIO()
            with patch.object(audit_entry, 'ROOT', root), contextlib.redirect_stdout(output):
                audit_entry.main()
            result = json.loads(output.getvalue())
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['hardware_coverage']['work_count'], 1)
            self.assertEqual(result['hardware_coverage_all_works']['metadata_screened_work_count'], 1)
            self.assertEqual(result['hardware_coverage_all_works']['full_text_screened_current_dictionary_work_count'], 0)
            self.assertEqual(result['hardware_coverage_included']['verified_relationship_work_count'], 1)
            self.assertEqual(result['hardware_addenda']['status'], 'passed')
            self.assertEqual(result['hardware_addenda']['addendum_review_count'], 0)
            self.assertEqual(result['pdf_reading']['source_work_count'], 0)
            self.assertEqual(result['pdf_reading']['all_work_count'], 0)
            self.assertEqual(result['sqlite_download']['status'], 'passed')
            self.assertEqual(result['sqlite_download']['sha256'], before)
            self.assertEqual(hashlib.sha256(local_sqlite_path(root).read_bytes()).hexdigest(), before)
            self.assertEqual((downloads / 'radar.sqlite.zip').read_bytes(), archive_before)
            self.assertFalse((downloads / 'radar.sqlite').exists())
            self.assertFalse((downloads / 'radar.sqlite.gz').exists())

    def test_equipment_audit_cannot_pass_when_coverage_api_download_or_sqlite_is_tampered(self):
        for target in ('summary', 'gzip', 'sqlite', 'manifest', 'pdf_api', 'pdf_table', 'pdf_download', 'pdf_manifest'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                api, downloads = install_fixture(root)
                if target == 'summary':
                    (api / 'equipment/coverage-summary.json').write_text('{}')
                elif target == 'gzip':
                    (downloads / 'equipment/hardware-coverage.jsonl.gz').unlink()
                elif target == 'sqlite':
                    with contextlib.closing(sqlite3.connect(local_sqlite_path(root))) as connection:
                        connection.execute('DELETE FROM hardware_coverage')
                        connection.commit()
                elif target == 'pdf_api':
                    (api / 'equipment/coverage-pdf-readings.json').write_text('{}')
                elif target == 'pdf_table':
                    with contextlib.closing(sqlite3.connect(local_sqlite_path(root))) as connection:
                        connection.execute('DROP TABLE pdf_reading_receipts')
                        connection.commit()
                elif target == 'pdf_download':
                    (downloads / 'equipment/pdf-readings.jsonl').unlink()
                elif target == 'pdf_manifest':
                    value = json.loads((api / 'catalog-manifest.json').read_text())
                    value['equipment'].pop('pdf_readings_api')
                    (api / 'catalog-manifest.json').write_text(encode(value))
                else:
                    value = json.loads((api / 'catalog-manifest.json').read_text())
                    value['equipment'].pop('coverage_api')
                    (api / 'catalog-manifest.json').write_text(encode(value))
                if target in {'sqlite', 'pdf_table'}:
                    # Rebind a valid archive to the changed DB: the original
                    # semantic SQL audit must still catch missing rows/tables.
                    publish_fixture_archive(root, json.loads((api / 'catalog-manifest.json').read_text()))
                with patch.object(audit_entry, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises((ValueError, FileNotFoundError, sqlite3.OperationalError)):
                        audit_entry.main()

    def test_archive_and_private_database_must_both_match_manifest(self):
        for target in ('missing_archive', 'truncated', 'crc', 'raw_hash', 'archive_hash', 'raw_bytes',
                       'archive_bytes', 'encoding', 'download_path', 'raw_duplicate', 'gzip_duplicate', 'private_db'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                api, downloads = install_fixture(root)
                manifest = json.loads((api / 'catalog-manifest.json').read_text())
                archive_path = downloads / 'radar.sqlite.zip'
                if target == 'missing_archive':
                    archive_path.unlink()
                elif target in {'truncated', 'crc'}:
                    archive = bytearray(archive_path.read_bytes())
                    if target == 'truncated':
                        archive = archive[:-22]
                    else:
                        # Keep DEFLATED data/entry contract valid, but corrupt
                        # its central-directory checksum to exercise full CRC.
                        archive[archive.index(b'PK\x01\x02') + 16] ^= 1
                        with zipfile.ZipFile(io.BytesIO(archive)) as package:
                            with self.assertRaisesRegex(zipfile.BadZipFile, 'CRC'):
                                package.read('radar.sqlite')
                    archive_path.write_bytes(archive)
                    manifest['downloads']['sqlite_integrity'].update(
                        archive_bytes=len(archive), archive_sha256=hashlib.sha256(archive).hexdigest())
                elif target in {'raw_hash', 'archive_hash'}:
                    key = 'sha256' if target == 'raw_hash' else 'archive_sha256'
                    manifest['downloads']['sqlite_integrity'][key] = '0' * 64
                elif target in {'raw_bytes', 'archive_bytes'}:
                    key = 'bytes' if target == 'raw_bytes' else 'archive_bytes'
                    manifest['downloads']['sqlite_integrity'][key] += 1
                elif target == 'encoding':
                    manifest['downloads']['sqlite_integrity']['encoding'] = 'identity'
                elif target == 'download_path':
                    manifest['downloads']['sqlite'] = '/downloads/radar.sqlite'
                elif target == 'raw_duplicate':
                    (downloads / 'radar.sqlite').write_bytes(local_sqlite_path(root).read_bytes())
                elif target == 'gzip_duplicate':
                    (downloads / 'radar.sqlite.gz').write_bytes(b'legacy gzip must not remain public')
                elif target == 'private_db':
                    with contextlib.closing(sqlite3.connect(local_sqlite_path(root))) as connection:
                        connection.execute('CREATE TABLE changed_after_archive (id INTEGER)')
                        connection.commit()
                (api / 'catalog-manifest.json').write_text(encode(manifest))
                with patch.object(audit_entry, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises((ValueError, OSError)):
                        audit_entry.main()

    def test_entrypoint_requires_dictionary_before_reading_or_reporting_coverage(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(audit_entry, 'ROOT', Path(directory)):
            with self.assertRaisesRegex(FileNotFoundError, 'hardware_coverage_dictionary_required'):
                audit_entry.main()

    def test_entrypoint_checks_parent_graph_even_when_four_equipment_tables_are_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_fixture(root)
            review_directory = root / 'data/hardware-review'
            review_directory.mkdir()
            (review_directory / 'section-reviews.jsonl').write_text(encode({'review_id': 'forged:addendum',
                'extends_review_id': 'hardware-section-review:missing-parent'}) + '\n')
            with patch.object(audit_entry, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'addendum_parent_not_found'):
                    audit_entry.main()


if __name__ == '__main__':
    unittest.main()
