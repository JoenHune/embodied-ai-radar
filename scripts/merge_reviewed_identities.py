"""Explicit cross-title identity merges with complete alias and source lineage."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from catalog_rules import normalized_title
from catalog_store import fingerprint, read_table
from prepare_catalog import merge_work


def checked_release_duplicate(payload: dict, review: dict, target: dict, old_ids: list[str], works: dict) -> bool:
    """Narrow exception for a reviewed duplicate official release card.

    Empty author fields on scraped company cards must not create a permanent
    duplicate of the already identified report/paper. A shared index URL or
    two authored papers is never sufficient for this exception.
    """
    proof = review.get("duplicate_release") or {}
    url, org_id = proof.get("url"), proof.get("organization_id")
    if not isinstance(url, str) or not org_id or not proof.get("same_release_evidence"):
        return False
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.path.rstrip("/") in {"", "/blog", "/research", "/publications", "/projects"}:
        return False
    source_urls = {row["source_record_id"]: row.get("url", "").rstrip("/") for row in payload["source-records"]}
    def owned_urls(work):
        return {row.get("url", "").rstrip("/") for row in payload["manifestations"] if row["work_id"] == work["work_id"]} | {source_urls.get(sid) for sid in work.get("source_record_ids", [])}
    def official_group(work):
        return any(row["work_id"] == work["work_id"] and row["organization_id"] == org_id and row.get("evidence_grade") == "G1" for row in payload["work-organization-links"])
    if url.rstrip("/") not in owned_urls(target) or not official_group(target):
        return False
    for old_id in old_ids:
        old = works[old_id]
        if not old_id.startswith("artifact:") or old.get("authors") or old["relevance"]["status"] == "excluded":
            return False
        if url.rstrip("/") not in owned_urls(old) or not official_group(old):
            return False
        if any(row.get("kind") not in {"project", "model", "dataset", "code", "benchmark", "demo", "deployment"} for row in payload["manifestations"] if row["work_id"] == old_id):
            return False
    return True


def merge_reviewed_identities(payload: dict, data: Path) -> dict:
    works = {row["work_id"]: row for row in payload["works"]}
    known_reviews = {row.get("review_id") for row in payload.get("work-relations", [])}
    for review in read_table(data, "identity-reviews"):
        if review.get("review_status") != "verified":
            continue
        if review.get("review_id") in known_reviews:
            continue
        target_id = review["canonical_work_id"]
        old_ids = [wid for wid in review["work_ids"] if wid != target_id]
        source_urls = review.get("source_urls", [])
        if target_id not in works or not old_ids or any(wid not in works for wid in old_ids):
            raise ValueError("Identity review targets are not current canonical records")
        if not review.get("reason") or not review.get("reviewed_at") or len(source_urls) < 2 or any(urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).hostname for url in source_urls):
            raise ValueError("A reviewed merge needs explicit public corroboration")
        target = works[target_id]
        authors = {normalized_title(name) for name in target.get("authors", [])}
        same_release = checked_release_duplicate(payload, review, target, old_ids, works)
        if not same_release and (not authors or any({normalized_title(name) for name in works[wid].get("authors", [])} != authors for wid in old_ids)):
            raise ValueError("Cross-title automatic application requires the reviewed identical author set")
        if not same_release and any(works[wid]["relevance"]["status"] != target["relevance"]["status"] for wid in old_ids):
            raise ValueError("Resolve conflicting relevance explicitly before applying an identity merge")
        for old_id in old_ids:
            old = works[old_id]
            target.setdefault("title_aliases", [])
            target["title_aliases"] = sorted(set([*target["title_aliases"], old["title"], *old.get("title_aliases", [])]))
            # Manifestations retain the exact title in which they were released.
            for version in payload["manifestations"]:
                if version["work_id"] == old_id:
                    version.setdefault("title", old["title"])
                elif version["work_id"] == target_id:
                    version.setdefault("title", target["title"])
            merge_work(target, old)
            target["aliases"] = sorted(set([*target.get("aliases", []), old_id, *old.get("aliases", [])]))
            for table in ["manifestations", "work-organization-links", "field-provenance", "work-aliases", "evidence-events", "reconciliation", "taxonomy-assignments"]:
                for row in payload.get(table, []):
                    if row.get("work_id") == old_id:
                        row["work_id"] = target_id
            payload["work-aliases"].append({"alias": old_id, "work_id": target_id, "kind": "reviewed_cross_title_merge", "valid_from": review["reviewed_at"], "valid_to": None})
            payload["work-relations"].append({"relation": "merged_into", "work_id": target_id, "previous_id": old_id,
                                               "review_id": review["review_id"], "reason": review["reason"], "source_urls": source_urls,
                                               "reviewed_at": review["reviewed_at"], "prior_canonical_record": old})
            del works[old_id]
        # Mark merged source lists as machine-maintained without erasing edits
        # made later by the user; historical records remain in the lineage.
        for field in ["authors", "institutions", "directions", "questions", "first_public_date", "first_public_date_precision"]:
            target.setdefault("_managed_field_hashes", {})[field] = fingerprint(target.get(field))
        first_version = next((version for version in payload["manifestations"] if version["work_id"] == target_id and version.get("published_at") == target.get("first_public_date")), None)
        if first_version:
            target["first_public_date_source"] = first_version["source_record_id"]
        known_reviews.add(review["review_id"])
    payload["works"] = sorted(works.values(), key=lambda row: row["work_id"])
    return payload
