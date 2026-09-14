"""Named research-question signals; retrieval is distinct from reviewed proof."""
from __future__ import annotations

from collections import Counter

from catalog_rules import eligible_month, independent_clusters, research_eligible
from temporal_evidence import _linked_source, _source_map, cutoff_day, evidence_as_of, public_by


def add_months(month: str, delta: int) -> str:
    year, number = map(int, month.split("-"))
    index = year * 12 + number - 1 + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def reviewed_signal_evidence(work: dict, signal_id: str, cutoff: str, source_records=None) -> list[dict]:
    """Accept source-bound human-reviewed records, never bare legacy labels."""
    if work.get("research_status_notices"):
        from research_status import research_status_as_of
        if not research_status_as_of(work, cutoff, source_records)["validation_eligible"]:
            return []
    entries = work.get("signal_evidence", [])
    if isinstance(entries, dict):
        entries = entries.get(signal_id, [])
    if not isinstance(entries, list):
        entries = [entries]
    sources = _source_map(source_records) if source_records is not None else None
    result = {}
    for record in entries:
        if not isinstance(record, dict) or record.get("signal_id") != signal_id or record.get("work_id") != work.get("work_id"):
            continue
        if record.get("review_status") != "verified" or record.get("research_scope") != "in_scope" or record.get("stance") not in {"supports", "contradicts", "neutral"}:
            continue
        if not record.get("record_id") or not isinstance(record.get("statement"), str) or not record["statement"].strip() or not isinstance(record.get("experiment"), dict):
            continue
        experiment = record["experiment"]
        if not {"setting", "baseline", "metric", "limitations"} <= experiment.keys() or any(experiment[key] is not None and not isinstance(experiment[key], str) for key in ["setting", "baseline", "metric"]) or not isinstance(experiment["limitations"], list) or any(not isinstance(value, str) for value in experiment["limitations"]):
            continue
        if not _linked_source(record, work, sources) or not public_by(record.get("public_at"), cutoff, record.get("public_at_precision", record.get("date_precision"))):
            continue
        result[record["record_id"]] = record
    return [result[key] for key in sorted(result)]


def assess_signal(spec: dict, rows: list[dict], months: list[str], groups: dict, versions: dict,
                  *, as_of_month: str | None = None, evidence_cutoff: str | None = None, source_records=None) -> dict:
    if not months:
        raise ValueError("At least one complete analysis month is required")
    latest = as_of_month or months[-1]
    cohort_until = cutoff_day(latest).isoformat()
    until = cutoff_day(evidence_cutoff or latest).isoformat()
    if until < cohort_until:
        raise ValueError("Evidence cutoff cannot precede the complete analysis month")
    sources = _source_map(source_records) if source_records is not None else None
    months = [month for month in months if month <= latest]
    if not months or months[-1] != latest:
        raise ValueError("The as-of month must be present in the analysis window")
    eligible = [w for w in rows if research_eligible(w) and eligible_month(w, cohort_until)]
    visible = [w for w in eligible if public_by(w.get("first_public_date"), cohort_until, w.get("first_public_date_precision"))]
    proof = {w["work_id"]: reviewed_signal_evidence(w, spec["signal_id"], until, sources) for w in visible}
    selected = []
    for work in visible:
        text = (work["title"] + " " + (work.get("abstract") or "")).lower()
        lexical = any(term.lower() in text for term in spec["terms"]) and any(term.lower() in text for term in spec["required_terms"])
        if lexical or proof[work["work_id"]]:
            selected.append(work)
    # A future bridging paper must not change historical source clusters.
    clusters = independent_clusters(visible)
    two_months = {latest, add_months(latest, -1)}
    recent = [w for w in selected if eligible_month(w) in two_months]
    in_window = [w for w in selected if eligible_month(w) in months]
    temporal = {w["work_id"]: evidence_as_of(w, versions.get(w["work_id"], []), until, sources) for w in selected if eligible_month(w) in set(months) | two_months}
    supported = [w for w in in_window if any(r["stance"] == "supports" for r in proof[w["work_id"]])]
    contradicted = [w for w in in_window if any(r["stance"] == "contradicts" for r in proof[w["work_id"]])]
    recent_supported = [w for w in supported if eligible_month(w) in two_months]
    known_groups = {group for w in recent for group in groups.get(w["work_id"], [])}
    known_clusters = {clusters[w["work_id"]] for w in recent if w.get("authors") or groups.get(w["work_id"])}
    support_clusters = {clusters[w["work_id"]] for w in recent_supported if w.get("authors") or groups.get(w["work_id"])}
    all_support_clusters = {clusters[w["work_id"]] for w in supported if w.get("authors") or groups.get(w["work_id"])}
    evidence_groups = {g for w in supported for g in groups.get(w["work_id"], [])}
    peer_venues = {v["venue"] for w in supported for v in temporal[w["work_id"]]["peer_reviewed_manifestations"] if v.get("venue")}
    has_real = any(temporal[w["work_id"]]["evidence_flags"].get("real_robot") for w in supported)
    replication = any(temporal[w["work_id"]]["independent_replication_evidence_ids"] for w in supported)
    activation = any(any(temporal[w["work_id"]]["evidence_flags"].get(key) for key in ["real_robot", "open_code", "open_data", "open_model", "benchmark", "deployment"]) for w in recent_supported)
    consecutive = len(months) >= 3 and all(any(eligible_month(w) == month for w in supported) for month in months[-3:])
    lifecycle = "candidate"
    if len(recent_supported) >= 3 and len(support_clusters) >= 2 and activation:
        lifecycle = "emerging"
    if consecutive and len(evidence_groups) >= 3 and len(all_support_clusters) >= 2 and (peer_venues or replication):
        lifecycle = "consolidating"
    if len(evidence_groups) >= 2 and len(all_support_clusters) >= 2 and has_real and (len(peer_venues) >= 2 or replication):
        lifecycle = "established"
    totals = Counter(eligible_month(w) for w in visible)
    counts_by_month = Counter(eligible_month(w) for w in selected)
    counts = [counts_by_month[month] for month in months]
    shares = [count / totals[month] if totals[month] else 0 for month, count in zip(months, counts)]
    previous_clusters = {clusters[w["work_id"]] for w in selected if eligible_month(w) in months[-4:-1]}
    new_clusters = {clusters[w["work_id"]] for w in selected if eligible_month(w) == latest} - previous_clusters
    base = sum(shares[-4:-1]) / 3 if len(shares) >= 4 else None
    momentum = "stable"
    if base and shares[-1] >= 1.25 * base and len(new_clusters) >= 2:
        momentum = "rising"
    elif len(shares) >= 3 and shares[-3] > 0 and shares[-2] <= .75 * shares[-3] and shares[-1] <= .75 * shares[-2] and not any(temporal[w["work_id"]]["evidence_grade"] in {"E3", "E4"} for w in recent):
        momentum = "cooling"
    grade = lambda w: int(temporal[w["work_id"]]["evidence_grade"][1:])
    key = lambda w: (grade(w), bool(w.get("curated")), w.get("first_public_date") or "")
    evidence_records = [r for w in in_window for r in proof[w["work_id"]]]
    gaps = [] if supported else ["主题检索命中尚未逐篇确认是否支持该命题，不能据此声明能力成熟。"]
    if any(temporal[w["work_id"]]["information_gaps"] for w in supported):
        gaps.append("部分实验或开源标记缺少截至当月可用的带日期证据，未用于成熟度升级。")
    inactive = [w["work_id"] for w in in_window if temporal[w["work_id"]].get("validation_eligible") is False]
    if inactive:
        gaps.append("部分已登记研究在所选证据日期已撤回或撤稿；保留活动记录，但不将受影响的结果用于支持、反例或成熟度升级。")
    return {**spec, "id": spec["signal_id"], "trend_id": spec["signal_id"], "as_of_month": latest,
            "evidence_as_of": until,
            "temporal_basis": "retrospective_validation_of_fixed_cohort" if until > cohort_until else "public_evidence_by_as_of_month_end", "lifecycle": lifecycle,
            "lifecycle_basis": "human_reviewed_source_bound_support", "disputed": bool(supported and contradicted),
            "momentum": momentum, "topic_momentum": momentum, "momentum_basis": "retrieval_topic_share_not_verified_capability",
            "evidence_grade": "E" + str(max((grade(w) for w in supported), default=0)),
            "retrieval_evidence_grade": "E" + str(max((grade(w) for w in recent), default=0)),
            "months": months, "counts": counts, "shares": shares,
            "rolling_two_month_works": len(recent), "reviewed_support_count": len(supported), "recent_reviewed_support_count": len(recent_supported),
            "independent_clusters": len(known_clusters), "reviewed_support_clusters": len(support_clusters),
            "cluster_basis": "explicit_shared_origin_only_not_proof_of_independent_replication",
            "unknown_cluster_count": sum(not w.get("authors") and not groups.get(w["work_id"]) for w in recent),
            "organization_count": len(known_groups), "new_cluster_count": len(new_clusters),
            "candidate_work_ids": [w["work_id"] for w in sorted(recent, key=key, reverse=True)],
            "supporting_work_ids": [w["work_id"] for w in supported], "counterevidence_ids": [w["work_id"] for w in contradicted],
            "supporting_evidence_ids": [r["record_id"] for r in evidence_records if r["stance"] == "supports"],
            "inactive_evidence_work_ids": inactive,
            "counterevidence_record_ids": [r["record_id"] for r in evidence_records if r["stance"] == "contradicts"],
            "evidence_records": evidence_records, "assessment_status": "evidence_reviewed" if supported or contradicted else "retrieval_only",
            "summary": f"窗口最后两个月有 {len(recent)} 项相关研究；截至所选证据日期，窗口内 {len(supported)} 项有已审阅支持证据。话题热度不等于能力结论成立。",
            "information_gaps": gaps}
