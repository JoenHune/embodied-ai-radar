import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { hardwareFrequency, hardwareMonth } from '../docs/.vitepress/theme/lib/hardware-frequency.mjs'

const device = (id, name = id, level = 'model_specified') => ({ hardware_id: id, name, category: 'robot_platform', identity_level: level })
const usage = (id, extra = {}) => ({ hardware_id: id, category: 'robot_platform', review_status: 'verified', source_url: 'https://arxiv.org/html/2609.00001v1', source_locator: '§4', role: 'real_robot', setting: 'real', statement: 'Used this platform in the experiment.', usage_scope: 'study', ...extra })
const work = (id, usages, extra = {}) => ({ work_id: id, title: id, relevance_status: 'included', first_public_date: '2026-09-01', first_public_date_precision: 'day', hardware_usage: usages, ...extra })

test('frequency counts canonical works once, retaining real/sim overlap and all proofs', () => {
  const a = usage('g1')
  const simulated = usage('g1', { role: 'simulated_robot', setting: 'simulation', source_url: 'https://arxiv.org/html/2609.00001v2' })
  const result = hardwareFrequency([device('g1')], [work('a', [a, a, simulated]), work('a', [a]), work('legacy-a', [a], { canonical_work_id: 'a' }), work('b', [a])]).models[0]
  assert.equal(result.work_count, 2)
  assert.equal(result.real_work_count, 2)
  assert.equal(result.simulation_work_count, 1)
  assert.equal(result.sources.length, 2)
  assert.equal(result.sources.find(s => s.work_id === 'a').usages.length, 2)
  assert.equal(result.source_count, 3)
})
test('sorts by work frequency, then stable model name and ID; no alphabetical default', () => {
  const devices = [device('z', 'Zulu'), device('a', 'Alpha'), device('b', 'Beta')]
  const rows = [work('1', [usage('z'), usage('a'), usage('b')]), work('2', [usage('z')])]
  assert.deepEqual(hardwareFrequency(devices, rows).models.map(d => d.hardware_id), ['z', 'a', 'b'])
})
test('unresolved series and anonymous hardware do not enter the model ranking', () => {
  const devices = [device('g1'), device('wuji', 'WUJI 20-DoF', 'family_only'), device('unknown', 'Onboard computer', 'unspecified')]
  const result = hardwareFrequency(devices, [work('a', devices.map(d => usage(d.hardware_id)))])
  assert.deepEqual(result.models.map(d => d.hardware_id), ['g1'])
  assert.equal(result.unresolved.length, 2)
  assert.equal(result.unresolved.find(d => d.hardware_id === 'wuji').sources.length, 1)
})
test('every combination filter applies to the matching use, not an unrelated device in the paper', () => {
  const devices = [device('g1'), { ...device('gpu'), category: 'compute_platform' }]
  const rows = [work('a', [usage('g1'), usage('gpu', { category: 'compute_platform', role: 'training_compute', setting: 'unknown' })])]
  assert.equal(hardwareFrequency(devices, rows, { device: 'gpu', role: 'real_robot' }).models.length, 0)
  assert.equal(hardwareFrequency(devices, rows, { category: 'compute_platform', role: 'training_compute', setting: 'unknown', month: '2026-09' }).models[0].work_count, 1)
  assert.equal(hardwareFrequency(devices, rows, { month: '2026-08' }).models.length, 0)
})
test('candidate works, mention-only/unverified uses, missing evidence and unsafe URLs are excluded', () => {
  const d = device('g1')
  const rows = [work('candidate', [usage('g1')], { relevance_status: 'manual_review' }), ...[
    { review_status: 'candidate' }, { role: 'mentioned' }, { statement: '' }, { source_url: 'javascript:alert(1)' }, { source_url: 'http://127.0.0.1/private' }, { source_url: 'https://user:password@example.org/' }, { category: 'motor' },
  ].map((extra, i) => work(String(i), [usage('g1', extra)]))]
  assert.equal(hardwareFrequency([d], rows).models.length, 0)
})
test('baseline/calibration are separate work counts and preserve their statements', () => {
  const result = hardwareFrequency([device('x')], [work('a', [usage('x', { usage_scope: 'baseline' }), usage('x', { usage_scope: 'calibration' })])]).models[0]
  assert.equal(result.work_count, 1)
  assert.equal(result.baseline_work_count, 1)
  assert.equal(result.calibration_work_count, 1)
  assert.equal(result.sources[0].usages.length, 2)
})
test('equal display names are not sufficient evidence to merge device identities', () => {
  const rows = hardwareFrequency([device('a', 'Hand'), device('b', 'Hand')], [work('1', [usage('a')]), work('2', [usage('b')])]).models
  assert.equal(rows.length, 2)
  assert.deepEqual(rows.map(r => r.work_count), [1, 1])
})
test('year-only and unknown dates do not fabricate month placement', () => {
  assert.equal(hardwareMonth({ first_public_date: '2026-01-01', first_public_date_precision: 'year' }), 'unknown')
  assert.equal(hardwareMonth({ first_public_date: '2026-09', first_public_date_precision: 'month' }), '2026-09')
})
test('frozen audited authority cohort: G1 16 works, PiPER-X one real work, WUJI one simulation-only family', () => {
  // Use tracked authority rather than ignored/generated API so clean CI works.
  const read = name => fs.readFileSync(new URL(`../data/equipment/${name}.jsonl`, import.meta.url), 'utf8').trim().split('\n').map(JSON.parse)
  const devices = read('devices')
  const byDevice = new Map(devices.map(d => [d.hardware_id, d]))
  const cohort = new Set(['arxiv:2509.20322', 'arxiv:2510.02252', 'arxiv:2510.03022', 'arxiv:2510.05070', 'arxiv:2511.02832', 'arxiv:2511.15200', 'arxiv:2602.06643', 'arxiv:2602.10106', 'arxiv:2602.16710', 'arxiv:2603.12263', 'arxiv:2606.22174', 'arxiv:2606.23680', 'arxiv:2608.06375', 'arxiv:2608.17027', 'arxiv:2609.05994', 'arxiv:2609.06591', 'arxiv:2609.12081'])
  const byWork = new Map()
  for (const row of read('usage-evidence')) { if (!cohort.has(row.work_id)) continue; const list = byWork.get(row.work_id) || []; list.push({ ...row, category: byDevice.get(row.hardware_id)?.category }); byWork.set(row.work_id, list) }
  const rows = [...byWork].map(([id, uses]) => work(id, uses))
  const result = hardwareFrequency(devices, rows)
  const g1 = result.models.find(d => d.hardware_id === 'hardware:unitree-g1')
  assert.equal(g1.work_count, 16)
  assert.equal(g1.real_work_count, 14)
  assert.equal(g1.simulation_work_count, 8)
  assert.equal(result.models.find(d => d.hardware_id === 'hardware:agilex-piper-x').real_work_count, 1)
  const wuji = result.unresolved.find(d => /WUJI/.test(d.name))
  assert.equal(wuji.work_count, 1)
  assert.equal(wuji.real_work_count, 0)
  assert.equal(wuji.simulation_work_count, 1)
})
