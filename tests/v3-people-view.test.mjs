import test from 'node:test'
import assert from 'node:assert/strict'
import { peopleStateFromUrl, peopleUrl, filterPeople, activitySummary, verifiedCollaborators, metricText, escapeChartText, personDetailMatchesIndex } from '../docs/.vitepress/theme/lib/people-view.mjs'
import { personWorkList } from '../docs/.vitepress/theme/lib/people-view.mjs'

const person = (id, extra = {}) => ({ person_id: id, name: id, slug: id, verified_work_ids: [], ...extra })
test('verified works show newest first; all-scope preserves older and non-included authorships', () => {
  const works = [{ work_id: 'old', first_public_date: '2024-01-01', in_complete_window: false }, { work_id: 'a', first_public_date: '2026-01-01', in_complete_window: true }, { work_id: 'b', first_public_date: '2026-08-01', in_complete_window: true }]
  assert.deepEqual(personWorkList(works).map(row => row.work_id), ['b', 'a'])
  assert.deepEqual(personWorkList(works, 'all').map(row => row.work_id), ['b', 'a', 'old'])
  assert.equal(works[0].work_id, 'old')
})
test('people filters and profile round-trip through a shareable URL', () => {
  const state = { q: '大小脑 π0', direction: 'D3', lens: 'recent', sort: 'active', person: 'yilun-du' }
  const url = peopleUrl('https://radar.test/organizations/people/?keep=yes#people', state)
  assert.deepEqual(peopleStateFromUrl(url), state)
  assert.match(url, /keep=yes/)
  assert.match(url, /#people$/)
})
test('invalid people URL values fall back without accepting a path as person', () => {
  assert.deepEqual(peopleStateFromUrl('/?directions=D90&person=..%2Fsecret&lens=rank&sort=influence'), { q: '', direction: '', person: '', lens: 'contribution', sort: 'name' })
})
test('direction filtering uses verified direction counts, not candidate names', () => {
  const rows = [person('a', { directions: [{ code: 'D1', count: 1 }] }), person('b', { candidate_work_ids: ['w'], directions: [] })]
  assert.deepEqual(filterPeople(rows, { q: '', direction: 'D1', sort: 'name' }).map(p => p.name), ['a'])
})
test('sort is stable and leaves missing metrics after actual zero', () => {
  const rows = [person('missing'), person('zero', { metrics: { verified_works_window: 0 } }), person('two', { metrics: { verified_works_window: 2 } })]
  assert.deepEqual(filterPeople(rows, { q: '', direction: '', sort: 'verified' }).map(p => p.name), ['two', 'zero', 'missing'])
  assert.deepEqual(rows.map(p => p.name), ['missing', 'zero', 'two'])
})
test('activity excludes out-of-window months and does not invent growth classification', () => {
  const row = person('a', { monthly_activity: [{ month: '2026-01', count: 100 }, { month: '2026-03', count: 1 }, { month: '2026-07', count: 2 }, { month: '2026-09', count: 10 }] })
  assert.deepEqual(activitySummary(row, ['2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08']), { active: 2, recent: 2, prior: 1 })
})
test('collaboration requires both authorships verified, deduplicates works, excludes self', () => {
  const a = person('a', { verified_work_ids: ['w', 'w2'] })
  const b = person('b', { verified_work_ids: ['w', 'w'], candidate_work_ids: ['w2'] })
  const c = person('c', { candidate_work_ids: ['w'] })
  const result = verifiedCollaborators(a, [a, b, c], [{ person_ids: ['a', 'b'], work_ids: ['w'] }])
  assert.equal(result.length, 1)
  assert.deepEqual(result[0].shared_work_ids, ['w'])
})
test('unknown impact is not zero and tooltip content is escaped', () => {
  assert.equal(metricText(null), '尚未核验')
  assert.equal(metricText(undefined), '尚未核验')
  assert.equal(metricText(0), '0')
  assert.equal(escapeChartText('<img "x">&'), '&lt;img &quot;x&quot;&gt;&amp;')
})
test('out-of-window shared works cannot add a collaboration edge', () => {
  const a = person('a', { verified_work_ids: ['old'] }), b = person('b', { verified_work_ids: ['old'] })
  assert.deepEqual(verifiedCollaborators(a, [a, b], []), [])
})
test('details must match index dataset and review version, not merely the name', () => {
  const index = { dataset_version: 'v2', review_hash: 'review2' }
  const detail = { slug: 'a', schema_version: '1', ...index }
  assert.equal(personDetailMatchesIndex(detail, index, 'a'), true)
  for (const change of [{ dataset_version: 'v1' }, { review_hash: 'review1' }, { slug: 'b' }, { schema_version: '0' }]) {
    assert.equal(personDetailMatchesIndex({ ...detail, ...change }, index, 'a'), false)
  }
  assert.equal(personDetailMatchesIndex({ slug: 'a' }, {}, 'a'), false)
})
