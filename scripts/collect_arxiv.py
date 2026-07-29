#!/usr/bin/env python3
"""Collect arXiv cs.RO papers and apply a transparent high-recall classifier.

The output is an auditable candidate corpus, not a claim of perfect semantic
classification. Curated fields and peer-review evidence are merged later.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TAXONOMY = json.loads((ROOT / "config" / "taxonomy.json").read_text())
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
MONTHS = []
year, month = 2024, 7
while (year, month) <= (2026, 7):
    MONTHS.append(f"{year:04d}-{month:02d}")
    month += 1
    if month == 13:
        year += 1
        month = 1


def month_bounds(month_key: str) -> tuple[str, str]:
    y, m = map(int, month_key.split("-"))
    if m == 12:
        ny, nm = y + 1, 1
    else:
        ny, nm = y, m + 1
    start = f"{y:04d}{m:02d}010000"
    next_start = date(ny, nm, 1).toordinal()
    end_day = date.fromordinal(next_start - 1).day
    end = f"{y:04d}{m:02d}{end_day:02d}2359"
    if month_key == "2026-07":
        end = "202607292359"
    return start, end


def fetch_month(month_key: str) -> str:
    cache = RAW / f"arxiv-csRO-{month_key}.xml"
    if cache.exists() and cache.stat().st_size > 1000:
        return cache.read_text()
    start, end = month_bounds(month_key)
    query = f"cat:cs.RO AND submittedDate:[{start} TO {end}]"
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": 2000,
            "sortBy": "submittedDate",
            "sortOrder": "ascending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "embodied-ai-radar/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                text = response.read().decode("utf-8")
            cache.write_text(text)
            time.sleep(3.1)
            return text
        except Exception as exc:
            if attempt == 3:
                raise
            print(f"retry {month_key}: {exc}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_feed(text: str) -> list[dict]:
    root = ET.fromstring(text)
    rows = []
    for entry in root.findall("a:entry", ATOM):
        raw_id = clean(entry.findtext("a:id", namespaces=ATOM))
        match = re.search(r"/(\d{4}\.\d{4,5})(?:v\d+)?$", raw_id)
        if not match:
            continue
        arxiv_id = match.group(1)
        links = {
            node.attrib.get("rel", ""): node.attrib.get("href", "")
            for node in entry.findall("a:link", ATOM)
        }
        comment = clean(entry.findtext("x:comment", namespaces=ATOM))
        journal_ref = clean(entry.findtext("x:journal_ref", namespaces=ATOM))
        doi = clean(entry.findtext("x:doi", namespaces=ATOM)) or None
        rows.append(
            {
                "id": arxiv_id,
                "title": clean(entry.findtext("a:title", namespaces=ATOM)),
                "authors": [
                    clean(author.findtext("a:name", namespaces=ATOM))
                    for author in entry.findall("a:author", ATOM)
                ],
                "institutions": [],
                "first_submitted": clean(entry.findtext("a:published", namespaces=ATOM))[:10],
                "updated": clean(entry.findtext("a:updated", namespaces=ATOM))[:10],
                "abstract": clean(entry.findtext("a:summary", namespaces=ATOM)),
                "categories": [
                    category.attrib.get("term", "")
                    for category in entry.findall("a:category", ATOM)
                ],
                "comment": comment,
                "journal_ref": journal_ref,
                "doi": doi,
                "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": links.get("related", f"https://arxiv.org/pdf/{arxiv_id}"),
            }
        )
    return rows


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def classify(row: dict) -> dict | None:
    title = row["title"].lower()
    abstract = row["abstract"].lower()
    text = f"{title} {abstract} {row['comment'].lower()}"
    if not contains_any(text, TAXONOMY["boundary_terms"]):
        return None
    if contains_any(
        title,
        ["autonomous driving", "self-driving", "autonomous vehicle", "gui visual agent", "web agent"],
    ):
        return None
    hard_excluded = contains_any(text, TAXONOMY.get("hard_exclude_context", []))
    robot_manipulation_context = contains_any(
        text,
        [
            "robot manipulation", "robotic manipulation", "mobile manipulation",
            "humanoid robot", "robotic hand", "robot arm", "robot policy",
            "physical robot", "legged robot", "quadruped robot",
        ],
    )
    if hard_excluded and not robot_manipulation_context:
        return None
    action_context = contains_any(
        text, ["action", "policy", "planning", "control", "robot", "manipulation", "embodied"]
    )
    if contains_any(text, TAXONOMY["exclude_unless_action_context"]) and not action_context:
        return None

    scores: dict[str, float] = {}
    for topic, spec in TAXONOMY["categories"].items():
        hits_title = sum(1 for term in spec["include"] if term in title)
        hits_text = sum(1 for term in spec["include"] if term in text)
        score = hits_text + 2.0 * hits_title
        if topic == "world_model" and not contains_any(text, spec["required_context"]):
            score = 0
        scores[topic] = score

    # General boundary terms rescue relevant learning/manipulation papers that
    # use method-specific names rather than taxonomy keywords.
    if scores["general_learning"] == 0 and contains_any(
        text,
        ["manipulation policy", "robot policy", "visuomotor", "grasping policy",
         "locomotion policy", "robot learning", "robotic manipulation"]
    ):
        scores["general_learning"] = 1
    if max(scores.values()) < 1:
        return None

    topic_order = ["foundation", "dual_system", "dexterous", "world_model", "general_learning"]
    primary = max(topic_order, key=lambda key: (scores[key], -topic_order.index(key)))
    topics = [key for key in topic_order if scores[key] >= 1]
    tags = [
        key
        for key, terms in TAXONOMY["horizontal_tags"].items()
        if contains_any(text, terms)
    ]
    evidence = {
        "real_robot": "real_robot" in tags,
        "multi_task": contains_any(text, ["multi-task", "multitask", "diverse tasks", "multiple tasks"]),
        "cross_embodiment": contains_any(
            text, ["cross-embodiment", "cross embodiment", "cross-robot", "multiple robot embodiments"]
        ),
        "long_horizon": contains_any(text, ["long-horizon", "long horizon", "long-duration", "multi-stage"]),
        "open_code": "open_code" in tags,
        "open_data": "open_data" in tags,
        "open_model": contains_any(text, ["open model", "model weights", "release the model"]),
    }
    confidence = "high" if scores[primary] >= 4 else "medium" if scores[primary] >= 2 else "low"
    result = dict(row)
    result.update(
        {
            "primary_topic": primary,
            "topics": topics,
            "tags": tags,
            "confidence": confidence,
            "topic_scores": scores,
            "evidence": evidence,
            "official_url": None,
            "code_url": None,
            "project_url": None,
            "peer_review": None,
            "contribution_zh": "",
            "limitation_zh": "",
            "selection_reason_zh": "",
            "source": "arXiv API",
        }
    )
    return result


def period(row: dict) -> str:
    day = row["first_submitted"]
    if "2024-07-01" <= day <= "2025-06-30":
        return "baseline"
    if "2025-07-01" <= day <= "2026-06-30":
        return "analysis"
    if "2026-07-01" <= day <= "2026-07-29":
        return "snapshot"
    return "outside"


def main() -> None:
    all_rows: dict[str, dict] = {}
    for index, month_key in enumerate(MONTHS, 1):
        print(f"[{index}/{len(MONTHS)}] {month_key}", flush=True)
        for row in parse_feed(fetch_month(month_key)):
            all_rows[row["id"]] = row
    candidates = [classified for row in all_rows.values() if (classified := classify(row))]
    candidates.sort(key=lambda row: (row["first_submitted"], row["id"]))
    for row in candidates:
        row["period"] = period(row)

    (PROCESSED / "arxiv-candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2)
    )
    fields = [
        "id", "title", "first_submitted", "updated", "primary_topic", "confidence",
        "categories", "topics", "tags", "authors", "arxiv_url", "doi", "journal_ref",
    ]
    with (PROCESSED / "arxiv-candidates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in candidates:
            output = {key: row.get(key, "") for key in fields}
            for key in ["categories", "topics", "tags", "authors"]:
                output[key] = "|".join(output[key])
            writer.writerow(output)
    counts = {}
    for row in candidates:
        month_key = row["first_submitted"][:7]
        counts.setdefault(month_key, {"total": 0, **{key: 0 for key in TAXONOMY["categories"]}})
        counts[month_key]["total"] += 1
        counts[month_key][row["primary_topic"]] += 1
    (PROCESSED / "monthly-counts.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2)
    )
    print(f"Saved {len(candidates)} candidates from {len(all_rows)} cs.RO records.")


if __name__ == "__main__":
    main()
