"""Lossless, streamed SQLite download packaging; no catalog transformation.

The raw database stays outside public/. Publication replaces each derived file
atomically, with rollback on ordinary exceptions. This is not a cross-file
power-loss transaction; a failed build must never be deployed.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import tempfile
import zipfile
import zlib
from contextlib import contextmanager
from pathlib import Path

SQLITE_DOWNLOAD_URL = "/downloads/radar.sqlite.zip"
SQLITE_HEADER = b"SQLite format 3\x00"
BLOCK_SIZE = 1024 * 1024
INTEGRITY_FIELDS = {"encoding", "sha256", "archive_sha256", "bytes", "archive_bytes"}


class PublicationRollbackError(RuntimeError):
    """Do not delete recovery copies if the filesystem prevents rollback."""


def local_sqlite_path(root):
    """Caller-provided root also keeps fixtures out of the real workspace."""
    return Path(root).resolve() / ".research" / "derived" / "radar.sqlite"


def _regular(path):
    path = Path(path)
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("sqlite_download_regular_file_required")
    return path


def _file_info(path, *, sqlite=False):
    path = _regular(path)
    digest, size, header = hashlib.sha256(), 0, b""
    with path.open("rb") as stream:
        while chunk := stream.read(BLOCK_SIZE):
            if len(header) < len(SQLITE_HEADER):
                header = (header + chunk)[:len(SQLITE_HEADER)]
            digest.update(chunk)
            size += len(chunk)
    if sqlite and header != SQLITE_HEADER:
        raise ValueError("sqlite_download_invalid_sqlite_header")
    return size, digest.hexdigest()


def verify_archive(archive_path, integrity, *, raw_path=None):
    """Read-only full ZIP CRC/length/hash/header audit, optionally vs raw.

    No temporary decompressed file and no whole-database memory buffer. The
    declared raw size bounds decompression, and reading to EOF validates CRC.
    """
    if (not isinstance(integrity, dict) or set(integrity) != INTEGRITY_FIELDS or
            integrity.get("encoding") != "zip" or
            any(not isinstance(integrity.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", integrity[key])
                for key in ("sha256", "archive_sha256")) or
            any(type(integrity.get(key)) is not int or integrity[key] <= 0 for key in ("bytes", "archive_bytes"))):
        raise ValueError("sqlite_download_integrity_contract_invalid")
    archive_path = _regular(archive_path)
    archive_bytes, archive_digest = _file_info(archive_path)
    if (archive_bytes, archive_digest) != (integrity["archive_bytes"], integrity["archive_sha256"]):
        raise ValueError("sqlite_download_compressed_integrity_mismatch")
    raw_digest, raw_bytes, header = hashlib.sha256(), 0, b""
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            entries = archive.infolist()
            if len(entries) != 1:
                raise ValueError("sqlite_download_single_entry_required")
            entry = entries[0]
            mode = entry.external_attr >> 16
            if (entry.filename != "radar.sqlite" or entry.orig_filename != entry.filename or entry.is_dir() or entry.flag_bits & 0x41 or
                    entry.compress_type != zipfile.ZIP_DEFLATED or
                    stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                raise ValueError("sqlite_download_invalid_zip_entry")
            if entry.file_size != integrity["bytes"]:
                raise ValueError("sqlite_download_uncompressed_integrity_mismatch")
            with archive.open(entry, "r") as stream:
                while chunk := stream.read(BLOCK_SIZE):
                    if len(header) < len(SQLITE_HEADER):
                        header = (header + chunk)[:len(SQLITE_HEADER)]
                    raw_bytes += len(chunk)
                    if raw_bytes > integrity["bytes"]:
                        raise ValueError("sqlite_download_uncompressed_size_exceeded")
                    raw_digest.update(chunk)
    except (zipfile.BadZipFile, EOFError, zlib.error) as error:
        raise ValueError("sqlite_download_invalid_zip_stream") from error
    if header != SQLITE_HEADER:
        raise ValueError("sqlite_download_invalid_sqlite_header")
    if (raw_bytes, raw_digest.hexdigest()) != (integrity["bytes"], integrity["sha256"]):
        raise ValueError("sqlite_download_uncompressed_integrity_mismatch")
    if raw_path is not None and _file_info(raw_path, sqlite=True) != (raw_bytes, raw_digest.hexdigest()):
        raise ValueError("sqlite_download_local_raw_mismatch")
    return {**integrity, "status": "passed"}


def _compress(raw_path, temporary_archive):
    raw_bytes, raw_digest = _file_info(raw_path, sqlite=True)
    with Path(raw_path).open("rb") as source, Path(temporary_archive).open("wb") as target:
        entry = zipfile.ZipInfo("radar.sqlite", date_time=(1980, 1, 1, 0, 0, 0))
        entry.create_system = 3
        entry.external_attr = (stat.S_IFREG | 0o644) << 16
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.file_size = raw_bytes
        # ZipInfo.compress_level is only public in Python 3.13+. This field is
        # used by streaming ZipFile.open on supported Python 3.12/3.13 hosts.
        entry._compresslevel = 6
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            with archive.open(entry, "w", force_zip64=True) as compressed:
                shutil.copyfileobj(source, compressed, length=BLOCK_SIZE)
        target.flush()
        os.fsync(target.fileno())
    archive_bytes, archive_digest = _file_info(temporary_archive)
    integrity = {"encoding": "zip", "sha256": raw_digest, "archive_sha256": archive_digest,
                 "bytes": raw_bytes, "archive_bytes": archive_bytes}
    verify_archive(temporary_archive, integrity, raw_path=raw_path)
    return integrity


def _check_existing_output(path):
    if path.is_symlink():
        raise ValueError("sqlite_download_output_symlink_forbidden")
    if path.exists():
        _regular(path)


def _publish(replacements, remove_legacy, backup_directory):
    """Exact derived targets only; preserve old bytes if publication fails."""
    targets = [target for _, target in replacements]
    targets.extend(target for target in remove_legacy if target.exists())
    backups = {}
    for index, target in enumerate(targets):
        _check_existing_output(target)
        if target.exists():
            backup = backup_directory / str(index)
            try:
                os.link(target, backup)
            except OSError:
                # E.g. another filesystem or a host without hard links.
                shutil.copy2(target, backup)
            backups[target] = backup
        else:
            backups[target] = None
    try:
        for temporary, target in replacements:
            os.replace(temporary, target)
        for target in remove_legacy:
            if target.exists():
                # Only the two exact, header-checked superseded derivatives.
                target.unlink()
    except BaseException as original_error:
        rollback_errors = []
        for target, backup in reversed(list(backups.items())):
            try:
                if backup is None:
                    if target.exists():
                        target.unlink()
                else:
                    os.replace(backup, target)
            except OSError as error:
                rollback_errors.append(error)
        if rollback_errors:
            raise PublicationRollbackError("sqlite_download_rollback_failed_backups_preserved") from original_error
        raise


@contextmanager
def sqlite_export(root, downloads, manifest_path, manifest):
    """Yield a fresh SQLite connection; publish verified raw/ZIP on success.

    The catalog builder owns all SQL. A raised body exception keeps the last
    raw database, archive and manifest; only private temporary files change.
    """
    root = Path(root).resolve()
    raw_target = local_sqlite_path(root)
    downloads, manifest_path = Path(downloads), Path(manifest_path)
    if downloads.is_symlink() or manifest_path.parent.is_symlink():
        raise ValueError("sqlite_download_output_directory_symlink_forbidden")
    downloads = downloads.resolve()
    if manifest_path.is_symlink():
        raise ValueError("sqlite_download_output_symlink_forbidden")
    manifest_path = manifest_path.resolve()
    if not downloads.is_relative_to(root) or not manifest_path.resolve().is_relative_to(root):
        raise ValueError("sqlite_download_output_outside_root")
    for path in (root / ".research", raw_target.parent):
        if path.is_symlink():
            raise ValueError("sqlite_download_private_directory_symlink_forbidden")
    archive_target = downloads / "radar.sqlite.zip"
    legacy_targets = (downloads / "radar.sqlite", downloads / "radar.sqlite.gz")
    if raw_target.is_relative_to(downloads) or len({raw_target, archive_target, *legacy_targets, manifest_path.resolve()}) != 5:
        raise ValueError("sqlite_download_output_paths_overlap")
    for path in (raw_target, archive_target, *legacy_targets, manifest_path):
        _check_existing_output(path)
    if legacy_targets[0].exists():
        with legacy_targets[0].open("rb") as old:
            if old.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
                raise ValueError("sqlite_download_legacy_target_not_sqlite")
    if legacy_targets[1].exists():
        try:
            with gzip.open(legacy_targets[1], "rb") as old:
                if old.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
                    raise ValueError("sqlite_download_legacy_gzip_not_sqlite")
        except (gzip.BadGzipFile, EOFError, zlib.error) as error:
            raise ValueError("sqlite_download_legacy_gzip_not_sqlite") from error
    raw_target.parent.mkdir(parents=True, exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=".sqlite-export-", dir=raw_target.parent))
    temporary_files = []
    connection = None
    preserve_backups = False
    try:
        temporary_raw = temporary_root / "radar.sqlite"
        connection = sqlite3.connect(temporary_raw)
        yield connection
        connection.commit()
        connection.execute("VACUUM")
        connection.close()
        connection = None
        with temporary_raw.open("rb") as stream:
            os.fsync(stream.fileno())
        for directory, prefix in ((downloads, ".radar.sqlite.zip-"), (manifest_path.parent, ".catalog-manifest-")):
            descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=directory)
            os.close(descriptor)
            temporary_files.append(Path(name))
        temporary_archive, temporary_manifest = temporary_files
        integrity = _compress(temporary_raw, temporary_archive)
        final_manifest = copy.deepcopy(manifest)
        final_manifest.setdefault("downloads", {}).update(sqlite=SQLITE_DOWNLOAD_URL, sqlite_integrity=integrity)
        with temporary_manifest.open("w", encoding="utf-8") as stream:
            json.dump(final_manifest, stream, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # All verification precedes any final-file replacement or removal.
        _publish([(temporary_raw, raw_target), (temporary_archive, archive_target),
                  (temporary_manifest, manifest_path)], legacy_targets, temporary_root)
    except PublicationRollbackError:
        preserve_backups = True
        raise
    finally:
        if connection is not None:
            connection.close()
        for path in temporary_files:
            if path.exists():
                path.unlink()
        if not preserve_backups:
            shutil.rmtree(temporary_root)
