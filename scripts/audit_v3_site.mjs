import fs from 'node:fs'
import path from 'node:path'
import { gzipSync } from 'node:zlib'
import { fileURLToPath } from 'node:url'
import { spawn, spawnSync } from 'node:child_process'
import { load } from 'cheerio'
import { readSourceRecordIds } from './lib/source-record-files.mjs'

const archiveVerificationCode = `import json,sys
sys.path.insert(0,sys.argv[1])
try:
 from sqlite_download import verify_archive
 result=verify_archive(sys.argv[2],json.loads(sys.argv[3]))
 print(json.dumps(result))
except Exception:
 print(json.dumps({'status':'failed','error':'sqlite_archive_verification_failed'}))
 sys.exit(1)
`

// Reuse the ZIP/ZIP64 reader and streaming CRC/hash/unique-entry checks from
// Python. Data travels only as argv, never interpolated code or shell commands.
// No SQLite dump is loaded into memory or decompressed to another file.
export async function auditSqliteDownload(dist, downloads) {
  if (downloads?.sqlite !== '/downloads/radar.sqlite.zip') throw new Error('sqlite_zip_manifest_download_required')
  const expected = downloads.sqlite_integrity
  if (!expected || Object.keys(expected).sort().join(',') !== 'archive_bytes,archive_sha256,bytes,encoding,sha256' || expected.encoding !== 'zip' ||
      typeof expected.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(expected.sha256) ||
      typeof expected.archive_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(expected.archive_sha256) ||
      !Number.isSafeInteger(expected.bytes) || expected.bytes < 16 ||
      !Number.isSafeInteger(expected.archive_bytes) || expected.archive_bytes < 1) throw new Error('sqlite_integrity_manifest_invalid')
  let stat
  const archive = path.join(dist, 'downloads/radar.sqlite.zip')
  try {
    for (const name of ['radar.sqlite', 'radar.sqlite.gz']) {
      if (fs.lstatSync(path.join(dist, 'downloads', name), { throwIfNoEntry: false })) throw new Error('sqlite_legacy_public_duplicate')
    }
    stat = fs.lstatSync(archive, { throwIfNoEntry: false })
  } catch (error) {
    throw new Error(error.message === 'sqlite_legacy_public_duplicate' ? error.message : 'sqlite_archive_unreadable')
  }
  if (!stat) throw new Error('sqlite_archive_missing')
  if (!stat.isFile() || stat.isSymbolicLink()) throw new Error('sqlite_archive_regular_file_required')
  if (stat.size !== expected.archive_bytes) throw new Error('sqlite_archive_size_mismatch')
  const root = path.resolve(import.meta.dirname, '..')
  const result = await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [path.join(root, 'scripts/run-python.mjs'), '-B', '-c', archiveVerificationCode,
      path.join(root, 'scripts'), archive, JSON.stringify(expected)], { cwd: root, shell: false, stdio: ['ignore', 'pipe', 'ignore'] })
    let output = '', overflow = false
    child.stdout.setEncoding('utf8')
    child.stdout.on('data', chunk => {
      if (overflow) return
      output += chunk
      if (output.length > 16_384) { overflow = true; child.kill(); reject(new Error('sqlite_archive_verifier_output_invalid')) }
    })
    child.on('error', () => reject(new Error('sqlite_archive_verifier_unavailable')))
    child.on('close', code => {
      if (overflow) return
      if (code !== 0) return reject(new Error('sqlite_archive_verification_failed'))
      try { resolve(JSON.parse(output)) } catch { reject(new Error('sqlite_archive_verifier_output_invalid')) }
    })
  })
  if (!result || result.status !== 'passed' || Object.keys(expected).some(key => result[key] !== expected[key])) throw new Error('sqlite_archive_verifier_output_invalid')
  return { ...expected, status: 'passed' }
}

async function main() {
const root = path.resolve(import.meta.dirname, '..')
const argument = (name, fallback) => {
  const index = process.argv.indexOf(name)
  return index < 0 ? fallback : process.argv[index + 1]
}
const dist = path.resolve(argument('--dist', path.join(root, 'docs/.vitepress/dist')))
const reportPath = path.resolve(argument('--report', path.join(root, 'logs/v3-site-audit.json')))
const base = (process.env.SITE_BASE || '/embodied-ai-radar/').replace(/\/?$/, '/')
const origin = 'https://built-radar.invalid'
const errors = []
const warnings = []
const issue = (type, detail) => errors.push({ type, ...detail })
const walk = (directory) => fs.existsSync(directory) ? fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => entry.isDirectory() ? walk(path.join(directory, entry.name)) : [path.join(directory, entry.name)]) : []
const readJson = (target, fallback = null) => {
  if (!fs.existsSync(target)) { issue('missing_artifact', { path: path.relative(dist, target) }); return fallback }
  try { return JSON.parse(fs.readFileSync(target, 'utf8')) } catch { issue('invalid_json', { path: path.relative(dist, target) }); return fallback }
}
const existsFile = (target) => fs.existsSync(target) && fs.statSync(target).isFile()
const routeForFile = (file) => {
  const relative = path.relative(dist, file).split(path.sep).join('/')
  return base + (relative === 'index.html' ? '' : relative.replace(/\/index\.html$/, '/').replace(/\.html$/, ''))
}
const resolveInternal = (raw, current) => {
  let url
  try { url = new URL(raw, origin + current) } catch { return { error: 'invalid_url' } }
  if (!['http:', 'https:'].includes(url.protocol)) return null
  if (![origin, 'https://joen.site'].includes(url.origin)) return null
  if (url.pathname !== base.slice(0, -1) && !url.pathname.startsWith(base)) return { error: 'outside_site_base', href: raw }
  let relative
  try { relative = decodeURIComponent(url.pathname.slice(base.length)) } catch { return { error: 'invalid_url_encoding', href: raw } }
  const target = path.resolve(dist, relative || 'index.html')
  if (target !== dist && !target.startsWith(dist + path.sep)) return { error: 'outside_dist', href: raw }
  const candidates = [target, `${target}.html`, path.join(target, 'index.html')]
  return { file: candidates.find(existsFile), url, candidates: candidates.map((value) => path.relative(dist, value)) }
}

const htmlFiles = walk(dist).filter((file) => file.endsWith('.html'))
const deploymentBytes = walk(dist).reduce((sum, file) => sum + fs.statSync(file).size, 0)
// https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
if (deploymentBytes > 1_000_000_000) issue('github_pages_site_size_exceeded', { actual: deploymentBytes, budget: 1_000_000_000 })
if (!htmlFiles.length) issue('missing_html_build', { path: dist })
const documents = new Map(htmlFiles.map((file) => [file, load(fs.readFileSync(file, 'utf8'))]))
let internalLinks = 0
const evidenceQueries = []
const preloadsByRoute = new Map()
for (const [file, $] of documents) {
  const current = routeForFile(file)
  const scriptEntries = new Set()
  $('a[href], link[href], script[src], img[src]').each((_, element) => {
    const raw = $(element).attr('href') || $(element).attr('src')
    if (!raw || /^(mailto:|tel:|data:|blob:)/i.test(raw)) return
    const resolved = resolveInternal(raw, current)
    if (!resolved) return
    internalLinks++
    if (resolved.error || !resolved.file) {
      issue('broken_internal_link', { page: current, href: raw, reason: resolved.error || 'not_in_built_output' })
      return
    }
    if (resolved.url.hash && resolved.file.endsWith('.html')) {
      let fragment
      try { fragment = decodeURIComponent(resolved.url.hash.slice(1)) } catch { fragment = resolved.url.hash.slice(1) }
      const target = documents.get(resolved.file)
      if (fragment && target && !target('[id], a[name]').toArray().some((node) => target(node).attr('id') === fragment || target(node).attr('name') === fragment)) issue('missing_anchor', { page: current, href: raw })
    }
    if (resolved.url.pathname.includes('/database/') && (resolved.url.searchParams.has('ids') || resolved.url.searchParams.has('work'))) evidenceQueries.push({ page: current, ids: (resolved.url.searchParams.get('ids') || resolved.url.searchParams.get('work')).split(',').filter(Boolean) })
    const isModule = element.tagName === 'script' && $(element).attr('type') === 'module'
    const isPreload = element.tagName === 'link' && ($(element).attr('rel') || '').split(/\s+/).includes('modulepreload')
    if ((isModule || isPreload) && resolved.file.endsWith('.js')) scriptEntries.add(resolved.file)
  })
  preloadsByRoute.set(current, scriptEntries)
}

// Follow static JS imports in the produced graph. Dynamic imports are counted
// when the rendered page actually declares them as modulepreloads, not merely
// because their names occur in a Vite dependency-map array.
const scriptDependencies = new Map()
const dependencies = (file) => {
  if (scriptDependencies.has(file)) return scriptDependencies.get(file)
  const contents = fs.readFileSync(file, 'utf8')
  const result = []
  const regex = /(?:^|[;\n])\s*(?:import\s*(?:[^;"']*?\bfrom\s*)?|export\s*\{[^}]*\}\s*from\s*)["']([^"']+)["']/g
  for (const match of contents.matchAll(regex)) {
    if (!match[1].startsWith('.')) continue
    const target = path.resolve(path.dirname(file), match[1].split('?')[0])
    if (!existsFile(target)) issue('missing_static_js_import', { file: path.relative(dist, file), import: match[1] })
    else result.push(target)
  }
  scriptDependencies.set(file, result)
  return result
}
const gzipCache = new Map()
const gzipBytes = (file) => {
  if (!gzipCache.has(file)) gzipCache.set(file, gzipSync(fs.readFileSync(file)).length)
  return gzipCache.get(file)
}
const routes = []
for (const [route, entries] of preloadsByRoute) {
  const loaded = new Set()
  const queue = [...entries]
  while (queue.length) {
    const item = queue.pop()
    if (loaded.has(item)) continue
    loaded.add(item)
    queue.push(...dependencies(item))
  }
  const isChartRoute = route === base || /^\/(?:trends|monthly|organizations|hardware)(?:\/|$)/.test(route.slice(base.length - 1))
  const budget = isChartRoute ? 450_000 : 250_000
  const bytes = [...loaded].reduce((sum, file) => sum + gzipBytes(file), 0)
  routes.push({ route, initial_js_gzip_bytes: bytes, budget_bytes: budget, pass: bytes <= budget,
    scripts: [...loaded].map((file) => ({ path: path.relative(dist, file), gzip_bytes: gzipBytes(file) })).sort((a, b) => b.gzip_bytes - a.gzip_bytes) })
  if (bytes > budget) issue('initial_js_budget_exceeded', { route, actual: bytes, budget })
}

const api = path.join(dist, 'api/v1')
const manifest = readJson(path.join(api, 'catalog-manifest.json'), {})
const currentManifest = readJson(path.join(root, 'docs/public/api/v1/catalog-manifest.json'), {})
const authorityManifest = readJson(path.join(root, 'data/catalog/manifest.json'), {})
if (!manifest.dataset_version || manifest.dataset_version !== currentManifest.dataset_version || manifest.catalog_hash !== authorityManifest.catalog_hash) issue('mixed_dataset_revisions', { built: manifest.dataset_version, current: currentManifest.dataset_version, built_catalog: manifest.catalog_hash, authority_catalog: authorityManifest.catalog_hash })
for (const route of ['', 'trends/', 'trends/loco-manip/', 'hardware/', 'hardware/coverage', 'monthly/', 'organizations/', 'database/', 'pulse/', 'methods/', 'organizations/collaboration']) {
  if (!resolveInternal(base + route, base)?.file) issue('missing_required_route', { route: base + route })
}
for (const required of ['trends.json', 'aliases.json', 'events.json', 'source-health.json', 'source-coverage.json', 'migration-report.json', 'release-recall.json', 'coverage-gold-releases.json', 'work-organization-links.json', 'equipment/coverage-summary.json', 'equipment/coverage-model-candidates.json']) readJson(path.join(api, required))
for (const edition of readJson(path.join(api, 'conference-editions.json'), {}).editions || []) {
  const changes = readJson(path.join(api, 'conference-changes', `${edition.edition_id}.json`), {})
  if (changes.edition_id !== edition.edition_id || changes.catalog_hash !== manifest.catalog_hash || !Array.isArray(changes.tracks)) issue('conference_change_contract', { edition: edition.edition_id })
}
const releaseRecall = readJson(path.join(api, 'release-recall.json'), {})
if (releaseRecall.catalog_hash !== manifest.catalog_hash || releaseRecall.regression_gate?.status !== 'passed') issue('release_recall_regression_failed', { gate: releaseRecall.regression_gate })
if (!Number.isInteger(manifest.counts?.works) || !Array.isArray(manifest.complete_months) || manifest.complete_months.length !== 12 || !Array.isArray(manifest.available_months)) issue('manifest_contract', { message: 'Expected work count, exactly 12 complete months and available_months.' })
const months = []
for (const month of manifest.available_months || []) {
  const snapshot = readJson(path.join(api, 'monthly', `${month}.json`), {})
  if (snapshot.month !== month || !snapshot.coverage || !['complete', 'provisional'].includes(snapshot.status)) issue('monthly_contract', { month })
  if (new Set(snapshot.directions?.map((row) => row.code)).size !== 15 || new Set(snapshot.questions?.map((row) => row.code)).size !== 11) issue('monthly_axis_coverage', { month })
  months.push(snapshot)
}
const organizations = readJson(path.join(api, 'organizations.json'), [])
if (!Array.isArray(organizations) || organizations.length !== manifest.counts?.organizations) issue('organization_count_mismatch', { expected: manifest.counts?.organizations, actual: organizations?.length })
for (const organization of Array.isArray(organizations) ? organizations : []) {
  const detail = readJson(path.join(api, 'organizations', `${organization.slug}.json`), {})
  if (!resolveInternal(`${base}organizations/${organization.slug}`, base)?.file) issue('missing_organization_profile', { organization_id: organization.organization_id, slug: organization.slug })
  if (detail.organization_id !== organization.organization_id || !Array.isArray(detail.work_ids) || !Array.isArray(detail.updates)) issue('organization_detail_contract', { slug: organization.slug })
}

let sourceIds = new Set()
try { sourceIds = readSourceRecordIds(path.join(root, 'data/catalog')) }
catch (error) { issue('invalid_source_authority', { reason: error.message?.startsWith('source_record_store:') ? error.message : 'source_authority_io_failed' }) }
const knownWorks = new Set()
let checkedSources = 0
let checkedManifestations = 0
const workFiles = walk(path.join(api, 'works')).filter((file) => file.endsWith('.json'))
if (workFiles.length !== manifest.work_shards) issue('work_shard_count', { actual: workFiles.length, expected: manifest.work_shards })
for (const file of workFiles) {
  const rows = readJson(file, [])
  if (!Array.isArray(rows)) { issue('work_shard_contract', { file }); continue }
  for (const work of rows) {
    if (knownWorks.has(work.work_id)) issue('duplicate_built_work', { work_id: work.work_id })
    knownWorks.add(work.work_id)
    for (const id of work.source_record_ids || []) { checkedSources++; if (!sourceIds.has(id)) issue('unresolved_source_record', { work_id: work.work_id, source_record_id: id }) }
    const manifestationIds = new Set((work.manifestations || []).map((row) => row.manifestation_id))
    for (const id of work.manifestation_ids || []) { checkedManifestations++; if (!manifestationIds.has(id)) issue('missing_work_manifestation', { work_id: work.work_id, manifestation_id: id }) }
  }
}
if (knownWorks.size !== manifest.counts?.works) issue('built_work_count', { actual: knownWorks.size, expected: manifest.counts?.works })
const knownTextIds = new Set()
for (const shard of manifest.text_shards || []) for (const row of readJson(path.join(api, 'text', `${shard}.json`), [])) {
  if (knownTextIds.has(row.snapshot_id) || !knownWorks.has(row.work_id) || !sourceIds.has(row.source_record_id)) issue('invalid_built_text_snapshot', { snapshot_id: row.snapshot_id, work_id: row.work_id })
  knownTextIds.add(row.snapshot_id)
}
if (knownTextIds.size !== manifest.text_snapshot_count) issue('text_snapshot_count_mismatch', { actual: knownTextIds.size, expected: manifest.text_snapshot_count })
const aliases = readJson(path.join(api, 'aliases.json'), {})
const validWork = (id) => knownWorks.has(id) || knownWorks.has(aliases[id])
for (const query of evidenceQueries) for (const id of query.ids) if (!validWork(id)) issue('unresolved_evidence_link', { page: query.page, id })
for (const organization of Array.isArray(organizations) ? organizations : []) {
  for (const id of organization.work_ids || []) if (!validWork(id)) issue('unresolved_organization_work', { organization_id: organization.organization_id, id })
  for (const event of organization.updates || []) if (event.work_id && !validWork(event.work_id)) issue('unresolved_organization_event_work', { event_id: event.event_id, id: event.work_id })
}

// Validate the actual public work objects with the project's full JSON Schema.
// The SQLite ZIP is checked separately in bounded chunks without loading a dump.
const schemaCode = `import json,sys\nfrom pathlib import Path\nfrom jsonschema import Draft202012Validator\nvalidator=Draft202012Validator(json.loads(Path(sys.argv[2]).read_text()))\nerrors=[]\ncount=0\nfor path in sorted(Path(sys.argv[1]).glob('*.json')):\n for row in json.loads(path.read_text()):\n  count+=1\n  for error in validator.iter_errors(row):\n   if len(errors)<20: errors.append({'work_id':row.get('work_id'),'path':list(error.path),'message':error.message})\nprint(json.dumps({'checked':count,'errors':errors}))\n`
const schemaRun = spawnSync(process.execPath, [path.join(root, 'scripts/run-python.mjs'), '-c', schemaCode, path.join(api, 'works'), path.join(root, 'config/catalog-v3.schema.json')], { cwd: root, encoding: 'utf8', maxBuffer: 4_000_000 })
let schema = { status: 'unverified' }
if (schemaRun.status !== 0) issue('public_schema_validation_unavailable', { message: (schemaRun.stderr || schemaRun.stdout).slice(0, 500) })
else { try { schema = JSON.parse(schemaRun.stdout); if (schema.errors.length) issue('public_schema_validation_failed', { examples: schema.errors }) } catch { issue('public_schema_validation_invalid_output', {}) } }
let sqliteDownload = { status: 'unverified' }
try { sqliteDownload = await auditSqliteDownload(dist, manifest.downloads) }
catch (error) { issue('invalid_sqlite_download', { message: error.message }) }

const pagefindDirectory = path.join(dist, 'pagefind')
const searchFiles = walk(pagefindDirectory)
const searchBytes = searchFiles.filter((file) => !file.endsWith('radar-metrics.json')).reduce((sum, file) => sum + gzipBytes(file), 0)
const searchMetrics = readJson(path.join(pagefindDirectory, 'radar-metrics.json'), {})
if (!existsFile(path.join(pagefindDirectory, 'pagefind.js')) || searchMetrics.indexed_works !== knownWorks.size) issue('search_build_incomplete', { indexed: searchMetrics.indexed_works, expected: knownWorks.size })
if (searchMetrics.dataset_version !== manifest.dataset_version || searchMetrics.catalog_hash !== manifest.catalog_hash) issue('search_dataset_revision_mismatch', { search: searchMetrics.dataset_version, site: manifest.dataset_version })
if (searchBytes > 20_000_000) issue('search_index_budget_exceeded', { actual: searchBytes, budget: 20_000_000 })
const home = routes.find((row) => row.route === base)
const homeData = home?.scripts.filter((row) => /v3-overview[^/]*\.js$/.test(row.path)).reduce((sum, row) => sum + row.gzip_bytes, 0) || 0
if (!homeData) warnings.push({ type: 'home_payload_not_separately_identified', message: 'Inspect emitted app modules; do not assume an unmeasured data payload is zero.' })
if (homeData > 200_000) issue('home_data_budget_exceeded', { actual: homeData, budget: 200_000 })
warnings.push({ type: 'runtime_metrics_unverified', message: 'Static audit cannot prove mobile LCP ≤ 2.5 s, CLS < 0.1 or runtime API availability. Browser measurements are a separate required gate.' })
const report = { status: errors.length ? 'failed' : 'passed_static_gates', generated_at: new Date().toISOString(), dist,
  counts: { html_pages: htmlFiles.length, checked_internal_links: internalLinks, organizations: organizations.length, works: knownWorks.size, source_references: checkedSources, manifestation_references: checkedManifestations, monthly_snapshots: months.length },
  public_schema: schema, sqlite_download: sqliteDownload, performance: { deployment_bytes: deploymentBytes, deployment_budget: 1_000_000_000, home_data_gzip_bytes: homeData || null, home_data_budget: 200_000, search_gzip_bytes: searchBytes, search_budget: 20_000_000, routes },
  runtime: { lcp: 'unverified', cls: 'unverified', api_availability: 'unverified' }, errors, warnings }
fs.mkdirSync(path.dirname(reportPath), { recursive: true })
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n')
console.log(JSON.stringify({ status: report.status, counts: report.counts, error_count: errors.length, errors: errors.slice(0, 12), home_data_gzip_bytes: homeData || null, search_gzip_bytes: searchBytes,
  largest_initial_routes: [...routes].sort((a, b) => b.initial_js_gzip_bytes - a.initial_js_gzip_bytes).slice(0, 4).map(({ scripts, ...row }) => row), report: reportPath }, null, 2))
if (errors.length) process.exitCode = 1
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main()
