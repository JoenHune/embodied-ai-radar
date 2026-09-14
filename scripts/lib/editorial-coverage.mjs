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
  // the dashboard uses the already-derived findings, facets and review labels.
  const { editorial, previous_editorial, ...view } = snapshot
  return view
}
