#!/usr/bin/env python3
"""Aggregate X Post metadata into a weekly embodied-AI discussion radar."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "x-discussion-radar.json"
ORGANIZATIONS = ROOT / "config" / "organizations.json"
DEFAULT_STORE = ROOT / "data" / "x-discussion-posts.json"
DEFAULT_WEEKLY = ROOT / "data" / "x-weekly-discussions.json"
DEFAULT_DOCS = ROOT / "docs"
LOOKUP_API = "https://api.x.com/2/tweets"
USER_AGENT = "embodied-ai-x-discussion-radar/1.0"


def read(path: Path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def parse_time(value: str | None) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def week_bounds(week_id: str | None, zone: ZoneInfo) -> tuple[str, datetime, datetime, date, date]:
    if week_id:
        match = re.fullmatch(r"(\d{4})-W(\d{2})", week_id)
        if not match:
            raise SystemExit("week must use YYYY-Www")
        monday = date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)
    else:
        local_today = datetime.now(zone).date()
        current_monday = local_today - timedelta(days=local_today.weekday())
        monday = current_monday - timedelta(days=7)
        iso_year, iso_week, _ = monday.isocalendar()
        week_id = f"{iso_year}-W{iso_week:02d}"
    next_monday = monday + timedelta(days=7)
    start = datetime.combine(monday, time.min, zone).astimezone(timezone.utc)
    end = datetime.combine(next_monday, time.min, zone).astimezone(timezone.utc)
    return week_id, start, end, monday, next_monday - timedelta(days=1)


def api_get(url: str, token: str, timeout: int = 45) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"X API HTTP {exc.code}: {detail[:500]}") from exc


def normalized_metrics(value: dict | None) -> dict:
    value = value or {}
    return {
        "like_count": int(value.get("like_count") or 0),
        "retweet_count": int(value.get("retweet_count") or 0),
        "reply_count": int(value.get("reply_count") or 0),
        "quote_count": int(value.get("quote_count") or 0),
        "bookmark_count": int(value.get("bookmark_count") or 0),
        "impression_count": int(value.get("impression_count") or 0),
    }


def verify_live_posts(posts: list[dict], token: str, config: dict) -> None:
    by_id = {row["post_id"]: row for row in posts}
    ids = list(by_id)
    for offset in range(0, len(ids), 100):
        batch = ids[offset:offset + 100]
        params = {
            "ids": ",".join(batch),
            "tweet.fields": "id,public_metrics,author_id,created_at",
            "expansions": "author_id",
            "user.fields": "id,username,verified,public_metrics",
        }
        payload = api_get(f"{LOOKUP_API}?{urllib.parse.urlencode(params)}", token, int(config["source"]["request_timeout_seconds"]))
        users = {str(row["id"]): row for row in (payload.get("includes") or {}).get("users", [])}
        returned = set()
        for item in payload.get("data") or []:
            post_id = str(item["id"])
            returned.add(post_id)
            row = by_id[post_id]
            row["metrics"] = normalized_metrics(item.get("public_metrics"))
            row["compliance_status"] = "live"
            author = users.get(str(item.get("author_id")), {})
            if author:
                row["author_username"] = author.get("username")
                row["author_verified"] = bool(author.get("verified"))
                row["author_followers"] = int((author.get("public_metrics") or {}).get("followers_count") or 0)
            row["last_seen_at"] = iso_utc(datetime.now(timezone.utc))
        error_by_id = {str(item.get("resource_id")): item for item in payload.get("errors") or []}
        for post_id in set(batch) - returned:
            detail = str(error_by_id.get(post_id, {})).casefold()
            status = "protected" if "protected" in detail else "suspended" if "suspend" in detail else "deleted"
            by_id[post_id]["compliance_status"] = status


def weighted_engagement(post: dict, weights: dict) -> float:
    metrics = post.get("metrics") or {}
    return (
        weights["likes"] * metrics.get("like_count", 0)
        + weights["reposts"] * metrics.get("retweet_count", 0)
        + weights["quotes"] * metrics.get("quote_count", 0)
        + weights["replies"] * metrics.get("reply_count", 0)
        + weights["bookmarks"] * metrics.get("bookmark_count", 0)
    )


def cluster_key(post: dict) -> str:
    if post.get("artifact_key"):
        return post["artifact_key"]
    topic = post.get("primary_topic_code") or (post.get("topic_codes") or ["T1"])[0]
    if post.get("entity_ids"):
        return f"entity:{post['entity_ids'][0]}:{topic}"
    return f"topic:{topic}"


def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).replace("|", "\\|").strip()


def topic_label(key: str, posts: list[dict], topic_map: dict, organization_map: dict) -> str:
    topic_code = Counter(post.get("primary_topic_code") for post in posts if post.get("primary_topic_code")).most_common(1)
    base = topic_map.get(topic_code[0][0], {}).get("label_zh", topic_code[0][0]) if topic_code else "具身智能讨论"
    if key.startswith("arxiv:"):
        return f"arXiv {key.removeprefix('arxiv:')} · {base}"
    if key.startswith("github:"):
        return f"GitHub {key.removeprefix('github:')} · {base}"
    if key.startswith("huggingface:"):
        return f"Hugging Face {key.removeprefix('huggingface:')} · {base}"
    if key.startswith("openreview:"):
        return f"OpenReview 工作 · {base}"
    if key.startswith("entity:"):
        organization_id = key.removeprefix("entity:").rsplit(":", 1)[0]
        return f"{organization_map.get(organization_id, organization_id)} · {base}"
    return base


def aggregate_cluster(key: str, rows: list[dict], baseline_rows: list[dict], config: dict, topic_map: dict, organization_map: dict) -> dict:
    weights = config["score_weights"]
    authors = Counter(row["author_id"] for row in rows)
    engagement = sum(weighted_engagement(row, weights) for row in rows)
    normalized_engagement = sum(weighted_engagement(row, weights) / math.sqrt(max(int(row.get("author_followers") or 0), 100)) for row in rows)
    baseline_signal = sum(weighted_engagement(row, weights) + 5 for row in baseline_rows) / 4
    current_signal = engagement + 5 * len(rows)
    momentum = max(0.5, min(5.0, (current_signal + 1) / (baseline_signal + 1)))
    max_share = max(authors.values()) / len(rows)
    raw_score = (
        weights["post_volume"] * math.log1p(len(rows))
        + weights["author_breadth"] * math.log1p(len(authors))
        + weights["engagement"] * (
            (1 - weights["audience_normalization"]) * math.log1p(engagement)
            + weights["audience_normalization"] * math.log1p(100 * normalized_engagement)
        )
        + weights["momentum"] * math.log1p(momentum)
    )
    if max_share > config["quality_rules"]["maximum_single_author_share"]:
        raw_score *= 0.75
    metrics = Counter()
    for row in rows:
        metrics.update(row.get("metrics") or {})
    lane = Counter(row.get("content_kind", "discussion") for row in rows).most_common(1)[0][0]
    if lane == "artifact":
        lane = "research"
    controversy = (metrics["reply_count"] + metrics["quote_count"]) / (metrics["like_count"] + metrics["retweet_count"] + 1)
    representative = sorted(rows, key=lambda row: weighted_engagement(row, weights), reverse=True)[:config["publication"]["representative_posts_per_topic"]]
    topic_codes = sorted({code for row in rows for code in row.get("topic_codes", [])})
    direction_codes = sorted({code for row in rows for code in row.get("direction_codes", [])}, key=lambda code: int(code[1:]))
    entity_ids = sorted({value for row in rows for value in row.get("entity_ids", [])})
    urls = list(dict.fromkeys(value for row in rows for value in row.get("canonical_urls", [])))
    return {
        "cluster_key": key,
        "label_zh": topic_label(key, rows, topic_map, organization_map),
        "lane": lane,
        "raw_score": raw_score,
        "heat_score": 0,
        "momentum": round(momentum, 2),
        "post_count": len(rows),
        "unique_authors": len(authors),
        "single_author_share": round(max_share, 3),
        "weighted_engagement": round(engagement, 2),
        "audience_normalized_engagement": round(normalized_engagement, 4),
        "controversy_ratio": round(controversy, 3),
        "metrics": dict(metrics),
        "topic_codes": topic_codes,
        "direction_codes": direction_codes,
        "entity_ids": entity_ids,
        "canonical_urls": urls[:5],
        "representative_posts": [{
            "post_id": row["post_id"],
            "url": f"https://x.com/i/web/status/{row['post_id']}",
            "author_username": row.get("author_username"),
            "metrics": row.get("metrics"),
        } for row in representative],
    }


def build_week(posts: list[dict], week_id: str, start: datetime, end: datetime, local_from: date, local_until: date, config: dict, organizations: dict, verified: bool) -> dict:
    topic_map = {row["code"]: row for row in config["topics"]}
    organization_map = {row["organization_id"]: row["display_name"] for row in organizations.get("organizations", [])}
    eligible = [row for row in posts if start <= parse_time(row["created_at"]) < end and row.get("compliance_status") in {"live", "unverified"}]
    baseline_start = start - timedelta(days=28)
    baseline = [row for row in posts if baseline_start <= parse_time(row["created_at"]) < start and row.get("compliance_status") in {"live", "unverified"}]
    grouped = defaultdict(list)
    baseline_grouped = defaultdict(list)
    for row in eligible:
        grouped[cluster_key(row)].append(row)
    for row in baseline:
        baseline_grouped[cluster_key(row)].append(row)
    clusters = [aggregate_cluster(key, rows, baseline_grouped.get(key, []), config, topic_map, organization_map) for key, rows in grouped.items()]
    max_raw = max((row["raw_score"] for row in clusters), default=0)
    for row in clusters:
        row["heat_score"] = round(100 * row.pop("raw_score") / max_raw, 1) if max_raw else 0
        row["rank_reason_zh"] = f"{row['post_count']} 项讨论、{row['unique_authors']} 位作者、加权互动 {row['weighted_engagement']:.0f}，较近四周基线 {row['momentum']:.1f}×"
    clusters.sort(key=lambda row: (row["heat_score"], row["unique_authors"], row["post_count"]), reverse=True)
    minimum_posts = config["publication"]["minimum_posts"]
    minimum_authors = config["publication"]["minimum_unique_authors"]
    ranked = [row for row in clusters if row["post_count"] >= minimum_posts and row["unique_authors"] >= minimum_authors]
    emerging = [row for row in clusters if row not in ranked and row["cluster_key"].startswith(("arxiv:", "openreview:", "github:", "huggingface:"))]
    top_n = config["publication"]["top_topics"]
    lanes = {lane: [row for row in ranked if row["lane"] == lane][:top_n] for lane in ("research", "startup", "discussion")}
    controversial = sorted(ranked, key=lambda row: row["controversy_ratio"], reverse=True)[:5]
    status = "ready" if verified else "unverified_metrics" if eligible else "awaiting_first_poll"
    return {
        "week_id": week_id,
        "from": local_from.isoformat(),
        "until": local_until.isoformat(),
        "timezone": config["timezone"],
        "status": status,
        "metrics_verified_before_publish": verified,
        "post_count": len(eligible),
        "unique_authors": len({row["author_id"] for row in eligible}),
        "ranked_topic_count": len(ranked),
        "top_topics": ranked[:top_n],
        "top_by_lane": lanes,
        "controversial_topics": controversial,
        "emerging_signals": emerging[:8],
        "unavailable_post_count": len([row for row in posts if start <= parse_time(row["created_at"]) < end and row.get("compliance_status") not in {"live", "unverified"}]),
    }


def topic_rows(rows: list[dict]) -> str:
    if not rows:
        return "| — | 本周尚无达到门槛的讨论簇 | — | — | — | — |"
    result = []
    for index, row in enumerate(rows, 1):
        sources = "、".join(f"[Post {offset + 1}]({item['url']})" for offset, item in enumerate(row["representative_posts"])) or "—"
        result.append(f"| {index} | {clean(row['label_zh'])} | {row['heat_score']:.1f} | {row['post_count']} / {row['unique_authors']} | {row['momentum']:.1f}× | {sources} |")
    return "\n".join(result)


def write_docs(week: dict, docs: Path, generated_at: str, config: dict) -> None:
    social = docs / "social"
    weekly = social / "weekly"
    weekly.mkdir(parents=True, exist_ok=True)
    week_slug = week["week_id"].lower()
    status_note = {
        "ready": "代表 Post 已在发布前重新查询，公开互动指标已刷新。",
        "unverified_metrics": "当前为 dry-run 或未配置凭据；指标未在发布前重新核验。",
        "awaiting_first_poll": "尚未配置 X_BEARER_TOKEN 或完成首次增量采集，页面先展示方法与空状态。",
    }[week["status"]]
    lanes = [("research", "研究、论文与开源"), ("startup", "初创与公司发布"), ("discussion", "方法与行业话题")]
    lane_sections = "\n\n".join(f"## {label}\n\n| # | 讨论簇 | 热度 | Post / 作者 | 动量 | 代表链接 |\n|---:|---|---:|---:|---:|---|\n{topic_rows(week['top_by_lane'][key])}" for key, label in lanes)
    emerging = "\n".join(f"- **{clean(row['label_zh'])}**：{clean(row['rank_reason_zh'])}；" + "、".join(f"[Post]({item['url']})" for item in row["representative_posts"]) for row in week["emerging_signals"]) or "- 无。"
    page = f"""---
outline: deep
---

# 具身智能 X 讨论周报 · {week['week_id']}

> 覆盖 {week['from']}—{week['until']}（Asia/Shanghai） · {week['post_count']} 项相关 Post · {week['unique_authors']} 位独立作者 · 生成于 {generated_at}

::: warning 解读边界
X 热度衡量“这周被讨论多少”，不衡量研究质量、技术真实性或投资价值。同行评审、公司技术报告、Demo 和普通讨论始终分栏。{status_note}
:::

## 本周总榜

| # | 讨论簇 | 热度 | Post / 作者 | 动量 | 代表链接 |
|---:|---|---:|---:|---:|---|
{topic_rows(week['top_topics'])}

{lane_sections}

## 新兴但未达广度门槛的信号

> 单一作者或只有一条 Post 的新论文/项目不进入热度总榜，但保留在这里防止错过早期信号。

{emerging}

## 口径

- 热度同时考虑 Post 数、独立作者、加权互动和较近四周基线的动量。
- 转发被排除，回复被保留；单一作者占比过高会降权。
- 不在仓库保存 Post 全文，只保存 ID、公开指标、外部链接和雷达派生标签。
- [查看完整方法](/social/method)
"""
    (weekly / f"{week_slug}.md").write_text(page)
    (weekly / "index.md").write_text(f"""---
outline: deep
---

# X 讨论历史周报

- [{week['week_id']} · {week['from']}—{week['until']}](/social/weekly/{week_slug})：{week['post_count']} 项 Post，{week['ranked_topic_count']} 个达到门槛的讨论簇。
""")
    (social / "index.md").write_text(f"""---
outline: deep
---

# 具身智能 X 讨论雷达

> 每 6 小时用 X API Recent Search 做重叠增量采集，周一生成过去一个完整自然周的话题榜。当前状态：**{week['status']}**。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>{week['post_count']}</strong><span>本周相关 Post</span></div>
  <div class="radar-kpi"><strong>{week['unique_authors']}</strong><span>独立作者</span></div>
  <div class="radar-kpi"><strong>{week['ranked_topic_count']}</strong><span>达门槛讨论簇</span></div>
  <div class="radar-kpi"><strong>{len(config['query_packs'])}</strong><span>检索 query packs</span></div>
</div>

## 最新周报

- [{week['week_id']} · {week['from']}—{week['until']}](/social/weekly/{week_slug})
- [历史周报](/social/weekly/)
- [检索、去噪与热度方法](/social/method)

## 读法

1. 先看“本周总榜”判断社区注意力。
2. 再分别看研究、初创和普通话题，避免公司宣传量压过论文讨论。
3. 最后回到论文、技术报告和研究组档案判断证据强度。
""")
    method = f"""---
outline: deep
---

# X 讨论雷达方法

## 数据流

```mermaid
flowchart LR
    A["8 组检索词<br/>Recent Search"] --> B["6 小时重叠采集<br/>按 Post ID 去重"]
    B --> C["论文 URL / 研究组 / D1–D15<br/>规则归一"]
    C --> D["去转发、去广告、单一作者降权"]
    D --> E["Post 数 + 作者广度<br/>互动 + 4 周动量"]
    E --> F["研究 / 初创 / 话题分栏周报"]
```

## 为什么不在周一一次性回查

[X Recent Search](https://docs.x.com/x-api/posts/search/introduction) 只覆盖最近 7 天。如果周一凌晨才回查，上周周一早期数据可能已滑出窗口；因此采用 6 小时轮询和 12 小时重叠窗口。

## 检索层

| Query pack | 用途 | D 映射 |
|---|---|---|
""" + "\n".join(f"| `{row['id']}` | {clean(row['label_zh'])} | {', '.join(row['direction_codes']) or '—'} |" for row in config["query_packs"]) + f"""

## 热度分数

Post 互动采用加权和：

$$E = likes + 2\\,reposts + 2.5\\,quotes + 1.5\\,replies + 0.25\\,bookmarks$$

话题层同时使用四个维度：Post 数、独立作者数、$E$ 和相对近四周基线的动量。互动项有 30% 按作者 followers 的平方根归一，减少大账号对榜单的单点支配；各项再做 $\\log(1+x)$ 压缩，并按周内最强话题归一为 0–100。

## 强制边界

- 排除纯转发，保留回复和 Quote，因为它们代表真正讨论。
- 进榜至少需要 {config['publication']['minimum_posts']} 项 Post 与 {config['publication']['minimum_unique_authors']} 位作者；单条新论文放入“新兴信号”。
- 公司 Demo、融资和招聘可以成为热门话题，但不会被表述为研究证据。
- 不使用 X 网页 HTML 抓取；采集只通过官方 API。
- 发布前重新 lookup 代表 Post，删除已删除、转私密或暂停账号的内容。参见 [X Batch Compliance](https://docs.x.com/x-api/compliance/batch-compliance/introduction)。

## 成本与限额

X API 使用[按量计费](https://docs.x.com/x-api/getting-started/pricing)，频率限制与账单互相独立。流程会记录每次请求和返回 Post 数，但不在代码中硬编码价格；实际单价以 Developer Console 为准。

## 数据最小化

仓库仅保存 Post ID、author ID、公开互动指标、规范外部 URL、内容指纹和雷达派生标签；不保存 Post 全文。与 X 上删除、转保护或暂停状态不一致的内容，需在 24 小时内从公开页面移除。
"""
    (social / "method.md").write_text(method)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--output-data", type=Path, default=DEFAULT_WEEKLY)
    parser.add_argument("--docs-root", type=Path, default=DEFAULT_DOCS)
    parser.add_argument("--verify-live", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = read(CONFIG, {})
    organizations = read(ORGANIZATIONS, {"organizations": []})
    zone = ZoneInfo(config["timezone"])
    week_id, start, end, local_from, local_until = week_bounds(args.week, zone)
    store = read(args.store, {"version": "1.0", "updated_at": None, "source": "x_api_v2", "posts": []})
    posts = store.get("posts", [])
    token = os.getenv("X_BEARER_TOKEN")
    verified = bool(store.get("last_compliance_check_at") and parse_time(store["last_compliance_check_at"]) >= end)
    if args.verify_live and posts:
        if not token:
            raise SystemExit("X_BEARER_TOKEN is required for --verify-live")
        candidates = [row for row in posts if start <= parse_time(row["created_at"]) < end]
        verify_live_posts(candidates, token, config)
        verified = True
        store["updated_at"] = iso_utc(datetime.now(timezone.utc))
        store["last_compliance_check_at"] = store["updated_at"]
        args.store.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n")
    week = build_week(posts, week_id, start, end, local_from, local_until, config, organizations, verified)
    generated_at = datetime.now(zone).date().isoformat()
    weekly = read(args.output_data, {"version": "1.0", "generated_at": generated_at, "status": "awaiting_first_poll", "latest_week": None, "weeks": []})
    by_week = {row["week_id"]: row for row in weekly.get("weeks", [])}
    by_week[week_id] = week
    weekly.update({"version": "1.0", "generated_at": generated_at, "status": week["status"], "latest_week": week_id, "weeks": sorted(by_week.values(), key=lambda row: row["week_id"], reverse=True)})
    if args.dry_run:
        print(json.dumps(week, ensure_ascii=False, indent=2))
        return
    args.output_data.parent.mkdir(parents=True, exist_ok=True)
    args.output_data.write_text(json.dumps(weekly, ensure_ascii=False, indent=2) + "\n")
    write_docs(week, args.docs_root, generated_at, config)
    public = args.docs_root / "public" / "x-weekly-discussions.json"
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(weekly, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"week": week_id, "status": week["status"], "posts": week["post_count"], "topics": week["ranked_topic_count"], "page": str(args.docs_root / "social" / "weekly" / f"{week_id.lower()}.md")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
