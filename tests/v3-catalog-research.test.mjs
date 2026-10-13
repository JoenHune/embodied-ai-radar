import test from 'node:test'
import assert from 'node:assert/strict'
import { activeSearchFilters, clearedSearchFilter, compareResearchDates, createSearchRestorer, orderSearchPositions, readSearchSort, writeSearchSort } from '../docs/.vitepress/theme/lib/catalog-research.mjs'
import { defaultFilters, readSearchUrl, writeSearchUrl } from '../docs/.vitepress/theme/lib/catalog-search.ts'

test('deep-linked filters retain recognizable labels and individual direction removals', () => {
  const filters = readSearchUrl(new URLSearchParams('q=world+model&directions=D1,D3&direction_match=all&organizations=org:pi&ids=work:a,work:b,work:a')).filters
  const chips = activeSearchFilters(filters, { directions: [{ value: 'D1', label: '基础模型' }, { value: 'D3', label: '世界模型' }], organizations: [{ value: 'org:pi', label: 'Physical Intelligence' }] })
  assert.deepEqual(chips.filter(chip => chip.key === 'direction').map(chip => chip.label), ['共同命中方向：基础模型', '共同命中方向：世界模型'])
  assert.equal(chips.find(chip => chip.key === 'organization').label, '组织：Physical Intelligence')
  assert.equal(chips.find(chip => chip.key === 'ids').label, '证据集合：2 项')
  Object.assign(filters, clearedSearchFilter(filters, chips.find(chip => chip.key === 'direction')))
  assert.equal(filters.direction, 'D3')
  assert.equal(filters.directionMatch, 'all')
  Object.assign(filters, clearedSearchFilter(filters, activeSearchFilters(filters).find(chip => chip.key === 'direction')))
  assert.equal(filters.direction, '')
  assert.equal(filters.directionMatch, 'any')
  assert.equal(filters.q, 'world model')
  assert.equal(filters.ids, 'work:a,work:b,work:a')
})

test('clearing boolean, exact collection and relevance filters restores the expected defaults', () => {
  const filters = { ...defaultFilters(), ids: 'work:a', relevance: 'all', realRobot: true }
  assert.deepEqual(clearedSearchFilter(filters, { key: 'realRobot' }), { realRobot: false })
  assert.deepEqual(clearedSearchFilter(filters, { key: 'ids' }), { ids: '' })
  assert.deepEqual(clearedSearchFilter(filters, { key: 'relevance' }), { relevance: 'included' })
  assert.deepEqual(clearedSearchFilter(filters, { key: '__proto__' }), {})
  assert.deepEqual(activeSearchFilters(defaultFilters()), [])
  assert.equal(activeSearchFilters({ ...defaultFilters(), q: 'all' })[0].label, '关键词：all')
})

test('sort, exact evidence, intersection mode, page and opened work survive URL roundtrips', () => {
  const filters = { ...defaultFilters(), direction: 'D1,D3', directionMatch: 'all', ids: 'work:a,work:b', relevance: 'all' }
  const url = writeSearchSort(writeSearchUrl(new URL('https://example.test/database/'), filters, 4, 'work:a'), 'oldest')
  assert.deepEqual(readSearchUrl(url.searchParams), { filters, page: 4, work: 'work:a' })
  assert.equal(readSearchSort(url.searchParams), 'oldest')
  assert.equal(writeSearchSort(url, 'auto').searchParams.has('sort'), false)
  assert.equal(readSearchSort(new URLSearchParams('sort=untrusted')), 'auto')
})

const datedLookup = {
  work_ids: ['work:year', 'work:aug-month', 'work:aug-20', 'work:aug-02', 'work:july', 'work:prior-year', 'work:unknown', 'work:missing'],
  dates: ['2026-01-01', '2026-08-31', '2026-08-20', '2026-08-02', '2026-07-01', '2025-12-31', '2027-01-01', ''],
  date_precisions: ['year', 'month', 'day', 'day', 'month', 'day', 'unknown', 'unknown'],
}
const positions = datedLookup.work_ids.map((_, index) => index)

test('latest order respects known periods without treating placeholders as exact publication days', () => {
  assert.deepEqual(orderSearchPositions(positions, datedLookup, 'newest', true), [2, 3, 1, 4, 0, 5, 7, 6])
  assert.deepEqual(orderSearchPositions(positions, datedLookup, 'auto', false), [2, 3, 1, 4, 0, 5, 7, 6])
  assert.deepEqual(positions, [0, 1, 2, 3, 4, 5, 6, 7])
})

test('oldest order still leaves unknown dates last and only orders a year within its known period', () => {
  assert.deepEqual(orderSearchPositions(positions, datedLookup, 'oldest', false), [5, 4, 3, 2, 1, 0, 7, 6])
})

test('default keyword search preserves Pagefind relevance order across pagination', () => {
  const relevant = [5, 3, 7, 2, 1]
  const sorted = orderSearchPositions(relevant, datedLookup, 'auto', true)
  assert.deepEqual(sorted, relevant)
  assert.notEqual(sorted, relevant)
  assert.deepEqual(sorted.slice(2, 4), [7, 2])
})

test('equal dates use stable identities, malformed dates remain unknown, month precision ignores placeholder days', () => {
  assert.ok(compareResearchDates('2026-08-01', 'day', 'work:a', '2026-08-01', 'day', 'work:b') < 0)
  assert.ok(compareResearchDates('2026-02-30', 'day', 'work:a', '2026-02-28', 'day', 'work:b') > 0)
  assert.ok(compareResearchDates('2026-08-31', 'month', 'work:a', '2026-08-01', 'day', 'work:b') > 0)
  assert.equal(compareResearchDates('2026-08-31', 'month', 'work:a', '2026-08-01', 'month', 'work:a'), 0)
})

test('slow work details do not delay URL search, suppress filter changes, or restore an obsolete page', async () => {
  let state = { work: 'work:slow', page: 5 }, restoring = false, invalidations = 0, finishSlow
  const searches = [], works = []
  const restorer = createSearchRestorer({
    invalidateSearch: () => { invalidations++ }, readState: () => ({ ...state }), flush: async () => {},
    setRestoring: value => { restoring = value },
    restoreWork: work => { works.push(work); return work === 'work:slow' ? new Promise(resolve => { finishSlow = resolve }) : Promise.resolve() },
    search: async page => { searches.push(page) },
  })
  const first = restorer.restore()
  await Promise.resolve()
  assert.deepEqual(searches, [5])
  assert.equal(restoring, false)
  state = { work: 'work:fast', page: 2 }
  await restorer.restore()
  finishSlow()
  await first
  assert.deepEqual(searches, [5, 2])
  assert.deepEqual(works, ['work:slow', 'work:fast'])
  assert.equal(invalidations, 2)
})

test('rapid history changes and unmount invalidate queued restores before any network work', async () => {
  let state = { work: 'work:old', page: 5 }, restoring = false
  const flushes = [], searches = [], works = []
  const restorer = createSearchRestorer({
    invalidateSearch: () => {}, readState: () => ({ ...state }),
    flush: () => new Promise(resolve => flushes.push(resolve)), setRestoring: value => { restoring = value },
    restoreWork: async work => { works.push(work) }, search: async page => { searches.push(page) },
  })
  const first = restorer.restore()
  state = { work: 'work:current', page: 2 }
  const second = restorer.restore()
  flushes[0]()
  await first
  assert.equal(restoring, true)
  assert.deepEqual(searches, [])
  flushes[1]()
  await second
  assert.deepEqual(searches, [2])
  assert.deepEqual(works, ['work:current'])
  const unmounted = restorer.restore()
  restorer.cancel()
  flushes[2]()
  await unmounted
  assert.equal(restoring, false)
  assert.deepEqual(searches, [2])
})
