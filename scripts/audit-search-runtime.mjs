import fs from 'node:fs'
import path from 'node:path'
import { gzipSync } from 'node:zlib'
import { createHash } from 'node:crypto'
import { defaultFilters, filterCatalog, loadResultPage, searchOptions } from '../docs/.vitepress/theme/lib/catalog-search.ts'

const dist = path.resolve(process.env.PAGEFIND_DIST || 'docs/.vitepress/dist')
let requests = []
const read = (name) => {
  const content = fs.readFileSync(path.join(dist, name))
  requests.push({ name, bytes: content.length, gzip: /\.(json|js)$/.test(name) ? gzipSync(content).length : content.length })
  return content
}
const json = (name) => JSON.parse(read(name).toString())
const measure = (scenario, details = {}) => {
  const row = { scenario, requests: requests.length, raw_bytes: requests.reduce((sum, row) => sum + row.bytes, 0), gzip_transfer_estimate: requests.reduce((sum, row) => sum + row.gzip, 0), ...details }
  requests = []
  return row
}
const metrics = JSON.parse(fs.readFileSync(path.join(dist, 'pagefind/radar-metrics.json'), 'utf8'))
const facets = json('pagefind/radar-facets.json')
const config = json('pagefind/radar-config.json')
const first = json('api/v1/search/browse/included/1.json')
const results = [measure('initial_browse_first_20', { results: first.total, rows: first.rows.length, pagefind_runtime_loaded: false })]
const page26 = json('api/v1/search/browse/included/26.json')
if (page26.rows.length !== 20) throw new Error('Page 26 is not fully reachable')
results.push(measure('browse_page_26', { rows: page26.rows.length }))
const lookup = json('api/v1/search/lookup.json')
const positions = new Map(lookup.ids.map((id, index) => [id, index]))
const resultCache = new Map()
const resultFor = async (workId) => {
  const shard = createHash('sha1').update(workId).digest('hex').slice(0, 2)
  if (!resultCache.has(shard)) resultCache.set(shard, json(`api/v1/search/results/${shard}.json`))
  const row = resultCache.get(shard).find((row) => row.meta.work_id === workId)
  if (!row) throw new Error(`Missing result metadata: ${workId}`)
  return { ...row, plain_excerpt: row.excerpt }
}
const statusPath = path.join(dist, 'api/v1/research-status.json')
if (fs.existsSync(statusPath)) {
  for (const status of JSON.parse(fs.readFileSync(statusPath, 'utf8')).works) {
    if (!status.notices?.length) continue
    const row = await resultFor(status.work_id)
    if (row.meta.research_status !== status.status || row.meta.research_validation_eligible !== String(status.validation_eligible !== false)) throw new Error(`Search omitted current research status: ${status.work_id}`)
    if (row.meta.research_status_as_of !== status.as_of) throw new Error('Search mixed current status with an older text cutoff')
    if (status.validation_eligible === false && (row.meta.evidence !== 'E0' || row.meta.peer_reviewed !== 'false')) throw new Error('Withdrawn search result still claims active validation')
  }
  requests = []
}
const originalFetch = globalThis.fetch
try {
  globalThis.fetch = async (input) => {
    const name = `pagefind/${String(input).split('/pagefind/').at(-1).split('?')[0]}`
    if (name.includes('/fragment/') || name.includes('/filter/')) throw new Error(`Adapter must not request redundant Pagefind asset: ${name}`)
    return new Response(read(name), { headers: { 'Content-Type': name.endsWith('wasm') ? 'application/wasm' : 'application/octet-stream' } })
  }
  const code = read('pagefind/pagefind.js')
  const engine = await import(`data:text/javascript;base64,${code.toString('base64')}`)
  await engine.options({ bundlePath: '/pagefind/', language: config.language })
  await engine.init()
  const requiredWorkByQuery = { 'π0': 'arxiv:2410.24164', pi0: 'arxiv:2410.24164', 'π0.5': 'arxiv:2504.16054', 'pi0.5': 'arxiv:2504.16054', 'GEN-1.5 59%': 'report:de9e41b42353bf59a7e3' }
  for (const query of ['世界模型', '大小脑', '灵巧操作', 'VLA', 'π0', 'pi0', 'π0.5', 'pi0.5', 'PI', 'cross-embodiment', 'GEN-1.5 59%', lookup.work_ids[lookup.postings.relevance.included[0]]]) {
    const started = performance.now()
    const search = searchOptions({ ...defaultFilters(), q: query }, Object.keys(facets.month), Object.keys(facets.publication), config.language)
    for (const field of lookup.identity_shards || []) {
      const selected = search.filters[field]
      if (!selected) continue
      for (const value of typeof selected === 'string' ? [selected] : selected.any) {
        const shard = createHash('sha1').update(value).digest('hex').slice(0, 2)
        lookup.postings[field] ||= {}
        Object.assign(lookup.postings[field], json(`api/v1/search/identity/${field}/${shard}.json`))
      }
    }
    const allowed = filterCatalog(lookup, search.filters)
    const indices = search.query ? (await engine.search(search.query)).results.map((row) => positions.get(row.id)).filter((index) => index !== undefined && allowed.has(index)) : [...allowed]
    const matchingWorks = new Set(indices.map((index) => lookup.work_ids[index]))
    if (requiredWorkByQuery[query] && !matchingWorks.has(requiredWorkByQuery[query])) throw new Error(`Known-work recall failed for ${query}: ${requiredWorkByQuery[query]}`)
    if (query === 'GEN-1.5 59%' && matchingWorks.has('arxiv:2503.04877')) throw new Error('Decimal query leaked unrelated Adapt3R result into GEN-1.5')
    if (['π0.5', 'pi0.5'].includes(query) && matchingWorks.has('arxiv:2410.24164')) throw new Error(`Exact model version filter leaked the original π0 into ${query}`)
    const handles = indices.map((index) => ({ id: lookup.ids[index], data: () => resultFor(lookup.work_ids[index]) }))
    const page = await loadResultPage(handles, 1)
    if (!page.total) throw new Error(`Golden query unexpectedly empty: ${query}`)
    results.push(measure(query, { results: page.total, rows: page.rows.length, local_wasm_ms: Math.round(performance.now() - started) }))
  }
} finally { globalThis.fetch = originalFetch }
process.stdout.write(`${JSON.stringify({ metrics, measurements: results, note: 'Local Node/WASM diagnostics; JSON gzip is a transfer estimate. Not a mobile Lighthouse result.' }, null, 2)}\n`)
