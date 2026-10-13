import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from json_array_stream import iter_json_array


class JsonArrayStreamTest(unittest.TestCase):
    def test_chunk_boundaries_preserve_nested_unicode_and_numbers(self):
        values = [{'title': '\u673a\u5668\u4eba' * 200, 'nested': [[], {'value': 'a\\b\"c'}]}, 1.25e-10, -12345, True, None]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.json'
            path.write_text(json.dumps(values, ensure_ascii=False))
            for size in (1, 7, 128):
                self.assertEqual(list(iter_json_array(path, size)), values)

    def test_malformed_array_fails_instead_of_silently_truncating(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.json'
            for raw in ('[1,]', '[1', '[{}] extra', '{}', '[1 2]'):
                path.write_text(raw)
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    list(iter_json_array(path, 2))
