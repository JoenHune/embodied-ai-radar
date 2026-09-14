import test from 'node:test'
import assert from 'node:assert/strict'
import { gzipSync } from 'node:zlib'
import * as pagefind from 'pagefind'
import { SEARCH_TEXT_CONTRACT, normalizeSearchBoundaries, searchText } from '../docs/.vitepress/theme/lib/search-text.mjs'
import { defaultFilters, searchOptions } from '../docs/.vitepress/theme/lib/catalog-search.ts'
import { indexAbstractText, workSearchRecord } from '../scripts/lib/search-records.mjs'

test('the shared contract equates separators with spaces, not invented joined spellings', () => {
  for (const variants of [['cross-embodiment', 'cross_embodiment', 'cross embodiment', 'cross‐embodiment', 'cross‑embodiment'],
    ['3D-FixUp', '3D_FixUp', '3D FixUp'], ['vision-language-action', 'vision_language_action', 'vision language action'],
    ['sim-to-real', 'sim_to_real', 'sim to real'], ['中文混写3D-FixUp与视觉_语言_动作', '中文混写3D FixUp与视觉 语言 动作']]) {
    const expected = searchText(variants[0], true)
    for (const value of variants) assert.equal(searchText(value, true), expected, value)
  }
  assert.notEqual(searchText('cross-embodiment'), searchText('crossembodiment'))
  assert.notEqual(searchText('3D-FixUp'), searchText('3DFixUp'))
  assert.equal(SEARCH_TEXT_CONTRACT.joined_spelling, 'not_implicitly_equivalent_unless_present_in_source_or_explicit_alias')
})

test('deduplication happens after boundary normalization and preserves complete alphanumeric atoms', () => {
  assert.equal(searchText(indexAbstractText('Cross-embodiment', ['Cross'])), 'embodiment')
  assert.ok(!indexAbstractText('Cross-embodiment', ['Cross']).includes('-embodiment'))
  assert.equal(searchText(indexAbstractText('3D-FixUp', ['D'])), '3D FixUp')
  assert.equal(searchText(indexAbstractText('RGBD4_pose', ['RGBD'])), 'RGBD4 pose')
  assert.equal(indexAbstractText("robot's r.m.s. Déjà", ['robot', 's', 'r', 'm', 'D']), "robot's r.m.s. Déjà")
  const source = 'Cross-embodiment与3D-FixUp：视觉_语言_动作。'
  const indexed = indexAbstractText(source, ['Cross', 'D', 'Fix'])
  assert.equal(indexed.replace(/[^\p{Script=Han}]/gu, ''), source.replace(/[^\p{Script=Han}]/gu, ''))
})

test('DOI, URL, work IDs and pi identity bypass full-text separator normalization', () => {
  const cases = [
    ['https://doi.org/10.1234/model-v2_test', 'identifier', '10.1234/model-v2_test'],
    ['10.1234/model-v2_test', 'identifier', '10.1234/model-v2_test'],
    ['https://github.com/lab/model-v2_test', 'source_url', 'https://github.com/lab/model-v2_test'],
    ['work:compound-example_v2', 'identifier', 'work:compound-example_v2'],
    ['pi-0.5', 'identity', 'model:pi0.5'], ['$π_{0.5}$', 'identity', 'model:pi0.5'],
  ]
  for (const [query, field, value] of cases) {
    const result = searchOptions({ ...defaultFilters(), q: query, relevance: 'all' }, [], [])
    assert.equal(result.query, null, query)
    assert.equal(result.filters[field], value, query)
  }
})

const fixtures = [
  { work_id: 'work:cross', title: 'Cross', abstract: 'Cross-embodiment transfer with cross_embodiment examples. 中文跨本体-策略。' },
  { work_id: 'work:fixup', title: '3D-FixUp: Lightweight Pose Refinement', abstract: '3D-FixUp and 3D_FixUp evaluate geometry.' },
  { work_id: 'work:vla', title: 'Vision-language-action in a shared system', abstract: 'A vision_language_action policy is described.' },
  { work_id: 'work:sim', title: 'Simulation Transfer', abstract: 'Sim-to-real transfer uses sim_to_real control.' },
  { work_id: 'work:pi', title: '$π_{0.5}$: Cross-embodiment VLA', abstract: 'This policy is tested.', identifiers: { doi: '10.1234/model-v2_test' }, repositories: ['https://github.com/lab/model-v2_test'] },
  { work_id: 'work:mixed', title: '中文混写3D-FixUp与视觉_语言_动作', abstract: "Mixed Unicode Déjà-vu and robot's r.m.s. keep their atoms." },
  { work_id: 'work:digit', title: 'D', abstract: '3D-FixUp remains an atomic model name.' },
].map((work) => ({ ...work, relevance: { status: 'included' }, directions: [], questions: [] }))

for (const language of ['zh', 'en']) test(`real ${language} WASM: compound and spaced queries, original titles, Chinese and identities remain retrievable`, async (t) => {
  const before = structuredClone(fixtures)
  const { index, errors } = await pagefind.createIndex({ forceLanguage: language, includeCharacters: 'π' })
  assert.deepEqual(errors, [])
  const records = fixtures.map((work, ordinal) => workSearchRecord(work, { explicitChinese: true, ordinal }))
  const originalFetch = globalThis.fetch
  try {
    for (const [position, record] of records.entries()) {
      assert.equal(record.meta.title, fixtures[position].title)
      assert.equal(record.excerpt, fixtures[position].abstract)
      assert.deepEqual((await index.addHTMLFile({ url: record.url, content: record.content })).errors, [])
    }
    const built = await index.getFiles()
    assert.deepEqual(built.errors, [])
    const files = new Map(built.files.map((file) => [file.path, file.content]))
    globalThis.fetch = async (input) => new Response(files.get(String(input).split('/pagefind/').at(-1).split('?')[0]))
    const engine = await import(`data:text/javascript;base64,${Buffer.from(files.get('pagefind.js')).toString('base64')}#compounds-${language}`)
    await engine.options({ bundlePath: '/pagefind/', language })
    await engine.init()
    const idsFor = async (query) => {
      const configured = searchOptions({ ...defaultFilters(), q: query, relevance: 'all' }, [], [], language)
      const result = await engine.search(configured.query, { filters: configured.filters })
      return Promise.all(result.results.map(async (row) => (await row.data()).meta.work_id))
    }
    for (const variants of [['cross-embodiment', 'cross embodiment', 'cross_embodiment'], ['3D-FixUp', '3D FixUp', '3D_FixUp'],
      ['vision-language-action', 'vision language action', 'vision_language_action'], ['sim-to-real', 'sim to real', 'sim_to_real']]) {
      const baseline = (await idsFor(variants[0])).sort()
      assert.ok(baseline.length > 0, variants[0])
      for (const variant of variants.slice(1)) assert.deepEqual((await idsFor(variant)).sort(), baseline, variant)
    }
    assert.ok((await idsFor('cross-embodiment')).includes('work:cross'), 'Cross in the title plus embodiment in the abstract must match')
    assert.ok((await idsFor('3D-FixUp')).includes('work:digit'), 'Title D must not remove D from the 3D atom')
    // A pasted full original title follows ordinary full-text query semantics.
    // Character-exact punctuation inside quoted phrases is not this contract.
    for (const fixture of fixtures) assert.ok((await idsFor(fixture.title)).includes(fixture.work_id), fixture.title)
    assert.ok((await idsFor('跨本体-策略')).includes('work:cross'))
    assert.ok((await idsFor('中文混写3D_FixUp与视觉-语言-动作')).includes('work:mixed'))
    for (const query of ['π0', 'pi0', 'π0.5', 'pi-0.5', '$π_{0.5}$', '10.1234/model-v2_test', 'https://doi.org/10.1234/model-v2_test', 'https://github.com/lab/model-v2_test']) assert.deepEqual(await idsFor(query), ['work:pi'], query)
    assert.equal((await engine.search(null)).results.length, fixtures.length)
    assert.deepEqual(fixtures, before)
    t.diagnostic(JSON.stringify({ fixture_records: fixtures.length,
      preserved_title_characters: fixtures.reduce((sum, row) => sum + [...row.title].length, 0),
      preserved_abstract_characters: fixtures.reduce((sum, row) => sum + [...row.abstract].length, 0),
      fixture_index_gzip_bytes: built.files.filter((file) => file.path.startsWith('index/')).reduce((sum, file) => sum + gzipSync(file.content).length, 0),
      scope: 'small synthetic fixture, not production size or a claim of legacy joined-spelling equivalence' }))
  } finally {
    globalThis.fetch = originalFetch
    await pagefind.close()
  }
})
