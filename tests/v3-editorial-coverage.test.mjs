import test from 'node:test'
import assert from 'node:assert/strict'
import { editorialCoverage, dashboardSnapshot } from '../scripts/lib/editorial-coverage.mjs'

test('one completed latest month does not mark the entire archive complete', () => {
  assert.deepEqual(editorialCoverage(['2026-07', '2026-08'], {'2026-07':'legacy_editorial','2026-08':'llm_complete'}), {
    status:'partial',completed_months:['2026-08'],remaining_months:['2026-07'],
  })
})
test('only validated overlays count, not missing or preserved historical output', () => {
  assert.equal(editorialCoverage(['2026-07','2026-08'], {'2026-07':'source_changed','2026-08':'data_only'}).status,'data_only')
  assert.equal(editorialCoverage([], {}).status,'data_only')
})
test('all required complete months can finish while provisional is separate', () => {
  assert.deepEqual(editorialCoverage(['2026-07','2026-08'], {'2026-07':'llm_complete','2026-08':'llm_complete','2026-09':'data_only'}), {
    status:'llm_complete',completed_months:['2026-07','2026-08'],remaining_months:[],
  })
})
test('dashboard omits duplicate model archives but preserves findings and evidence links', () => {
  const source = {month:'2026-08',editorial:{private_duplicate:'raw'},previous_editorial:{old:true},executive_findings:[{supporting_ids:['work:a']}],directions:[{code:'D1',primary_count:3}],editorial_reviews:[{review_id:'review:1'}]}
  const before = structuredClone(source)
  const view = dashboardSnapshot(source)
  assert.ok(!('editorial' in view) && !('previous_editorial' in view))
  assert.deepEqual(view.executive_findings, source.executive_findings)
  assert.deepEqual(view.directions, source.directions)
  assert.deepEqual(view.editorial_reviews, source.editorial_reviews)
  assert.deepEqual(source, before)
})
