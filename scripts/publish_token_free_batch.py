#!/usr/bin/env python3
"""Publish compact, unverified research records, then release private full text."""
from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from collect_hardware_sources import atomic_write, encode
from prepare_fulltext_reading import latest_observations
from token_free_research import read_log


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".research/token-free-research"
CACHE = ROOT / ".research/hardware-fulltext"
PUBLISH_TREE = ROOT / ".research/token-free-publisher"
RECORDS_REL = Path("data/token-free-public/records.jsonl")
RECEIPTS = PRIVATE / "published-receipts.jsonl"
STATE = PRIVATE / "publish-state.json"
LABEL = "JoenHune/embodied-ai-radar"
ONLINE_SUMMARY = "https://joen.site/embodied-ai-radar/api/v1/token-free/summary.json"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
OBSERVATION_ID = re.compile(r"hardware-source:[0-9a-f]{32}\Z")
UTC_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z")
MAX_BATCH = 200
RECORD_FIELDS = {"schema_version", "work_id", "observation_id", "observed_at", "source_url",
                 "source_state", "raw_sha256", "text_sha256", "process_state", "processing_key",
                 "article_read_complete", "usage_verified", "matches"}
MATCH_FIELDS = {"dictionary_id", "name", "category", "context_only", "source_locator",
                "simulation_word_present", "negation_word_present"}


def command(args, *, cwd=ROOT, timeout=120, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f"{args[0]} failed ({result.returncode}): {result.stderr[-500:]}")
    return result


def git(*args, cwd=ROOT, timeout=120):
    return command(["git", *args], cwd=cwd, timeout=timeout).stdout.strip()


def parse_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def safe_arxiv_url(value, *, fragment=False):
    if not isinstance(value, str) or len(value) > 512:
        raise ValueError("invalid_arxiv_url")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname not in {"arxiv.org", "www.arxiv.org"}
            or parsed.username or parsed.password or parsed.query or
            (parsed.fragment and not fragment) or
            (parsed.fragment and fragment and
             not re.fullmatch(r"[A-Za-z0-9_.:-]{1,256}", parsed.fragment)) or
            not parsed.path.startswith("/html/") or
            not re.fullmatch(r"/html/(?:\d{4}\.\d{4,5}|[A-Za-z][A-Za-z.\-]+/\d{7})(?:v[1-9]\d*)?", parsed.path)):
        raise ValueError("invalid_arxiv_url")
    return value


def safe_hash(value, *, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError("invalid_source_hash")
    return value


def safe_object(path):
    if not path:
        return None
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.resolve().is_relative_to((CACHE / "objects").resolve()):
        raise ValueError("unsafe_private_cache_reference")
    return candidate


def validate_public_record(record):
    if (not isinstance(record, dict) or set(record) != RECORD_FIELDS or
            record["schema_version"] != "1" or record["article_read_complete"] is not False or
            record["usage_verified"] is not False or not isinstance(record["work_id"], str) or
            not 0 < len(record["work_id"]) <= 200 or
            not OBSERVATION_ID.fullmatch(record["observation_id"]) or
            record["source_state"] not in {"full_text_available", "partial_text", "unavailable",
                                           "blocked", "identity_mismatch"} or
            record["process_state"] not in {"extracted_not_read", "source_needed"} or
            not isinstance(record["matches"], list) or len(record["matches"]) > 10000 or
            not isinstance(record["observed_at"], str) or
            not UTC_STAMP.fullmatch(record["observed_at"])):
        raise ValueError("invalid_public_record")
    try:
        datetime.fromisoformat(record["observed_at"].replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("invalid_observed_at") from None
    safe_arxiv_url(record["source_url"])
    safe_hash(record["raw_sha256"], optional=True)
    safe_hash(record["text_sha256"], optional=True)
    safe_hash(record["processing_key"], optional=True)
    for match in record["matches"]:
        if (not isinstance(match, dict) or set(match) != MATCH_FIELDS or
                any(type(match[field]) is not bool for field in
                    ("context_only", "simulation_word_present", "negation_word_present")) or
                any(not isinstance(match[field], str) or len(match[field]) > 512 for field in
                    ("dictionary_id", "name", "category"))):
            raise ValueError("invalid_public_match")
        safe_arxiv_url(match["source_locator"], fragment=True)
    if re.search(r"/(?:Users|home|private|tmp|var|Volumes|mnt|workspace|root)/",
                 encode(record)):
        raise ValueError("private_path_in_public_record")
    return record


def make_record(observation, dbrow, dictionary_entries):
    work_id = observation["work_id"]
    if dbrow["work_id"] != work_id or dbrow["source_state"] != observation["status"]:
        raise ValueError("source_database_mismatch")
    oid = observation.get("observation_id")
    if not isinstance(oid, str) or not OBSERVATION_ID.fullmatch(oid):
        raise ValueError("invalid_observation_id")
    source_url = safe_arxiv_url(observation["source_url"])
    source_hash = safe_hash(observation.get("raw_sha256"), optional=True)
    text_hash = safe_hash(observation.get("text_sha256"), optional=True)
    source_state = observation["status"]
    if source_state not in {"full_text_available", "partial_text", "unavailable", "blocked", "identity_mismatch"}:
        raise ValueError("invalid_source_state")
    result = {
        "schema_version": "1", "work_id": work_id, "observation_id": oid,
        "observed_at": observation["observed_at"], "source_url": source_url,
        "source_state": source_state, "raw_sha256": source_hash, "text_sha256": text_hash,
        "process_state": dbrow["process_state"], "processing_key": None,
        "article_read_complete": False, "usage_verified": False, "matches": [],
    }
    if source_state not in {"full_text_available", "partial_text"}:
        if dbrow["process_state"] != "source_needed":
            raise ValueError("unavailable_source_state_mismatch")
        return validate_public_record(result)
    if dbrow["process_state"] != "extracted_not_read" or dbrow["processed_key"] != dbrow["source_key"]:
        raise ValueError("available_source_not_extracted")
    card_path = PRIVATE / (dbrow["card_path"] or "")
    if (not dbrow["card_path"] or card_path.is_symlink() or
            not card_path.resolve().is_relative_to((PRIVATE / "cards").resolve())):
        raise ValueError("unsafe_card_path")
    card = json.loads(gzip.decompress(card_path.read_bytes()))
    if (card.get("work_id") != work_id or card.get("processing_key") != dbrow["source_key"] or
            card.get("source", {}).get("observation_id") != oid or
            card.get("source", {}).get("raw_sha256") != source_hash or
            card.get("article_read_complete") is not False or
            card.get("understanding_verified") is not False):
        raise ValueError("card_source_binding_mismatch")
    raw_path = safe_object(observation.get("cache_ref"))
    if raw_path is None or sha256(raw_path.read_bytes()) != source_hash:
        raise ValueError("cached_raw_hash_mismatch")
    matches = {}
    for candidate in card["hardware_candidates"]:
        did = candidate["dictionary_id"]
        if (did not in dictionary_entries or
                candidate.get("name") != dictionary_entries[did]["name"] or
                candidate.get("status") != "unverified_mention" or
                candidate.get("usage_verified") is not False):
            raise ValueError("candidate_not_unverified_or_not_in_dictionary")
        locator = safe_arxiv_url(candidate["source_locator"], fragment=True)
        if urlsplit(locator).path != urlsplit(source_url).path:
            raise ValueError("candidate_locator_source_mismatch")
        item = {key: candidate[key] for key in (
            "dictionary_id", "name", "category", "context_only", "source_locator",
            "simulation_word_present", "negation_word_present")}
        key = (did, locator, bool(item["context_only"]))
        matches[key] = item
    result["matches"] = [matches[key] for key in sorted(matches)]
    result["processing_key"] = dbrow["source_key"]
    return validate_public_record(result)


def ensure_publish_tree():
    git("fetch", "--no-tags", "origin", "main:refs/remotes/origin/main", timeout=180)
    if not PUBLISH_TREE.exists():
        git("worktree", "add", "--detach", "--no-checkout", str(PUBLISH_TREE), "origin/main", timeout=180)
        git("sparse-checkout", "init", "--no-cone", cwd=PUBLISH_TREE)
        git("sparse-checkout", "set", "--no-cone", "/data/token-free-public/", cwd=PUBLISH_TREE)
    if git("status", "--porcelain", cwd=PUBLISH_TREE):
        # This worktree is dedicated to the publisher; local unsent records are rebuilt.
        git("reset", "--hard", "origin/main", cwd=PUBLISH_TREE)
    else:
        git("reset", "--hard", "origin/main", cwd=PUBLISH_TREE)
    return PUBLISH_TREE / RECORDS_REL


def page_digest():
    response = command(["/usr/bin/curl", "--fail", "--silent", "--show-error", "--location",
                        "--max-time", "20", ONLINE_SUMMARY + "?t=" + str(int(time.time()))],
                       timeout=30, check=False)
    if response.returncode:
        return None
    try:
        value = json.loads(response.stdout)
        return value.get("records_sha256")
    except json.JSONDecodeError:
        return None


def deployment_state(commit):
    result = command(["gh", "run", "list", "-R", LABEL, "--workflow", "deploy.yml",
                      "--commit", commit, "--json", "status,conclusion", "--limit", "5"],
                     timeout=45, check=False)
    if result.returncode:
        return None
    try:
        runs = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not runs:
        return None
    if any(row["status"] == "completed" and row["conclusion"] == "success" for row in runs):
        return "success"
    if all(row["status"] == "completed" for row in runs):
        return "failure"
    return "pending"


def wait_online(commit, expected_hash, *, timeout_seconds=45 * 60):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if page_digest() == expected_hash:
            return
        if deployment_state(commit) == "failure":
            raise RuntimeError("pages_deployment_failed_private_cache_retained")
        time.sleep(30)
    raise RuntimeError("pages_digest_not_confirmed_private_cache_retained")


def receipts_by_work():
    result = {}
    seen = {}
    for item in parse_jsonl(RECEIPTS):
        if (set(item) != {"work_id", "observation_id", "processing_key", "record_sha256",
                          "commit_sha", "published_at", "process_state"} or
                not isinstance(item["work_id"], str) or
                not OBSERVATION_ID.fullmatch(item["observation_id"]) or
                not SHA256.fullmatch(item["record_sha256"]) or
                not re.fullmatch(r"[0-9a-f]{40}", item["commit_sha"]) or
                (item["processing_key"] is not None and not SHA256.fullmatch(item["processing_key"]))):
            raise ValueError("invalid_publish_receipt")
        key = (item["work_id"], item["observation_id"], item["processing_key"])
        previous = seen.get(key)
        if previous and previous != item:
            raise ValueError("conflicting_publish_receipt")
        seen[key] = item
        result[item["work_id"]] = item
    return result


def cleanup(records, observations, dbrows, commit):
    receipts = receipts_by_work()
    new_receipts = {}
    for record in records:
        if record["process_state"] != "extracted_not_read":
            continue
        work_id = record["work_id"]
        if (work_id in receipts and
                receipts[work_id]["observation_id"] == record["observation_id"] and
                receipts[work_id]["processing_key"] == record["processing_key"]):
            continue
        new_receipts[work_id] = {
            "work_id": work_id, "observation_id": record["observation_id"],
            "processing_key": record["processing_key"],
            "record_sha256": sha256(encode(record).encode()), "commit_sha": commit,
            "published_at": stamp(), "process_state": record["process_state"],
        }
    if new_receipts:
        receipts.update(new_receipts)
        history = parse_jsonl(RECEIPTS)
        history.extend(new_receipts.values())
        atomic_write(RECEIPTS, "".join(encode(row) + "\n" for row in history).encode())
    # The durable receipt precedes all deletions. An interrupted cleanup is safe to retry.
    cleanup_ids = {work_id for work_id, receipt in receipts.items()
                   if work_id in observations and
                   receipt["observation_id"] == observations[work_id]["observation_id"]}
    cleanup_ids.update(record["work_id"] for record in records
                       if record["process_state"] == "source_needed")
    protected = set()
    for work_id, observation in observations.items():
        if work_id in cleanup_ids:
            continue
        for key in ("cache_ref", "blocks_ref", "body_cache_ref"):
            path = safe_object(observation.get(key))
            if path:
                protected.add(path.resolve())
    with closing(sqlite3.connect(PRIVATE / "research.sqlite")) as db:
        for work_id, receipt in receipts.items():
            observation = observations.get(work_id)
            if not observation or observation["observation_id"] != receipt["observation_id"]:
                continue
            row = dbrows.get(work_id)
            if not row:
                continue
            if receipt["process_state"] == "extracted_not_read":
                if row["source_key"] != receipt["processing_key"]:
                    continue
                if row["card_path"]:
                    card = PRIVATE / row["card_path"]
                    if card.resolve().is_relative_to((PRIVATE / "cards").resolve()) and not card.is_symlink():
                        card.unlink(missing_ok=True)
                with db:
                    db.execute("UPDATE search SET body='' WHERE rowid=?", (row["search_rowid"],))
                    db.execute("DELETE FROM candidates WHERE work_id=?", (work_id,))
                    db.execute("UPDATE works SET process_state='published_compacted',processed_key=?,card_path=NULL,reason=NULL WHERE work_id=?",
                               (receipt["processing_key"], work_id))
            for key in ("cache_ref", "blocks_ref", "body_cache_ref"):
                path = safe_object(observation.get(key))
                if path and path.resolve() not in protected:
                    path.unlink(missing_ok=True)
        for record in records:
            if record["process_state"] != "source_needed":
                continue
            observation = observations.get(record["work_id"])
            if not observation or observation["observation_id"] != record["observation_id"]:
                continue
            for key in ("cache_ref", "blocks_ref", "body_cache_ref"):
                path = safe_object(observation.get(key))
                if path and path.resolve() not in protected:
                    path.unlink(missing_ok=True)
        referenced_cards = {
            str(PRIVATE / row[0]) for row in
            db.execute("SELECT card_path FROM works WHERE card_path IS NOT NULL")
        }
        for card in (PRIVATE / "cards").glob("*.json.gz"):
            if card.is_symlink():
                raise ValueError("symlink_card_forbidden")
            if str(card) not in referenced_cards:
                card.unlink()
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        db.execute("VACUUM")
    atomic_write(STATE, (encode({"last_success_at": stamp(), "commit_sha": commit,
                                 "records_sha256": sha256((PUBLISH_TREE / RECORDS_REL).read_bytes()),
                                 "compacted_works": len(receipts)}) + "\n").encode())
    return len(new_receipts)


def publish(*, dry_run=False, max_records=MAX_BATCH):
    PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (PRIVATE / "runner.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "collector_busy_try_next_interval"}
        observations = latest_observations(read_log(CACHE / "observations.jsonl")[0])
        if not observations:
            return {"status": "nothing_collected"}
        db = sqlite3.connect(PRIVATE / "research.sqlite")
        db.row_factory = sqlite3.Row
        with closing(db):
            dbrows = {row["work_id"]: dict(row) for row in
                      db.execute("SELECT rowid AS search_rowid,* FROM works WHERE active=1")}
        dictionary = json.loads((ROOT / "config/hardware-dictionary.json").read_text())
        dictionary_entries = {entry["dictionary_id"]: entry for entry in dictionary["entries"]}
        public_path = ((PUBLISH_TREE / RECORDS_REL) if PUBLISH_TREE.exists() else
                       (ROOT / RECORDS_REL)) if dry_run else ensure_publish_tree()
        previous = {}
        for record in parse_jsonl(public_path):
            validate_public_record(record)
            if record["work_id"] in previous:
                raise ValueError("duplicate_public_work")
            previous[record["work_id"]] = record
        changed = []
        review = []
        for work_id, observation in sorted(observations.items()):
            old = previous.get(work_id)
            current = dbrows.get(work_id)
            if (old and old["observation_id"] == observation["observation_id"] and
                    (old["process_state"] != "extracted_not_read" or
                     not current or current["process_state"] != "extracted_not_read" or
                     old["processing_key"] == current["source_key"])):
                continue
            try:
                record = make_record(observation, dbrows[work_id], dictionary_entries)
            except (ValueError, KeyError) as exc:
                if str(exc) in {"available_source_not_extracted"}:
                    continue
                review.append({"work_id": work_id, "reason": str(exc)[:120] if isinstance(exc, ValueError)
                               else "missing_required_field"})
                continue
            previous[work_id] = record
            changed.append(record)
            if len(changed) >= max_records:
                break
        if dry_run:
            return {"status": "dry_run", "new_records": len(changed),
                    "pending_local_observations": len(observations),
                    "review_required": len(review),
                    "sample_work_ids": [row["work_id"] for row in changed[:5]]}
        atomic_write(PRIVATE / "publish-review-queue.jsonl",
                     "".join(encode(row) + "\n" for row in review).encode())
        if changed:
            public_path.parent.mkdir(parents=True, exist_ok=True)
            raw = "".join(encode(row) + "\n" for row in sorted(previous.values(), key=lambda row: row["work_id"])).encode()
            atomic_write(public_path, raw)
            git("add", "--", str(RECORDS_REL), cwd=PUBLISH_TREE)
            if git("diff", "--cached", "--name-only", cwd=PUBLISH_TREE):
                command(["git", "-c", "user.name=embodied-ai-radar-local",
                         "-c", "user.email=actions@users.noreply.github.com",
                         "commit", "-m", f"data: publish {len(changed)} unverified source records"],
                        cwd=PUBLISH_TREE, timeout=120)
                commit = git("rev-parse", "HEAD", cwd=PUBLISH_TREE)
                git("push", "origin", "HEAD:main", cwd=PUBLISH_TREE, timeout=180)
            else:
                commit = git("rev-parse", "HEAD", cwd=PUBLISH_TREE)
        else:
            commit = git("rev-parse", "HEAD", cwd=PUBLISH_TREE)
            raw = public_path.read_bytes() if public_path.exists() else b""
        receipts = receipts_by_work()
        uncleaned = []
        for record in previous.values():
            work_id = record["work_id"]
            if (work_id not in observations or
                    record["observation_id"] != observations[work_id]["observation_id"]):
                continue
            receipt = receipts.get(work_id)
            row = dbrows.get(work_id)
            artifacts_remain = (row and record["process_state"] == "extracted_not_read" and
                                (row["process_state"] != "published_compacted" or bool(row["card_path"])))
            artifacts_remain = artifacts_remain or any(
                (path := safe_object(observations[work_id].get(key))) is not None and path.exists()
                for key in ("cache_ref", "blocks_ref", "body_cache_ref"))
            needs_receipt = (record["process_state"] == "extracted_not_read" and
                             (receipt is None or receipt["observation_id"] != record["observation_id"] or
                              receipt["processing_key"] != record["processing_key"]))
            if needs_receipt or artifacts_remain:
                uncleaned.append(record)
        if not changed and not uncleaned:
            return {"status": "up_to_date", "total_public_records": len(previous)}
        wait_online(commit, sha256(raw))
        compacted = cleanup(uncleaned, observations, dbrows, commit)
        return {"status": "published_and_compacted", "new_records": len(changed),
                "compacted_records": compacted, "total_public_records": len(previous),
                "commit_sha": commit}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Push to main and compact after online verification")
    parser.add_argument("--max-records", type=int, default=MAX_BATCH)
    args = parser.parse_args(argv)
    if not 1 <= args.max_records <= MAX_BATCH:
        parser.error("max-records must be between 1 and 200")
    try:
        print(json.dumps(publish(dry_run=not args.apply, max_records=args.max_records),
                         ensure_ascii=False, indent=2), flush=True)
    except (ValueError, OSError, sqlite3.Error, subprocess.TimeoutExpired, RuntimeError) as exc:
        print("token-free-publish: " + str(exc), file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
