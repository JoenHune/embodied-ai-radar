import test from 'node:test'
import assert from 'node:assert/strict'
import { compactResultCard, workSearchRecord } from '../scripts/lib/search-records.mjs'
import { applySearchStatus } from '../scripts/lib/search-status.mjs'

test('indexing authority rows applies verified status without replacing original text', () => {
  const raw = { work_id: 'work:x', title: 'Original title', abstract: 'Original abstract', evidence_grade: 'E3', strict_peer_reviewed: true }
  const status = { work_id: raw.work_id, as_of: '2026-09-06', status: 'withdrawn', validation_eligible: false, notices: [{ notice_id: 'notice:x' }] }
  const detail = { work_id: raw.work_id, title: 'Must not overwrite original', research_status: status, research_status_as_of: status.as_of,
    evidence_grade: 'E0', evidence_flags: { real_robot: false, open_code: true }, strict_peer_reviewed: false }
  const overlaid = applySearchStatus(raw, status, detail)
  assert.equal(overlaid.title, raw.title)
  assert.equal(overlaid.abstract, raw.abstract)
  assert.equal(raw.evidence_grade, 'E3')
  const record = workSearchRecord(overlaid)
  assert.equal(record.meta.research_status, 'withdrawn')
  assert.equal(record.meta.research_status_as_of, '2026-09-06')
  assert.deepEqual(record.filters.peer_reviewed, ['false'])
  assert.deepEqual(record.filters.real_robot, ['false'])
  assert.deepEqual(record.filters.open_assets, ['true'])
  assert.throws(() => applySearchStatus(raw, status, { ...detail, work_id: 'wrong' }), /mismatch/)
  assert.throws(() => applySearchStatus(raw, status, { ...detail, research_status_as_of: '2026-08-31' }), /cutoff/)
})

test('verified status remains visible in both search results and compact browse cards', () => {
  const work = { work_id: 'work:status-fixture', title: 'Archived robot result', evidence_grade: 'E0',
    research_status: { status: 'withdrawn', validation_eligible: false, notices: [{ notice_id: 'notice:fixture' }] } }
  const record = workSearchRecord(work)
  assert.equal(record.meta.research_status, 'withdrawn')
  assert.equal(record.meta.research_validation_eligible, 'false')
  const compact = compactResultCard({ id: work.work_id, meta: record.meta, excerpt: record.excerpt })
  assert.equal(compact.meta.research_status, 'withdrawn')
  assert.equal(compact.meta.research_validation_eligible, 'false')
  assert.equal(compact.meta.work_id, work.work_id)
})

test('absence of a verified notice is not advertised as proof of clean status', () => {
  for (const status of [undefined, { status: 'active', notices: [], information_gaps: [{ reason: 'unverified' }] }]) {
    const record = workSearchRecord({ work_id: 'work:unknown', title: 'Robot research', research_status: status })
    assert.equal(record.meta.research_status, undefined)
    assert.equal(record.meta.research_validation_eligible, undefined)
  }
})
