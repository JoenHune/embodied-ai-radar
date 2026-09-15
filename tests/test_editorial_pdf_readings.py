"""PDF editorial integration uses synthetic public JSON only; no PDF parser."""
import contextlib
import copy
import io
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import editorial_readings as er
import pdf_reading_reviews as pdf
import generate_v3_editorial as editor
from catalog_store import fingerprint
import test_editorial_readings as html_fixtures
from test_v3_editorial import version_fixture, valid_editorial, response


def synthetic_pdf(catalog, wid, *, version="v1", marker="original", pages=21,
                  observed="2026-09-14T03:00:00Z", checked="2026-09-14T03:00:10Z",
                  completed="2026-09-14T03:30:00Z"):
    """Build validator-compatible metadata, without downloading/extracting PDF."""
    work = next(row for row in catalog["works"] if row["work_id"] == wid)
    work.setdefault("title", "Synthetic robot paper")
    work.setdefault("authors", ["Synthetic Author"])
    aid = work["identifiers"]["arxiv"]
    year = int("20" + aid[:2])
    landing = f"https://arxiv.org/abs/{aid}{version}"
    address = f"https://arxiv.org/pdf/{aid}{version}"
    mid, sid = "manifest:pdf-fixture:" + version, "source:pdf-fixture:" + version
    manifest = {"manifestation_id": mid, "source_record_id": sid, "work_id": wid, "kind": "preprint",
                "url": landing, "version": version, "year": year, "venue": None,
                "published_at": f"{year}-01-01", "date_precision": "day", "peer_reviewed": False}
    if not any(row.get("manifestation_id") == mid for row in catalog.setdefault("manifestations", [])):
        catalog["manifestations"].append(manifest)
        catalog.setdefault("source-records", []).append({"source_record_id": sid, "url": landing})
    page_hashes = {str(n): fingerprint([marker, "page", n]) for n in range(1, pages + 1)}
    transport = {"http_status": 200, "returncode": 0, "complete": True, "truncated": False,
                 "response_bytes": 1000, "content_length": 1000}
    source = {"schema_version": "1", "work_id": wid, "manifestation_id": mid, "source_record_id": sid,
              "source_format": "pdf", "source_url": address, "landing_url": landing,
              "landing_sha256": fingerprint([marker, "landing"]), "pdf_sha256": fingerprint([marker, "pdf"]),
              "observed_at": observed, "landing_observed_at": observed,
              "landing_transport": copy.deepcopy(transport), "pdf_transport": copy.deepcopy(transport),
              "page_count": pages, "page_text_sha256": page_hashes,
              "page_text_characters": {str(n): 20 for n in range(1, pages + 1)},
              "document_text_sha256": fingerprint([marker, "all pages"]), "extractor_version": pdf.EXTRACTOR_VERSION,
              "edition": {"kind": "preprint", "venue": None, "year": year,
                          "doi": work["identifiers"].get("doi"), "arxiv_version": version},
              "edition_label": "arXiv " + version, "version": version,
              "identity_check": {"status": "same_work_confirmed", "reader_kind": "AI", "checked_at": checked,
                                 "source_pages": [1], "title_checked": True, "authors_checked": True,
                                 "identifier_or_venue_checked": True, "differences_zh": "合成身份检查示例。",
                                 "reason_zh": "仅测试公开元数据链，不读取PDF。"},
              "identity_status": "same_work_confirmed", "license_status": "unknown", "status": "pdf_available",
              "landing_identity": {"title": work["title"], "authors": work["authors"],
                                   "doi_candidates": [work["identifiers"]["doi"]] if work["identifiers"].get("doi") else [],
                                   "venue": None, "publication_year": year},
              "pdf_link_evidence": {"citation_pdf_url": address, "anchor_href": address}}
    source["source_observation_id"] = pdf.source_id(source)
    source["metadata_sha256"] = fingerprint(source)
    reading = {key: copy.deepcopy(source[key]) for key in pdf.READING_KEYS if key in source}
    reading.update(schema_version="1", reading_id=pdf.reading_id(source), read_pages=list(range(1, pages + 1)),
                   read_completed_at=completed, reader_kind="AI", reading_status="completed", assurance=pdf.ASSURANCE,
                   human_reviewed=False, understanding_verified=False,
                   verification_scope="source_hash_pdf_pages_and_explicit_declaration_only", text_scope=pdf.TEXT_SCOPE,
                   checked_table_count=1, tables_exhaustive=False, visual_pages_checked=[1, pages],
                   supplementary_materials_inspected=False, publisher_fulltext_or_media_completeness_verified=False,
                   findings_zh=[{"text_zh": "PDF内嵌补充提供新的方法条件。", "source_pages": [pages]}],
                   limitations_zh=[{"text_zh": "外部视频未核验，不能当作独立复现。", "source_pages": [1, pages]}])
    reading["declaration_sha256"] = fingerprint({key: reading[key] for key in pdf.READING_DECLARATION_KEYS})
    return source, reading


def reseal_reading(reading):
    reading["declaration_sha256"] = fingerprint({key: reading[key] for key in pdf.READING_DECLARATION_KEYS})
    return reading


class EditorialPdfReadingTests(unittest.TestCase):
    def setUp(self):
        self.html_fixture = html_fixtures.EditorialReadingsTests()
        self.html_fixture.setUp()
        self.addCleanup(self.html_fixture.doCleanups)
        self.catalog = self.html_fixture.catalog
        self.work = self.html_fixture.work
        self.wid = self.work["work_id"]
        self.source, self.reading = synthetic_pdf(self.catalog, self.wid)
        self.as_of = "2026-09-15T00:00:00Z"
        for target in ("pdf_reading_reviews.extract_pdf", "pdf_reading_reviews.private_bytes",
                       "fulltext_reading_reviews.private_bytes", "fulltext_reading_reviews._material"):
            guard = patch(target, side_effect=AssertionError("No private source access or parsing"))
            guard.start(); self.addCleanup(guard.stop)

    def index(self, *, readings=None, sources=None, as_of=None):
        return er.build_reading_index(self.catalog, [self.html_fixture.receipt], [self.html_fixture.observation],
                                      as_of or self.as_of,
                                      pdf_readings=[self.reading] if readings is None else readings,
                                      pdf_observations=[self.source] if sources is None else sources)

    def annotations(self, index=None, work=None):
        return er.annotations_for_work(work or self.work, index if index is not None else self.index(), "2026-06-30")

    def test_same_version_HTML_and_PDF_are_independent_and_keep_original_fields(self):
        old = self.annotations(self.index(readings=[], sources=[]))
        rows = self.annotations()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], old[0], "HTML interpretation and digest cannot be overwritten")
        pdf_row = rows[1]
        self.assertEqual(pdf_row["annotation_kind"], "ai_pdf_reading_paraphrase")
        self.assertEqual(pdf_row["source_format"], "pdf")
        self.assertEqual(pdf_row["reading_source_url"], self.reading["source_url"])
        self.assertEqual(pdf_row["read_pages"], list(range(1, 22)))
        self.assertEqual(pdf_row["findings_zh"][0]["source_pages"], [21])
        self.assertEqual(pdf_row["page_text_sha256"], self.reading["page_text_sha256"])
        self.assertEqual(pdf_row["pdf_source_metadata_sha256"], self.source["metadata_sha256"])
        self.assertNotIn("article_text_sha256", pdf_row)
        self.assertNotIn("checked_table_ids", pdf_row)
        self.assertIn("reading_after_historical_cutoff_not_backdated", pdf_row["warnings"])
        self.assertFalse(pdf_row["independent_validation"])

    def test_PDF_never_calls_HTML_URL_normalizer(self):
        index = er.build_reading_index(self.catalog, [], [], self.as_of,
                                      pdf_readings=[self.reading], pdf_observations=[self.source])
        with patch.object(er, "versioned_read_url", side_effect=AssertionError("PDF is not HTML")):
            self.assertEqual(self.annotations(index)[0]["source_format"], "pdf")

    def test_latest_same_version_selected_per_format_not_across_formats(self):
        source, reading = synthetic_pdf(self.catalog, self.wid, marker="later", completed="2026-09-14T04:00:00Z")
        first = self.annotations(self.index(readings=[reading, self.reading], sources=[source, self.source]))
        second = self.annotations(self.index(readings=[self.reading, reading], sources=[self.source, source]))
        self.assertEqual(first, second)
        self.assertEqual(first[0]["reading_id"], self.html_fixture.receipt["reading_id"])
        self.assertEqual(first[1]["reading_id"], reading["reading_id"])

    def test_PDF_v2_never_annotates_selected_v1(self):
        source, reading = synthetic_pdf(self.catalog, self.wid, version="v2", marker="v2")
        only_html = self.annotations(self.index(readings=[], sources=[]))
        self.assertEqual(self.annotations(self.index(readings=[reading], sources=[source])), only_html)
        rows = self.annotations(self.index(readings=[reading, self.reading], sources=[source, self.source]))
        self.assertEqual(rows[1]["version"], "v1")

    def test_future_read_and_identity_are_filtered_with_exact_clock(self):
        for as_of in ["2026-09-14T03:29:59.999999Z", "2026-09-14T03:00:09Z"]:
            self.assertEqual(len(self.annotations(self.index(as_of=as_of))), 1)
        self.assertEqual(len(self.annotations(self.index(as_of="2026-09-14T03:30:00Z"))), 2)
        future = reseal_reading({**self.reading, "read_completed_at": "2026-09-16T00:00:00Z"})
        self.assertEqual(len(self.annotations(self.index(readings=[future]))), 1)
        bad = copy.deepcopy(future); bad["reading_id"] = "forged"
        with self.assertRaises(ValueError): self.index(readings=[bad])

    def test_existing_historical_snapshot_date_and_hold_gates_still_apply(self):
        for update in [dict(experimental_text_available=False), dict(text_version=None), dict(text_snapshot_ids=[]),
                       dict(text_status="source_content_conflict"), dict(research_status_blocked=True),
                       dict(validation_eligible=False), dict(text_available_at="2026-07-01"), dict(text_date_precision="year")]:
            with self.subTest(update=update): self.assertEqual(self.annotations(work={**self.work, **update}), [])

    def test_page_hash_identity_or_source_mapping_tampering_is_not_hidden(self):
        changes = [lambda r: r.update(pdf_sha256="f" * 64),
                   lambda r: r["page_text_sha256"].update({"21": "f" * 64}),
                   lambda r: r["findings_zh"][0].update(source_pages=[22]),
                   lambda r: r.update(source_url="https://arxiv.org/pdf/9999.00001v1"),
                   lambda r: r.update(cache_ref="/private/paper.pdf")]
        for change in changes:
            row = copy.deepcopy(self.reading); change(row)
            with self.assertRaises(ValueError): self.index(readings=[row])

    def test_annotation_digest_binds_PDF_findings_and_source_metadata(self):
        before = self.annotations()
        updated = copy.deepcopy(self.reading)
        updated["findings_zh"][0]["text_zh"] = "PDF补充说明了不同的训练条件。"
        reseal_reading(updated)
        after = self.annotations(self.index(readings=[updated]))
        self.assertEqual(after[0], before[0])
        self.assertNotEqual(after[1]["annotation_digest"], before[1]["annotation_digest"])
        source = copy.deepcopy(self.source)
        source["identity_check"]["reason_zh"] = "修订的来源身份核对说明。"
        source["metadata_sha256"] = fingerprint({k: v for k, v in source.items() if k != "metadata_sha256"})
        self.assertNotEqual(self.annotations(self.index(sources=[source]))[1]["annotation_digest"], before[1]["annotation_digest"])

    def test_input_records_and_legacy_HTML_only_digest_stay_unchanged(self):
        before = copy.deepcopy((self.catalog, self.source, self.reading, self.work))
        old_index = er.build_reading_index(self.catalog, [self.html_fixture.receipt], [self.html_fixture.observation], self.as_of)
        self.assertEqual(self.index(readings=[], sources=[]), old_index)
        index = self.index(); saved = copy.deepcopy(index)
        rows = self.annotations(index)
        rows[1]["findings_zh"][0]["source_pages"].append(2)
        self.assertEqual(index, saved)
        self.assertEqual((self.catalog, self.source, self.reading, self.work), before)

    def test_load_accepts_both_missing_legacy_PDF_files_but_rejects_one_missing(self):
        directory = self.html_fixture.fixture.root / "editorial-metadata"
        directory.mkdir()
        for name, value in [("fulltext-readings", self.html_fixture.receipt), ("source-observations", self.html_fixture.observation)]:
            (directory / (name + ".jsonl")).write_text(json.dumps(value) + "\n")
        self.assertEqual(er.load_reading_index(self.catalog, directory, self.as_of), self.index(readings=[], sources=[]))
        (directory / "pdf-readings.jsonl").write_text(json.dumps(self.reading) + "\n")
        with self.assertRaisesRegex(ValueError, "pair_incomplete"): er.load_reading_index(self.catalog, directory, self.as_of)
        (directory / "pdf-source-observations.jsonl").write_text(json.dumps(self.source) + "\n")
        self.assertEqual(er.load_reading_index(self.catalog, directory, self.as_of), self.index())
        (directory / "pdf-source-observations.jsonl").unlink()
        (directory / "pdf-source-observations.jsonl").symlink_to(directory / "missing")
        with self.assertRaisesRegex(ValueError, "regular_metadata"): er.load_reading_index(self.catalog, directory, self.as_of)


class PdfPacketIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.catalog = version_fixture()
        # All synthetic manifestations need IDs for the PDF validator.
        for number, row in enumerate(self.catalog["manifestations"]):
            row.setdefault("manifestation_id", "manifest:existing:" + str(number))
        self.wid = "work:first"
        self.source, self.reading = synthetic_pdf(self.catalog, self.wid)
        self.clock = "2026-09-14T23:59:59Z"

    def index(self):
        with patch("pdf_reading_reviews.extract_pdf", side_effect=AssertionError("No PDF parsing")), patch.object(socket, "socket", side_effect=AssertionError("No network")):
            return er.build_reading_index(self.catalog, [], [], self.clock,
                                          pdf_readings=[self.reading], pdf_observations=[self.source])

    def packet(self, **kwargs):
        return editor.build_evidence_packet(self.snapshot, self.catalog, reading_index=self.index(),
                                             source_review_as_of=self.clock, **kwargs)

    def test_PDF_changes_context_digest_not_sampling_facts_grades_or_quote_sources(self):
        before = editor.build_evidence_packet(self.snapshot, self.catalog, source_review_as_of=self.clock)
        after = self.packet()
        for key in ("facts", "sampling", "coverage", "directions", "questions", "signal_candidate_cards", "required_localization_ids"):
            self.assertEqual(before[key], after[key], key)
        for a, b in zip(before["evidence_cards"], after["evidence_cards"]):
            self.assertEqual(a, {k: v for k, v in b.items() if k != "reading_annotations"})
        self.assertNotEqual(editor.editorial_input_digest(before), editor.editorial_input_digest(after))
        refs = editor.available_reading_references(after)[self.wid]
        self.assertEqual(refs[0]["source_format"], "pdf")
        self.assertEqual(refs[0]["reading_id"], self.reading["reading_id"])
        self.assertEqual(refs[0]["read_pages"], list(range(1, 22)))
        self.clock = "2026-09-15T02:00:00Z"
        changed_clock = self.packet()
        self.assertEqual(editor.editorial_input_digest(after), editor.editorial_input_digest(changed_clock))

    def test_source_hold_blocks_PDF_without_changing_work_counts(self):
        notice = {"work_id": self.wid, "version": "v1", "experimental_use": "hold"}
        packet = self.packet(source_conflicts=[notice])
        card = next(row for row in packet["evidence_cards"] if row["work_id"] == self.wid)
        self.assertFalse(card["experimental_text_available"])
        self.assertNotIn("reading_annotations", card)
        self.assertEqual(packet["coverage"], self.snapshot["coverage"])

    def test_numeric_and_signal_quote_contract_not_widened_by_PDF_context(self):
        packet = self.packet(); value = valid_editorial(packet)
        editor.validate_editorial(value, packet)
        value["claims"][0]["summary"] = "补充说明成功率为97%。"
        with self.assertRaisesRegex(editor.EditorialError, "unbound_number"):
            editor.validate_editorial(value, packet)
        value = valid_editorial(packet); value["claims"][0]["supporting_ids"] = [self.reading["reading_id"]]
        with self.assertRaisesRegex(editor.EditorialError, "citation_unknown"):
            editor.validate_editorial(value, packet)
        card = next(row for row in packet["evidence_cards"] if row["work_id"] == self.wid)
        self.assertEqual(set(card["source_text_ranges"]), {"title", "abstract"})
        self.assertNotIn(self.reading["source_url"], [row["url"] for row in card["source_documents"]])

    def test_PDF_enrichment_invalidates_old_editorial_and_archives_exact_packet(self):
        base = editor.build_evidence_packet(self.snapshot, self.catalog, source_review_as_of=self.clock)
        enhanced = self.packet()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            def run(packet):
                value = valid_editorial(packet)
                return editor.run_month(packet, packet["month"], output, base_url="http://fixture.invalid",
                    requester=lambda *_: (value, response(value)), sleeper=lambda _: None)
            self.assertEqual(run(base)["status"], "complete")
            previous = json.loads((output / "monthly" / (base["month"] + ".json")).read_text())
            self.assertFalse(editor.validated_editorial_overlay(previous, enhanced)["usable"])
            self.assertEqual(run(enhanced)["status"], "complete")
            saved = json.loads((output / "monthly" / (base["month"] + ".json")).read_text())
            self.assertEqual(json.loads((output / saved["evidence_packet_ref"]["path"]).read_text()), enhanced)
            self.assertEqual(saved["available_reading_references"], editor.available_reading_references(enhanced))

    def test_fixture_entrypoint_passes_PDF_pair_into_evidence_packet(self):
        fixture = {"manifest": {"data_through": "2026-09-14", "available_months": ["2026-08"]},
                   "catalog": self.catalog, "snapshots": {"2026-08": self.snapshot},
                   "pdf_readings": [self.reading], "pdf_source_observations": [self.source]}
        seen = []
        def fake_run(packet, month, output, **kwargs):
            seen.append(packet)
            return {"month": month, "status": "data_only", "model": "fixture", "generated_at": "2026-09-15T00:00:00Z"}
        with tempfile.TemporaryDirectory() as directory, patch.object(editor, "run_month", side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory); source = root / "fixture.json"; source.write_text(json.dumps(fixture))
            self.assertEqual(editor.main(["--fixture", str(source), "--month", "2026-08", "--output-directory", str(root / "output"), "--allow-data-only"]), 0)
        self.assertEqual(editor.available_reading_references(seen[0])[self.wid][0]["reading_id"], self.reading["reading_id"])


if __name__ == "__main__":
    unittest.main()
