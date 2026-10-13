"""Offline URL normalization checks; no production env or file reads."""
import os,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import publish_token_free_batch as publisher
class LocatorTests(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ,{},clear=True);env.start();self.addCleanup(env.stop)
    def test_safe_locator_normalizes_only_percent_encoded_backslash(self):
        base='https://arxiv.org/html/2403.16877'
        url=base+'#S4.SS3%5cpar.p6.1'
        canonical=publisher.safe_arxiv_url(url,fragment=True)
        self.assertEqual(canonical,base+'#S4.SS3%5Cpar.p6.1')
        self.assertEqual(publisher.safe_arxiv_url(canonical,fragment=True),canonical)
        for bad in ['#a%0Ab','#a%2Fb','#a%253Cb','#a%FF','#a%GG']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):publisher.safe_arxiv_url(base+bad,fragment=True)
        for bad in [url.replace('arxiv.org','evil.example'),url.replace('https:','http:'),base+'?x=y#S4',url.replace('/html/','/pdf/')]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):publisher.safe_arxiv_url(bad,fragment=True)
        with self.assertRaises(ValueError):publisher.safe_arxiv_url(url)
