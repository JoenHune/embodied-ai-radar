import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import config from '../docs/.vitepress/config.ts'

const read = path => fs.readFileSync(new URL(`../${path}`, import.meta.url), 'utf8')
test('seven top-level navigation items retain existing entry points and add equipment within menus', () => {
  const nav = config.themeConfig.nav
  assert.equal(nav.length, 7)
  assert.deepEqual(nav.map(item => item.text), ['总览', '趋势', '月度', '人物与组织', '研究库', '动态', '方法'])
  assert.deepEqual(nav.find(item => item.text === '趋势').items.map(item => item.link), ['/trends/', '/trends/loco-manip/'])
  assert.deepEqual(nav.find(item => item.text === '研究库').items.map(item => item.link), ['/database/', '/hardware/'])
  assert.ok(nav.find(item => item.text === '人物与组织').items.some(item => item.link === '/organizations/people/'))
})
test('new page routes register their actual asynchronous component and methods document', () => {
  const theme = read('docs/.vitepress/theme/index.ts')
  for (const [path, name] of [['docs/hardware/index.md', 'HardwareRadar'], ['docs/trends/loco-manip/index.md', 'LocoManipRadar']]) {
    assert.match(read(path), new RegExp(`<${name} />`))
    assert.match(theme, new RegExp(`app\\.component\\('${name}', defineAsyncComponent\\(`))
    assert.match(theme, new RegExp(`import\\('\\./components/${name}\\.vue'\\)`))
  }
  assert.ok(config.themeConfig.sidebar['/methods/'][0].items.some(item => item.link === '/methods/equipment-loco'))
  const methods = read('docs/methods/equipment-loco.md')
  for (const term of ['未登记', '未明型号', '基线', '标定', '回放', '真机闭环', '候选判断']) assert.ok(methods.includes(term), term)
  assert.match(methods, /不进入本页已核验趋势柱/)
})
test('home shortcuts are small source-aware links with a dynamic provisional month', () => {
  const home = read('docs/.vitepress/theme/components/RadarDashboard.vue')
  assert.match(home, /<nav v-if="mode === 'home'" class="v3-research-shortcuts"/)
  assert.match(home, /\/monthly\/\?month=\$\{manifest\.provisional_month\}/)
  assert.match(home, /withBase\('\/hardware\/'\)/)
  assert.match(home, /withBase\('\/trends\/loco-manip\/'\)/)
  assert.doesNotMatch(home, /import\(.+(?:HardwareRadar|LocoManipRadar)/)
})

function locoHarness() {
  const filename = 'docs/.vitepress/theme/components/LocoManipRadar.vue'
  const { descriptor, errors } = parse(read(filename))
  assert.deepEqual(errors, [])
  const script = compileScript(descriptor, { id: 'loco-test' })
  const template = compileTemplate({ filename, id: 'loco-test', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } })
  assert.deepEqual(template.errors, [])
  let chartFactory
  const listeners = new Map()
  const mounted = []
  const unmounted = []
  let uri = new URL('https://radar.example/embodied-ai-radar/trends/loco-manip/')
  const router = {}
  const window = { get location() { return { href: uri.href, search: uri.search, pathname: uri.pathname } }, history: { state: {}, pushState(_state, _title, value) { uri = new URL(value, uri) } }, addEventListener(event, fn) { listeners.set(event, fn) }, removeEventListener(event) { listeners.delete(event) } }
  const context = { Map, Set, URL, URLSearchParams, AbortController, window,
    computed: fn => ({ get value() { return fn() } }), ref: value => ({ value }), nextTick: async () => {},
    onMounted: fn => mounted.push(fn), onBeforeUnmount: fn => unmounted.push(fn), useRouter: () => router,
    withBase: value => value, eventDate: value => value, echarts: { use() {} },
    BarChart: {}, AriaComponent: {}, GridComponent: {}, LegendComponent: {}, TooltipComponent: {}, CanvasRenderer: {},
    useEChart: factory => { chartFactory = factory; return { element: { value: null } } },
    chartTokens: () => ({ palette: ['#111', '#222'], background: '#fff', divider: '#ddd', muted: '#666', text: '#111' }),
    fetch: async () => ({ ok: false }),
  }
  const source = descriptor.scriptSetup.content.replace(/^import .*$/gm, '') + '\nglobalThis.api = { data, rows, groups, scope, month, filtered, visible, shown, readUrl, more, monthOf, observationIsCandidate, dependencyStatus, reviewIsCandidate, candidateReason };'
  vm.runInNewContext(ts.transpile(source, { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None }), context)
  return { ...context.api, chart: () => chartFactory(), setUrl: value => { uri = new URL(value, uri) }, uri: () => uri, listeners, mounted, unmounted, router }
}
test('loco scope remains separate from validation, and pending dependencies never become verified claims', () => {
  const view = locoHarness()
  assert.match(view.groups.find(group => group.key === 'core').note, /核心分组不自动代表真机闭环/)
  const observation = { review_status: 'verified', candidate_work_ids: [], supporting_work_status: { 'work:a': { relevance_status: 'included', review_status: 'verified', effective_scope: 'core' } } }
  assert.equal(view.observationIsCandidate(observation), false)
  assert.equal(view.observationIsCandidate({ ...observation, review_status: 'candidate' }), true)
  assert.equal(view.observationIsCandidate({ ...observation, candidate_work_ids: ['work:a'] }), true)
  const pending = { ...observation, supporting_work_status: { 'work:a': { relevance_status: 'manual_review', review_status: 'verified', effective_scope: 'candidates' } } }
  assert.equal(view.observationIsCandidate(pending), true)
  assert.match(view.dependencyStatus(pending, 'work:a'), /分类待复核/)
  assert.equal(view.observationIsCandidate({}), true, 'missing review status must not imply verified')
  assert.equal(view.reviewIsCandidate({ review_status: 'verified', relevance_status: 'manual_review', effective_scope: 'candidates' }), true)
  assert.match(view.candidateReason({ candidate_reason: 'catalog_not_included' }), /不能自动升级/)
})
test('loco chart excludes candidates and marks provisional points without assigning year-only dates to months', () => {
  const view = locoHarness()
  view.data.value = { monthly: [{ month: '2026-09', provisional: true, core: 2, support: 3, candidates: 99 }] }
  const chart = view.chart()
  assert.deepEqual(Array.from(chart.series, row => row.name), ['核心已核验', '支撑已核验'])
  assert.equal(chart.series[0].data[0].itemStyle.borderType, 'dashed')
  assert.equal(chart.series[0].data[0].value, 2)
  assert.equal(view.monthOf({ first_public_date: '2026-01-01', first_public_date_precision: 'year' }), 'unknown')
  assert.equal(view.monthOf({ first_public_date: '2026-09', first_public_date_precision: 'month' }), '2026-09')
})
test('loco appends twelve items, shares state and restores candidate browsing from URL', async () => {
  const view = locoHarness()
  const rows = Array.from({ length: 30 }, (_, i) => ({ work_id: `work:${i}`, title: `Work ${i}`, first_public_date: '2026-09-01', first_public_date_precision: 'day' }))
  view.rows.value = rows
  view.data.value = { reviews: [], work_ids: { core: rows.map(row => row.work_id), support: [], candidates: ['work:1'], excluded: [] } }
  assert.equal(view.visible.value.length, 12)
  await view.more()
  assert.equal(view.visible.value.length, 24)
  assert.equal(view.uri().searchParams.get('shown'), '24')
  view.setUrl('?scope=candidates&month=2026-09&shown=12')
  view.readUrl()
  assert.equal(view.scope.value, 'candidates')
  assert.equal(view.filtered.value.length, 1)
  view.setUrl('?scope=core&shown=24')
  view.readUrl()
  assert.equal(view.visible.value.length, 24)
})
