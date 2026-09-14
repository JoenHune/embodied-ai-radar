import fs from 'node:fs'
import path from 'node:path'
import { visualMediaCatalog, publicMediaUrl } from './lib/visual-media.mjs'

const root = path.resolve(import.meta.dirname, '..')
const api = path.join(root, 'docs/public/api/v1')
const read = name => JSON.parse(fs.readFileSync(path.join(api, name), 'utf8'))
const lines = name => fs.readFileSync(path.join(root, name), 'utf8').split('\n').filter(Boolean).map(JSON.parse)
const manifest = read('catalog-manifest.json')
const sourceRecords = lines('data/visual-media.jsonl')
const persons = lines('data/people/persons.jsonl')
const workIds = fs.readdirSync(path.join(root, 'data/catalog/works')).flatMap(file => lines(`data/catalog/works/${file}`).map(row => row.work_id))
const expected = visualMediaCatalog(sourceRecords, persons, workIds)
const actual = read('visual-media.json')
const errors = []
const require = (condition, message) => { if (!condition) errors.push(message) }
require(JSON.stringify(actual) === JSON.stringify(expected), 'media_authority_projection_mismatch')
const equalIds = (left, right) => JSON.stringify([...new Set(left)].sort()) === JSON.stringify([...new Set(right)].sort())
let cards = 0
const checkRows = (body, label) => {
  require(body.schema_version === '1' && body.dataset_version === manifest.dataset_version, `feed_version:${label}`)
  require(body.total === body.rows.length && new Set(body.rows.map(row => row.work_id)).size === body.rows.length, `feed_duplicate_or_count:${label}`)
  for (const row of body.rows) {
    require(publicMediaUrl(row.original_url), `feed_original_url:${row.work_id}`)
    require(row.source_catalog_hash === manifest.catalog_hash, `feed_catalog_hash:${row.work_id}`)
  }
  cards += body.rows.length
}
for (const month of manifest.available_months) {
  const body = read(`visual-feed/monthly/${month}.json`)
  checkRows(body, month)
  require(equalIds(body.rows.map(row => row.work_id), read(`monthly/${month}.json`).work_ids), `feed_cohort:${month}`)
}
const windowIds = new Set(manifest.complete_months.flatMap(month => read(`monthly/${month}.json`).work_ids))
const featured = read('visual-feed/featured.json')
checkRows(featured, 'featured')
require(featured.selection === 'reviewed_official_media_examples_not_research_ranking', 'featured_selection_not_disclosed')
require(featured.rows.every(row => windowIds.has(row.work_id) && actual.assets[row.work_id]), 'featured_scope_or_media')
for (const organization of read('organizations.json')) {
  const body = read(`visual-feed/organizations/${organization.slug}.json`)
  checkRows(body, organization.slug)
  require(equalIds(body.rows.map(row => row.work_id), organization.research_work_ids.filter(id => windowIds.has(id))), `organization_feed_scope:${organization.slug}`)
}
const index = read('visual-feed/index.json')
require(index.media_registry_hash === expected.registry_hash && index.dataset_version === manifest.dataset_version, 'visual_index_version')
const report = { status: errors.length ? 'failed' : 'passed', errors, counts: { ...expected.counts, featured: featured.total, monthly_feeds: manifest.available_months.length, checked_cards: cards },
  limits: ['Metadata and source relationships audited; this does not assert image reuse permission or live browser image availability.'] }
fs.mkdirSync(path.join(root, 'logs'), { recursive: true })
fs.writeFileSync(path.join(root, 'logs/v3-visual-audit.json'), JSON.stringify(report, null, 2) + '\n')
process.stdout.write(JSON.stringify(report, null, 2) + '\n')
if (errors.length) process.exitCode = 1
