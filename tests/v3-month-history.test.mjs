import test from 'node:test'
import assert from 'node:assert/strict'
import { monthHistoryTarget, monthRequestIsCurrent, resolveMonthFromUrl } from '../docs/.vitepress/theme/lib/month-history.mjs'

const options = { availableMonths: ['2026-06', '2026-07', '2026-08', '2026-09'], defaultMonth: '2026-08' }
const july = 'https://radar.example/project/monthly/?month=2026-07'

test('July to June creates a target entry; selecting the same month does not', () => {
  assert.equal(monthHistoryTarget(july, '2026-06', options), 'https://radar.example/project/monthly/?month=2026-06')
  assert.equal(monthHistoryTarget(july, '2026-07', options), null)
})

test('Back and Forward restore existing entries without pushing or losing forward history', () => {
  const entries = [july]
  const june = monthHistoryTarget(entries[0], '2026-06', options)
  entries.push(june)
  for (const index of [0, 1, 0, 1]) {
    const href = entries[index]
    const month = resolveMonthFromUrl(href, options.availableMonths, options.defaultMonth)
    assert.equal(monthHistoryTarget(href, month, { ...options, source: 'restore' }), null)
  }
  assert.deepEqual(entries, [july, june])
  // Non-user intent cannot push even if completion races a different URL.
  assert.equal(monthHistoryTarget(july, '2026-06', { ...options, source: 'restore' }), null)
  assert.equal(monthHistoryTarget(july, '2026-06', { ...options, source: 'hydrate' }), null)
})

test('absent month resolves to the latest complete month, not the provisional month', () => {
  const bare = 'https://radar.example/project/monthly/?evidence_view=retrospective#findings'
  assert.equal(resolveMonthFromUrl(bare, options.availableMonths, options.defaultMonth), '2026-08')
  assert.equal(monthHistoryTarget(bare, '2026-08', options), null)
  const target = monthHistoryTarget(bare, '2026-07', options)
  assert.equal(new URL(target).searchParams.get('month'), '2026-07')
  assert.equal(resolveMonthFromUrl(bare, options.availableMonths, options.defaultMonth), '2026-08') // Back to the untouched bare entry.
})

test('invalid and unavailable URL months use the same default; invalid targets never push', () => {
  for (const invalid of ['not-a-month', '2026-99', '2023-01', '']) {
    const href = `https://radar.example/monthly/?month=${invalid}`
    assert.equal(resolveMonthFromUrl(href, options.availableMonths, options.defaultMonth), '2026-08')
    assert.equal(monthHistoryTarget(href, '2026-08', options), null)
    assert.equal(new URL(monthHistoryTarget(href, '2026-06', options)).searchParams.get('month'), '2026-06')
  }
  assert.equal(monthHistoryTarget(july, '2026-99', options), null)
})

test('other query values, duplicate parameters, origin, project path and hash survive', () => {
  const href = `${july}&directions=D5&evidence_view=retrospective&q=world%20model&tag=a&tag=b#%E8%AF%81%E6%8D%AE`
  const url = new URL(monthHistoryTarget(href, '2026-06', options))
  assert.equal(url.origin, 'https://radar.example')
  assert.equal(url.pathname, '/project/monthly/')
  assert.equal(url.searchParams.get('directions'), 'D5')
  assert.equal(url.searchParams.get('evidence_view'), 'retrospective')
  assert.equal(url.searchParams.get('q'), 'world model')
  assert.deepEqual(url.searchParams.getAll('tag'), ['a', 'b'])
  assert.equal(url.hash, '#%E8%AF%81%E6%8D%AE')
})

test('a successful entry can retain router history.state unchanged', () => {
  const historyState = { key: 'router-entry', scroll: { left: 0, top: 120 }, userData: ['retained'] }
  const before = structuredClone(historyState)
  const pushes = []
  const history = { state: historyState, pushState(state, title, url) { pushes.push({ state, title, url }) } }
  const target = monthHistoryTarget(july, '2026-06', options)
  if (target) history.pushState(history.state, '', target)
  assert.equal(pushes[0].state, historyState)
  assert.deepEqual(historyState, before)
})

test('stale, unmounted and other-route requests cannot commit snapshot or URL', () => {
  const current = { request: 4, currentRequest: 4, disposed: false, requestPath: '/monthly/', currentPath: '/monthly/' }
  assert.equal(monthRequestIsCurrent(current), true)
  assert.equal(monthRequestIsCurrent({ ...current, currentRequest: 5 }), false)
  assert.equal(monthRequestIsCurrent({ ...current, disposed: true }), false)
  assert.equal(monthRequestIsCurrent({ ...current, currentPath: '/database/' }), false)
  const pushes = []
  for (const state of [{ ...current, currentRequest: 5 }, { ...current, disposed: true }]) {
    if (monthRequestIsCurrent(state)) pushes.push(monthHistoryTarget(july, '2026-06', options))
  }
  assert.deepEqual(pushes, [])
})
