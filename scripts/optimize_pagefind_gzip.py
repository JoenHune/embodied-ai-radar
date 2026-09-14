#!/usr/bin/env python3
"""Losslessly recompress explicit Pagefind gzip assets, never index semantics.

Only index/*.pf_index, pagefind.*.pf_meta and wasm.*.pagefind are eligible.
Every original and replacement is decoded with Python's standard gzip reader.
The Pagefind filenames, decompressed bytes, JS and user files remain unchanged.
The cache is an ignored build cache, not an editable source or search service.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import os
import re
import stat
import sys
import tempfile
import zlib
from pathlib import Path

import zopfli.gzip

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = ROOT / "node_modules/.cache/radar-pagefind-gzip"
ITERATIONS = 12
ASSET_PATTERNS = (
    re.compile(r"index/[A-Za-z][A-Za-z0-9-]*_[0-9a-f]+\.pf_index"),
    re.compile(r"pagefind\.[A-Za-z][A-Za-z0-9-]*_[0-9a-f]+\.pf_meta"),
    re.compile(r"wasm\.[A-Za-z][A-Za-z0-9_-]*\.pagefind"),
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _no_symlink(path: Path) -> Path:
    absolute = path.absolute()
    if any(part.is_symlink() for part in [absolute, *absolute.parents]):
        raise ValueError("Symlink paths are not permitted")
    return absolute


def _decode(value: bytes, label: str) -> bytes:
    if not value.startswith(b"\x1f\x8b"):
        raise ValueError(f"Not a standard gzip asset: {label}")
    try:
        return gzip.decompress(value)
    except (OSError, EOFError, zlib.error) as error:
        raise ValueError(f"Invalid gzip payload: {label}") from error


def discover_assets(directory: Path) -> tuple[Path, list[Path], int]:
    """Read-only preflight of the root, whitelist, symlinks and all CRCs."""
    root = _no_symlink(directory)
    if not root.is_dir():
        raise ValueError("--directory must name an existing Pagefind directory")
    marker = root / "pagefind-entry.json"
    if marker.is_symlink() or not marker.is_file():
        raise ValueError("A regular pagefind-entry.json is required")
    try:
        entry = json.loads(marker.read_text())
    except (ValueError, OSError) as error:
        raise ValueError("Invalid pagefind-entry.json") from error
    if not isinstance(entry, dict) or not isinstance(entry.get("version"), str) or not isinstance(entry.get("languages"), dict):
        raise ValueError("Directory is not a recognized Pagefind output root")
    assets, ignored = [], 0
    for current, directories, files in os.walk(root, followlinks=False):
        for name in [*directories, *files]:
            if (Path(current) / name).is_symlink():
                raise ValueError("Symlinks inside the Pagefind directory are not permitted")
        for name in files:
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            if any(pattern.fullmatch(relative) for pattern in ASSET_PATTERNS):
                if not stat.S_ISREG(path.stat().st_mode):
                    raise ValueError("Pagefind asset must be a regular file")
                _decode(path.read_bytes(), relative)
                assets.append(path)
            else:
                ignored += 1
    return root, sorted(assets), ignored


def algorithm_spec() -> dict:
    return {"schema_version": 1, "algorithm": "minimum-of-original-gzip9-zopfli",
            "zopfli_version": importlib.metadata.version("zopfli"), "zopfli_numiterations": ITERATIONS,
            "zlib_version": zlib.ZLIB_RUNTIME_VERSION, "gzip_compresslevel": 9, "gzip_mtime": 0}


def cache_key(decoded_sha256: str, spec: dict) -> str:
    return sha256(json.dumps({"decoded_sha256": decoded_sha256, "spec": spec}, sort_keys=True, separators=(",", ":")).encode())


def _atomic_write(path: Path, content: bytes, *, mode: int = 0o600, expected_before: bytes | None = None) -> None:
    _no_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        _no_symlink(path)
        if expected_before is not None and (not path.is_file() or path.read_bytes() != expected_before):
            raise RuntimeError("Pagefind asset changed concurrently; refusing replacement")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()  # exact temporary file created by this call


def _cached_candidate(cache: Path, key: str, raw: bytes, spec: dict) -> tuple[bytes | None, str | None, str]:
    compressed, metadata = cache / (key + ".gz"), cache / (key + ".json")
    _no_symlink(compressed)
    _no_symlink(metadata)
    if not compressed.exists() and not metadata.exists():
        return None, None, "miss"
    try:
        if not compressed.is_file() or not metadata.is_file():
            return None, None, "invalid"
        value, info = compressed.read_bytes(), json.loads(metadata.read_text())
        if not isinstance(info, dict):
            return None, None, "invalid"
        if info.get("cache_key") != key or info.get("spec") != spec or info.get("decoded_sha256") != sha256(raw):
            return None, None, "invalid"
        if info.get("compressed_sha256") != sha256(value) or info.get("compressed_bytes") != len(value) or info.get("algorithm") not in {"original", "gzip9", "zopfli"}:
            return None, None, "invalid"
        if _decode(value, "cache") != raw:
            return None, None, "invalid"
        return value, info["algorithm"], "hit"
    except (ValueError, OSError):
        return None, None, "invalid"


def optimize_asset(path: Path, relative: str, cache: Path, spec: dict) -> dict:
    before = path.read_bytes()
    raw = _decode(before, relative)
    decoded_digest = sha256(raw)
    key = cache_key(decoded_digest, spec)
    cached, cached_algorithm, cache_status = _cached_candidate(cache, key, raw, spec)
    if cached is not None:
        candidates = [("original", before), (cached_algorithm, cached)]
    else:
        candidates = [("original", before), ("gzip9", gzip.compress(raw, compresslevel=9, mtime=0)),
                      ("zopfli", zopfli.gzip.compress(raw, numiterations=ITERATIONS))]
    for _, candidate in candidates:
        if _decode(candidate, relative) != raw:
            raise RuntimeError(f"Decoded-byte mismatch; refusing to modify {relative}")
    # Stable tie break retains the original wrapper; there is never expansion.
    algorithm, after = min(candidates, key=lambda item: len(item[1]))
    changed = len(after) < len(before)
    if len(after) > len(before):
        raise AssertionError("Lossless optimizer must never enlarge an asset")
    if cache_status != "hit" or (cached is not None and len(after) < len(cached)):
        info = {"cache_key": key, "spec": spec, "algorithm": algorithm, "decoded_sha256": decoded_digest,
                "compressed_sha256": sha256(after), "compressed_bytes": len(after)}
        _atomic_write(cache / (key + ".gz"), after)
        _atomic_write(cache / (key + ".json"), json.dumps(info, sort_keys=True, separators=(",", ":")).encode())
    if changed:
        mode = stat.S_IMODE(path.stat().st_mode)
        _atomic_write(path, after, mode=mode, expected_before=before)
    final = path.read_bytes()
    if final != after or _decode(final, relative) != raw:
        raise RuntimeError(f"Post-write verification failed for {relative}")
    return {"path": relative, "before_bytes": len(before), "after_bytes": len(after), "saved_bytes": len(before) - len(after),
            "before_sha256": sha256(before), "after_sha256": sha256(after), "decoded_sha256": decoded_digest,
            "decoded_bytes": len(raw), "decoded_bytes_identical": True, "changed": changed, "algorithm": algorithm,
            "cache_key": key, "cache_hit": cache_status == "hit", "cache_status": cache_status}


def optimize_directory(directory: Path, cache_directory: Path = DEFAULT_CACHE) -> dict:
    root, assets, ignored = discover_assets(directory)
    cache = _no_symlink(cache_directory)
    if cache == root or cache.is_relative_to(root):
        raise ValueError("Compression cache must be outside the Pagefind output")
    if cache.exists() and not cache.is_dir():
        raise ValueError("Compression cache must be a directory")
    spec = algorithm_spec()
    results = [optimize_asset(path, path.relative_to(root).as_posix(), cache, spec) for path in assets]
    before = sum(row["before_bytes"] for row in results)
    after = sum(row["after_bytes"] for row in results)
    return {"schema_version": "1", "status": "ok", "directory": str(root), "cache_directory": str(cache), "spec": spec,
            "asset_count": len(results), "changed_assets": sum(row["changed"] for row in results), "ignored_files": ignored,
            "before_bytes": before, "after_bytes": after, "saved_bytes": before - after,
            "cache_hits": sum(row["cache_hit"] for row in results), "invalid_cache_entries": sum(row["cache_status"] == "invalid" for row in results),
            "all_decoded_bytes_identical": all(row["decoded_bytes_identical"] for row in results), "files": results}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True, help="Explicit Pagefind output containing pagefind-entry.json")
    parser.add_argument("--cache-directory", type=Path, default=DEFAULT_CACHE, help="Ignored build cache outside Pagefind output")
    args = parser.parse_args(argv)
    try:
        result = optimize_directory(args.directory, args.cache_directory)
    except Exception as error:
        # No source bytes, environment variables, credentials or exception
        # payloads are emitted. Details are intentionally structural only.
        print(json.dumps({"schema_version": "1", "status": "error", "error_type": type(error).__name__}))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
