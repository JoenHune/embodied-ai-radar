"""Import reviewed organization additions without inferring lab ownership."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

from catalog_rules import attribution_valid
from catalog_store import fingerprint, read_table


def ingest_attribution_additions(payload: dict, data: Path) -> dict:
    for organization_file in sorted(data.glob("organization-additions*.json")):
        additions = json.loads(organization_file.read_text()).get("organizations", [])
        existing = {row["organization_id"] for row in payload["organizations"]}
        for org in additions:
            if org["organization_id"] not in existing:
                official_channels = (org.get("official_urls") or {}).values()
                valid_channels = [url for url in official_channels if isinstance(url, str) and urlsplit(url).scheme in {"http", "https"} and urlsplit(url).hostname and not urlsplit(url).username and not urlsplit(url).password]
                if not valid_channels:
                    raise ValueError(f"A new organization requires a registered official homepage or research channel: {org['organization_id']}")
                payload["organizations"].append(org)
                existing.add(org["organization_id"])
    works = {row["work_id"]: row for row in payload["works"]}
    organizations = {row["organization_id"]: row for row in payload["organizations"]}
    aliases = {row["alias"]: row["work_id"] for row in payload["work-aliases"]}
    seen = {(row["work_id"], row["organization_id"], row.get("evidence_url")): row for row in payload["work-organization-links"]}
    strength = {"G0": 0, "G3": 1, "G2": 2, "G1": 3}
    additions = [row for path in sorted(data.glob("attribution-additions*.jsonl")) for row in read_table(data, path.stem)]
    for incoming in additions:
        row = dict(incoming)
        row["work_id"] = aliases.get(row["work_id"], row["work_id"])
        key = (row["work_id"], row["organization_id"], row.get("evidence_url"))
        previous = seen.get(key)
        if previous and strength.get(previous.get("evidence_grade"), 0) >= strength.get(row.get("evidence_grade"), 0):
            continue
        if row["work_id"] not in works or row["organization_id"] not in organizations:
            raise ValueError(f"Attribution references an unregistered identity: {key[:2]}")
        if urlsplit(row.get("evidence_url", "")).scheme not in {"http", "https"} or not row.get("source_excerpt"):
            raise ValueError("Reviewed attribution requires an official URL and inspected source excerpt")
        parent_observation = row.get("evidence_grade") == "G0" and not organizations[row["organization_id"]].get("tracking_unit")
        if not attribution_valid(row, works[row["work_id"]]) and not parent_observation:
            raise ValueError("Attribution lacks direct or time-bounded official evidence")
        source_id = "source:attribution:" + fingerprint(row)[:24]
        payload["source-records"].append({"source_record_id": source_id, "source_type": "parent_affiliation" if parent_observation else "official_group_attribution", "url": row["evidence_url"], "retrieved_at": row.get("verified_at"), "source_excerpt": row["source_excerpt"], "payload_hash": fingerprint(row)})
        if parent_observation:
            row["review_required"] = True
        row["source_record_id"] = source_id
        if previous:
            row["prior_attribution"] = dict(previous)
            payload["work-organization-links"] = [link for link in payload["work-organization-links"] if link is not previous]
        payload["work-organization-links"].append(row)
        works[row["work_id"]]["source_record_ids"].append(source_id)
        payload["field-provenance"].append({"work_id": row["work_id"], "field": "organization_id", "source_record_id": source_id, "observed_at": row.get("verified_at"), "basis": row.get("attribution_basis")})
        seen[key] = row
    return payload
