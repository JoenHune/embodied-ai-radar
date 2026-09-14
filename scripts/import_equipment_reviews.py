"""Normalize inspected hardware evidence without guessing product variants."""
import argparse
import copy
import json
import re
from pathlib import Path

from catalog_store import encode, fingerprint, load_catalog, write_if_changed
from equipment_radar import TABLES, load_equipment_authority, validate_equipment

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    'Unitree G1 model': 'Unitree G1', 'Unitree G1 model (42-DoF configuration)': 'Unitree G1',
    'Galaxea R1 Pro model': 'Galaxea R1 Pro', 'Unitree Dex31': 'Unitree Dex3-1',
    'PICO 4U (PICO 4 Ultra)': 'PICO 4 Ultra', 'PICO4U VR kit': 'PICO 4 Ultra',
    'NVIDIA A100 GPUs': 'NVIDIA A100', 'NVIDIA A100 cluster': 'NVIDIA A100',
    'NVIDIA H100 GPUs': 'NVIDIA H100', 'NVIDIA GB200 GPUs': 'NVIDIA GB200',
}
ROLE_MAP = {'teleoperation': 'data_collection', 'video_capture': 'data_collection', 'simulation_data_generation': 'data_collection',
            'sensor_calibration': 'sensing', 'baseline_sensing': 'sensing', 'baseline_teleoperation': 'data_collection'}


def normalize(raw):
    tables = {key: [] for key in TABLES}
    devices = {}
    source_by_work = {}
    for work in raw['works']:
        wid = work['work_id']
        work_url = 'https://arxiv.org/abs/' + work['arxiv_id']
        source_by_work[wid] = work['source_url']
        for device in work['devices']:
            reported_name = device['device_name']
            name = re.sub(r'^\d+\s*[×x]\s*', '', reported_name)
            name = ALIASES.get(name, name)
            category = device['category']
            specificity = {'exact': 'model_specified', 'family': 'family_only', 'unspecified': 'unspecified', 'unknown': 'unspecified'}.get(device.get('model_specificity'), 'unspecified')
            # A family label or unnamed camera is not proof of a shared model.
            # Keep uncertain identities local to the inspected work, including
            # their granularity, so input ordering cannot upgrade them to exact.
            suffix = '-' + fingerprint([wid, reported_name, specificity, device.get('vendor'), category])[:8] if specificity != 'model_specified' else ''
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:90] + suffix
            if not slug:
                slug = category + '-' + fingerprint([wid, name])[:10]
            hid = 'hardware:' + slug
            row = {'hardware_id': hid, 'slug': slug, 'name': name, 'vendor': device.get('vendor'), 'category': category,
                   'identity_level': specificity, 'official_url': device['source_url'], 'aliases': [reported_name] if reported_name != name else []}
            if specificity != 'model_specified':
                row['identity_context_work_id'] = wid
            if hid in devices:
                if devices[hid]['category'] != category:
                    raise ValueError('equipment_category_conflict:' + hid)
                if devices[hid]['identity_level'] != specificity or devices[hid].get('vendor') != row.get('vendor'):
                    raise ValueError('equipment_identity_conflict:' + hid)
                devices[hid]['aliases'] = sorted(set(devices[hid]['aliases'] + row['aliases']))
            else:
                devices[hid] = row
            for original_role in device['usage_roles']:
                role = ROLE_MAP.get(original_role, original_role)
                validation = device.get('validation_level', '')
                if original_role == 'dataset_source':
                    setting = 'dataset'
                elif original_role in {'simulated_robot', 'simulation_data_generation'}:
                    setting = 'simulation'
                elif original_role == 'real_robot' or original_role == 'sensor_calibration':
                    setting = 'real'
                elif role in {'training_compute', 'inference_compute'}:
                    # Compute allocation is not evidence of a physical robot trial.
                    setting = 'unknown'
                else:
                    setting = 'simulation' if validation == 'simulation_only' else 'real' if 'real_robot' in validation else 'unknown'
                baseline = original_role.startswith('baseline_') or device.get('method_role') == 'baseline_only'
                calibration = original_role == 'sensor_calibration'
                usage_scope = 'calibration' if calibration else 'baseline' if baseline else 'study'
                configuration = ('仅用于传感器校准/标定，不代表策略部署感知；' if calibration else '仅用于对照基线；' if baseline else '') + ('原文配置：' + reported_name if reported_name != name else '')
                entry = {'work_id': wid, 'hardware_id': hid, 'role': role, 'setting': setting,
                         'usage_scope': usage_scope, 'reported_role': original_role, 'reported_roles': [original_role],
                         'configuration': configuration, 'reported_device_name': reported_name,
                         'validation_context': validation, 'review_status': device['verification_status'],
                         'source_url': device['source_url'], 'source_locator': device['source_section'], 'source_kind': 'paper',
                         'source_version': work.get('source_version'), 'work_url': work_url,
                         'statement': device['evidence_paraphrase_zh'], 'observed_at': device['observed_at']}
                entry['usage_id'] = 'usage:' + fingerprint([wid, hid, role, setting, usage_scope, entry['source_url'], entry['source_locator']])[:24]
                tables['usage-evidence'].append(entry)
        assessment = work['loco_manipulation']
        source_validation = assessment['validation_level']
        validation = 'simulation_only' if source_validation == 'simulation_only' else 'replay_only_real' if 'trajectory_replay' in source_validation else 'closed_loop_real' if 'real_robot' in source_validation else 'unclear'
        entry = {'review_id': 'loco:' + fingerprint(wid)[:24], 'work_id': wid, 'work_url': work_url,
                 'scope': assessment['scope'].split('/')[0], 'coordination': assessment['control_class'],
                 'validation': validation, 'validation_context': source_validation,
                 'source_url': assessment['source_url'], 'source_locator': assessment['source_section'], 'source_kind': 'paper',
                 'statement': assessment['evidence_paraphrase_zh'], 'observed_at': assessment['observed_at'],
                 'review_status': work['verification_status']}
        if wid in {'arxiv:2606.26425', 'arxiv:2609.01518'}:
            entry['project_id'] = 'ihmc-runtime-editable-behavior-system'
        tables['loco-reviews'].append(entry)
    tables['devices'] = list(devices.values())
    titles = {'motion-is-not-manipulation': '运动追踪不等于接触操作',
              'contact-control-has-multiple-interfaces': '接触、躯干与腿臂协调存在不同控制接口',
              'evidence-level-is-independent': '相同机型不代表相同验证程度',
              'collection-observation-and-compute-must-be-separated': '采集、部署与训练算力需要分开看',
              'september-progress-needs-phase-and-baseline-controls': '9月新增路线需区分阶段、基线与自主程度'}
    for observation in raw['observations']:
        ids = observation['works']
        tables['loco-observations'].append({'claim_id': 'loco-observation:' + observation['id'],
            'title': titles.get(observation['id'], observation['id']), 'summary': observation['text'],
            'supporting_ids': ids, 'counterevidence_ids': [], 'source_urls': list(dict.fromkeys(source_by_work[key] for key in ids)),
            'observed_at': raw['observed_at'], 'judgment_type': 'source_reviewed_observation_not_population_trend'})
    for table, key in TABLES.items():
        unique = {}
        for row in tables[table]:
            previous = unique.get(row[key])
            if previous and previous != row:
                # Synonymous raw roles can collapse onto the same public role,
                # but study/baseline/calibration identities never collapse.
                ignored = {'reported_role', 'reported_roles'} if table == 'usage-evidence' else set()
                if {k: v for k, v in previous.items() if k not in ignored} != {k: v for k, v in row.items() if k not in ignored}:
                    raise ValueError('equipment_normalization_conflict:' + row[key])
                roles = sorted(set(previous.get('reported_roles', []) + row.get('reported_roles', [])))
                row = {**row, 'reported_role': roles[0], 'reported_roles': roles}
            unique[row[key]] = row
        tables[table] = [unique[key] for key in sorted(unique)]
    return tables


def merge_equipment_reviews(payload, existing, proposed):
    """Validate the complete prospective authority before any filesystem write."""
    merged = {}
    for table, key in TABLES.items():
        by_id = {}
        for row in [*existing.get(table, []), *proposed.get(table, [])]:
            identity = row.get(key)
            if not identity:
                raise ValueError('equipment_duplicate_or_missing_id:' + table)
            if identity in by_id and by_id[identity] != row:
                raise ValueError('equipment_existing_authority_conflict:' + identity)
            by_id[identity] = copy.deepcopy(row)
        merged[table] = [by_id[identity] for identity in sorted(by_id)]
    validate_equipment(payload, merged)
    return merged


def import_reviews(raw, payload, directory, *, apply=False):
    proposed = normalize(raw)
    existing = load_equipment_authority(directory, allow_missing=True)
    merged = merge_equipment_reviews(payload, existing, proposed)
    if apply:
        for table, rows in merged.items():
            write_if_changed(Path(directory) / (table + '.jsonl'), ''.join(encode(row) + '\n' for row in rows))
    return {'applied': apply, 'counts': {key: len(rows) for key, rows in merged.items()},
            'proposed_counts': {key: len(rows) for key, rows in proposed.items()}}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    payload, _ = load_catalog(ROOT / 'data/catalog')
    print(json.dumps(import_reviews(json.loads(args.input.read_text()), payload, ROOT / 'data/equipment', apply=args.apply)))


if __name__ == '__main__':
    main()
