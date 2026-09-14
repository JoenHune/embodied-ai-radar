"""Derived editorial views of audited report excerpts; no source or count edits."""
from __future__ import annotations

import hashlib
import json
import math
import re
from urllib.parse import quote


def editorial_source_digest(work: dict) -> str:
    source = {"title": work.get("title") or "", "abstract": work.get("abstract") or ""}
    report = work.get("report_text") or {}
    if report.get("status") == "available":
        source["report_text_snapshots"] = sorted(
            [[row["snapshot_id"], row["excerpt_digest"]] for row in report.get("snapshots", [])])
    return hashlib.sha256(json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def report_editorial_view(work: dict, selection: dict) -> dict | None:
    if selection.get("status") != "available" or not selection.get("snapshots"):
        return None
    return {**work, "abstract": "", "summary_zh": "", "title_zh": None, "report_text": selection,
            "source_record_ids": sorted({row["source_record_id"] for row in selection["snapshots"]})}


def report_quote_text(card: dict) -> str:
    report = card.get("report_text") or {}
    if report.get("status") != "available":
        return ""
    return "\n".join(row["text"] for snapshot in report["snapshots"] for row in snapshot.get("excerpts", []))


def report_view_with_provenance(selection: dict, sources: dict, cutoff: str) -> dict:
    links = {}
    for snapshot in selection.get("snapshots", []):
        source = sources.get(snapshot["source_record_id"], {})
        attestation = next((row for row in source.get("report_text_attestations", []) if row.get("attestation_id") == snapshot["attestation_id"]), {})
        proof = attestation.get("proof", {})
        items = []
        url = proof.get("deployment_url", "")
        match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/actions/runs/[0-9]+", url)
        if match:
            items.append({"label": "历史发布的时间证明", "url": url})
            items.append({"label": "该提交登记的原始内容哈希", "url": f"https://github.com/{match[1]}/blob/{proof['commit']}/{quote(proof['path'], safe='/')}"})
        links[snapshot["snapshot_id"]] = items
    return {**selection, "as_of": cutoff, "proof_links": links}


def add_report_facts(facts: dict, cards: list[dict]) -> None:
    """Numeric observations remain attached to a source, condition and work.

    These are author-reported measurements, never additional papers/events.
    Multiple cards for the same observation share one metric and list their
    respective evidence IDs without changing its measured value.
    """
    for card in cards:
        report = card.get("report_text") or {}
        if report.get("status") != "available":
            continue
        for snapshot in report["snapshots"]:
            for observation in snapshot.get("observations", []):
                value = float(observation["value"]) if "." in observation["value"] else int(observation["value"])
                if not math.isfinite(value) or observation["unit"] not in {"count", "ratio", "percentage", "percentage_points"}:
                    raise ValueError("invalid_report_observation")
                key = "report." + snapshot["snapshot_id"] + "." + observation["id"]
                metric = {"value": value, "display_value": observation["value"], "unit": observation["unit"], "evidence_ids": [card["evidence_id"]],
                          "work_id": card["work_id"], "report_title": card["title"], "report_url": snapshot["report_url"],
                          "label": observation["label"], "required_context": observation["context"],
                          "required_qualifier": "公司自报", "measurement_scope": "author_report",
                          "source_record_id": snapshot["source_record_id"], "snapshot_id": snapshot["snapshot_id"],
                          "excerpt_ids": observation["excerpt_ids"]}
                if "约" in observation["label"]:
                    metric["required_approximation"] = "约"
                if key in facts:
                    if any(facts[key].get(field) != metric[field] for field in metric if field != "evidence_ids"):
                        raise ValueError("conflicting_report_observation")
                    metric["evidence_ids"] = sorted(set(facts[key]["evidence_ids"]) | {card["evidence_id"]})
                facts[key] = metric


def render_report_measurements(row: dict, facts: dict) -> dict:
    """Only deterministic source facts can assign a number to its condition.

    Model prose remains qualitative for report-backed claims. This renderer
    never accepts the model's formatting, labels, units or condition mapping.
    """
    lines = []
    seen = set()
    for item in row.get("numeric_claims", []):
        key = item["metric"]
        fact = facts.get(key, {})
        if fact.get("measurement_scope") != "author_report" or key in seen:
            continue
        seen.add(key)
        suffix = {"percentage": "%", "percentage_points": " 个百分点"}.get(fact["unit"], "")
        value = fact.get("required_approximation", "") + fact["display_value"] + suffix
        lines.append(f"{fact['report_title']}（公司自报）：{fact['required_context']}；{fact['label']}：{value}。")
    return {**row, "summary": row["summary"] + ("\n\n" + "\n".join(lines) if lines else "")}
