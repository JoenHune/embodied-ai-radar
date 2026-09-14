import test from 'node:test'
import assert from 'node:assert/strict'
import { publicationRecords, statusNotices, venueLabel } from '../docs/.vitepress/theme/lib/work-status.mjs'
import { workSearchRecord, compactResultCard } from '../scripts/lib/search-records.mjs'
import { searchCardFromResult, researchOutputLabel } from '../docs/.vitepress/theme/lib/research-card.mjs'

test('normal active state with no notice produces no false follow-up banner', () => {
  assert.deepEqual(statusNotices({ research_status: { status: 'active', notices: [] } }), [])
  assert.deepEqual(statusNotices({}), [])
})
test('actual notices show event, explanation, date and original source', () => {
  const notice = { event_type: 'withdrawn', public_at: '2026-09-05', date_precision: 'day', summary_zh: '作者因实验问题撤回。', source_url: 'https://arxiv.org/abs/2607.00001' }
  assert.deepEqual(statusNotices({ research_status: { status: 'withdrawn', notices: [notice] } })[0], { label: '作者撤回', summary: notice.summary_zh, date: notice.public_at, date_precision: 'day', url: notice.source_url })
})
test('venue names are precise without manufacturing a year', () => {
  assert.equal(venueLabel('CoRL', 2026, 'conference'), "CoRL'26")
  assert.equal(venueLabel('T-RO', 2026, 'journal'), 'TRO · 2026')
  assert.equal(venueLabel('Science Robotics', null, 'journal'), 'Science Robotics')
  assert.equal(venueLabel('unknown', 2026, 'conference'), '')
})
test('workshops remain explicit and serialized records reject unsafe source URLs', () => {
  assert.equal(publicationRecords({ manifestations: [{ kind: 'conference', venue: 'CoRL', year: 2026, track: 'workshop', status: 'official_program_only', url: 'https://example.org/workshop' }] })[0].venue, "CoRL'26 · Workshop")
  assert.deepEqual(publicationRecords({ publication_records: '[{"venue":"CoRL","state":"published","url":"javascript:alert(1)"}]' }), [])
})
test('ICRA program-only record never becomes formal publication or strict peer review', () => {
  const record = publicationRecords({ manifestations: [{ kind: 'conference', venue: 'ICRA', year: 2026, status: 'official_program_only', peer_reviewed: false, publication_status: 'unverified', url: 'https://example.org/program#paper' }] })[0]
  assert.equal(record.venue, "ICRA'26")
  assert.equal(record.state, '官方会议程序收录')
  assert.equal(record.peer_reviewed, false)
  assert.equal(record.date, null)
})
test('acceptance and publication are distinct, dates retain precision, DOI alone is unverified', () => {
  assert.equal(researchOutputLabel({ strict_peer_reviewed: true, output_types: ['conference'] }), '同行评审已核验')
  const base = { kind: 'conference', venue: 'CoRL', year: 2026, url: 'https://openreview.net/forum?id=example' }
  assert.equal(publicationRecords({ manifestations: [{ ...base, status: 'official_accepted_pending_proceedings' }] })[0].state, '已接收')
  assert.equal(publicationRecords({ manifestations: [{ ...base, status: 'publisher_url_from_registered_doi', published_at: '2026-01-01' }] })[0].state, '发表信息待官方核验')
  const published = { ...base, peer_reviewed: true, publication_status: 'published_proceedings', published_at: '2026-09', date_precision: 'month' }
  const rows = publicationRecords({ manifestations: [{ ...base, status: 'official_program_only' }, published] })
  assert.equal(rows.length, 1)
  assert.equal(rows[0].state, '已正式出版')
  assert.equal(rows[0].date_precision, 'month')
})
test('search cards retain concrete publication and status notices through compaction', () => {
  const work = { work_id: 'arxiv:2607.00001', title: 'Example', abstract: '', authors: [], directions: ['D1'], questions: [], relevance: { status: 'included' }, research_status: { status: 'corrected', validation_eligible: true, notices: [{ event_type: 'corrected', public_at: '2026-09-05', date_precision: 'day', summary_zh: '作者更正。', source_url: 'https://example.org/correction' }] } }
  const row = workSearchRecord(work, { manifestations: [{ kind: 'conference', venue: 'CoRL', year: 2026, status: 'official_accepted_pending_proceedings', url: 'https://openreview.net/forum?id=example' }] })
  const result = searchCardFromResult(compactResultCard(row))
  assert.equal(result.publication_records[0].venue, "CoRL'26")
  assert.equal(result.research_status.notices[0].summary_zh, '作者更正。')
})
