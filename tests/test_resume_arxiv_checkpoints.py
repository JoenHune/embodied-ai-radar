import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from resume_arxiv_checkpoints import validated_checkpoint_records


class ResumeCheckpointTest(unittest.TestCase):
    def fixture(self, root):
        cutoff = date(2026, 9, 5)
        query = {'id': 'cs_ro', 'query': 'cat:cs.RO'}
        sources = {'queries': [query]}
        (root / 'config').mkdir()
        (root / 'config/source-registry.json').write_text(json.dumps({'arxiv_sources': sources}))
        scope = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()[:16]
        identity = hashlib.sha256(json.dumps({'query': query, 'month': '2026-09', 'cutoff': cutoff.isoformat(), 'schema': 1}, sort_keys=True).encode()).hexdigest()
        folder = root / 'data/raw/arxiv-v2/weekly' / (cutoff.isoformat() + '-' + scope)
        folder.mkdir(parents=True)
        row = {'arxiv_id': '2609.00001', 'title': 'Robot paper', 'first_submitted': '2026-09-02', 'categories': ['cs.RO']}
        checkpoint = folder / (identity + '.checkpoint.json')
        checkpoint.write_text(json.dumps({'identity': identity, 'records': [row], 'offset': 1, 'total': 2}))
        (folder / '2026-09-cs_ro-00000-to-20260905.xml').write_text(json.dumps({'total': 2, 'rows': [row]}))
        collector = SimpleNamespace(parse_feed=lambda body: (json.loads(body)['total'], json.loads(body)['rows']),
                                    merge_record=lambda old, new, query_id: {**new, 'discovery_queries': [query_id]})
        return cutoff, checkpoint, collector

    def test_partial_pagination_is_verified_without_becoming_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cutoff, checkpoint, collector = self.fixture(root)
            records, evidence = validated_checkpoint_records(root, cutoff, collector)
            self.assertEqual(list(records), ['2609.00001'])
            self.assertEqual(evidence[0]['offset'], 1)
            self.assertEqual(evidence[0]['expected_records'], 2)

    def test_changed_identity_source_fields_and_duplicate_rows_fail_closed(self):
        for change in ('identity', 'title', 'duplicate'):
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                cutoff, checkpoint, collector = self.fixture(root)
                payload = json.loads(checkpoint.read_text())
                if change == 'identity': payload['identity'] = 'wrong'
                elif change == 'title': payload['records'][0]['title'] = 'different'
                else: payload['records'] *= 2; payload['offset'] = 2
                checkpoint.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):
                    validated_checkpoint_records(root, cutoff, collector)
