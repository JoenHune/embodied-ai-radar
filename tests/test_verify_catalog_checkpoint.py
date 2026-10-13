import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from catalog_store import save_catalog
from verify_catalog_checkpoint import verify_checkpoint


class VerifyCheckpointTest(unittest.TestCase):
    def fixture(self, root):
        return save_catalog(root, {'works': [{'work_id': 'arxiv:2601.00001', 'title': 'Robot paper'}]}, {'data_through': '2026-10-09'})

    def bytes(self, root):
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

    def test_every_table_verified_with_no_source_or_catalog_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); metadata = self.fixture(root); before = self.bytes(root)
            with contextlib.redirect_stdout(io.StringIO()):
                result = verify_checkpoint(root, metadata['catalog_hash'], '2026-10-09')
            self.assertEqual(result['counts']['works'], 1)
            self.assertEqual(self.bytes(root), before)

    def test_same_manifest_with_changed_work_or_wrong_cutoff_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); metadata = self.fixture(root)
            with self.assertRaises(ValueError): verify_checkpoint(root, metadata['catalog_hash'], '2026-10-08')
            path = next(p for p in (root / 'works').glob('*.jsonl') if p.stat().st_size)
            row = json.loads(path.read_text()); row['title'] = 'Different source'; path.write_text(json.dumps(row) + '\n')
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                verify_checkpoint(root, metadata['catalog_hash'], '2026-10-09')
