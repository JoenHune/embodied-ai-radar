"""Bounded arXiv status extraction, separate from weekly collection.

Official format/policy references:
https://github.com/arXiv/arxiv-browse/blob/develop/browse/templates/abs/abs.html
https://info.arxiv.org/help/withdraw.html
https://info.arxiv.org/help/api/user-manual.html

extract_arxiv_status is pure: a staging notice, None for no explicit signal,
or a {status: review_required, error_code: ...} result. Only #abs's own header
banner plus the same version's marked, UTC submission-history entry can
produce a notice. Normal publication after an earlier withdrawal is NOT
automatically reinstatement. Reasons are clipped source metadata, not claims.

Future weekly hook: refresh bounded id_list batches for known arXiv works and
compare updated_at/version/comment to the previous observation. The existing
collect_arxiv_v2 parser already reads comment, but its metadata_history keys
do not retain comment. A changed record is a fetch candidate, not a status
decision. Do not restrict this check to the current first-submission month.
This module deliberately does not change that collector or the weekly job.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

MAX_HTML_BYTES = 2_000_000
MAX_QUOTE_WORDS = 25
WORD = re.compile(r"[A-Za-z]+|\d+")  # Hyphens and timestamps count conservatively.
VERSION_URL = re.compile(r"/abs/((?:\d{4}\.\d{4,5}|[A-Za-z.-]+/\d{7}))v([1-9]\d*)")
STAMP = re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})\s+UTC\b")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class StatusExtractionError(ValueError):
    pass


def _identity(source_url, work_id):
    if not isinstance(source_url, str):
        raise StatusExtractionError("official_versioned_arxiv_url_required")
    url = urlsplit(source_url)
    match = VERSION_URL.fullmatch(url.path)
    if url.scheme != "https" or url.netloc != "arxiv.org" or url.query or url.fragment or not match:
        raise StatusExtractionError("official_versioned_arxiv_url_required")
    base, version = match.group(1), "v" + match.group(2)
    if work_id != "arxiv:" + base:
        raise StatusExtractionError("work_identity_mismatch")
    return base, version


def _utc(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value):
        raise StatusExtractionError("observation_must_be_utc")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StatusExtractionError("invalid_observation_time") from exc


class _Node:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def has_class(self, name):
        return name in (self.attrs.get("class") or "").split()

    def text(self):
        if self.tag in {"script", "style", "template"}:
            return ""
        return re.sub(r"\s+", " ", " ".join(child.text() if isinstance(child, _Node) else child for child in self.children)).strip()

    def descendants(self):
        for child in self.children:
            if isinstance(child, _Node):
                yield child
                if child.tag not in {"script", "style", "template"}:
                    yield from child.descendants()


class _Tree(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = _Node("document")
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _history(history):
    text = history.text()
    markers = list(re.finditer(r"\[v([1-9]\d*)\]", text))
    rows = {}
    for index, marker in enumerate(markers):
        version = "v" + marker.group(1)
        if version in rows:
            raise StatusExtractionError("duplicate_submission_history_version")
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        segment = text[marker.start():end].strip()
        after_marker = segment[len(marker.group(0)):]
        date_start = len(marker.group(0)) + len(after_marker) - len(after_marker.lstrip())
        match = STAMP.match(segment, date_start)
        if not match:
            rows[version] = {"text": segment, "time": None}
            continue
        weekday, day, month, year, hour, minute, second = match.groups()
        try:
            timestamp = datetime(int(year), MONTHS.index(month) + 1, int(day), int(hour), int(minute), int(second), tzinfo=timezone.utc)
        except ValueError as exc:
            raise StatusExtractionError("invalid_submission_history_time") from exc
        if timestamp.strftime("%a") != weekday:
            raise StatusExtractionError("submission_history_weekday_mismatch")
        tail = segment[match.end():]
        states = set(re.findall(r"\((withdrawn|reinstated)\)", tail, re.I))
        rows[version] = {"text": segment, "time": timestamp, "states": {state.lower() for state in states},
                         "date_end": match.end(), "status_start": match.end()}
    return rows


def _check_page_identity(nodes, base, version):
    heads = [node for node in nodes if node.tag == "head"]
    if len(heads) != 1:
        raise StatusExtractionError("page_head_missing_or_ambiguous")
    version_proof = False
    for node in heads[0].descendants():
        if node.tag == "title":
            match = re.match(r"\[([^\]]+)\]", node.text())
            if match:
                if match.group(1) != base + version:
                    raise StatusExtractionError("page_version_identity_mismatch")
                version_proof = True
        elif node.tag == "meta" and node.attrs.get("property") == "og:url":
            if node.attrs.get("content") != f"https://arxiv.org/abs/{base}{version}":
                raise StatusExtractionError("page_version_identity_mismatch")
            version_proof = True
        elif node.tag == "meta" and node.attrs.get("name") == "citation_arxiv_id":
            if node.attrs.get("content") not in {base, base + version}:
                raise StatusExtractionError("page_work_identity_mismatch")
    if not version_proof:
        raise StatusExtractionError("page_version_identity_missing")


def _excerpts(header, history_row, state, comments):
    excerpts = []
    def add(text, start, end, locator, label):
        excerpts.append({"label": label, "text": text[start:end], "start": start, "end": end,
                         "locator": locator, "offset_scope": "normalized_element_text_codepoints"})
    header_match = re.match(r"This (?:paper|submission) has been (?:withdrawn|reinstated)", header, re.I)
    add(header, 0, header_match.end(), "#abs > span.error", "official_status_banner")
    add(history_row["text"], 0, history_row["date_end"], f".submission-history [{history_row['version']}]", "official_version_timestamp")
    marker = re.search(r"\(" + state + r"\)", history_row["text"], re.I)
    add(history_row["text"], marker.start(), marker.end(), f".submission-history [{history_row['version']}]", "official_version_status")
    remaining = MAX_QUOTE_WORDS - sum(len(WORD.findall(row["text"])) for row in excerpts)
    if remaining < 0:
        raise StatusExtractionError("required_source_excerpts_exceed_budget")
    if comments and remaining:
        words = list(WORD.finditer(comments))
        end = min(len(comments), 160, words[remaining - 1].end() if len(words) > remaining else len(comments))
        if end and len(WORD.findall(comments[:end])) <= remaining:
            add(comments, 0, end, "#abs .comments", "comments_metadata_fragment")
            excerpts[-1]["truncated"] = end < len(comments)
            excerpts[-1]["interpretation"] = "source_metadata_only_not_a_verified_causal_explanation"
    return excerpts


def extract_arxiv_status(html, source_url, work_id, observed_at):
    """Return a verified structural notice, None, or a review-required record.

    work_id must be the exact arxiv:<base-id> identity (the importer can then
    resolve that unique alias to a DOI canonical work). No title fuzzy-match.
    """
    valid_url = valid_work = valid_observed = None
    try:
        base, version = _identity(source_url, work_id)
        valid_url, valid_work = source_url, work_id
        observed = _utc(observed_at)
        valid_observed = observed_at
        if not isinstance(html, str) or len(html.encode("utf-8")) > MAX_HTML_BYTES:
            raise StatusExtractionError("invalid_or_oversize_html")
        tree = _Tree(html)
        nodes = list(tree.root.descendants())
        _check_page_identity(nodes, base, version)
        abs_nodes = [node for node in nodes if node.attrs.get("id") == "abs"]
        histories = [node for node in nodes if node.has_class("submission-history") and node.parent and node.parent.has_class("leftcolumn")]
        if len(abs_nodes) != 1 or len(histories) != 1:
            raise StatusExtractionError("official_page_structure_missing_or_ambiguous")
        headers = []
        for child in abs_nodes[0].children:
            if not isinstance(child, _Node):
                continue
            if child.has_class("dateline") or child.has_class("title") or child.tag == "blockquote":
                break
            if child.tag == "span" and child.has_class("error"):
                headers.append(child.text())
        if len(headers) > 1:
            raise StatusExtractionError("ambiguous_official_status_banner")
        rows = _history(histories[0])
        row = rows.get(version)
        if not row:
            raise StatusExtractionError("requested_version_missing_from_history")
        header = headers[0] if headers else ""
        if re.match(r"A newer version of this paper has been withdrawn\b", header, re.I):
            newer = [int(key[1:]) for key, value in rows.items() if int(key[1:]) > int(version[1:]) and "withdrawn" in value.get("states", set())]
            result = {"status": "review_required", "error_code": "newer_version_withdrawn_not_requested_version", "work_id": work_id,
                      "source_url": source_url, "observed_at": observed_at}
            if newer:
                result["suggested_source_url"] = f"https://arxiv.org/abs/{base}v{max(newer)}"
            return result
        match = re.match(r"This (?:paper|submission) has been (withdrawn|reinstated)\b", header, re.I)
        comments_nodes = [node for node in abs_nodes[0].descendants() if node.tag == "td" and node.has_class("comments")]
        comments = comments_nodes[0].text() if len(comments_nodes) == 1 else ""
        if not match:
            if header or any(value.get("states") for value in rows.values()) or re.match(r"(?:This paper has been |This submission has been )?(?:withdrawn|reinstated)\b", comments, re.I):
                raise StatusExtractionError("status_requires_explicit_matching_header_and_version")
            return None
        state = match.group(1).lower()
        if row.get("time") is None:
            raise StatusExtractionError("requested_status_version_has_no_utc_time")
        if row.get("states") != {state}:
            raise StatusExtractionError("status_banner_and_version_marker_disagree")
        if row["time"] > observed:
            raise StatusExtractionError("status_date_after_observation")
        row = {**row, "version": version}
        excerpts = _excerpts(header, row, state, comments)
        public_at = row["time"].isoformat().replace("+00:00", "Z")
        notice_id = "notice:arxiv-status:" + _digest([base, version, state])[:24]
        html_sha = _sha(html)
        source_id = "source:arxiv-status:" + _digest([base, version, state, html_sha])[:24]
        return {"notice_id": notice_id, "work_id": work_id, "event_type": state, "scope": "work",
                "public_at": public_at, "date_precision": "second", "source_record_ids": [source_id], "source_url": source_url,
                "review_status": "verified",
                "summary_zh": "arXiv官方版本页明确标记该论文已撤回；状态日期来自同版本提交历史，不采用本次采集时间。" if state == "withdrawn" else
                              "arXiv官方版本页明确标记该论文已恢复；仅记录状态变化，不代表研究结论获独立验证。",
                "source_record": {"source_record_id": source_id, "url": source_url, "source_type": "official_arxiv_status_notice",
                                  "observed_at": observed_at, "published_at": public_at, "date_precision": "second",
                                  "raw": {"work_identifiers": {"arxiv": base}, "version": version, "status": state,
                                          "html_sha256": html_sha, "hash_scope": "utf8_html_input", "excerpts": excerpts,
                                          "excerpt_word_count": sum(len(WORD.findall(item["text"])) for item in excerpts),
                                          "comments_sha256": _sha(comments) if comments else None,
                                          "comments_source_url": source_url if comments else None,
                                          "verification_scope": "machine_structural_source_check_not_independent_validation"}}}
    except StatusExtractionError as exc:
        return {"status": "review_required", "error_code": str(exc), "work_id": valid_work, "source_url": valid_url, "observed_at": valid_observed}
    except (ValueError, TypeError, UnicodeError):
        return {"status": "review_required", "error_code": "unreadable_official_status_html", "work_id": valid_work, "source_url": valid_url, "observed_at": valid_observed}


def merge_status_notice(existing, notice):
    """Keep the first identical observation; changed content conflicts, not overwrites."""
    if not isinstance(existing, list) or any(not isinstance(row, dict) or "notice_id" not in row for row in existing):
        raise StatusExtractionError("output_is_not_notice_jsonl")
    if not isinstance(notice, dict) or "notice_id" not in notice:
        raise StatusExtractionError("only_confirmed_notices_may_be_written")
    def content(row):
        value = copy.deepcopy(row)
        for field in ("observed_at", "retrieved_at"):
            value.get("source_record", {}).pop(field, None)
        return value
    matches = [row for row in existing if row["notice_id"] == notice["notice_id"]]
    if any(content(row) != content(notice) for row in matches):
        raise StatusExtractionError("notice_content_conflict_requires_review")
    return copy.deepcopy(existing if matches else [*existing, notice])


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise StatusExtractionError("official_status_redirect_requires_review")


def fetch_html(source_url):
    parsed = urlsplit(source_url)
    match = VERSION_URL.fullmatch(parsed.path)
    _identity(source_url, "arxiv:" + match.group(1) if match else None)
    request = urllib.request.Request(source_url, headers={"User-Agent": "EmbodiedResearchRadar/3 public-status-check", "Accept": "text/html"})
    with urllib.request.build_opener(_NoRedirect).open(request, timeout=30) as response:
        if response.geturl() != source_url or "text/html" not in response.headers.get("Content-Type", ""):
            raise StatusExtractionError("unexpected_official_status_response")
        body = response.read(MAX_HTML_BYTES + 1)
    if len(body) > MAX_HTML_BYTES:
        raise StatusExtractionError("invalid_or_oversize_html")
    return body.decode("utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-id", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, help="Explicit append-only staging JSONL; default is JSON stdout only")
    args = parser.parse_args(argv)
    try:
        _identity(args.url, args.work_id)  # No network request before URL/work validation.
        html = fetch_html(args.url)
        observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result = extract_arxiv_status(html, args.url, args.work_id, observed_at)
        if result is None:
            print(json.dumps({"status": "no_explicit_status", "source_url": args.url}))
            return 0
        if result.get("status") == "review_required":
            print(json.dumps(result, ensure_ascii=False))
            return 2  # Caller routes this to review; never append it to notice JSONL.
        if args.output:
            path = args.output
            if path.suffix != ".jsonl" or path.is_symlink() or path.parent.is_symlink():
                raise StatusExtractionError("explicit_nonsymlink_jsonl_output_required")
            old = path.read_text() if path.exists() else ""
            existing = [json.loads(line) for line in old.splitlines() if line.strip()]
            combined = merge_status_notice(existing, result)
            if len(combined) != len(existing):
                path.parent.mkdir(parents=True, exist_ok=True)
                # Preserve the original file's bytes and append one immutable row.
                body = old + ("\n" if old and not old.endswith("\n") else "") + json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".arxiv-status-", delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(body)
                try:
                    if (path.read_text() if path.exists() else "") != old:
                        raise StatusExtractionError("output_changed_during_status_check")
                    temporary.replace(path)
                finally:
                    temporary.unlink(missing_ok=True)
            print(json.dumps({"status": "already_recorded" if len(combined) == len(existing) else "appended", "notice_id": result["notice_id"]}))
        else:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except StatusExtractionError as exc:
        print(json.dumps({"status": "review_required", "error_code": str(exc)}))
    except urllib.error.HTTPError as exc:
        print(json.dumps({"status": "review_required", "error_code": "official_status_http_error", "http_status": exc.code}))
    except (OSError, ValueError, UnicodeError):
        print(json.dumps({"status": "review_required", "error_code": "official_status_read_failed"}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
