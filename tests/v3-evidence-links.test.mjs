import test from 'node:test'
import assert from 'node:assert/strict'
import { evidenceIds, evidenceWorkIds, evidenceSearchParams } from '../docs/.vitepress/theme/lib/evidence-links.mjs'
test('editorial references override generic direction representatives', () => {
  assert.deepEqual(evidenceIds({supporting_ids:['work:reviewed'],supporting_work_ids:['work:sample']}),['work:reviewed'])
  assert.deepEqual(evidenceIds({supporting_ids:[],supporting_work_ids:['work:sample']}),[])
  assert.deepEqual(evidenceIds({supporting_work_ids:['work:sample']}),['work:sample'])
})
test('event citations lead to canonical work details without duplicate works', () => {
  const ids=['event:release','work:a','event:review','work:b']
  assert.deepEqual(evidenceWorkIds(ids,{'event:release':'work:a','event:review':'work:b'}),['work:a','work:b'])
  assert.deepEqual(ids,['event:release','work:a','event:review','work:b'])
})
test('explicit evidence is not hidden by first-publication bounds, ordinary browse keeps dates', () => {
  const params = {from:'2026-08',to:'2026-08',directions:'D1'}
  const cited = evidenceSearchParams(['event:accepted'], {'event:accepted':'work:older'}, params)
  assert.equal(cited.get('ids'),'work:older')
  assert.equal(cited.get('from'),null)
  assert.equal(cited.get('to'),null)
  assert.equal(cited.get('directions'),'D1')
  assert.equal(evidenceSearchParams([],{},params).get('from'),'2026-08')
  assert.equal(params.from,'2026-08')
})
