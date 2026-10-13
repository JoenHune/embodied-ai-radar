import test from 'node:test'
import assert from 'node:assert/strict'
import { researchBrief } from '../scripts/lib/research-brief.mjs'

const manifest = { data_through: '2026-09-14', complete_months: ['2026-08'], generated_at: '2026-10-13' }
test('collection freshness never borrows the build date or requested cutoff', () => {
  const result = researchBrief({ manifest, coverage: { requested_source_cutoff: '2026-10-13',
    available_data_through: '2026-09-11', status: 'partial', sources: [
      { source: 'arxiv', status: 'partial', complete: false, checked_at: '2026-09-14T02:00:00Z' },
      { source: 'publications', status: 'not_checked_this_run' },
    ] } })
  assert.equal(result.last_source_check, '2026-09-14')
  assert.equal(result.available_data_through, '2026-09-11')
  assert.equal(result.complete, false)
  assert.equal(result.sources[1].checked_at, null)
  assert.equal(researchBrief({ manifest }).last_source_check, null)
  assert.equal(researchBrief({ manifest }).status, 'not_run')
})
test('team activity requires dated attributed research inside the analysis window', () => {
  const update = { published_at: '2026-09-08', date_precision: 'day', attribution_grade: 'G1',
    title: 'Research', url: 'https://example.org/research', event_id: 'e1', event_type: 'preprint' }
  const org = { organization_id: 'org:a', slug: 'a', name: 'A', tier: 'T0', updates: [update] }
  const organizations = [org, ...[
    { published_at: '2026-10-01' }, { published_at: '2026-07-31' }, { date_precision: 'month' },
    { attribution_grade: 'G0' }, { research_eligible: false }, { url: 'javascript:alert(1)' },
    { event_type: 'retracted' }, { event_type: 'accepted' }, { event_type: 'corrected' },
  ].map((changes, i) => ({ ...org, slug: `excluded-${i}`, updates: [{ ...update, ...changes }] }))]
  const result = researchBrief({ manifest, organizations })
  assert.deepEqual(result.teams.map(team => team.slug), ['a'])
  assert.deepEqual(result.team_window, { from: '2026-08-01', through: '2026-09-14' })
})
test('a global completeness flag cannot hide an incomplete source', () => {
  assert.equal(researchBrief({ manifest, coverage: { registered_scope_complete: true,
    sources: [{ source: 'arxiv', complete: false }] } }).complete, false)
})
test('check timestamps use the Shanghai calendar without assigning precision to invalid dates', () => {
  const result = researchBrief({ manifest, coverage: { sources: [
    { source: 'arxiv', checked_at: '2026-09-13T20:00:00Z' },
    { source: 'invalid', checked_at: '2026-02-30' },
    { source: 'unbound', checked_at: '2026-09-14T20:00:00' },
  ] } })
  assert.equal(result.last_source_check, '2026-09-14')
  assert.equal(result.sources[1].checked_at, null)
  assert.equal(result.sources[2].checked_at, null)
})
