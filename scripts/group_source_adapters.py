"""Read publication data embedded in registered pages' public script resources.

Remote JavaScript is never executed. A small literal grammar accepts strings,
numbers, booleans, null, arrays and objects; expressions are rejected. Resource
discovery is restricted to script tags read on the registered page, on the same
origin or an explicitly registered resource origin.
"""
from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

MAX_RESOURCE_BYTES = 5_000_000
MAX_LITERAL_BYTES = 100_000
FIELDS = {"title", "authors", "conference", "paperLink", "projectLink", "codeLink", "datasetLink", "dataLink", "modelsLink", "modelLink", "benchmarkLink", "announcementLink"}
LINK_FIELDS = ("paperLink", "projectLink", "codeLink", "datasetLink", "dataLink", "modelsLink", "modelLink", "benchmarkLink", "announcementLink")


class NotLiteral(ValueError):
    pass


def origin(url: str) -> str:
    try:
        parts = urlsplit(url)
        if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username or parts.password:
            return ""
        return f"{parts.scheme.lower()}://{parts.netloc.lower()}"
    except ValueError:
        return ""


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts, self.inline_json, self.current_json = [], [], None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "script":
            return
        values = dict(attrs)
        if values.get("src"):
            self.scripts.append(values["src"])
        if values.get("type", "").lower() in {"application/json", "application/ld+json"}:
            self.current_json = []

    def handle_data(self, data):
        if self.current_json is not None:
            self.current_json.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.current_json is not None:
            self.inline_json.append("".join(self.current_json))
            self.current_json = None


def discover_publication_scripts(page_url: str, html: str, allowed_resource_origins=()) -> list[str]:
    parser = ResourceParser()
    parser.feed(html)
    allowed = {origin(page_url), *(origin(value) for value in allowed_resource_origins)} - {""}
    result = []
    for src in parser.scripts:
        try:
            url = urljoin(page_url, src)
        except ValueError:
            continue
        if not origin(url):
            continue
        path = urlsplit(url).path
        if origin(url) in allowed and re.search(r"(?:publication|project|research)[^/]*\.(?:m?js|json)$", path, re.I):
            result.append(url)
    return list(dict.fromkeys(result))


def string_literal(text: str, start: int) -> tuple[str, int]:
    quote = text[start]
    if quote not in {'"', "'"}:
        raise NotLiteral("not_a_string")
    result, index = [], start + 1
    escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
    while index < len(text):
        char = text[index]
        index += 1
        if char == quote:
            try:
                value = "".join(result).encode("utf-16-le", "surrogatepass").decode("utf-16-le")
            except UnicodeDecodeError as exc:
                raise NotLiteral("invalid_surrogate_pair") from exc
            return value, index
        if char in "\r\n":
            raise NotLiteral("unescaped_newline")
        if char != "\\":
            result.append(char)
            continue
        if index >= len(text):
            raise NotLiteral("unfinished_escape")
        escape = text[index]
        index += 1
        if escape in "\r\n":
            if escape == "\r" and index < len(text) and text[index] == "\n":
                index += 1
            continue
        if escape in {"u", "x"}:
            width = 4 if escape == "u" else 2
            if escape == "u" and index < len(text) and text[index] == "{":
                stop = text.find("}", index + 1)
                digits = text[index + 1:stop] if stop >= 0 else ""
                if not re.fullmatch(r"[0-9a-fA-F]{1,6}", digits):
                    raise NotLiteral("invalid_unicode_escape")
                index = stop + 1
            else:
                digits = text[index:index + width]
                if not re.fullmatch(r"[0-9a-fA-F]{%d}" % width, digits):
                    raise NotLiteral("invalid_unicode_escape")
                index += width
            try:
                result.append(chr(int(digits, 16)))
            except ValueError as exc:
                raise NotLiteral("invalid_unicode_escape") from exc
        elif escape in escapes:
            result.append(escapes[escape])
        elif escape in {"\\", "'", '"', "/"}:
            result.append(escape)
        else:
            raise NotLiteral("unsupported_escape")
    raise NotLiteral("unfinished_string")


def whitespace(text: str, index: int) -> int:
    while index < len(text):
        if text[index].isspace():
            index += 1
        elif text.startswith("//", index):
            stop = text.find("\n", index + 2)
            return len(text) if stop < 0 else whitespace(text, stop + 1)
        elif text.startswith("/*", index):
            stop = text.find("*/", index + 2)
            if stop < 0:
                raise NotLiteral("unfinished_comment")
            index = stop + 2
        else:
            break
    return index


def parse_literal(text: str, index: int = 0, depth: int = 0):
    if depth > 20:
        raise NotLiteral("literal_depth_limit")
    index = whitespace(text, index)
    if index >= len(text):
        raise NotLiteral("missing_value")
    char = text[index]
    if char in {"'", '"'}:
        return string_literal(text, index)
    if char in "[{":
        is_object, closing = char == "{", "}" if char == "{" else "]"
        result = {} if is_object else []
        index = whitespace(text, index + 1)
        while index < len(text) and text[index] != closing:
            if is_object:
                if text[index] in {"'", '"'}:
                    key, index = string_literal(text, index)
                else:
                    match = re.match(r"[A-Za-z_$][A-Za-z0-9_$]*", text[index:])
                    if not match:
                        raise NotLiteral("invalid_key")
                    key, index = match.group(), index + len(match.group())
                index = whitespace(text, index)
                if index >= len(text) or text[index] != ":" or key in result:
                    raise NotLiteral("computed_or_duplicate_key")
                value, index = parse_literal(text, index + 1, depth + 1)
                result[key] = value
            else:
                value, index = parse_literal(text, index, depth + 1)
                result.append(value)
            index = whitespace(text, index)
            if index < len(text) and text[index] == ",":
                index = whitespace(text, index + 1)
            elif index >= len(text) or text[index] != closing:
                raise NotLiteral("expressions_not_allowed")
        if index >= len(text):
            raise NotLiteral("unfinished_container")
        return result, index + 1
    for word, value in [("null", None), ("true", True), ("false", False)]:
        if text.startswith(word, index) and (index + len(word) == len(text) or not text[index + len(word)].isalnum()):
            return value, index + len(word)
    match = re.match(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?", text[index:])
    if match:
        return json.loads(match.group()), index + len(match.group())
    raise NotLiteral("expressions_not_allowed")


def object_spans(text: str):
    """Find balanced objects while ignoring strings, comments and templates."""
    stack, index = [], 0
    while index < len(text):
        char = text[index]
        if char in {"'", '"'}:
            try:
                _, index = string_literal(text, index)
                continue
            except NotLiteral:
                index += 1
        elif char == "`":
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                elif text[index] == "`":
                    index += 1
                    break
                else:
                    index += 1
            continue
        elif text.startswith("//", index) or text.startswith("/*", index):
            try:
                index = whitespace(text, index)
                continue
            except NotLiteral:
                return
        elif char == "{":
            stack.append(index)
        elif char == "}" and stack:
            start = stack.pop()
            if index + 1 - start <= MAX_LITERAL_BYTES:
                yield text[start:index + 1]
        index += 1


def publication_records(value) -> list[dict]:
    rows = []
    if isinstance(value, dict):
        if isinstance(value.get("title"), str) and value["title"].strip() and any(isinstance(value.get(key), str) and origin(value[key]) for key in LINK_FIELDS):
            rows.append({key: value[key] for key in FIELDS if key in value and isinstance(value[key], (str, type(None)))})
        else:
            for child in value.values():
                rows.extend(publication_records(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(publication_records(child))
    return rows


def json_parse_values(text: str):
    """Decode only one literal-string argument at a code-position JSON.parse."""
    index = 0
    while index < len(text):
        char = text[index]
        if char in {"'", '"'}:
            try:
                _, index = string_literal(text, index)
                continue
            except NotLiteral:
                return
        if char == "`":
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                elif text[index] == "`":
                    index += 1
                    break
                else:
                    index += 1
            continue
        if text.startswith("//", index) or text.startswith("/*", index):
            try:
                index = whitespace(text, index)
                continue
            except NotLiteral:
                return
        match = re.match(r"JSON\.parse\s*\(\s*", text[index:]) if text.startswith("JSON.parse", index) else None
        if match and (index == 0 or not (text[index - 1].isalnum() or text[index - 1] in "_$")):
            try:
                value, end = string_literal(text, index + len(match.group()))
                end = whitespace(text, end)
                if end < len(text) and text[end] == ")":
                    yield json.loads(value)
                    index = end + 1
                    continue
            except (NotLiteral, ValueError, IndexError):
                pass
        index += 1


def extract_publication_literals(text: str) -> dict:
    if len(text.encode()) > MAX_RESOURCE_BYTES:
        return {"records": [], "rejected_candidate_count": 0, "formats": [], "error": "resource_size_limit"}
    records, formats, rejected, expression_objects = [], set(), 0, 0
    try:
        value = json.loads(text)
        rows = publication_records(value)
        if rows:
            records.extend(rows)
            formats.add("json")
    except (ValueError, TypeError):
        pass
    for literal in object_spans(text):
        try:
            value, end = parse_literal(literal)
            if whitespace(literal, end) != len(literal):
                raise NotLiteral("trailing_expression")
            rows = publication_records(value)
            if rows:
                records.extend(rows)
                formats.add("javascript_literal")
        except (NotLiteral, RecursionError, ValueError):
            if re.match(r"\{\s*(?:title|\"title\"|'title')\s*:", literal):
                if re.match(r"\{\s*(?:title|\"title\"|'title')\s*:\s*['\"`]", literal):
                    rejected += 1
                else:
                    # React props such as {title:a.title, ...} are renderer code,
                    # not publication literals or a failed publication record.
                    expression_objects += 1
    for value in json_parse_values(text):
        rows = publication_records(value)
        if rows:
            records.extend(rows)
            formats.add("json_parse_string")
    deduped = {json.dumps(row, sort_keys=True): row for row in records}
    return {"records": list(deduped.values()), "rejected_candidate_count": rejected, "ignored_expression_objects": expression_objects,
            "formats": sorted(formats), "error": None}


def adapt_group_publications(page_url: str, html: str, fetch_resource, *, previous_known_links=(),
                             allowed_resource_origins=(), source_kind="publications") -> dict:
    result = {"applicable": False, "links": [], "known_links": sorted(set(previous_known_links)), "parser_status": "not_applicable",
              "content_state": "ordinary_html", "empty_verified": False, "resource_urls": [], "resource_hashes": {}, "errors": [], "code_executed": False}
    if source_kind not in {"publications", "projects", "research"} or not origin(page_url):
        return result
    parser = ResourceParser()
    parser.feed(html)
    scripts = discover_publication_scripts(page_url, html, allowed_resource_origins)
    inline = []
    for body in parser.inline_json:
        try:
            inline.extend(publication_records(json.loads(body)))
        except (ValueError, TypeError):
            pass
    gear_skeleton = "/labs/gear/publications" in urlsplit(page_url).path
    if not scripts and not inline and not gear_skeleton:
        return result
    result.update(applicable=True, resource_urls=scripts, parser_status="partial", content_state="not_loaded")
    collected = [(row, page_url) for row in inline]
    rejected = 0
    for url in scripts:
        try:
            fetched = fetch_resource(url)
            if isinstance(fetched, dict):
                if fetched.get("final_url") and origin(fetched["final_url"]) not in {origin(page_url), *(origin(value) for value in allowed_resource_origins)}:
                    result["errors"].append("resource_redirect_outside_registered_origins")
                    continue
                fetched = fetched.get("text", fetched.get("body", ""))
            if isinstance(fetched, tuple):
                fetched = fetched[0]
            text = fetched.decode("utf-8") if isinstance(fetched, bytes) else fetched
            if not isinstance(text, str):
                raise ValueError("invalid_resource")
            parsed = extract_publication_literals(text)
            result["resource_hashes"][url] = hashlib.sha256(text.encode()).hexdigest()
            rejected += parsed["rejected_candidate_count"]
            if parsed["error"]:
                result["errors"].append(parsed["error"])
            collected.extend((row, url) for row in parsed["records"])
        except Exception:
            # Error bodies can contain origin credentials; publish a fixed reason only.
            result["errors"].append("resource_fetch_or_parse_failed")
    links = {}
    for record, source_url in collected:
        for field in LINK_FIELDS:
            url = record.get(field)
            if not isinstance(url, str) or not origin(url):
                continue
            links[(record["title"], url)] = {"title": record["title"], "url": url, "authors": record.get("authors"),
                                           "evidence_url": page_url, "structured_source_url": source_url,
                                           "source_excerpt": record["title"], "record_field": field}
    result["links"] = sorted(links.values(), key=lambda row: (row["title"], row["url"]))
    result["known_links"] = sorted(set(previous_known_links) | {row["url"] for row in result["links"]})
    result["record_count"] = len({row["title"] for row in result["links"]})
    result["rejected_candidate_count"] = rejected
    result["previous_links_preserved"] = all(url in result["known_links"] for url in previous_known_links)
    if result["links"]:
        result["parser_status"] = "partial" if rejected or result["errors"] else "parsed"
        result["content_state"] = "structured_publications_found"
    else:
        result["errors"].append("no_verified_publication_records_from_dynamic_source")
    return result
