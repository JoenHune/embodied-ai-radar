import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from repair_arxiv_author_lists import parse_authors

class AuthorMetadataTests(unittest.TestCase):
    def test_full_visible_names_not_bibliographic_inversion(self):
        html = '<meta name="citation_arxiv_id" content="2609.12345"><meta name="citation_author" content="Wang, Xiaolong"><div class="authors"><a>Xiaolong Wang</a></div>'
        self.assertEqual(parse_authors(html, '2609.12345'), ['Xiaolong Wang'])
    def test_identity_or_count_mismatch_fails_closed(self):
        html = '<meta name="citation_arxiv_id" content="2609.12345"><meta name="citation_author" content="Wang, Xiaolong">'
        with self.assertRaises(ValueError): parse_authors(html, '2609.99999')
        with self.assertRaises(ValueError): parse_authors(html, '2609.12345')
