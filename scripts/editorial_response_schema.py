"""Compile packet-scoped restrictions without weakening the public schema.

No network/IO or fact edits. Call the existing Responses-subset converter
AFTER this function, and still run the complete editorial validator afterwards.
Official limits: https://developers.openai.com/api/docs/guides/structured-outputs
"""
from __future__ import annotations

import copy
import hashlib
import json

from jsonschema import Draft202012Validator


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def schema_budget(schema):
    """Count physical definitions once, not once per reference use."""
    count = {"enum_values": 0, "object_properties": 0, "schema_bytes": len(_encode(schema).encode()), "string_budget_characters": 0}
    large = []
    def walk(node):
        if isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, dict):
            count["enum_values"] += len(node.get("enum", []))
            count["object_properties"] += len(node.get("properties", {}))
            strings = [*node.get("properties", {}), *node.get("$defs", {}), *node.get("enum", [])]
            if "const" in node:
                strings.append(node["const"])
            count["string_budget_characters"] += sum(len(value) for value in strings if isinstance(value, str))
            if len(node.get("enum", [])) > 250:
                large.append(sum(len(value) for value in node["enum"] if isinstance(value, str)))
            for child in node.values():
                walk(child)
    walk(schema)
    def nesting(node, references=frozenset()):
        if not isinstance(node, dict):
            return 0
        if "$ref" in node:
            ref = node["$ref"]
            if ref in references:
                return 0  # A recursive definition is counted once per path.
            if ref.startswith("#/$defs/"):
                name = ref.split("/", 2)[2].replace("~1", "/").replace("~0", "~")
                return nesting(schema["$defs"][name], references | {ref})
        kinds = node.get("type", [])
        kinds = [kinds] if isinstance(kinds, str) else kinds
        children = [*node.get("properties", {}).values(), node.get("items"), *node.get("anyOf", [])]
        return int(bool(set(kinds) & {"object", "array"})) + max((nesting(child, references) for child in children), default=0)
    count["max_container_nesting"] = nesting(schema)
    count["largest_enum_over_250_string_characters"] = max(large, default=0)
    return count


def packet_response_schema(base_schema, packet, missing_summary):
    """Tighten generation IDs; never silently remove a base restriction.

    Ordinary research sections cannot cite unavailable text. Organization
    changes can cite registered organization events as metadata. Facet branches
    require their own available text or the exact missing-text placeholder.
    """
    Draft202012Validator.check_schema(base_schema)
    schema = copy.deepcopy(base_schema)
    if schema.get("type") != "object" or "anyOf" in schema:
        raise ValueError("editorial_response_root_must_be_object")
    definitions = schema.setdefault("$defs", {})
    def resolved(node):
        node = copy.deepcopy(node)
        seen = set()
        while "$ref" in node:
            ref = node["$ref"]
            if ref in seen or not ref.startswith("#/$defs/") or set(node) - {"$ref", "description", "title", "$comment"}:
                raise ValueError("unsupported_editorial_schema_reference")
            seen.add(ref)
            key = ref.split("/", 2)[2].replace("~1", "/").replace("~0", "~")
            if key not in definitions:
                raise ValueError("unknown_editorial_schema_reference")
            node = {**copy.deepcopy(definitions[key]), **{name: value for name, value in node.items() if name != "$ref"}}
        return node
    def shared(node):
        name = "packet_" + hashlib.sha256(_encode(node).encode()).hexdigest()[:18]
        if name in definitions and definitions[name] != node:
            raise ValueError("packet_schema_definition_conflict")
        definitions[name] = node
        return {"$ref": "#/$defs/" + name}
    def enum_ref(node, values):
        node = resolved(node)
        validator = Draft202012Validator({**node, "$defs": definitions})
        allowed = sorted({value for value in values if isinstance(value, str) and validator.is_valid(value)})
        if not allowed:
            return None
        return shared({**node, "enum": allowed})
    def empty(node):
        node = resolved(node)
        if node.get("minItems", 0) > 0:
            raise ValueError("base_schema_requires_nonempty_section_without_eligible_evidence")
        return {**node, "maxItems": 0}
    def ids_array(node, ids):
        array = resolved(node)
        item = enum_ref(array["items"], ids)
        return {**array, "items": item} if item else empty(array)
    def cited_object(node, ids):
        result = resolved(node)
        for field in ["supporting_ids", "counterevidence_ids"]:
            result["properties"][field] = ids_array(result["properties"][field], ids)
        return result
    def array_items(section, branches, required_count=None):
        array = resolved(schema["properties"][section])
        if required_count is not None:
            minimum = max(array.get("minItems", 0), required_count)
            maximum = min(array.get("maxItems", required_count), required_count)
            if minimum > maximum:
                raise ValueError("base_array_limits_conflict_with_required_packet_items:" + section)
            array.update(minItems=minimum, maxItems=maximum)
        schema["properties"][section] = {**array, "items": branches[0] if len(branches) == 1 else {"anyOf": branches}} if branches else empty(array)

    cards = {}
    for card in packet.get("evidence_cards", []):
        if card.get("evidence_month") != packet.get("month"):
            continue
        eid = card["evidence_id"]
        if eid in cards:
            raise ValueError("duplicate_packet_evidence_id")
        cards[eid] = card
    available = {eid for eid, card in cards.items() if card.get("experimental_text_available") is not False}
    metadata = {eid for eid, card in cards.items() if card.get("kind") == "event" and card.get("organization_id")}
    month = enum_ref(schema["properties"]["month"], [packet["month"]])
    if month is None:
        raise ValueError("packet_month_not_allowed_by_base_schema")
    schema["properties"]["month"] = month
    for section in ["claims", "counterevidence", "watchlist", "organization_changes"]:
        ids = metadata if section == "organization_changes" else available
        base = resolved(schema["properties"][section])
        array_items(section, [shared(cited_object(base["items"], ids))] if ids else [])
    for section, family, required_key in [("direction_summaries", "directions", "required_direction_codes"),
                                           ("question_summaries", "questions", "required_question_codes")]:
        base = resolved(schema["properties"][section])
        original = resolved(base["items"])
        branches = []
        for code in sorted(set(packet.get(required_key, []))):
            matching = {eid for eid, card in cards.items() if code in card.get(family, [])}
            ids = matching & available
            if not matching:
                raise ValueError("required_facet_has_no_packet_evidence:" + code)
            branch = cited_object(original, ids or matching)
            code_ref = enum_ref(branch["properties"]["code"], [code])
            if code_ref is None:
                raise ValueError("required_facet_not_allowed_by_base_schema:" + code)
            branch["properties"]["code"] = code_ref
            if not ids:
                summary = enum_ref(branch["properties"]["summary"], [missing_summary])
                if summary is None:
                    raise ValueError("missing_summary_not_allowed_by_base_schema")
                branch["properties"]["summary"] = summary
                for field in ["counterevidence_ids", "numeric_claims"]:
                    branch["properties"][field] = empty(branch["properties"][field])
            branches.append(shared(branch))
        array_items(section, branches, len(branches))
    localization_array = resolved(schema["properties"]["localizations"])
    branches = []
    for wid in sorted(set(packet.get("required_localization_ids", []))):
        card = cards.get(wid)
        if not card or card.get("kind") != "work" or wid not in available or not card.get("source_record_ids"):
            raise ValueError("required_localization_has_no_eligible_source:" + wid)
        branch = resolved(localization_array["items"])
        wid_ref = enum_ref(branch["properties"]["work_id"], [wid])
        if wid_ref is None:
            raise ValueError("required_localization_not_allowed_by_base_schema:" + wid)
        branch["properties"]["work_id"] = wid_ref
        branch["properties"]["source_ids"] = ids_array(branch["properties"]["source_ids"], card["source_record_ids"])
        branches.append(shared(branch))
    array_items("localizations", branches, len(branches))
    schema["properties"]["limitations"] = ids_array(schema["properties"]["limitations"], packet.get("known_limitations", []))
    budget = schema_budget(schema)
    if budget["enum_values"] > 1000 or budget["object_properties"] > 5000 or budget["string_budget_characters"] > 120000 or budget["largest_enum_over_250_string_characters"] > 15000 or budget["max_container_nesting"] > 10:
        raise ValueError("packet_response_schema_budget_exceeded:" + _encode(budget))
    Draft202012Validator.check_schema(schema)
    return schema
