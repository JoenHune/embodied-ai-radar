#!/usr/bin/env python3
"""Restore existing research editing with exact citations and full reconciliation.

This is a provenance-preserving import, not new LLM output, scientific validation,
or evidence-grade promotion. Historical comparisons and forecasts keep their dates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data/editorial/legacy"
LABEL = "历史研究编辑；新增自动摘要待生成"


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(body)
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_table(directory: Path, name: str) -> list[dict]:
    shards = sorted((directory / name).glob("*.jsonl"))
    paths = shards or [directory / f"{name}.jsonl"]
    rows = []
    for path in paths:
        if path.exists():
            with path.open() as stream:
                rows.extend(json.loads(line) for line in stream if line.strip())
    return rows


def arxiv_id(value: Any) -> str | None:
    text = str(value or "").strip()
    match = re.fullmatch(r"(?:(?:https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/)|arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?", text, re.I)
    return match.group(1) if match else None


class Resolver:
    def __init__(self, works: list[dict], aliases: list[dict], manifestations: list[dict]):
        self.works = {row["work_id"]: row for row in works}
        self.index = defaultdict(set)
        self.urls = defaultdict(set)
        for row in aliases:
            if row.get("work_id") in self.works and row.get("alias"):
                self.add(row["alias"], row["work_id"])
        for row in works:
            self.add(row["work_id"], row["work_id"])
            for alias in row.get("aliases", []):
                self.add(alias, row["work_id"])
            identifier = row.get("identifiers", {}).get("arxiv")
            if identifier:
                self.add(identifier, row["work_id"])
            for identifier in row.get("identifier_aliases", {}).get("arxiv", []):
                self.add(identifier, row["work_id"])
        for row in manifestations:
            if row.get("work_id") in self.works and row.get("url"):
                self.urls[row["work_id"]].add(row["url"])

    def add(self, alias: str, work_id: str) -> None:
        self.index[alias].add(work_id)
        identifier = arxiv_id(alias)
        if identifier:
            self.index[identifier].add(work_id)
            self.index["arxiv:" + identifier].add(work_id)

    def resolve(self, legacy_id: str, month: str | None = None) -> dict:
        identifier = arxiv_id(legacy_id)
        candidates = set(self.index.get(legacy_id, set()))
        if identifier:
            candidates.update(self.index.get(identifier, set()))
        row = {"legacy_id": legacy_id, "arxiv_id": identifier,
               "work_id": None, "mapping_status": "unresolved", "candidate_work_ids": sorted(candidates),
               "canonical_relevance": None, "classification_state": None, "first_public_date": None,
               "temporal_role": "unknown", "directions": [], "questions": [],
               "source_urls": [f"https://arxiv.org/abs/{identifier}"] if identifier else []}
        if len(candidates) > 1:
            row["mapping_status"] = "ambiguous"
        elif len(candidates) == 1:
            work_id = next(iter(candidates))
            work = self.works[work_id]
            date = work.get("first_public_date")
            evidence_month = date[:7] if date and work.get("first_public_date_precision") not in {"year", "unknown"} else None
            role = "unknown" if not month or not evidence_month else "current_month" if evidence_month == month else "historical_context" if evidence_month < month else "future_evidence"
            row.update(work_id=work_id, mapping_status="exact", canonical_relevance=work.get("relevance", {}).get("status"),
                       classification_state=work.get("classification_state"), first_public_date=date, temporal_role=role,
                       title=work.get("title"), directions=work.get("directions", []), questions=work.get("questions", []),
                       source_urls=sorted(set(row["source_urls"]) | self.urls[work_id]))
        row["review_reasons"] = []
        if row["mapping_status"] != "exact":
            row["review_reasons"].append("canonical_id_" + row["mapping_status"])
        if row["canonical_relevance"] != "included":
            row["review_reasons"].append("canonical_relevance_" + str(row["canonical_relevance"] or "unknown"))
        if row["classification_state"] in {"review_required", "low_confidence", "manual_review", "low_confidence_review", "missing_primary_review"}:
            row["review_reasons"].append("classification_review_required")
        if role := row["temporal_role"]:
            if role == "future_evidence":
                row["review_reasons"].append("evidence_postdates_editorial_month")
        if not row["source_urls"]:
            row["review_reasons"].append("direct_source_missing")
        return row


def original_source(path: str, pointer: str, raw: Any) -> dict:
    return {"path": path, "json_pointer": pointer, "record_sha256": digest(raw)}


def link_fields(ids: list[str], resolver: Resolver, month: str | None) -> dict:
    references = [resolver.resolve(str(value), month) for value in ids]
    mapped = list(dict.fromkeys(row["work_id"] for row in references if row["work_id"]))
    review = any(row["review_reasons"] for row in references) or not references
    return {"supporting_ids": mapped, "counterevidence_ids": [], "references": references,
            "directions": sorted({code for row in references for code in row["directions"]}),
            "questions": sorted({code for row in references for code in row["questions"]}),
            "direction_assignment": "canonical_evidence_union",
            "evidence_review_required": review, "unresolved_legacy_ids": [row["legacy_id"] for row in references if row["work_id"] is None],
            "review_required_work_ids": list(dict.fromkeys(row["work_id"] for row in references if row["work_id"] and row["review_reasons"])),
            "source_urls": sorted({url for row in references for url in row["source_urls"]}),
            "semantic_verification_status": "historical_editorial_not_reaudited"}


def restore(trends: dict, papers: list[dict], directions: dict, forecasts: dict,
            resolver: Resolver, active_months: list[str], provisional_month: str | None, output: Path) -> dict:
    monthly = {}
    def month_record(month):
        if month not in monthly:
            monthly[month] = {"schema_version": "3", "month": month, "status": "legacy_editorial", "label": LABEL,
                              "in_active_window": month in active_months or month == provisional_month,
                              "claims": [], "work_notes": [], "historical_watchlist": [],
                              "limitations": ["历史趋势等级与预测置信度沿用旧编辑口径，未转换为新版证据成熟度。",
                                              "历史比较和实验数字保留原文，未作为当前统计值重新计算。"]}
        return monthly[month]
    reconciliation = []
    for month, cards in sorted(trends.get("months", {}).items()):
        for index, raw in enumerate(cards):
            claim_id = f"claim:legacy:{month}:{digest([raw.get('title'), index])[:12]}"
            claim = {"claim_id": claim_id, "month": month, "title": raw.get("title", ""), "summary": raw.get("change", ""),
                     "status": "legacy_editorial", "generator": "legacy_editorial_import", "original_source": original_source("data/trends.json", f"/months/{month}/{index}", raw),
                     **link_fields(raw.get("evidence_ids", []), resolver, month),
                     "comparison": raw.get("comparison", ""), "maturity": raw.get("maturity", ""),
                     "bottleneck": raw.get("bottleneck", ""), "implication": raw.get("implication", ""),
                     "legacy_grade": raw.get("grade"), "legacy_kind": raw.get("kind"),
                     "historical_statistic_review_required": bool(re.search(r"[0-9].*(%|％|环比|同比)|(?:环比|同比).*[0-9]", raw.get("comparison", ""))),
                     "original_record": raw}
            # A legacy bottleneck is a limitation, not an independent counterexample.
            if raw.get("counterevidence_ids"):
                counter = link_fields(raw["counterevidence_ids"], resolver, month)
                claim["counterevidence_ids"] = counter["supporting_ids"]
                claim["counterevidence_references"] = counter["references"]
                claim["evidence_review_required"] |= counter["evidence_review_required"]
            month_record(month)["claims"].append(claim)
            reconciliation.append({"claim_id": claim_id, "month": month, "title": claim["title"],
                                   "original_source": claim["original_source"], "legacy_evidence_count": len(raw.get("evidence_ids", [])),
                                   "canonical_evidence_count": len(claim["supporting_ids"]), "unresolved_legacy_ids": claim["unresolved_legacy_ids"],
                                   "evidence_review_required": claim["evidence_review_required"], "in_active_window": month in active_months,
                                   "disposition": "restored_active_month" if month in active_months else "restored_archive_outside_default_window",
                                   "output_path": f"data/editorial/legacy/{month}.json"})
    work_notes = []
    for index, raw in enumerate(papers):
        if not (raw.get("contribution_zh") or raw.get("limitation_zh") or raw.get("selection_reason_zh")):
            continue
        month = raw.get("v1_month") or str(raw.get("first_submitted") or "")[:7] or None
        links = link_fields([raw["id"]], resolver, month)
        note = {"note_id": "note:legacy:" + str(raw["id"]), "work_id": links["supporting_ids"][0] if links["supporting_ids"] else None,
                "legacy_id": raw["id"], "title": raw.get("title", ""), "month": month, "status": "legacy_editorial",
                "contribution_zh": raw.get("contribution_zh", ""), "limitation_zh": raw.get("limitation_zh", ""),
                "selection_reason_zh": raw.get("selection_reason_zh", ""),
                "original_source": original_source("data/papers.json", f"/{index}", raw), **links}
        work_notes.append(note)
        if month:
            month_record(month)["work_notes"].append(note)
    context = {"schema_version": "3", "status": "legacy_editorial", "direction_context": [], "forecasts": []}
    for key, raw in sorted(directions.items()):
        context["direction_context"].append({"context_id": "context:legacy:direction:" + key, "legacy_topic": key,
            "title": raw.get("label", key), "status": "legacy_editorial_context", "as_of": None,
            "monthly_use": "background_only_not_monthly_observation", "original_source": original_source("data/directions.json", "/" + key, raw),
            **link_fields(raw.get("representative_ids", []), resolver, None), "original_record": raw})
    forecast_month = str(forecasts.get("as_of") or "")[:7] or None
    for index, raw in enumerate(forecasts.get("signals", [])):
        item = {"forecast_id": "forecast:legacy:" + digest([raw.get("title"), index])[:12], "title": raw.get("title", ""),
                "summary": raw.get("judgment", ""), "observed": raw.get("observed", ""), "confirm": raw.get("confirm", ""),
                "falsifier": raw.get("falsifier", ""), "horizon": raw.get("horizon", ""), "strategic": raw.get("strategic", ""),
                "legacy_confidence": raw.get("confidence"), "status": "legacy_forecast", "as_of": forecasts.get("as_of"),
                "outcome_verified": False, "monthly_use": "historical_watchlist_only",
                "original_source": original_source("data/forecasts.json", f"/signals/{index}", raw),
                **link_fields(raw.get("evidence_ids", []), resolver, forecast_month), "original_record": raw}
        context["forecasts"].append(item)
        if forecast_month:
            month_record(forecast_month)["historical_watchlist"].append(item)
    for month in active_months + ([provisional_month] if provisional_month else []):
        month_record(month)
    for month, value in sorted(monthly.items()):
        value["source_digest"] = digest({key: value[key] for key in ("claims", "work_notes", "historical_watchlist")})
        write_json(output / f"{month}.json", value)
    atomic_text(output / "work-notes.jsonl", "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in sorted(work_notes, key=lambda row: row["note_id"])))
    write_json(output / "context.json", context)
    references = [reference for month in monthly.values() for claim in month["claims"] for reference in claim["references"]]
    review_reasons = Counter(reason for reference in references for reason in reference["review_reasons"])
    report = {"schema_version": "3", "status": "reconciled", "label": LABEL,
              "active_complete_months": active_months, "provisional_month": provisional_month,
              "source_counts": {"trend_cards": sum(len(rows) for rows in trends.get("months", {}).values()),
                                "paper_editorial_notes": sum(bool(row.get("contribution_zh") or row.get("limitation_zh") or row.get("selection_reason_zh")) for row in papers),
                                "direction_context": len(directions), "forecasts": len(forecasts.get("signals", []))},
              "restored_counts": {"trend_cards": len(reconciliation), "active_window_trend_cards": sum(row["in_active_window"] for row in reconciliation),
                                  "paper_editorial_notes": len(work_notes), "direction_context": len(context["direction_context"]), "forecasts": len(context["forecasts"])},
              "trend_cards_requiring_evidence_review": sum(row["evidence_review_required"] for row in reconciliation),
              "paper_notes_requiring_evidence_review": sum(row["evidence_review_required"] for row in work_notes),
              "mapping_counts": dict(sorted(Counter(row["mapping_status"] for row in references).items())),
              "relevance_counts": dict(sorted(Counter(str(row["canonical_relevance"]) for row in references).items())),
              "review_reasons": dict(sorted(review_reasons.items())), "cards": reconciliation,
              "output_months": sorted(monthly), "scientific_judgments_reaudited": False,
              "context_assessment": {"directions": "Five legacy categories contain useful definitions, route comparisons and limitations; use as dated background only, not D1–D15 monthly statistics.",
                                     "forecasts": "All existing forecasts retain observed evidence, confirmation milestones and falsifiers; use only in the as-of month watchlist without claiming outcomes occurred."}}
    if report["source_counts"]["trend_cards"] != report["restored_counts"]["trend_cards"] or report["source_counts"]["paper_editorial_notes"] != len(work_notes):
        raise ValueError("Legacy editorial reconciliation failed")
    write_json(output / "reconciliation.json", report)
    write_json(output / "manifest.json", {"schema_version": "3", "months": sorted(monthly), "source_counts": report["source_counts"],
                                          "status": "legacy_editorial", "source_digest": digest([trends, papers, directions, forecasts])})
    counts = report["source_counts"]
    audit = f"""# 内容恢复审校报告

> 审校对象：旧趋势卡、论文中文贡献/局限、方向综述、预测。
> 审校依据：仓库原始 JSON、canonical work 与精确 arXiv/alias 映射。
> 审校范围：数据一致性、来源归属、内容遗漏、重复导入；不宣称重新验证全文实验或未来预测。

## 一、已直接修改的问题

未修改原始科学判断。修复的是迁移中的内容遗漏，并为旧 ID 添加 canonical work 映射及待复核标识。

## 二、文章正确修正了原始转录错误的地方

本任务不包含转录或 ASR 修正，不适用。

## 三、待确认的专有名词与证据

🟡 {report['trend_cards_requiring_evidence_review']} 张趋势卡和 {report['paper_notes_requiring_evidence_review']} 篇中文论文笔记的引用仍需相关性、分类或身份核验。原文保留，未把待复核工作升级为已纳入。逐条原因见 reconciliation.json 与各月 references。

## 四、事实与数据核查

### 4.1 已验证一致的关键数据

| 内容 | 原始条数 | 恢复条数 |
|---|---:|---:|
| 趋势卡 | {counts['trend_cards']} | {report['restored_counts']['trend_cards']} |
| 中文贡献、局限与入选理由 | {counts['paper_editorial_notes']} | {report['restored_counts']['paper_editorial_notes']} |
| 跨期方向综述 | {counts['direction_context']} | {report['restored_counts']['direction_context']} |
| 历史预测 | {counts['forecasts']} | {report['restored_counts']['forecasts']} |

当前默认窗口包含 {report['restored_counts']['active_window_trend_cards']} 张旧趋势卡；窗口外内容另存月度归档，没有删除。原始记录摘要哈希用于逐条对账，重复导入保持幂等。

### 4.2 有微调但可接受的表述

只添加“{LABEL}”等来源标识，未风格改写正文，也未把旧 A/B/C/D 等级映射成新的成熟度。

### 4.3 时效性数据备注

历史统计比较没有重新计算，应与当前数据库统计并列说明。预测只在原 as_of 月份作为观察清单出现，保留确认路标与反证条件，outcome_verified 为 false。

## 五、人名与身份核查

没有推断或修改作者、公司、课题组身份；work 映射只用精确 ID，不使用标题相似度或当前雇主反推。

## 六、技术名词一致性

旧五类方向保留在背景综述。月度卡片的 D/Q 覆盖来自关联 canonical evidence 的并集，并明确标注映射来源，不将旧标签冒充新分类。

## 七、审校结论

已完成原文恢复、全部记录对账和待复核分层；科学内容仍属于历史编辑。方向综述适合作为路线背景，预测适合作为有日期的后续验证清单，二者均不计作当月新增研究或已确认趋势。
"""
    atomic_text(output / "content-audit.md", audit)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", type=Path, default=ROOT / "data")
    parser.add_argument("--catalog-directory", type=Path, default=ROOT / "data/catalog")
    parser.add_argument("--api-directory", type=Path, default=ROOT / "docs/public/api/v1")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    values = {name: json.loads((args.data_directory / f"{name}.json").read_text()) for name in ("trends", "papers", "directions", "forecasts")}
    manifest = json.loads((args.api_directory / "catalog-manifest.json").read_text())
    resolver = Resolver(read_table(args.catalog_directory, "works"), read_table(args.catalog_directory, "work-aliases"), read_table(args.catalog_directory, "manifestations"))
    report = restore(values["trends"], values["papers"], values["directions"], values["forecasts"], resolver,
                     manifest["complete_months"][-12:], manifest.get("provisional_month"), args.output_directory)
    print(json.dumps({key: report[key] for key in ("status", "source_counts", "restored_counts", "trend_cards_requiring_evidence_review", "review_reasons")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
