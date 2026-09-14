import fs from 'node:fs'
import path from 'node:path'
import { originalSourceUrl } from '../docs/.vitepress/theme/lib/research-card.mjs'
import { publicationRecords } from '../docs/.vitepress/theme/lib/work-status.mjs'

const root = path.resolve(import.meta.dirname, '..')
const api = path.join(root, 'docs/public/api/v1')
const read = name => JSON.parse(fs.readFileSync(path.join(api, name), 'utf8'))
const manifest = read('catalog-manifest.json')
const usage = read('equipment/usage.json')
const loco = read('equipment/loco-manip.json')
if ([usage, loco].some(row => row.dataset_version !== manifest.dataset_version)) throw Error('equipment_card_dataset_mismatch')
const ids = new Set([...Object.keys(usage.by_work), ...Object.values(loco.work_ids).flat()])
const rows = []
for (const file of fs.readdirSync(path.join(api, 'works')).filter(name => name.endsWith('.json'))) {
  for (const work of read(`works/${file}`)) {
    if (!ids.has(work.work_id)) continue
    rows.push({ work_id: work.work_id, title: work.title, title_zh: work.title_zh || '',
      summary: work.summary_zh || work.abstract?.slice(0, 260) || '', original_url: originalSourceUrl(work),
      first_public_date: work.first_public_date, first_public_date_precision: work.first_public_date_precision,
      primary_direction: work.primary_direction, directions: work.directions || [], relevance_status: work.relevance?.status,
      output_types: [...new Set((work.manifestations || []).map(row => row.kind))],
      company_self_report: (work.manifestations || []).some(row => row.kind === 'technical_report'),
      strict_peer_reviewed: work.strict_peer_reviewed, research_status: work.research_status,
      publication_records: publicationRecords(work), hardware_usage: usage.by_work[work.work_id] || [],
      organizations: (work.organization_attributions || []).filter(row => ['G1', 'G2'].includes(row.evidence_grade)).map(row => ({ organization_id: row.organization_id, name: row.name })) })
  }
}
if (rows.length !== ids.size) throw Error('equipment_missing_work_card')
rows.sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || '') || a.work_id.localeCompare(b.work_id))
fs.writeFileSync(path.join(api, 'equipment/works.json'), JSON.stringify({ schema_version: '1', dataset_version: manifest.dataset_version, rows }) + '\n')
// Small lazy lookup used by existing research cards; no full corpus download.
fs.writeFileSync(path.join(api, 'equipment/card-usage.json'), JSON.stringify({ schema_version: '1', dataset_version: manifest.dataset_version, by_work: usage.by_work }) + '\n')
console.log(JSON.stringify({ status: 'ok', equipment_work_cards: rows.length }))
