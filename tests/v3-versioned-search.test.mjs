import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { gzipSync } from 'node:zlib'
import { createHash } from 'node:crypto'
import * as pagefind from 'pagefind'
import { availabilityUpper, localizationStatus, prepareSearchWork, sourceTextDigest, textAsOf, textHash, validTextSnapshot } from '../scripts/lib/versioned-search-text.mjs'
import { workSearchRecord } from '../scripts/lib/search-records.mjs'

const root = path.resolve(import.meta.dirname, '..')
const authorityWork = (id) => {
  const shard = createHash('sha1').update(id).digest('hex').slice(0, 2)
  return fs.readFileSync(path.join(root, `data/catalog/works/${shard}.jsonl`), 'utf8').trim().split('\n').map(JSON.parse).find((row) => row.work_id === id)
}
const snapshot = (id, version, availableAt, fields = {}) => {
  const text = { title: `Title ${version}`, abstract: `Abstract ${version}`, authors: [`Author ${version}`], ...fields }
  return { snapshot_id: `text:${id}`, source_record_id: `source:${id}`, work_id: 'arxiv:2602.12345', version, ...text,
    available_at: availableAt, date_precision: availableAt === null ? 'unknown' : availableAt.length === 7 ? 'month' : availableAt.length === 10 ? 'day' : 'second',
    source_url: `https://arxiv.org/abs/2602.12345${version || ''}`, content_digest: textHash(text), basis: 'synthetic-test' }
}
const workFor = (rows, fields = {}) => ({ work_id: 'arxiv:2602.12345', title: 'Raw future title', abstract: 'Raw future abstract', authors: ['FutureAuthor'],
  source_record_ids: rows.map((row) => row.source_record_id), first_public_date: '2026-02-01', first_public_date_precision: 'day', relevance: { status: 'included' }, ...fields })

test('search version selector agrees with Python across calendar, same-day, unknown, conflict and edition-order cases', () => {
  const sets = [
    [snapshot('a', 'v1', '2026-02-27'), snapshot('b', 'v2', '2026-06-30')],
    [snapshot('a', 'v2', '2026-06-30')],
    [snapshot('a', 'v1', '2026-08-31T15:00:00Z'), snapshot('b', 'v2', '2026-08-31T17:00:00Z')],
    [snapshot('a', 'v1', '2026-08-20T01:00:00Z'), snapshot('b', 'v2', '2026-08-20T02:00:00Z')],
    [snapshot('a', 'v1', null)],
    [snapshot('a', 'v1', '2026-08')],
    [snapshot('a', 'v1', '2026-08-01'), snapshot('b', 'v1', '2026-08-01', { title: 'Conflict' })],
    [snapshot('a', 'v1', '2026-09-01'), snapshot('b', 'v2', '2026-06-30')],
    [snapshot('a', null, '2026-09-01'), snapshot('b', 'v2', '2026-06-30')],
    [snapshot('a', 'v1', '2026-08-01T00:00:00.123456Z'), snapshot('b', 'v2', '2026-08-01T00:00:00.123457Z')],
  ]
  const cutoffs = ['2026-02', '2026-08-15', '2026-08', '2026-09', '2026-08-20T01:30:00Z', '2026-08-01T00:00:00.123456Z']
  const cases = sets.flatMap((snapshots) => cutoffs.map((cutoff) => ({ work: workFor(snapshots), snapshots, cutoff })))
  const command = "import json,sys; sys.path.insert(0,'scripts'); from versioned_text import text_as_of; print(json.dumps([text_as_of(x['work'],x['snapshots'],x['cutoff']) for x in json.load(sys.stdin)],ensure_ascii=False))"
  const python = fs.existsSync(path.join(root, '.venv/bin/python')) ? path.join(root, '.venv/bin/python') : 'python3'
  const result = spawnSync(python, ['-c', command], { cwd: root, input: JSON.stringify(cases), encoding: 'utf8' })
  assert.equal(result.status, 0, result.stderr)
  const expected = JSON.parse(result.stdout)
  cases.forEach((fixture, index) => assert.deepEqual(textAsOf(fixture.work, fixture.snapshots, fixture.cutoff), expected[index], `case ${index}`))
})

test('no timezone or impossible date never becomes midnight UTC', () => {
  assert.equal(availabilityUpper('2026-08-01T12:00:00'), null)
  assert.equal(availabilityUpper('2026-02-30'), null)
  assert.equal(availabilityUpper('2026-13'), null)
  assert.equal(availabilityUpper('2026-08-01', 'unknown'), null)
  assert.equal(availabilityUpper('2026-08-31'), availabilityUpper('2026-08'))
  assert.ok(availabilityUpper('2026-08-31T17:00:00Z') > availabilityUpper('2026-08'))
})

test('invalid content hashes and foreign source identities are excluded', () => {
  const row = snapshot('a', 'v1', '2026-02-27')
  const work = workFor([row])
  assert.equal(validTextSnapshot(row, work), true)
  assert.equal(validTextSnapshot({ ...row, abstract: 'Tampered' }, work), false)
  assert.equal(validTextSnapshot({ ...row, source_record_id: 'source:foreign' }, work), false)
})

test('selected title and authors are current; older labels remain aliases without old abstract', () => {
  const rows = [snapshot('a', 'v1', '2026-02-27', { title: 'OlderTitleNeedle', abstract: 'OldAbstractNeedle', authors: ['FormerAuthorNeedle'] }),
    snapshot('b', 'v2', '2026-06-30', { title: 'LatestTitleNeedle', abstract: 'LatestAbstractNeedle', authors: ['LatestAuthorNeedle'] }),
    snapshot('c', 'v3', '2026-09-02', { title: 'FutureTitleNeedle', abstract: 'FutureAbstractNeedle', authors: ['FutureAuthorNeedle'] })]
  const work = workFor(rows, { title: rows[2].title, title_aliases: ['RegisteredIdentifierAlias'], model_name: 'FutureModelNeedle', summary_zh: '旧译文不能继续使用', keywords_zh: ['失效关键词'] })
  const before = structuredClone(work)
  const record = workSearchRecord(work, { snapshots: rows, dataThrough: '2026-08-31' })
  for (const value of ['LatestTitleNeedle', 'LatestAuthorNeedle', 'OlderTitleNeedle', 'FormerAuthorNeedle', 'FutureTitleNeedle', 'RegisteredIdentifierAlias']) assert.ok(record.content.includes(value), value)
  for (const value of ['OldAbstractNeedle', 'FutureAbstractNeedle', 'FutureAuthorNeedle', 'FutureModelNeedle', '失效关键词']) assert.ok(!record.content.includes(value), value)
  assert.equal(record.meta.title, 'LatestTitleNeedle')
  assert.equal(record.meta.authors, 'LatestAuthorNeedle')
  assert.equal(record.meta.text_version, 'v2')
  assert.equal(record.meta.title_role, 'selected_version_text')
  assert.equal(record.meta.identifier_title, 'FutureTitleNeedle')
  assert.equal(record.meta.identifier_metadata_scope, 'latest_registered_names_not_historical_text')
  assert.equal(record.meta.work_id, work.work_id)
  assert.equal(record.index_info.historical_title_aliases, 1)
  assert.equal(record.index_info.historical_author_aliases, 1)
  assert.deepEqual(work, before)
})

test('missing historical text keeps the registered title as labeled identity, not future experimental text', () => {
  const future = [snapshot('future', 'v2', '2026-09-01', { title: 'FutureOnly', abstract: 'FutureOnlyBody' })]
  const record = workSearchRecord(workFor(future), { snapshots: future, dataThrough: '2026-08' })
  assert.equal(record.meta.title, 'Raw future title')
  assert.equal(record.meta.title_role, 'latest_identifier_metadata')
  assert.equal(record.meta.text_status, 'retrospective_only')
  assert.equal(record.excerpt, '')
  assert.ok(!record.content.includes('FutureOnly'))
  assert.ok(record.content.includes('Raw future title'))
  const conflicts = [snapshot('a', 'v1', '2026-08-01', { title: 'ConflictA' }), snapshot('b', 'v1', '2026-08-01', { title: 'ConflictB' })]
  const ambiguous = workSearchRecord(workFor(conflicts), { snapshots: conflicts, dataThrough: '2026-08' })
  assert.equal(ambiguous.meta.text_status, 'conflicting_snapshots')
  assert.equal(ambiguous.excerpt, '')
  assert.ok(!ambiguous.content.includes('ConflictA'))
  assert.ok(!ambiguous.content.includes('ConflictB'))
})

test('real Embrace Contacts identity review remains searchable when no arXiv text archive is available', () => {
  const id = 'arxiv:2502.01465'
  const shard = createHash('sha1').update(id).digest('hex').slice(0, 2)
  const work = fs.readFileSync(path.join(root, `data/catalog/works/${shard}.jsonl`), 'utf8').trim().split('\n').map(JSON.parse).find((row) => row.work_id === id)
  const reviews = fs.readFileSync(path.join(root, 'data/catalog/work-relations.jsonl'), 'utf8').trim().split('\n').map(JSON.parse).filter((row) => row.work_id === id)
  assert.ok(work.title_aliases.some((title) => title.startsWith('Embrace Contacts')))
  assert.ok(reviews.some((row) => row.review_id === 'identity-review:embrace-contacts-collisions'))
  const record = workSearchRecord(work, { dataThrough: '2026-08-31', snapshots: [], identityReviews: reviews })
  assert.match(record.content, /Embrace Contacts/)
  assert.match(record.content, /Embrace Collisions/)
  assert.equal(record.meta.work_id, id)
  assert.equal(record.meta.title, work.title)
  assert.equal(record.meta.title_role, 'unversioned_catalog_title')
  assert.equal(record.meta.text_status, 'unversioned_catalog_text')
  assert.equal(record.excerpt, work.abstract.slice(0, 260))
  assert.match(record.meta.identifier_review_dates, /2026-09-05T16:13:19Z/)
  assert.match(record.meta.identifier_publication_dates, /2025-10-07 \[day\]/)
  assert.equal(record.url, '/database/?work=arxiv%3A2502.01465')
})

test('no archive retains all collected bibliography text without claiming historical availability', () => {
  const work = workFor([], { title: 'Collected bibliography title', abstract: 'Originalbodyneedle. '.repeat(300) + 'Uniqueendingneedle. 中文原文保留。', authors: ['Collected Author'] })
  const before = structuredClone(work)
  const prepared = prepareSearchWork(work, { dataThrough: '2026-08-31', snapshots: [] })
  assert.equal(prepared.work.abstract, work.abstract)
  assert.deepEqual(prepared.work.authors, work.authors)
  assert.equal(prepared.work.text_status, 'unversioned_catalog_text')
  assert.equal(prepared.work.text_version_status, 'version_not_verified')
  assert.equal(prepared.work.text_cutoff_applicability, 'not_applicable_unversioned_catalog_text')
  assert.equal(prepared.work.text_available_at, null)
  assert.equal(prepared.text.status, 'unavailable', 'The strict historical selector must still refuse unversioned text')
  const record = workSearchRecord(work, { dataThrough: '2026-08-31', snapshots: [] })
  assert.match(record.content, /Uniqueendingneedle/)
  assert.match(record.content, /Collected Author/)
  assert.equal(record.meta.text_status, 'unversioned_catalog_text')
  assert.equal(record.meta.text_version_status, 'version_not_verified')
  assert.equal(record.meta.text_cutoff_applicability, 'not_applicable_unversioned_catalog_text')
  assert.equal(record.meta.text_available_at, '')
  assert.deepEqual(work, before)
})

test('invalid existing archive does not trigger unversioned fallback', () => {
  const invalid = { ...snapshot('a', 'v1', '2026-02-27'), content_digest: 'bad-hash' }
  const work = workFor([invalid], { abstract: 'DoNotFallbackToThisBody' })
  const record = workSearchRecord(work, { dataThrough: '2026-08-31', snapshots: [invalid] })
  assert.equal(record.meta.text_status, 'unavailable')
  assert.equal(record.meta.text_cutoff_applicability, 'blocked_no_available_text')
  assert.ok(!record.content.includes('DoNotFallbackToThisBody'))
})

test('actual HGSLoc keeps DOI/arXiv identity, complete collected abstract and authors without an archive', () => {
  const work = authorityWork('doi:10.1109/icra55743.2025.11127431')
  assert.equal(work.identifiers.arxiv, '2409.10925')
  assert.match(work.abstract, /steplevel/)
  const prepared = prepareSearchWork(work, { dataThrough: '2026-08-31', snapshots: [] })
  assert.equal(prepared.work.abstract, work.abstract)
  assert.deepEqual(prepared.work.authors, work.authors)
  const record = workSearchRecord(work, { dataThrough: '2026-08-31', snapshots: [] })
  for (const needle of ['HGSLoc', 'steplevel', 'Deep', 'Blending', 'Zhongyan Niu']) assert.ok(record.content.includes(needle), needle)
  assert.equal(record.meta.work_id, work.work_id)
  assert.ok(record.filters.work_id.includes('arxiv:2409.10925'))
  assert.equal(record.meta.text_status, 'unversioned_catalog_text')
  assert.equal(record.meta.text_version_status, 'version_not_verified')
})

test('preprint metadata cannot smuggle a future revision into current text; dated publications remain separately searchable', () => {
  const rows = [snapshot('a', 'v1', '2026-02-27', { title: 'OriginalTitle' })]
  const record = workSearchRecord(workFor(rows), { snapshots: rows, dataThrough: '2026-02', manifestations: [
    { kind: 'preprint', title: 'FutureRevisionHiddenInManifestation', published_at: '2026-02-27', date_precision: 'day' },
    { kind: 'conference', title: 'FutureConferenceTitle', published_at: '2026-09-01', date_precision: 'day', venue: 'FutureVenue' },
  ] })
  assert.ok(!record.content.includes('FutureRevisionHiddenInManifestation'))
  assert.ok(record.content.includes('FutureConferenceTitle'))
  assert.ok(record.content.includes('FutureVenue'))
  assert.equal(record.meta.title, 'OriginalTitle')
  assert.equal(record.meta.text_cutoff, '2026-02')
  assert.match(record.meta.publication_dates, /published:2026-09-01 \[day\]/)
  assert.equal(record.meta.publication_metadata_scope, 'latest_registered')
})

test('September CoRL acceptance stays filterable alongside August-capped arXiv text', () => {
  const rows = [snapshot('a', 'v1', '2026-02-27'), snapshot('b', 'v2', '2026-09-02', { abstract: 'September revision text' })]
  const record = workSearchRecord(workFor(rows), { snapshots: rows, dataThrough: '2026-08-31', manifestations: [{ kind: 'conference', venue: 'CoRL', year: 2026,
    track: 'main_conference', peer_reviewed: true, status: 'accepted_official', publication_status: 'accepted_peer_reviewed',
    accepted_at: '2026-09-04', date_precision: 'day', title: 'Official accepted title', url: 'https://openreview.net/forum?id=fixture' }] })
  assert.equal(record.meta.text_version, 'v1')
  assert.ok(!record.content.includes('September revision text'))
  assert.deepEqual(record.filters.venue, ['CoRL'])
  assert.deepEqual(record.filters.year, ['2026'])
  assert.deepEqual(record.filters.track, ['main_conference'])
  assert.deepEqual(record.filters.acceptance, ['accepted'])
  assert.deepEqual(record.filters.publication_status, ['accepted_peer_reviewed'])
  assert.ok(record.filters.source_url.includes('https://openreview.net/forum?id=fixture'))
  assert.match(record.meta.publication_dates, /accepted:2026-09-04/)
})

test('localization binds selected version content and its source IDs, not raw canonical', () => {
  const rows = [snapshot('a', 'v1', '2026-02-27'), snapshot('b', 'v2', '2026-06-30')]
  const work = workFor(rows, { title: rows[0].title, abstract: rows[0].abstract })
  const localized = { work_id: work.work_id, title_zh: '新版中文', summary_zh: '新版摘要', source_ids: ['source:b'], source_content_digest: sourceTextDigest(rows[1]), keywords_zh: ['有效关键词'] }
  assert.equal(localizationStatus(localized, work), 'source_changed')
  const prepared = prepareSearchWork(work, { snapshots: rows, dataThrough: '2026-08', localization: localized })
  assert.equal(prepared.localization_status, 'current')
  assert.equal(prepared.work.title_zh, '新版中文')
  assert.equal(work.title, rows[0].title)
  const feb = prepareSearchWork(work, { snapshots: rows, dataThrough: '2026-02', localization: localized })
  assert.equal(feb.localization_status, 'source_changed')
  assert.equal(feb.work.title_zh, '')
  const foreign = prepareSearchWork(work, { snapshots: rows, dataThrough: '2026-08', localization: { ...localized, source_ids: ['source:a'] } })
  assert.equal(foreign.localization_status, 'invalid_source')
})

test('non-arxiv reports preserve their source text and non-versioned legacy notes', () => {
  const prepared = prepareSearchWork({ work_id: 'report:a', title: 'Company report', abstract: '', authors: [], source_record_ids: [] }, { dataThrough: '2026-08-31', legacyNote: { contribution_zh: '公司自报说明' } })
  assert.equal(prepared.work.title, 'Company report')
  assert.equal(prepared.work.summary_zh, '公司自报说明')
  assert.equal(prepared.work.text_status, 'non_arxiv_source_text')
})

test('actual StemVLA v1/v2 select changed experiments and retain prior author as alias', () => {
  const rows = fs.readFileSync(path.join(root, 'data/versioned-text-additions.jsonl'), 'utf8').trim().split('\n').map(JSON.parse)
  const work = workFor(rows, { work_id: 'arxiv:2602.23721', title: rows[0].title, abstract: rows[0].abstract, authors: rows[0].authors })
  const february = prepareSearchWork(work, { snapshots: rows, dataThrough: '2026-02' })
  assert.match(february.work.abstract, /XXX/)
  assert.equal(february.work.authors.length, 6)
  const august = prepareSearchWork(work, { snapshots: rows, dataThrough: '2026-08-31' })
  assert.match(august.work.abstract, /92\.0%/)
  assert.doesNotMatch(august.work.abstract, /XXX/)
  assert.equal(august.work.authors.length, 5)
  assert.deepEqual(august.work.author_aliases, ['Ziang Tong'])
  const record = workSearchRecord(work, { snapshots: rows, dataThrough: '2026-08-31' })
  assert.ok(record.content.includes('Ziang Tong'))
  assert.ok(!record.content.includes('XXX'))
  assert.deepEqual(record.filters.work_id, ['arxiv:2602.23721'])
})

test('large older abstracts are not duplicated into the index and the hard budget stays enabled', () => {
  const rows = [snapshot('a', 'v1', '2026-02-27', { abstract: 'olduniquetoken '.repeat(100_000) }), snapshot('b', 'v2', '2026-06-30')]
  const record = workSearchRecord(workFor(rows), { snapshots: rows, dataThrough: '2026-08' })
  assert.ok(record.content.length < 10_000)
  assert.ok(gzipSync(record.content).length < 5_000)
  assert.ok(!record.content.includes('olduniquetoken'))
  const build = fs.readFileSync(path.join(root, 'scripts/build-pagefind-index.mjs'), 'utf8')
  assert.match(build, /index_budget_bytes = 20_000_000/)
  assert.match(build, /if \(!metrics\.index_budget_pass\) throw/)
})

test('small real Pagefind index returns current and historical labels once, never future text', async () => {
  const rows = [snapshot('a', 'v1', '2026-02-27', { title: 'Archivedtitleuniqueneedle', abstract: 'Oldbodyuniqueneedle', authors: ['Archivedauthoruniqueneedle'] }),
    snapshot('b', 'v2', '2026-06-30', { title: 'Currenttitleuniqueneedle', abstract: 'Currentbodyuniqueneedle', authors: ['Currentauthoruniqueneedle'] }),
    snapshot('c', 'v3', '2026-09-01', { title: 'Futuretitleuniqueneedle', abstract: 'Futurebodyuniqueneedle', authors: ['Futureauthoruniqueneedle'] })]
  const { index, errors } = await pagefind.createIndex({ forceLanguage: 'en' })
  assert.deepEqual(errors, [])
  const record = workSearchRecord(workFor(rows, { title: rows[1].title }), { dataThrough: '2026-08', snapshots: rows })
  const unversioned = workSearchRecord(authorityWork('doi:10.1109/icra55743.2025.11127431'), { dataThrough: '2026-08-31', snapshots: [] })
  const originalFetch = globalThis.fetch
  try {
    assert.deepEqual((await index.addHTMLFile({ url: record.url, content: record.content })).errors, [])
    assert.deepEqual((await index.addHTMLFile({ url: unversioned.url, content: unversioned.content })).errors, [])
    const response = await index.getFiles()
    const files = new Map(response.files.map((file) => [file.path, file.content]))
    globalThis.fetch = async (input) => new Response(files.get(String(input).split('/pagefind/').at(-1).split('?')[0]))
    const engine = await import(`data:text/javascript;base64,${Buffer.from(files.get('pagefind.js')).toString('base64')}#version-fixture`)
    await engine.options({ bundlePath: '/pagefind/', language: 'en' })
    await engine.init()
    for (const term of ['Currenttitleuniqueneedle', 'Currentbodyuniqueneedle', 'Currentauthoruniqueneedle', 'Archivedtitleuniqueneedle', 'Archivedauthoruniqueneedle']) {
      const found = await engine.search(term)
      assert.equal(found.results.length, 1, term)
      assert.equal((await found.results[0].data()).meta.work_id, record.meta.work_id)
    }
    for (const term of ['Futuretitleuniqueneedle', 'Futurebodyuniqueneedle', 'Futureauthoruniqueneedle', 'Oldbodyuniqueneedle']) assert.equal((await engine.search(term)).results.length, 0, term)
    for (const query of ['HGSLoc', 'steplevel', 'Deep Blending', 'Zhongyan Niu']) {
      const found = await engine.search(query)
      assert.equal(found.results.length, 1, query)
      const data = await found.results[0].data()
      assert.equal(data.meta.work_id, unversioned.meta.work_id)
      assert.equal(data.meta.text_status, 'unversioned_catalog_text')
    }
    assert.equal((await engine.search(null)).results.length, 2)
  } finally {
    globalThis.fetch = originalFetch
    await pagefind.close()
  }
})
