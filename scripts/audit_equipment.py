"""Recompute equipment, loco-manip and whole-catalog hardware coverage exports."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from catalog_store import load_catalog, read_table
from equipment_radar import load_equipment_authority, build_equipment_bundle, audit_equipment
from hardware_coverage_export import build_coverage, audit_coverage, load_hardware_dictionary
from import_hardware_source_reviews import audit_addenda_lineage
from pdf_coverage_export import build_pdf_coverage, audit_pdf_coverage, attach_pdf_coverage, API, SOURCE_DOWNLOAD, READING_DOWNLOAD

ROOT = Path(__file__).resolve().parents[1]


def main():
    api = ROOT / 'docs/public/api/v1'
    dictionary = load_hardware_dictionary(ROOT / 'config/hardware-dictionary.json')
    manifest = json.loads((api / 'catalog-manifest.json').read_text())
    if manifest.get('equipment', {}).get('coverage_api') != '/api/v1/equipment/coverage-summary.json':
        raise ValueError('hardware_coverage_manifest_api_missing')
    if manifest.get('downloads', {}).get('hardware_coverage') != '/downloads/equipment/hardware-coverage.jsonl.gz':
        raise ValueError('hardware_coverage_manifest_download_missing')
    if manifest.get('equipment', {}).get('readings_api') != '/api/v1/equipment/coverage-readings.json':
        raise ValueError('hardware_coverage_manifest_readings_api_missing')
    if manifest.get('downloads', {}).get('fulltext_readings') != '/downloads/equipment/fulltext-readings.jsonl':
        raise ValueError('hardware_coverage_manifest_readings_download_missing')
    if (manifest.get('equipment', {}).get('pdf_readings_api') != API or
            manifest.get('downloads', {}).get('pdf_readings') != READING_DOWNLOAD or
            manifest.get('downloads', {}).get('pdf_source_observations') != SOURCE_DOWNLOAD):
        raise ValueError('pdf_coverage_manifest_links_missing')
    payload, _ = load_catalog(ROOT / 'data/catalog')
    authority = load_equipment_authority(ROOT / 'data/equipment')
    bundle = build_equipment_bundle(payload, authority, manifest)
    public_observations = read_table(ROOT / 'data/hardware-review', 'source-observations')
    addenda_audit = audit_addenda_lineage(read_table(ROOT / 'data/hardware-review', 'section-reviews'),
                                        bundle['tables']['usage-evidence'], public_observations)
    coverage = build_coverage(payload, authority, dictionary,
        read_table(ROOT / 'data/hardware-review', 'source-scans'),
        public_observations, manifest,
        reading_reviews=read_table(ROOT / 'data/hardware-review', 'fulltext-readings'))
    pdf_coverage = build_pdf_coverage(payload, read_table(ROOT / 'data/hardware-review', 'pdf-source-observations'),
        read_table(ROOT / 'data/hardware-review', 'pdf-readings'), manifest, coverage['summary']['dictionary_hash'])
    attach_pdf_coverage(coverage, pdf_coverage)
    with closing(sqlite3.connect(f"file:{ROOT / 'docs/public/downloads/radar.sqlite'}?mode=ro", uri=True)) as connection:
        audit_equipment(bundle, api / 'equipment', ROOT / 'docs/public/downloads/equipment', connection)
        coverage_audit = audit_coverage(coverage, api / 'equipment', ROOT / 'docs/public/downloads/equipment', connection)
        pdf_audit = audit_pdf_coverage(pdf_coverage, payload, api / 'equipment', ROOT / 'docs/public/downloads/equipment', connection)
    print(json.dumps({'status': 'passed', 'equipment': bundle['index']['counts'], 'loco_manip': bundle['loco-manip']['counts'],
                      'hardware_coverage': coverage_audit,
                      'hardware_coverage_all_works': coverage['summary']['all_works'],
                      'hardware_coverage_included': coverage['summary']['included'],
                      'article_reading': coverage['readings']['counts'], 'hardware_addenda': addenda_audit,
                      'pdf_reading': pdf_audit}))


if __name__ == '__main__':
    main()
