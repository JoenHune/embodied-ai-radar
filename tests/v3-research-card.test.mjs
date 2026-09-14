import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { parse, compileTemplate } from '@vue/compiler-sfc'
import { originalSourceUrl, filterResearchCards, researchOutputLabel, searchCardFromResult } from '../docs/.vitepress/theme/lib/research-card.mjs'

test('primary card URL leads to the original work, never an intermediate drawer', () => {
  assert.equal(originalSourceUrl({ work_id: 'arxiv:2602.16710' }), 'https://arxiv.org/abs/2602.16710')
  assert.equal(originalSourceUrl({ work_id: 'doi:10.1234/example' }), 'https://doi.org/10.1234/example')
  assert.equal(originalSourceUrl({ work_id: 'report:a', manifestations: [{ kind: 'technical_report', url: 'https://company.example/research/report' }] }), 'https://company.example/research/report')
})
test('source links cannot be javascript or credentials', () => {
  assert.equal(originalSourceUrl({ original_url: 'javascript:alert(1)' }), '')
  assert.equal(originalSourceUrl({ url: 'https://user:secret@example.com' }), '')
})
test('strategic observations remain outside the default research lane', () => {
  const rows = [{ work_id: 'paper', primary_direction: 'D3', directions: ['D3'], output_types: ['preprint'], strategic_only: false }, { work_id: 'report', primary_direction: 'D3', directions: ['D3'], output_types: ['technical_report'], strategic_only: false }, { work_id: 'demo', output_types: ['demo'], strategic_only: true }]
  assert.deepEqual(filterResearchCards(rows).map(row => row.work_id), ['paper', 'report'])
  assert.deepEqual(filterResearchCards(rows, { kind: 'reports', direction: 'D3' }).map(row => row.work_id), ['report'])
  assert.deepEqual(filterResearchCards(rows, { kind: 'strategic' }).map(row => row.work_id), ['demo'])
  assert.equal(researchOutputLabel(rows[1]), '企业技术报告')
})
test('chart-linked feeds count primary directions rather than inflating shares with cross-labels', () => {
  const rows = [{ work_id: 'a', primary_direction: 'D3', directions: ['D3', 'D1'] }, { work_id: 'b', primary_direction: 'D1', directions: ['D1', 'D3'] }]
  assert.deepEqual(filterResearchCards(rows, { direction: 'D3' }).map(row => row.work_id), ['a'])
})
test('search-to-visual projection preserves status, original URL, scope and version warning', () => {
  const row = { excerpt: 'Original source excerpt', meta: { work_id: 'arxiv:2607.04837', title: 'Original title', original_url: 'https://arxiv.org/abs/2607.04837', research_status: 'withdrawn', research_validation_eligible: 'false', relevance: 'included', evidence: 'E0', peer_reviewed: 'false', date: '2026-07-06', date_precision: 'day', text_status: 'unversioned_catalog_text' } }
  const before = structuredClone(row)
  const card = searchCardFromResult(row)
  assert.equal(card.work_id, row.meta.work_id)
  assert.equal(card.research_status.status, 'withdrawn')
  assert.equal(card.research_status.validation_eligible, false)
  assert.equal(card.original_url, row.meta.original_url)
  assert.equal(card.text_notice, '摘要版次未核验')
  assert.equal(card.relevance_status, 'included')
  assert.deepEqual(row, before)
})

const cardSource = () => fs.readFileSync(new URL('../docs/.vitepress/theme/components/ResearchCard.vue', import.meta.url), 'utf8')
test('hardware card links use stable hardware_id and preserve baseline, calibration and replay evidence', async () => {
  const { descriptor } = parse(cardSource())
  const compiled = compileTemplate({ id: 'hardware-card-test', filename: 'ResearchCard.vue', source: descriptor.template.content, compilerOptions: { mode: 'function' } })
  assert.deepEqual(compiled.errors, [])
  const render = new Function('Vue', compiled.code)(Vue)
  const hardware = [
    { usage_id: 'usage:baseline', hardware_id: 'hardware:baseline-platform', device_slug: 'wrong-slug', name: 'Baseline robot', role: 'real_robot', setting: 'real', usage_scope: 'baseline', statement: 'Only used in the baseline comparison.', source_url: 'https://example.org/baseline' },
    { usage_id: 'usage:calibration', hardware_id: 'hardware:calibration-sensor', name: 'Calibration sensor', role: 'sensing', setting: 'real', usage_scope: 'calibration', statement: 'Used only to calibrate force measurements.', source_url: 'https://example.org/calibration' },
    { usage_id: 'usage:replay', hardware_id: 'hardware:replay-platform', name: 'Replay robot', role: 'real_robot', setting: 'real', statement: 'Trajectory replay only; no closed-loop autonomous policy evaluation.', configuration: 'Replay evaluation', source_url: 'https://example.org/replay' },
  ]
  const work = { work_id: 'work:hardware-test', title: 'Hardware evidence fixture', directions: [], hardware_usage: hardware }
  const context = { work, compact: false, detailButton: false, asset: null, original: 'https://example.org/paper', report: false, blocked: false, publications: [], notices: [], relevanceLabels: {}, directionShortNames: {}, details: '/database/', hardware, hardwareNames: hardware.map(row => row.name), usageLabels: { real_robot: '真机使用', sensing: '感知' }, settingLabels: { real: '真实设备' }, eventDate: () => '日期未登记', researchOutputLabel: () => '论文', withBase: value => value }
  const app = Vue.createSSRApp({ render, setup: () => context, components: { SourceImage: { render: () => null }, SourceConflictNotice: { render: () => null } } })
  const html = await renderToString(app)
  assert.match(html, /\/hardware\/\?device=hardware%3Abaseline-platform/)
  assert.doesNotMatch(html, /device=wrong-slug/)
  for (const phrase of ['仅对照基线', '校准用途', 'Only used in the baseline comparison.', 'Used only to calibrate force measurements.', 'Trajectory replay only; no closed-loop autonomous policy evaluation.', 'Replay evaluation', '设备使用不等同于闭环自主能力验证']) assert.ok(html.includes(phrase), phrase)
  for (const row of hardware) assert.ok(html.includes(`href="${row.source_url}"`))
})

function equipmentHarness(body, manifest) {
  const source = fs.readFileSync(new URL('../docs/.vitepress/theme/composables/useEquipmentEvidence.ts', import.meta.url), 'utf8')
  const mounted = [], requests = []
  let replies = { body, manifest }
  const context = { Promise, Error, shallowRef: value => ({ value }), onMounted: hook => mounted.push(hook), withBase: value => value,
    fetch: async url => { requests.push(url); return { ok: true, json: async () => url.endsWith('/card-usage.json') ? replies.body : replies.manifest } },
  }
  const script = source.replace(/^import .*$/gm, '').replace(/export function useEquipmentEvidence/, 'function useEquipmentEvidence') + '\nglobalThis.useEvidence = useEquipmentEvidence;'
  vm.runInNewContext(ts.transpile(script, { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None }), context)
  return { useEvidence: context.useEvidence, mounted, requests, setReplies: (body, manifest) => { replies = { body, manifest } } }
}
const flushEquipment = () => new Promise(resolve => setImmediate(resolve))
test('equipment composable is lazy, shares one request pair and accepts only matching dataset versions', async () => {
  const by_work = { 'work:one': [{ hardware_id: 'hardware:robot', name: 'Robot' }] }
  const harness = equipmentHarness({ schema_version: '1', dataset_version: 'v1', by_work }, { dataset_version: 'v1' })
  const first = harness.useEvidence(), second = harness.useEvidence()
  assert.equal(first, second)
  assert.equal(harness.requests.length, 0, 'SSR/setup alone must not request equipment')
  harness.mounted.forEach(hook => hook())
  await flushEquipment()
  assert.equal(harness.requests.length, 2, 'concurrent cards reuse the lookup and manifest request')
  assert.equal(first.value, by_work)
  harness.useEvidence(); harness.mounted.at(-1)(); await flushEquipment()
  assert.equal(harness.requests.length, 2, 'later cards reuse the cache')
})
test('equipment lookup refuses mismatched versions and can retry without leaking rejected rows', async () => {
  const rejected = { 'work:one': [{ name: 'Wrong version' }] }
  const harness = equipmentHarness({ schema_version: '1', dataset_version: 'v1', by_work: rejected }, { dataset_version: 'v2' })
  const evidence = harness.useEvidence(); harness.mounted.at(-1)(); await flushEquipment()
  assert.equal(Object.keys(evidence.value).length, 0)
  const accepted = { 'work:one': [{ name: 'Matching version' }] }
  harness.setReplies({ schema_version: '1', dataset_version: 'v2', by_work: accepted }, { dataset_version: 'v2' })
  harness.useEvidence(); harness.mounted.at(-1)(); await flushEquipment()
  assert.equal(evidence.value, accepted)
  assert.equal(harness.requests.length, 4)
})
test('explicit card hardware evidence, including an empty list, takes priority over lazy cached evidence', () => {
  const { descriptor } = parse(cardSource())
  const expression = descriptor.scriptSetup.content.match(/const hardware = computed<any\[\]>\(\(\) => (.+)\)/)?.[1]
  assert.ok(expression, 'the precedence expression must remain testable')
  const choose = new Function('props', 'equipment', `return ${expression}`)
  const cached = { value: { 'work:one': [{ name: 'Cached robot' }] } }
  const direct = [{ name: 'Direct robot' }]
  assert.equal(choose({ work: { work_id: 'work:one', hardware_usage: direct } }, cached), direct)
  assert.deepEqual(choose({ work: { work_id: 'work:one', hardware_usage: [] } }, cached), [])
  assert.equal(choose({ work: { work_id: 'work:one' } }, cached), cached.value['work:one'])
})
