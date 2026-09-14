import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'

const source = fs.readFileSync(new URL('../docs/.vitepress/theme/components/FulltextReadings.vue', import.meta.url), 'utf8')
const descriptor = parse(source).descriptor
const entry = (id = 'a', extra = {}) => ({ reading_id: id, work_id: `arxiv:2407.0000${id}`, title: `Paper ${id}`, relevance_status: 'included', source_url: 'https://arxiv.org/html/2407.00001v1', version: 'v1', read_completed_at: '2026-09-14T08:00:00Z', checked_table_count: 2, reader_kind: 'AI', reading_status: 'completed', human_reviewed: false, images_inspected: false, supplementary_materials_inspected: false, text_scope: 'complete_available_article_text', findings_zh: [{ text_zh: '原文新增发现', source_locator: 'S4; A1' }], limitations_zh: [{ text_zh: '仅仿真，不能当真机部署', source_locator: 'S5' }], ...extra })
const envelope = records => ({ schema_version: '1', dataset_version: 'revision', dictionary_hash: 'dictionary', assurance: 'self_attested_AI_reading_not_human_review', records })
function harness(value = envelope([entry()])) {
  const requests = []
  const props = { expectedVersion: 'revision', dictionaryHash: 'dictionary', cohort: 'all_works' }
  const ctx = { URL, URLSearchParams, AbortController, Set, computed: fn => ({ get value() { return fn() } }), ref: value => ({ value }),
    defineProps: () => props, onMounted() {}, onBeforeUnmount() {}, withBase: value => value, eventDate: value => value,
    fetch: async (...args) => { requests.push(args); if (value instanceof Error) throw value; return { ok: true, json: async () => value } } }
  vm.runInNewContext(ts.transpile(descriptor.scriptSetup.content.replace(/^import .*$/gm, '') + '\nglobalThis.view = {load,readings,error,loading,filtered,visible,shown,versionMismatch,sourceAllowed,sourceParts,locationUrl};', { target: ts.ScriptTarget.ES2022 }), ctx)
  return { ...ctx.view, props, requests }
}
test('reading view compiles and is only mounted after an explicit expand action', () => {
  const script = compileScript(descriptor, { id: 'fulltext-reading-view' })
  assert.deepEqual(compileTemplate({ id: 'fulltext-reading-view', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } }).errors, [])
  const parent = fs.readFileSync(new URL('../docs/.vitepress/theme/components/HardwareCoverage.vue', import.meta.url), 'utf8')
  assert.match(parent, /const showReadings = ref\(false\)/)
  assert.match(parent, /<FulltextReadings v-else/)
  assert.match(parent, /AI已通读可用HTML文字/)
})
test('fetches one small readings API and never the full work catalog', async () => {
  const view = harness(); await view.load()
  assert.equal(view.error.value, '')
  assert.deepEqual(view.requests.map(r => r[0]), ['/api/v1/equipment/coverage-readings.json'])
  assert.equal(view.visible.value.length, 1)
  assert.equal(view.readings.value[0].human_reviewed, false)
})
test('filters cohort and appends records without changing pages or inferring a human review', async () => {
  const view = harness(envelope(Array.from({ length: 25 }, (_, i) => entry(String(i), { relevance_status: i === 0 ? 'excluded' : 'included' }))))
  await view.load(); assert.equal(view.visible.value.length, 12)
  view.shown.value += 12; assert.equal(view.visible.value.length, 24)
  view.props.cohort = 'included'; assert.equal(view.filtered.value.length, 24)
})
test('prepared packets, unsafe sources and fabricated media/human review claims are rejected', async () => {
  for (const extra of [{ reading_status: 'prepared_not_read' }, { human_reviewed: true }, { images_inspected: true }, { supplementary_materials_inspected: true }, { source_url: 'https://example.com/private' }, { source_url: 'javascript:alert(1)' }, { text_scope: 'abstract_only' }]) {
    const view = harness(envelope([entry('bad', extra)])); await view.load()
    assert.ok(view.error.value); assert.equal(view.readings.value.length, 0)
  }
})
test('stale versions and errors remain unknown; changing the parent version hides old readings', async () => {
  for (const response of [{ ...envelope([entry()]), dataset_version: 'stale' }, new Error('network')]) {
    const view = harness(response); await view.load(); assert.ok(view.error.value)
  }
  const view = harness(); await view.load(); view.props.expectedVersion = 'next'
  assert.equal(view.versionMismatch.value, true)
  assert.match(source, /error \|\| versionMismatch/)
})
test('each clause retains its original section links and limitations are not omitted', async () => {
  const view = harness(); await view.load()
  const row = view.readings.value[0]
  assert.deepEqual(Array.from(view.sourceParts(row.findings_zh[0])), ['S4', 'A1'])
  assert.equal(view.locationUrl(row, 'S4'), row.source_url + '#S4')
  assert.match(source, /row\.limitations_zh/)
  assert.match(source, /非人工审稿或独立复现/)
})

test('legacy observed URL keeps a fixed-version original and section citation', async () => {
  const row = entry('legacy', { source_url: 'https://arxiv.org/html/2407.00001', versioned_source_url: 'https://arxiv.org/html/2407.00001v1' })
  const view = harness(envelope([row])); await view.load()
  assert.equal(view.error.value, '')
  assert.equal(view.locationUrl(view.readings.value[0], 'S4'), row.versioned_source_url + '#S4')
  assert.match(source, /:href="readingUrl\(row\)"/)
})

test('legacy observed URL trailing slash matches the server canonical version pin', async () => {
  const row = entry('legacy-slash', { source_url: 'https://arxiv.org/html/2407.00001/', versioned_source_url: 'https://arxiv.org/html/2407.00001v1' })
  const view = harness(envelope([row])); await view.load()
  assert.equal(view.error.value, '')
  assert.equal(view.locationUrl(view.readings.value[0], 'S4'), row.versioned_source_url + '#S4')
})

test('unversioned sources need an exact safe pin rather than a foreign or different paper', async () => {
  const base = { source_url: 'https://arxiv.org/html/2407.00001' }
  for (const extra of [base, { ...base, versioned_source_url: 'https://arxiv.org/html/2407.00002v1' },
    { ...base, versioned_source_url: 'https://arxiv.org/html/2407.00001v2' },
    { ...base, versioned_source_url: 'https://example.com/2407.00001v1' },
    { ...base, versioned_source_url: 'https://arxiv.org/html/2407.00001v1?token=secret' },
    { source_url: 'https://private.example/html/2407.00001', versioned_source_url: 'https://arxiv.org/html/2407.00001v1' }]) {
    const view = harness(envelope([entry('invalid-pin', extra)])); await view.load()
    assert.ok(view.error.value)
    assert.equal(view.readings.value.length, 0)
  }
})
