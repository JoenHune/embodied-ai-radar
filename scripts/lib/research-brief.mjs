const rows = value => Array.isArray(value) ? value : []
const localDate = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' })
const date = value => {
  if (typeof value !== 'string') return null
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const parsed = new Date(`${value}T00:00:00Z`)
    return Number.isFinite(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value ? value : null
  }
  if (!/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return null
  const parsed = new Date(value)
  return Number.isFinite(parsed.valueOf()) ? localDate.format(parsed) : null
}
const releaseTypes = new Set(['preprint', 'paper', 'technical_report', 'model_release', 'model', 'dataset_release', 'dataset', 'code', 'repository', 'benchmark_release', 'benchmark', 'project'])

// A site build and a historical full-text extraction are not collection checks.
export function researchBrief({ manifest, coverage, organizations }) {
  const sources = rows(coverage?.sources).map(source => ({
    source: source.source,
    status: source.status || 'unknown',
    complete: source.complete === true,
    checked_at: date(source.checked_at),
    observed_through: date(source.last_observed_data_through || source.source_data_through),
  }))
  const from = `${manifest.complete_months?.at(-1) || ''}-01`
  const through = date(manifest.data_through)
  const teams = rows(organizations).filter(org => ['T0', 'T1'].includes(org.tier)).flatMap(org => {
    const updates = rows(org.updates).filter(update => {
      const published = date(update.published_at)
      return published && update.date_precision === 'day' && published >= from && through && published <= through
        && ['G1', 'G2'].includes(update.attribution_grade) && update.research_eligible !== false
        && releaseTypes.has(update.event_type)
        && typeof update.url === 'string' && /^https?:\/\//.test(update.url)
    }).sort((a, b) => b.published_at.localeCompare(a.published_at) || String(a.event_id).localeCompare(String(b.event_id)))
    if (!updates.length) return []
    const update = updates[0]
    return [{ organization_id: org.organization_id, slug: org.slug, name: org.short_name || org.name,
      tier: org.tier, title: update.title, published_at: date(update.published_at),
      event_type: update.event_type, url: update.url, work_id: update.work_id || null }]
  }).sort((a, b) => b.published_at.localeCompare(a.published_at) || a.slug.localeCompare(b.slug)).slice(0, 4)
  return {
    analysis_through: through,
    available_data_through: date(coverage?.available_data_through),
    last_source_check: sources.map(source => source.checked_at).filter(Boolean).sort().at(-1) || null,
    status: coverage?.status || 'not_run',
    complete: coverage?.registered_scope_complete === true && sources.length > 0 && sources.every(source => source.complete),
    sources,
    teams,
    team_window: { from: date(from), through },
  }
}
