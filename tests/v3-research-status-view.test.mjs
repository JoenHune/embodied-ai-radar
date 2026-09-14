import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import ts from 'typescript'
import { computed, ref } from 'vue'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { eventDate, eventMonth } from '../docs/.vitepress/theme/lib/dates.ts'

const directory = new URL('../docs/.vitepress/theme/components/', import.meta.url)
const dashboard = fs.readFileSync(new URL('RadarDashboard.vue', directory), 'utf8')
const database = fs.readFileSync(new URL('DatabaseExplorer.vue', directory), 'utf8')

function projections(snapshot) {
  const code = dashboard.match(/\/\/ Research status projections: begin\.[\s\S]*?\/\/ Research status projections: end\./)?.[0]
  assert.ok(code, 'Use the actual production projection block, not a duplicated test implementation')
  const javascript = ts.transpileModule(code, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  const monthlySnapshot = ref(snapshot)
  const evidenceView = ref('as_of_month')
  const selectedEvidence = computed(() => evidenceView.value === 'retrospective' ? monthlySnapshot.value.retrospective_evidence : monthlySnapshot.value)
  const evidenceCutoff = computed(() => evidenceView.value === 'retrospective' ? monthlySnapshot.value.retrospective_evidence?.as_of : monthlySnapshot.value.evidence_as_of)
  const evidenceViewLabel = computed(() => evidenceView.value === 'retrospective' ? '今天回看' : '当月可用证据')
  const build = new Function('computed', 'monthlySnapshot', 'selectedEvidence', 'evidenceView', 'evidenceCutoff', 'evidenceViewLabel', 'withBase', 'eventDate', 'eventMonth',
    javascript + '\nreturn {selectedResearchStatuses,currentResearchStatuses,currentStatusCutoff,monthlyStatusEvents,followUpResearchStatuses,editorialStatusDependencies,dependencyNoticeSources,dependencyIsLater,dependencyExceedsSelectedCutoff,statusWorkUrl,selectedStatusContext,followUpStatusContext,statusTimeUpper}')
  return { monthlySnapshot, evidenceView, ...build(computed, monthlySnapshot, selectedEvidence, evidenceView, evidenceCutoff, evidenceViewLabel, path => '/radar' + path, eventDate, eventMonth) }
}

function fixture() {
  const july = { notice_id: 'notice:july', event_type: 'corrected', public_at: '2026-07-15', date_precision: 'day', source_url: 'https://example.test/july', summary_zh: '作者更正说明。' }
  const august = { notice_id: 'notice:august', event_type: 'withdrawn', public_at: '2026-08-24T07:00:55Z', date_precision: 'second', source_url: 'https://example.test/august', summary_zh: '后来撤回说明。' }
  const work = { work_id: 'work:x', title: '研究标题', as_of: '2026-07-31', status: 'corrected', validation_eligible: true, notices: [july], information_gaps: [] }
  return { month: '2026-07', evidence_as_of: '2026-07-31', coverage: { included_works: 100 }, executive_findings: [{ text: '不应被状态界面改写的旧叙述。' }],
    research_status: [work], retrospective_evidence: { as_of: '2026-08-31', research_status: [{ ...work, as_of: '2026-08-31', status: 'withdrawn', validation_eligible: false, notices: [july, august] }] },
    research_status_changes: [{ ...july, work_id: work.work_id, work_title: work.title }, { ...august, work_id: work.work_id, work_title: work.title }],
    editorial_status_dependencies: [{ claim_id: 'claim:old', section: 'direction_summaries', index: 4, code: 'D5', work_id: 'work:x', work_title: work.title, status: 'withdrawn', validation_eligible: false, as_of: '2026-08-31', notice_ids: ['notice:august'], review_state: 'needs_review' }] }
}

test('official status notices are not duplicated as unverified company/report evidence', () => {
  const code = database.match(/^const evidenceEvents = .+$/m)?.[0]
  assert.ok(code)
  const javascript = ts.transpileModule(code, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  const detail = ref({ evidence_events: [{ event_id: 'notice:event', research_status_notice_id: 'notice:withdrawn' }, { event_id: 'report:event', event_type: 'technical_report' }] })
  const projected = new Function('computed', 'detail', javascript + '\nreturn evidenceEvents')(computed, detail)
  assert.deepEqual(projected.value.map(row => row.event_id), ['report:event'])
  assert.equal(detail.value.evidence_events.length, 2)
})

test('history and retrospective select different state evidence without mutating old prose/counts', () => {
  const input = fixture()
  const before = structuredClone(input)
  const view = projections(input)
  assert.deepEqual(view.selectedResearchStatuses.value[0].notices.map(row => row.notice_id), ['notice:july'])
  assert.deepEqual(view.monthlyStatusEvents.value.map(row => row.notice_id), ['notice:july'])
  assert.deepEqual(view.followUpResearchStatuses.value[0].notices.map(row => row.notice_id), ['notice:august'])
  assert.match(view.followUpStatusContext(view.followUpResearchStatuses.value[0]), /不在所选证据截止 2026-07-31 的可用范围，不计入所选证据/)
  view.evidenceView.value = 'retrospective'
  assert.equal(view.selectedResearchStatuses.value[0].status, 'withdrawn')
  assert.equal(view.selectedResearchStatuses.value[0].notices.length, 2)
  assert.deepEqual(view.followUpResearchStatuses.value, [])
  assert.match(view.selectedStatusContext.value, /2026-08-31/)
  assert.deepEqual(input, before)
})

test('September status remains separately visible in both views when evidence ends in August', () => {
  const input = fixture()
  input.research_status = []
  input.retrospective_evidence.research_status = []
  input.research_status_changes = []
  const notice = { notice_id: 'notice:september', event_type: 'withdrawn', public_at: '2026-09-05', date_precision: 'day', source_url: 'https://example.test/september', summary_zh: '九月才发布的官方撤回通知。' }
  input.research_status_current = [{ work_id: 'work:x', title: '研究标题', status: 'withdrawn', validation_eligible: false, as_of: '2026-09-06', notices: [notice] }]
  input.editorial_status_dependencies[0].notice_ids = [notice.notice_id]
  input.editorial_status_dependencies[0].as_of = '2026-09-06'
  const before = structuredClone(input)
  const view = projections(input)
  for (const mode of ['as_of_month', 'retrospective']) {
    view.evidenceView.value = mode
    assert.deepEqual(view.selectedResearchStatuses.value, [], 'Do not replace the selected historical evidence with current status')
    assert.deepEqual(view.monthlyStatusEvents.value, [], 'A September notice is not a July publication event')
    assert.deepEqual(view.followUpResearchStatuses.value[0].notices.map(row => row.notice_id), ['notice:september'])
    assert.equal(view.currentStatusCutoff.value, '2026-09-06')
    const context = view.followUpStatusContext(view.followUpResearchStatuses.value[0])
    assert.match(context, /最新综合状态截至 2026-09-06/)
    assert.match(context, new RegExp(mode === 'retrospective' ? '所选证据截止 2026-08-31' : '所选证据截止 2026-07-31'))
    assert.equal(view.dependencyExceedsSelectedCutoff(input.editorial_status_dependencies[0]), true)
    assert.deepEqual(view.dependencyNoticeSources(input.editorial_status_dependencies[0]).map(row => row.source_url), ['https://example.test/september'])
  }
  assert.deepEqual(input, before)
})

test('current rows have independent cutoffs and explicit empty current is not stale fallback', () => {
  const input = fixture()
  const august = input.retrospective_evidence.research_status[0]
  input.research_status_current = [
    { ...august, as_of: '2026-09-03' },
    { ...august, work_id: 'work:y', as_of: '2026-09-06' },
  ]
  const view = projections(input)
  assert.equal(view.currentStatusCutoff.value, '2026-09-06')
  assert.match(view.followUpStatusContext(view.followUpResearchStatuses.value[0]), /最新综合状态截至 2026-09-03/)
  view.monthlySnapshot.value.research_status_current = []
  assert.deepEqual(view.currentResearchStatuses.value, [])
  assert.deepEqual(view.followUpResearchStatuses.value, [])
})

test('follow-up filtering uses selected cutoff and conservative explicit date precision', () => {
  const input = fixture()
  const work = input.retrospective_evidence.research_status[0]
  const notice = work.notices[1]
  input.research_status_current = [{ ...work, as_of: '2026-09-06', notices: [
    { ...notice, notice_id: 'within-august', public_at: '2026-08-31T15:59:59Z', date_precision: 'second' },
    { ...notice, notice_id: 'september-boundary', public_at: '2026-08-31T16:00:00Z', date_precision: 'second' },
    { ...notice, notice_id: 'unknown', public_at: '2026-09-05', date_precision: 'unknown' },
  ] }]
  const view = projections(input)
  view.evidenceView.value = 'retrospective'
  assert.deepEqual(view.followUpResearchStatuses.value[0].notices.map(row => row.notice_id), ['september-boundary'])
  assert.equal(view.statusTimeUpper('invalid'), null)
  assert.equal(view.statusTimeUpper('2026-09-05T00:00:00'), null)
})

test('dependency links resolve only its work and notices; missing IDs cannot invent sources', () => {
  const input = fixture()
  const view = projections(input)
  const dependency = input.editorial_status_dependencies[0]
  assert.equal(view.dependencyIsLater(dependency), true)
  assert.equal(view.dependencyIsLater({ ...dependency, notice_ids: ['notice:july'] }), false)
  assert.equal(view.dependencyIsLater({ ...dependency, notice_ids: ['missing'] }), false)
  assert.deepEqual(view.dependencyNoticeSources({ ...dependency, notice_ids: ['notice:august', 'missing'] }).map(row => row.source_url), ['https://example.test/august'])
  assert.deepEqual(view.dependencyNoticeSources({ ...dependency, work_id: 'work:other' }), [])
  const link = new URL(view.statusWorkUrl('work:x'), 'https://example.test')
  assert.equal(link.searchParams.get('work'), 'work:x')
  assert.equal(link.searchParams.get('relevance'), 'all')
  assert.equal(link.searchParams.has('organizations'), false)
  assert.equal(link.searchParams.has('from'), false, 'Do not hide an older work behind the current notice month filter')
})

test('actual publication lane respects Shanghai month and does not assign unknown/year dates', () => {
  const input = fixture()
  input.month = '2026-08'
  const common = { work_id: 'work:x', event_type: 'withdrawn', source_url: 'https://example.test/notice' }
  input.research_status_changes = [
    { ...common, notice_id: 'august', public_at: '2026-08-31T15:59:59Z', date_precision: 'second' },
    { ...common, notice_id: 'september', public_at: '2026-08-31T16:00:00Z', date_precision: 'second' },
    { ...common, notice_id: 'month', public_at: '2026-08', date_precision: 'month' },
    { ...common, notice_id: 'unknown', public_at: '2026-08-24', date_precision: 'unknown' },
    { ...common, notice_id: 'year', public_at: '2026-08-01', date_precision: 'year' },
  ]
  const view = projections(input)
  assert.deepEqual(view.monthlyStatusEvents.value.map(row => row.notice_id), ['august', 'month'])
})

test('month changes drop previous dependencies and never manufacture a state', () => {
  const view = projections(fixture())
  view.monthlySnapshot.value = { month: '2026-06', evidence_as_of: '2026-06-30', retrospective_evidence: { as_of: '2026-08-31' } }
  assert.deepEqual(view.selectedResearchStatuses.value, [])
  assert.deepEqual(view.followUpResearchStatuses.value, [])
  assert.deepEqual(view.monthlyStatusEvents.value, [])
  assert.deepEqual(view.editorialStatusDependencies.value, [])
})

test('database status warning precedes the summary and result badge never hides rows', () => {
  const template = parse(database).descriptor.template.content
  const heading = template.indexOf('id="work-detail-title"')
  const warning = template.indexOf('<ResearchStatusNotice')
  const summary = template.indexOf('<p v-if="detail.summary_zh">')
  assert.ok(heading < warning && warning < summary)
  assert.match(template, /:value="detail\.research_status"/)
  assert.match(template, /<ResearchCard v-for="row in rows" :key="row\.id" :work="researchCard\(row\)"/)
  assert.match(template, /@details="openWork"/)
  const card = parse(fs.readFileSync(new URL('../docs/.vitepress/theme/components/ResearchCard.vue', import.meta.url), 'utf8')).descriptor.template.content
  assert.match(card, /v-if="notices\.length"/)
  assert.match(card, /结果不作验证/)
  assert.ok(card.indexOf('research-card-alert') < card.indexOf('research-card-summary'))
})

test('monthly dependencies are prominent, actual events separate, and preserved prose stays unchanged', () => {
  const template = parse(dashboard).descriptor.template.content
  assert.ok(template.indexOf('v-if="editorialStatusDependencies.length"') < template.indexOf('class="v3-findings"'))
  assert.match(template, /后续状态提醒：保留的研究判断存在受影响引用/)
  assert.match(template, /原始编辑文本没有改写/)
  assert.match(template, /撤回、更正与后续状态/)
  assert.match(template, /v-for="notice in monthlyStatusEvents"/)
  assert.match(template, /notice\.public_at, notice\.date_precision/)
  assert.match(template, /不作为研究组归属证据/)
  assert.match(template, /后续通知提醒 · 不计入所选证据截止/)
  assert.match(template, /:context="followUpStatusContext\(row\)"/)
  assert.match(template, /\{\{ finding\.text \}\}/)
  assert.match(template, /:href="notice\.source_url" target="_blank" rel="noopener noreferrer"/)
})

for (const [name, source] of [['RadarDashboard.vue', dashboard], ['DatabaseExplorer.vue', database]]) test(`${name} template compiles with the shared notice binding`, () => {
  const { descriptor, errors } = parse(source, { filename: name })
  assert.deepEqual(errors, [])
  const script = compileScript(descriptor, { id: 'status-view-test' })
  const result = compileTemplate({ source: descriptor.template.content, filename: name, id: 'status-view-test',
    compilerOptions: { bindingMetadata: script.bindings, expressionPlugins: ['typescript'] } })
  assert.deepEqual(result.errors, [])
  assert.ok(script.bindings.ResearchStatusNotice)
})
