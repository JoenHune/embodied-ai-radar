import test from 'node:test'
import assert from 'node:assert/strict'
import * as pagefind from 'pagefind'
import { identityAliases, indexAbstractText, publicationTuple, workSearchRecord } from '../scripts/lib/search-records.mjs'
import { defaultFilters, filterCatalog, loadResultPage, readSearchUrl, searchOptions, writeSearchUrl } from '../docs/.vitepress/theme/lib/catalog-search.ts'
import { piModelNames, piModelQuery, searchText } from '../docs/.vitepress/theme/lib/search-text.mjs'

test('imprecise dates do not invent January distribution or pass open-ended date filters', () => {
  const work = { work_id: 'title:undated', title: 'Robot research', first_public_date: '2026-01-01', first_public_date_precision: 'year' }
  assert.deepEqual(workSearchRecord(work).filters.month, ['unknown'])
  assert.equal(workSearchRecord(work).meta.date_precision, 'year')
  const selected = searchOptions({ ...defaultFilters(), from: '2026-01' }, ['unknown', '2026-01', '2026-08'], [])
  assert.deepEqual(selected.filters.month, { any: ['2026-01', '2026-08'] })
  assert.deepEqual(workSearchRecord({ ...work, first_public_date_precision: 'month' }).filters.month, ['2026-01'])
})
test('reviewed title changes remain searchable under one canonical identity', () => {
  const record = workSearchRecord({ work_id: 'arxiv:2502.01465', title: 'Embrace Collisions', title_aliases: ['Embrace Contacts'], aliases: ['title:older-proceedings-id'] })
  assert.match(record.content, /Embrace Contacts/)
  assert.equal(record.meta.work_id, 'arxiv:2502.01465')
  assert.ok(record.filters.work_id.includes('title:older-proceedings-id'))
})

test('canonical organization labels display once per group while all aliases remain searchable', () => {
  const record = workSearchRecord({ work_id: 'work:dreamdojo-fixture', title: 'DreamDojo fixture' }, {
    organizationIds: ['org:rpl', 'org:gear', 'org:gear'],
    organizationDisplayNames: ['UT Austin Robot Perception and Learning Lab', 'NVIDIA GEAR', 'NVIDIA GEAR'],
    organizationNames: ['UT Austin Robot Perception and Learning Lab UT Austin RPL UT Austin RPL Lab', 'NVIDIA GEAR NVIDIA GEAR GEAR GearAliasNeedle', 'NVIDIA GEAR GEAR'],
  })
  assert.equal(record.meta.organizations, 'UT Austin Robot Perception and Learning Lab · NVIDIA GEAR')
  for (const alias of ['UT Austin RPL', 'UT Austin RPL Lab', 'GEAR', 'GearAliasNeedle']) assert.ok(record.content.includes(alias), alias)
})

test('unknown venues remain filterable but never appear as display placeholders', () => {
  const record = workSearchRecord({ work_id: 'work:venues', title: 'Venue labels' }, { manifestations: [{ kind: 'project' }, { kind: 'preprint', venue: 'arXiv' }] })
  assert.equal(record.meta.venues, 'arXiv')
  assert.deepEqual(record.filters.venue, ['unknown', 'arXiv'])
  assert.ok(record.filters.publication.some((tuple) => JSON.parse(tuple)[0] === 'unknown'))
  assert.equal(workSearchRecord({ work_id: 'work:unknown', title: 'Unknown venue' }, { manifestations: [{ kind: 'project' }] }).meta.venues, '')
})

test('full result set remains reachable after the old 500-result boundary, loading only one page', async () => {
  const loaded = []
  const handles = Array.from({ length: 1203 }, (_, id) => ({ id: String(id), data: async () => { loaded.push(id); return { meta: { record_type: 'work', work_id: `work:${id}` } } } }))
  const first = await loadResultPage(handles, 1)
  assert.equal(first.total, 1203)
  assert.equal(first.pageCount, 61)
  assert.deepEqual(loaded, Array.from({ length: 20 }, (_, id) => id))
  const beyond = await loadResultPage(handles, 26)
  assert.equal(beyond.rows[0].meta.work_id, 'work:500')
  const last = await loadResultPage(handles, 100)
  assert.equal(last.page, 61)
  assert.equal(last.rows.length, 3)
  assert.equal(last.rows.at(-1).meta.work_id, 'work:1202')
})

test('non-work records and failed fragments cannot look like successful search results', async () => {
  await assert.rejects(loadResultPage([{ id: 'page', data: async () => ({ meta: { title: 'Home' } }) }], 1), /非研究记录/)
  await assert.rejects(loadResultPage([{ id: 'failed', data: async () => { throw new Error('offline') } }], 1), /offline/)
  assert.equal((await loadResultPage([], 1)).total, 0)
})

test('URLs roundtrip all facets, page and exact evidence IDs without losing original query', () => {
  const filters = { ...defaultFilters(), q: 'π0 世界模型', direction: 'D1,D3', organization: 'org:physical-intelligence', venue: 'CoRL', year: '2026', track: 'main', acceptance: 'accepted', publicationStatus: 'accepted', ids: 'arxiv:2501.00123,doi:10.123/example', relevance: 'all', peerReviewed: true }
  const url = writeSearchUrl(new URL('https://example.test/database/'), filters, 26, 'arxiv:2501.00123')
  assert.deepEqual(readSearchUrl(url.searchParams), { filters, page: 26, work: 'arxiv:2501.00123' })
  assert.equal(readSearchUrl(new URLSearchParams('ids=work:a')).filters.relevance, 'all')
  assert.equal(readSearchUrl(new URLSearchParams('page=-1')).page, 1)
  const includedIds = { ...filters, relevance: 'included' }
  assert.equal(readSearchUrl(writeSearchUrl(url, includedIds, 1, '').searchParams).filters.relevance, 'included')
})

test('publication facets match one version, avoiding CoRL 2025 + ICRA 2026 false match', () => {
  const publications = [JSON.stringify(['CoRL', '2025', 'main', 'accepted', 'published']), JSON.stringify(['ICRA', '2026', 'main', 'accepted', 'published'])]
  assert.equal(searchOptions({ ...defaultFilters(), venue: 'CoRL', year: '2026' }, [], publications).empty, true)
  const positive = searchOptions({ ...defaultFilters(), venue: 'CoRL', year: '2025', track: 'main' }, [], publications)
  assert.deepEqual(positive.filters.publication, { any: [publications[0]] })
  assert.deepEqual(searchOptions({ ...defaultFilters(), ids: 'work:a,work:b', relevance: 'all' }, [], []).filters.work_id, { any: ['work:a', 'work:b'] })
})

test('empty query browses full index; impossible time windows are explicit empty sets', () => {
  assert.equal(searchOptions(defaultFilters(), ['2026-08'], []).query, null)
  assert.equal(searchOptions({ ...defaultFilters(), from: '2026-09', to: '2026-08' }, ['2026-08'], []).empty, true)
  assert.equal(searchOptions({ ...defaultFilters(), from: '2020-01', to: '2020-02' }, ['2026-08'], []).empty, true)
  const exact = searchOptions({ ...defaultFilters(), q: 'work:c', ids: 'work:a,work:b' }, [], [])
  assert.deepEqual(exact.filters.work_id, { any: ['work:a', 'work:b'] })
  assert.equal(exact.filters.identifier, 'work:c')
})

test('PI and π0 aliases require organization or model identity, never a whole D category', () => {
  assert.deepEqual(identityAliases({ title: 'Generic VLA foundation model', directions: ['D1'], abstract: 'We compare with pi0.' }), [])
  assert.deepEqual(identityAliases({ title: 'Physical Intelligence research', directions: ['D1'] }, ['org:mpi-is-physical-intelligence']), [])
  assert.ok(identityAliases({ title: 'π0: A Vision-Language-Action Flow Model' }).includes('pi0'))
  assert.ok(identityAliases({ title: 'New model' }, ['org:physical-intelligence']).includes('PI'))
})

test('π model identities normalize actual arXiv TeX titles and preserve exact decimal versions', () => {
  const originalTitle = '$π_0$: A Vision-Language-Action Flow Model for General Robot Control'
  const openWorldTitle = '$π_{0.5}$: a Vision-Language-Action Model with Open-World Generalization'
  assert.deepEqual(piModelNames(originalTitle), ['pi0'])
  assert.deepEqual(piModelNames(openWorldTitle), ['pi0.5'])
  for (const title of [String.raw`$\pi_{0.5}$: Model`, 'π_0.5: Model', 'π₀.₅: Model', 'pi-0.5: Model']) assert.deepEqual(piModelNames(title), ['pi0.5'])
  for (const query of ['π0.5', 'pi0.5', '$π_{0.5}$', String.raw`\(\pi_{0.5}\)`]) assert.equal(piModelQuery(query), 'pi0.5')
  assert.equal(piModelQuery('π0'), 'pi0')
  for (const query of ['PI', 'pi0.5x', 'scipi0', 'pi0.5 policy']) assert.equal(piModelQuery(query), null)
  for (const title of ['pirate robot', 'scipi0', 'pi0.5x']) assert.deepEqual(piModelNames(title), [])
  const work = { work_id: 'arxiv:2504.16054', title: openWorldTitle, relevance: { status: 'included' }, directions: ['D1'] }
  const record = workSearchRecord(work)
  assert.deepEqual(record.filters.identity, ['model:pi0', 'model:pi0.5'])
  assert.ok(!record.filters.identity.includes('company:physical-intelligence'))
  assert.ok(!record.filters.identity.includes('model:pi0.7'))
  assert.equal(searchOptions({ ...defaultFilters(), q: 'π0.5' }, [], []).filters.identity, 'model:pi0.5')
})

test('work record indexes original abstract, assets and identifiers with real field weights', () => {
  const work = { work_id: 'arxiv:2501.12345', title: '<Robot> & force', abstract: 'Cross-embodiment transfer with uniqueabstractterm', authors: ['Ada Robot'], identifiers: { doi: '10.1234/robot' }, directions: ['D3'], questions: ['Q10'], repositories: ['https://github.com/example/uniquecodename'], relevance: { status: 'excluded' } }
  const record = workSearchRecord(work, { manifestations: [{ venue: 'CoRL', year: 2026, kind: 'conference', url: 'https://example.org/technical-report', track: 'main', status: 'accepted' }] })
  for (const value of ['uniqueabstractterm', 'uniquecodename', '10.1234/robot', 'Ada Robot', '世界 模型', 'technical-report']) assert.ok(record.content.includes(value), value)
  assert.ok(record.content.includes('data-pagefind-weight="8"'))
  assert.ok(record.content.includes('&lt;Robot&gt; &amp; force'))
  assert.deepEqual(record.filters.relevance, ['excluded'])
  assert.equal(publicationTuple({ status: 'official_program_only', kind: 'conference' })[3], 'unknown')
})

test('compact abstract postings preserve every distinct English word and all non-English text', () => {
  const text = 'Robot action learning. ROBOT action transfer with cross-embodiment; safety is not solved. 世界模型的机器人研究。'
  const indexed = indexAbstractText(text)
  const vocabulary = (value) => [...new Set(value.match(/[A-Za-z][A-Za-z0-9]*/g).map((word) => word.toLowerCase()))].sort()
  assert.deepEqual(vocabulary(indexed), vocabulary(text))
  assert.ok(indexed.includes('not solved'))
  assert.ok(indexed.includes('世界模型的机器人研究'))
})

test('cross-field abstract compaction preserves every original English word, Chinese text and complete title/author phrases', () => {
  const work = { work_id: 'work:cross-field', title: 'Preserved Title Phrase', title_aliases: ['Preserved Historical Title'],
    authors: ['Alice Surname'], author_aliases: ['Earlier Author'], project_series: 'Projectneedle', model_name: 'Modelneedle',
    abstract: 'Preserved Title Phrase. Alice Surname, Earlier Author, Projectneedle and Modelneedle use Facetneedle, Assetneedle and Venueneedle. Uniqueabstractneedle remains. 世界模型与灵巧操作。',
    facets: { methods: ['Facetneedle'] }, repositories: ['https://github.com/lab/Assetneedle'], directions: ['D3'] }
  const record = workSearchRecord(work, { organizationNames: ['Organizationneedle'], manifestations: [{ kind: 'preprint', title: 'Publication Title Phrase', venue: 'Venueneedle' }] })
  const paragraphs = [...record.content.matchAll(/<p data-pagefind-weight="([\d.]+)"[^>]*>([\s\S]*?)<\/p>/g)]
  const abstractField = paragraphs.find((row) => row[1] === '1')[2].split('\n')[0]
  for (const word of ['Preserved', 'Title', 'Phrase', 'Alice', 'Surname', 'Earlier', 'Author', 'Projectneedle', 'Modelneedle', 'Facetneedle', 'Assetneedle', 'Venueneedle']) assert.ok(!abstractField.includes(word), word)
  for (const phrase of ['Preserved Title Phrase', 'Preserved Historical Title', 'Alice Surname', 'Earlier Author', 'Publication Title Phrase']) assert.ok(record.content.includes(phrase), phrase)
  assert.match(abstractField, /Uniqueabstractneedle/)
  assert.match(abstractField, /世界 模型/)
  assert.match(abstractField, /灵巧 操作/)
  const englishWords = (value) => new Set((value.match(/[A-Za-z][A-Za-z0-9]*/g) || []).map((word) => word.toLowerCase()))
  const original = indexAbstractText(work.abstract)
  const present = englishWords(paragraphs.map((row) => row[2]).join(' '))
  // Common English stopwords are already omitted by the established search
  // transform, independently of this duplicate-elimination change.
  for (const word of englishWords(searchText(original))) assert.ok(present.has(word), word)
  assert.match(paragraphs.find((row) => row[1] === '8')[2], /Preserved Title Phrase/)
})

test('taxonomy aliases do not downgrade existing English abstract terms or remove Chinese', () => {
  const record = workSearchRecord({ work_id: 'work:weight', title: 'Controlled forecasting', abstract: 'A world model enables control.', directions: ['D3'] })
  const weightOne = record.content.match(/<p data-pagefind-weight="1"[^>]*>([\s\S]*?)<\/p>/)[1]
  const weightHalf = record.content.match(/<p data-pagefind-weight="0.5"[^>]*>([\s\S]*?)<\/p>/)[1]
  assert.match(weightOne, /world model/)
  assert.doesNotMatch(weightHalf, /world model/)
  assert.match(weightHalf, /世界 模型/)
})

for (const language of ['zh', 'en']) test(`real Pagefind ${language}/WASM index: multilingual queries, precise aliases, all statuses, correlated venue facets and full pagination`, async () => {
  const { index, errors } = await pagefind.createIndex({ forceLanguage: language, includeCharacters: 'π' })
  assert.deepEqual(errors, [])
  const makeWork = (id, fields = {}) => ({ work_id: id, title: `Robot fixture ${id}`, abstract: 'Robot experimental results.', relevance: { status: 'included' }, directions: [], questions: [], first_public_date: '2026-08-01', ...fields })
  const fixtures = [
    [makeWork('work:slow', { title: 'Hierarchical cognition', directions: ['D2'] }), {}],
    [makeWork('work:world', { title: '机器人世界模型的研究与进展', directions: ['D3'] }), {}],
    [makeWork('work:dexterity', { title: 'Dexterous hands', directions: ['D4'] }), {}],
    [makeWork('work:pi0', { title: 'π0: Vision-Language-Action Flow Model', directions: ['D1'] }), { organizationIds: ['org:physical-intelligence'], organizationNames: ['Physical Intelligence'] }],
    [makeWork('arxiv:2410.24164', { title: '$π_0$: A Vision-Language-Action Flow Model for General Robot Control', directions: ['D1'] }), {}],
    [makeWork('arxiv:2504.16054', { title: '$π_{0.5}$: a Vision-Language-Action Model with Open-World Generalization', directions: ['D1'] }), {}],
    [makeWork('work:pi07', { title: 'π0.7: generalist policy technical report', directions: ['D1'] }), {}],
    [makeWork('work:generic-vla', { title: 'An unrelated vision-language-action model', directions: ['D1'] }), {}],
    [makeWork('work:prefix-noise', { title: 'Pipeline policy pickup research', abstract: 'Comparison cites pi0 as a baseline.', directions: ['D1'] }), {}],
    [makeWork('work:original', { abstract: 'cross-embodiment transfer uniqueabstracttoken', authors: ['UniqueAuthor'], identifiers: { doi: '10.1234/uniquedoi' }, repositories: ['https://github.com/lab/uniquecoderepo'] }), {}],
    [makeWork('work:excluded', { title: 'excludeduniquephrase', relevance: { status: 'excluded' } }), {}],
    [makeWork('work:title-rank', { title: 'Rankingneedle robot', abstract: 'A robot.' }), {}],
    [makeWork('work:body-rank', { title: 'A robot', abstract: 'Rankingneedle robot.' }), {}],
    [makeWork('work:versions'), { manifestations: [{ kind: 'conference', venue: 'CoRL', year: 2025, peer_reviewed: true, track: 'main' }, { kind: 'conference', venue: 'ICRA', year: 2026, peer_reviewed: true, track: 'main' }] }],
    [makeWork('work:field-runtime', { title: 'Fieldtitleuniqueneedle Full Preserved Title', title_aliases: ['Historicalfielduniqueneedle'], authors: ['Fieldauthoruniqueneedle'],
      facets: { methods: ['Fieldfacetuniqueneedle'] }, repositories: ['https://github.com/lab/Fieldassetuniqueneedle'],
      abstract: 'Fieldtitleuniqueneedle Fieldauthoruniqueneedle Fieldfacetuniqueneedle Fieldassetuniqueneedle Fieldorguniqueneedle Fieldvenueuniqueneedle Historicalfielduniqueneedle Fieldabstractuniqueneedle. 字段去重示例。' }),
      { organizationNames: ['Canonical Display Institute Fieldorguniqueneedle AliasDiscoveryNeedle'], organizationDisplayNames: ['Canonical Display Institute'], manifestations: [{ kind: 'preprint', venue: 'Fieldvenueuniqueneedle', title: 'Preserved Publication Title' }] }],
  ]
  for (let i = 0; i < 603; i++) fixtures.push([makeWork(`bulk:${i}`), {}])
  const records = []
  const postings = {}
  try {
    for (const [work, context] of fixtures) {
      const ordinal = records.length
      const record = workSearchRecord(work, { ...context, explicitChinese: true, ordinal })
      records.push(record)
      for (const [name, values] of Object.entries(record.filters)) for (const value of values) {
        postings[name] ||= {}
        ;(postings[name][value] ||= []).push(ordinal)
      }
      const result = await index.addHTMLFile({ url: record.url, content: record.content })
      assert.deepEqual(result.errors, [])
    }
    const filesResponse = await index.getFiles()
    assert.deepEqual(filesResponse.errors, [])
    const files = new Map(filesResponse.files.map((file) => [file.path, file.content]))
    const originalFetch = globalThis.fetch
    globalThis.fetch = async (input) => {
      const key = String(input).split('/pagefind/').at(-1).split('?')[0]
      const bytes = files.get(key)
      if (!bytes) throw new Error(`Missing Pagefind fixture asset: ${key}`)
      return new Response(bytes, { headers: { 'Content-Type': key.endsWith('wasm') ? 'application/wasm' : 'application/octet-stream' } })
    }
    try {
      const engine = await import(`data:text/javascript;base64,${Buffer.from(files.get('pagefind.js')).toString('base64')}#${language}`)
      await engine.options({ bundlePath: '/pagefind/', language })
      await engine.init()
      const idsFor = async (query, filters = {}) => {
        const config = searchOptions({ ...defaultFilters(), q: query || '', relevance: 'all' }, [], [], language)
        const response = await engine.search(config.query, { filters: { ...config.filters, ...filters } })
        return Promise.all(response.results.map(async (result) => (await result.data()).meta.work_id))
      }
      for (const [query, expected] of [['大小脑', 'work:slow'], ['世界模型', 'work:world'], ['灵巧操作', 'work:dexterity'], ['PI', 'work:pi0'], ['π0.5', 'arxiv:2504.16054'], ['pi0.5', 'arxiv:2504.16054'], ['$π_{0.5}$', 'arxiv:2504.16054'], ['π0.7', 'work:pi07'], ['cross-embodiment', 'work:original'], ['uniqueabstracttoken', 'work:original'], ['UniqueAuthor', 'work:original'], ['10.1234/uniquedoi', 'work:original'], ['uniquecoderepo', 'work:original']]) assert.deepEqual(await idsFor(query), [expected], query)
      for (const query of ['Fieldtitleuniqueneedle', 'Fieldauthoruniqueneedle', 'Fieldfacetuniqueneedle', 'Fieldassetuniqueneedle', 'Fieldorguniqueneedle', 'AliasDiscoveryNeedle', 'Fieldvenueuniqueneedle', 'Historicalfielduniqueneedle', 'Fieldabstractuniqueneedle', '"Full Preserved Title"', '"Preserved Publication Title"', '字段去重示例']) assert.deepEqual(await idsFor(query), ['work:field-runtime'], query)
      assert.equal(records.find((record) => record.meta.work_id === 'work:field-runtime').meta.organizations, 'Canonical Display Institute')
      for (const query of ['π0', 'pi0', '$π_0$']) assert.deepEqual((await idsFor(query)).sort(), ['arxiv:2410.24164', 'arxiv:2504.16054', 'work:pi0', 'work:pi07'], query)
      assert.ok((await idsFor('VLA')).includes('work:generic-vla'))
      assert.deepEqual(await idsFor('excludeduniquephrase', { relevance: 'included' }), [])
      assert.deepEqual(await idsFor('excludeduniquephrase'), ['work:excluded'])
      assert.deepEqual(await idsFor('https://github.com/lab/uniquecoderepo'), ['work:original'])
      assert.deepEqual(await idsFor('work:pi0'), ['work:pi0'])
      assert.equal((await idsFor('Rankingneedle'))[0], 'work:title-rank')
      const response = await engine.search(null, { filters: { record_type: 'work' } })
      assert.equal(response.results.length, fixtures.length)
      const last = await loadResultPage(response.results, Math.ceil(fixtures.length / 20))
      assert.equal(last.rows.length, fixtures.length % 20)
      const allFilters = await engine.filters()
      const correlated = searchOptions({ ...defaultFilters(), venue: 'CoRL', year: '2026' }, [], Object.keys(allFilters.publication))
      assert.equal(correlated.empty, true)
      assert.deepEqual((await idsFor(null, { work_id: { any: ['work:pi0', 'work:excluded'] } })).sort(), ['work:excluded', 'work:pi0'])
      const range = searchOptions({ ...defaultFilters(), from: '2026-07', to: '2026-09' }, ['2026-07', '2026-08', '2026-09'], [])
      assert.equal((await engine.search(range.query, { filters: range.filters })).results.length, fixtures.length - 1)
      const ordered = await engine.search(null, { sort: { ordinal: 'asc' } })
      for (let i = 0; i < ordered.results.length; i++) assert.equal((await ordered.results[i].data()).meta.work_id, fixtures[i][0].work_id)
      const lookup = { ids: ordered.results.map((row) => row.id), work_ids: fixtures.map(([work]) => work.work_id), dates: fixtures.map(([work]) => work.first_public_date), postings }
      for (const key of files.keys()) if (key.startsWith('fragment/') || key.startsWith('filter/')) files.delete(key)
      const deployed = await import(`data:text/javascript;base64,${Buffer.from(files.get('pagefind.js')).toString('base64')}#deployed-${language}`)
      await deployed.options({ bundlePath: '/pagefind/', language })
      await deployed.init()
      const query = searchOptions({ ...defaultFilters(), q: '世界模型' }, [], [], language)
      const allowed = filterCatalog(lookup, query.filters)
      const results = await deployed.search(query.query)
      const positions = results.results.map((row) => lookup.ids.indexOf(row.id)).filter((position) => allowed.has(position))
      const adapted = positions.map((position) => ({ id: lookup.ids[position], data: async () => ({ meta: records[position].meta }) }))
      assert.deepEqual((await loadResultPage(adapted, 1)).rows.map((row) => row.meta.work_id), ['work:world'])
      // No fragment or native-filter assets remain available during this adapter query.
      assert.equal([...files.keys()].some((key) => key.startsWith('fragment/')), false)
    } finally { globalThis.fetch = originalFetch }
  } finally { await pagefind.close() }
})
