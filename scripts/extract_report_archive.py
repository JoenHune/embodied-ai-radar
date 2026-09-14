#!/usr/bin/env python3
"""Verify a public Git-hash-anchored archive and emit copyright-limited input.

No authority or cache writes. Default extraction prints one JSON envelope with
source_proof and snapshot; --verify checks the saved JSONL inputs independently.
Only the local ignored HTML is read in full. Published input contains <=25
lexical words of excerpts, never the full embedded search text.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = "data/group-source-status.json"
RAW_PATH = "data/raw/organizations/generalist-ai/198d445139e8-2026-08-26.html"
DEPLOY_PATH = "research/august-cache-deployment-proof.json"
WORK_ID = "report:de9e41b42353bf59a7e3"
MANIFESTATION_ID = "manifest:29c0bd6a32f3e7b5dd1e"
SOURCE_URL = "https://generalistai.com/blog/research"
REPORT_URL = "https://generalistai.com/blog/gen-1.5"
SELECTOR = 'a.blog-entry[href="/blog/gen-1.5"]'
SOURCE_SCOPE = "source_content"
VERIFIER = "codex_archive_byte_check"
ICL_CONTEXT = "单次示教、无梯度更新"
FT_CONTEXT = "多次示教后的少量梯度更新"
PINNED_GEN15 = {
    "commit": "7ed6bedcd6bcdf8730e8012e28dcb81994176773", "path": STATUS_PATH,
    "blob_sha1": "0f618caf6ac768d78e2f22afd461659f2e14a19b",
    "archive_status_sha256": "f928256bed8469fa24648ab28d1c713d5adb67fd0901dc28a89aa7ed53abaf70",
    "archive_source_record_id": "source:198d445139e8",
    "archive_content_sha256": "6c49daf1cea8d5927ff89fd8be8ee4df281f99830e13ceaae6f20e8c1183f35d",
    "archive_captured_at": "2026-08-26T14:29:04.760164+00:00", "organization_id": "org:generalist-ai",
    "deployment_url": "https://github.com/JoenHune/embodied-ai-radar/actions/runs/32994514392", "run_id": 32994514392,
    "head_sha": "7ed6bedcd6bcdf8730e8012e28dcb81994176773", "deploy_completed_at": "2026-08-26T17:31:56Z",
    "deployment_proof_sha256": "7b8cb431a0ee50d8848b89ded7ed0814728f7346b17bd67f8f6b7049aa438374",
    "archive_html_path": RAW_PATH, "deployment_proof_path": DEPLOY_PATH, "selector": SELECTOR,
    "attribute": "data-search", "entity_unescape_passes": 1, "offset_unit": "unicode_codepoints",
    "extracted_text_sha256": "8d3339242ab917d5c80080e73066b464af7929dca5aafaa13552ffabbf8d63c5", "extracted_text_characters": 25536,
}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utc(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError) as error:
        raise ValueError("timezone_aware_archive_date_required") from error


def _safe_local(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("archive_path_not_relative")
    target = root / path
    if target.is_symlink() or any((root / Path(*path.parts[:i])).is_symlink() for i in range(1, len(path.parts))):
        raise ValueError("archive_symlink_forbidden")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("archive_path_escape")
    return target


def _git_status(root: Path, proof: dict) -> bytes:
    if not re.fullmatch(r"[a-f0-9]{40}", proof.get("commit", "")) or proof.get("path") != STATUS_PATH:
        raise ValueError("unexpected_git_archive_target")
    return subprocess.check_output(["git", "show", proof["commit"] + ":" + STATUS_PATH], cwd=root)


def check_archive_materials(proof: dict, raw_html: bytes, status_blob: bytes, deployment_blob: bytes, source_url: str, report_url: str) -> str:
    """Return full text only in memory, after every independent hash check."""
    if sha256(status_blob) != proof["archive_status_sha256"]:
        raise ValueError("archive_status_sha256_mismatch")
    git_blob = hashlib.sha1(f"blob {len(status_blob)}\0".encode() + status_blob).hexdigest()
    if git_blob != proof["blob_sha1"]:
        raise ValueError("git_blob_sha1_mismatch")
    status = json.loads(status_blob)
    rows = [row for row in status.get("sources", []) if row.get("source_id") == proof["archive_source_record_id"]]
    if len(rows) != 1:
        raise ValueError("archive_source_not_unique")
    source = rows[0]
    if source.get("url") != source_url or source.get("organization_id") != proof["organization_id"]:
        raise ValueError("archive_official_url_or_organization_mismatch")
    if source.get("content_hash") != proof["archive_content_sha256"] or sha256(raw_html) != proof["archive_content_sha256"]:
        raise ValueError("archive_html_hash_mismatch")
    if source.get("last_checked") != proof["archive_captured_at"] or source.get("status") != "healthy":
        raise ValueError("archive_capture_metadata_mismatch")
    if sha256(deployment_blob) != proof["deployment_proof_sha256"]:
        raise ValueError("deployment_proof_hash_mismatch")
    deployment = json.loads(deployment_blob)
    if deployment.get("head_sha") != proof["commit"] or proof["head_sha"] != proof["commit"]:
        raise ValueError("deployment_commit_mismatch")
    if deployment.get("run_id") != proof["run_id"] or deployment.get("url") != proof["deployment_url"]:
        raise ValueError("deployment_run_mismatch")
    parsed = urlsplit(proof["deployment_url"])
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password or not parsed.path.endswith("/actions/runs/" + str(proof["run_id"])):
        raise ValueError("invalid_public_deployment_url")
    if deployment.get("status") != "completed" or deployment.get("conclusion") != "success":
        raise ValueError("deployment_not_successful")
    jobs = [row for row in deployment.get("jobs", []) if row.get("name") == "deploy"]
    if len(jobs) != 1 or jobs[0].get("conclusion") != "success" or jobs[0].get("completed_at") != proof["deploy_completed_at"]:
        raise ValueError("deployment_job_not_proven")
    if deployment.get("conservative_archive_available_by") != proof["deploy_completed_at"]:
        raise ValueError("deployment_availability_mismatch")
    if not (_utc(proof["archive_captured_at"]) <= _utc(deployment["created_at"]) <= _utc(jobs[0]["started_at"]) <= _utc(proof["deploy_completed_at"]) <= _utc(deployment["updated_at"])):
        raise ValueError("archive_deployment_chronology_invalid")
    if proof.get("attribute") != "data-search" or proof.get("entity_unescape_passes") != 1 or proof.get("offset_unit") != "unicode_codepoints":
        raise ValueError("unsupported_archive_extraction")
    soup = BeautifulSoup(raw_html.decode("utf-8"), "html.parser")
    elements = soup.select(proof["selector"])
    if len(elements) != 1 or elements[0].name != "a" or "blog-entry" not in elements[0].get("class", []):
        raise ValueError("archive_selector_not_unique_report_anchor")
    if urljoin(source_url, elements[0].get("href", "")) != report_url:
        raise ValueError("archive_report_link_mismatch")
    attribute = elements[0].get("data-search")
    if not isinstance(attribute, str):
        raise ValueError("archive_attribute_missing")
    text = html.unescape(attribute)
    if sha256(text.encode()) != proof["extracted_text_sha256"] or len(text) != proof["extracted_text_characters"]:
        raise ValueError("archive_extracted_text_hash_mismatch")
    for check in proof.get("context_checks", []):
        start, end = check["start"], check["end"]
        if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(text) or sha256(text[start:end].encode()) != check["sha256"]:
            raise ValueError("archive_context_window_mismatch")
    return text


def lexical_word_count(texts) -> int:
    # Conservative: hyphenated words are split; numeric tokens also count.
    return sum(len(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:\.\d+)?", text)) for text in set(texts))


def validate_total_excerpt_quota(additions):
    by_report = {}
    for row in additions:
        by_report.setdefault(row["report_url"], set()).update(item["text"] for item in row["excerpts"])
    for texts in by_report.values():
        if lexical_word_count(texts) > 25 or sum(len(re.findall(r"[\u3400-\u9fff]", text)) for text in texts) > 160:
            raise ValueError("public_excerpt_quota_exceeded")


def _validate_public_snapshot(snapshot: dict, attestation: dict, text: str) -> None:
    from jsonschema import Draft202012Validator, FormatChecker
    schema = json.loads((ROOT / "config/report-text.schema.json").read_text())
    if any(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(snapshot)):
        raise ValueError("report_snapshot_schema_invalid")
    copied = dict(snapshot)
    copied.pop("snapshot_id", None)
    if snapshot["snapshot_id"] != "report-text:" + digest(copied)[:24]:
        raise ValueError("report_snapshot_id_mismatch")
    fields = ["attestation_id", "report_url", "source_url", "report_published_at", "report_date_precision", "captured_at", "available_at", "date_precision", "content_sha256", "excerpt_digest", "verified_by", "verified_at"]
    if any(snapshot[key] != attestation.get(key) for key in fields):
        raise ValueError("snapshot_attestation_mismatch")
    if attestation.get("status") != "verified" or attestation.get("verification_scope") != SOURCE_SCOPE or attestation.get("basis") != "git_archive":
        raise ValueError("source_content_attestation_required")
    proof = attestation["proof"]
    if proof.get("observations_digest") != digest(snapshot["observations"]):
        raise ValueError("report_observations_not_attested")
    if snapshot["available_at"] != proof["deploy_completed_at"] or snapshot["content_sha256"] != proof["extracted_text_sha256"]:
        raise ValueError("snapshot_availability_or_content_unproven")
    if not (_utc(snapshot["available_at"]) <= _utc(snapshot["captured_at"]) <= _utc(snapshot["verified_at"])):
        raise ValueError("snapshot_capture_chronology_invalid")
    if snapshot["report_date_precision"] != "day" or snapshot["report_published_at"] not in text:
        raise ValueError("publisher_date_not_in_archived_text")
    quotes = snapshot["excerpts"]
    if len({row["excerpt_id"] for row in quotes}) != len(quotes) or digest(quotes) != snapshot["excerpt_digest"]:
        raise ValueError("excerpt_ids_or_digest_mismatch")
    if lexical_word_count(row["text"] for row in quotes) > 25 or sum(len(re.findall(r"[\u3400-\u9fff]", row["text"])) for row in quotes) > 160:
        raise ValueError("public_excerpt_quota_exceeded")
    planned = proof["excerpt_positions"]
    if [{key: row[key] for key in ["excerpt_id", "start", "end", "locator"]} for row in quotes] != planned:
        raise ValueError("excerpt_positions_not_attested")
    for row in quotes:
        if not 0 <= row["start"] < row["end"] <= len(text) or text[row["start"]:row["end"]] != row["text"]:
            raise ValueError("excerpt_text_or_offset_mismatch")
    by_id = {row["excerpt_id"]: row for row in quotes}
    contexts = {row["context"]: set(row["excerpt_ids"]) for row in proof["context_checks"]}
    if len({row["id"] for row in snapshot["observations"]}) != len(snapshot["observations"]):
        raise ValueError("duplicate_report_observation")
    for row in snapshot["observations"]:
        if not set(row["excerpt_ids"]) <= set(by_id) or row["context"] not in contexts or not set(row["excerpt_ids"]) <= contexts[row["context"]]:
            raise ValueError("observation_context_or_excerpt_unbound")
        quoted = "\n".join(by_id[key]["text"] for key in row["excerpt_ids"])
        if not re.search(r"(?<![\d.])" + re.escape(row["value"]) + r"(?![\d.])", quoted):
            raise ValueError("observation_numeric_token_unbound")
        if row["unit"] == "percentage" and not re.search(r"(?<![\d.])" + re.escape(row["value"]) + r"\s*%", quoted):
            raise ValueError("observation_percentage_unit_unbound")


def verify_report_archive_proof(source_proof: dict, snapshot: dict, *, root: Path = ROOT) -> None:
    """Full local verification; callers must not infer trust from inline flags."""
    if source_proof.get("work_id") != snapshot.get("work_id") or source_proof.get("source_record_id") != snapshot.get("source_record_id"):
        raise ValueError("report_source_work_identity_mismatch")
    attestations = source_proof.get("report_text_attestations", [])
    matches = [row for row in attestations if row.get("attestation_id") == snapshot.get("attestation_id")]
    if len(matches) != 1:
        raise ValueError("report_attestation_not_unique")
    attestation = matches[0]
    proof = attestation["proof"]
    if any(proof.get(key) != value for key, value in PINNED_GEN15.items()):
        raise ValueError("archive_proof_differs_from_pinned_public_anchor")
    if set(proof) != set(PINNED_GEN15) | {"context_checks", "excerpt_positions", "observations_digest"}:
        raise ValueError("unexpected_public_archive_proof_fields")
    for check in proof["context_checks"]:
        if set(check) != {"context", "start", "end", "sha256", "excerpt_ids"} or check.get("context") not in {ICL_CONTEXT, FT_CONTEXT}:
            raise ValueError("unexpected_archive_context_fields")
    if not str(proof.get("archive_html_path", "")).startswith("data/raw/organizations/") or source_proof.get("cache_ref") != proof["archive_html_path"]:
        raise ValueError("report_cache_outside_registered_raw_scope")
    allowed_source = {"work_id", "source_record_id", "source_type", "url", "retrieved_at", "raw_sha256", "hash_scope", "byte_count", "content_sha256", "cache_ref", "report_text_attestations"}
    if set(source_proof) != allowed_source or source_proof.get("content_sha256") != snapshot.get("content_sha256"):
        raise ValueError("unexpected_source_fields_or_content_hash")
    if source_proof.get("source_type") != "official_report_text_archive" or source_proof.get("url") != snapshot["source_url"] or source_proof.get("retrieved_at") != snapshot["captured_at"]:
        raise ValueError("source_record_archive_scope_mismatch")
    raw = _safe_local(root, proof["archive_html_path"]).read_bytes()
    if source_proof.get("raw_sha256") != proof["archive_content_sha256"] or source_proof.get("hash_scope") != "http_response_body_bytes" or source_proof.get("byte_count") != len(raw):
        raise ValueError("source_record_raw_hash_mismatch")
    status_blob = _git_status(root, proof)
    deployment = _safe_local(root, proof["deployment_proof_path"]).read_bytes()
    text = check_archive_materials(proof, raw, status_blob, deployment, snapshot["source_url"], snapshot["report_url"])
    _validate_public_snapshot(snapshot, attestation, text)


def make_gen15_records(proof: dict, text: str, byte_count: int, *, captured_at: str, verified_at: str) -> tuple[dict, dict]:
    """Construct only six short slices; full text never enters returned rows."""
    positions = [
        ("gen15:icl-seconds", 4465, 4480), ("gen15:no-training", 4508, 4528),
        ("gen15:icl-success", 6404, 6407), ("gen15:adapted-success", 6558, 6561),
        ("gen15:adaptation-budget", 6582, 6650), ("gen15:short-task-scope", 1192, 1216),
    ]
    excerpts = [{"excerpt_id": key, "text": text[start:end], "start": start, "end": end,
                 "locator": SELECTOR + "@data-search; DOM decode then html.unescape; Unicode codepoints"} for key, start, end in positions]
    proof = {**proof, "excerpt_positions": [{key: row[key] for key in ["excerpt_id", "start", "end", "locator"]} for row in excerpts],
             "context_checks": [
                 {"context": ICL_CONTEXT, "start": 4390, "end": 6510, "sha256": sha256(text[4390:6510].encode()),
                  "excerpt_ids": ["gen15:icl-seconds", "gen15:no-training", "gen15:icl-success", "gen15:short-task-scope"]},
                 {"context": FT_CONTEXT, "start": 6510, "end": 7100, "sha256": sha256(text[6510:7100].encode()),
                  "excerpt_ids": ["gen15:adapted-success", "gen15:adaptation-budget", "gen15:short-task-scope"]},
             ]}
    excerpt_digest = digest(excerpts)
    identity = {"work_id": WORK_ID, "content_sha256": proof["extracted_text_sha256"], "excerpt_digest": excerpt_digest,
                "available_at": proof["deploy_completed_at"], "captured_at": captured_at, "verified_at": verified_at}
    source_id = "source:report-archive:" + digest(identity)[:24]
    attestation_id = "report-attestation:" + digest({**identity, "source_record_id": source_id})[:24]
    observations = [
        {"id": "gen15-icl-success", "label": "平均成功率", "value": "59", "unit": "percentage", "context": ICL_CONTEXT,
         "excerpt_ids": ["gen15:icl-success", "gen15:icl-seconds", "gen15:no-training", "gen15:short-task-scope"]},
        {"id": "gen15-adapted-success", "label": "平均成功率", "value": "83", "unit": "percentage", "context": FT_CONTEXT,
         "excerpt_ids": ["gen15:adapted-success", "gen15:adaptation-budget", "gen15:short-task-scope"]},
        {"id": "gen15-demo-seconds-min", "label": "示教时长下限（秒）", "value": "3", "unit": "count", "context": ICL_CONTEXT,
         "excerpt_ids": ["gen15:icl-seconds", "gen15:no-training", "gen15:short-task-scope"]},
        {"id": "gen15-demo-seconds-max", "label": "示教时长上限（秒）", "value": "12", "unit": "count", "context": ICL_CONTEXT,
         "excerpt_ids": ["gen15:icl-seconds", "gen15:no-training", "gen15:short-task-scope"]},
        {"id": "gen15-gradient-steps", "label": "梯度更新步数", "value": "10", "unit": "count", "context": FT_CONTEXT,
         "excerpt_ids": ["gen15:adaptation-budget", "gen15:short-task-scope"]},
        {"id": "gen15-demo-minutes", "label": "每任务示教时长（分钟）", "value": "5", "unit": "count", "context": FT_CONTEXT,
         "excerpt_ids": ["gen15:adaptation-budget", "gen15:short-task-scope"]},
        {"id": "gen15-demo-count", "label": "每任务示教次数（约数）", "value": "50", "unit": "count", "context": FT_CONTEXT,
         "excerpt_ids": ["gen15:adaptation-budget", "gen15:short-task-scope"]},
    ]
    proof["observations_digest"] = digest(observations)
    snapshot = {"work_id": WORK_ID, "manifestation_id": MANIFESTATION_ID, "report_url": REPORT_URL, "source_url": SOURCE_URL,
                "source_record_id": source_id, "attestation_id": attestation_id, "report_published_at": "2026-08-19", "report_date_precision": "day",
                "captured_at": captured_at, "available_at": proof["deploy_completed_at"], "date_precision": "second",
                "content_sha256": proof["extracted_text_sha256"], "excerpts": excerpts, "excerpt_digest": excerpt_digest, "observations": observations,
                "license": "copyrighted_excerpt_only", "evidence_scope": "author_report", "review_status": "source_content_checked",
                "context_kind": "ai_extracted_context", "verified_by": VERIFIER, "verified_at": verified_at}
    snapshot["snapshot_id"] = "report-text:" + digest(snapshot)[:24]
    attestation = {key: snapshot[key] for key in ["attestation_id", "report_url", "source_url", "report_published_at", "report_date_precision", "captured_at", "available_at", "date_precision", "content_sha256", "excerpt_digest", "verified_by", "verified_at"]}
    attestation.update(status="verified", verification_scope=SOURCE_SCOPE, basis="git_archive", proof=proof)
    source = {"work_id": WORK_ID, "source_record_id": source_id, "source_type": "official_report_text_archive", "url": SOURCE_URL,
              "retrieved_at": captured_at, "raw_sha256": proof["archive_content_sha256"], "hash_scope": "http_response_body_bytes", "byte_count": byte_count,
              "content_sha256": proof["extracted_text_sha256"], "cache_ref": proof["archive_html_path"], "report_text_attestations": [attestation]}
    _validate_public_snapshot(snapshot, attestation, text)
    return source, snapshot


def extract_gen15(*, root: Path = ROOT) -> tuple[dict, dict]:
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    proof = dict(PINNED_GEN15)
    raw = _safe_local(root, RAW_PATH).read_bytes()
    status_blob = _git_status(root, proof)
    deployment_blob = _safe_local(root, DEPLOY_PATH).read_bytes()
    text = check_archive_materials(proof, raw, status_blob, deployment_blob, SOURCE_URL, REPORT_URL)
    verified_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return make_gen15_records(proof, text, len(raw), captured_at=captured_at, verified_at=verified_at)


def register_report_archive_proofs(payload: dict, proofs: list[dict], additions: list[dict], *, root: Path = ROOT) -> dict:
    """Copy-on-write registration; identical registered proofs need no raw cache.

    CI can use the persisted global attestation after initial local validation.
    Changed IDs, dangling work/version references and inline self-proofs fail.
    """
    validate_total_excerpt_quota(additions)
    sources = {row["source_record_id"]: row for row in payload.get("source-records", [])}
    works = {row["work_id"]: row for row in payload.get("works", [])}
    versions = {row["manifestation_id"]: row for row in payload.get("manifestations", [])}
    def resolve_work(identifier):
        if identifier in works:
            return identifier
        matches = {key for key, row in works.items() if identifier in row.get("aliases", [])}
        matches.update(row["work_id"] for row in payload.get("work-aliases", []) if row.get("alias") == identifier and row.get("work_id") in works)
        if len(matches) != 1:
            raise ValueError("report_archive_work_alias_missing_or_ambiguous")
        return next(iter(matches))
    pending = []
    seen = set()
    for row in proofs:
        sid, original_wid = row["source_record_id"], row["work_id"]
        wid = resolve_work(original_wid)
        if sid in seen:
            raise ValueError("duplicate_report_archive_proof")
        seen.add(sid)
        source = {key: value for key, value in row.items() if key != "work_id"}
        if sid in sources:
            if sources[sid] != source or wid not in works or sid not in works[wid].get("source_record_ids", []):
                raise ValueError("registered_report_archive_source_conflict")
            continue
        matching = [item for item in additions if item.get("source_record_id") == sid and item.get("work_id") == original_wid]
        if wid not in works or len(matching) != 1:
            raise ValueError("report_archive_work_or_snapshot_missing")
        snapshot = matching[0]
        version = versions.get(snapshot.get("manifestation_id"), {})
        if version.get("work_id") != wid or version.get("kind") != "technical_report" or version.get("url") != snapshot.get("report_url"):
            raise ValueError("report_archive_manifestation_mismatch")
        verify_report_archive_proof(row, snapshot, root=root)
        pending.append((wid, source, snapshot, original_wid))
    if not pending:
        return payload
    result = {**payload, "source-records": [*payload.get("source-records", []), *(source for _, source, _, _ in pending)],
              "reconciliation": list(payload.get("reconciliation", [])), "field-provenance": list(payload.get("field-provenance", []))}
    changed = {}
    for wid, source, snapshot, original_wid in pending:
        work = changed.setdefault(wid, {**works[wid], "source_record_ids": list(works[wid].get("source_record_ids", []))})
        work["source_record_ids"] = sorted(set(work["source_record_ids"]) | {source["source_record_id"]})
        result["reconciliation"].append({"source_record_id": source["source_record_id"], "work_id": wid,
            "status": "matched_report_archive", "basis": "archive_content_check", "original_work_id": original_wid,
            "snapshot_id": snapshot["snapshot_id"]})
        for field in ["excerpts", "available_at"]:
            result["field-provenance"].append({"work_id": wid, "field": f"report_text.{snapshot['snapshot_id']}.{field}",
                "source_record_id": source["source_record_id"], "observed_at": snapshot["verified_at"],
                "basis": "archive_content_check", "original_work_id": original_wid})
    result["works"] = [changed.get(row["work_id"], row) for row in payload.get("works", [])]
    return result


def _read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Fully verify saved proofs against Git and local HTML, without writing")
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--proofs", type=Path, default=ROOT / "data/report-archive-proofs.jsonl")
    parser.add_argument("--additions", type=Path, default=ROOT / "data/report-text-additions.jsonl")
    args = parser.parse_args(argv)
    if not args.verify:
        source, snapshot = extract_gen15(root=args.repository)
        print(json.dumps({"source_proof": source, "snapshot": snapshot}, ensure_ascii=False, sort_keys=True))
        return 0
    proofs, additions = _read_rows(args.proofs), _read_rows(args.additions)
    validate_total_excerpt_quota(additions)
    verified = []
    for proof in proofs:
        matches = [row for row in additions if row.get("source_record_id") == proof["source_record_id"]]
        if len(matches) != 1:
            raise ValueError("saved_proof_snapshot_not_unique")
        verify_report_archive_proof(proof, matches[0], root=args.repository)
        verified.append({"source_record_id": proof["source_record_id"], "snapshot_id": matches[0]["snapshot_id"],
                         "public_words": lexical_word_count(row["text"] for row in matches[0]["excerpts"]), "available_at": matches[0]["available_at"]})
    print(json.dumps({"status": "source_content_verified", "semantic_review": "not_performed", "records": verified}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
