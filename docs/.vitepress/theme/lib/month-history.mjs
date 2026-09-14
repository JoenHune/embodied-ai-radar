/** Pure month URL rules. No history/browser state is read or mutated here. */
export function resolveMonthFromUrl(href, availableMonths, defaultMonth) {
  const month = new URL(href).searchParams.get('month')
  return availableMonths.includes(month) ? month : defaultMonth
}

/** Only a successful, user-selected month transition creates an entry. */
export function monthHistoryTarget(href, month, { availableMonths, defaultMonth, source = 'selection' }) {
  if (source !== 'selection' || !availableMonths.includes(month)) return null
  if (resolveMonthFromUrl(href, availableMonths, defaultMonth) === month) return null
  const url = new URL(href)
  url.searchParams.set('month', month)
  return url.href
}

/** Protect both the displayed snapshot and URL from stale/unmounted loads. */
export function monthRequestIsCurrent({ request, currentRequest, disposed, requestPath, currentPath }) {
  return !disposed && request === currentRequest && requestPath === currentPath
}
