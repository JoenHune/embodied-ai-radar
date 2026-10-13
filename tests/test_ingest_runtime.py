import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from catalog_enrichment import ingest_delta
from catalog_store import table_fingerprint, fingerprint, encode
from ingest_runtime import stage, spool_incoming, load_incoming
import test_catalog_ingest as fixtures


class IngestRuntimeTest(unittest.TestCase):
    def test_streamed_table_hash_matches_the_existing_canonical_hash(self):
        for rows in ([], [{'b': '\u673a\u5668\u4eba', 'a': [1, None]}, {'x': {'z': True}}], [{'x': '\U0001f916'}, {'x': '\uffff'}, {'x': '\U0001f916'}]):
            self.assertEqual(table_fingerprint(rows), fingerprint(sorted(rows, key=encode)))
            self.assertEqual(table_fingerprint(rows, disk_sort=True), fingerprint(sorted(rows, key=encode)))

    def test_disk_backed_ingestion_preserves_the_same_authority(self):
        fixture = fixtures.CatalogIngestTest()
        current = fixture.publication()
        incoming = copy.deepcopy(current)
        incoming['source-records'][0]['new_provenance_field'] = 'retained'
        incoming['input_counts'] = {'preprints': 1}
        expected = ingest_delta(copy.deepcopy(current), copy.deepcopy(incoming))
        with tempfile.TemporaryDirectory() as folder:
            spool_incoming(folder, incoming)
            disk = load_incoming(folder)
            self.assertEqual(list(disk['source-records']), list(disk['source-records']))
            self.assertEqual(ingest_delta(copy.deepcopy(current), disk), expected)
            self.assertEqual(disk['input_counts'], incoming['input_counts'])

    def test_absent_source_health_is_not_added_by_spooling(self):
        with tempfile.TemporaryDirectory() as folder:
            spool_incoming(folder, {'works': [], 'source-records': []})
            self.assertNotIn('source-health', load_incoming(folder))

    def test_failed_stage_reports_the_exact_step_and_does_not_return(self):
        with patch('ingest_runtime.wait_resource_headroom', return_value=None), redirect_stdout(io.StringIO()) as out:
            with self.assertRaises(ValueError):
                stage('identity_check', lambda: (_ for _ in ()).throw(ValueError('conflict')))
        records = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(records[-1]['stage'], 'identity_check')
        self.assertEqual(records[-1]['status'], 'catalog_stage_failed')
