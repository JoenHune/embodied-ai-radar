#!/usr/bin/env python3
"""Collect embodied-AI discussions from X Recent Search without persisting Post text.

The collector is designed for a six-hour GitHub Actions poll.  It stores only
Post/user IDs, public metrics, canonical external links and radar-derived
labels.  Full Post text is used in memory for classification and immediately
discarded.  Overlapping polls are deduplicated by Post ID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "x-discussion-radar.json"
DEFAULT_STORE = ROOT / "data" / "x-discussion-posts.json"
API = "https://api.x.com/2/tweets/search/recent"
USER_AGENT = "embodied-ai-x-discussion-radar/1.0"
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})", re.I)


def read(path: Path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None, fallback: datetime) -> datetime:
    if not value:
        return fallback
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def canonical_url(value: str, allowed_domains: set[str]) -> str | None:
    try:
        parts = urllib.parse.urlsplit(value)
    except ValueError:
        return None
    host = parts.netloc.lower().removeprefix("www.")
    if not any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains):
        return None
    path = parts.path.rstrip("/")
    if host == "arxiv.org" and path.endswith(".pdf"):
        path = path[:-4]
    query = ""
    if host == "openreview.net":
        identifier = urllib.parse.parse_qs(parts.query).get("id", [])
        if identifier:
            query = urllib.parse.urlencode({"id": identifier[0]})
    return urllib.parse.urlunsplit(("https", host, path, query, ""))


def api_get(url: str, token: str, timeout: int) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"X API HTTP {exc.code}: {detail[:500]}") from exc


def fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.casefold()).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def artifact_key(urls: list[str]) -> str | None:
    for url in urls:
        if match := ARXIV_RE.search(url):
            return f"arxiv:{match.group(1)}"
        parts = urllib.parse.urlsplit(url)
        if parts.netloc == "github.com":
            segments = [part for part in parts.path.split("/") if part]
            if len(segments) >= 2:
                return f"github:{segments[0].lower()}/{segments[1].lower()}"
        if parts.netloc == "openreview.net":
            identifier = urllib.parse.parse_qs(parts.query).get("id", [])
            if identifier:
                return f"openreview:{identifier[0]}"
        if parts.netloc == "huggingface.co":
            segments = [part for part in parts.path.split("/") if part]
            if len(segments) >= 2:
                return f"huggingface:{segments[0].lower()}/{segments[1].lower()}"
    return None


def classify_post(post: dict, author: dict, pack: dict, config: dict, collected_at: str) -> dict | None:
    if post.get("possibly_sensitive") and config["quality_rules"].get("exclude_sensitive", True):
        return None
    if any(item.get("type") == "retweeted" for item in post.get("referenced_tweets", [])):
        return None
    text = str(post.get("text") or "")
    lowered = text.casefold()
    if any(term.casefold() in lowered for term in config["quality_rules"].get("spam_terms", [])):
        return None

    allowed_domains = {"arxiv.org", "openreview.net", "github.com", "huggingface.co"}
    for entity in config.get("entity_terms", []):
        allowed_domains.update(domain.lower() for domain in entity.get("domains", []))
    urls = []
    for item in (post.get("entities") or {}).get("urls", []):
        value = item.get("unwound_url") or item.get("expanded_url") or item.get("url")
        normalized = canonical_url(str(value or ""), allowed_domains)
        if normalized and normalized not in urls:
            urls.append(normalized)

    matched_topics = []
    for topic in config["topics"]:
        if any(keyword.casefold() in lowered for keyword in topic.get("keywords", [])):
            matched_topics.append(topic["code"])
    keyword_matched = bool(matched_topics)
    matched_topics = list(dict.fromkeys(matched_topics or pack.get("topic_codes", [])))
    if not matched_topics:
        return None

    matched_entities = []
    for entity in config.get("entity_terms", []):
        term_hit = any(term.casefold() in lowered for term in entity.get("terms", []))
        domain_hit = any(any(domain.lower() in url for domain in entity.get("domains", [])) for url in urls)
        if term_hit or domain_hit:
            matched_entities.append(entity["organization_id"])

    topic_map = {item["code"]: item for item in config["topics"]}
    directions = list(dict.fromkeys([
        *(pack.get("direction_codes", []) if not keyword_matched else []),
        *(code for topic_code in matched_topics for code in topic_map[topic_code].get("direction_codes", [])),
    ]))
    metrics = post.get("public_metrics") or {}
    normalized_metrics = {
        "like_count": int(metrics.get("like_count") or 0),
        "retweet_count": int(metrics.get("retweet_count") or 0),
        "reply_count": int(metrics.get("reply_count") or 0),
        "quote_count": int(metrics.get("quote_count") or 0),
        "bookmark_count": int(metrics.get("bookmark_count") or 0),
        "impression_count": int(metrics.get("impression_count") or 0),
    }
    key = artifact_key(urls)
    if key and key.startswith(("arxiv:", "openreview:")):
        content_kind = "research"
    elif key:
        content_kind = "artifact"
    elif matched_entities or pack.get("category") == "startup":
        content_kind = "startup"
    else:
        content_kind = "discussion"
    author_metrics = author.get("public_metrics") or {}
    return {
        "post_id": str(post["id"]),
        "author_id": str(post.get("author_id") or "0"),
        "author_username": author.get("username"),
        "author_verified": bool(author.get("verified")),
        "author_followers": int(author_metrics.get("followers_count") or 0),
        "created_at": post.get("created_at"),
        "lang": post.get("lang") or "und",
        "conversation_id": str(post.get("conversation_id") or post["id"]),
        "metrics": normalized_metrics,
        "query_tags": [pack["id"]],
        "topic_codes": matched_topics,
        "primary_topic_code": matched_topics[0],
        "direction_codes": directions,
        "entity_ids": matched_entities,
        "canonical_urls": urls,
        "artifact_key": key,
        "content_kind": content_kind,
        "text_fingerprint": fingerprint(text),
        "collected_at": collected_at,
        "last_seen_at": collected_at,
        "compliance_status": "live",
    }


def merge_post(existing: dict | None, incoming: dict) -> dict:
    if not existing:
        return incoming
    merged = {**existing, **incoming}
    for field in ("query_tags", "topic_codes", "direction_codes", "entity_ids", "canonical_urls"):
        merged[field] = list(dict.fromkeys([*(existing.get(field) or []), *(incoming.get(field) or [])]))
    merged["collected_at"] = existing.get("collected_at") or incoming["collected_at"]
    return merged


def live_payloads(pack: dict, config: dict, token: str, start: datetime, end: datetime) -> list[dict]:
    source = config["source"]
    payloads = []
    next_token = None
    for _ in range(int(source["max_pages_per_query"])):
        params = {
            "query": pack["query"],
            "start_time": iso_utc(start),
            "end_time": iso_utc(end),
            "max_results": source["max_results_per_page"],
            "tweet.fields": "id,author_id,created_at,lang,public_metrics,entities,conversation_id,referenced_tweets,possibly_sensitive",
            "expansions": "author_id",
            "user.fields": "id,username,verified,public_metrics",
        }
        if next_token:
            params["next_token"] = next_token
        payload = api_get(f"{API}?{urllib.parse.urlencode(params)}", token, int(source["request_timeout_seconds"]))
        payloads.append(payload)
        next_token = (payload.get("meta") or {}).get("next_token")
        if not next_token:
            break
    return payloads


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="inclusive UTC timestamp")
    parser.add_argument("--end", help="exclusive UTC timestamp")
    parser.add_argument("--lookback-hours", type=int)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = read(CONFIG, {})
    now = datetime.now(timezone.utc)
    end = parse_time(args.end, now)
    lookback = args.lookback_hours or int(config["source"]["lookback_hours"])
    start = parse_time(args.start, end - timedelta(hours=lookback))
    if start >= end:
        raise SystemExit("start must precede end")
    if end - start > timedelta(days=7):
        raise SystemExit("Recent Search cannot cover more than seven days; use incremental polling")

    if args.dry_run and not args.fixture:
        print(json.dumps({
            "mode": "dry-run",
            "from": iso_utc(start),
            "until": iso_utc(end),
            "query_packs": [{"id": row["id"], "characters": len(row["query"]), "query": row["query"]} for row in config["query_packs"]],
            "estimated_max_post_reads": len(config["query_packs"]) * config["source"]["max_pages_per_query"] * config["source"]["max_results_per_page"],
        }, ensure_ascii=False, indent=2))
        return

    token = os.getenv("X_BEARER_TOKEN")
    if not args.fixture and not token:
        raise SystemExit("X_BEARER_TOKEN is required unless --fixture or --dry-run is used")
    fixture = read(args.fixture, {"responses": {}}) if args.fixture else None
    collected_at = iso_utc(now)
    store = read(args.store, {"version": "1.0", "updated_at": None, "source": "x_api_v2", "posts": []})
    posts = {row["post_id"]: row for row in store.get("posts", [])}
    accepted = 0
    request_count = 0
    query_stats = []
    for pack in config["query_packs"]:
        payloads = (fixture.get("responses", {}).get(pack["id"], []) if fixture else live_payloads(pack, config, token, start, end))
        request_count += len(payloads)
        pack_returned = 0
        pack_accepted = 0
        for payload in payloads:
            users = {str(row["id"]): row for row in (payload.get("includes") or {}).get("users", [])}
            for post in payload.get("data") or []:
                pack_returned += 1
                author = users.get(str(post.get("author_id")), {})
                normalized = classify_post(post, author, pack, config, collected_at)
                if not normalized:
                    continue
                posts[normalized["post_id"]] = merge_post(posts.get(normalized["post_id"]), normalized)
                accepted += 1
                pack_accepted += 1
        query_stats.append({"query_pack": pack["id"], "requests": len(payloads), "returned": pack_returned, "accepted": pack_accepted})

    cutoff = now - timedelta(weeks=int(config["publication"]["retention_weeks"]))
    retained = [row for row in posts.values() if parse_time(row.get("created_at"), now) >= cutoff]
    retained.sort(key=lambda row: (row.get("created_at") or "", row["post_id"]), reverse=True)
    output = {
        "version": "1.0",
        "updated_at": collected_at,
        "last_compliance_check_at": store.get("last_compliance_check_at"),
        "source": "x_api_v2",
        "posts": retained,
        "collection_runs": [
            *(store.get("collection_runs") or []),
            {
                "collected_at": collected_at,
                "from": iso_utc(start),
                "until": iso_utc(end),
                "request_count": request_count,
                "returned_post_count": sum(row["returned"] for row in query_stats),
                "accepted_post_count": accepted,
                "query_stats": query_stats,
            },
        ][-100:],
    }
    args.store.parent.mkdir(parents=True, exist_ok=True)
    args.store.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"mode": "fixture" if fixture else "live", "requests": request_count, "accepted": accepted, "unique_posts": len(retained), "store": str(args.store)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
