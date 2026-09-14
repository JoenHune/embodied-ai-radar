import fs from 'node:fs'
import path from 'node:path'
import { visualMediaCatalog } from './lib/visual-media.mjs'
import { originalSourceUrl } from '../docs/.vitepress/theme/lib/research-card.mjs'
import { publicationRecords } from '../docs/.vitepress/theme/lib/work-status.mjs'
import { conflictsForWork, sourceConflictIndex } from '../docs/.vitepress/theme/lib/source-conflicts.mjs'

const root = path.resolve(import.meta.dirname, '..')
const lines = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const records = lines(path.join(root, 'data/visual-media.jsonl'))
const persons = lines(path.join(root, 'data/people/persons.jsonl'))
const workIds = fs.readdirSync(path.join(root, 'data/catalog/works')).filter(file => file.endsWith('.jsonl'))
  .flatMap(file => lines(path.join(root, 'data/catalog/works', file)).map(work => work.work_id))
const catalog = visualMediaCatalog(records, persons, workIds)
const api = path.join(root, 'docs/public/api/v1')
const read = file => JSON.parse(fs.readFileSync(path.join(api, file), 'utf8'))
const manifest = read('catalog-manifest.json')
const sourceConflicts = sourceConflictIndex(read('source-content-conflicts.json'), manifest.dataset_version)
fs.mkdirSync(api, { recursive: true })
fs.writeFileSync(path.join(api, 'visual-media.json'), JSON.stringify(catalog) + '\n')
const people = read('people/index.json').people
const verifiedPeople = new Map()
for (const person of people.filter(row => row.identity_status === 'profile_verified')) {
  for (const work of person.verified_work_ids) {
    if (!verifiedPeople.has(work)) verifiedPeople.set(work, [])
    verifiedPeople.get(work).push({ person_id: person.person_id, slug: person.slug, name: person.name })
  }
}
const workCards = new Map()
for (const file of fs.readdirSync(path.join(api, 'works')).filter(file => file.endsWith('.json'))) {
  for (const work of read(`works/${file}`)) {
    if (work.relevance?.status !== 'included') continue
    const source = originalSourceUrl(work)
    const asset = catalog.assets[work.work_id]
    // The asset registry can supply a reviewed direct report URL, but only
    // when that URL already belongs to this canonical work.
    const knownUrls = new Set([source, ...(work.manifestations || []).map(row => row.url)])
    if (asset?.original_url && !knownUrls.has(asset.original_url)) throw Error(`visual_original_work_mismatch:${work.work_id}`)
    const summary = work.summary_zh || work.abstract?.slice(0, 260) || ''
    const kinds = [...new Set((work.manifestations || []).map(row => row.kind))]
    workCards.set(work.work_id, {
      work_id: work.work_id, title: work.title, title_zh: work.title_zh || '',
      summary, summary_kind: work.summary_zh ? 'source_bound_editorial' : 'original_excerpt',
      first_public_date: work.first_public_date, first_public_date_precision: work.first_public_date_precision,
      primary_direction: work.primary_direction, directions: work.directions || [], questions: work.questions || [],
      original_url: asset?.original_url || source,
      output_types: kinds,
      company_self_report: kinds.includes('technical_report') || asset?.company_self_report === true,
      strategic_only: kinds.length > 0 && kinds.every(kind => ['demo', 'deployment', 'hiring', 'personnel_change', 'organization_change', 'funding'].includes(kind)),
      strict_peer_reviewed: Boolean(work.strict_peer_reviewed), evidence_grade: work.evidence_grade,
      research_status: work.research_status || null,
      source_conflicts: conflictsForWork(sourceConflicts, work.work_id),
      publication_records: publicationRecords(work),
      organizations: (work.organization_attributions || []).filter(row => ['G1', 'G2'].includes(row.evidence_grade)).map(row => ({ organization_id: row.organization_id, name: row.name })),
      people: verifiedPeople.get(work.work_id) || [],
      source_catalog_hash: manifest.catalog_hash,
    })
  }
}
const directory = path.join(api, 'visual-feed')
fs.mkdirSync(path.join(directory, 'monthly'), { recursive: true })
const write = (file, data) => fs.writeFileSync(path.join(directory, file), JSON.stringify(data) + '\n')
const monthCounts = []
const windowIds = new Set()
for (const month of manifest.available_months) {
  const snapshot = read(`monthly/${month}.json`)
  const ids = [...new Set(snapshot.work_ids)]
  const rows = ids.map(id => workCards.get(id)).filter(Boolean).sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || '') || a.work_id.localeCompare(b.work_id))
  if (rows.length !== ids.length) throw Error(`visual_feed_cohort_mismatch:${month}`)
  if (manifest.complete_months.includes(month)) rows.forEach(row => windowIds.add(row.work_id))
  write(`monthly/${month}.json`, { schema_version: '1', dataset_version: manifest.dataset_version, month, status: snapshot.status, rows, total: rows.length })
  monthCounts.push({ month, count: rows.length, status: snapshot.status })
}
const featured = records.filter(row => row.entity_type === 'work' && windowIds.has(row.entity_id)).map(row => workCards.get(row.entity_id))
  .sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || '') || a.work_id.localeCompare(b.work_id))
write('featured.json', { schema_version: '1', dataset_version: manifest.dataset_version, selection: 'reviewed_official_media_examples_not_research_ranking', rows: featured, total: featured.length })
write('index.json', { schema_version: '1', dataset_version: manifest.dataset_version, data_through: manifest.data_through,
  complete_months: manifest.complete_months, provisional_month: manifest.provisional_month, months: monthCounts,
  featured_count: featured.length, media_registry_hash: catalog.registry_hash })
const peopleHighlights = {}
for (const person of people) peopleHighlights[person.person_id] = person.verified_work_ids.map(id => workCards.get(id)).filter(Boolean)
  .sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || ''))
write('people-highlights.json', { schema_version: '1', dataset_version: manifest.dataset_version, people: peopleHighlights })
fs.mkdirSync(path.join(directory, 'organizations'), { recursive: true })
for (const organization of read('organizations.json')) {
  const rows = [...new Set(organization.research_work_ids)].filter(id => windowIds.has(id)).map(id => workCards.get(id)).filter(Boolean)
    .sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || ''))
  if (!/^[a-z0-9][a-z0-9-]*$/.test(organization.slug)) throw Error('unsafe organization slug')
  write(`organizations/${organization.slug}.json`, { schema_version: '1', dataset_version: manifest.dataset_version, organization_id: organization.organization_id, rows, total: rows.length })
}
process.stdout.write(JSON.stringify({ status: 'ok', visual_media: catalog.counts, featured: featured.length, monthly_feeds: monthCounts.length, included_cards: workCards.size }) + '\n')
