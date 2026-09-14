"""Evidence-bound research equipment and loco-manipulation views.

These JSONL overlays describe inspected sources, never ownership, market share,
or independent validation. Name matches are discovery candidates only.
"""
from __future__ import annotations

import copy
import ipaddress
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from catalog_store import encode, fingerprint, read_table, write_if_changed
from temporal_evidence import public_day
from people_radar import _hard_identity, _work_identities

TABLES = {"devices": "hardware_id", "usage-evidence": "usage_id", "loco-reviews": "review_id", "loco-observations": "claim_id"}
CATEGORIES = {"robot_platform": "人形与移动机器人", "robot_arm": "机械臂", "dexterous_hand": "灵巧手", "gripper": "夹爪",
              "compute_platform": "算力平台", "data_collection": "数采与遥操作设备", "tactile_sensor": "触觉传感器", "force_sensor": "力与力矩传感器", "vision_sensor": "视觉与空间传感器"}
COMPUTE_ROLES = {"training_compute", "inference_compute", "control_compute", "model_fitting_compute", "experiment_compute"}
ROLES = {"real_robot", "simulated_robot", "data_collection", "sensing", "dataset_source", "mentioned"} | COMPUTE_ROLES
SETTINGS = {"real", "simulation", "dataset", "unknown"}
USAGE_SCOPES = {"study", "baseline", "calibration"}
VALIDATIONS = {"closed_loop_real", "replay_only_real", "simulation_only", "unclear"}
FORBIDDEN = re.compile(r"\b(motors?|actuators?|servos?|joint[- _]modules?|pcbs?|circuits?|driver[- _]chips?)\b|电机|关节模组|电路|驱动芯片", re.I)
SOFTWARE = re.compile(r"^(?:NVIDIA\s+)?(?:Isaac (?:Gym|Sim|Lab)|MuJoCo|Genesis(?: simulator)?|ROS ?2?|PyTorch|PyBullet|SAPIEN|TensorFlow|JAX)(?:\b|$)", re.I)
LOCO_TERMS = re.compile(r"loco[ -]?manipulat|whole[ -]?body manipulation|mobile manipulation|humanoid manipulation", re.I)


def _url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        raise ValueError("equipment_public_source_required")
    url = urlsplit(value)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
        raise ValueError("equipment_public_source_required")
    host = url.hostname.lower()
    try:
        private_ip = not ipaddress.ip_address(host).is_global
    except ValueError:
        private_ip = False
    if host == 'localhost' or host.endswith(('.localhost', '.local')) or private_ip:
        raise ValueError("equipment_private_source_forbidden")
    return value


def _observed(value):
    if not isinstance(value, str) or not value.endswith('Z'):
        raise ValueError("equipment_utc_observation_required")
    if datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo != timezone.utc:
        raise ValueError("equipment_utc_observation_required")


def load_equipment_authority(directory, *, allow_missing=False):
    directory = Path(directory)
    missing = [name for name in TABLES if not (directory / (name + '.jsonl')).is_file() and not (directory / name).is_dir()]
    if missing and not allow_missing:
        raise ValueError('equipment_authority_missing:' + ','.join(missing))
    return {name: read_table(directory, name) for name in TABLES}


def validate_equipment(payload, authority):
    works = {row["work_id"]: row for row in payload["works"]}
    aliases = defaultdict(set)
    versions = defaultdict(list)
    for work in works.values():
        for key in [work["work_id"], *work.get("aliases", [])]:
            aliases[key].add(work["work_id"])
    for row in payload.get("work-aliases", []):
        aliases[row["alias"]].add(row["work_id"])
    for row in payload.get("manifestations", []):
        versions[row["work_id"]].append(row)
    identities = {wid: _work_identities(work, versions[wid]) for wid, work in works.items()}
    identity_owners = defaultdict(set)
    for wid, values in identities.items():
        for value in values:
            identity_owners[value].add(wid)
    result = copy.deepcopy(authority)
    for table, key in TABLES.items():
        rows = result.setdefault(table, [])
        ids = [row.get(key) for row in rows]
        if any(not value for value in ids) or len(ids) != len(set(ids)):
            raise ValueError("equipment_duplicate_or_missing_id:" + table)
    devices = {row["hardware_id"]: row for row in result["devices"]}
    slugs = set()
    for device in devices.values():
        if device.get("category") not in CATEGORIES or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", device.get("slug", "")):
            raise ValueError("equipment_device_category_or_slug_invalid")
        if device["slug"] in slugs or device["hardware_id"] != 'hardware:' + device["slug"]:
            raise ValueError("equipment_device_identity_conflict")
        slugs.add(device["slug"])
        if not isinstance(device.get('name'), str) or not device['name'].strip() or FORBIDDEN.search(device["name"]) or SOFTWARE.search(device["name"]):
            raise ValueError("equipment_out_of_scope_component")
        if device.get("identity_level") not in {"model_specified", "family_only", "unspecified"}:
            raise ValueError("equipment_device_identity_level_required")
        _url(device.get("official_url"))
        if not isinstance(device.get("aliases", []), list) or any(not isinstance(value, str) or not value.strip() for value in device.get('aliases', [])):
            raise ValueError("equipment_aliases_invalid")

    def source(row):
        matches = aliases.get(row.get("work_id"), set())
        if len(matches) != 1:
            raise ValueError("equipment_unknown_or_ambiguous_work:" + str(row.get("work_id")))
        row["submitted_work_id"] = row.get("submitted_work_id", row["work_id"])
        row["work_id"] = next(iter(matches))
        _url(row.get("source_url"))
        _observed(row.get("observed_at"))
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in ('source_locator', 'statement')) or row.get("source_kind") not in {"paper", "project", "technical_report", "code_documentation"}:
            raise ValueError("equipment_source_context_required")
        identity = _hard_identity(_url(row.get("work_url", row["source_url"])))
        if identity not in identities[row["work_id"]] or identity_owners[identity] != {row['work_id']}:
            raise ValueError("equipment_work_source_mismatch:" + row["work_id"])
        source_identity = _hard_identity(row['source_url'])
        if source_identity and source_identity.startswith(('arxiv:', 'doi:')) and source_identity not in identities[row['work_id']]:
            raise ValueError("equipment_work_source_mismatch:" + row["work_id"])
        if row.get("review_status") not in {"verified", "candidate"}:
            raise ValueError("equipment_explicit_review_required")

    semantic = set()
    unspecified_owners = defaultdict(set)
    for row in result["usage-evidence"]:
        source(row)
        if row.get("hardware_id") not in devices or row.get("role") not in ROLES or row.get("setting") not in SETTINGS:
            raise ValueError("equipment_usage_role_or_device_invalid")
        if row["review_status"] == 'verified' and row["role"] == 'mentioned':
            raise ValueError("equipment_mention_cannot_be_verified_use")
        if row['role'] in COMPUTE_ROLES and devices[row['hardware_id']]['category'] != 'compute_platform':
            raise ValueError('equipment_compute_role_category_conflict')
        if row["role"] == 'simulated_robot' and row["setting"] != 'simulation':
            raise ValueError("equipment_simulation_setting_conflict")
        if row["role"] == 'real_robot' and row["setting"] != 'real':
            raise ValueError("equipment_real_setting_conflict")
        scope = row.setdefault('usage_scope', 'study')
        if scope not in USAGE_SCOPES:
            raise ValueError('equipment_usage_scope_invalid')
        if scope in {'baseline', 'calibration'} and (not isinstance(row.get('configuration'), str) or not row['configuration'].strip()):
            raise ValueError('equipment_nonstudy_configuration_required')
        raw_roles = row.get('reported_roles', [row.get('reported_role')])
        if not isinstance(raw_roles, list) or any(role is not None and not isinstance(role, str) for role in raw_roles):
            raise ValueError('equipment_reported_roles_invalid')
        reported_roles = set(raw_roles)
        if 'sensor_calibration' in reported_roles and scope != 'calibration':
            raise ValueError('equipment_calibration_scope_required')
        if any(str(role).startswith('baseline_') for role in reported_roles) and scope != 'baseline':
            raise ValueError('equipment_baseline_scope_required')
        if devices[row['hardware_id']]['identity_level'] == 'unspecified':
            unspecified_owners[row['hardware_id']].add(row['work_id'])
        key = (row["work_id"], row["hardware_id"], row["role"], row["setting"], scope, row["source_url"], row["source_locator"])
        if key in semantic:
            raise ValueError("equipment_duplicate_usage_evidence")
        semantic.add(key)
    if any(len(owners) > 1 for owners in unspecified_owners.values()):
        raise ValueError('equipment_unspecified_identity_shared_across_works')
    reviewed = set()
    for row in result["loco-reviews"]:
        source(row)
        if row["work_id"] in reviewed or row.get("scope") not in {'core', 'support', 'excluded'}:
            raise ValueError("loco_duplicate_or_invalid_scope")
        reviewed.add(row["work_id"])
        if not row.get("coordination") or row.get("validation") not in VALIDATIONS:
            raise ValueError("loco_coordination_validation_required")
        if row.get("project_id") and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", row["project_id"]):
            raise ValueError("loco_project_id_invalid")
    for row in result['loco-observations']:
        if not row.get('title') or not row.get('summary') or not row.get('supporting_ids') or not row.get('source_urls'):
            raise ValueError('loco_observation_sources_required')
        row.setdefault('counterevidence_ids', [])
        _observed(row.get('observed_at'))
        for field in ('supporting_ids', 'counterevidence_ids'):
            ids = []
            for value in row[field]:
                matches = aliases.get(value, set())
                if len(matches) != 1 or next(iter(matches)) not in reviewed:
                    raise ValueError('loco_observation_unreviewed_work')
                ids.append(next(iter(matches)))
            row[field] = ids
        for value in row['source_urls']:
            _url(value)
    return result


def build_equipment_bundle(payload, authority, manifest):
    data = validate_equipment(payload, authority)
    works = {row['work_id']: row for row in payload['works']}
    included = {key for key, row in works.items() if row.get('relevance', {}).get('status') == 'included'}
    months = [*manifest['complete_months'], manifest['provisional_month']]
    common = {'schema_version': '1', 'dataset_version': manifest['dataset_version'], 'data_through': manifest['data_through'],
              'window': {key: manifest[key] for key in ('complete_months', 'provisional_month')},
              'authority_hash': fingerprint(authority)}
    devices = {row['hardware_id']: row for row in data['devices']}
    usage = []
    for row in data['usage-evidence']:
        if row['review_status'] != 'verified' or row['work_id'] not in included:
            continue
        device = devices[row['hardware_id']]
        usage.append({**row, 'name': device['name'], 'category': device['category'], 'device_slug': device['slug'], 'identity_level': device['identity_level']})
    by_work, by_device = defaultdict(list), defaultdict(set)
    for row in usage:
        by_work[row['work_id']].append(row)
        by_device[row['hardware_id']].add(row['work_id'])
    # Candidate names are not inferred usage, even when a device has a verified
    # relationship to another paper. Only title/abstract text is searched here.
    mentions = []
    for key in sorted(included):
        text = works[key]['title'] + '\n' + (works[key].get('abstract') or '')
        for device in devices.values():
            labels = [device['name'], *device.get('aliases', [])]
            match = next((label for label in labels if len(label) >= 2 and re.search(r'(?<!\w)' + re.escape(label) + r'(?!\w)', text, re.I)), None)
            if match and key not in by_device[device['hardware_id']]:
                mentions.append({'work_id': key, 'hardware_id': device['hardware_id'], 'matched_term': match, 'status': 'mention_only_not_verified_usage'})
    directory = [{**device, 'work_ids': sorted(by_device[device['hardware_id']])} for device in devices.values()]
    categories = [{'code': code, 'label': label, 'devices': sum(row['category'] == code for row in directory),
                   'works': len({row['work_id'] for row in usage if row['category'] == code})} for code, label in CATEGORIES.items()]
    index = {**common, 'counts': {'devices': len(directory), 'usage_links': len(usage), 'works': len(by_work), 'hardware_candidates': len(mentions)},
             'categories': categories, 'devices': sorted(directory, key=lambda row: row['name'].lower()),
             'limits': ['仅统计已纳入研究的已核验使用关系；未登记不表示未使用。', '设备型号与用途来自当前核验版本，不代表采购量、市场份额或独立实验复现。', '电机、关节模组、电路及仿真软件不作为硬件设备条目。']}
    # Scope verification and catalog inclusion are independent decisions. Keep
    # non-included source reviews visible without promoting their works.
    reviews = []
    for row in data['loco-reviews']:
        relevance = works[row['work_id']].get('relevance', {}).get('status', 'unknown')
        eligible = row['review_status'] == 'verified' and row['work_id'] in included
        reviews.append({**row, 'relevance_status': relevance,
                        'effective_scope': row['scope'] if eligible else 'candidates',
                        'candidate_reason': None if eligible else 'catalog_not_included' if row['work_id'] not in included else 'scope_review_pending'})
    lanes = {scope: sorted(row['work_id'] for row in reviews if row['effective_scope'] == scope) for scope in ('core', 'support', 'excluded')}
    known = {row['work_id'] for row in reviews}
    candidates = {row['work_id'] for row in reviews if row['effective_scope'] == 'candidates'}
    candidates.update(key for key in included - known if LOCO_TERMS.search(works[key]['title'] + '\n' + (works[key].get('abstract') or '')))
    review_by_work = {row['work_id']: row for row in reviews}
    observations = []
    for row in data['loco-observations']:
        ids = list(dict.fromkeys([*row['supporting_ids'], *row['counterevidence_ids']]))
        pending = [wid for wid in ids if wid not in included or review_by_work[wid]['review_status'] != 'verified']
        candidates.update(pending)
        observations.append({**row, 'review_status': 'candidate' if pending else 'verified',
                             'candidate_work_ids': pending,
                             'supporting_work_status': {wid: {'relevance_status': works[wid].get('relevance', {}).get('status', 'unknown'),
                                                             'review_status': review_by_work[wid]['review_status'],
                                                             'effective_scope': review_by_work[wid]['effective_scope']} for wid in ids}})
    # The ID lane also supplies the lazy detail-card builder, including every
    # observation dependency; monthly trends remain included-only below.
    lanes['candidates'] = sorted(candidates)
    monthly = []
    for month in months:
        count = lambda scope: sum(key in included and works[key].get('first_public_date_precision') in {'day', 'month'} and str(works[key].get('first_public_date', '')).startswith(month) for key in lanes[scope])
        monthly.append({'month': month, 'provisional': month == manifest['provisional_month'], **{scope: count(scope) for scope in ('core', 'support', 'candidates')}})
    loco = {**common, 'counts': {key: len(value) for key, value in lanes.items()}, 'monthly': monthly,
            'observations': observations, 'reviews': reviews, 'work_ids': lanes,
            'limits': ['主题检索命中不等于已核验loco-manip研究。', '分月图仅计已纳入研究，非included的观察依赖保留候选详情但不计入任何趋势柱。', '分月图按研究首次公开月组织已核验样本，不是全领域增长率。', '轨迹回放、仅仿真、真机闭环分别记录；暂行月不参与完整月趋势判断。']}
    return {'index': index, 'usage': {**common, 'by_work': dict(by_work), 'candidates': mentions}, 'loco-manip': loco, 'tables': data}


def export_equipment(bundle, api, downloads):
    for key in ('index', 'usage', 'loco-manip'):
        write_if_changed(Path(api) / (key + '.json'), encode(bundle[key]) + '\n')
    for key, rows in bundle['tables'].items():
        write_if_changed(Path(downloads) / (key + '.jsonl'), ''.join(encode(row) + '\n' for row in rows))


def equipment_sqlite(connection, bundle):
    for table, key in TABLES.items():
        name = 'equipment_' + table.replace('-', '_')
        connection.execute(f'CREATE TABLE {name} (record_id TEXT PRIMARY KEY, work_id TEXT, payload_json TEXT NOT NULL)')
        connection.executemany(f'INSERT INTO {name} VALUES (?,?,?)', [(row[key], row.get('work_id'), encode(row)) for row in bundle['tables'][table]])
    connection.execute('CREATE TABLE equipment_api (path TEXT PRIMARY KEY, payload_json TEXT NOT NULL)')
    connection.executemany('INSERT INTO equipment_api VALUES (?,?)', [(key, encode(bundle[key])) for key in ('index', 'usage', 'loco-manip')])


def audit_equipment(bundle, api, downloads, connection):
    saved_api = {key: json.loads(text) for key, text in connection.execute('SELECT path,payload_json FROM equipment_api')}
    if saved_api != {key: bundle[key] for key in ('index', 'usage', 'loco-manip')}:
        raise ValueError('equipment_sqlite_api_mismatch')
    for key in ('index', 'usage', 'loco-manip'):
        if json.loads((Path(api) / (key + '.json')).read_text()) != bundle[key]:
            raise ValueError('equipment_api_mismatch:' + key)
        saved = connection.execute('SELECT payload_json FROM equipment_api WHERE path=?', (key,)).fetchone()
        if not saved or json.loads(saved[0]) != bundle[key]:
            raise ValueError('equipment_sqlite_api_mismatch:' + key)
    for table, key in TABLES.items():
        expected = {row[key]: row for row in bundle['tables'][table]}
        saved_rows = list(connection.execute('SELECT record_id,work_id,payload_json FROM equipment_' + table.replace('-', '_')))
        saved = {rid: json.loads(text) for rid, _, text in saved_rows}
        downloaded_rows = read_table(Path(downloads), table)
        downloaded = {row[key]: row for row in downloaded_rows}
        if saved != expected or downloaded != expected or len(downloaded_rows) != len(downloaded) or any(wid != expected.get(rid, {}).get('work_id') for rid, wid, _ in saved_rows):
            raise ValueError('equipment_authority_roundtrip_mismatch:' + table)
