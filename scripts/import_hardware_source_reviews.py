#!/usr/bin/env python3
"""Import AI section-level hardware reviews with privately cached source proof.

Default is dry-run. A review is not a whole-paper reading or a finding that
hardware was absent. Neither raw HTML, body text nor local cache paths are
published. Historical observations remain valid after an extractor revision.

Legacy observations with unversioned official URLs retain those exact URLs.
New imports of them require the cached HTML itself to prove the requested
version; the declaration or a versioned redirect alone cannot supply it.

An optional extends_review_id appends NEW usage assertions to an existing
section review of the exact same source observation. It is not a replacement,
new fetch, wider absence claim, or permission to modify existing usage rows.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from catalog_store import encode, fingerprint, load_catalog, write_if_changed
from collect_hardware_sources import arxiv_identity, page_identity
from equipment_radar import CATEGORIES, ROLES, COMPUTE_ROLES, SETTINGS, USAGE_SCOPES, TABLES, load_equipment_authority
from import_equipment_reviews import merge_equipment_reviews
from people_radar import _hard_identity

ROOT = Path(__file__).resolve().parents[1]
LEVELS = {"model_specified", "family_only", "unspecified"}
DECISIONS = {"verified_use", "no_explicit_named_usage_in_reviewed_sections", "ambiguous"}
USE_ROLES = ROLES - {"mentioned", "dataset_source"}
HASH = re.compile(r"^[0-9a-f]{64}$")
# Explicitly reviewed product aliases, never fuzzy matching. In particular,
# neither RTX 4090D nor the old GPU/CPU composite workstation is an alias.
MODEL_NAME_ALIASES = {"nvidia geforce rtx 4090": "NVIDIA RTX 4090"}


def fail(reason):
    raise ValueError("hardware_source_review:" + reason)


def required_text(row, key, *, limit=4000):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        fail("invalid_" + key)
    return value


def normalized(value):
    return re.sub(r"\s+", " ", value.strip()).casefold()


def timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        fail("utc_timestamp_required")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail("utc_timestamp_required")


def jsonl(path):
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def source_key(row, *, review=False):
    return tuple(row.get(key) for key in ("work_id", "source_url", "source_version" if review else "version",
                                          "raw_sha256", "text_sha256", "observed_at"))


def official_source_identity(source_url, version, *, reason="versioned_official_html_url_required"):
    """Allow a legacy unversioned URL, never a contradictory version/host."""
    url = urlsplit(source_url)
    identity = arxiv_identity(source_url)
    if (url.scheme != "https" or url.hostname not in {"arxiv.org", "www.arxiv.org"} or
            url.username or url.password or url.port not in {None, 443} or url.query or url.fragment or
            not url.path.startswith("/html/") or not re.fullmatch(r"v[1-9]\d*", version) or
            identity is None or identity[1] not in {None, version}):
        fail(reason)
    return identity


def review_ledger(records):
    """Preserve legacy records while validating explicit addendum ancestry."""
    ledger = {}
    for row in records:
        rid = row.get('review_id')
        if not rid or (rid in ledger and ledger[rid] != row):
            fail('existing_section_review_conflict')
        ledger[rid] = row
    active, complete = set(), set()

    def visit(rid):
        if rid in active:
            fail('addendum_ancestry_cycle')
        if rid in complete:
            return
        active.add(rid)
        row = ledger[rid]
        if 'extends_review_id' in row:
            parent_id = required_text(row, 'extends_review_id', limit=250)
            if parent_id not in ledger:
                fail('addendum_parent_not_found:' + parent_id)
            visit(parent_id)
        active.remove(rid)
        complete.add(rid)

    for rid in ledger:
        visit(rid)
    for row in ledger.values():
        if 'extends_review_id' not in row:
            continue
        parent = ledger[row['extends_review_id']]
        if source_key(row, review=True) != source_key(parent, review=True):
            fail('addendum_parent_source_mismatch')
        if (not row.get('source_observation_id') or
                row['source_observation_id'] != parent.get('source_observation_id')):
            fail('addendum_parent_observation_mismatch')
        if timestamp(row.get('reviewed_at')) <= timestamp(parent.get('reviewed_at')):
            fail('addendum_review_not_strictly_later')
        if row.get('review_kind') != 'addendum' or row.get('addendum_scope') != 'new_semantic_usage_assertions_only':
            fail('explicit_addendum_scope_required')
        if row.get('decision') != 'verified_use' or not row.get('usage_ids'):
            fail('addendum_new_usage_assertions_required')
    return ledger


def addendum_parent(review, ledger):
    if 'extends_review_id' not in review:
        return None
    parent_id = required_text(review, 'extends_review_id', limit=250)
    if parent_id not in ledger:
        fail('addendum_parent_not_found:' + parent_id)
    parent = ledger[parent_id]
    if source_key(review, review=True) != source_key(parent, review=True):
        fail('addendum_parent_source_mismatch')
    if timestamp(review.get('reviewed_at')) <= timestamp(parent.get('reviewed_at')):
        fail('addendum_review_not_strictly_later')
    if review.get('decision') != 'verified_use' or not review.get('devices'):
        fail('addendum_new_usage_assertions_required')
    return parent


def addendum_review_id(review, parent_id, source_observation_id):
    return 'hardware-section-review:' + fingerprint(['addendum', parent_id, review['reviewed_at'],
                                                     source_key(review, review=True), source_observation_id])[:24]


def usage_semantics(entry):
    # Addenda introduce a new use, not a second citation or a configuration
    # revision of an existing use. Locator edits (including subsets or new
    # sections), prose and configuration changes cannot manufacture novelty.
    # Keep the legacy usage_id formula unchanged below: non-addendum imports
    # may still preserve their historical per-locator evidence records.
    return (entry.get('work_id'), entry.get('hardware_id'), entry.get('role'), entry.get('setting'),
            entry.get('usage_scope', 'study'), entry.get('source_url'))


def audit_addenda_lineage(section_reviews, usage_evidence, public_observations=None):
    """Public metadata only: no private HTML, cache reads, re-reading or writes.

    Legacy records without extends_review_id need no new parent or reading
    receipt. When supplied, public_observations must bind both source hashes,
    the exact historical observation ID, version, URL and observation time.
    """
    ledger = review_ledger(section_reviews)
    usage_by_id, usage_owners, semantics = {}, {}, {}
    for entry in usage_evidence:
        usage_by_id.setdefault(entry.get('usage_id'), []).append(entry)
        semantics.setdefault(usage_semantics(entry), []).append(entry)
    for rid, review in ledger.items():
        for uid in review.get('usage_ids', []):
            usage_owners.setdefault(uid, set()).add(rid)
    addenda = [review for review in ledger.values() if 'extends_review_id' in review]
    addon_usage_ids = set()
    constants = {'reviewer_kind': 'AI', 'review_scope': 'sections_only',
                 'assertion_review_scope': 'hardware_use_assertions_only', 'images_inspected': False,
                 'supplementary_materials_inspected': False, 'full_text_reviewed': False,
                 'whole_paper_hardware_absence_conclusion': False, 'review_kind': 'addendum',
                 'addendum_scope': 'new_semantic_usage_assertions_only'}
    proof_fields = ('source_observation_id', 'reviewed_at', 'review_input_hash', 'reviewer_kind', 'review_scope',
                    'assertion_review_scope', 'images_inspected', 'supplementary_materials_inspected',
                    'full_text_reviewed', 'review_kind', 'addendum_scope', 'extends_review_id')
    for review in addenda:
        rid = review['review_id']
        if rid != addendum_review_id(review, review['extends_review_id'], review['source_observation_id']):
            fail('addendum_review_id_mismatch')
        if any((review.get(key) is not value) if isinstance(value, bool) else (review.get(key) != value)
               for key, value in constants.items()):
            fail('addendum_public_scope_mismatch')
        version = required_text(review, 'source_version')
        official_source_identity(required_text(review, 'source_url'), version,
                                 reason='addendum_public_official_source_invalid')
        for key in ('raw_sha256', 'text_sha256', 'review_input_hash'):
            if not HASH.fullmatch(str(review.get(key, ''))):
                fail('addendum_public_source_hash_invalid')
        timestamp(review.get('observed_at'))
        if timestamp(review['reviewed_at']) < timestamp(review['observed_at']):
            fail('addendum_review_before_source_observation')
        selected, section_hashes = review.get('reviewed_sections'), review.get('section_text_sha256')
        if (not isinstance(selected, list) or not selected or any(not isinstance(sid, str) or not sid for sid in selected)
                or len(selected) != len(set(selected)) or not isinstance(section_hashes, dict)
                or set(section_hashes) != set(selected) or any(not HASH.fullmatch(str(value)) for value in section_hashes.values())):
            fail('addendum_public_section_hash_invalid')
        ids = review.get('usage_ids')
        if (not isinstance(ids, list) or not ids or any(not isinstance(uid, str) or not uid for uid in ids)
                or len(ids) != len(set(ids)) or type(review.get('assertion_count')) is not int
                or review['assertion_count'] != len(ids)):
            fail('addendum_public_assertion_count_invalid')
        if public_observations is not None:
            from collect_hardware_sources import transport_incomplete
            sources = [source for source in public_observations
                       if source_key(source) == source_key(review, review=True)
                       and source.get('observation_id') == review['source_observation_id']
                       and source.get('status') == 'full_text_available' and not transport_incomplete(source)]
            if not sources:
                fail('addendum_public_source_observation_mismatch')
        hardware_ids = set()
        for uid in ids:
            matches = usage_by_id.get(uid, [])
            if len(matches) != 1:
                fail('addendum_usage_missing_or_ambiguous')
            entry = matches[0]
            if usage_owners.get(uid) != {rid}:
                fail('addendum_usage_reused_by_another_review')
            if (entry.get('section_review_id') != rid or source_key(entry, review=True) != source_key(review, review=True)
                    or any(entry.get(key) != review.get(key) for key in proof_fields)
                    or entry.get('review_status') != 'verified'):
                fail('addendum_usage_parent_proof_mismatch')
            locator, section_ids = bound_locator(entry.get('source_locator'), review)
            if locator != entry['source_locator'] or entry.get('source_section_ids') != section_ids:
                fail('addendum_usage_section_binding_mismatch')
            if len(semantics[usage_semantics(entry)]) != 1:
                fail('addendum_duplicate_semantic_usage_conflict')
            hardware_ids.add(entry['hardware_id'])
            addon_usage_ids.add(uid)
        if review.get('hardware_ids') != sorted(hardware_ids):
            fail('addendum_public_hardware_links_mismatch')
    # Reject a usage claiming additive provenance with no matching public
    # addendum, even when its four-table device/use relation is otherwise valid.
    for entry in usage_evidence:
        if 'extends_review_id' in entry or entry.get('review_kind') == 'addendum':
            if entry.get('usage_id') not in addon_usage_ids:
                fail('addendum_orphan_usage_proof')
    return {'status': 'passed', 'section_review_count': len(ledger), 'addendum_review_count': len(addenda),
            'addendum_usage_count': len(addon_usage_ids), 'public_source_bindings_checked': public_observations is not None,
            'verification_scope': 'public_addendum_lineage_and_usage_proof_consistency_only',
            'private_source_reverified': False}


def private_file(reference, cache_root):
    if not isinstance(reference, str):
        fail("private_cache_reference_required")
    path = Path(reference).resolve()
    if not path.is_relative_to(Path(cache_root).resolve()) or not path.is_file():
        fail("private_cache_missing_or_outside_root")
    return path


def verify_source(review, works, history, cache_root):
    wid = required_text(review, "work_id")
    if wid not in works:
        fail("unknown_canonical_work:" + wid)
    source_url = required_text(review, "source_url")
    version = required_text(review, "source_version")
    url_identity = official_source_identity(source_url, version)
    canonical_aid = works[wid].get("identifiers", {}).get("arxiv")
    identity = _hard_identity(source_url)
    if not canonical_aid or identity != _hard_identity("https://arxiv.org/abs/" + canonical_aid):
        fail("canonical_source_identity_mismatch")
    owners = {key for key, work in works.items()
              if work.get("identifiers", {}).get("arxiv") and
              _hard_identity("https://arxiv.org/abs/" + work["identifiers"]["arxiv"]) == identity}
    if owners != {wid}:
        fail("ambiguous_canonical_source_identity")
    for key in ("raw_sha256", "text_sha256"):
        if not HASH.fullmatch(str(review.get(key, ""))):
            fail("invalid_" + key)
    if timestamp(review.get("reviewed_at")) < timestamp(review.get("observed_at")):
        fail("review_before_source_observation")
    candidates = history.get(source_key(review, review=True), [])
    observation = next((row for row in candidates if row.get("status") == "full_text_available"), None)
    if observation is None:
        fail("no_matching_available_historical_observation")
    proofs = observation.get("identity_proofs", [])
    if not any(p.get("kind") in {"citation_arxiv_id", "canonical_abs_link", "original_abs_link"} and
               _hard_identity("https://arxiv.org/abs/" + str(p.get("arxiv_id", ""))) == identity and
               p.get("version") in {None, version} for p in proofs):
        fail("official_identity_proof_missing")
    if any(p.get("arxiv_id") and _hard_identity("https://arxiv.org/abs/" + p["arxiv_id"]) != identity or
           p.get("version") and p["version"] != version for p in proofs):
        fail("conflicting_identity_proof")
    raw_path = private_file(observation.get("cache_ref"), cache_root)
    raw_bytes = raw_path.read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest() != review["raw_sha256"]:
        fail("raw_cache_hash_mismatch")
    if url_identity[1] is None:
        effective_url = observation.get("effective_url") or source_url
        if official_source_identity(effective_url, version)[0] != url_identity[0]:
            fail("raw_page_identity_or_version_mismatch:effective_url_identity_mismatch")
        # Deliberately pass the observed unversioned URL, not a versioned
        # redirect, so page_identity must obtain vN from the actual HTML.
        valid, resolved_version, _, reason = page_identity(
            BeautifulSoup(raw_bytes, "html.parser"), source_url, url_identity[0], version)
        if not valid or resolved_version != version:
            fail("raw_page_identity_or_version_mismatch:" + str(reason))
    blocks = json.loads(private_file(observation.get("blocks_ref"), cache_root).read_text(encoding="utf-8"))
    if not isinstance(blocks, list) or not blocks:
        fail("body_blocks_required")
    block_map = {}
    for block in blocks:
        sid = required_text(block, "section_id")
        required_text(block, "text", limit=5_000_000)
        if sid in block_map:
            fail("ambiguous_section_id")
        block_map[sid] = block
    body = "\n\n".join(block["text"] for block in blocks).encode("utf-8")
    if hashlib.sha256(body).hexdigest() != review["text_sha256"]:
        fail("body_blocks_hash_mismatch")
    selected = review.get("reviewed_sections")
    if (not isinstance(selected, list) or not selected or any(not isinstance(x, str) for x in selected) or
            len(set(selected)) != len(selected) or not set(selected) <= set(block_map)):
        fail("reviewed_sections_not_bound_to_source")
    return observation, {sid: hashlib.sha256(block_map[sid]["text"].encode()).hexdigest() for sid in selected}


def bound_locator(value, review):
    if not isinstance(value, str) or not value.strip():
        fail("source_locator_required")
    sections = []
    for locator in value.split(";"):
        locator = locator.strip()
        if "://" in locator:
            base, separator, fragment = locator.partition("#")
            if base != review["source_url"] or not separator:
                fail("source_locator_url_mismatch")
            locator = fragment
        if locator not in review["reviewed_sections"]:
            fail("source_locator_outside_reviewed_sections")
        sections.append(locator)
    if len(sections) != len(set(sections)):
        fail("duplicate_source_locator")
    return "; ".join(sections), sections


def resolve_device(assertion, review, devices, owners, proposed):
    reported_name = required_text(assertion, "name", limit=250)
    name = MODEL_NAME_ALIASES.get(normalized(reported_name), reported_name)
    vendor = required_text(assertion, "vendor", limit=250)
    category, level = assertion.get("category"), assertion.get("identity_level")
    if category not in CATEGORIES or level not in LEVELS:
        fail("device_category_or_identity_level_invalid")
    wid = review["work_id"]

    def compatible(row, *, explicit=False):
        labels = [row["name"], *row.get("aliases", [])] if explicit else [row["name"]]
        return (normalized(name) in {normalized(MODEL_NAME_ALIASES.get(normalized(label), label)) for label in labels} and
                row["category"] == category and row["identity_level"] == level and
                normalized(str(row.get("vendor", ""))) == normalized(vendor))

    given = assertion.get("hardware_id")
    if given:
        row = devices.get(given)
        if not row or not compatible(row, explicit=True):
            fail("explicit_hardware_id_identity_mismatch:" + str(given))
        if level != "model_specified" and (row.get("identity_context_work_id") not in {None, wid} or
                                           owners.get(given, set()) - {wid}):
            fail("uncertain_hardware_identity_cross_work")
        if level != "model_specified" and row.get("identity_context_work_id") != wid and owners.get(given) != {wid}:
            fail("uncertain_hardware_identity_has_no_work_context")
        owners.setdefault(given, set()).add(wid)
        return given
    named = [row for row in devices.values() if row["category"] == category and
             normalized(MODEL_NAME_ALIASES.get(normalized(row["name"]), row["name"])) == normalized(name) and row["identity_level"] == level and
             (level == "model_specified" or row.get("identity_context_work_id") == wid)]
    if len(named) > 1 or (named and not compatible(named[0])):
        fail("ambiguous_or_conflicting_named_device:" + name)
    if named:
        hid = named[0]["hardware_id"]
        if level != "model_specified" and owners.get(hid, set()) - {wid}:
            fail("uncertain_hardware_identity_cross_work")
        owners.setdefault(hid, set()).add(wid)
        return hid
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:90] or category
    identity_key = [normalized(name), category, normalized(vendor), level]
    suffix = "-" + fingerprint([wid, *identity_key])[:10] if level != "model_specified" else ""
    slug = base + suffix
    if "hardware:" + slug in devices:
        slug = base + "-" + fingerprint(identity_key)[:12]
    hid = "hardware:" + slug
    if hid in devices:
        fail("generated_device_id_conflict")
    row = {"hardware_id": hid, "slug": slug, "name": name, "vendor": vendor, "category": category,
           "identity_level": level, "official_url": review["source_url"], "aliases": []}
    if name == "NVIDIA RTX 4090":
        row["aliases"] = ["NVIDIA GeForce RTX 4090"]
    if level != "model_specified":
        row["identity_context_work_id"] = wid
    devices[hid] = row
    proposed.append(row)
    owners.setdefault(hid, set()).add(wid)
    return hid


def prepare_reviews(raw, payload, existing, observations, cache_root, *, existing_section_reviews=()):
    if raw.get("schema_version") != "1" or not isinstance(raw.get("reviews"), list):
        fail("unsupported_schema")
    works = {row["work_id"]: row for row in payload["works"]}
    history = {}
    for row in observations:
        history.setdefault(source_key(row), []).append(row)
    proposed = {table: [] for table in TABLES}
    devices = {row["hardware_id"]: copy.deepcopy(row) for row in existing["devices"]}
    owners = {}
    for row in existing["usage-evidence"]:
        owners.setdefault(row["hardware_id"], set()).add(row["work_id"])
    parents = review_ledger(existing_section_reviews)
    known_usage = {}
    for row in existing['usage-evidence']:
        known_usage.setdefault(usage_semantics(row), []).append(row)
    public, seen = [], set()
    for review in sorted(raw["reviews"], key=lambda row: (row.get("work_id", ""), row.get("source_url", ""))):
        if review.get("review_scope") != "hardware_use_assertions_only" or review.get("reviewer_kind", "AI") != "AI":
            fail("explicit_AI_section_assertion_scope_required")
        if review.get("images_inspected") is not False or review.get("supplementary_materials_inspected") is not False:
            fail("uninspected_media_scope_required")
        decision = review.get("decision")
        assertions = review.get("devices")
        if decision not in DECISIONS or not isinstance(assertions, list):
            fail("invalid_review_decision")
        if (decision == "verified_use") != bool(assertions):
            fail("decision_assertion_conflict")
        parent = addendum_parent(review, parents)
        observation, section_hashes = verify_source(review, works, history, cache_root)
        identity = source_key(review, review=True)
        if parent is not None:
            if (observation.get('observation_id') != parent.get('source_observation_id') or
                    ('source_observation_id' in review and review['source_observation_id'] != observation.get('observation_id'))):
                fail('addendum_parent_observation_mismatch')
            review_id = addendum_review_id(review, parent['review_id'], observation['observation_id'])
            duplicate_key = ('addendum', review_id)
        else:
            # No extends field: retain the exact legacy ID and behavior.
            review_id = "hardware-section-review:" + fingerprint(identity)[:24]
            duplicate_key = ('base', identity)
        if duplicate_key in seen:
            fail("duplicate_source_review")
        seen.add(duplicate_key)
        proof = {"reviewer_kind": "AI", "review_scope": "sections_only", "assertion_review_scope": "hardware_use_assertions_only",
                 "images_inspected": False, "supplementary_materials_inspected": False, "full_text_reviewed": False,
                 "raw_sha256": review["raw_sha256"], "text_sha256": review["text_sha256"],
                 "source_observation_id": required_text(observation, "observation_id"),
                 "reviewed_at": review["reviewed_at"], "review_input_hash": fingerprint(review)}
        if parent is not None:
            proof.update(extends_review_id=parent['review_id'], review_kind='addendum',
                         addendum_scope='new_semantic_usage_assertions_only')
        usage_ids, hardware_ids = [], set()
        for assertion in assertions:
            for field in ("name", "vendor", "role", "setting", "usage_scope", "configuration", "validation_context", "statement_zh"):
                required_text(assertion, field)
            if assertion["role"] not in USE_ROLES or assertion["setting"] not in SETTINGS or assertion["usage_scope"] not in USAGE_SCOPES:
                fail("unknown_or_nonusage_role_setting_scope")
            if assertion["role"] in COMPUTE_ROLES and assertion["category"] != "compute_platform":
                fail("compute_role_category_mismatch")
            locator, section_ids = bound_locator(assertion.get("source_locator"), review)
            hid = resolve_device(assertion, review, devices, owners, proposed["devices"])
            entry = {"work_id": review["work_id"], "hardware_id": hid, "role": assertion["role"],
                     "setting": assertion["setting"], "usage_scope": assertion["usage_scope"],
                     "reported_device_name": assertion["name"], "reported_role": assertion["role"], "reported_roles": [assertion["role"]],
                     "configuration": assertion["configuration"], "validation_context": assertion["validation_context"],
                     "source_url": review["source_url"], "source_version": review["source_version"], "source_locator": locator,
                     "source_section_ids": section_ids, "source_kind": "paper", "review_status": "verified",
                     "work_url": "https://arxiv.org/abs/" + works[review["work_id"]]["identifiers"]["arxiv"],
                     "statement": assertion["statement_zh"], "observed_at": review["observed_at"],
                     "section_review_id": review_id, **proof}
            key = [entry[key] for key in ("work_id", "hardware_id", "role", "setting", "usage_scope", "source_url", "source_locator")]
            entry["usage_id"] = "usage:" + fingerprint(key)[:24]
            if entry["usage_id"] in usage_ids:
                fail("duplicate_usage_assertion")
            semantic_key = usage_semantics(entry)
            if parent is not None:
                for previous in known_usage.get(semantic_key, []):
                    # Re-applying this exact already-imported addendum is
                    # idempotent. Any other same-semantic assertion (including
                    # altered prose/configuration or another timestamp) fails.
                    if previous.get('section_review_id') != review_id or previous != entry:
                        fail('addendum_duplicate_semantic_usage_conflict')
            known_usage.setdefault(semantic_key, []).append(entry)
            proposed["usage-evidence"].append(entry)
            usage_ids.append(entry["usage_id"])
            hardware_ids.add(hid)
        record = {"schema_version": "1", "review_id": review_id, "work_id": review["work_id"],
                  "source_url": review["source_url"], "source_version": review["source_version"],
                  "observed_at": review["observed_at"], "reviewed_sections": review["reviewed_sections"],
                  "section_text_sha256": section_hashes, "decision": decision, "assertion_count": len(usage_ids),
                  "usage_ids": sorted(usage_ids), "hardware_ids": sorted(hardware_ids),
                  "whole_paper_hardware_absence_conclusion": False, **proof}
        for key in ("review_note_zh", "excluded_evidence_zh"):
            if key in review:
                record[key] = required_text(review, key)
        public.append(record)
    return proposed, public


def import_source_reviews(raw, payload, directory, observation_path, review_path, *, apply=False, cache_root=None):
    """Preflight all four authority tables and the public ledger before writing."""
    existing = load_equipment_authority(directory)
    existing_reviews = jsonl(review_path)
    observations = jsonl(observation_path)
    proposed, section_reviews = prepare_reviews(raw, payload, existing, observations,
                                                cache_root or Path(observation_path).parent,
                                                existing_section_reviews=existing_reviews)
    merged = merge_equipment_reviews(payload, existing, proposed)
    # Preserve every existing public review; a changed assertion requires a
    # deliberate resolution, never a last-row-wins overwrite.
    ledger = review_ledger([*existing_reviews, *section_reviews])
    usage_ids = {row["usage_id"] for row in merged["usage-evidence"]}
    if any(not set(row.get("usage_ids", [])) <= usage_ids for row in ledger.values()):
        fail("section_review_usage_link_missing")
    audit_addenda_lineage(list(ledger.values()), merged['usage-evidence'], observations)
    if apply:
        # Loco tables were fully validated above but are not reserialized, so
        # the original files (including any formatting) remain byte-for-byte.
        for table in ("devices", "usage-evidence"):
            write_if_changed(Path(directory) / (table + ".jsonl"), "".join(encode(row) + "\n" for row in merged[table]))
        write_if_changed(Path(review_path), "".join(encode(ledger[rid]) + "\n" for rid in sorted(ledger)))
    return {"applied": apply, "counts": {table: len(merged[table]) for table in TABLES},
            "added": {table: len(merged[table]) - len(existing[table]) for table in TABLES},
            "review_batch_count": len(section_reviews), "public_section_review_count": len(ledger),
            "verified_use_review_count": sum(row["decision"] == "verified_use" for row in section_reviews),
            "imported_assertion_count": len(proposed["usage-evidence"]), "reviewer_kind": "AI", "review_scope": "sections_only"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--observations", type=Path, default=ROOT / ".research/hardware-fulltext/observations.jsonl")
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog")
    parser.add_argument("--equipment", type=Path, default=ROOT / "data/equipment")
    parser.add_argument("--section-reviews", type=Path, default=ROOT / "data/hardware-review/section-reviews.jsonl")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload, _ = load_catalog(args.catalog)
        result = import_source_reviews(json.loads(args.input.read_text(encoding="utf-8")), payload, args.equipment,
                                       args.observations, args.section_reviews, apply=args.apply, cache_root=args.cache_root)
        print(encode(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, "hardware source review import failed: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
