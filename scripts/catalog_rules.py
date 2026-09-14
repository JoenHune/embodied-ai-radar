"""Evidence/identity/date rules shared by migration, ingestion and audits."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timezone
from urllib.parse import urlparse

VERIFIED_PUBLICATION_STATES = {
    "peer_reviewed_official_proceedings", "peer_reviewed_official", "published_proceedings",
    "official_publisher_page", "peer_reviewed_official_journal", "published_journal",
}
ACCEPTED_STATES = {"accepted_peer_reviewed", "accepted_official", "Accept", "Accept (Oral)", "Accept (Poster)"}


def normalized_title(value: str) -> str:
    value = re.sub(r"\\(?:textit|textrm|mathrm|mathbf|emph)\{([^}]*)\}", r"\1", value or "")
    value = value.replace("\\pi", "π").replace("$", "")
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in value if c.isalnum())


def publication_verified(version: dict, official_urls: set[str]) -> bool:
    if version.get("kind") not in {"conference", "journal"}:
        return False
    url = (version.get("url") or "").rstrip("/")
    parts = urlparse(url)
    if not parts.scheme.startswith("http") or not parts.netloc:
        return False
    if (version.get("status") or "") not in VERIFIED_PUBLICATION_STATES | ACCEPTED_STATES:
        return False
    if url not in {value.rstrip("/") for value in official_urls}:
        return False
    # A venue home/index is not a per-work proof of peer review.
    if parts.netloc == "proceedings.mlr.press" and not parts.path.endswith(".html"):
        return False
    if parts.netloc.endswith("openreview.net") and not (parts.path == "/forum" and "id=" in parts.query):
        return False
    return True


def eligible_month(work: dict, until: str | None = None) -> str | None:
    value = work.get("first_public_date")
    if work.get("first_public_date_precision") not in {"day", "month"} or not value:
        return None
    if until and value[:10] > until[:10]:
        return None
    try:
        date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None
    return value[:7]


def research_eligible(work: dict) -> bool:
    return work.get("relevance", {}).get("status") == "included"


def attribution_valid(link: dict, work: dict | None) -> bool:
    if not work or not link.get("evidence_url"):
        return False
    grade = link.get("evidence_grade")
    if grade == "G1":
        return True
    if grade != "G2":
        return False
    membership = link.get("membership_evidence") or {}
    start = membership.get("valid_from")
    end = membership.get("valid_to")
    when = work.get("first_public_date")
    authors = {normalized_title(author) for author in work.get("authors", [])}
    person = normalized_title(membership.get("author", ""))
    return bool(start and when and membership.get("source_url") and person in authors
                and start <= when[:10] and (not end or when[:10] <= end))


def event_eligible(event: dict, work: dict | None) -> bool:
    if event.get("evidence_layer") == "S" or event.get("research_eligible") is False:
        return False
    if not work or not research_eligible(work):
        return False
    flags = ("review_required", "date_review_required", "source_review_required", "date_conflict", "source_conflict")
    if any(event.get(flag) for flag in flags):
        return False
    status_types = {"withdrawn", "retracted", "corrected", "expression_of_concern", "reinstated"}
    if event.get("research_status_notice_id") or event.get("event_type") in status_types:
        # A work-level status is not an organizational attribution. Accept it
        # only as the exact projection of an already verified authority notice.
        try:
            from research_status import _interval
        except ModuleNotFoundError:
            from scripts.research_status import _interval
        notice_id = event.get("research_status_notice_id")
        if not isinstance(notice_id, str) or not notice_id.strip():
            return False
        identities = {work.get("work_id"), *work.get("aliases", [])}
        if event.get("work_id") not in identities or event.get("scope") != "work" or event.get("review_status") != "verified":
            return False
        if event.get("attribution_grade") not in {None, "G1", "G2"}:
            return False
        registered = work.get("research_status_notices", [])
        if not isinstance(registered, list):
            return False
        notices = [row for row in registered if isinstance(row, dict) and row.get("notice_id") == notice_id]
        if len(notices) != 1:
            return False
        notice = notices[0]
        if notice.get("scope") != "work" or notice.get("review_status") != "verified" or notice.get("event_type") != event.get("event_type") or notice.get("event_type") not in status_types:
            return False
        if notice.get("work_id", work["work_id"]) not in identities or any(notice.get(flag) for flag in flags):
            return False
        if event.get("date_precision") != notice.get("date_precision") or _interval(notice.get("public_at"), notice.get("date_precision")) is None:
            return False
        if event.get("published_at") != notice.get("public_at") or any(event.get(key) != notice.get("public_at") for key in ["public_at", "occurred_at"] if key in event):
            return False
        def normalized_url(value):
            if not isinstance(value, str) or any(char.isspace() for char in value):
                return None
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                return None
            return parsed._replace(fragment="", scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower()).geturl().rstrip("/")
        try:
            source_url = normalized_url(notice.get("source_url"))
            if not source_url or normalized_url(event.get("url")) != source_url or ("source_url" in event and normalized_url(event["source_url"]) != source_url):
                return False
        except ValueError:
            return False
        ids = notice.get("source_record_ids")
        event_ids = event.get("source_record_ids") or ([event["source_record_id"]] if event.get("source_record_id") else [])
        if not isinstance(ids, list) or not ids or not isinstance(event_ids, list) or any(not isinstance(sid, str) or not sid for sid in [*ids, *event_ids]):
            return False
        if len(ids) != len(set(ids)) or len(event_ids) != len(set(event_ids)):
            return False
        if set(ids) != set(event_ids) or not set(ids) <= set(work.get("source_record_ids", [])):
            return False
        if event.get("source_record_id") is not None and event["source_record_id"] not in ids:
            return False
        return True
    if event.get("attribution_grade") not in {"G1", "G2"}:
        return False
    return True


def evidence_relationships(works: list[dict]) -> list[dict]:
    """Describe shared assets/authors without claiming shared experimental origin.

    Canonical ``project_series_ids`` are explicitly curated project identities,
    not model/benchmark names extracted from text. Repositories and coauthors
    describe relationships only: neither establishes an evidence dependency.
    """
    relations = []
    keys = defaultdict(list)
    pairs = defaultdict(set)
    author_sets = {}
    ids = {work["work_id"] for work in works}
    for work in works:
        wid = work["work_id"]
        for asset in set(work.get("repositories", [])):
            keys[("shared_repository", asset.casefold().rstrip("/"))].append(wid)
        for series in set(work.get("project_series_ids", [])):
            keys[("verified_project_series", series)].append(wid)
        for dependency in work.get("evidence_dependencies", []):
            if not isinstance(dependency, dict):
                continue
            target = dependency.get("target_work_id") or dependency.get("work_id")
            if target in ids and target != wid and dependency.get("review_status") == "verified" and re.match(r"^https?://[^/]+", dependency.get("source_url", "")):
                relations.append({"source_work_id": wid, "target_work_id": target, "type": "verified_evidence_dependency", "source_url": dependency["source_url"], "merges_evidence_origin": True})
        authors = sorted({normalized_title(a) for a in work.get("authors", []) if a})
        author_sets[wid] = set(authors)
        for i, a in enumerate(authors):
            for b in authors[i + 1:]:
                pairs[(a, b)].add(wid)
    for (kind, value), members in keys.items():
        members = sorted(set(members))
        # A star records shared membership in linear space; it is not a claim
        # that unrelated benchmark users should be transitively unioned.
        for wid in members[1:]:
            relations.append({"source_work_id": members[0], "target_work_id": wid, "type": kind, "shared_value": value, "merges_evidence_origin": kind == "verified_project_series"})
    checked = set()
    for members in pairs.values():
        members = sorted(members)
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if (a, b) in checked:
                    continue
                checked.add((a, b))
                shared = author_sets[a] & author_sets[b]
                both = author_sets[a] | author_sets[b]
                if len(shared) >= 2 and len(shared) / len(both) >= 0.3:
                    relations.append({"source_work_id": a, "target_work_id": b, "type": "author_overlap", "shared_authors": sorted(shared), "jaccard": len(shared) / len(both), "merges_evidence_origin": False})
    return sorted(relations, key=lambda row: (row["source_work_id"], row["target_work_id"], row["type"], row.get("shared_value", "")))


def independent_clusters(works: list[dict]) -> dict[str, str]:
    """Group proven common origins, not shared benchmarks or social proximity.

    Distinct origin IDs are *not* proof of independent replication; that needs
    its own dated, reviewed evidence. ``evidence_relationships`` exposes the
    shared-resource and author-overlap links separately for reviewers.
    """
    parent = {work["work_id"]: work["work_id"] for work in works}

    def find(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a, b)] = min(a, b)

    series_owners = {}
    for work in works:
        wid = work["work_id"]
        for series in work.get("project_series_ids", []):
            if series in series_owners:
                union(series_owners[series], wid)
            else:
                series_owners[series] = wid
        for dependency in work.get("evidence_dependencies", []):
            if not isinstance(dependency, dict):
                continue
            target = dependency.get("target_work_id") or dependency.get("work_id")
            if target in parent and target != wid and dependency.get("review_status") == "verified" and re.match(r"^https?://[^/]+", dependency.get("source_url", "")):
                union(wid, target)
    return {wid: find(wid) for wid in parent}
