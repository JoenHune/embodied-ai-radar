import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'

const source = fs.readFileSync(new URL('../docs/.vitepress/theme/components/PdfReadings.vue', import.meta.url), 'utf8')
const descriptor = parse(source).descriptor
const entry = (id = 'one', extra = {}) => ({ reading_id: id, work_id: `work:${id}`, title: `Paper ${id}`, relevance_status: 'included', source_format: 'pdf', source_url: 'https://www.roboticsproceedings.org/rss20/p001.pdf', edition_label: 'RSS 2024', page_count: 2, read_pages: [1, 2], visual_pages_checked: [1], read_completed_at: '2026-09-14T08:00:00Z', checked_table_count: 1, reader_kind: 'AI', reading_status: 'completed', human_reviewed: false, supplementary_materials_inspected: false, text_scope: 'complete_available_pdf_text', findings_zh: [{ text_zh: '原文发现', source_pages: [1, 2] }], limitations_zh: [{ text_zh: '没有独立复现', source_pages: [2] }], ...extra })
const envelope = records => ({ schema_version: '1', source_format: 'pdf', dataset_version: 'revision', dictionary_hash: 'dictionary', assurance: 'self_attested_AI_reading_not_human_review', human_reviewed: false, private_source_reverified: false, records })
function harness(value = envelope([entry()])) {
  const props = { expectedVersion: 'revision', dictionaryHash: 'dictionary', cohort: 'all_works' }
  const requests = []
  const ctx = { URL, URLSearchParams, AbortController, Set, computed: fn => ({ get value() { return fn() } }), ref: value => ({ value }), defineProps: () => props, onMounted() {}, onBeforeUnmount() {}, withBase: value => value, eventDate: value => value,
    fetch: async (...args) => { requests.push(args); if (value instanceof Error) throw value; return { ok: true, json: async () => value } } }
  vm.runInNewContext(ts.transpile(descriptor.scriptSetup.content.replace(/^import .*$/gm, '') + '\nglobalThis.view={load,records,loading,error,shown,filtered,mismatch,sourceAllowed,pageUrl};', { target: ts.ScriptTarget.ES2022 }), ctx)
  return { ...ctx.view, props, requests }
}
test('PDF view compiles, loads only on expansion, and retains separate HTML counts', () => {
  const script = compileScript(descriptor, { id: 'pdf-reading-view' })
  assert.deepEqual(compileTemplate({ id: 'pdf-reading-view', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } }).errors, [])
  const parent = fs.readFileSync(new URL('../docs/.vitepress/theme/components/HardwareCoverage.vue', import.meta.url), 'utf8')
  assert.match(parent, /const showPdfReadings = ref\(false\)/)
  assert.match(parent, /<PdfReadings v-else/)
  assert.match(parent, /PDF与HTML可能属于同一研究，不直接相加/)
  assert.match(parent, /AI已通读可用HTML文字/)
})
test('one on-demand PDF API, correct edition and 1-based page links', async () => {
  const view = harness(); await view.load()
  assert.equal(view.error.value, '')
  assert.deepEqual(view.requests.map(row => row[0]), ['/api/v1/equipment/coverage-pdf-readings.json'])
  const row = view.records.value[0]
  assert.equal(row.edition_label, 'RSS 2024')
  assert.equal(view.pageUrl(row, 2), row.source_url + '#page=2')
  assert.match(source, /row\.limitations_zh/)
  assert.match(source, /文件页码/)
  assert.match(source, /relevanceLabels\[row\.relevance_status\]/)
})
test('missing pages, out-of-range citations, fake human review and abstract-only rejected', async () => {
  for (const extra of [{ read_pages: [1] }, { read_pages: [1, 1] }, { visual_pages_checked: [3] }, { findings_zh: [{ text_zh: '越界', source_pages: [0] }] }, { human_reviewed: true }, { text_scope: 'abstract_only' }, { reading_status: 'prepared' }, { supplementary_materials_inspected: true }]) {
    const view = harness(envelope([entry('bad', extra)])); await view.load()
    assert.ok(view.error.value); assert.equal(view.records.value.length, 0)
  }
})
test('only approved public PDF URLs can navigate; no credentials or unsafe protocols', async () => {
  for (const address of ['javascript:alert(1)', 'http://arxiv.org/pdf/2407.00001v1', 'https://arxiv.org/html/2407.00001v1', 'https://user:secret@arxiv.org/pdf/2407.00001v1', 'https://example.com/paper.pdf', 'https://raw.githubusercontent.com/other/repo/paper.pdf']) {
    const view = harness(envelope([entry('bad', { source_url: address })])); await view.load()
    assert.ok(view.error.value)
  }
  const view = harness()
  assert.equal(view.sourceAllowed('https://raw.githubusercontent.com/mlresearch/v305/main/assets/a/a.pdf'), true)
  assert.equal(view.sourceAllowed('https://arxiv.org/pdf/2409.11952v1'), true)
})
test('cohort filtering and append are not numbered pagination', async () => {
  const view = harness(envelope(Array.from({ length: 17 }, (_, i) => entry(String(i), { relevance_status: i === 0 ? 'candidate' : 'included' }))))
  await view.load(); assert.equal(view.shown.value, 8)
  view.shown.value += 8; assert.equal(view.shown.value, 16)
  view.props.cohort = 'included'; assert.equal(view.filtered.value.length, 16)
})
test('stale version and network errors stay unknown, and updated parent hides old receipts', async () => {
  for (const value of [new Error('network'), { ...envelope([entry()]), dataset_version: 'old' }]) {
    const view = harness(value); await view.load(); assert.ok(view.error.value)
  }
  const view = harness(); await view.load(); view.props.expectedVersion = 'new'
  assert.equal(view.mismatch.value, true)
})
