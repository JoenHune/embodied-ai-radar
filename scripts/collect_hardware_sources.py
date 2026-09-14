#!/usr/bin/env python3
"""Acquire official arXiv HTML bodies into a PRIVATE resumable cache.

This is source acquisition, not a hardware assertion or a human full-paper
review. No PDF fallback, search proxy, API crawl, authentication workaround,
or parallel requests are used. Exported observations never contain body text.

Examples (run from the repository root)::

    python3 scripts/collect_hardware_sources.py --work-ids arxiv:2407.02648
    python3 scripts/collect_hardware_sources.py --queue queue.jsonl --limit 100 \
        --observations .research/hardware-fulltext/observations.jsonl

Queue rows are work IDs or objects with ``work_id`` and optional ``arxiv_id``
and ``version`` consistency constraints. IDs and explicit versions must be
backed by the canonical works / text-snapshots tables. A work with no known
version uses the unversioned official HTML URL; the returned version must be
identifiable before the body can be classified full_text_available.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
PARSER_VERSION = "arxiv-html-body-v2"
ARXIV_RE = re.compile(r"^(\d{4}\.\d{4,5}|[a-zA-Z][a-zA-Z.\-]+/\d{7})(v[1-9]\d*)?$")
SECTION_SELECTOR = "section, .ltx_section, .ltx_subsection, .ltx_subsubsection, .ltx_appendix"
OMITTED_TITLE = re.compile(r"^(?:abstract|references|bibliography|related\s+works?|prior\s+works?|literature\s+review)(?:\b|$)", re.I)
REMOVALS = ("script, style, noscript, nav, header, footer, [role=navigation], "
            ".ltx_bibliography, .ltx_biblist, .ltx_bibitem, .ltx_cite, .ltx_abstract, "
            ".ltx_authors, .ltx_TOC, .ltx_page_header, .ltx_page_footer, .ltx_dates")


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: bytes):
    return hashlib.sha256(value).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def utc_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def utc_from_timestamp(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean(value):
    return re.sub(r"\s+", " ", value).strip()


def arxiv_identity(value):
    """Strict ID / official URL parsing: not a substring search in arbitrary text."""
    value = str(value or "").strip()
    if value.startswith("arXiv:") or value.startswith("arxiv:"):
        value = value.split(":", 1)[1]
    if "://" in value:
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in {"arxiv.org", "www.arxiv.org"}:
            return None
        match = re.fullmatch(r"/(?:abs|html|pdf)/(.+?)/?", parsed.path)
        if not match:
            return None
        value = urllib.parse.unquote(match.group(1)).removesuffix(".pdf")
    match = ARXIV_RE.fullmatch(value)
    return (match.group(1), match.group(2)) if match else None


def table_rows(catalog: Path, table: str):
    directory = catalog / table
    paths = sorted(directory.glob("*.jsonl")) if directory.is_dir() else [catalog / f"{table}.jsonl"]
    for path in paths:
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def load_targets(catalog: Path, queue):
    """Resolve selected IDs only through canonical identity and version evidence."""
    requests = [({"work_id": row} if isinstance(row, str) else row) for row in queue]
    if any(not isinstance(row, dict) or not row.get("work_id") for row in requests):
        raise ValueError("Every queue entry must have a canonical work_id")
    wanted = {row["work_id"] for row in requests}
    works = {row["work_id"]: row for row in table_rows(catalog, "works") if row["work_id"] in wanted}
    versions = {}
    for row in table_rows(catalog, "text-snapshots"):
        wid = row.get("work_id")
        if wid not in works:
            continue
        identity = arxiv_identity(row.get("source_url"))
        canonical = arxiv_identity(works[wid].get("identifiers", {}).get("arxiv"))
        if identity and canonical and identity[0] == canonical[0] and identity[1] == row.get("version"):
            versions.setdefault(wid, set()).add(identity[1])
    result, seen = [], set()
    for row in requests:
        wid = row["work_id"]
        if wid in seen:
            continue
        seen.add(wid)
        if wid not in works:
            raise ValueError(f"Unknown canonical work_id: {wid}")
        identity = arxiv_identity(works[wid].get("identifiers", {}).get("arxiv"))
        if not identity:
            # Identity absence is an explicit acquisition failure, not guessed
            # from a DOI, title, work_id string, or a noncanonical queue URL.
            result.append({"work_id": wid, "arxiv_id": None, "version": None,
                           "source_url": None, "resolution_error": "no_canonical_arxiv_identity"})
            continue
        aid, canonical_version = identity
        known = versions.get(wid, set()) - {None}
        if canonical_version:
            known.add(canonical_version)
        supplied = arxiv_identity(row.get("arxiv_id")) if row.get("arxiv_id") else None
        if row.get("arxiv_id") and (not supplied or supplied[0] != aid):
            raise ValueError(f"Queue arxiv_id contradicts canonical identity: {wid}")
        requested_version = row.get("version") or (supplied[1] if supplied else None)
        if requested_version is not None:
            requested_version = str(requested_version)
            if not requested_version.startswith("v"):
                requested_version = "v" + requested_version
            if requested_version not in known:
                raise ValueError(f"Queue version lacks canonical evidence: {wid} {requested_version}")
        version = requested_version or (max(known, key=lambda item: int(item[1:])) if known else None)
        result.append({"work_id": wid, "arxiv_id": aid, "version": version,
                       "version_basis": "canonical_explicit" if version else "resolve_from_official_html",
                       "source_url": f"https://arxiv.org/html/{aid}{version or ''}"})
    return result


def read_queue(path: Path):
    source = path.read_text(encoding="utf-8")
    try:
        value = json.loads(source)
    except json.JSONDecodeError:
        return [json.loads(line) for line in source.splitlines() if line.strip()]
    if isinstance(value, dict):
        for key in ("queue", "works", "items", "work_ids"):
            if key in value:
                return value[key]
        return [value]
    if not isinstance(value, list):
        raise ValueError("Queue must be a JSON array, queue object, or JSONL")
    return value


def page_identity(soup, effective_url, expected_id, expected_version):
    proofs = []
    for node in soup.find_all("meta", attrs={"name": re.compile(r"^citation_arxiv_id$", re.I)}):
        identity = arxiv_identity(node.get("content"))
        if identity:
            proofs.append(("citation_arxiv_id", identity))
    for node in soup.find_all(["link", "a"], href=True):
        href = urllib.parse.urljoin(effective_url, node["href"])
        parsed = urllib.parse.urlparse(href)
        if not parsed.path.startswith("/abs/"):
            continue
        # Never use a bibliographic paper link as a page-identity proof.
        rel = set(node.get("rel", []))
        in_body = node.find_parent("article") or node.find_parent(class_="ltx_document")
        original_link = "link-original" in node.get("class", [])
        canonical = node.name == "link" and "canonical" in rel
        outside_original = node.name == "a" and not in_body and (original_link or node.find_parent(["header", "nav"]))
        if not (canonical or outside_original):
            continue
        identity = arxiv_identity(href)
        if identity:
            proofs.append(("canonical_abs_link" if canonical else "original_abs_link", identity))
    effective = arxiv_identity(effective_url)
    if not effective or effective[0] != expected_id:
        return False, None, proofs, "effective_url_identity_mismatch"
    if not proofs:
        return False, None, proofs, "missing_page_identity_proof"
    if any(identity[0] != expected_id for _, identity in proofs):
        return False, None, proofs, "page_identity_mismatch"
    returned_versions = {identity[1] for _, identity in proofs if identity[1]}
    if effective[1]:
        returned_versions.add(effective[1])
    if len(returned_versions) > 1 or (expected_version and returned_versions and expected_version not in returned_versions):
        return False, None, proofs, "page_version_mismatch"
    version = next(iter(returned_versions), None)
    if expected_version and not version:
        return False, None, proofs, "missing_requested_version_proof"
    return True, version, proofs, None


def normalized_heading(title):
    return re.sub(r"^(?:(?:(?i:appendix)\s+)?(?:\d+(?:\.\d+)*|[IVX]+|[A-Z])[.:]?\s+)+", "", clean(title))


def extract_blocks(soup):
    document = soup.select_one("article.ltx_document, .ltx_document, article")
    if document is None:
        return [], False
    for node in list(document.select(REMOVALS)):
        if node.parent is not None:
            node.decompose()
    for section in list(document.select(SECTION_SELECTOR)):
        if section.parent is None:
            continue
        heading = section.find(re.compile("^h[1-6]$"))
        title = clean(heading.get_text(" ", strip=True)) if heading else ""
        if OMITTED_TITLE.match(normalized_heading(title)):
            section.decompose()
    sections = list(document.select(SECTION_SELECTOR))
    section_keys = {id(node): index for index, node in enumerate(sections)}
    titles = []
    for index, node in enumerate(sections):
        heading = node.find(re.compile("^h[1-6]$"))
        titles.append({"section_id": node.get("id") or f"section-{index + 1}",
                       "section_title": clean(heading.get_text(" ", strip=True)) if heading else "Untitled section"})
    buckets = {}
    for node in document.find_all(string=True):
        if isinstance(node, Comment) or not clean(str(node)):
            continue
        if node.find_parent(re.compile("^h[1-6]$")):
            continue
        parent = node.parent
        while parent is not None and parent is not document and id(parent) not in section_keys:
            parent = parent.parent
        index = section_keys.get(id(parent), -1)
        buckets.setdefault(index, []).append(str(node))
    blocks = []
    for index, strings in buckets.items():
        text = clean(" ".join(strings))
        if text:
            meta = titles[index] if index != -1 else {"section_id": "body", "section_title": "Unsectioned body"}
            blocks.append({**meta, "text": text})
    return blocks, True


def assess_html(raw, target, effective_url, *, min_body_characters=1500, min_sections=2):
    soup = BeautifulSoup(raw, "html.parser")
    title = clean(soup.title.get_text(" ", strip=True)) if soup.title else ""
    challenge = (not soup.select_one("article.ltx_document, .ltx_document, article") and
                 (re.search(r"^(?:access denied|just a moment|verify you are human|captcha|attention required)", title, re.I) or
                  soup.select_one("#cf-chl-widget, .g-recaptcha, #challenge-form")))
    valid, version, proofs, error = page_identity(soup, effective_url, target["arxiv_id"], target.get("version"))
    common = {"version": version, "identity_proofs": [{"kind": kind, "arxiv_id": aid, "version": ver} for kind, (aid, ver) in proofs],
              "thresholds": {"min_body_characters": min_body_characters, "min_sections": min_sections,
                             "max_conversion_error_markers_for_available": 4, "max_response_bytes": 30_000_000},
              "parser_version": PARSER_VERSION, "manual_reviewed": False,
              "scope": "body", "text_scope": "main_document_text_excluding_references_related_work",
              "images_not_inspected": True, "supplementary_materials_not_inspected": True,
              "excluded_sections": ["abstract", "references", "bibliography", "related work", "prior work", "literature review"],
              "limitations": ["HTML text only; images, audio, video and conversion completeness are not verified"]}
    if challenge:
        return {**common, "status": "blocked", "error": "html_access_challenge", "body_characters": 0, "section_count": 0}, []
    if not valid:
        return {**common, "status": "identity_mismatch", "error": error, "body_characters": 0, "section_count": 0}, []
    if not urllib.parse.urlparse(effective_url).path.startswith("/html/"):
        return {**common, "status": "unavailable", "error": "not_official_html_body_url", "body_characters": 0, "section_count": 0}, []
    conversion_errors = len(soup.select(".ltx_ERROR, .ltx_error"))
    blocks, structured = extract_blocks(soup)
    body_characters = sum(len(block["text"]) for block in blocks)
    section_count = sum(block["section_id"] != "body" for block in blocks)
    common.update(body_characters=body_characters, section_count=section_count, structured_document=structured,
                  conversion_error_markers=conversion_errors)
    if not structured or not body_characters:
        return {**common, "status": "unavailable", "error": "no_structured_html_body"}, blocks
    reasons = []
    if not version:
        reasons.append("version_unresolved")
    if body_characters < min_body_characters:
        reasons.append("body_below_character_threshold")
    if section_count < min_sections:
        reasons.append("body_below_section_threshold")
    if conversion_errors >= 5:
        reasons.append("conversion_error_markers_at_least_5")
    return {**common, "status": "partial_text" if reasons else "full_text_available",
            "error": ";".join(reasons) if reasons else None}, blocks


class OfficialRedirectsOnly(urllib.request.HTTPRedirectHandler):
    max_redirections = 3
    max_repeats = 2

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in {"arxiv.org", "www.arxiv.org"}:
            raise urllib.error.HTTPError(req.full_url, 403, "Refusing non-official redirect", headers, fp)
        # Redirects are requests too; urllib otherwise follows them immediately.
        deadline = time.time() + max(3, retry_after_seconds(dict(headers.items()), time.time()))
        while time.time() < deadline:
            time.sleep(min(30, deadline - time.time()))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_html(url, timeout=20):
    request = urllib.request.Request(url, headers={"User-Agent": "embodied-ai-hardware-source-audit/1.0 (single request; 3s minimum interval)", "Accept": "text/html"})
    opener = urllib.request.build_opener(OfficialRedirectsOnly())
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(30_000_001)
            return {"http_status": response.status, "effective_url": response.url,
                    "headers": dict(response.headers.items()), "raw": raw[:30_000_000],
                    "truncated": len(raw) > 30_000_000}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "effective_url": exc.geturl(), "headers": dict(exc.headers.items()) if exc.headers else {},
                "raw": exc.read(1_000_000), "error": f"HTTP {exc.code}: {exc.reason}"}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"http_status": None, "effective_url": url, "headers": {}, "raw": b"", "error": f"{type(exc).__name__}: {exc}"}


def fetch_html_curl(url, timeout=20):
    """Alternate TLS-validating transport, with no redirects or auto retries."""
    if not arxiv_identity(url):
        raise ValueError('Official arXiv URL required')
    with tempfile.TemporaryDirectory(prefix='radar-hardware-http-') as directory:
        body, headers_path = Path(directory) / 'body', Path(directory) / 'headers'
        try:
            result = subprocess.run(['curl', '--silent', '--show-error', '--proto', '=https',
                '--retry', '0', '--connect-timeout', str(timeout), '--max-time', str(timeout),
                '--max-filesize', '30000000', '--user-agent', 'embodied-ai-hardware-source-audit/1.0 (3s minimum interval)',
                '--dump-header', str(headers_path), '--output', str(body), '--write-out', '%{http_code}', url],
                capture_output=True, text=True, timeout=timeout + 5, check=False)
            raw = body.read_bytes() if body.exists() else b''
            headers = {}
            for line in (headers_path.read_text(errors='replace') if headers_path.exists() else '').splitlines():
                if line.startswith('HTTP/'):
                    headers = {}
                elif ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            code = int(result.stdout[-3:]) if result.stdout[-3:].isdigit() and result.stdout[-3:] != '000' else None
            return {'http_status': code, 'effective_url': url, 'headers': headers, 'raw': raw[:30_000_000],
                    'truncated': len(raw) > 30_000_000 or result.returncode == 63,
                    'transport_returncode': result.returncode,
                    'error': f'curl_transport_error:{result.returncode}' if result.returncode else None}
        except (OSError, subprocess.TimeoutExpired) as error:
            return {'http_status': None, 'effective_url': url, 'headers': {}, 'raw': b'', 'error': type(error).__name__}


def retry_after_seconds(headers, now):
    value = next((value for key, value in headers.items() if key.lower() == "retry-after"), None)
    if value is None:
        return 0
    try:
        return max(0, float(value))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(0, parsed.timestamp() - now)
        except (ValueError, TypeError, OverflowError):
            return 0


def transport_incomplete(record):
    """Preserve known transport failures when cached bytes are reparsed offline."""
    return (record.get('transport_complete') is False or
            bool(record.get('transport_truncated') or record.get('truncated')) or
            any(record.get(key) not in (None, 0, '0') for key in ('transport_returncode', 'curl_exit_code')) or
            str(record.get('error') or '').startswith('curl_transport_error:'))


def constrain_transport(assessment, provenance):
    if assessment['status'] in {'full_text_available', 'partial_text'} and transport_incomplete(provenance):
        reasons = [reason for reason in (assessment.get('error'), 'incomplete_transport_cached_response') if reason]
        return {**assessment, 'status': 'partial_text', 'error': ';'.join(reasons)}
    return assessment


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


class Collector:
    """One process / one request; persistent global pacing and append-only export."""
    def __init__(self, cache_dir, observations, *, interval=3, timeout=20, min_body_characters=1500, min_sections=2,
                 fetcher=fetch_html, clock=time.time, sleeper=time.sleep):
        if interval < 3:
            raise ValueError("Official arXiv request interval must be at least 3 seconds")
        self.cache = Path(cache_dir).resolve()
        self.observations = Path(observations).resolve()
        self.interval, self.timeout = interval, timeout
        self.min_body_characters, self.min_sections = min_body_characters, min_sections
        self.fetcher, self.clock, self.sleeper = fetcher, clock, sleeper
        self.cache.mkdir(parents=True, exist_ok=True)
        self.pacing_file = self.cache / "pacing.json"
        self.exported = set()
        if self.observations.exists():
            raw_export = self.observations.read_bytes()
            offset = 0
            lines = raw_export.splitlines(keepends=True)
            for index, line in enumerate(lines):
                if line.strip():
                    try:
                        self.exported.add(json.loads(line)["observation_id"])
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        if index != len(lines) - 1:
                            raise ValueError("Observation export contains corruption before its last line")
                        # Preserve the interrupted append, then restore the valid
                        # JSONL prefix. Request state re-exports the missing row.
                        tail = self.observations.with_name(self.observations.name + ".interrupted-tail." + digest(line)[:12])
                        atomic_write(tail, line)
                        atomic_write(self.observations, raw_export[:offset])
                offset += len(line)
            if self.observations.stat().st_size and not self.observations.read_bytes().endswith(b"\n"):
                with self.observations.open("ab") as handle:
                    handle.write(b"\n")

    def state_path(self, target):
        key = digest(encode([target["work_id"], target["source_url"], PARSER_VERSION,
                             self.min_body_characters, self.min_sections]).encode())
        return self.cache / "requests" / f"{key}.json"

    def export(self, row):
        if row["observation_id"] not in self.exported:
            self.observations.parent.mkdir(parents=True, exist_ok=True)
            with self.observations.open("a", encoding="utf-8") as handle:
                handle.write(encode(row) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.exported.add(row["observation_id"])

    def _wait(self):
        state = json.loads(self.pacing_file.read_text()) if self.pacing_file.exists() else {}
        deadline = state.get("next_request_at", 0)
        while deadline > self.clock():
            self.sleeper(min(30, deadline - self.clock()))

    def _pace(self, seconds):
        atomic_write(self.pacing_file, encode({"next_request_at": self.clock() + max(self.interval, seconds)}).encode())

    def collect(self, target, *, retry_failed=False):
        state_path = self.state_path(target)
        previous = json.loads(state_path.read_text()) if state_path.exists() else None
        if previous:
            self.export(previous)
            if not retry_failed or previous["status"] == "full_text_available":
                return previous, False
            if previous.get("next_retry_at") and utc_timestamp(previous["next_retry_at"]) > self.clock():
                return previous, False
        row = {**target, "observed_at": utc_from_timestamp(self.clock()), "effective_url": target.get("source_url"),
               "raw_sha256": None, "text_sha256": None, "cache_ref": None, "blocks_ref": None, "body_cache_ref": None,
               "body_characters": 0, "section_count": 0, "manual_reviewed": False, "parser_version": PARSER_VERSION,
               "text_scope": "main_document_text_excluding_references_related_work", "images_not_inspected": True,
               "supplementary_materials_not_inspected": True,
               "transport_verification": "not_requested",
               "attempt": previous.get("attempt", 0) + 1 if previous else 1}
        if target.get("resolution_error"):
            row.update(status="unavailable", error=target["resolution_error"], http_status=None)
        else:
            self._wait()
            # Persist a conservative reservation before I/O: process interruption
            # cannot cause the next invocation to immediately retry the request.
            self._pace(self.timeout + self.interval)
            response = self.fetcher(target["source_url"], timeout=self.timeout)
            row.update(observed_at=utc_from_timestamp(self.clock()), effective_url=response["effective_url"], http_status=response["http_status"],
                       transport_returncode=response.get('transport_returncode'),
                       transport_truncated=bool(response.get('truncated')),
                       transport_complete=(response['http_status'] == 200 and not response.get('error') and
                                           not response.get('transport_returncode', 0) and not response.get('truncated')))
            row['transport_verification'] = 'complete' if row['transport_complete'] else 'incomplete'
            raw = response.get("raw", b"")
            if raw:
                row["raw_sha256"] = digest(raw)
                raw_path = self.cache / "objects" / f"{row['raw_sha256']}.html"
                atomic_write(raw_path, raw)
                row["cache_ref"] = str(raw_path)
            code = response["http_status"]
            delay = retry_after_seconds(response.get("headers", {}), self.clock())
            if code in {403, 429}:
                delay = max(delay, 900 if code == 403 else 60 * 2 ** min(row["attempt"] - 1, 6))
                row.update(status="blocked", error=response.get("error") or f"HTTP {code}", next_retry_at=utc_from_timestamp(self.clock() + delay))
            elif code != 200 or response.get("error") or response.get("transport_returncode", 0):
                # An HTTP 200 header does not certify a completed transfer.
                # curl can retain a parseable prefix then exit with e.g. 18
                # (partial transfer), 28 (timeout), or 63 (size limit). Keep
                # those raw bytes privately for diagnostics, never promote
                # them through assess_html into an available-body record.
                if code is None or code >= 500 or response.get("error") or response.get("transport_returncode", 0):
                    delay = max(delay, 60 * 2 ** min(row["attempt"] - 1, 6))
                row.update(status="unavailable", error=response.get("error") or
                           (f"transport_error:{response['transport_returncode']}" if response.get("transport_returncode") else f"HTTP {code}"),
                           next_retry_at=utc_from_timestamp(self.clock() + max(delay, 3600)))
            else:
                assessment, blocks = assess_html(raw, target, response["effective_url"],
                                                 min_body_characters=self.min_body_characters, min_sections=self.min_sections)
                row.update(assessment)
                if row["status"] == "blocked":
                    delay = max(delay, 900)
                    row["next_retry_at"] = utc_from_timestamp(self.clock() + delay)
                if response.get("truncated") and row["status"] in {"full_text_available", "partial_text"}:
                    row.update(status="partial_text", error="response_exceeded_30000000_byte_cap")
                if blocks:
                    body = "\n\n".join(block["text"] for block in blocks).encode("utf-8")
                    row["text_sha256"] = digest(body)
                    blocks_path = self.cache / "objects" / f"{row['raw_sha256']}.{PARSER_VERSION}.blocks.json"
                    body_path = self.cache / "objects" / f"{row['text_sha256']}.txt"
                    atomic_write(blocks_path, (encode(blocks) + "\n").encode())
                    atomic_write(body_path, body)
                    row.update(blocks_ref=str(blocks_path), body_cache_ref=str(body_path))
            self._pace(delay)
        row["observation_id"] = "hardware-source:" + digest(encode(row).encode())[:32]
        atomic_write(state_path, (encode(row) + "\n").encode())
        self.export(row)
        return row, True

    def run(self, targets, *, limit=100, retry_failed=False):
        # fcntl lock is kernel-released on interruption, unlike a stale lockfile.
        import fcntl
        with (self.cache / "collector.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("Another collector owns this cache; concurrent arXiv collection is prohibited") from exc
            counts, attempted, resumed = {}, 0, 0
            for target in targets:
                if attempted >= limit:
                    break
                row, fresh = self.collect(target, retry_failed=retry_failed)
                attempted += int(fresh)
                resumed += int(not fresh)
                counts[row["status"]] = counts.get(row["status"], 0) + 1
                print(encode({"work_id": row["work_id"], "status": row["status"], "resumed": not fresh,
                              "error": row.get("error"), "attempted": attempted}), flush=True)
                if row["status"] == "blocked" and fresh:
                    break  # No host cycling or same-run retry after 403 / 429.
            return {"attempted": attempted, "resumed": resumed, "statuses": counts,
                    "observations": str(self.observations), "manual_reviewed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--work-ids", nargs="+")
    source.add_argument("--queue", type=Path)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".research/hardware-fulltext")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--limit", type=int, default=100, help="Maximum NEW observations per run; resume does not consume limit")
    parser.add_argument("--interval", type=float, default=3, help="Minimum seconds between requests, never below 3")
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--min-body-characters", type=int, default=1500)
    parser.add_argument("--min-sections", type=int, default=2)
    parser.add_argument("--retry-failed", action="store_true", help="Revisit failed observations only after saved cooldown")
    parser.add_argument("--transport", choices=['urllib', 'curl'], default='curl')
    parser.add_argument("--dry-run", action="store_true", help="Resolve identities/versions and print targets without I/O")
    args = parser.parse_args(argv)
    if args.limit < 1 or args.timeout <= 0 or args.min_body_characters < 1 or args.min_sections < 1:
        parser.error("limit, timeout, and body/section thresholds must be positive")
    if args.interval < 3:
        parser.error("--interval must be at least 3 seconds")
    if not args.cache_dir.resolve().is_relative_to((ROOT / ".research").resolve()):
        parser.error("Raw body cache must stay in the git-ignored repository .research directory")
    try:
        targets = load_targets(args.catalog, read_queue(args.queue) if args.queue else args.work_ids)
        if args.dry_run:
            print(encode({"resolved_targets": len(targets), "limit": args.limit, "targets": targets[:args.limit]}))
            return 0
        collector = Collector(args.cache_dir, args.observations or args.cache_dir / "observations.jsonl",
                              interval=args.interval, timeout=args.timeout,
                              fetcher=fetch_html_curl if args.transport == 'curl' else fetch_html,
                              min_body_characters=args.min_body_characters, min_sections=args.min_sections)
        print(encode(collector.run(targets, limit=args.limit, retry_failed=args.retry_failed)))
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"collector: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
