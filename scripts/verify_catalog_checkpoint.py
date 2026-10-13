"""Read-only verification of every authoritative table before post-ingest resume."""
from __future__ import annotations
import argparse
import gc
import json
from pathlib import Path
from catalog_store import TABLES, read_table, table_fingerprint, fingerprint


def verify_checkpoint(root: Path, expected_hash: str, as_of: str) -> dict:
    path = root / 'manifest.json'
    original = path.read_bytes()
    metadata = json.loads(original)
    if metadata.get('catalog_hash') != expected_hash or metadata.get('data_through') != as_of:
        raise ValueError('Catalog checkpoint hash or cutoff mismatch')
    hashes, counts = {}, {}
    for table in TABLES:
        rows = read_table(root, table)
        hashes[table] = table_fingerprint(rows, disk_sort=True)
        counts[table] = len(rows)
        if hashes[table] != metadata.get('table_hashes', {}).get(table):
            raise ValueError('Catalog checkpoint table content mismatch: ' + table)
        print(json.dumps({'status': 'catalog_checkpoint_table_verified', 'table': table, 'rows': counts[table]}), flush=True)
        del rows
        gc.collect()
    if fingerprint(hashes) != expected_hash or path.read_bytes() != original:
        raise ValueError('Catalog checkpoint changed during validation')
    return {'status': 'catalog_checkpoint_verified', 'catalog_hash': expected_hash,
            'data_through': as_of, 'counts': counts, 'input_counts': metadata.get('input_counts', {})}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--expected-hash', required=True)
    parser.add_argument('--as-of', required=True)
    args = parser.parse_args(argv)
    print(json.dumps(verify_checkpoint(args.catalog, args.expected_hash, args.as_of)), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
