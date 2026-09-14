export const PEOPLE_BATCH_SIZE = 12

export function nextPeopleCount(current, total) {
  return Math.min(total, current + PEOPLE_BATCH_SIZE)
}

// Opening a profile is not a new result set.
export function peopleStreamKey(state) {
  return JSON.stringify([state.q, state.direction, state.lens, state.sort])
}

// VitePress would otherwise reload the same page on query-history navigation,
// replacing its initial lean component and losing the accumulated stream.
export function preservePeoplePage(router, pathname, restore = () => {}) {
  const previous = router.onBeforePageLoad
  const guard = href => {
    if (new URL(href, 'https://radar.invalid').pathname === pathname) { restore(); return false }
    return previous?.(href)
  }
  router.onBeforePageLoad = guard
  return () => { if (router.onBeforePageLoad === guard) router.onBeforePageLoad = previous }
}

export function observePeopleEnd(element, canLoad, loadMore, Observer = typeof IntersectionObserver === 'undefined' ? null : IntersectionObserver) {
  if (!Observer || !element) return () => {}
  let stopped = false
  const observer = new Observer(entries => {
    if (!stopped && entries.some(entry => entry.isIntersecting) && canLoad()) loadMore()
  }, { rootMargin: '360px 0px', threshold: 0 })
  observer.observe(element)
  return () => { stopped = true; observer.disconnect() }
}
