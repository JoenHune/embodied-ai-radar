"""Pure structural quality checks for a full public monthly snapshot.

Call before stripping snapshot.editorial from a lightweight API response.
This module reads no files, creates no prose or citations, and does not replace
the editorial/source validator. source_bound_editorial means a completed
editorial supplies nonempty prose and explicit references, not that this
function independently verified the referenced research.
"""
from __future__ import annotations

from collections import Counter

DIRECTION_CODES = tuple(f"D{i}" for i in range(1, 16))
QUESTION_CODES = tuple(f"Q{i}" for i in range(11))
MISSING_VERSION_SUMMARY = "该方向的已列入研究缺少截止时点可核验的版本原文，不能据此判断实验结果。"
AXIS_STATUSES = ("source_bound_editorial", "zero_registered", "missing_historical_text", "withheld_research_status", "editorial_missing", "not_generated")


def _count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _references(row):
    value = row.get("supporting_ids")
    return value if isinstance(value, list) and value and all(isinstance(item, str) and item.strip() for item in value) else []


def _text(row, field):
    value = row.get(field)
    return value if isinstance(value, str) else ""


def _index(rows):
    indexed, duplicates = {}, set()
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("code"), str):
                continue
            code = row["code"]
            if code in indexed:
                duplicates.add(code)
            indexed[code] = row
    return indexed, duplicates


def _registered(row, family):
    if row is None:
        return None
    if family == "questions":
        return _count(row.get("count"))
    primary, multi = _count(row.get("primary_count")), _count(row.get("multi_label_count"))
    # Zero primary assignments do not imply zero cross-direction coverage.
    # Prefer the encompassing multi-label count, retaining any positive primary
    # count in inconsistent input so recorded work can never become a false zero.
    if multi is not None:
        return max(multi, primary or 0)
    return primary if primary else None


def assess_editorial_completeness(snapshot: dict) -> dict:
    """Return generation state, the 5–8 finding target and all 26 axis states.

    Count-zero and missing-historical-text axes are legitimate accounted-for
    states, not invented findings. Unknown counts or missing snapshot rows are
    not zeros. Only editorial_status=llm_complete enables current editorial
    attribution; retained historical/legacy content cannot satisfy the target.
    The output is newly allocated and contains no references to input objects.
    """
    generated = snapshot.get("editorial_status") == "llm_complete"
    editorial = snapshot.get("editorial")
    editorial = editorial if generated and isinstance(editorial, dict) else {}
    issues = []
    claims = editorial.get("claims")
    count = len(claims) if generated and isinstance(claims, list) else None
    bound = sum(isinstance(row, dict) and bool(_text(row, "title").strip()) and
                bool(_text(row, "summary").strip()) and bool(_references(row)) for row in (claims if isinstance(claims, list) else []))
    executive_status = "not_generated"
    if generated:
        executive_status = "editorial_missing" if count is None else "below_target" if count < 5 else "above_target" if count > 8 else "in_range"
        if executive_status != "in_range":
            issues.append({"code": "executive_" + executive_status, "path": "/editorial/claims"})
        if count is not None and bound != count:
            issues.append({"code": "executive_unbound_or_empty_claims", "path": "/editorial/claims", "count": count - bound})
            if executive_status == "in_range":
                executive_status = "unbound_claims"
    axes = {}
    for family, codes, summary_key in (("directions", DIRECTION_CODES, "direction_summaries"),
                                        ("questions", QUESTION_CODES, "question_summaries")):
        registered, duplicate_counts = _index(snapshot.get(family))
        edited, duplicate_edits = _index(editorial.get(summary_key))
        result = []
        for code in codes:
            source, raw = registered.get(code), edited.get(code, {})
            registered_count = None if code in duplicate_counts else _registered(source, family)
            summary, references = _text(raw, "summary"), _references(raw)
            source_refs = []
            if source:
                for field in ("supporting_ids", "supporting_work_ids"):
                    value = source.get(field)
                    if isinstance(value, list):
                        source_refs.extend(item for item in value if isinstance(item, str) and item.strip())
            has_record = bool(registered_count or source_refs or references)
            known_zero = registered_count == 0 and not source_refs
            blocked_ids = (source or {}).get("status_blocked_work_ids", [])
            all_results_withheld = (isinstance(blocked_ids, list) and registered_count is not None and registered_count > 0
                                    and all(isinstance(wid, str) and wid for wid in blocked_ids)
                                    and len(set(blocked_ids)) == registered_count and not summary.strip() and not references)
            if generated and code in duplicate_edits:
                state = "editorial_missing"
                issues.append({"code": "duplicate_editorial_axis", "path": f"/editorial/{summary_key}", "axis": code})
            elif generated and summary == MISSING_VERSION_SUMMARY and has_record:
                state = "missing_historical_text"
            elif generated and summary.strip() and references and summary != MISSING_VERSION_SUMMARY:
                state = "source_bound_editorial"
            elif all_results_withheld:
                state = "withheld_research_status"
            elif known_zero and not summary.strip() and not references:
                state = "zero_registered"
            else:
                state = "editorial_missing" if generated else "not_generated"
            if state == "editorial_missing":
                issues.append({"code": "axis_editorial_missing", "path": f"/editorial/{summary_key}", "axis": code})
            if code in duplicate_counts:
                issues.append({"code": "duplicate_snapshot_axis", "path": f"/{family}", "axis": code})
            result.append({"code": code, "status": state, "registered_count": registered_count, "citation_count": len(references)})
        axes[family] = result
    counts = Counter(row["status"] for family in axes.values() for row in family)
    axes_complete = not (counts["editorial_missing"] or counts["not_generated"])
    overall = "not_generated" if not generated else "meets_target" if executive_status == "in_range" and axes_complete and not issues else "needs_attention"
    return {"schema_version": "1", "month": snapshot.get("month"),
            "generation_status": "llm_complete" if generated else "not_generated", "overall_status": overall,
            "executive": {"status": executive_status, "count": count, "source_bound_count": bound if generated else None, "min": 5, "max": 8},
            **axes, "status_counts": {status: counts[status] for status in AXIS_STATUSES},
            "axes_complete": axes_complete, "has_missing_historical_text": bool(counts["missing_historical_text"]), "issues": issues}
