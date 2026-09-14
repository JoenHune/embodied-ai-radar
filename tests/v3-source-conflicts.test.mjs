import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import vm from 'node:vm'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { applySourceConflicts, compactSourceConflicts, conflictsForWork, safeConflictUrl, sourceConflictIndex, sourceConflictState } from '../docs/.vitepress/theme/lib/source-conflicts.mjs'
import { workSearchRecord, compactResultCard } from '../scripts/lib/search-records.mjs'
import { searchCardFromResult, researchOutputLabel } from '../docs/.vitepress/theme/lib/research-card.mjs'
import { publicationRecords, statusNotices } from '../docs/.vitepress/theme/lib/work-status.mjs'
import { dashboardSnapshot } from '../scripts/lib/editorial-coverage.mjs'

const conflict = (extra = {}) => ({ conflict_id: 'source-conflict:fixture', work_id: 'arxiv:2609.02046', version: 'v1', status: 'open',
  experimental_use: 'hold', summary_zh: '元数据与缓存正文的结果限定和日期仍待核对。', detected_at: '2026-09-15T00:00:00Z',
  issue_types: ['content_mismatch', 'date_mismatch'], source_urls: ['https://arxiv.org/abs/2609.02046v1', 'https://arxiv.org/html/2609.02046v1'], ...extra })
const envelope = conflicts => ({ schema_version: '1', dataset_version: 'revision', as_of: '2026-09-15', conflicts })
const source = name => fs.readFileSync(new URL('../' + name, import.meta.url), 'utf8')

test('full API records become bounded warning fields and preserve exact identity without mutation', () => {
  const input = envelope([conflict({ detailed_evidence: { raw_sha256: 'a'.repeat(64), internal_key: 'not copied' } })])
  const before = structuredClone(input)
  const index = sourceConflictIndex(input, 'revision')
  const rows = conflictsForWork(index, 'arxiv:2609.02046', 'v1')
  assert.equal(rows.length, 1)
  assert.deepEqual(rows[0], conflict())
  assert.equal(rows[0].detailed_evidence, undefined)
  rows[0].source_urls.push('https://example.test/not-persisted')
  assert.equal(conflictsForWork(index, 'arxiv:2609.02046')[0].source_urls.length, 2)
  assert.deepEqual(input, before)
  assert.deepEqual(conflictsForWork(index, 'arxiv:2609.02046', 'v2'), [])
  assert.deepEqual(conflictsForWork(index, 'other-work'), [])
})

test('resolved records and absent data do not fabricate warnings; malformed data stays unknown', () => {
  for (const value of [undefined, [], [conflict({ status: 'resolved', experimental_use: 'released' })]]) {
    assert.deepEqual(sourceConflictState(value), { unknown: false, rows: [] })
  }
  for (const value of [null, {}, 'not-json', [conflict({ experimental_use: 'released' })], [conflict({ work_id: 'wrong-work' })]]) {
    assert.equal(sourceConflictState(value, { workId: 'arxiv:2609.02046' }).unknown, true)
  }
  assert.equal(sourceConflictState(JSON.stringify([conflict()]), { workId: 'arxiv:2609.02046' }).rows.length, 1)
})

test('API schema and dataset mismatch fail closed; unsafe links and private metadata never render', () => {
  for (const body of [{}, { ...envelope([]), schema_version: '2' }, { ...envelope([]), dataset_version: 'old' },
                      { ...envelope([]), as_of: 'unknown' }, envelope([conflict(), conflict()])]) {
    assert.throws(() => sourceConflictIndex(body, 'revision'), /contract_invalid/)
  }
  for (const url of ['javascript:alert(1)', 'http://example.test', 'https://user:secret@example.test/', '/local', 'file:///tmp/x', 'https://example.test/\nsecret']) {
    assert.equal(safeConflictUrl(url), '')
    assert.throws(() => compactSourceConflicts([conflict({ source_urls: [url] })]), /contract_invalid/)
  }
  assert.throws(() => compactSourceConflicts([conflict({ summary_zh: '.research/private/path' })]), /contract_invalid/)
  assert.equal(sourceConflictState([conflict({ source_urls: ['file:///private/x'] })]).unknown, true)
})

test('search and compact browse retain warnings without adding body text, changing counts or publication status', () => {
  const raw = { work_id: 'arxiv:2609.02046', title: 'Original', abstract: 'Original unchanged abstract', authors: [], directions: ['D3'],
    questions: [], relevance: { status: 'included' }, first_public_date: '2026-09-01', evidence_grade: 'E3', strict_peer_reviewed: true,
    evidence_flags: { real_robot: true }, research_status: { status: 'active', notices: [], validation_eligible: true } }
  const before = structuredClone(raw), index = sourceConflictIndex(envelope([conflict()]), 'revision')
  const overlaid = applySourceConflicts(raw, index)
  const baseline = workSearchRecord(raw), record = workSearchRecord(overlaid)
  const body = value => value.content.match(/<body data-pagefind-body>([\s\S]*)<\/body>/)[1]
  assert.equal(body(record), body(baseline))
  assert.deepEqual(record.filters, baseline.filters)
  assert.equal(record.excerpt, baseline.excerpt)
  assert.equal(record.meta.evidence, 'E3')
  assert.equal(record.meta.peer_reviewed, 'true')
  const card = searchCardFromResult(compactResultCard(record))
  assert.ok(Array.isArray(card.source_conflicts))
  assert.equal(sourceConflictState(card.source_conflicts, { workId: card.work_id }).rows[0].conflict_id, conflict().conflict_id)
  assert.equal(researchOutputLabel(card), '同行评审已核验')
  assert.deepEqual(statusNotices(overlaid), [])
  assert.deepEqual(publicationRecords(overlaid), publicationRecords(raw))
  assert.deepEqual(raw, before)
  assert.equal(overlaid.research_status, raw.research_status)
  assert.equal(overlaid.first_public_date, raw.first_public_date)
  const malformed = searchCardFromResult({ meta: { work_id: raw.work_id, source_conflicts: '{not-json' } })
  assert.equal(malformed.source_conflicts_unknown, true)
  assert.deepEqual(malformed.source_conflicts, [])
})

test('conflict and actual retraction can coexist without overwriting either lane', () => {
  const raw = { work_id: 'arxiv:2609.02046', research_status: { status: 'withdrawn', validation_eligible: false, notices: [] } }
  const work = applySourceConflicts(raw, sourceConflictIndex(envelope([conflict()]), 'revision'))
  assert.equal(statusNotices(work)[0].label, '作者撤回')
  assert.equal(sourceConflictState(work.source_conflicts).rows.length, 1)
  assert.equal(work.research_status.validation_eligible, false)
})

const noticeSource = source('docs/.vitepress/theme/components/SourceConflictNotice.vue')
const descriptor = parse(noticeSource).descriptor
async function renderNotice(value, extra = {}) {
  const compiled = compileTemplate({ id: 'source-conflicts', source: descriptor.template.content, compilerOptions: { mode: 'function' } })
  assert.deepEqual(compiled.errors, [])
  const render = new Function('Vue', compiled.code)(Vue)
  const context = { state: sourceConflictState(value, { workId: extra.workId, version: extra.version }), unknown: false, compact: false,
    monthly: false, workId: '', workUrl: id => '/radar/database/?work=' + encodeURIComponent(id), eventDate: value => value, ...extra }
  return renderToString(Vue.createSSRApp({ render, setup: () => context }))
}

test('notice SSR shows amber source review boundary and safe evidence links, never an official retraction assertion', async () => {
  const script = compileScript(descriptor, { id: 'source-conflicts' })
  assert.deepEqual(compileTemplate({ id: 'source-conflicts', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } }).errors, [])
  const html = await renderNotice([conflict()], { monthly: true })
  for (const text of ['来源待核', '不是撤稿通知', '未判定哪一方错误', '暂不作为确定实验结论', '不改变论文登记数量', '发现时间不等于当月已知', '核对来源']) assert.ok(html.includes(text), text)
  assert.ok(html.includes('https://arxiv.org/html/2609.02046v1'))
  assert.ok(html.includes('/radar/database/?work=arxiv%3A2609.02046'))
  assert.doesNotMatch(noticeSource, /v-html|vp-c-danger|官方通知/)
  assert.match(noticeSource, /vp-c-warning/)
  assert.doesNotMatch(await renderNotice(undefined), /source-conflict-notice/)
  assert.match(await renderNotice(undefined, { unknown: true }), /来源冲突状态未知/)
  const escaped = await renderNotice([conflict({ summary_zh: '<script>alert(1)</script>' })])
  assert.doesNotMatch(escaped, /<script>/)
  assert.match(escaped, /&lt;script&gt;/)
})

test('detail, all card routes and monthly/history retain the independent warning lane', () => {
  const database = source('docs/.vitepress/theme/components/DatabaseExplorer.vue')
  assert.ok(database.indexOf('<SourceConflictNotice :value="detail.source_conflicts"') < database.indexOf('<p v-if="detail.summary_zh">'))
  assert.match(database, /detailSourceConflict\.unknown \|\| detailSourceConflict\.rows\.length/)
  assert.match(database, /不能仅凭相同版本号认定两渠道内容和日期一致/)
  const card = source('docs/.vitepress/theme/components/ResearchCard.vue')
  assert.ok(card.indexOf('<SourceConflictNotice') < card.indexOf('<p v-if="work.summary"'))
  const dashboard = source('docs/.vitepress/theme/components/RadarDashboard.vue')
  assert.ok(dashboard.indexOf(':value="monthlySnapshot.source_conflicts" monthly') < dashboard.indexOf('<header><h2>本月总判断'))
  assert.match(source('docs/.vitepress/theme/components/HistoricalEditorial.vue'), /input_digest_changed:/)
  assert.match(source('docs/.vitepress/theme/components/HistoricalEditorial.vue'), /旧版摘要（依据已变化，不作为当前结论）/)
  const snapshot = { month: '2026-09', coverage: { included_works: 100 }, source_conflicts: [conflict()], executive_findings: [{ text: 'Original' }] }
  const before = structuredClone(snapshot)
  assert.deepEqual(dashboardSnapshot(snapshot).source_conflicts, snapshot.source_conflicts)
  assert.deepEqual(snapshot, before)
  const search = source('scripts/build-pagefind-index.mjs'), visual = source('scripts/build-visual-catalog.mjs')
  for (const code of [search, visual]) assert.match(code, /sourceConflictIndex\(/)
  assert.match(search, /applySourceConflicts\(work, sourceConflicts\)/)
  assert.match(visual, /source_conflicts: conflictsForWork\(sourceConflicts, work.work_id\)/)
  assert.ok(visual.indexOf("sourceConflictIndex(read('source-content-conflicts.json')") < visual.indexOf('fs.writeFileSync'))
})

test('actual Pagefind startup requires an explicit same-revision conflict index in temporary fixtures', t => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'source-conflict-search-gate-'))
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }))
  const dist = path.join(directory, 'dist'), catalog = path.join(directory, 'catalog')
  fs.mkdirSync(path.join(dist, 'api/v1'), { recursive: true }); fs.mkdirSync(catalog)
  fs.writeFileSync(path.join(dist, 'api/v1/catalog-manifest.json'), JSON.stringify({ catalog_hash: 'fixture', dataset_version: 'revision', data_through: '2026-09-15' }))
  fs.writeFileSync(path.join(catalog, 'manifest.json'), JSON.stringify({ catalog_hash: 'fixture' }))
  const build = source('scripts/build-pagefind-index.mjs')
  // Evaluate the actual startup guards only: no Pagefind build, optimizer,
  // user ledger or hard-coded repository log output is executed.
  const startup = build.slice(0, build.indexOf('const reportViewPath')).replace(/^import .*$/gm, '')
    .replaceAll('import.meta.dirname', JSON.stringify(path.join(directory, 'scripts')))
  const run = () => {
    const context = { fs, path, sourceConflictIndex, process: { env: { PAGEFIND_DIST: dist, PAGEFIND_CATALOG: catalog } } }
    vm.runInNewContext(startup + '\nglobalThis.result = sourceConflicts;', context)
    return context.result
  }
  assert.throws(run, /ENOENT/)
  const api = path.join(dist, 'api/v1/source-content-conflicts.json')
  fs.writeFileSync(api, JSON.stringify({ ...envelope([]), dataset_version: 'stale' }))
  assert.throws(run, /contract_invalid/)
  fs.writeFileSync(api, JSON.stringify(envelope([])))
  assert.equal(run().size, 0, 'An intentionally empty fixture is explicit, not a production fallback')
  fs.writeFileSync(api, JSON.stringify(envelope([conflict()])))
  assert.equal(run().get('arxiv:2609.02046')[0].conflict_id, conflict().conflict_id)
  assert.deepEqual(fs.readdirSync(directory).sort(), ['catalog', 'dist'])
})
