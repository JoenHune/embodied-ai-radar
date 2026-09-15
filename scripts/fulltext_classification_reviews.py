"""Explicit AI fulltext classification decisions, not a new classifier.

Pure copy-on-write application; no filesystem, clock, network or model calls.
Ingestion guards validate the immutable catalog-side chain. Publication must
also call audit_classification_reviews with the public receipts and ledgers.
"""
from __future__ import annotations

import copy
import math
import re

from catalog_store import fingerprint
from catalog_rules import attribution_valid, research_eligible
from collect_hardware_sources import arxiv_identity
from fulltext_reading_reviews import public_audit, versioned_read_url
from source_review_clock import utc_cutoff
from temporal_evidence import public_by
from versioned_text import validate_snapshot

SOURCE_TYPE = 'ai_fulltext_classification_review'
POINTER_FIELD = 'fulltext_classification_review'
REVIEW_VERSION = 'ai-fulltext-classification-1'
ASSURANCE = 'source_bound_AI_classification_not_human_review_or_independent_validation'
FIELDS = ('relevance.status', 'primary_direction', 'directions', 'questions', 'classification_state')
REVIEW_FIELDS = {'review_id', 'work_id', 'reviewer_kind', 'reviewed_at', 'supersedes_review_id',
                 'before', 'before_state_hash', 'after', 'proof', 'rationales'}
PROOF_FIELDS = {'reading_id', 'receipt_sha256', 'version', 'source_url', 'raw_sha256',
                'text_snapshot_id', 'text_snapshot_sha256'}
HASH = re.compile(r'[0-9a-f]{64}\Z')
STAMP = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z')
PRIVATE = re.compile(r'file://|/Users/|/home/|/private/|\.research/|[A-Za-z]:\\')


def require(condition, reason):
    if not condition:
        raise ValueError('fulltext_classification_review:' + reason)


def _text(value, *, chinese=False, maximum=2000):
    require(isinstance(value, str) and 0 < len(value.strip()) <= maximum and
            not PRIVATE.search(value) and all(c.isprintable() for c in value), 'invalid_public_text')
    if chinese:
        require(re.search(r'[\u3400-\u9fff]', value) is not None, 'chinese_reason_required')


def _time(value):
    require(isinstance(value, str) and STAMP.fullmatch(value), 'utc_timestamp_required')
    return utc_cutoff(value)


def review_state(work):
    """Only the five editable values; score / classifier_version stay outside."""
    return {'relevance.status': work.get('relevance', {}).get('status'),
            **{field: copy.deepcopy(work.get(field)) for field in FIELDS[1:]}}


def review_source_id(review_id):
    return 'source:fulltext-classification:' + fingerprint(review_id)[:24]


def _machine_metadata(value):
    require(isinstance(value, dict) and set(value) == {'score', 'classifier_version'} and
            type(value['score']) in {int, float} and math.isfinite(value['score']) and
            isinstance(value['classifier_version'], str) and bool(value['classifier_version']),
            'machine_relevance_metadata_invalid')
    return value


def _index(rows, field):
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(field), str) and row[field], 'missing_' + field)
        require(row[field] not in result, 'duplicate_' + field)
        result[row[field]] = row
    return result


def _state(value, *, after=False):
    require(isinstance(value, dict) and set(value) == set(FIELDS), 'classification_state_fields_invalid')
    require(value['relevance.status'] in {'included', 'candidate', 'manual_review', 'excluded'}, 'relevance_status_invalid')
    for field, pattern in [('directions', r'D(?:[1-9]|1[0-5])'), ('questions', r'Q(?:[0-9]|10)')]:
        codes = value[field]
        require(isinstance(codes, list) and all(isinstance(x, str) and re.fullmatch(pattern, x) for x in codes) and
                len(codes) == len(set(codes)), 'taxonomy_codes_invalid')
    primary = value['primary_direction']
    require(primary is None or isinstance(primary, str) and primary in value['directions'], 'primary_not_in_directions')
    require(value['relevance.status'] != 'included' or primary is not None, 'included_requires_primary_direction')
    require(isinstance(value['classification_state'], str), 'classification_state_invalid')
    if after:
        require(value['classification_state'] == 'ai_fulltext_reviewed', 'explicit_AI_classification_state_required')


def _review(row):
    require(isinstance(row, dict) and set(row) == REVIEW_FIELDS, 'review_schema_invalid')
    for key in ('review_id', 'work_id'):
        _text(row[key], maximum=250)
    require(row['reviewer_kind'] == 'AI', 'AI_only_review')
    _time(row['reviewed_at'])
    if row['supersedes_review_id'] is not None:
        _text(row['supersedes_review_id'], maximum=250)
        require(row['supersedes_review_id'] != row['review_id'], 'self_supersession')
    _state(row['before'])
    _state(row['after'], after=True)
    require(isinstance(row['before_state_hash'], str) and HASH.fullmatch(row['before_state_hash']) and
            fingerprint(row['before']) == row['before_state_hash'], 'before_state_hash_mismatch')
    proof = row['proof']
    require(isinstance(proof, dict) and set(proof) == PROOF_FIELDS, 'proof_schema_invalid')
    for field in ('reading_id', 'version', 'source_url', 'text_snapshot_id'):
        _text(proof[field], maximum=500)
    for field in ('receipt_sha256', 'raw_sha256', 'text_snapshot_sha256'):
        require(isinstance(proof[field], str) and HASH.fullmatch(proof[field]), 'proof_hash_invalid')
    require(re.fullmatch(r'v[1-9]\d*', proof['version']), 'proof_version_invalid')
    # This helper also rejects foreign hosts, query strings and wrong versions.
    versioned_read_url(proof['source_url'], proof['version'])
    rationales = row['rationales']
    require(isinstance(rationales, dict) and set(rationales) == set(FIELDS), 'all_reviewed_fields_need_rationales')
    for rationale in rationales.values():
        require(isinstance(rationale, dict) and set(rationale) == {'reason_zh', 'locators'}, 'rationale_schema_invalid')
        _text(rationale['reason_zh'], chinese=True)
        locators = rationale['locators']
        require(isinstance(locators, dict) and locators and all(
            isinstance(k, str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,256}', k) and
            isinstance(v, str) and HASH.fullmatch(v) for k, v in locators.items()), 'locator_hashes_required')
    return row


def active_bindings(payload):
    """Catalog-side immutable chain/state checks, safe for ingest guards.

    Does not replace the receipt/hold audit: no public ledgers are implicitly
    loaded here. An unbound pointer or a hand-edited active result fails closed.
    """
    relevant_sources = [row for row in payload.get('source-records', []) if row.get('source_type') == SOURCE_TYPE or
                        str(row.get('source_record_id', '')).startswith('source:fulltext-classification:')]
    if not relevant_sources and not any(POINTER_FIELD in work for work in payload.get('works', [])):
        return {}  # Preserve the pre-existing no-review ingestion/dedup path.
    require(all(row.get('source_type') == SOURCE_TYPE for row in relevant_sources), 'review_source_type_changed')
    works = _index(payload.get('works', []), 'work_id')
    # Existing ingest adapters append ordinary source observations before
    # finalize_facts deduplicates them. Preserve that legacy path, but never
    # let last-wins semantics hide duplicate/conflicting classification IDs.
    sources = {}
    for source in payload.get('source-records', []):
        sid = source.get('source_record_id')
        require(isinstance(sid, str) and sid, 'missing_source_record_id')
        previous = sources.get(sid)
        if previous is not None and (source.get('source_type') == SOURCE_TYPE or
                previous.get('source_type') == SOURCE_TYPE or sid.startswith('source:fulltext-classification:')):
            require(False, 'duplicate_classification_source_record_id')
        sources[sid] = source
    reviews, source_for = {}, {}
    for sid, source in sources.items():
        if source.get('source_type') != SOURCE_TYPE:
            continue
        row = _review(source.get('classification_review'))
        rid, wid = row['review_id'], row['work_id']
        require(wid in works, 'review_work_missing_or_identity_changed')
        require(rid not in reviews, 'duplicate_review_id')
        require(sid == review_source_id(rid) and source.get('payload_hash') == fingerprint(row), 'stored_review_hash_or_id_mismatch')
        require(source.get('review_id') == rid and source.get('reviewer_kind') == 'AI' and
                source.get('assurance') == ASSURANCE and source.get('reviewed_at') == row['reviewed_at'] and
                source.get('url') == versioned_read_url(row['proof']['source_url'], row['proof']['version']) and
                source.get('published_at') is None and source.get('date_precision') == 'unknown' and
                source.get('score_semantics') == 'original_machine_score_not_AI_confidence',
                'stored_review_metadata_mismatch')
        require(sid in works[wid].get('source_record_ids', []), 'review_source_not_owned')
        original_machine = _machine_metadata(source.get('preserved_machine_relevance_metadata'))
        current_machine = _machine_metadata({key: works[wid].get('relevance', {}).get(key)
                                            for key in ('score', 'classifier_version')})
        require(fingerprint(original_machine) == fingerprint(current_machine), 'machine_relevance_metadata_changed')
        reviews[rid], source_for[rid] = row, source
    bindings, claimed = {}, set()
    for wid, work in works.items():
        if POINTER_FIELD not in work:
            continue
        pointer = work[POINTER_FIELD]
        require(isinstance(pointer, dict) and set(pointer) == {'review_id', 'source_record_id', 'locked_fields'} and
                pointer['locked_fields'] == list(FIELDS), 'active_pointer_schema_invalid')
        rid = pointer['review_id']
        require(rid in reviews and source_for[rid]['source_record_id'] == pointer['source_record_id'] and
                reviews[rid]['work_id'] == wid, 'active_pointer_unbound')
        require(review_state(work) == reviews[rid]['after'], 'active_review_result_drift')
        chain, seen, current = [], set(), rid
        while current is not None:
            require(current in reviews and current not in seen, 'review_chain_missing_or_cyclic')
            seen.add(current)
            row = reviews[current]
            require(row['work_id'] == wid, 'review_chain_work_identity_changed')
            chain.append(row)
            parent = row['supersedes_review_id']
            if parent is not None:
                require(parent in reviews and row['before'] == reviews[parent]['after'] and
                        _time(row['reviewed_at']) > _time(reviews[parent]['reviewed_at']), 'invalid_review_supersession')
            current = parent
        require(not claimed.intersection(seen), 'review_chain_shared_across_works')
        claimed.update(seen)
        bindings[wid] = {'review': reviews[rid], 'source': source_for[rid], 'chain': chain,
                         'machine_classification_state': chain[-1]['before']['classification_state']}
    require(claimed == set(reviews), 'orphan_or_branching_classification_review')
    provenance = payload.get('field-provenance', [])
    for rid, row in reviews.items():
        sid = source_for[rid]['source_record_id']
        for field in FIELDS:
            matching = [p for p in provenance if (p.get('work_id'), p.get('field'), p.get('source_record_id')) ==
                        (row['work_id'], field, sid)]
            require(len(matching) == 1 and matching[0].get('review_id') == rid and
                    matching[0].get('observed_at') == row['reviewed_at'] and
                    matching[0].get('basis') == SOURCE_TYPE, 'review_field_provenance_missing_or_changed')
    return bindings


def locked_fields(payload):
    """Top-level source-ingestion fields protected by a validated active record."""
    return {wid: {field.split('.')[0] for field in FIELDS} for wid in active_bindings(payload)}


def taxonomy_projection(payload, work_ids=None):
    """The existing six-column projection, plus D/Q-only reviewed provenance."""
    bindings = active_bindings(payload)
    existing_facets = {}
    for item in payload.get('taxonomy-assignments', []):
        if item.get('work_id') in bindings and item.get('axis') not in {'direction', 'question'}:
            existing_facets.setdefault((item['work_id'], item['axis'], item['code']), []).append(item)
    rows = []
    for work in payload['works']:
        if work_ids is not None and work['work_id'] not in work_ids:
            continue
        binding = bindings.get(work['work_id'])
        for axis, values in [('direction', work.get('directions', [])), ('question', work.get('questions', [])),
                             *work.get('facets', {}).items()]:
            for code in values:
                prior_facets = existing_facets.get((work['work_id'], axis, code))
                if binding and axis not in {'direction', 'question'} and prior_facets:
                    rows.extend(copy.deepcopy(prior_facets))
                    continue
                row = {'work_id': work['work_id'], 'axis': axis, 'code': code,
                    'is_primary': axis == 'direction' and code == work.get('primary_direction'),
                    'classifier_version': work['relevance']['classifier_version'],
                    'confidence': binding['machine_classification_state'] if binding else work.get('classification_state', 'unverified')}
                if binding and axis in {'direction', 'question'}:
                    row.update(classifier_version=REVIEW_VERSION, confidence='ai_fulltext_reviewed',
                        review_id=binding['review']['review_id'], reviewer_kind='AI', assurance=ASSURANCE,
                        source_record_ids=[binding['source']['source_record_id']])
                rows.append(row)
    return rows


def _proof_context(payload, readings, observations, data_through, source_review_as_of, conflicts):
    utc_cutoff(data_through)
    _time(source_review_as_of)
    require(isinstance(conflicts, list), 'raw_conflict_ledger_required')
    from source_content_conflicts import build_source_conflicts
    visible_conflicts = build_source_conflicts(conflicts, payload, readings, observations, source_review_as_of)
    audited = public_audit(readings, payload, observations, source_review_as_of)
    return {'receipts': _index(audited['records'], 'reading_id'),
            'snapshots': _index(payload.get('text-snapshots', []), 'snapshot_id'),
            'sources': _index(payload.get('source-records', []), 'source_record_id'),
            'works': _index(payload['works'], 'work_id'), 'visible_conflicts': visible_conflicts,
            'raw_conflicts': conflicts, 'readings': readings, 'observations': observations,
            'data_through': data_through, 'source_review_as_of': source_review_as_of}


def _proof(row, context, *, new=False):
    _review(row)
    require(_time(row['reviewed_at']) <= _time(context['source_review_as_of']), 'review_after_approved_clock')
    proof = row['proof']
    receipt = context['receipts'].get(proof['reading_id'])
    require(receipt is not None, 'reading_missing_or_not_visible')
    require(fingerprint(receipt) == proof['receipt_sha256'], 'receipt_digest_mismatch')
    require(receipt['work_id'] == row['work_id'] and all(receipt.get(field) == proof[field]
            for field in ('version', 'source_url', 'raw_sha256')), 'reading_work_version_or_source_mismatch')
    require(_time(receipt['read_completed_at']) <= _time(row['reviewed_at']), 'review_precedes_reading')
    work = context['works'].get(row['work_id'])
    require(work is not None and arxiv_identity(work.get('identifiers', {}).get('arxiv')) and
            arxiv_identity(proof['source_url'])[0] == arxiv_identity(work['identifiers']['arxiv'])[0], 'canonical_identity_mismatch')
    snapshot = context['snapshots'].get(proof['text_snapshot_id'])
    require(snapshot is not None and fingerprint(snapshot) == proof['text_snapshot_sha256'], 'text_snapshot_digest_mismatch')
    require(snapshot.get('work_id') == row['work_id'] and snapshot.get('version') == proof['version'] and
            not validate_snapshot(snapshot, work, context['sources']), 'text_snapshot_identity_or_proof_invalid')
    require(snapshot.get('date_precision') in {'day', 'month', 'second'} and public_by(
            snapshot.get('available_at'), context['data_through'], snapshot.get('date_precision')), 'version_not_public_by_catalog_cutoff')
    locators = {}
    for judgment in [*receipt['findings_zh'], *receipt['limitations_zh']]:
        for locator, digest in judgment['locator_text_sha256'].items():
            require(locator not in locators or locators[locator] == digest, 'receipt_locator_conflict')
            locators[locator] = digest
    require(all(locators.get(locator) == digest for reason in row['rationales'].values()
                for locator, digest in reason['locators'].items()), 'rationale_locator_not_bound_to_reading')
    # Existing decisions retain historical validity when a later hold appears;
    # a new approval cannot evade a current hold by submitting an older date.
    from source_content_conflicts import build_source_conflicts
    holds = context['visible_conflicts'] if new else build_source_conflicts(context['raw_conflicts'],
        {'works': list(context['works'].values()), 'text-snapshots': list(context['snapshots'].values()),
         'source-records': list(context['sources'].values())}, context['readings'], context['observations'], row['reviewed_at'])
    require(not any(h['work_id'] == row['work_id'] and h['version'] == proof['version'] and
                    h.get('experimental_use') == 'hold' for h in holds), 'unresolved_source_hold')
    return receipt


def audit_classification_reviews(payload, readings, observations, *, data_through, source_review_as_of, conflicts):
    bindings = active_bindings(payload)
    utc_cutoff(data_through)
    _time(source_review_as_of)
    if not bindings:
        return {'status': 'passed', 'active_reviewed_works': 0, 'review_records': 0,
                'assurance': ASSURANCE, 'machine_score_and_classifier_version_preserved': True,
                'score_semantics': 'original_machine_score_not_AI_confidence',
                'data_through': data_through, 'source_review_as_of': source_review_as_of}
    context = _proof_context(payload, readings, observations, data_through, source_review_as_of, conflicts)
    for binding in bindings.values():
        for row in binding['chain']:
            receipt = _proof(row, context)
            source = context['sources'][review_source_id(row['review_id'])]
            require(source.get('observed_at') == receipt['observed_at'], 'source_observation_date_mismatch')
    expected = taxonomy_projection(payload, set(bindings))
    actual = [row for row in payload.get('taxonomy-assignments', []) if row.get('work_id') in bindings]
    require(sorted(actual, key=fingerprint) == sorted(expected, key=fingerprint), 'reviewed_taxonomy_projection_mismatch')
    return {'status': 'passed', 'active_reviewed_works': len(bindings),
            'review_records': sum(len(item['chain']) for item in bindings.values()),
            'assurance': ASSURANCE, 'machine_score_and_classifier_version_preserved': True,
            'score_semantics': 'original_machine_score_not_AI_confidence',
            'data_through': data_through, 'source_review_as_of': source_review_as_of}


def _refresh_events(payload, touched):
    works = {row['work_id']: row for row in payload['works']}
    links = {(row['work_id'], row['organization_id']): row for row in payload.get('work-organization-links', [])
             if attribution_valid(row, works.get(row['work_id']))}
    for event in payload.get('evidence-events', []):
        wid = event.get('work_id')
        if wid not in touched or event.get('source_type') not in {'derived_canonical_first_publication', 'official_peer_review'}:
            continue
        work, org = works[wid], event.get('organization_id')
        event.update(direction_codes=copy.deepcopy(work['directions']), question_codes=copy.deepcopy(work['questions']),
            research_eligible=bool(research_eligible(work) and event.get('evidence_layer') != 'S' and
                                  not event.get('superseded_by') and (not org or (wid, org) in links)))
        # Never clear review_required, dates, statuses or other review reasons.


def apply_classification_reviews(payload, document, readings, observations, *, data_through, source_review_as_of, conflicts):
    require(isinstance(document, dict) and set(document) == {'schema_version', 'reviews'} and
            document['schema_version'] == '1' and isinstance(document['reviews'], list) and document['reviews'], 'batch_schema_invalid')
    audit_classification_reviews(payload, readings, observations, data_through=data_through,
                                 source_review_as_of=source_review_as_of, conflicts=conflicts)
    incoming = [_review(copy.deepcopy(row)) for row in document['reviews']]
    require(len({row['review_id'] for row in incoming}) == len(incoming), 'duplicate_input_review_id')
    out = copy.deepcopy(payload)
    touched = set()
    for row in incoming:
        bindings = active_bindings(out)
        sources = _index(out['source-records'], 'source_record_id')
        sid, wid = review_source_id(row['review_id']), row['work_id']
        existing = sources.get(sid)
        if existing is not None:
            require(existing.get('source_type') == SOURCE_TYPE and existing.get('payload_hash') == fingerprint(row) and
                    existing.get('classification_review') == row, 'review_id_content_conflict')
            continue  # Historical exact replay does not restore an old result.
        works = _index(out['works'], 'work_id')
        require(wid in works, 'unknown_canonical_work_no_alias_transfer')
        work = works[wid]
        require(review_state(work) == row['before'], 'before_state_drift')
        active = bindings.get(wid)
        require(row['supersedes_review_id'] == (active['review']['review_id'] if active else None), 'explicit_active_supersession_required')
        if active:
            require(_time(row['reviewed_at']) > _time(active['review']['reviewed_at']), 'supersession_not_later')
        context = _proof_context(out, readings, observations, data_through, source_review_as_of, conflicts)
        receipt = _proof(row, context, new=True)
        original_machine = _machine_metadata({key: copy.deepcopy(work['relevance'].get(key))
                                              for key in ('score', 'classifier_version')})
        source = {'source_record_id': sid, 'source_type': SOURCE_TYPE,
            'url': versioned_read_url(row['proof']['source_url'], row['proof']['version']),
            'published_at': None, 'date_precision': 'unknown', 'observed_at': receipt['observed_at'],
            'reviewed_at': row['reviewed_at'], 'reviewer_kind': 'AI', 'review_id': row['review_id'],
            'assurance': ASSURANCE, 'payload_hash': fingerprint(row), 'classification_review': row,
            'preserved_machine_relevance_metadata': original_machine,
            'score_semantics': 'original_machine_score_not_AI_confidence'}
        out['source-records'].append(source)
        for field in FIELDS:
            out.setdefault('field-provenance', []).append({'work_id': wid, 'field': field, 'source_record_id': sid,
                'observed_at': row['reviewed_at'], 'basis': SOURCE_TYPE, 'review_id': row['review_id']})
        work['relevance']['status'] = row['after']['relevance.status']
        for field in FIELDS[1:]:
            work[field] = copy.deepcopy(row['after'][field])
        work['source_record_ids'] = [*work.get('source_record_ids', []), sid]
        work[POINTER_FIELD] = {'review_id': row['review_id'], 'source_record_id': sid, 'locked_fields': list(FIELDS)}
        touched.add(wid)
    if touched:
        projected = taxonomy_projection(out, touched)
        out['taxonomy-assignments'] = [row for row in out.get('taxonomy-assignments', []) if row.get('work_id') not in touched]
        out['taxonomy-assignments'].extend(projected)
        _refresh_events(out, touched)
    audit_classification_reviews(out, readings, observations, data_through=data_through,
                                 source_review_as_of=source_review_as_of, conflicts=conflicts)
    return out
