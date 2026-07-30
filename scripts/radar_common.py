#!/usr/bin/env python3
"""Shared normalization, classification, and canonical-ID helpers for radar v2."""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "config" / "taxonomy-v2.json"
TAXONOMY = json.loads(TAXONOMY_PATH.read_text())


def clean_text(value: Any) -> str:
    """Normalize metadata text without losing meaningful punctuation."""
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    value = re.sub(r"<[^>]+>", " ", html.unescape(str(value)))
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", clean_text(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = clean_text(value).lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.rstrip(" .") or None


def extract_arxiv_id(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(?:arxiv:|arxiv\.org/(?:abs|pdf)/)?(\d{4}\.\d{4,5})(?:v\d+)?", value, re.I)
    return match.group(1) if match else None


def canonical_work_id(
    *,
    arxiv_id: str | None = None,
    doi: str | None = None,
    title: str,
    first_author: str | None = None,
    year: int | str | None = None,
) -> str:
    arxiv_id = extract_arxiv_id(arxiv_id)
    if arxiv_id:
        return f"arxiv:{arxiv_id}"
    doi = normalize_doi(doi)
    if doi:
        return f"doi:{doi}"
    payload = "|".join([normalize_title(title), normalize_title(first_author or ""), str(year or "")])
    return f"title:{hashlib.sha1(payload.encode()).hexdigest()[:20]}"


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text for term in terms)


def classify_research(
    *,
    title: str,
    abstract: str = "",
    extra_text: str = "",
    source_is_robotics: bool = False,
) -> dict:
    """High-recall, transparent v2 classification.

    This deliberately produces a candidate state. A lexical hit is evidence for
    screening, not a claim that the work is a strategic trend or a top paper.
    """
    title_lower = clean_text(title).lower()
    abstract_lower = clean_text(abstract).lower()
    text = f"{title_lower} {abstract_lower} {clean_text(extra_text).lower()}".strip()
    robot_context = source_is_robotics or _contains_any(text, TAXONOMY["boundary_terms"])

    hard_excluded = _contains_any(text, TAXONOMY.get("hard_exclude_context", []))
    has_robot_action = _contains_any(text, TAXONOMY.get("robot_action_context", []))
    excluded_context = _contains_any(text, TAXONOMY.get("exclude_unless_robot_action_context", []))
    if hard_excluded and not has_robot_action:
        return {
            "status": "excluded",
            "score": 0,
            "classifier_version": TAXONOMY["version"],
            "reasons": ["hard_exclude_without_robot_action_context"],
            "primary_topic": None,
            "topics": [],
            "topic_scores": {},
            "tags": [],
        }
    if excluded_context and not has_robot_action and not source_is_robotics:
        return {
            "status": "excluded",
            "score": 0,
            "classifier_version": TAXONOMY["version"],
            "reasons": ["excluded_context_without_robot_action_context"],
            "primary_topic": None,
            "topics": [],
            "topic_scores": {},
            "tags": [],
        }
    if not robot_context:
        return {
            "status": "excluded",
            "score": 0,
            "classifier_version": TAXONOMY["version"],
            "reasons": ["outside_robotics_boundary"],
            "primary_topic": None,
            "topics": [],
            "topic_scores": {},
            "tags": [],
        }

    scores: dict[str, float] = {}
    hits_by_topic: dict[str, list[str]] = {}
    for topic, spec in TAXONOMY["categories"].items():
        hits_title = [term for term in spec["include"] if term.lower() in title_lower]
        hits_abstract = [
            term for term in spec["include"]
            if term.lower() in abstract_lower and term not in hits_title
        ]
        score = 3.0 * len(hits_title) + len(hits_abstract)
        required = spec.get("required_context", [])
        if required and not _contains_any(text, required):
            score = 0
            hits_title = []
            hits_abstract = []
        scores[topic] = score
        hits_by_topic[topic] = [*hits_title, *hits_abstract]

    # Rescue method-specific papers whose titles avoid generic taxonomy phrases.
    rescues = {
        "policy_learning": [
            "visuomotor", "policy learning", "policy optimization", "skill learning",
            "behavior cloning", "behaviour cloning", "reinforcement learning"
        ],
        "dexterous_manipulation": [
            "grasping", "grasp synthesis", "manipulation", "tactile sensing"
        ],
        "humanoid_whole_body": [
            "walking", "running", "locomotion", "whole body"
        ],
        "navigation_mobile_manipulation": [
            "robot navigation", "mobile robot", "visual navigation"
        ],
    }
    for topic, terms in rescues.items():
        if scores.get(topic, 0) == 0 and _contains_any(text, terms) and has_robot_action:
            scores[topic] = 1.0
            hits_by_topic[topic] = ["contextual_rescue"]

    ordered_topics = list(TAXONOMY["categories"])
    ranked = sorted(ordered_topics, key=lambda key: (-scores[key], ordered_topics.index(key)))
    primary = ranked[0] if scores[ranked[0]] > 0 else None
    topics = [key for key in ordered_topics if scores[key] > 0]
    max_score = scores[primary] if primary else 0
    tags = [
        key
        for key, terms in TAXONOMY["horizontal_tags"].items()
        if _contains_any(text, terms)
    ]
    if max_score >= 3 or (max_score >= 2 and bool(abstract_lower)):
        status = "included"
    elif max_score > 0:
        status = "candidate"
    else:
        status = "manual_review" if source_is_robotics else "excluded"
    reasons = []
    if primary:
        reasons.append(f"primary:{primary}")
        reasons.extend(f"hit:{term}" for term in hits_by_topic[primary][:5])
    elif source_is_robotics:
        reasons.append("robotics_venue_without_v2_topic_hit")
    return {
        "status": status,
        "score": max_score,
        "classifier_version": TAXONOMY["version"],
        "reasons": reasons,
        "primary_topic": primary,
        "topics": topics,
        "topic_scores": scores,
        "tags": tags,
    }


def date_from_parts(value: dict | list | None) -> tuple[str | None, str]:
    """Convert Crossref-style date-parts to ISO date and precision."""
    if not value:
        return None, "unknown"
    if isinstance(value, dict):
        parts = value.get("date-parts", [[]])
        parts = parts[0] if parts else []
    else:
        parts = value
    if not parts:
        return None, "unknown"
    year = int(parts[0])
    if len(parts) == 1:
        return f"{year:04d}-01-01", "year"
    month = int(parts[1])
    if len(parts) == 2:
        return f"{year:04d}-{month:02d}-01", "month"
    return f"{year:04d}-{month:02d}-{int(parts[2]):02d}", "day"
