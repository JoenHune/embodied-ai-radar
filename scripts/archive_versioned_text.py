"""Persist source-bound version text independently from mutable feed arrays."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from catalog_store import fingerprint, read_table
from versioned_text import build_versioned_text, register_versioned_text_additions, validate_snapshot


def archive_versioned_text(payload: dict, data: Path, preprints: list[dict]) -> dict:
    additions = read_table(data, "versioned-text-additions")
    if additions:
        payload = register_versioned_text_additions(payload, additions)
    works = {row["work_id"]: row for row in payload["works"]}
    sources = {row["source_record_id"]: row for row in payload["source-records"]}
    existing = {row["snapshot_id"]: row for row in payload.get("text-snapshots", [])}
    # Only Atom metadata/explicit version archives carry version text. Other
    # legacy links remain valid provenance but cannot restore an old abstract.
    selected_ids = {sid for sid, row in sources.items() if row.get("source_type") in {"preprints", "official_arxiv_version_metadata"}}
    views = [{**row, "source_record_ids": [sid for sid in row.get("source_record_ids", []) if sid in selected_ids]} for row in works.values()]
    bundle = build_versioned_text(views, sources, raw_payloads={"data/preprints.json": preprints}, preprints=preprints, additions=[*existing.values(), *additions])
    for snapshot in bundle["snapshots"]:
        origin = sources[snapshot["source_record_id"]]
        if origin.get("source_type") == "official_arxiv_version_metadata":
            archived = snapshot
            origin.setdefault("text_content_digest", fingerprint({key: snapshot[key] for key in ["abstract", "title"]}))
        else:
            # Timestamp belongs to the observed metadata version's `updated`
            # field, not the canonical work's original submission date.
            sid = "source:version-text:" + fingerprint(snapshot["snapshot_id"])[:24]
            archived = {**snapshot, "source_record_id": sid}
            if snapshot.get("version"):
                arxiv_id = works[snapshot["work_id"]].get("identifiers", {}).get("arxiv")
                if arxiv_id:
                    archived["source_url"] = f"https://arxiv.org/abs/{arxiv_id}{snapshot['version']}"
            archived["basis"] = "archived_from_verified_atom_payload:" + snapshot["basis"]
            archived["snapshot_id"] = "text-snapshot:" + fingerprint({key: value for key, value in archived.items() if key != "snapshot_id"})[:24]
            source = {"source_record_id": sid, "source_type": "official_arxiv_version_metadata", "url": archived["source_url"],
                      "published_at": archived["available_at"], "date_precision": archived["date_precision"], "version": archived["version"],
                      "retrieved_at": origin.get("retrieved_at"), "recorded_at": origin.get("recorded_at"), "source_origin_id": origin["source_record_id"],
                      "payload_hash": fingerprint(archived), "text_content_digest": fingerprint({key: archived[key] for key in ["abstract", "title"]}),
                      "raw_ref": "data/catalog/text-snapshots#" + archived["snapshot_id"], "metadata_license": "CC0-1.0"}
            if sid in sources and sources[sid] != source:
                raise ValueError("Immutable version source changed")
            if sid not in sources:
                sources[sid] = source
                payload["source-records"].append(source)
        work = works[archived["work_id"]]
        work["source_record_ids"] = sorted(set(work.get("source_record_ids", [])) | {archived["source_record_id"]})
        errors = validate_snapshot(archived, work, sources)
        if errors:
            raise ValueError("Archived version source is inconsistent: " + ",".join(errors))
        previous = existing.get(archived["snapshot_id"])
        if previous and previous != archived:
            raise ValueError("Immutable text snapshot changed")
        existing[archived["snapshot_id"]] = archived
    payload["text-snapshots"] = sorted(existing.values(), key=lambda row: row["snapshot_id"])
    return payload
