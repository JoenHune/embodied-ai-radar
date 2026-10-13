import test from 'node:test'
import assert from 'node:assert/strict'
import * as pagefind from 'pagefind'
import { defaultFilters, filterCatalog, readSearchUrl, searchOptions, writeSearchUrl } from '../docs/.vitepress/theme/lib/catalog-search.ts'
import { cooccurrenceParams, evidenceSearchParams } from '../docs/.vitepress/theme/lib/evidence-links.mjs'
import { workSearchRecord } from '../scripts/lib/search-records.mjs'

const fixtures = [
  { work_id: 'work:d1-only', directions: ['D1'] },
  { work_id: 'work:d2-only', directions: ['D2'] },
  { work_id: 'work:both', directions: ['D1', 'D2'] },
  { work_id: 'work:both-older', directions: ['D1', 'D2'], first_public_date: '2026-07-10' },
  { work_id: 'work:both-candidate', directions: ['D1', 'D2'], relevance: { status: 'candidate' } },
  { work_id: 'work:other', directions: ['D3'] },
].map((work) => ({ title: `Robot comparison ${work.work_id}`, abstract: 'Commonneedle findings.', first_public_date: '2026-08-10', relevance: { status: 'included' }, ...work }))

const linkParams = (mode) => {
  const params = cooccurrenceParams('D1', 'D2', ['2026-08'])
  if (mode) params.direction_match = mode
  else delete params.direction_match
  return evidenceSearchParams([], {}, params)
}
const configuredSearch = (mode, extra = {}) => searchOptions({ ...readSearchUrl(linkParams(mode)).filters, ...extra }, ['2026-07', '2026-08'], [])
const records = fixtures.map((work, ordinal) => workSearchRecord(work, { explicitChinese: true, ordinal }))
const postings = {}
for (const [position, record] of records.entries()) for (const [field, values] of Object.entries(record.filters)) for (const value of values) {
  postings[field] ||= {}
  ;(postings[field][value] ||= []).push(position)
}
const lookup = { ids: [], work_ids: fixtures.map((work) => work.work_id), dates: fixtures.map((work) => work.first_public_date), postings }
const workIds = (positions) => [...positions].map((position) => lookup.work_ids[position]).sort()

test('cooccurrence URL preserves explicit intersection through restore and pagination', () => {
  const parsed = readSearchUrl(linkParams('all'))
  assert.equal(parsed.filters.directionMatch, 'all')
  const url = writeSearchUrl(new URL('https://example.test/database/'), parsed.filters, 3, 'work:both')
  assert.equal(url.searchParams.get('direction_match'), 'all')
  assert.equal(url.searchParams.get('from'), '2026-08')
  assert.equal(url.searchParams.get('to'), '2026-08')
  assert.deepEqual(readSearchUrl(url.searchParams), { filters: parsed.filters, page: 3, work: 'work:both' })
})

test('cooccurrence links preserve the full analysis window instead of silently browsing all history', () => {
  const months = ['2026-09', '2025-09', '2026-08']
  const params = cooccurrenceParams('D4', 'D8', months)
  assert.deepEqual(params, { directions: 'D4,D8', direction_match: 'all', from: '2025-09', to: '2026-09' })
  assert.deepEqual(months, ['2026-09', '2025-09', '2026-08'])
  const restored = readSearchUrl(evidenceSearchParams([], {}, params)).filters
  assert.equal(restored.directionMatch, 'all')
  assert.equal(restored.from, '2025-09')
  assert.equal(restored.to, '2026-09')
  assert.throws(() => cooccurrenceParams('D4', 'D8', []), /analysis month window/)
})

test('ordinary direction multiselect remains a union and invalid or empty modes normalize to any', () => {
  assert.equal(defaultFilters().directionMatch, 'any')
  for (const mode of [undefined, 'any', 'invalid', 'ALL']) {
    const { filters } = readSearchUrl(linkParams(mode))
    assert.equal(filters.directionMatch, 'any')
    assert.deepEqual(configuredSearch(mode).filters.direction, { any: ['D1', 'D2'] })
    assert.deepEqual(workIds(filterCatalog(lookup, configuredSearch(mode).filters)), ['work:both', 'work:d1-only', 'work:d2-only'])
    const url = writeSearchUrl(new URL('https://example.test/database/?direction_match=all'), filters, 1, '')
    assert.equal(url.searchParams.has('direction_match'), false)
  }
  assert.equal(readSearchUrl(new URLSearchParams('direction_match=all')).filters.directionMatch, 'any')
  const cleared = { ...readSearchUrl(linkParams('all')).filters, direction: '' }
  assert.equal(writeSearchUrl(new URL('https://example.test/database/?direction_match=all'), cleared, 1, '').searchParams.has('direction_match'), false)
})

test('intersection requires every direction while retaining date and relevance constraints', () => {
  const search = configuredSearch('all')
  assert.deepEqual(search.filters.direction, { all: ['D1', 'D2'] })
  assert.deepEqual(workIds(filterCatalog(lookup, search.filters)), ['work:both'])
  assert.deepEqual(workIds(filterCatalog(lookup, configuredSearch('all', { relevance: 'all' }).filters)), ['work:both', 'work:both-candidate'])
  assert.deepEqual(workIds(filterCatalog(lookup, configuredSearch('all', { direction: 'D1, D2,D1' }).filters)), ['work:both'])
  assert.deepEqual(workIds(filterCatalog(lookup, configuredSearch('all', { direction: 'D1,missing' }).filters)), [])
  assert.deepEqual(workIds(filterCatalog(lookup, configuredSearch('all', { direction: 'missing,D1' }).filters)), [])
})

for (const language of ['zh', 'en']) test(`real ${language} index and deployed lookup agree on direction intersections`, async () => {
  const { index, errors } = await pagefind.createIndex({ forceLanguage: language })
  assert.deepEqual(errors, [])
  const originalFetch = globalThis.fetch
  try {
    for (const record of records) assert.deepEqual((await index.addHTMLFile({ url: record.url, content: record.content })).errors, [])
    const built = await index.getFiles()
    assert.deepEqual(built.errors, [])
    const files = new Map(built.files.map((file) => [file.path, file.content]))
    globalThis.fetch = async (input) => {
      const key = String(input).split('/pagefind/').at(-1).split('?')[0]
      assert.ok(files.has(key), `Unexpected missing index asset: ${key}`)
      return new Response(files.get(key))
    }
    const engineSource = `data:text/javascript;base64,${Buffer.from(files.get('pagefind.js')).toString('base64')}`
    const engine = await import(`${engineSource}#direction-${language}`)
    await engine.options({ bundlePath: '/pagefind/', language })
    await engine.init()
    for (const [mode, expected] of [[undefined, ['work:both', 'work:d1-only', 'work:d2-only']], ['all', ['work:both']]]) {
      for (const q of ['', 'Commonneedle']) {
        const search = configuredSearch(mode, { q })
        const response = await engine.search(search.query, { filters: search.filters })
        const actual = await Promise.all(response.results.map(async (row) => (await row.data()).meta.work_id))
        assert.deepEqual(actual.sort(), expected, `${mode || 'any'}: ${q || 'browse'}`)
      }
    }
    const ordered = await engine.search(null, { sort: { ordinal: 'asc' } })
    const deployedLookup = { ...lookup, ids: ordered.results.map((row) => row.id) }
    // Production searches full text without native filter/fragment assets, then applies the compact lookup.
    for (const key of files.keys()) if (key.startsWith('filter/') || key.startsWith('fragment/')) files.delete(key)
    const deployed = await import(`${engineSource}#direction-deployed-${language}`)
    await deployed.options({ bundlePath: '/pagefind/', language })
    await deployed.init()
    for (const [mode, expected] of [[undefined, ['work:both', 'work:d1-only', 'work:d2-only']], ['all', ['work:both']]]) {
      const search = configuredSearch(mode, { q: 'Commonneedle' })
      const allowed = filterCatalog(deployedLookup, search.filters)
      const response = await deployed.search(search.query)
      const positions = response.results.map((row) => deployedLookup.ids.indexOf(row.id)).filter((position) => allowed.has(position))
      assert.deepEqual(workIds(positions), expected, mode || 'any')
    }
  } finally {
    globalThis.fetch = originalFetch
    await pagefind.close()
  }
})
