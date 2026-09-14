import fs from 'node:fs'
import path from 'node:path'
import { editorialCoverage, dashboardSnapshot } from './lib/editorial-coverage.mjs'

const root = path.resolve(import.meta.dirname, '..')
const api = path.join(root, 'docs', 'public', 'api', 'v1')
const target = path.join(root, 'docs', '.vitepress', 'data', 'v3-overview.json')
const read = (name) => JSON.parse(fs.readFileSync(path.join(api, name), 'utf8'))

const manifest = read('catalog-manifest.json')
const trends = read('trends.json')
const latestComplete = read(`monthly/${manifest.complete_months.at(-1)}.json`)
const provisional = read(`monthly/${manifest.provisional_month}.json`)
const organizations = read('organizations.json')
const editorialStatusPath = path.join(root, 'data', 'editorial', 'status.json')
const editorialRuns = fs.existsSync(editorialStatusPath)
  ? JSON.parse(fs.readFileSync(editorialStatusPath, 'utf8'))
  : { status: 'data_only', reason: 'No editorial run recorded' }
const editorialStatus = {
  ...editorialRuns,
  ...editorialCoverage(manifest.complete_months, Object.fromEntries(manifest.complete_months.map((month) => [month, read(`monthly/${month}.json`).editorial_status]))),
  latest_complete_month_status: latestComplete.editorial_status,
}

const overview = {
  manifest,
  trends,
  latestComplete: dashboardSnapshot(latestComplete),
  provisional: dashboardSnapshot(provisional),
  editorialStatus,
  evidenceTimeline: [...manifest.complete_months, manifest.provisional_month].map((month) => {
    const snapshot = read(`monthly/${month}.json`)
    const events = snapshot.evidence_events || []
    const count = (types) => new Set(events.filter((event) => types.includes(event.event_type)).map((event) => event.work_id || event.event_id)).size
    return {
      month, new_works: snapshot.coverage?.included_works || 0,
      accepted: count(['acceptance', 'accepted_peer_reviewed', 'accepted']),
      published: count(['publication', 'published_proceedings', 'published']),
      replicated: count(['independent_replication']),
    }
  }),
  organizations: organizations.map((row) => ({
    organization_id: row.organization_id,
    slug: row.slug,
    name: row.name,
    short_name: row.short_name,
    tier: row.tier,
    entity_type: row.entity_type,
    tracking_category: row.tracking_category,
    startup_frontier: row.startup_frontier,
    region: row.region,
    source_health: row.source_health,
    last_checked: row.last_checked,
    last_changed: row.last_changed || row.updates?.map((event) => event.published_at || '').sort().at(-1) || null,
    official_urls: row.official_urls,
    summary_zh: row.summary_zh,
    declared_direction_codes: row.declared_direction_codes,
    actual_direction_counts: row.actual_direction_counts,
    recent_work_count: row.recent_work_count,
    work_ids: row.work_ids || [],
    updates: row.updates || [],
  })),
}

// Organization archives are needed on organization routes, not in every
// homepage/trend bundle. Keep the same fields behind one versioned request.
fs.writeFileSync(path.join(api, 'organization-overview.json'), `${JSON.stringify({ dataset_version: manifest.dataset_version, rows: overview.organizations })}\n`)
overview.organizations = []
fs.mkdirSync(path.dirname(target), { recursive: true })
fs.writeFileSync(target, `${JSON.stringify(overview)}\n`)
fs.writeFileSync(path.join(api, 'editorial-status.json'), `${JSON.stringify(editorialStatus)}\n`)
const organizationPages = path.join(root, 'docs', 'organizations')
fs.mkdirSync(organizationPages, { recursive: true })
for (const organization of organizations) {
  if (!/^[a-z0-9][a-z0-9-]*$/.test(organization.slug)) throw new Error(`Unsafe organization slug: ${organization.slug}`)
  fs.writeFileSync(path.join(organizationPages, `${organization.slug}.md`), `---\nlayout: page\ntitle: ${JSON.stringify(organization.name)}\nsidebar: false\naside: false\npageClass: v3-page\n---\n\n<RadarDashboard mode="organizations" organization="${organization.slug}" />\n`)
}
process.stdout.write(`Saved v3 overview for ${manifest.complete_months[0]}—${manifest.provisional_month}.\n`)

const weeklyDirectory = path.join(root, 'docs/pulse/weekly')
fs.mkdirSync(weeklyDirectory, { recursive: true })
const weeklyPages = fs.readdirSync(weeklyDirectory).filter((name) => /^20\d{2}-w\d{2}\.md$/.test(name)).sort().reverse()
fs.writeFileSync(path.join(weeklyDirectory, 'index.md'), `---\ntitle: 研究组历史周报\n---\n\n# 研究组历史周报\n\n每周按 ISO 周归档；论文首次出现与后续验证分别记录。\n\n${weeklyPages.length ? weeklyPages.map((file) => `- [${file.slice(0, -3).toUpperCase()}](./${file.slice(0, -3)})`).join('\n') : '首份 v3 周报会在完成一次正式周更后出现在这里。'}\n`)
