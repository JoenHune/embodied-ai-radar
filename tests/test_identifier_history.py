"""Hard-identity deltas use one canonical work and preserve curated fields."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_enrichment import ingest_delta
from catalog_store import TABLES, fingerprint

ARXIV = "2506.09937"
WID = "arxiv:" + ARXIV
DOI = "10.52202/085713-1337"


def fixture(*, source_already_known=False):
    current = {table: [] for table in TABLES}
    work = {"work_id": WID, "title": "SAFE", "abstract": "Existing source text", "authors": ["Qiao Gu"],
            "identifiers": {"arxiv": ARXIV, "doi": None}, "identifier_aliases": {"doi": ["10.48550/arxiv." + ARXIV], "arxiv": [ARXIV]},
            "aliases": [WID], "source_record_ids": ["old"], "manifestation_ids": [], "repositories": [],
            "first_public_date": "2025-06-11", "first_public_date_precision": "day", "primary_direction": "D1", "directions": ["D1", "D12"],
            "relevance": {"status": "manual_review"}, "classification_state": "low_confidence_review", "summary_zh": "保留已有人工编辑"}
    old_source = {"source_record_id": "old", "payload_hash": "a" * 64}
    official = {"source_record_id": "official", "payload_hash": "b" * 64, "source_type": "peer-review"}
    current["works"] = [work]
    current["source-records"] = [old_source]
    if source_already_known:
        current["source-records"].append(copy.deepcopy(official))
        work["source_record_ids"].append("official")
    incoming = {table: [] for table in TABLES}
    revised = copy.deepcopy(work)
    revised["source_record_ids"] = ["old", "official"]
    revised["identifier_aliases"]["doi"].append(DOI)
    incoming["works"] = [revised]
    incoming["source-records"] = [copy.deepcopy(old_source), copy.deepcopy(official)]
    incoming["reconciliation"] = [{"source_record_id": "official", "work_id": WID, "status": "mapped", "basis": "arxiv_id"}]
    return current, incoming


class IdentifierHistoryTests(unittest.TestCase):
    def test_new_official_doi_only_in_history_is_retained_and_exact_search_matches(self):
        current, incoming = fixture()
        original = copy.deepcopy(current["works"][0])
        result = ingest_delta(current, incoming)
        self.assertEqual(len(result["works"]), 1)
        work = result["works"][0]
        self.assertEqual(work["work_id"], WID)
        self.assertIn(DOI, work["identifier_aliases"]["doi"])
        self.assertIn("doi:" + DOI, work["aliases"])
        self.assertTrue(any(row["alias"] == "doi:" + DOI and row["work_id"] == WID for row in result["work-aliases"]))
        self.assertEqual(next(row for row in result["work-aliases"] if row["alias"] == "doi:" + DOI)["source_record_ids"], ["official"])
        for field in ["first_public_date", "first_public_date_precision", "relevance", "primary_direction", "classification_state", "summary_zh"]:
            self.assertEqual(work[field], original[field])
        script = """import fs from 'node:fs';
import {workSearchRecord} from './scripts/lib/search-records.mjs';
import {defaultFilters,searchOptions,filterCatalog} from './docs/.vitepress/theme/lib/catalog-search.ts';
const work=JSON.parse(fs.readFileSync(0,'utf8'));
const record=workSearchRecord(work);
const options=searchOptions({...defaultFilters(),q:'https://doi.org/10.52202/085713-1337',relevance:'all'},[],[]);
const postings={};
for(const [key,values] of Object.entries(record.filters)) for(const value of values){postings[key]||={};postings[key][value]=[0];}
console.log(JSON.stringify({identifier:options.filters.identifier,query:options.query,matches:[...filterCatalog({ids:['result'],work_ids:[work.work_id],dates:[work.first_public_date],postings},options.filters)]}));
"""
        search = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT, input=json.dumps(work), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(search.stdout), {"identifier": DOI, "query": None, "matches": [0]})

    def test_known_source_repair_does_not_replay_dates_titles_or_classification(self):
        current, incoming = fixture(source_already_known=True)
        old = copy.deepcopy(current["works"][0])
        current["works"][0]["_managed_field_hashes"] = {field: fingerprint(old[field]) for field in ["title", "first_public_date", "relevance"]}
        incoming["works"][0].update(title="Stale generated title", first_public_date="2025-01-01", first_public_date_precision="year", relevance={"status": "included"}, primary_direction="D12")
        result = ingest_delta(current, incoming)
        for field in ["title", "authors", "abstract", "first_public_date", "first_public_date_precision", "relevance", "primary_direction", "classification_state", "identifiers"]:
            self.assertEqual(result["works"][0][field], old[field], field)
        self.assertIn(DOI, result["works"][0]["identifier_aliases"]["doi"])

    def test_repeated_import_is_idempotent(self):
        current, incoming = fixture()
        result = ingest_delta(current, incoming)
        first = fingerprint(result)
        ingest_delta(result, incoming)
        self.assertEqual(fingerprint(result), first)
        self.assertEqual(sum(row["alias"] == "doi:" + DOI for row in result["work-aliases"]), 1)

    def test_existing_primary_doi_is_never_overwritten(self):
        current, incoming = fixture()
        current["works"][0]["identifiers"]["doi"] = "10.1234/human-reviewed"
        incoming["works"][0]["identifiers"]["doi"] = DOI
        result = ingest_delta(current, incoming)
        self.assertEqual(result["works"][0]["identifiers"]["doi"], "10.1234/human-reviewed")
        self.assertIn(DOI, result["works"][0]["identifier_aliases"]["doi"])

    def test_foreign_doi_does_not_merge_or_overwrite_two_canonical_works(self):
        current, incoming = fixture()
        foreign = copy.deepcopy(current["works"][0])
        foreign.update(work_id="doi:" + DOI, identifiers={"doi": DOI, "arxiv": "2510.00001"}, identifier_aliases={}, aliases=["doi:" + DOI])
        current["works"].append(foreign)
        before = fingerprint(current)
        with self.assertRaisesRegex(ValueError, "already belongs to another work"):
            ingest_delta(current, incoming)
        self.assertEqual(fingerprint(current), before)

    def test_ambiguous_new_record_requires_explicit_identity_review(self):
        current, incoming = fixture()
        foreign = copy.deepcopy(current["works"][0])
        foreign.update(work_id="doi:" + DOI, identifiers={"doi": DOI, "arxiv": "2510.00001"}, identifier_aliases={}, aliases=["doi:" + DOI])
        current["works"].append(foreign)
        incoming["works"][0]["work_id"] = "title:new-record"
        incoming["reconciliation"][0]["work_id"] = "title:new-record"
        with self.assertRaisesRegex(ValueError, "Conflicting identifier targets"):
            ingest_delta(current, incoming)
        self.assertEqual(len(current["works"]), 2)

    def test_known_source_requires_matching_immutable_payload_hash(self):
        current, incoming = fixture(source_already_known=True)
        incoming["source-records"][1]["payload_hash"] = "changed"
        result = ingest_delta(current, incoming)
        self.assertNotIn(DOI, result["works"][0]["identifier_aliases"]["doi"])

    def test_historical_arxiv_and_primary_values_are_normalized_without_replacement(self):
        current, incoming = fixture()
        incoming["works"][0]["identifier_aliases"]["arxiv"] += ["arxiv:2506.09937v2", "https://arxiv.org/abs/2506.09937v3"]
        incoming["works"][0]["identifier_aliases"]["doi"][-1] = "https://doi.org/10.52202/085713-1337"
        work = ingest_delta(current, incoming)["works"][0]
        self.assertEqual(work["identifier_aliases"]["arxiv"], [ARXIV])
        self.assertIn(DOI, work["identifier_aliases"]["doi"])
        self.assertEqual(work["identifiers"]["arxiv"], ARXIV)


if __name__ == "__main__":
    unittest.main()
