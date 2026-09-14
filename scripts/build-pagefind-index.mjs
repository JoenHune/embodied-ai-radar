import fs from 'node:fs'
import path from 'node:path'
import readline from 'node:readline'
import { gzipSync } from 'node:zlib'
import { createHash } from 'node:crypto'
import { spawnSync } from 'node:child_process'
import * as pagefind from 'pagefind'
import { SEARCH_DICTIONARY_VERSION, workSearchRecord, compactResultCard } from './lib/search-records.mjs'
import { SEARCH_TEXT_CONTRACT } from '../docs/.vitepress/theme/lib/search-text.mjs'
import { applySearchStatus } from './lib/search-status.mjs'

const root = path.resolve(import.meta.dirname, '..')
const dist = path.resolve(process.env.PAGEFIND_DIST || path.join(root, 'docs/.vitepress/dist'))
const catalog = path.resolve(process.env.PAGEFIND_CATALOG || path.join(root, 'data/catalog'))
const output = path.join(dist, 'pagefind')
const base = (process.env.SITE_BASE || '/embodied-ai-radar/').replace(/\/?$/, '/')
const language = process.env.PAGEFIND_LANGUAGE || 'zh'
if (!fs.existsSync(dist)) throw new Error('VitePress dist is missing; build the site before Pagefind')
const publicManifest = JSON.parse(fs.readFileSync(path.join(dist, 'api/v1/catalog-manifest.json'), 'utf8'))
const authorityManifest = JSON.parse(fs.readFileSync(path.join(catalog, 'manifest.json'), 'utf8'))
if (publicManifest.catalog_hash !== authorityManifest.catalog_hash) throw new Error('Site and search authority revisions differ; rebuild VitePress from the current catalog')
const dataThrough = publicManifest.data_through
if (!dataThrough) throw new Error('The exported catalogue must declare its data_through before search indexing')
const reportViewPath = path.join(dist,'api/v1/report-text-index.json')
const reportViews = fs.existsSync(reportViewPath) ? JSON.parse(fs.readFileSync(reportViewPath,'utf8')) : {catalog_hash:publicManifest.catalog_hash,data_through:dataThrough,works:{}}
if (reportViews.catalog_hash !== publicManifest.catalog_hash || reportViews.data_through !== dataThrough || (publicManifest.report_text_snapshot_count && !fs.existsSync(reportViewPath))) throw new Error('Report search views differ from the audited catalogue')
const statusViewPath = path.join(dist, 'api/v1/research-status.json')
const statusView = fs.existsSync(statusViewPath) ? JSON.parse(fs.readFileSync(statusViewPath, 'utf8')) : null
if (statusView && (statusView.catalog_hash !== publicManifest.catalog_hash || statusView.text_data_through !== dataThrough || statusView.as_of !== publicManifest.research_status_as_of)) throw new Error('Search research-status revision differs from the catalogue')
const statusById = new Map((statusView?.works || []).map(row => [row.work_id, row]))
const statusDetails = new Map()
for (const id of statusById.keys()) {
  const shard = createHash('sha1').update(id).digest('hex').slice(0, 2)
  if (!statusDetails.has(shard)) statusDetails.set(shard, JSON.parse(fs.readFileSync(path.join(dist, 'api/v1/works', `${shard}.json`), 'utf8')))
}

const readJsonLines = async (target, callback) => {
  const lines = readline.createInterface({ input: fs.createReadStream(target, { encoding: 'utf8' }), crlfDelay: Infinity })
  for await (const line of lines) if (line.trim()) await callback(JSON.parse(line))
}
const orgPath = path.join(catalog, 'organizations.jsonl')
const orgNames = new Map()
const orgDisplayNames = new Map()
const registerOrganizationNames = (row) => {
  const display = row.display_name || row.name || row.canonical_name || row.organization_id
  orgDisplayNames.set(row.organization_id, display)
  orgNames.set(row.organization_id, [display, row.short_name, ...(row.aliases || [])].filter(Boolean).join(' '))
}
if (fs.existsSync(orgPath)) await readJsonLines(orgPath, registerOrganizationNames)
else for (const row of JSON.parse(fs.readFileSync(path.join(root, 'docs/public/api/v1/organizations.json'), 'utf8'))) registerOrganizationNames(row)
const workOrganizations = new Map()
const manifestations = new Map()
const localizations = new Map()
const legacyNotes = new Map()
const textSnapshots = new Map()
const identityReviews = new Map()
const textStatusCounts = {}
const localizationStatusCounts = {}
let titleAliasCount = 0
let authorAliasCount = 0
let registeredTitleAliasCount = 0
const editorialDirectory = path.join(root, 'data/editorial')
if (fs.existsSync(path.join(editorialDirectory, 'work-localizations.jsonl'))) await readJsonLines(path.join(editorialDirectory, 'work-localizations.jsonl'), (row) => localizations.set(row.work_id, row))
if (fs.existsSync(path.join(editorialDirectory, 'legacy/work-notes.jsonl'))) await readJsonLines(path.join(editorialDirectory, 'legacy/work-notes.jsonl'), (row) => legacyNotes.set(row.work_id, row))
if (fs.existsSync(path.join(catalog, 'work-relations.jsonl'))) await readJsonLines(path.join(catalog, 'work-relations.jsonl'), (row) => {
  if (row.relation !== 'merged_into' || !row.review_id) return
  const values = identityReviews.get(row.work_id) || []
  values.push(row)
  identityReviews.set(row.work_id, values)
})
const textDirectory = path.join(catalog, 'text-snapshots')
const textPaths = fs.existsSync(textDirectory) ? fs.readdirSync(textDirectory).filter((name) => /^[a-f0-9]{2}\.jsonl$/.test(name)).sort().map((name) => path.join(textDirectory, name)) : [path.join(catalog, 'text-snapshots.jsonl')].filter((name) => fs.existsSync(name))
for (const source of textPaths) await readJsonLines(source, (row) => {
  const values = textSnapshots.get(row.work_id) || []
  values.push(row)
  textSnapshots.set(row.work_id, values)
})
await readJsonLines(path.join(catalog, 'work-organization-links.jsonl'), (row) => {
  if (!['G1', 'G2'].includes(row.evidence_grade)) return
  const values = workOrganizations.get(row.work_id) || new Set()
  values.add(row.organization_id)
  workOrganizations.set(row.work_id, values)
})
await readJsonLines(path.join(catalog, 'manifestations.jsonl'), (row) => {
  const values = manifestations.get(row.work_id) || []
  values.push(row)
  manifestations.set(row.work_id, values)
})

const { index, errors } = await pagefind.createIndex({ forceLanguage: language, includeCharacters: 'π' })
if (!index || errors?.length) throw new Error(errors?.join('\n') || 'Pagefind did not return an index')
let indexedWorks = 0
const seenIds = new Set()
const facets = {}
const postings = {}
const searchRows = []
let builtFiles
let pending = []
const flush = async () => {
  const results = await Promise.all(pending)
  pending = []
  const errors = results.flatMap((result) => result.errors || [])
  if (errors.length) throw new Error(errors.slice(0, 10).join('\n'))
}
try {
  const workDir = path.join(catalog, 'works')
  const sources = fs.existsSync(workDir) ? fs.readdirSync(workDir).filter((name) => /^[a-f0-9]{2}\.jsonl$/.test(name)).sort().map((name) => path.join(workDir, name)) : [path.join(catalog, 'works.jsonl')]
  if (!sources.length) throw new Error('No authority work shards found')
  for (const source of sources) await readJsonLines(source, async (work) => {
    if (work.research_status_notices?.length && !statusView) throw new Error('Research-status projection missing during indexing')
    const status = statusById.get(work.work_id)
    if (status) {
      const shard = createHash('sha1').update(work.work_id).digest('hex').slice(0, 2)
      work = applySearchStatus(work, status, statusDetails.get(shard).find(row => row.work_id === work.work_id))
    }
    if (seenIds.has(work.work_id)) throw new Error(`Duplicate work ID in authority: ${work.work_id}`)
    seenIds.add(work.work_id)
    const organizationIds = [...(workOrganizations.get(work.work_id) || [])]
    const ordinal = searchRows.length
    const record = workSearchRecord(work, { manifestations: manifestations.get(work.work_id) || [], organizationIds, organizationNames: organizationIds.map((id) => orgNames.get(id) || id), organizationDisplayNames: organizationIds.map((id) => orgDisplayNames.get(id) || id), base, explicitChinese: true, ordinal,
      dataThrough, snapshots: textSnapshots.get(work.work_id) || [], localization: localizations.get(work.work_id), legacyNote: legacyNotes.get(work.work_id), identityReviews: identityReviews.get(work.work_id) || [], reportText:reportViews.works[work.work_id] })
    searchRows.push({ id: work.work_id, url: record.url, excerpt: record.excerpt, meta: record.meta })
    textStatusCounts[record.meta.text_status] = (textStatusCounts[record.meta.text_status] || 0) + 1
    localizationStatusCounts[record.meta.localization_status] = (localizationStatusCounts[record.meta.localization_status] || 0) + 1
    titleAliasCount += record.index_info.historical_title_aliases
    authorAliasCount += record.index_info.historical_author_aliases
    registeredTitleAliasCount += record.index_info.registered_title_aliases
    for (const [name, values] of Object.entries(record.filters)) {
      if (name === 'record_type') continue
      postings[name] ||= {}
      for (const value of new Set(values)) (postings[name][value] ||= []).push(ordinal)
      if (['identifier', 'work_id', 'source_url'].includes(name)) continue
      facets[name] ||= {}
      for (const value of new Set(values)) facets[name][value] = (facets[name][value] || 0) + 1
    }
    // Virtual records provide field weighting without producing one page per work.
    // Site navigation/articles are deliberately not crawled into this evidence index.
    pending.push(index.addHTMLFile({ url: record.url, content: record.content }))
    indexedWorks += 1
    if (pending.length >= 48) await flush()
  })
  if (pending.length) await flush()
  const { files, errors: fileErrors } = await index.getFiles()
  if (fileErrors?.length) throw new Error(fileErrors.join('\n'))
  builtFiles = new Map(files.map((file) => [file.path, file.content]))
} finally { await pagefind.close() }

// Export handle identities only through the public search API. The numeric ordinal sort
// is unique and follows authority ingestion order; no compressed Pagefind file is parsed.
const originalFetch = globalThis.fetch
let resultIds
try {
  globalThis.fetch = async (input) => {
    const key = String(input).split('/pagefind/').at(-1).split('?')[0]
    const bytes = builtFiles.get(key)
    if (!bytes) throw new Error(`Missing build-time Pagefind asset: ${key}`)
    return new Response(bytes, { headers: { 'Content-Type': key.endsWith('wasm') ? 'application/wasm' : 'application/octet-stream' } })
  }
  const engine = await import(`data:text/javascript;base64,${Buffer.from(builtFiles.get('pagefind.js')).toString('base64')}`)
  await engine.options({ bundlePath: '/pagefind/', language })
  await engine.init()
  const response = await engine.search(null, { sort: { ordinal: 'asc' } })
  if (response.results.length !== searchRows.length) throw new Error('Pagefind work count does not reconcile with authority')
  resultIds = response.results.map((row) => row.id)
  if (new Set(resultIds).size !== searchRows.length) throw new Error('Duplicate Pagefind result IDs')
  for (const position of new Set([0, searchRows.length - 1, ...searchRows.map((_, index) => index).filter((index) => index % 1000 === 0)])) {
    const row = await response.results[position].data()
    if (row.meta.work_id !== searchRows[position].meta.work_id) throw new Error(`Pagefind ordinal mapping mismatch: ${position}`)
  }
} finally { globalThis.fetch = originalFetch }

if (fs.existsSync(output)) {
  if (!fs.existsSync(path.join(output, 'pagefind-entry.json')) && fs.readdirSync(output).length) throw new Error(`Refusing to replace a non-Pagefind directory: ${output}`)
  fs.rmSync(output, { recursive: true, force: true })
}
for (const [name, content] of builtFiles) {
  // Filtering/pagination and result descriptions use the public catalogue adapter.
  // Full abstracts remain in the inverted index and canonical API, not a duplicate fragment.
  if (name.startsWith('fragment/') || name.startsWith('filter/') || /pagefind-(?:ui|component-ui|modular-ui|highlight)\./.test(name)) continue
  const target = path.join(output, name)
  fs.mkdirSync(path.dirname(target), { recursive: true })
  fs.writeFileSync(target, content)
}
// Only the standard gzip wrapper changes. The worker verifies every decoded
// byte; Pagefind's native payload format, filenames and query behavior stay intact.
const compressionRun = spawnSync(process.execPath, [path.join(root, 'scripts/run-python.mjs'), path.join(root, 'scripts/optimize_pagefind_gzip.py'), '--directory', output], { cwd: root, encoding: 'utf8', maxBuffer: 10_000_000 })
if (compressionRun.status !== 0) throw new Error(`Pagefind lossless compression failed: ${(compressionRun.stdout || compressionRun.stderr || '').slice(0, 1000)}`)
const compression = JSON.parse(compressionRun.stdout)
if (compression.status !== 'ok' || !compression.asset_count || !compression.all_decoded_bytes_identical) throw new Error('Pagefind compression did not prove payload identity')
fs.mkdirSync(path.join(root, 'logs'), { recursive: true })
fs.writeFileSync(path.join(root, 'logs/pagefind-gzip-audit.json'), JSON.stringify(compression, null, 2))
const api = path.join(dist, 'api/v1/search')
if (fs.existsSync(path.join(api, 'lookup.json'))) fs.rmSync(api, { recursive: true, force: true })
fs.mkdirSync(api, { recursive: true })
const writeJSON = (name, value) => {
  const target = path.join(api, name)
  fs.mkdirSync(path.dirname(target), { recursive: true })
  fs.writeFileSync(target, JSON.stringify(value))
}
const identityFields = ['identifier', 'work_id', 'source_url']
for (const field of identityFields) {
  const shards = new Map()
  for (const [value, positions] of Object.entries(postings[field] || {})) {
    const shard = createHash('sha1').update(value).digest('hex').slice(0, 2)
    const rows = shards.get(shard) || {}
    rows[value] = positions
    shards.set(shard, rows)
  }
  for (const [shard, rows] of shards) writeJSON(`identity/${field}/${shard}.json`, rows)
}
writeJSON('lookup.json', { ids: resultIds, work_ids: searchRows.map((row) => row.meta.work_id), dates: searchRows.map((row) => row.meta.date), identity_shards: identityFields, postings: Object.fromEntries(Object.entries(postings).filter(([name]) => !identityFields.includes(name))) })
const rowShards = new Map()
for (const row of searchRows) {
  const rows = rowShards.get(row.meta.shard) || []
  rows.push(row)
  rowShards.set(row.meta.shard, rows)
}
for (const [shard, rows] of rowShards) writeJSON(`results/${shard}.json`, rows)
for (const status of ['all', ...Object.keys(postings.relevance)]) {
  const rows = searchRows.filter((row) => status === 'all' || row.meta.relevance === status).sort((a, b) => b.meta.date.localeCompare(a.meta.date) || a.meta.work_id.localeCompare(b.meta.work_id))
  for (let start = 0; start < Math.max(rows.length, 1); start += 20) writeJSON(`browse/${status}/${start / 20 + 1}.json`, { rows: rows.slice(start, start + 20).map(compactResultCard), total: rows.length, page: start / 20 + 1 })
}

const metricsFor = (target) => fs.readdirSync(target, { withFileTypes: true }).reduce((total, entry) => {
  const filename = path.join(target, entry.name)
  if (entry.name === 'radar-metrics.json') return total
  const value = entry.isDirectory() ? metricsFor(filename) : (() => { const data = fs.readFileSync(filename); return { bytes: data.length, gzip: gzipSync(data).length } })()
  return { bytes: total.bytes + value.bytes, gzip: total.gzip + value.gzip }
}, { bytes: 0, gzip: 0 })
fs.writeFileSync(path.join(output, 'radar-facets.json'), `${JSON.stringify(facets)}\n`)
fs.writeFileSync(path.join(output, 'radar-config.json'), JSON.stringify({ language, adapter: 'catalog-v1', page_size: 20 }))
const sizes = metricsFor(output)
const metadata = metricsFor(api)
const metrics = { indexed_works: indexedWorks, indexed_site_pages: 0, index_bytes: sizes.bytes, index_gzip_bytes: sizes.gzip, inverted_index_bytes: metricsFor(path.join(output, 'index')).bytes, result_fragment_bytes: 0, filter_bytes: 0, catalogue_adapter_bytes: metadata.bytes, catalogue_adapter_gzip_bytes: metadata.gzip, dictionary_version: SEARCH_DICTIONARY_VERSION, generated_at: new Date().toISOString(),
  data_through: dataThrough, text_status_counts: textStatusCounts, localization_status_counts: localizationStatusCounts, historical_title_aliases: titleAliasCount, historical_author_aliases: authorAliasCount, indexed_historical_abstracts: 0 }
metrics.registered_title_aliases = registeredTitleAliasCount
metrics.text_query_contract = SEARCH_TEXT_CONTRACT
metrics.text_cutoff_semantics = 'versioned_arxiv_text_uses_data_through; unversioned_catalog_text_is_searchable_without_historical_date_claim'
metrics.lossless_gzip_optimization = { ...compression.spec, asset_count: compression.asset_count, changed_assets: compression.changed_assets, saved_bytes: compression.saved_bytes, all_decoded_bytes_identical: compression.all_decoded_bytes_identical }
metrics.publication_metadata_scope = 'latest_registered_canonical_manifestations_not_limited_by_text_cutoff'
metrics.catalog_hash = authorityManifest.catalog_hash
metrics.dataset_version = publicManifest.dataset_version
metrics.index_budget_bytes = 20_000_000
metrics.index_budget_pass = metrics.index_gzip_bytes <= metrics.index_budget_bytes
fs.writeFileSync(path.join(output, 'radar-metrics.json'), `${JSON.stringify(metrics, null, 2)}\n`)
process.stdout.write(`${JSON.stringify(metrics)}\n`)
if (!metrics.index_budget_pass) throw new Error(`Pagefind compressed index exceeds 20 MB: ${metrics.index_gzip_bytes} bytes`)
