import test from 'node:test'
import assert from 'node:assert/strict'
import * as pagefind from 'pagefind'
import { normalizeSearchBoundaries, searchText } from '../docs/.vitepress/theme/lib/search-text.mjs'
import { defaultFilters, searchOptions } from '../docs/.vitepress/theme/lib/catalog-search.ts'
import { workSearchRecord } from '../scripts/lib/search-records.mjs'

test('dotted numeric chains are distinct, idempotent derived tokens, not metadata edits', () => {
  assert.equal(searchText('GEN-1.5 59%', true), 'GEN zzqnumx1x5q 59%')
  assert.equal(searchText('GEN 1.5', true), 'GEN zzqnumx1x5q')
  assert.notEqual(searchText('1.5'), searchText('15'))
  assert.notEqual(searchText('1.5'), searchText('1.52'))
  assert.notEqual(searchText('1.5.2'), searchText('1.52'))
  assert.notEqual(searchText('0.5'), searchText('0.50'))
  assert.equal(searchText('１．５'), searchText('1.5'))
  assert.equal(searchText('world model.'), 'world model.')
  assert.equal(searchText('π0.5 control'), 'π zzqnumx0x5q control')
  assert.equal(searchText('1.5ms'), 'zzqnumx1x5q ms')
  assert.equal(searchText(searchText('GEN-1.5')), searchText('GEN-1.5'))
  assert.equal(normalizeSearchBoundaries('3D-FixUp'), '3D FixUp')
  const work = { work_id: 'work:decimal', title: 'GEN-1.5', abstract: 'A 1.5-point measurement.', relevance: { status: 'included' } }
  const before = structuredClone(work)
  const record = workSearchRecord(work)
  assert.deepEqual(work, before)
  assert.equal(record.meta.title, 'GEN-1.5')
  assert.match(record.content, /zzqnumx1x5q/)
})

test('DOI, arXiv, URLs and standalone pi identities bypass decimal text encoding', () => {
  for (const [query, key, value] of [
    ['https://doi.org/10.1234/radar.1.5', 'identifier', '10.1234/radar.1.5'],
    ['arxiv:2608.26103v1', 'identifier', '2608.26103'],
    ['https://example.test/model/1.5', 'source_url', 'https://example.test/model/1.5'],
    ['π0.5', 'identity', 'model:pi0.5'], ['pi0.50', 'identity', 'model:pi0.50'],
  ]) {
    const result = searchOptions({ ...defaultFilters(), q: query }, [], [])
    assert.equal(result.query, null, query)
    assert.equal(result.filters[key], value, query)
  }
})

for (const language of ['zh', 'en']) test(`native ${language} WASM proves decimals and every fixture handle identity`, async () => {
  const make = (id, title, abstract = '') => ({ work_id: id, title, abstract, relevance: { status: 'included' }, directions: [], questions: [] })
  const fixtures = [
    make('work:gen', 'GEN-1.5', '59% robot result 世界模型'),
    make('work:integer', 'GEN-15', '59% robot result'),
    make('work:adapt', 'Adapt3R', 'generalization 15 59% robot result'),
    make('work:sentence', 'World model.', 'ordinary sentence.'),
    make('work:version', 'Version 1.5.2', 'versioned release'),
    make('work:measurement152', 'Measurement 1.52', 'a different value'),
    make('work:pi05', 'π0.5 control', 'robot control'),
    make('work:pi050', 'π0.50 control', 'robot control'),
    make('work:pi07', 'π0.7 control', 'robot control'),
    make('work:pi05tex', '$π_{0.5}$ force', 'robot force'),
    make('work:radar', 'Radar sensors', 'mmWave sensing'),
    make('work:decimal-word', 'Decimal arithmetic', 'numeric precision'),
  ]
  const { index, errors } = await pagefind.createIndex({ forceLanguage: language, includeCharacters: 'π' })
  assert.deepEqual(errors, [])
  let files
  try {
    // Submit asynchronously, just as the real builder does. All identities are
    // checked below, not merely every thousandth ordinal or nonempty results.
    const writes = fixtures.map((work, ordinal) => {
      const record = workSearchRecord(work, { ordinal, explicitChinese: true })
      return index.addHTMLFile({ url: record.url, content: record.content })
    })
    for (const response of await Promise.all(writes)) assert.deepEqual(response.errors, [])
    const result = await index.getFiles()
    assert.deepEqual(result.errors, [])
    files = new Map(result.files.map((file) => [file.path, file.content]))
  } finally { await pagefind.close() }
  const originalFetch = globalThis.fetch
  globalThis.fetch = async (input) => {
    const key = String(input).split('/pagefind/').at(-1).split('?')[0]
    assert.ok(files.has(key), `Missing fixture asset: ${key}`)
    return new Response(files.get(key))
  }
  try {
    const engine = await import(`data:text/javascript;base64,${Buffer.from(files.get('pagefind.js')).toString('base64')}#decimal-${language}`)
    await engine.options({ bundlePath: '/pagefind/', language })
    await engine.init()
    const all = await engine.search(null, { sort: { ordinal: 'asc' } })
    assert.equal(all.results.length, fixtures.length)
    const actualByHandle = new Map()
    for (let ordinal = 0; ordinal < all.results.length; ordinal++) {
      const handle = all.results[ordinal]
      const native = await handle.data()
      assert.equal(native.meta.work_id, fixtures[ordinal].work_id)
      assert.equal(native.meta.title, fixtures[ordinal].title)
      actualByHandle.set(handle.id, native.meta.work_id)
    }
    const idsFor = async (q) => {
      const search = searchOptions({ ...defaultFilters(), q, relevance: 'all' }, [], [], language)
      const response = await engine.search(search.query, { filters: search.filters })
      const results = []
      for (const handle of response.results) {
        const native = await handle.data()
        assert.equal(actualByHandle.get(handle.id), native.meta.work_id, `${q}: changed handle identity`)
        results.push(native.meta.work_id)
      }
      return results.sort()
    }
    for (const q of ['GEN-1.5 59%', 'GEN 1.5 59%', 'GEN-1.5', 'GEN 1.5', '1.5', '世界模型1.5']) {
      assert.deepEqual(await idsFor(q), ['work:gen'], q)
    }
    assert.deepEqual(await idsFor('1.52'), ['work:measurement152'])
    assert.deepEqual(await idsFor('1.5.2'), ['work:version'])
    const integer = await idsFor('GEN-15')
    assert.ok(integer.includes('work:integer'))
    assert.ok(!integer.includes('work:gen'))
    // "gen" is ordinary Pagefind prefix search and may match generalization;
    // that legitimate prefix behavior must not turn 1.5 into the integer 15.
    assert.ok(!integer.includes('work:measurement152'))
    for (const q of ['π0.5 control', 'pi0.5 control']) assert.deepEqual(await idsFor(q), ['work:pi05'], q)
    assert.deepEqual(await idsFor('π0.50 control'), ['work:pi050'])
    assert.deepEqual(await idsFor('π0.7 control'), ['work:pi07'])
    assert.deepEqual(await idsFor('$π_{0.5}$ force'), ['work:pi05tex'])
    assert.deepEqual(await idsFor('π0.5'), ['work:pi05', 'work:pi05tex'])
    assert.deepEqual(await idsFor('radar'), ['work:radar'])
    assert.deepEqual(await idsFor('decimal'), ['work:decimal-word'])
    for (const q of ['model', '"world model"', '"world model."']) assert.deepEqual(await idsFor(q), ['work:sentence'], q)
  } finally { globalThis.fetch = originalFetch }
})
