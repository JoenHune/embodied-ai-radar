"""Equipment audit entrypoint must also check every hardware-coverage export."""
import contextlib
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import audit_equipment as audit_entry
from catalog_store import encode, save_catalog
from equipment_radar import build_equipment_bundle, equipment_sqlite, export_equipment
from hardware_coverage_export import build_coverage, coverage_sqlite, export_coverage
from test_equipment_radar import fixture
from test_hardware_census import dictionary_fixture


def install_fixture(root):
    payload, authority, manifest = fixture()
    manifest.update(equipment={'coverage_api': '/api/v1/equipment/coverage-summary.json'},
                    downloads={'hardware_coverage': '/downloads/equipment/hardware-coverage.jsonl.gz'})
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
    export_equipment(equipment, api / 'equipment', downloads / 'equipment')
    export_coverage(coverage, api / 'equipment', downloads / 'equipment')
    (api / 'catalog-manifest.json').write_text(encode(manifest))
    with contextlib.closing(sqlite3.connect(downloads / 'radar.sqlite')) as connection:
        equipment_sqlite(connection, equipment)
        coverage_sqlite(connection, coverage)
        connection.execute('CREATE TABLE works (work_id TEXT PRIMARY KEY)')
        connection.executemany('INSERT INTO works VALUES (?)', [(row['work_id'],) for row in payload['works']])
        connection.commit()
    return api, downloads


class EquipmentAuditEntrypointTests(unittest.TestCase):
    def test_entrypoint_checks_coverage_and_opens_sqlite_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            api, downloads = install_fixture(root)
            before = hashlib.sha256((downloads / 'radar.sqlite').read_bytes()).hexdigest()
            output = io.StringIO()
            with patch.object(audit_entry, 'ROOT', root), contextlib.redirect_stdout(output):
                audit_entry.main()
            result = json.loads(output.getvalue())
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['hardware_coverage']['work_count'], 1)
            self.assertEqual(result['hardware_coverage_all_works']['metadata_screened_work_count'], 1)
            self.assertEqual(result['hardware_coverage_all_works']['full_text_screened_current_dictionary_work_count'], 0)
            self.assertEqual(result['hardware_coverage_included']['verified_relationship_work_count'], 1)
            self.assertEqual(hashlib.sha256((downloads / 'radar.sqlite').read_bytes()).hexdigest(), before)

    def test_equipment_audit_cannot_pass_when_coverage_api_download_or_sqlite_is_tampered(self):
        for target in ('summary', 'gzip', 'sqlite', 'manifest'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                api, downloads = install_fixture(root)
                if target == 'summary':
                    (api / 'equipment/coverage-summary.json').write_text('{}')
                elif target == 'gzip':
                    (downloads / 'equipment/hardware-coverage.jsonl.gz').unlink()
                elif target == 'sqlite':
                    with contextlib.closing(sqlite3.connect(downloads / 'radar.sqlite')) as connection:
                        connection.execute('DELETE FROM hardware_coverage')
                        connection.commit()
                else:
                    value = json.loads((api / 'catalog-manifest.json').read_text())
                    value['equipment'].pop('coverage_api')
                    (api / 'catalog-manifest.json').write_text(encode(value))
                with patch.object(audit_entry, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        audit_entry.main()

    def test_entrypoint_requires_dictionary_before_reading_or_reporting_coverage(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(audit_entry, 'ROOT', Path(directory)):
            with self.assertRaisesRegex(FileNotFoundError, 'hardware_coverage_dictionary_required'):
                audit_entry.main()


if __name__ == '__main__':
    unittest.main()
