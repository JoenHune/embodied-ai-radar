#!/usr/bin/env python3
"""Resolve curated group updates into canonical works and attribution edges.

Only G1/G2 evidence is accepted into the public group radar.  G3/G0 remains
in a review queue.  Institution strings are deliberately *not* used to infer a
lab: NVIDIA does not imply GEAR and CMU does not imply Robotics Institute.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
ORGS = ROOT / "config" / "organizations.json"
WORKS = ROOT / "data" / "works.json"
CANDIDATES = ROOT / "data" / "group-update-candidates.json"
UPDATES = ROOT / "data" / "group-updates.json"
LINKS = ROOT / "data" / "work-organization-links.json"
REVIEW = ROOT / "data" / "group-review-queue.json"
SOURCE_STATUS = ROOT / "data" / "group-source-status.json"
COLLABORATIONS = ROOT / "config" / "group-collaboration-seeds.json"
TAXONOMY = ROOT / "config" / "taxonomy-v2.json"
QUESTION_EVIDENCE = ROOT / "data" / "research-question-evidence.json"
MANUAL_UPDATES = ROOT / "config" / "group-update-seeds.json"


def read(path: Path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def canonical_url(value: str) -> str:
    if not value:
        return ""
    parts = urlsplit(value.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def extract_arxiv_id(value: str) -> str | None:
    match = re.search(r"(?:arxiv\.org/(?:abs|pdf)/|arxiv:)(\d{4}\.\d{4,5})", value or "", re.I)
    return match.group(1) if match else None


def ancestors(organization_id: str, by_id: dict[str, dict]) -> set[str]:
    result = set()
    frontier = [organization_id]
    while frontier:
        current = frontier.pop()
        for relation in by_id.get(current, {}).get("parent_relations", []):
            parent_id = relation["parent_id"]
            if parent_id not in result:
                result.add(parent_id)
                frontier.append(parent_id)
    return result


def stable_update_id(organization_id: str, title: str, url: str) -> str:
    digest = hashlib.sha1(f"{organization_id}|{normalize_title(title)}|{canonical_url(url)}".encode()).hexdigest()[:16]
    return f"group-update:{digest}"


def main() -> None:
    registry = read(ORGS, {"organizations": []})
    organizations = registry["organizations"]
    by_org = {row["organization_id"]: row for row in organizations}
    works = read(WORKS, [])
    taxonomy = read(TAXONOMY, {"categories": {}})
    question_evidence = read(QUESTION_EVIDENCE, {"records": []})
    questions_by_work = {
        row.get("work_id"): row.get("question_ids", [])
        for row in question_evidence.get("records", [])
        if row.get("work_id")
    }
    by_arxiv = {row.get("arxiv_id"): row for row in works if row.get("arxiv_id")}
    by_title = {normalize_title(row.get("title", "")): row for row in works if row.get("title")}
    by_project: dict[str, list[dict]] = defaultdict(list)
    for row in works:
        project = normalize_title((row.get("title") or "").split(":", 1)[0])
        if len(project) >= 5:
            by_project[project].append(row)

    candidates = []
    for org in organizations:
        if not org.get("tracking_unit"):
            continue
        for raw in org.get("representative_updates", []):
            candidates.append({**raw, "organization_id": org["organization_id"], "curated": True})
    for raw in read(CANDIDATES, {"candidates": []}).get("candidates", []):
        candidates.append({**raw, "curated": False})

    accepted: dict[str, dict] = {}
    review: dict[str, dict] = {}
    for raw in candidates:
        org_id = raw.get("organization_id")
        if org_id not in by_org or not by_org[org_id].get("tracking_unit"):
            continue
        title = str(raw.get("title") or "").strip()
        url = str(raw.get("url") or "").strip()
        if not title or not url:
            continue
        grade = raw.get("evidence_grade") or "G3"
        # HTML links found inside a GitHub page are not themselves verified
        # releases.  Keep them in the review queue even if an older collector
        # snapshot assigned the source a permissive grade.
        if raw.get("source_type") == "official_github" and not raw.get("curated"):
            grade = "G3"
        update_id = raw.get("update_id") or stable_update_id(org_id, title, url)
        arxiv_id = raw.get("arxiv_id") or extract_arxiv_id(url)
        work = by_arxiv.get(arxiv_id) if arxiv_id else None
        if not work:
            work = by_title.get(normalize_title(title))
        if not work:
            project = normalize_title(title.split(":", 1)[0])
            project_matches = by_project.get(project, [])
            if len(project_matches) == 1:
                work = project_matches[0]
        published_at = raw.get("published_at") or (work or {}).get("first_public_date")
        inferred_direction = taxonomy.get("categories", {}).get((work or {}).get("primary_topic"), {}).get("code")
        item = {
            "update_id": update_id,
            "organization_id": org_id,
            "title": title,
            "url": url,
            "published_at": published_at,
            "date_precision": raw.get("date_precision") or ((work or {}).get("first_public_date_precision") or "unknown"),
            "update_type": raw.get("update_type") or "project",
            "evidence_grade": grade,
            "source_type": raw.get("source_type") or ("official_group_page" if raw.get("curated") else "official_source_monitor"),
            "work_id": (work or {}).get("work_id"),
            "direction_codes": list(dict.fromkeys(raw.get("direction_codes") or ([inferred_direction] if inferred_direction else []))),
            "question_codes": list(dict.fromkeys(raw.get("question_codes") or questions_by_work.get((work or {}).get("work_id"), []))),
            "summary_zh": raw.get("summary_zh") or "官方研究组来源发现的新动态。",
            "first_seen_at": raw.get("first_seen_at") or registry.get("updated") or date.today().isoformat(),
            "strict_peer_reviewed": bool((work or {}).get("strict_peer_reviewed")),
            "curated": bool(raw.get("curated")),
        }
        for field in (
            "artifact_class", "evidence_lane", "publication_status", "peer_reviewed",
            "independent_validation", "metric_owner", "claim_status",
            "technical_stack_tags", "validation_tags", "open_assets", "report_metrics",
        ):
            if field in raw:
                item[field] = raw[field]
        if published_at and published_at < "2024-07-01":
            continue
        if grade in {"G1", "G2"}:
            accepted[update_id] = item
        else:
            review[update_id] = {**item, "review_reason": "G3/G0 evidence cannot enter public research claims automatically."}

    for seed in read(COLLABORATIONS, {"links": []}).get("links", []):
        work = next((row for row in works if row["work_id"] == seed["work_id"]), None)
        if not work:
            continue
        for org_id in seed.get("organization_ids", []):
            if org_id not in by_org:
                continue
            update_id = stable_update_id(org_id, work["title"], seed["evidence_url"])
            accepted[update_id] = {
                "update_id": update_id,
                "organization_id": org_id,
                "title": work["title"],
                "url": seed["evidence_url"],
                "published_at": work.get("first_public_date"),
                "date_precision": work.get("first_public_date_precision") or "unknown",
                "update_type": "peer_reviewed_paper" if work.get("strict_peer_reviewed") else "preprint",
                "evidence_grade": seed.get("evidence_grade", "G2"),
                "source_type": "curated_collaboration_evidence",
                "work_id": work["work_id"],
                "direction_codes": seed.get("direction_codes", []),
                "question_codes": seed.get("question_codes", []),
                "summary_zh": seed.get("summary_zh") or "官方来源支持的跨研究组合作。",
                "first_seen_at": seed.get("verified_at") or read(COLLABORATIONS, {}).get("updated") or date.today().isoformat(),
                "strict_peer_reviewed": bool(work.get("strict_peer_reviewed")),
                "curated": True,
            }
    for seed in read(MANUAL_UPDATES, {"updates": []}).get("updates", []):
        if seed.get("organization_id") not in by_org:
            continue
        grade = seed.get("evidence_grade", "G3")
        item = {**seed, "strict_peer_reviewed": bool((next((row for row in works if row["work_id"] == seed.get("work_id")), {}) or {}).get("strict_peer_reviewed")), "curated": True}
        if grade in {"G1", "G2"}:
            accepted[item["update_id"]] = item
        else:
            review[item["update_id"]] = {**item, "review_reason": "Manual G3/G0 observation is not a research result."}

    update_rows = sorted(
        accepted.values(),
        key=lambda row: (row.get("published_at") or "0000-00-00", row["organization_id"], row["title"]),
        reverse=True,
    )

    grouped: dict[str, set[str]] = defaultdict(set)
    evidence_for_pair: dict[tuple[str, str], dict] = {}
    for update in update_rows:
        work_id = update.get("work_id")
        if not work_id:
            continue
        grouped[work_id].add(update["organization_id"])
        evidence_for_pair[(work_id, update["organization_id"])] = update

    link_rows = []
    for work_id, org_ids in grouped.items():
        leaf_ids = set(org_ids)
        for org_id in org_ids:
            leaf_ids -= ancestors(org_id, by_org) & org_ids
        if not leaf_ids:
            continue
        fractional = round(1 / len(leaf_ids), 8)
        for org_id in sorted(leaf_ids):
            update = evidence_for_pair[(work_id, org_id)]
            link_rows.append(
                {
                    "work_id": work_id,
                    "organization_id": org_id,
                    "role": "contributor",
                    "attribution_basis": "official_group_update",
                    "evidence_grade": update["evidence_grade"],
                    "confidence": 1 if update["evidence_grade"] == "G1" else 0.8,
                    "evidence_url": update["url"],
                    "verified_at": update["first_seen_at"],
                    "allocation_method": "equal_leaf_split",
                    "allocation_quality": "coarse",
                    "fractional_credit": fractional,
                }
            )

    source_snapshot = read(SOURCE_STATUS, {"generated_at": None})
    today = source_snapshot.get("generated_at") or date.today().isoformat()
    UPDATES.write_text(json.dumps({"version": "1.0", "generated_at": today, "updates": update_rows}, ensure_ascii=False, indent=2) + "\n")
    LINKS.write_text(json.dumps({"version": "1.0", "generated_at": today, "links": link_rows}, ensure_ascii=False, indent=2) + "\n")
    REVIEW.write_text(json.dumps({"version": "1.0", "generated_at": today, "candidates": sorted(review.values(), key=lambda row: row["update_id"])}, ensure_ascii=False, indent=2) + "\n")
    if not SOURCE_STATUS.exists():
        SOURCE_STATUS.write_text(json.dumps({"version": "1.0", "generated_at": today, "sources": []}, ensure_ascii=False, indent=2) + "\n")
    print(f"Resolved {len(update_rows)} public updates, {len(link_rows)} work links, {len(review)} review candidates")


if __name__ == "__main__":
    main()
