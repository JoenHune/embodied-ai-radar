"""Recompute equipment and loco-manip views from their authority, including SQLite."""
import json
import sqlite3
from pathlib import Path

from catalog_store import load_catalog
from equipment_radar import load_equipment_authority, build_equipment_bundle, audit_equipment

ROOT = Path(__file__).resolve().parents[1]


def main():
    api = ROOT / 'docs/public/api/v1'
    manifest = json.loads((api / 'catalog-manifest.json').read_text())
    payload, _ = load_catalog(ROOT / 'data/catalog')
    bundle = build_equipment_bundle(payload, load_equipment_authority(ROOT / 'data/equipment'), manifest)
    with sqlite3.connect(f"file:{ROOT / 'docs/public/downloads/radar.sqlite'}?mode=ro", uri=True) as connection:
        audit_equipment(bundle, api / 'equipment', ROOT / 'docs/public/downloads/equipment', connection)
    print(json.dumps({'status': 'passed', 'equipment': bundle['index']['counts'], 'loco_manip': bundle['loco-manip']['counts']}))


if __name__ == '__main__':
    main()
