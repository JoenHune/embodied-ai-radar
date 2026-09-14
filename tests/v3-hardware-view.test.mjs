import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { hardwareFrequency, hardwareMonth } from '../docs/.vitepress/theme/lib/hardware-frequency.mjs'

const read = file => fs.readFileSync(new URL(`../docs/.vitepress/theme/components/${file}`, import.meta.url), 'utf8')
function harness() {
  const { descriptor, errors } = parse(read('HardwareRadar.vue'))
  assert.deepEqual(errors, [])
  const script = compileScript(descriptor, { id: 'model-view' })
  assert.deepEqual(compileTemplate({ id: 'model-view', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } }).errors, [])
  let uri = new URL('https://radar.test/hardware/')
  let chartFactory
  const context = { Set, Map, URL, URLSearchParams, AbortController, hardwareFrequency, hardwareMonth,
    computed: fn => ({ get value() { return fn() } }), ref: value => ({ value }), nextTick: async () => {},
    onMounted() {}, onBeforeUnmount() {}, useRouter: () => ({}), withBase: x => x, eventDate: x => x,
    echarts: { use() {} }, BarChart: {}, AriaComponent: {}, GridComponent: {}, TooltipComponent: {}, CanvasRenderer: {},
    chartTokens: () => ({ palette: ['#000'] }), useEChart: fn => { chartFactory = fn; return { element: {} } },
    window: { get location() { return { href: uri.href, pathname: uri.pathname, search: uri.search } }, history: { state: {}, pushState(_a, _b, url) { uri = new URL(url) }, replaceState(_a, _b, url) { uri = new URL(url) } } },
  }
  const source = descriptor.scriptSetup.content.replace(/^import .*$/gm, '') + '\nglobalThis.view = { index, rows, modelQuery, models, unresolved, filters, readUrl, searchModels, visibleModels, shown, openSources, moreModels, topModels };'
  vm.runInNewContext(ts.transpile(source, { target: ts.ScriptTarget.ES2022 }), context)
  return { ...context.view, url: () => uri, setUrl: q => { uri = new URL(q, uri) }, chart: () => chartFactory() }
}
function seed(view) {
  const devices = Array.from({ length: 25 }, (_, i) => ({ hardware_id: `h:${i}`, slug: `model-${i}`, name: i ? `Model ${i}` : 'Unitree G1', category: 'robot_platform', identity_level: 'model_specified' }))
  devices.push({ hardware_id: 'h:wuji', slug: 'wuji', name: 'WUJI 20-DoF hand', category: 'robot_platform', identity_level: 'family_only' })
  view.index.value = { categories: [{ code: 'robot_platform', label: '机器人' }], devices }
  view.rows.value = [{ work_id: 'work:a', title: 'Robot study', relevance_status: 'included', first_public_date: '2026-09-01', first_public_date_precision: 'day', hardware_usage: devices.map(d => ({ hardware_id: d.hardware_id, category: d.category, review_status: 'verified', role: 'simulated_robot', setting: 'simulation', source_url: 'https://arxiv.org/html/2609.00001v1', statement: 'Simulator experiment' })) }]
}
test('model lists append without pagination and restore the displayed count from URL', async () => {
  const v = harness(); seed(v)
  assert.equal(v.visibleModels.value.length, 12)
  await v.moreModels()
  assert.equal(v.visibleModels.value.length, 24)
  assert.equal(v.url().searchParams.get('shown'), '24')
  v.setUrl('?shown=12'); v.readUrl()
  assert.equal(v.visibleModels.value.length, 12)
})
test('WUJI Hand phrase finds a generation-unresolved series and opens its complete source list', () => {
  const v = harness(); seed(v)
  v.modelQuery.value = 'Wuji Hand'; v.searchModels()
  assert.equal(v.models.value.length, 0)
  assert.equal(v.unresolved.value.length, 1)
  assert.equal(v.openSources.value.has('h:wuji'), true)
  assert.equal(v.url().searchParams.get('model_q'), 'Wuji Hand')
  v.setUrl('?device=h%3Awuji'); v.readUrl()
  assert.equal(v.unresolved.value[0].simulation_work_count, 1)
  assert.equal(v.openSources.value.has('h:wuji'), true)
})
test('chart uses specific model names and distinct work counts, not category totals', () => {
  const v = harness(); seed(v)
  const chart = v.chart()
  assert.equal(chart.yAxis.data.length, 12)
  assert.ok(chart.yAxis.data.every(name => name !== '机器人'))
  assert.ok(chart.series[0].data.every(row => row.value === 1))
})
test('source rows render every work and usage with direct URL, locus and validation boundaries', () => {
  const source = read('HardwareFrequencyRow.vue')
  const { descriptor } = parse(source)
  const script = compileScript(descriptor, { id: 'model-row' })
  assert.deepEqual(compileTemplate({ id: 'model-row', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } }).errors, [])
  assert.ok(source.includes('v-for="source in device.sources"'))
  assert.ok(source.includes('v-for="(usage, i) in source.usages"'))
  for (const field of ['usage.source_locator', 'usage.validation_context', 'usage.usage_scope', 'source.title']) assert.ok(source.includes(field), field)
  assert.ok(source.includes("import { hardwareEvidenceUrl } from '../lib/hardware-frequency.mjs'"))
  assert.ok(source.includes(':href="hardwareEvidenceUrl(usage)"'))
  assert.ok(source.includes('身份依据'))
})
