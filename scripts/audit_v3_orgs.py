"""Audit the actual v3 organization graph, identities and attribution dates."""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator

from radar_common import ROOT
from catalog_store import read_table
from catalog_rules import attribution_valid


def audit_graph(organizations: list[dict], links: list[dict], works: list[dict]) -> list[str]:
    errors = []
    by_id = {row["organization_id"]: row for row in organizations}
    by_work = {row["work_id"]: row for row in works}
    if len(by_id) != len(organizations):
        errors.append("Duplicate organization_id")
    slugs, aliases = {}, {}
    for org in organizations:
        oid = org["organization_id"]
        slug = org.get("slug")
        if slug in slugs and slugs[slug] != oid:
            errors.append(f"Duplicate slug: {slug}")
        slugs[slug] = oid
        for label in [org.get("display_name", ""), *org.get("aliases", [])]:
            key = "".join(c for c in unicodedata.normalize("NFKC", label).casefold() if c.isalnum())
            if not key:
                continue
            if key in aliases and aliases[key] != oid:
                errors.append(f"Ambiguous registered alias: {label}")
            aliases[key] = oid
        for leader in org.get("leaders", []):
            if urlsplit(leader.get("source_url", "")).scheme not in {"http", "https"}:
                errors.append(f"Leader without official source: {oid}")
            if leader.get("valid_from") and leader.get("valid_to") and leader["valid_from"] > leader["valid_to"]:
                errors.append(f"Invalid leader interval: {oid}")
        for relation in org.get("parent_relations", []):
            if relation["parent_id"] not in by_id:
                errors.append(f"Missing parent: {oid} -> {relation['parent_id']}")
            if urlsplit(relation.get("evidence_url", "")).scheme not in {"http", "https"}:
                errors.append(f"Parent without source: {oid}")
    visiting, visited = set(), set()

    def visit(oid):
        if oid in visiting:
            errors.append(f"Organization cycle: {oid}")
            return
        if oid in visited or oid not in by_id:
            return
        visiting.add(oid)
        for relation in by_id[oid].get("parent_relations", []):
            if relation.get("relation") in {"part_of", "historical_part_of"}:
                visit(relation["parent_id"])
        visiting.remove(oid)
        visited.add(oid)

    for oid in by_id:
        visit(oid)
    for link in links:
        if link["organization_id"] not in by_id or link["work_id"] not in by_work:
            errors.append("Dangling work-organization edge")
        elif link.get("evidence_grade") in {"G1", "G2"} and not attribution_valid(link, by_work[link["work_id"]]):
            errors.append(f"Invalid accepted attribution: {link['work_id']} / {link['organization_id']}")
    return errors


def main():
    catalog = ROOT / "data/catalog"
    organizations = read_table(catalog, "organizations")
    schema = json.loads((ROOT / "config/organization.schema.json").read_text())["properties"]["organizations"]["items"]
    validator = Draft202012Validator(schema)
    for org in organizations:
        validator.validate(org)
    errors = audit_graph(organizations, read_table(catalog, "work-organization-links"), read_table(catalog, "works"))
    mandatory = {"org:nvidia-gear", "org:physical-intelligence", "org:cmu-robotics-institute", "org:amazon-far", "org:amazon-robotics", "org:rai-institute", "org:boston-dynamics", "org:nvidia-cosmos-lab", "org:genesis-ai", "org:generalist-ai", "org:figure-ai", "org:dyna-robotics", "org:sunday-robotics", "org:cornell-emprise", "org:ut-austin-rpl", "org:columbia-roam", "org:nyu-grail", "org:ucsd-xiaolong-wang", "org:princeton-irom"}
    missing = mandatory - {org["organization_id"] for org in organizations}
    errors.extend(f"Missing mandatory organization: {oid}" for oid in sorted(missing))
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({"status": "ok", "organizations": len(organizations), "core_groups": sum(org.get("tier") == "T0" for org in organizations)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
