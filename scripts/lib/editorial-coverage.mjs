// Only validated public monthly overlays count; a successful latest run or a
// preserved-but-stale historical artifact cannot stand in for twelve months.
export function editorialCoverage(months, statusByMonth) {
  const required = [...new Set(months)]
  const completed = required.filter((month) => statusByMonth[month] === 'llm_complete')
  return {
    status: required.length && completed.length === required.length ? 'llm_complete' : completed.length ? 'partial' : 'data_only',
    completed_months: completed,
    remaining_months: required.filter((month) => !completed.includes(month)),
  }
}

export function dashboardSnapshot(snapshot) {
  // Full model artifacts/review lineage remain in the monthly JSON endpoint;
  // retain only the small public narrative of a stale previous artifact. This
  // never promotes its claims into current findings or completion coverage.
  const { editorial, previous_editorial, previous_editorial_summary, editorial_history, ...view } = snapshot
  const previous = previousEditorialSummary(previous_editorial || previous_editorial_summary, snapshot.month)
  if (previous) view.previous_editorial_summary = previous
  if (Array.isArray(editorial_history)) {
    view.editorial_history = editorial_history.filter(isObject).map(row => Object.fromEntries(
      ['artifact_digest', 'generated_at', 'model', 'input_digest', 'archive_url', 'input_packet_status']
        .filter(key => typeof row[key] === 'string').map(key => [key, row[key]]),
    ))
  }
  return view
}

const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value)
const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value)
const publicText = value => typeof value === 'string' && Boolean(value.trim())
const strings = value => Array.isArray(value) ? value.filter(publicText) : []
const historicalSections = ['claims', 'direction_summaries', 'question_summaries', 'counterevidence', 'watchlist']

export function previousEditorialSummary(artifact, month) {
  if (!isObject(artifact) || !/^20\d{2}-(0[1-9]|1[0-2])$/.test(month || '') || artifact.month !== month ||
      !['complete', 'historical_not_current'].includes(artifact.status) || !digest(artifact.input_digest) ||
      !publicText(artifact.model) || !publicText(artifact.generated_at) || !Number.isFinite(Date.parse(artifact.generated_at))) return null
  const summary = { month, model: artifact.model, generated_at: artifact.generated_at,
    input_digest: artifact.input_digest, status: 'historical_not_current' }
  for (const section of historicalSections) {
    summary[section] = (Array.isArray(artifact[section]) ? artifact[section] : []).filter(isObject)
      .filter(row => publicText(row.summary) || publicText(row.text)).map(row => {
        const copy = Object.fromEntries(['claim_id', 'code', 'title', 'summary', 'text']
          .filter(key => publicText(row[key])).map(key => [key, row[key]]))
        for (const key of ['directions', 'questions', 'supporting_ids', 'counterevidence_ids']) {
          if (Array.isArray(row[key])) copy[key] = [...strings(row[key])]
        }
        return copy
      })
  }
  return historicalSections.some(key => summary[key].length) ? summary : null
}
