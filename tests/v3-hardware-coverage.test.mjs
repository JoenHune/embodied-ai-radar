import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import { createHash, webcrypto } from 'node:crypto'
import ts from 'typescript'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { eventDate } from '../docs/.vitepress/theme/lib/dates.ts'

const component = fs.readFileSync(new URL('../docs/.vitepress/theme/components/HardwareCoverage.vue', import.meta.url), 'utf8')
const descriptor = parse(component).descriptor
const countFields = ['denominator', 'metadata_screened_work_count', 'metadata_missing_abstract_work_count', 'full_text_available_work_count', 'full_text_screened_current_dictionary_work_count', 'verified_relationship_work_count', 'verified_usage_relationship_count', 'full_text_not_attempted_work_count', 'full_text_failed_work_count', 'partial_text_available_work_count', 'full_text_available_pending_scan_work_count']
const counts = (denominator, values = {}) => ({ ...Object.fromEntries(countFields.map(key => [key, 0])), denominator, metadata_screened_work_count: denominator, full_text_not_attempted_work_count: denominator, ...values })
const revision = { schema_version: '1', dataset_version: 'revision-a', dictionary_hash: 'dictionary-a', metadata_scope: 'metadata_only' }
const summary = () => ({ ...revision, data_through: '2026-09-14', dictionary_version: '1', all_works: counts(42720, { verified_relationship_work_count: 33, verified_usage_relationship_count: 163 }), included: counts(9992, { verified_relationship_work_count: 29, verified_usage_relationship_count: 147 }), by_direction: [{ primary_direction: 'D10', all_works: counts(4), included: counts(2) }, { primary_direction: 'D2', all_works: counts(5), included: counts(1) }], by_month: [{ first_public_month: '2026-07', all_works: counts(4), included: counts(2) }, { first_public_month: 'unknown', all_works: counts(1), included: counts(0) }, { first_public_month: '2026-09', all_works: counts(5), included: counts(1) }], by_relevance: [{ relevance_status: 'excluded', all_works: counts(4), included: counts(0) }, { relevance_status: 'included', all_works: counts(5), included: counts(5) }], downloads: { coverage: '/downloads/equipment/hardware-coverage.jsonl.gz' } })
const work = (id = 'arxiv:2609.07859', overrides = {}) => ({ work_id: id, metadata_hits: 0, body_source_state: 'not_attempted', body_scan_status: 'not_attempted', body_hits: 0, verified_count: 0, full_text_scanned: false, partial_text_scanned: false, relevance: 'excluded', ...overrides })
const model = (number = 0, ids = ['arxiv:2609.07859']) => ({ dictionary_id: `model:unitree-g1-${number}`, name: `Unitree G1 ${number}`, category: 'robot_platform', identity_level: 'model_specified', evidence_status: 'unverified_mention', usage_inference: 'none', metadata_work_count: ids.length, body_work_count: 0, candidate_work_count: ids.length, included_candidate_work_count: Math.min(ids.length, 1), work_ids: ids, metadata_work_ids: ids, body_work_ids: [] })
const shard = id => createHash('sha1').update(id).digest('hex').slice(0, 2)
const tick = () => new Promise(resolve => setImmediate(resolve))

function harness({ compact = false, routes = {} } = {}) {
  const requests = []
  let dispose
  const responseRoutes = { '/api/v1/equipment/coverage-summary.json': summary(), '/api/v1/equipment/coverage-model-candidates.json': { ...revision, models: [model()] }, ...routes }
  const context = {
    Set, Map, Object, URLSearchParams, AbortController, TextEncoder, Uint8Array, crypto: webcrypto,
    computed: fn => ({ get value() { return fn() } }), ref: value => ({ value }), nextTick: async () => {},
    onMounted() {}, onBeforeUnmount(fn) { dispose = fn }, withBase: value => '/base' + value, eventDate,
    defineProps: () => ({ compact }), withDefaults: (values, defaults) => ({ ...defaults, ...values }),
    fetch: async (url, options) => {
      const path = url.replace(/^\/base/, '')
      requests.push({ path, options })
      const value = responseRoutes[path]
      if (typeof value === 'function') return value(url, options)
      if (value instanceof Error) throw value
      return { ok: value !== undefined, status: value === undefined ? 404 : 200, json: async () => structuredClone(value) }
    },
  }
  const source = descriptor.scriptSetup.content.replace(/^import .*$/gm, '') + '\nglobalThis.view = { props, revisionMismatch, summary, loading, error, cohort, selected, cohortLabel, dimension, groups, groupLabel, modelIndex, modelsLoading, modelsError, modelQuery, modelCategory, onlyMentions, shownModels, filteredModels, visibleModels, openModels, shownWorks, visibleWorkIds, toggleModel, moreWorks, resetModels, number, workInput, workResult, workStatus, workError, queriedId, loadSummary, loadModels, lookupWork, inspectWork, loadTitle, titles, titleErrors, titleLoading, workUrl, downloadHref, analysisClock, reviewClock, clockLabel };'
  vm.runInNewContext(ts.transpile(source, { target: ts.ScriptTarget.ES2022 }), context)
  return { ...context.view, requests, routes: responseRoutes, dispose: () => dispose() }
}

test('coverage Vue script and template compile with compact and full modes', () => {
  assert.deepEqual(parse(component).errors, [])
  const script = compileScript(descriptor, { id: 'coverage-view' })
  assert.deepEqual(compileTemplate({ id: 'coverage-view', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } }).errors, [])
  const page = fs.readFileSync(new URL('../docs/hardware/coverage.md', import.meta.url), 'utf8')
  assert.ok(page.includes('<HardwareCoverage />'))
  assert.ok(page.includes('layout: page'))
})
test('coverage labels and filters inertial mentions without upgrading them to verified uses', async () => {
  assert.match(component, /inertial_sensor:\s*'惯性传感器'/)
  const imu = { ...model(1), name: 'TransducerM TM171', category: 'inertial_sensor' }
  const view = harness({ routes: { '/api/v1/equipment/coverage-model-candidates.json': { ...revision, models: [model(), imu] } } })
  await view.loadSummary(); await view.loadModels()
  view.modelCategory.value = 'inertial_sensor'
  assert.equal(view.filteredModels.value.length, 1)
  assert.equal(view.filteredModels.value[0].name, 'TransducerM TM171')
  assert.equal(view.filteredModels.value[0].evidence_status, 'unverified_mention')
  assert.equal(view.filteredModels.value[0].usage_inference, 'none')
})

test('compact mode reads summary only and keeps both verified denominators separate', async () => {
  const view = harness({ compact: true })
  await view.loadSummary(); await tick()
  assert.deepEqual(view.requests.map(row => row.path), ['/api/v1/equipment/coverage-summary.json'])
  assert.equal(view.selected.value.denominator, 42720)
  assert.equal(view.selected.value.verified_relationship_work_count, 33)
  view.cohort.value = 'included'
  assert.equal(view.selected.value.denominator, 9992)
  assert.equal(view.selected.value.verified_relationship_work_count, 29)
  assert.equal(view.summary.value.all_works.denominator, 42720)
  assert.equal(view.selected.value.full_text_screened_current_dictionary_work_count, 0)
})

test('coverage keeps the analysis date separate from a safe Beijing review visibility cutoff', async () => {
  const value = { ...summary(), source_review_as_of: '2026-09-14T16:00:00.123456Z' }, before = structuredClone(value)
  const view = harness({ compact: true, routes: { '/api/v1/equipment/coverage-summary.json': value } })
  await view.loadSummary()
  assert.equal(view.analysisClock.value, '2026-09-14')
  assert.equal(view.reviewClock.value, '2026-09-15 00:00:00（北京时间）')
  assert.deepEqual(value, before)
  assert.equal(view.selected.value.denominator, value.all_works.denominator)
  for (const bad of [undefined, null, '/Users/private', '<script>x</script>', '2026-09-14T16:00:00', '2026-02-30T00:00:00Z', '2026-09-14T24:00:00Z', 123]) {
    view.summary.value.source_review_as_of = bad
    assert.equal(view.reviewClock.value, '')
  }
  assert.equal(view.clockLabel('2026-02-30', 'day'), '')
  assert.equal(view.clockLabel('/private/cache', 'day'), '')
  assert.match(component, /语料分析截至/)
  assert.match(component, /v-if="reviewClock">来源\/阅读核验记录可见截至/)
  view.props.expectedVersion = 'wrong'
  assert.equal(view.revisionMismatch.value, true)
})

test('full initial load gets only two small coverage APIs, not 42720 work rows', async () => {
  const view = harness()
  await view.loadSummary(); await tick()
  assert.deepEqual(view.requests.map(row => row.path).sort(), ['/api/v1/equipment/coverage-model-candidates.json', '/api/v1/equipment/coverage-summary.json'])
  assert.equal(view.modelIndex.value.models.length, 1)
  view.toggleModel('model:unitree-g1-0')
  assert.equal(view.requests.length, 2)
  assert.equal(view.visibleWorkIds(view.modelIndex.value.models[0]).length, 1)
})
test('compact progress cannot silently mix revisions with the parent model frequency', async () => {
  const view = harness({ compact: true })
  await view.loadSummary()
  assert.equal(view.revisionMismatch.value, false)
  view.props.expectedVersion = 'older-equipment-revision'
  assert.equal(view.revisionMismatch.value, true)
  view.props.expectedVersion = revision.dataset_version
  assert.equal(view.revisionMismatch.value, false)
  assert.match(component, /v-else-if="error \|\| revisionMismatch"/)
  assert.match(fs.readFileSync(new URL('../docs/.vitepress/theme/components/HardwareRadar.vue', import.meta.url), 'utf8'), /:expected-version="index\?\.dataset_version"/)
})

test('summary failure clears stale values and remains unknown, not zero', async () => {
  const view = harness({ compact: true })
  await view.loadSummary()
  view.routes['/api/v1/equipment/coverage-summary.json'] = new Error('network failed')
  await view.loadSummary()
  assert.equal(view.summary.value, null)
  assert.equal(view.selected.value, null)
  assert.match(view.error.value, /未知/)
  assert.equal(view.number(undefined), '未知')
  assert.equal(view.number(null), '未知')
  assert.equal(view.number(0), '0')
  assert.equal(view.loading.value, false)
})

test('model fetch failure or revision mismatch does not turn into an empty model inventory', async () => {
  for (const value of [new Error('network'), { ...revision, dataset_version: 'stale', models: [model()] }, { ...revision, models: [{ ...model(), evidence_status: 'verified' }] }]) {
    const view = harness({ routes: { '/api/v1/equipment/coverage-model-candidates.json': value } })
    await view.loadSummary(); await tick()
    assert.ok(view.summary.value)
    assert.equal(view.modelIndex.value, null)
    assert.ok(view.modelsError.value)
  }
})

test('coverage groups are sorted by numeric direction and descending month without fabricating dates', async () => {
  const view = harness({ compact: true })
  await view.loadSummary()
  assert.equal(view.groups.value[0].primary_direction, 'D2')
  view.dimension.value = 'by_month'
  assert.equal(view.groups.value[0].first_public_month, '2026-09')
  assert.equal(view.groups.value.at(-1).first_public_month, 'unknown')
  assert.equal(view.groupLabel(view.groups.value.at(-1)), '月份待核验')
  view.dimension.value = 'by_relevance'
  assert.equal(view.groups.value[0].relevance_status, 'included')
})

test('an exact work lookup reads only its hash shard and keeps no-hit unverified', async () => {
  const id = 'arxiv:2609.07859'
  const path = `/api/v1/equipment/coverage/works/${shard(id)}.json`
  const view = harness({ compact: true, routes: { [path]: { ...revision, by_work: { [id]: work(id) } } } })
  await view.loadSummary()
  view.workInput.value = id
  await view.lookupWork()
  assert.equal(view.workStatus.value, 'found')
  assert.equal(view.workResult.value.metadata_hits, 0)
  assert.equal(view.workResult.value.body_scan_status, 'not_attempted')
  assert.equal(view.workResult.value.verified_count, 0)
  assert.deepEqual(view.requests.slice(1).map(row => row.path), [path])
  assert.equal(view.workUrl(id), '/base/database/?work=arxiv%3A2609.07859&relevance=all')
})

test('missing, failed, wrong-work and stale work responses never become no-hardware claims', async () => {
  const id = 'arxiv:2609.07859'
  const path = `/api/v1/equipment/coverage/works/${shard(id)}.json`
  for (const [response, expected] of [[{ ...revision, by_work: {} }, 'missing'], [new Error('network'), 'error'], [{ ...revision, by_work: { [id]: work('arxiv:wrong') } }, 'error'], [{ ...revision, dictionary_hash: 'old-dictionary', by_work: { [id]: work(id) } }, 'error']]) {
    const view = harness({ compact: true, routes: { [path]: response } })
    await view.loadSummary(); view.workInput.value = id; await view.lookupWork()
    assert.equal(view.workStatus.value, expected)
    assert.equal(view.workResult.value, null)
  }
})

test('work lookup shows PDF receipt state separately when HTML was never acquired', async () => {
  const id = 'work:pdf-only'
  const path = `/api/v1/equipment/coverage/works/${shard(id)}.json`
  const row = work(id, { pdf: { source_count: 1, reading_count: 1 } })
  const view = harness({ compact: true, routes: { [path]: { ...revision, by_work: { [id]: row } } } })
  await view.loadSummary(); view.workInput.value = id; await view.lookupWork()
  assert.equal(view.workStatus.value, 'found')
  assert.equal(view.workResult.value.body_source_state, 'not_attempted')
  assert.equal(view.workResult.value.pdf.reading_count, 1)
  assert.match(component, /HTML正文获取状态/)
  assert.match(component, /<dt>PDF原文<\/dt>/)
  for (const pdf of [null, [], { source_count: 0, reading_count: 0 }, { source_count: 1, reading_count: 2 }]) {
    const invalid = harness({ compact: true, routes: { [path]: { ...revision, by_work: { [id]: work(id, { pdf }) } } } })
    await invalid.loadSummary(); invalid.workInput.value = id; await invalid.lookupWork()
    assert.equal(invalid.workStatus.value, 'error')
    assert.equal(invalid.workResult.value, null)
  }
})

test('model and source lists reveal bounded batches without hidden full-library requests', async () => {
  const models = Array.from({ length: 25 }, (_, i) => model(i, Array.from({ length: 30 }, (_, n) => `arxiv:2609.${String(n).padStart(5, '0')}`)))
  const view = harness({ routes: { '/api/v1/equipment/coverage-model-candidates.json': { ...revision, models } } })
  await view.loadSummary(); await tick()
  assert.equal(view.visibleModels.value.length, 12)
  view.shownModels.value += 12
  assert.equal(view.visibleModels.value.length, 24)
  const first = view.visibleModels.value[0]
  assert.equal(view.visibleWorkIds(first).length, 12)
  view.moreWorks(first.dictionary_id)
  assert.equal(view.visibleWorkIds(first).length, 24)
  assert.equal(view.requests.length, 2)
  view.modelQuery.value = 'not-found'; view.resetModels()
  assert.equal(view.filteredModels.value.length, 0)
})

test('titles are an explicit per-work request with catalogue revision check and hash-shard cache', async () => {
  const id = 'arxiv:2609.07859'
  const path = `/api/v1/works/${shard(id)}.json`
  const view = harness({ compact: true, routes: { '/api/v1/catalog-manifest.json': { dataset_version: revision.dataset_version }, [path]: [{ work_id: id, title: 'A robotics study', abstract: 'Not retained in the title cache' }] } })
  await view.loadSummary()
  assert.equal(view.requests.length, 1)
  await view.loadTitle(id)
  assert.equal(view.titles.value[id], 'A robotics study')
  assert.equal(view.requests.length, 3)
  await view.loadTitle(id)
  assert.equal(view.requests.length, 3)
  const stale = harness({ compact: true, routes: { '/api/v1/catalog-manifest.json': { dataset_version: 'old' }, [path]: [{ work_id: id, title: 'Wrong version' }] } })
  await stale.loadSummary(); await stale.loadTitle(id)
  assert.equal(stale.titles.value[id], undefined)
  assert.ok(stale.titleErrors.value[id])
  assert.equal(stale.requests.length, 2)
})

test('copy and links explicitly distinguish metadata, body text, and unverified mention counts', () => {
  for (const phrase of ['元数据筛查 ≠ 正文文本扫描 ≠ 设备使用关系核验', '两个分母不混用', '正文文本不包含图片', '未核验不是“无硬件”', '名称提及不是设备使用频次', '本区保留全库候选出处', '状态未知', '未核验提及', '尚未建立，不等于没有使用']) assert.ok(component.includes(phrase), phrase)
  assert.ok(component.includes(':href="downloadHref" download'))
  assert.ok(component.includes('v-if="workResult.full_text_scanned || workResult.partial_text_scanned"'))
  assert.ok(component.includes('尚未完成HTML正文文本扫描，命中数未知'))
  assert.ok(component.includes('withBase(\'/methods/equipment-loco\')'))
  assert.ok(!component.includes('v-html'))
  assert.ok(!descriptor.template.content.includes('100%'))
})
