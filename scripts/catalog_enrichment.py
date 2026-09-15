"""Idempotent source ingestion and evidence-scoped canonical facts."""
from __future__ import annotations

import copy
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from catalog_rules import attribution_valid, publication_verified, research_eligible, normalized_title
from catalog_store import encode, fingerprint, read_table
from prepare_catalog import blank_from_source, merge_work
from temporal_evidence import evidence_as_of, public_day
from radar_common import normalize_doi, extract_arxiv_id
from fulltext_classification_reviews import locked_fields as fulltext_locked_fields, taxonomy_projection

MANAGED_FIELDS = ("title", "abstract", "authors", "institutions", "first_public_date", "first_public_date_precision", "primary_direction", "directions", "questions", "facets", "relevance", "classification_state")


def deduplicate(rows, keys):
    by_key = {}
    for row in rows:
        key = tuple(row.get(field) for field in keys) if keys else encode(row)
        by_key[key] = row
    return list(by_key.values())


def _identifier_history(work: dict) -> list[tuple[str, str]]:
    """Normalize hard DOI/arXiv identities without changing primary values."""
    values = defaultdict(list)
    for kind, value in work.get("identifiers", {}).items():
        if value:
            values[kind].append(value)
    for kind, history in work.get("identifier_aliases", {}).items():
        values[kind].extend(history if isinstance(history, list) else [history])
    for alias in work.get("aliases", []):
        if isinstance(alias, str) and alias.startswith(("doi:", "arxiv:")):
            kind, value = alias.split(":", 1)
            values[kind].append(value)
    result = []
    for kind in ("doi", "arxiv"):
        for value in values[kind]:
            if not isinstance(value, str) or not value.strip():
                continue
            normalized = normalize_doi(value) if kind == "doi" else extract_arxiv_id(value)
            if normalized and (kind, normalized) not in result:
                result.append((kind, normalized))
    return result


def finalize_facts(payload: dict, when: str) -> dict:
    fulltext_locked_fields(payload)  # Never finalize over a drifted active review.
    works = {row["work_id"]: row for row in payload["works"]}
    sources = {row["source_record_id"]: row for row in payload["source-records"]}
    official_urls = {row.get("url") for row in sources.values() if row.get("source_type") in {"official-proceedings", "peer-review", "official_openreview_decision"}}
    official_urls.discard(None)
    by_work = defaultdict(list)
    sources_by_url = defaultdict(list)
    for source in sources.values():
        if source.get("url"):
            sources_by_url[source["url"]].append(source)
    for manifestation in payload["manifestations"]:
        # Preserve IDs across metadata corrections; status is verified locally.
        manifestation["peer_reviewed"] = publication_verified(manifestation, official_urls)
        manifestation["track"] = manifestation.get("track") or ("main_conference" if manifestation.get("kind") == "conference" else "journal" if manifestation.get("kind") == "journal" else "research_artifact")
        manifestation["publication_status"] = (
            "accepted_peer_reviewed" if manifestation["peer_reviewed"] and manifestation.get("status") in {"Accept", "Accept (Oral)", "Accept (Poster)", "accepted_peer_reviewed", "accepted_official"}
            else "published_proceedings" if manifestation["peer_reviewed"] and manifestation["kind"] == "conference"
            else "published_journal" if manifestation["peer_reviewed"]
            else "technical_report" if manifestation["kind"] == "technical_report"
            else "preprint" if manifestation["kind"] == "preprint" else "unverified"
        )
        source_dates = [s for s in sources_by_url.get(manifestation.get("url"), []) if s.get("date_precision") in {"day", "month"} and s.get("published_at") == manifestation.get("published_at")]
        if source_dates:
            manifestation["date_precision"] = source_dates[0]["date_precision"]
        by_work[manifestation["work_id"]].append(manifestation)
    for wid, work in works.items():
        versions = by_work.get(wid, [])
        date_changed = False
        earlier_publication = sorted((v for v in versions if v.get("peer_reviewed") and v.get("published_at") and v.get("date_precision") == "day" and (not work.get("first_public_date") or v["published_at"][:10] < work["first_public_date"][:10])), key=lambda v: v["published_at"])
        date_managed = work.get("_managed_field_hashes", {}).get("first_public_date")
        if earlier_publication and (date_managed is None or date_managed == fingerprint(work.get("first_public_date"))):
            date_changed = True
            version = earlier_publication[0]
            work.setdefault("date_history", []).append({"previous_date": work.get("first_public_date"), "reason": "verified_publication_predates_arxiv_upload", "evidence_manifestation_id": version["manifestation_id"]})
            work["first_public_date"] = version["published_at"][:10]
            work["first_public_date_precision"] = "day"
            work["first_public_date_source"] = version["source_record_id"]
            payload["field-provenance"].append({"work_id": wid, "field": "first_public_date", "source_record_id": version["source_record_id"], "observed_at": None, "basis": "earliest_verified_publication"})
        work["manifestation_ids"] = sorted({v["manifestation_id"] for v in versions})
        work["strict_peer_reviewed"] = any(v["peer_reviewed"] for v in versions)
        work["source_record_ids"] = sorted(set(work.get("source_record_ids", [])))
        flags = work.get("evidence_flags", {})
        if any(v["kind"] == "code" and v.get("url", "").startswith("https://github.com/") and v.get("status") in {"verified_repository", "verified_asset_release"} for v in versions):
            flags["open_code"] = True
        flags["benchmark"] = any(v["kind"] == "benchmark" for v in versions)
        checked = evidence_as_of(work, versions, when, sources)
        for flag, value in checked["evidence_flags"].items():
            if value:
                flags[flag] = True
        work["evidence_flags"] = flags
        company = any(v["kind"] in {"technical_report", "demo"} and v.get("evidence_layer") != "S" for v in versions)
        independent = bool(work.get("independent_replication_evidence_ids"))
        if work["strict_peer_reviewed"] and independent and flags.get("real_robot"):
            work["evidence_grade"] = "E4"
        elif work["strict_peer_reviewed"] or independent:
            work["evidence_grade"] = "E3"
        elif company:
            work["evidence_grade"] = "E1"
        elif any(flags.get(k) for k in ["real_robot", "open_code", "open_data", "open_model", "benchmark", "deployment"]):
            work["evidence_grade"] = "E2"
        else:
            work["evidence_grade"] = "E0"
        work["updated_at"] = work.get("updated_at") or when
        origin_hashes = work.setdefault("_managed_field_hashes", {})
        for field in MANAGED_FIELDS:
            origin_hashes.setdefault(field, fingerprint(work.get(field)))
        if date_changed:
            work["_managed_field_hashes"]["first_public_date"] = fingerprint(work.get("first_public_date"))
            work["_managed_field_hashes"]["first_public_date_precision"] = fingerprint(work.get("first_public_date_precision"))
    for link in payload["work-organization-links"]:
        if link.get("evidence_grade") == "G2" and not attribution_valid(link, works.get(link["work_id"])):
            link.update(previous_evidence_grade="G2", evidence_grade="G3", review_reason="missing_or_nonoverlapping_membership")
    health_by_org = defaultdict(list)
    for source in payload.get("source-health", []):
        health_by_org[source.get("organization_id")].append(source)
    for org in payload["organizations"]:
        checks = health_by_org.get(org["organization_id"], [])
        if checks:
            org["last_checked"] = max(s.get("last_checked") or "" for s in checks) or org.get("last_checked")
            org["source_health"] = "stale" if any(s.get("consecutive_failures", 0) >= 2 for s in checks) else "partial" if any(s.get("status") != "healthy" for s in checks) else "healthy"
        org["tier"] = org.get("tier") or ("T0" if org.get("tracking_unit") else "T2")

    proof_by_org = {(l["work_id"], l["organization_id"]): l for l in payload["work-organization-links"] if attribution_valid(l, works.get(l["work_id"]))}
    for event in payload["evidence-events"]:
        work = works.get(event.get("work_id"))
        org = event.get("organization_id")
        when_event = event.get("published_at")
        event.setdefault("occurred_at", when_event)
        event.setdefault("date_precision", "day" if when_event else "unknown")
        if when_event and len(when_event) == 10 and event.get("date_precision") == "day":
            event["occurred_at"] = when_event
        event.setdefault("observed_at", None)
        strategic = event.get("evidence_layer") == "S"
        event["research_eligible"] = bool(not strategic and work and research_eligible(work) and (not org or (work["work_id"], org) in proof_by_org))
        if not event["research_eligible"] and not strategic:
            event["review_required"] = True
    known_events = {row["event_id"]: row for row in payload["evidence-events"]}
    for version in payload["manifestations"]:
        if not version["peer_reviewed"]:
            continue
        eid = f"event:validation:{version['manifestation_id']}"
        wid = version["work_id"]
        work = works[wid]
        state = version["publication_status"]
        published = version.get("accepted_at") if state == "accepted_peer_reviewed" else version.get("published_at")
        validation_event = {
            "event_id": eid, "work_id": wid, "organization_id": None,
            "event_type": "accepted" if state == "accepted_peer_reviewed" else "published",
            "title": work["title"], "url": version["url"], "published_at": published,
            "occurred_at": published, "date_precision": version.get("date_precision", "unknown"),
            "observed_at": version.get("observed_at"), "attribution_grade": "G1",
            "source_type": "official_peer_review", "source_record_id": version["source_record_id"],
            "direction_codes": work.get("directions", []), "question_codes": work.get("questions", []),
            "research_eligible": research_eligible(work), "summary_zh": "官方同行评审接收" if state == "accepted_peer_reviewed" else "官方论文集/期刊发表",
            "venue": version.get("venue"), "venue_year": version.get("year"),
        }
        previous = known_events.get(eid)
        if previous is not None:
            # These are derived validation events, not editorial assertions.
            # Source date/precision corrections must reach the existing event
            # without inventing another acceptance or moving first observation.
            validation_event["observed_at"] = previous.get("observed_at") or validation_event["observed_at"]
            previous.update(validation_event)
            previous.pop("review_required", None)
            if not validation_event["research_eligible"]:
                previous["review_required"] = True
        else:
            payload["evidence-events"].append(validation_event)
            known_events[eid] = validation_event
    payload["taxonomy-assignments"] = taxonomy_projection(payload)
    add_canonical_publication_events(payload, works, by_work)
    payload["works"] = sorted(works.values(), key=lambda row: row["work_id"])
    for name, keys in {"manifestations": ["manifestation_id"], "source-records": ["source_record_id"], "work-aliases": ["alias", "work_id"], "work-organization-links": ["work_id", "organization_id", "evidence_url"], "field-provenance": ["work_id", "field", "source_record_id"], "evidence-events": ["event_id"]}.items():
        payload[name] = deduplicate(payload[name], keys)
    return payload


def add_canonical_publication_events(payload: dict, works: dict, versions_by_work: dict) -> None:
    """Attributing a paper must make it visible in its group's dated activity.

    The canonical first-public date is distinct from discovery and acceptance.
    Preserve curated release events and never duplicate a known group release.
    """
    organizations = {row["organization_id"]: row for row in payload["organizations"]}
    events = {row["event_id"]: row for row in payload["evidence-events"]}
    direct = {(row.get("work_id"), row.get("organization_id"), str(row.get("published_at") or "")[:10]): row for row in events.values()
              if row.get("event_type") in {"paper", "preprint", "technical_report", "model_release", "dataset_release", "benchmark_release", "project"}
              and row.get("source_type") != "derived_canonical_first_publication"}
    for link in payload["work-organization-links"]:
        wid, org_id = link["work_id"], link["organization_id"]
        work = works.get(wid)
        if not work or not research_eligible(work) or not attribution_valid(link, work) or not organizations.get(org_id, {}).get("tracking_unit"):
            continue
        published = work.get("first_public_date")
        if not published or work.get("first_public_date_precision") not in {"day", "month"}:
            continue
        event_id = "event:first-publication:" + fingerprint([wid, org_id])[:24]
        existing_release = direct.get((wid, org_id, published[:10]))
        if existing_release:
            if event_id in events:
                events[event_id].update(superseded_by=existing_release["event_id"], research_eligible=False, review_required=True)
            continue
        versions = sorted(versions_by_work.get(wid, []), key=lambda version: (version.get("published_at") != published, version.get("kind") not in {"preprint", "technical_report", "conference", "journal"}, version["manifestation_id"]))
        version = next((v for v in versions if v.get("url")), None)
        if not version:
            continue
        kind = "technical_report" if version["kind"] == "technical_report" else "preprint" if version["kind"] == "preprint" else "paper"
        previous = events.get(event_id, {})
        event = {"event_id": event_id, "work_id": wid, "organization_id": org_id,
                 "event_type": kind, "semantic_role": "canonical_first_publication", "source_type": "derived_canonical_first_publication",
                 "title": work["title"], "url": version["url"], "source_record_id": version["source_record_id"],
                 "published_at": published, "occurred_at": published, "date_precision": work["first_public_date_precision"],
                 "observed_at": previous.get("observed_at") or link.get("verified_at"), "attribution_grade": link["evidence_grade"],
                 "attribution_evidence_url": link["evidence_url"], "attribution_source_record_id": link.get("source_record_id"),
                 "direction_codes": work.get("directions", []), "question_codes": work.get("questions", []),
                 "research_eligible": True, "summary_zh": "首次公开研究；具体贡献与实验条件请查看原文。"}
        if event_id in events:
            events[event_id].update(event)
        else:
            payload["evidence-events"].append(event)
            events[event_id] = event


def ingest_delta(current: dict, incoming: dict) -> dict:
    """Unseen sources update content; exact owned sources may repair identity metadata.

    Historical DOI/arXiv additions do not replay old titles, classification or
    dates, and never overwrite an existing primary identifier. Cross-work
    identifier conflicts require explicit identity review before persistence.
    """
    protected_classification = fulltext_locked_fields(current)
    current_sources = {row["source_record_id"] for row in current["source-records"]}
    unseen = {row["source_record_id"] for row in incoming["source-records"]} - current_sources
    changed = {row.get("work_id") for row in incoming["reconciliation"] if row["source_record_id"] in unseen and row.get("work_id")}
    works = {row["work_id"]: row for row in current["works"]}
    aliases = {a["alias"]: a["work_id"] for a in current["work-aliases"]}
    identity_owners = defaultdict(set)
    for wid, row in works.items():
        for kind, value in _identifier_history(row):
            identity_owners[f"{kind}:{value}"].add(wid)
    for row in current["work-aliases"]:
        if row.get("alias", "").startswith(("doi:", "arxiv:")):
            identity_owners[row["alias"]].add(row["work_id"])
    incoming_sources = {row["source_record_id"]: row for row in incoming["source-records"]}
    current_source_rows = {row["source_record_id"]: row for row in current["source-records"]}
    mapped_sources = defaultdict(set)
    incoming_public_aliases = defaultdict(list)
    for row in incoming.get("work-aliases", []):
        if row.get("work_id") and isinstance(row.get("alias"), str):
            incoming_public_aliases[row["work_id"]].append(row["alias"])
    for row in incoming.get("reconciliation", []):
        if row.get("work_id"):
            mapped_sources[row["work_id"]].add(row["source_record_id"])
    public_aliases = {(row["alias"], row["work_id"]) for row in current["work-aliases"]}
    remap = {}
    for work in incoming["works"]:
        previous_id = work["work_id"]
        incoming_history = _identifier_history({**work, "aliases": [*work.get("aliases", []), *incoming_public_aliases[previous_id]]})
        identity_sources = sorted(set(work.get("source_record_ids", [])) & mapped_sources[previous_id] & set(incoming_sources))
        matches = {owner for kind, value in incoming_history for owner in identity_owners.get(f"{kind}:{value}", set())}
        matches.update(aliases[alias] for alias in work.get("aliases", []) if alias in aliases)
        existing = previous_id if previous_id in works else next(iter(matches)) if len(matches) == 1 else None
        if previous_id not in works and len(matches) > 1:
            raise ValueError(f"Conflicting identifier targets require explicit identity review: {previous_id}")
        has_source_delta = previous_id in changed
        if not has_source_delta:
            if not existing:
                continue
            # Recover metadata lost by an earlier importer only when an exact
            # source is already owned and mapped to this same incoming work.
            # Do not replay titles, classification or dates from an old source.
            shared = set(work.get("source_record_ids", [])) & set(works[existing].get("source_record_ids", [])) & mapped_sources[previous_id] & current_sources
            shared = {sid for sid in shared if sid in incoming_sources and incoming_sources[sid].get("payload_hash") and incoming_sources[sid]["payload_hash"] == current_source_rows[sid].get("payload_hash")}
            if not shared:
                continue
        if existing:
            remap[previous_id] = existing
            target = works[existing]
            owned = set(_identifier_history(target))
            for kind, value in incoming_history:
                other_owners = identity_owners.get(f"{kind}:{value}", set()) - {existing}
                if other_owners and (kind, value) not in owned:
                    raise ValueError(f"Identifier already belongs to another work; explicit identity review required: {kind}:{value}")
            if has_source_delta:
                origin_hashes = target.get("_managed_field_hashes", {})
                for field in MANAGED_FIELDS:
                    if field in protected_classification.get(existing, set()):
                        continue
                    if field not in work:
                        continue
                    if field in {"first_public_date", "first_public_date_precision"} and target.get("first_public_date_source") and target.get("first_public_date") and work.get("first_public_date") and target["first_public_date"] < work["first_public_date"]:
                        continue
                    unchanged = origin_hashes.get(field) == fingerprint(target.get(field))
                    if unchanged or not target.get(field):
                        target[field] = copy.deepcopy(work[field])
                        origin_hashes[field] = fingerprint(target[field])
                target["_managed_field_hashes"] = origin_hashes
                for field in ("manifestation_ids", "source_record_ids", "aliases", "repositories"):
                    target[field] = list(dict.fromkeys([*target.get(field, []), *work.get(field, [])]))
                for kind, value in work.get("identifiers", {}).items():
                    if value and not target.setdefault("identifiers", {}).get(kind):
                        target["identifiers"][kind] = value
                    if value and kind not in {"doi", "arxiv"}:
                        other_history = target.setdefault("identifier_aliases", {}).setdefault(kind, [])
                        if value not in other_history:
                            other_history.append(value)
            for kind, value in incoming_history:
                history = target.setdefault("identifier_aliases", {}).setdefault(kind, [])
                if value not in history:
                    history.append(value)
                alias = f"{kind}:{value}"
                # Existing ambiguous legacy identities remain untouched; never
                # materialize an ambiguous alias as a last-wins public route.
                if identity_owners.get(alias, set()) - {existing}:
                    continue
                identity_owners[alias].add(existing)
                if alias not in target.setdefault("aliases", []):
                    target["aliases"].append(alias)
                if alias != existing and (alias, existing) not in public_aliases:
                    current["work-aliases"].append({"alias": alias, "work_id": existing, "kind": "source_identifier_alias", "valid_from": None, "valid_to": None, "source_record_ids": identity_sources})
                    public_aliases.add((alias, existing))
            if existing != previous_id:
                if (previous_id, existing) not in public_aliases:
                    current["work-aliases"].append({"alias": previous_id, "work_id": existing, "kind": "new_identifier", "valid_from": None, "valid_to": None})
                    public_aliases.add((previous_id, existing))
        else:
            work = copy.deepcopy(work)
            works[previous_id] = work
            for kind, value in incoming_history:
                history = work.setdefault("identifier_aliases", {}).setdefault(kind, [])
                if value not in history:
                    history.append(value)
                alias = f"{kind}:{value}"
                identity_owners[alias].add(previous_id)
                if alias not in work.setdefault("aliases", []):
                    work["aliases"].append(alias)
                if alias != previous_id and (alias, previous_id) not in public_aliases:
                    current["work-aliases"].append({"alias": alias, "work_id": previous_id, "kind": "source_identifier_alias", "valid_from": None, "valid_to": None, "source_record_ids": identity_sources})
                    public_aliases.add((alias, previous_id))
    for table in ["manifestations", "field-provenance", "work-aliases", "work-relations", "work-organization-links", "evidence-events", "reconciliation"]:
        rows = [row for row in incoming.get(table, []) if row.get("work_id") in changed or row.get("source_record_id") in unseen]
        rows = [{**row, "work_id": remap.get(row["work_id"], row["work_id"])} if row.get("work_id") else row for row in rows]
        current[table] = deduplicate([*current.get(table, []), *rows], None)
    current["source-records"].extend(row for row in incoming["source-records"] if row["source_record_id"] in unseen)
    # Metadata-schema enrichment may fill absent provenance fields on an
    # unchanged source payload; it must not overwrite existing observations.
    new_sources = {row["source_record_id"]: row for row in incoming["source-records"]}
    for source in current["source-records"]:
        for key, value in new_sources.get(source["source_record_id"], {}).items():
            if key not in source:
                source[key] = value
    new_events = {row["event_id"]: row for row in incoming["evidence-events"]}
    owned_event_sources = {row["source_record_id"]: row for row in current["source-records"]}
    # Reviewed context updates can have no work by design. Recover them from
    # an exact already-owned source, never by title or organization alone.
    current_event_ids = {row["event_id"] for row in current["evidence-events"]}
    for eid, event in new_events.items():
        sid = event.get("source_record_id")
        exact_owned_source = sid in current_source_rows and sid in incoming_sources and current_source_rows[sid].get("payload_hash") == incoming_sources[sid].get("payload_hash") and incoming_sources[sid].get("payload_hash")
        if eid not in current_event_ids and exact_owned_source and event.get("evidence_layer") == "S" and event.get("review_status") == "verified":
            current["evidence-events"].append(copy.deepcopy(event))
            current_event_ids.add(eid)
    for event in current["evidence-events"]:
        for key in ["report_metrics", "validation_tags", "technical_stack_tags", "open_assets"]:
            if key not in event and key in new_events.get(event["event_id"], {}):
                event[key] = new_events[event["event_id"]][key]
        incoming_event = new_events.get(event["event_id"], {})
        sid = incoming_event.get("source_record_id")
        exact_event_source = sid in incoming_sources and sid in owned_event_sources and incoming_sources[sid].get('payload_hash') and incoming_sources[sid]['payload_hash'] == owned_event_sources[sid].get('payload_hash')
        if incoming_event.get("evidence_layer") == event.get("evidence_layer") == "S" and incoming_event.get("review_status") == event.get("review_status") == "verified" and exact_event_source:
            for key in ("source_record_id", "counts_as_new_paper", "counts_as_new_model", "original_research_eligible"):
                if key not in event and key in incoming_event:
                    event[key] = incoming_event[key]
    if "source-health" in incoming:
        current["source-health"] = incoming["source-health"]
    current["works"] = list(works.values())
    fulltext_locked_fields(current)
    return current


def ingest_conferences(payload: dict, root: Path) -> dict:
    works = {row["work_id"]: row for row in payload["works"]}
    arxiv = {row.get("identifiers", {}).get("arxiv"): row["work_id"] for row in works.values() if row.get("identifiers", {}).get("arxiv")}
    doi = {row.get("identifiers", {}).get("doi"): row["work_id"] for row in works.values() if row.get("identifiers", {}).get("doi")}
    known_aliases = {row["alias"]: row["work_id"] for row in payload["work-aliases"]}
    for path in sorted(root.glob("*/records.jsonl")):
        for row in read_table(path.parent, "records"):
            if row.get("venue_scope") != "main" or row.get("source_kind") != "official_openreview":
                continue
            forum = row["forum_id"]
            # Only the collector's actual public root-note pdate may establish
            # publication. An accepted_at fallback would manufacture new work
            # at the notification date for formerly private submissions.
            public_at = row.get("first_public_at") if (row.get("root_note_public") is True
                        and row.get("root_note_id") == forum
                        and row.get("first_public_at_basis") == "public_root_note_pdate"
                        and row.get("published_at_basis") == "pdate"
                        and row.get("first_public_at") == row.get("published_at")) else None
            public_date = public_day(public_at, row.get("first_public_at_precision")) if public_at else None
            public_source_id = f"source:openreview-publication:{forum}:{fingerprint([forum, public_at])[:16]}" if public_date else None
            wid = known_aliases.get(f"openreview:{forum}") or arxiv.get(row.get("arxiv_id")) or doi.get(row.get("doi"))
            if wid is None:
                # Exact titles require author agreement, never a bare fuzzy title.
                for work in works.values():
                    if normalized_title(work["title"]) == normalized_title(row["title"]) and set(work["authors"]) & set(row.get("authors", [])):
                        wid = work["work_id"]
                        break
            if wid is None:
                work = blank_from_source({**row, "venue": "CoRL"}, row["observed_at"])
                wid = f"openreview:{forum}"
                work["work_id"] = wid
                work["first_public_date"] = public_date.isoformat() if public_date else None
                work["first_public_date_precision"] = "day" if public_date else "unknown"
                work["first_public_date_source"] = public_source_id
                work["first_seen_at"] = row["observed_at"]
                work["first_seen_basis"] = "first_official_conference_observation_for_new_identity"
                if not public_date:
                    work["relevance"]["previous_status"] = work["relevance"]["status"]
                    work["relevance"]["status"] = "manual_review"
                    work["relevance"].setdefault("reasons", []).append("first_public_date_unverified")
                works[wid] = work
            elif public_date and wid.startswith("openreview:") and works[wid].get("first_public_date_precision") == "unknown" and not works[wid].get("first_public_date"):
                # Fill a previously unknown conference-only date, never
                # overwrite an existing arXiv/DOI or reviewed publication date.
                works[wid]["first_public_date"] = public_date.isoformat()
                works[wid]["first_public_date_precision"] = "day"
                works[wid]["first_public_date_source"] = public_source_id
            source_id = f"source:openreview:{forum}:{fingerprint(row)[:16]}"
            if works[wid].get("first_seen_basis") == "first_official_conference_observation_for_new_identity":
                works[wid].setdefault("first_seen_source_record_id", source_id)
            payload["source-records"].append({"source_record_id": source_id, "source_type": "official_openreview_decision", "url": row["forum_url"], "retrieved_at": row["observed_at"], "raw_ref": str(path), "payload_hash": fingerprint(row)})
            if public_source_id:
                payload["source-records"].append({"source_record_id": public_source_id, "source_type": "official_openreview_publication", "url": row["forum_url"],
                    "published_at": public_at, "date_precision": row["first_public_at_precision"], "retrieved_at": row["observed_at"],
                    "root_note_id": forum, "public_date_basis": "public_root_note_pdate", "raw_ref": str(path), "payload_hash": fingerprint([forum, public_at])})
                payload["manifestations"].append({"manifestation_id": f"manifest:openreview-public:{forum}", "work_id": wid,
                    "kind": "preprint", "url": row["forum_url"], "title": row["title"], "venue": row.get("venue", "CoRL"), "year": row.get("year", 2026),
                    "track": "public_manuscript", "status": "public_openreview_manuscript", "published_at": public_at,
                    "date_precision": row["first_public_at_precision"], "observed_at": row["observed_at"], "source_record_id": public_source_id, "peer_reviewed": False})
                works[wid]["source_record_ids"].append(public_source_id)
                if works[wid].get("first_public_date_source") == public_source_id:
                    payload.setdefault("field-provenance", []).append({"work_id": wid, "field": "first_public_date", "source_record_id": public_source_id,
                        "observed_at": row["observed_at"], "basis": "public_root_note_pdate_shanghai_calendar_day"})
            payload["manifestations"].append({
                "manifestation_id": f"manifest:openreview:{forum}", "work_id": wid,
                "kind": "conference", "url": row["forum_url"], "venue": "CoRL", "year": 2026,
                "track": "main_conference", "status": "accepted_peer_reviewed",
                "decision_status": row["decision_status"], "accepted_at": row.get("accepted_at"),
                "published_at": None, "date_precision": row.get("accepted_at_precision", "unknown"),
                "observed_at": row["observed_at"], "source_record_id": source_id,
                "review_records": row.get("review_records", []), "peer_reviewed": True,
            })
            payload["work-aliases"].append({"alias": f"openreview:{forum}", "work_id": wid, "kind": "openreview", "valid_from": None, "valid_to": None})
            payload["reconciliation"].append({"source_record_id": source_id, "work_id": wid, "status": "mapped", "basis": "official_conference_decision"})
            works[wid]["source_record_ids"].append(source_id)
    payload["works"] = list(works.values())
    return payload
