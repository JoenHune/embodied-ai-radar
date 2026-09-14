"""Pure, additive import of inspected official releases; never merge works.

Run after canonical finalization. Observation (S) events must remain outside
research statistics in every downstream finalizer/exporter. This importer has
no network, clock, or filesystem writes and never modifies its input payload.
"""
from __future__ import annotations

import copy
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

try:
    from catalog_store import fingerprint, read_table
    from temporal_evidence import public_day
except ModuleNotFoundError:
    from scripts.catalog_store import fingerprint, read_table
    from scripts.temporal_evidence import public_day

KINDS = {"preprint", "technical_report", "project", "model", "data", "code", "benchmark", "demo", "deployment"}
EVENTS = {"preprint": "preprint", "technical_report": "technical_report", "project": "project", "model": "model_release",
          "data": "dataset_release", "code": "repository", "benchmark": "benchmark_release", "demo": "company_demo", "deployment": "deployment"}
REQUIRED = {"review_id", "work_id", "mode", "review_status", "reviewed_by", "reviewed_at", "identity_evidence",
            "sources", "manifestations", "organization_links", "relevance_review"}
OPTIONAL = {"new_work", "earlier_date_review", "relations", "gold_id"}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _url(value):
    parsed = urlsplit(value or "")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Reviewed releases require public source URLs")
    return parsed._replace(fragment="").geturl().rstrip("/")


def _resolve(identifier, aliases):
    seen = set()
    while identifier in aliases and aliases[identifier] != identifier:
        if identifier in seen:
            raise ValueError("Alias cycle in release target")
        seen.add(identifier)
        identifier = aliases[identifier]
    return identifier


def _sid(review_id, key):
    return "source:reviewed-release:" + fingerprint([review_id, key])[:24]


def _validate(incoming):
    row = copy.deepcopy(incoming)
    if not REQUIRED <= set(row) or set(row) - REQUIRED - OPTIONAL:
        raise ValueError("Invalid reviewed release fields")
    if row["review_status"] != "verified" or row["mode"] not in {"existing", "create_if_missing"}:
        raise ValueError("Unreviewed release or invalid import mode")
    if not all(_text(row.get(k)) for k in ["review_id", "work_id", "reviewed_by", "reviewed_at"]):
        raise ValueError("Review identity, reviewer and timestamp are required")
    try:
        checked = datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00"))
        if checked.tzinfo is None:
            raise ValueError()
    except ValueError as exc:
        raise ValueError("Review timestamp must carry a timezone") from exc
    sources = {}
    for source in row["sources"]:
        required = {"source_key", "url", "title", "published_at", "date_precision", "retrieved_at", "raw_sha256", "hash_scope", "byte_count", "excerpt", "original_id"}
        if not required <= set(source) or not all(_text(source.get(k)) for k in required - {"published_at", "byte_count"}):
            raise ValueError("Source is missing auditable raw metadata")
        if source["source_key"] in sources or not re.fullmatch(r"[0-9a-f]{64}", source["raw_sha256"]) or source["hash_scope"] != "http_response_body_bytes" or not isinstance(source["byte_count"], int) or source["byte_count"] <= 0:
            raise ValueError("Invalid source key/hash/snapshot size")
        _url(source["url"])
        if source.get("effective_url"):
            _url(source["effective_url"])
        try:
            if datetime.fromisoformat(source["retrieved_at"].replace("Z", "+00:00")).tzinfo is None:
                raise ValueError()
        except ValueError as exc:
            raise ValueError("Source retrieval timestamp must carry a timezone") from exc
        observed = public_day(source["retrieved_at"])
        published = public_day(source["published_at"], source["date_precision"])
        if not observed or observed > public_day(row["reviewed_at"]) or source["date_precision"] not in {"day", "month", "year", "unknown"}:
            raise ValueError("Invalid source observation date")
        if (source["date_precision"] == "unknown" and source["published_at"] is not None) or (source["date_precision"] != "unknown" and not published) or (published and published > observed):
            raise ValueError("Unknown/future source dates cannot be made precise")
        sources[source["source_key"]] = source
    if not sources:
        raise ValueError("Release has no inspected sources")
    def proof(value):
        if not isinstance(value, dict) or value.get("review_status") != "verified" or not _text(value.get("statement")) or not value.get("source_keys") or not set(value["source_keys"]) <= set(sources):
            raise ValueError("Release judgment lacks inspected source evidence")
    proof(row["identity_evidence"])
    identity = row["identity_evidence"]
    if identity.get("basis") not in {"arxiv_identifier", "official_model_identifier", "same_title_all_authors_official_chain", "named_product_deployment", "same_project_followup"}:
        raise ValueError("A title-only or inferred corporate identity is not sufficient")
    if identity.get("confirmed_work_id") != row["work_id"]:
        raise ValueError("Hard identity must select the explicit canonical target")
    relevance = row["relevance_review"]
    proof(relevance)
    if relevance.get("scope") not in {"research_contribution", "research_release", "observation_only"}:
        raise ValueError("Missing research/observation relevance scope")
    if relevance.get("status") not in {"included", "candidate", "manual_review", "excluded", "preserve_existing"}:
        raise ValueError("Invalid relevance review status")
    if relevance.get("status") == "included":
        quote = relevance.get("contribution_excerpt")
        if relevance["scope"] != "research_contribution" or not _text(quote) or not any(quote in sources[key]["excerpt"] for key in relevance["source_keys"]):
            raise ValueError("Included requires a checked technical contribution, not organizational attribution")
        if not re.fullmatch(r"D([1-9]|1[0-5])", relevance.get("primary_direction") or ""):
            raise ValueError("Included release has no reviewed primary contribution direction")
    versions = row["manifestations"]
    if not versions or len({v.get("key") for v in versions}) != len(versions):
        raise ValueError("Manifestation keys must be nonempty and unique")
    for version in versions:
        allowed = {"key", "kind", "source_key", "date_source_key", "evidence_layer", "asset_id", "title", "version", "event"}
        if set(version) - allowed or not _text(version.get("key")) or version.get("kind") not in KINDS or version.get("source_key") not in sources:
            raise ValueError("Invalid manifestation; peer review must use the official publication importer")
        if version.get("date_source_key", version["source_key"]) not in sources or version.get("evidence_layer") not in {"R", "S"}:
            raise ValueError("Invalid manifestation date source or evidence lane")
        if version["kind"] in {"demo", "deployment"} and version["evidence_layer"] != "S":
            raise ValueError("Demo/deployment observations must remain in S layer")
        if relevance["scope"] == "observation_only" and version["evidence_layer"] != "S":
            raise ValueError("Observation release cannot enter a research lane")
    if not row["organization_links"]:
        raise ValueError("Official release needs an explicit execution-unit attribution review")
    for link in row["organization_links"]:
        if link.get("evidence_grade") != "G1" or link.get("source_key") not in sources or not _text(link.get("organization_id")) or not _text(link.get("statement")):
            raise ValueError("Release attribution requires direct inspected G1 proof")
    if row["mode"] == "create_if_missing":
        work = row.get("new_work")
        if not isinstance(work, dict) or not all(_text(work.get(k)) for k in ["title", "abstract"]) or not isinstance(work.get("authors"), list):
            raise ValueError("New work needs a sourced title, abstract and authors")
        allowed = {"title", "abstract", "abstract_kind", "authors", "identifiers", "summary_zh", "directions", "questions", "facets", "source_key"}
        if set(work) - allowed or work.get("source_key") not in sources:
            raise ValueError("New-work fields must not inject derived evidence/peer flags")
        if relevance["status"] == "preserve_existing" or not row["organization_links"]:
            raise ValueError("A new work needs its own relevance and direct attribution review")
        if relevance["status"] == "included" and relevance["primary_direction"] not in work.get("directions", []):
            raise ValueError("Primary direction must be in the reviewed taxonomy")
        if row["work_id"].startswith("arxiv:") and (work.get("identifiers") or {}).get("arxiv") != row["work_id"].split(":", 1)[1]:
            raise ValueError("New arXiv identity mismatch")
        if row["work_id"].startswith("official:") and (work.get("identifiers") or {}).get("official_id") != row["work_id"].split(":", 1)[1]:
            raise ValueError("New official model identity mismatch")
    elif row.get("new_work"):
        raise ValueError("Existing works cannot have replacement metadata")
    earlier = row.get("earlier_date_review")
    if earlier:
        proof(earlier)
        key = earlier.get("date_source_key")
        if key not in sources or sources[key]["date_precision"] != "day" or not public_day(earlier.get("expected_previous_date")) or relevance["scope"] == "observation_only":
            raise ValueError("Earlier work dates need precise research-publication evidence")
        if public_day(sources[key]["published_at"], "day") >= public_day(earlier["expected_previous_date"]):
            raise ValueError("Earlier-date review does not establish an earlier publication")
    for relation in row.get("relations", []):
        if relation.get("relation") not in {"same_product_family", "deployment_of", "followup_of"} or relation.get("source_key") not in sources or not _text(relation.get("related_work_id")):
            raise ValueError("Unsupported relation: this importer cannot merge identities")
    return row


def ingest_reviewed_releases(payload: dict, data: Path | list[dict]) -> dict:
    """Apply a complete reviewed batch additively; input and old fields survive."""
    incoming = read_table(data, "release-additions") if isinstance(data, Path) else data
    prepared = [_validate(row) for row in incoming]
    if len({r["review_id"] for r in prepared}) != len(prepared):
        raise ValueError("Duplicate reviewed release IDs")
    out = copy.deepcopy(payload)
    for name in ["works", "manifestations", "source-records", "work-aliases", "work-organization-links", "field-provenance", "evidence-events", "work-relations", "reconciliation", "taxonomy-assignments"]:
        out.setdefault(name, [])
    # Build each append-only table's fingerprint index once, not once per field
    # citation in a 40k-work catalog. Holding the list prevents id reuse.
    append_indexes = {}
    def _append(rows, value):
        entry = append_indexes.get(id(rows))
        if entry is None:
            entry = (rows, {fingerprint(old) for old in rows})
            append_indexes[id(rows)] = entry
        marker = fingerprint(value)
        if marker not in entry[1]:
            rows.append(value)
            entry[1].add(marker)
    works = {w["work_id"]: w for w in out["works"]}
    organizations = {o["organization_id"]: o for o in out.get("organizations", [])}
    aliases = {a["alias"]: a["work_id"] for a in out["work-aliases"]}
    existing_sources = {s["source_record_id"]: s for s in out["source-records"]}
    for row in prepared:
        rid, digest = row["review_id"], fingerprint(row)
        receipt_id = _sid(rid, "review_receipt")
        previous = existing_sources.get(receipt_id)
        if previous:
            if previous.get("payload_hash") != digest:
                raise ValueError("Archived release review changed; create a new explicit revision")
            continue  # Preserve later manual edits; never replay stale metadata.
        wid = _resolve(row["work_id"], aliases)
        if row["mode"] == "existing" and wid not in works:
            raise ValueError("Existing release target not found by hard ID")
        for link in row["organization_links"]:
            if link["organization_id"] not in organizations or not organizations[link["organization_id"]].get("tracking_unit"):
                raise ValueError("G1 target must be a registered research execution unit")
        local = {s["source_key"]: s for s in row["sources"]}
        ids = {key: _sid(rid, key) for key in local}
        version_urls = {_url(local[v["source_key"]]["url"]) for v in row["manifestations"]}
        if any(_url(v.get("url")) in version_urls and _resolve(v["work_id"], aliases) != wid for v in out["manifestations"] if v.get("url")):
            raise ValueError("Official release URL belongs to another work; explicit identity review required")
        created = wid not in works
        if created:
            new, relevance = row["new_work"], row["relevance_review"]
            source = local[new["source_key"]]
            first_day = public_day(source["published_at"], source["date_precision"])
            first = first_day.isoformat() if first_day else None
            work = {"work_id": wid, "title": new["title"], "title_zh": None, "authors": copy.deepcopy(new["authors"]), "institutions": [],
                    "abstract": new["abstract"], "abstract_kind": new.get("abstract_kind", "source_original"), "summary_zh": new.get("summary_zh", ""),
                    "identifiers": copy.deepcopy(new.get("identifiers", {})), "first_public_date": first, "first_public_date_precision": source["date_precision"],
                    "first_public_date_source": ids[new["source_key"]], "primary_direction": relevance.get("primary_direction"),
                    "directions": copy.deepcopy(new.get("directions", [])), "questions": copy.deepcopy(new.get("questions", [])),
                    "facets": copy.deepcopy(new.get("facets", {"methods": [], "capabilities": [], "embodiments": [], "modalities": []})),
                    "relevance": {"status": relevance["status"], "score": 1 if relevance["status"] == "included" else 0, "classifier_version": "reviewed-release-1",
                                  "reasons": ["inspected_technical_contribution"] if relevance["status"] == "included" else [relevance["scope"]], "review_id": rid},
                    "classification_state": "reviewed", "curated": True, "evidence_grade": "E1" if any(v["kind"] == "technical_report" for v in row["manifestations"]) else "E0",
                    "evidence_flags": {}, "strict_peer_reviewed": False, "repositories": [], "manifestation_ids": [], "source_record_ids": [],
                    "aliases": [row["work_id"]], "updated_at": row["reviewed_at"]}
            works[wid] = work
            out["works"].append(work)
            _append(out["work-aliases"], {"alias": row["work_id"], "work_id": wid, "source": "reviewed_official_release"})
            for code in work["directions"]:
                _append(out["taxonomy-assignments"], {"work_id": wid, "axis": "direction", "code": code, "is_primary": code == work["primary_direction"], "classifier_version": "reviewed-release-1", "confidence": "reviewed", "review_id": rid})
        work = works[wid]
        for key, source in local.items():
            saved = {"source_record_id": ids[key], "source_type": "reviewed_official_release", "url": source["url"], "title": source["title"],
                     "published_at": source["published_at"], "date_precision": source["date_precision"], "retrieved_at": source["retrieved_at"],
                     "source_excerpt": source["excerpt"], "raw_sha256": source["raw_sha256"], "hash_scope": source["hash_scope"], "byte_count": source["byte_count"],
                     "original_id": source["original_id"], "effective_url": source.get("effective_url", source["url"]), "review_id": rid,
                     "reviewed_by": row["reviewed_by"], "reviewed_at": row["reviewed_at"], "review_status": "verified", "payload_hash": fingerprint(source),
                     "raw_ref": "data/release-additions.jsonl#" + rid + ":" + key}
            if source.get("date_basis"):
                saved["date_basis"] = copy.deepcopy(source["date_basis"])
            if ids[key] in existing_sources:
                raise ValueError("Partial/conflicting release receipt; inspect before replaying")
            existing_sources[ids[key]] = saved
            out["source-records"].append(saved)
            _append(out["reconciliation"], {"source_record_id": ids[key], "work_id": wid, "status": "matched_reviewed_identity", "review_id": rid, "original_id": source["original_id"]})
        work["source_record_ids"] = sorted(set(work.get("source_record_ids", [])) | set(ids.values()))
        _append(work.setdefault("release_reviews", []), {"review_id": rid, "identity_evidence": copy.deepcopy(row["identity_evidence"]), "relevance_review": copy.deepcopy(row["relevance_review"]),
                                                         "reviewed_by": row["reviewed_by"], "reviewed_at": row["reviewed_at"], "source_record_ids": sorted(ids.values())})
        for spec in row["manifestations"]:
            source = local[spec["source_key"]]
            dated_key = spec.get("date_source_key", spec["source_key"])
            dated = local[dated_key]
            mid = "manifest:reviewed-release:" + fingerprint([rid, spec["key"]])[:24]
            version = {"manifestation_id": mid, "work_id": wid, "kind": spec["kind"], "title": spec.get("title", source["title"]), "url": source["url"],
                       "published_at": dated["published_at"], "date_precision": dated["date_precision"], "source_record_id": ids[spec["source_key"]],
                       "date_source_record_id": ids[dated_key], "observed_at": source["retrieved_at"], "peer_reviewed": False, "venue": None, "year": None,
                       "status": "reviewed_official_release", "publication_status": "technical_report" if spec["kind"] == "technical_report" else "preprint" if spec["kind"] == "preprint" else "unverified",
                       "track": "strategic_observation" if spec["evidence_layer"] == "S" else "research_artifact", "evidence_layer": spec["evidence_layer"],
                       "review_id": rid, "research_eligible": spec["evidence_layer"] == "R" and work["relevance"]["status"] == "included"}
            for key in ["asset_id", "version"]:
                if spec.get(key):
                    version[key] = spec[key]
            out["manifestations"].append(version)
            work["manifestation_ids"] = sorted(set(work.get("manifestation_ids", [])) | {mid})
            if spec.get("event", True):
                _append(out["evidence-events"], {"event_id": "event:reviewed-release:" + fingerprint([rid, spec["key"]])[:24], "work_id": wid,
                    "organization_id": row["organization_links"][0]["organization_id"] if row["organization_links"] else None,
                    "event_type": EVENTS[spec["kind"]], "title": version["title"], "url": source["url"], "published_at": dated["published_at"], "occurred_at": dated["published_at"],
                    "date_precision": dated["date_precision"], "observed_at": source["retrieved_at"], "source_record_id": ids[spec["source_key"]],
                    "date_source_record_id": ids[dated_key], "source_record_ids": sorted({ids[spec["source_key"]], ids[dated_key]}), "manifestation_id": mid,
                    "source_type": "reviewed_official_release", "attribution_grade": "G1", "evidence_layer": spec["evidence_layer"], "peer_reviewed": False,
                    "research_eligible": version["research_eligible"], "review_required": False, "review_id": rid,
                    "direction_codes": work.get("directions", []) if spec["evidence_layer"] == "R" else [], "question_codes": work.get("questions", []) if spec["evidence_layer"] == "R" else [],
                    "summary_zh": row["relevance_review"]["statement"]})
        for spec in row["organization_links"]:
            key = spec["source_key"]
            _append(out["work-organization-links"], {"work_id": wid, "organization_id": spec["organization_id"], "evidence_grade": "G1", "evidence_url": local[key]["url"],
                    "source_record_id": ids[key], "source_excerpt": local[key]["excerpt"], "attribution_basis": "official_release_or_publications_page", "role": "research_contributor",
                    "confidence": 1, "verified_at": row["reviewed_at"], "verified_by": row["reviewed_by"], "review_id": rid, "reason": spec["statement"]})
        for spec in row.get("relations", []):
            other = _resolve(spec["related_work_id"], aliases)
            if other not in works:
                raise ValueError("Reviewed release relationship target does not exist")
            _append(out["work-relations"], {"relation": spec["relation"], "work_id": wid, "related_work_id": other, "review_id": rid,
                                          "source_record_id": ids[spec["source_key"]], "evidence_url": local[spec["source_key"]]["url"], "independent_evidence": False})
        earlier = row.get("earlier_date_review")
        date_changed = False
        if earlier:
            key = earlier["date_source_key"]
            date_day = public_day(local[key]["published_at"], "day")
            date = date_day.isoformat()
            previous_date = work.get("first_public_date")
            previous_day = public_day(previous_date)
            if previous_date and previous_day is None:
                raise ValueError("Existing publication date is invalid; explicit date review required")
            if previous_date and previous_date != date and previous_date != earlier["expected_previous_date"] and previous_day > date_day:
                raise ValueError("First publication changed since review; preserve manual date and request new review")
            if not previous_date or previous_day > date_day:
                date_changed = True
                history = {"field": "first_public_date", "previous_date": previous_date, "previous_precision": work.get("first_public_date_precision"),
                           "previous_source_record_id": work.get("first_public_date_source"), "date": date, "date_precision": "day", "source_record_id": ids[key],
                           "review_id": rid, "reviewed_at": row["reviewed_at"], "reason": earlier["statement"]}
                _append(work.setdefault("date_history", []), history)
                _append(out["work-relations"], {"relation": "publication_date_revised", "work_id": wid, **history})
                work.update(first_public_date=date, first_public_date_precision="day", first_public_date_source=ids[key], date_authority="reviewed_earlier_official_report")
        for field in ["release_reviews", "manifestation_ids", "source_record_ids"]:
            for sid in sorted(ids.values()):
                _append(out["field-provenance"], {"work_id": wid, "field": field, "source_record_id": sid, "observed_at": row["reviewed_at"], "basis": "reviewed_official_release", "review_id": rid})
        if date_changed:
            for field in ["first_public_date", "first_public_date_precision"]:
                _append(out["field-provenance"], {"work_id": wid, "field": field, "source_record_id": ids[earlier["date_source_key"]],
                    "observed_at": row["reviewed_at"], "basis": "reviewed_earlier_official_report", "review_id": rid})
        if created:
            for field in ["title", "abstract", "authors", "identifiers", "first_public_date", "first_public_date_precision"]:
                _append(out["field-provenance"], {"work_id": wid, "field": field, "source_record_id": ids[row["new_work"]["source_key"]],
                    "observed_at": row["reviewed_at"], "basis": "reviewed_source_summary" if field == "abstract" and row["new_work"].get("abstract_kind") == "reviewed_source_summary" else "official_source_content", "review_id": rid})
            for field in ["relevance", "primary_direction", "directions"]:
                for key in row["relevance_review"]["source_keys"]:
                    _append(out["field-provenance"], {"work_id": wid, "field": field, "source_record_id": ids[key],
                        "observed_at": row["reviewed_at"], "basis": "inspected_technical_contribution", "review_id": rid})
        receipt_source = local[row["sources"][0]["source_key"]]
        receipt = {"source_record_id": receipt_id, "source_type": "official_release_review_receipt", "url": receipt_source["url"], "title": row["review_id"],
                   "retrieved_at": row["reviewed_at"], "review_id": rid, "review_status": "verified", "reviewed_by": row["reviewed_by"], "payload_hash": digest,
                   "raw_ref": "data/release-additions.jsonl#" + rid}
        out["source-records"].append(receipt)
        existing_sources[receipt_id] = receipt
        work["source_record_ids"] = sorted(set(work["source_record_ids"]) | {receipt_id})
    return out
