export function evidenceIds(row) {
  // Explicit editorial references take precedence over generic top-five samples.
  for (const field of ['supporting_ids', 'supporting_work_ids', 'work_ids']) {
    if (Array.isArray(row?.[field])) return row[field]
  }
  return []
}

export function evidenceWorkIds(ids, eventToWork = {}) {
  return [...new Set(ids.map((id) => eventToWork[id] || id))]
}

export function evidenceSearchParams(ids, eventToWork = {}, params = {}) {
  const query = new URLSearchParams(params)
  if (ids.length) {
    query.set('ids', evidenceWorkIds(ids, eventToWork).join(','))
    // A current-month acceptance may cite a much older canonical work.
    // Explicit evidence drilldowns must not hide it behind first-public dates.
    query.delete('from')
    query.delete('to')
  }
  return query
}
