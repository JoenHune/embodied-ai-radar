#!/usr/bin/env python3
"""Build the checked-in organization registry from isolated research notes.

This is a seed/import helper, not part of the weekly build.  It accepts the
three `.research/groups-*.json` files produced during the initial curation,
normalizes their shapes, adds explicit parent entities, and writes the stable
`config/organizations.json` registry.  Subsequent changes should be made to
the registry and supported by official evidence rather than inferred from a
paper affiliation string.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_FILES = [
    ROOT / ".research" / "groups-corporate.json",
    ROOT / ".research" / "groups-academic.json",
    ROOT / ".research" / "groups-platform-watch.json",
]
OUTPUT = ROOT / "config" / "organizations.json"

PARENT_URLS = {
    "NVIDIA": "https://www.nvidia.com/",
    "Carnegie Mellon University": "https://www.cmu.edu/",
    "Stanford University": "https://www.stanford.edu/",
    "University of California, Berkeley": "https://www.berkeley.edu/",
    "MIT": "https://www.mit.edu/",
    "Massachusetts Institute of Technology": "https://www.mit.edu/",
    "University of Washington": "https://www.washington.edu/",
    "Tsinghua University": "https://www.tsinghua.edu.cn/en/",
    "Amazon": "https://www.amazon.science/",
    "Google DeepMind": "https://deepmind.google/",
    "Meta": "https://ai.meta.com/",
    "ByteDance": "https://seed.bytedance.com/",
    "Toyota Research Institute": "https://www.tri.global/",
    "Columbia University": "https://www.columbia.edu/",
    "New York University": "https://www.nyu.edu/",
    "ETH Zurich": "https://ethz.ch/en.html",
    "EPFL": "https://www.epfl.ch/",
    "Cornell University": "https://www.cornell.edu/",
    "University of Texas at Austin": "https://www.utexas.edu/",
    "University of California, San Diego": "https://ucsd.edu/",
    "Princeton University": "https://www.princeton.edu/",
    "University of Oxford": "https://www.ox.ac.uk/",
    "Technical University of Munich": "https://www.tum.de/en/",
    "Allen Institute for AI": "https://allenai.org/",
    "The University of Hong Kong": "https://www.hku.hk/",
}
PARENT_ID_OVERRIDES = {
    "Carnegie Mellon University Robotics Institute": "org:cmu-robotics-institute",
    "MIT Computer Science and Artificial Intelligence Laboratory": "org:mit-csail",
}


def slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def read_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return payload
    for key in ("organizations", "groups", "records"):
        if isinstance(payload.get(key), list):
            return payload[key]
    raise ValueError(f"unsupported research payload shape: {path}")


def normalize_urls(value) -> dict:
    if isinstance(value, str):
        return {"home": value}
    if isinstance(value, list):
        result = {}
        for index, url in enumerate(value):
            lowered = str(url).lower()
            kind = "home" if index == 0 else (
                "publications" if "publication" in lowered else
                "projects" if "project" in lowered else
                "people" if any(token in lowered for token in ("people", "team", "about")) else
                "blog" if "blog" in lowered else "publications"
            )
            result.setdefault(kind, str(url))
        return result
    value = dict(value or {})
    return {str(key): str(url) for key, url in value.items() if url}


def normalize_update(item: dict, organization_id: str, index: int) -> dict:
    title = str(item.get("title") or "").strip()
    update_id = item.get("update_id") or f"update:{slug(organization_id)}:{index + 1}"
    update_type = {
        "paper": "preprint",
        "release": "project",
        "research_release": "technical_report",
        "model": "model_release",
        "product": "deployment",
        "publication_roundup": "project",
        "research_output": "project",
        "recruitment": "hiring_signal",
        "investor_update": "organization_change",
    }.get(item.get("update_type"), item.get("update_type") or "project")
    evidence_grade = item.get("evidence_grade") or item.get("attribution_grade") or "G1"
    if update_type in {"hiring_signal", "organization_change"}:
        evidence_grade = "G3"
    return {
        "update_id": update_id,
        "title": title,
        "url": item.get("url") or "",
        "published_at": item.get("published_at") or item.get("published") or None,
        "date_precision": item.get("date_precision") or ("day" if item.get("published_at") else "unknown"),
        "update_type": update_type,
        "evidence_grade": evidence_grade,
        "source_type": item.get("source_type") or "official_group_page",
        "direction_codes": list(dict.fromkeys(item.get("direction_codes") or [])),
        "question_codes": list(dict.fromkeys(item.get("question_codes") or [])),
        "summary_zh": item.get("summary_zh") or item.get("summary") or "官方研究组页面列出的代表工作。",
    }


def normalize_group(row: dict) -> dict:
    raw_id = row.get("organization_id") or row.get("id") or ""
    organization_id = raw_id if str(raw_id).startswith("org:") else f"org:{row.get('slug') or slug(row.get('display_name') or row.get('canonical_name'))}"
    official_value = row.get("official_urls") or row.get("official_url")
    if not official_value:
        channels = row.get("monitoring_channels") or []
        channel_kind_map = {
            "engineering_and_research": "blog",
            "research_and_engineering": "blog",
            "company": "home",
            "deployment_case_studies": "projects",
            "deployment": "projects",
            "labs": "people",
            "models": "models",
            "datasets": "datasets",
        }
        official_value = {
            (item.get("channel_type") if item.get("channel_type") in {"home", "publications", "projects", "research", "people", "hiring", "blog", "github"} else channel_kind_map.get(item.get("channel_type"), f"source_{index + 1}")): item.get("url")
            for index, item in enumerate(channels) if item.get("url")
        }
    if not official_value:
        official_value = [item.get("url") for item in row.get("official_sources") or [] if item.get("url")]
    official_urls = normalize_urls(official_value)
    parent_name = (row.get("parent_name") or row.get("parent_institution") or "").strip()
    parent_relations = []
    if parent_name and parent_name.lower() != str(row.get("display_name", "")).lower():
        parent_relations.append(
            {
                "parent_id": PARENT_ID_OVERRIDES.get(parent_name, f"org:{slug(parent_name)}"),
                "relation": "part_of",
                "valid_from": row.get("active_from"),
                "valid_to": row.get("active_to"),
                "evidence_url": official_urls.get("home") or next(iter(official_urls.values()), ""),
            }
        )
    leaders = []
    for leader in row.get("leaders") or []:
        if isinstance(leader, str):
            leader = {"name": leader, "role": "Lead", "source_url": official_urls.get("people") or official_urls.get("home")}
        leaders.append(
            {
                "name": leader.get("name") or "",
                "role": leader.get("role") or "Lead",
                "valid_from": leader.get("valid_from"),
                "valid_to": leader.get("valid_to"),
                "source_url": leader.get("source_url") or official_urls.get("people") or official_urls.get("home") or "",
            }
        )
    update_source = [*(row.get("representative_updates") or []), *(row.get("representative_research_updates") or [])]
    for item in row.get("peer_reviewed_evidence") or []:
        update_source.append({
            "title": item.get("title"), "url": item.get("url"),
            "published_at": item.get("published") or item.get("published_at"),
            "update_type": "peer_reviewed_paper", "evidence_grade": "G1",
            "summary_zh": item.get("note") or "官方同行评审研究证据。",
        })
    for item in row.get("deployment_evidence") or []:
        update_source.append({
            "title": item.get("title"), "url": item.get("url"),
            "published_at": item.get("published") or item.get("published_at"),
            "update_type": "deployment", "evidence_grade": "G1",
            "summary_zh": item.get("note") or "公司官方披露的部署证据；不等同同行评审。",
        })
    updates = [
        normalize_update(item, organization_id, index)
        for index, item in enumerate(update_source)
        if item.get("title") and item.get("url")
    ]
    entity_type = {
        "corporate_lab": "laboratory",
        "corporate_research_group": "research_group",
        "independent_research_company": "research_company",
        "robotics_company": "research_company",
        "academic_lab": "laboratory",
        "pi_group": "research_group",
        "university_research_institute": "research_institute",
        "open_research_platform": "research_institute",
        "commercial_robotics_company": "deployment_team",
    }.get(row.get("entity_type") or row.get("organization_type"), row.get("entity_type") or "research_group")
    region_value = row.get("region") or "Global"
    region = region_value.get("macro_region") if isinstance(region_value, dict) else region_value
    country = region_value.get("country") if isinstance(region_value, dict) else (row.get("country") or "Unknown")
    focus = row.get("inferred_focus") or {}
    health = row.get("source_health") or "healthy"
    if isinstance(health, dict):
        health = health.get("status") or "unverified"
    if health == "degraded":
        health = "partial"
    return {
        "organization_id": organization_id,
        "display_name": row.get("display_name") or row.get("canonical_name") or "",
        "short_name": row.get("short_name") or row.get("display_name") or row.get("canonical_name") or "",
        "slug": row.get("slug") or organization_id.removeprefix("org:"),
        "entity_type": entity_type,
        "tracking_unit": True,
        "tracking_category": row.get("tracking_category") or "academic",
        "region": region or "Global",
        "country": country or "Unknown",
        "aliases": list(dict.fromkeys(row.get("aliases") or [])),
        "parent_relations": parent_relations,
        "official_urls": official_urls,
        "leaders": leaders,
        "active_from": row.get("active_from"),
        "active_to": row.get("active_to"),
        "pi_lineage_id": row.get("pi_lineage_id"),
        "declared_direction_codes": list(dict.fromkeys(row.get("declared_direction_codes") or row.get("direction_codes") or focus.get("directions") or [])),
        "question_codes": list(dict.fromkeys(row.get("question_codes") or focus.get("questions") or [])),
        "disclosure_level": row.get("disclosure_level") or "medium",
        "status": row.get("status") or ("observation" if row.get("tracking_category") == "deployment_watch" else "active"),
        "last_checked": row.get("last_checked") or date.today().isoformat(),
        "last_changed": row.get("last_changed"),
        "source_health": health,
        "summary_zh": row.get("summary_zh") or focus.get("summary") or row.get("inclusion_basis") or "全球具身智能关键研究组。",
        "information_gaps": row.get("information_gaps") or [],
        "representative_updates": updates,
    }


def parent_node(parent_name: str, child: dict) -> dict:
    parent_id = f"org:{slug(parent_name)}"
    return {
        "organization_id": parent_id,
        "display_name": parent_name,
        "short_name": parent_name,
        "slug": parent_id.removeprefix("org:"),
        "entity_type": "company" if child["tracking_category"] in {"corporate", "deployment_watch"} else "university",
        "tracking_unit": False,
        "tracking_category": "parent",
        "region": child["region"],
        "country": child["country"],
        "aliases": [],
        "parent_relations": [],
        "official_urls": {"home": PARENT_URLS.get(parent_name, child["official_urls"].get("home", ""))},
        "leaders": [],
        "active_from": None,
        "active_to": None,
        "pi_lineage_id": None,
        "declared_direction_codes": [],
        "question_codes": [],
        "disclosure_level": "medium",
        "status": "active",
        "last_checked": child["last_checked"],
        "last_changed": None,
        "source_health": "healthy",
        "summary_zh": f"{parent_name} 母机构节点；研究成果由已核验子研究组向上聚合。",
        "representative_updates": [],
    }


def main() -> None:
    missing = [str(path) for path in RESEARCH_FILES if not path.exists()]
    if missing:
        raise SystemExit(f"missing research files: {missing}")
    groups = [normalize_group(row) for path in RESEARCH_FILES for row in read_rows(path)]
    if len(groups) != 60:
        raise SystemExit(f"expected exactly 60 tracking groups, got {len(groups)}")
    ids = [row["organization_id"] for row in groups]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate organization_id in research files")
    parents: dict[str, dict] = {}
    for group in groups:
        for relation in group["parent_relations"]:
            parent_id = relation["parent_id"]
            if parent_id not in parents and parent_id not in set(ids):
                display_name = parent_id.removeprefix("org:").replace("-", " ").title()
                for candidate in PARENT_URLS:
                    if f"org:{slug(candidate)}" == parent_id:
                        display_name = candidate
                        break
                parents[parent_id] = parent_node(display_name, group)
    payload = {
        "version": "1.0",
        "updated": date.today().isoformat(),
        "tracking_target": 60,
        "organizations": sorted([*parents.values(), *groups], key=lambda row: (not row["tracking_unit"], row["tracking_category"], row["display_name"])),
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUTPUT}: {len(groups)} tracked groups + {len(parents)} parent nodes")


if __name__ == "__main__":
    main()
