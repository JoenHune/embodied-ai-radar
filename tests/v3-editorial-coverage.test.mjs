import test from 'node:test'
import assert from 'node:assert/strict'
import { editorialCoverage, dashboardSnapshot, previousEditorialSummary } from '../scripts/lib/editorial-coverage.mjs'

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

const previous = (extra = {}) => ({ month:'2026-08', model:'gpt-5.6-sol', generated_at:'2026-09-06T06:01:44Z', input_digest:'a'.repeat(64), status:'complete',
  claims:[{claim_id:'old:1',title:'旧判断',summary:'旧稿内容',directions:['D1'],supporting_ids:['arxiv:2608.00001'],response_id:'do-not-copy',source_spans:['large-original-text']}],
  direction_summaries:[{code:'D1',summary:'旧方向',supporting_ids:['arxiv:2608.00001']}],
  question_summaries:[{code:'Q0',summary:'旧问题'}],counterevidence:[{title:'旧反例',summary:'不能升级的信号'}],watchlist:[{title:'旧观察',summary:'以后核查'}],
  localizations:Array.from({length:100},()=>({full_text:'not-a-dashboard-field'})),signal_assessments:[{source_spans:'do-not-copy'}],response_id:'private-api-id',post_edit_reviews:[{large:'review-history'}],...extra })

test('previous complete prose is a small historical projection, never current completion', () => {
  const source = {month:'2026-08',editorial_status:'data_only',previous_editorial:previous(),editorial_unavailable_reason:'input_digest_changed',executive_findings:[{text:'当前数据'}]}
  const before = structuredClone(source)
  const view = dashboardSnapshot(source)
  assert.equal(view.previous_editorial_summary.status,'historical_not_current')
  assert.equal(view.previous_editorial_summary.claims[0].summary,'旧稿内容')
  for(const key of ['claims','direction_summaries','question_summaries','counterevidence','watchlist']) assert.equal(view.previous_editorial_summary[key].length,1)
  assert.deepEqual(Object.keys(view.previous_editorial_summary).sort(), ['month','model','generated_at','input_digest','status','claims','direction_summaries','question_summaries','counterevidence','watchlist'].sort())
  assert.ok(!JSON.stringify(view).includes('do-not-copy') && !JSON.stringify(view).includes('private-api-id'))
  assert.ok(!('previous_editorial' in view) && !('editorial' in view))
  assert.equal(view.editorial_status,'data_only')
  assert.equal(view.executive_findings[0].text,'当前数据')
  assert.equal(editorialCoverage(['2026-08'], {'2026-08':view.editorial_status}).status,'data_only')
  assert.deepEqual(source,before)
  view.previous_editorial_summary.claims[0].supporting_ids.push('work:later')
  assert.deepEqual(source,before)
})

test('missing or mismatched provenance never becomes an apparent historical complete summary', () => {
  for(const extra of [{month:'2026-07'},{status:'failed'},{input_digest:null},{generated_at:'not-a-date'},{model:null}]) {
    assert.equal(previousEditorialSummary(previous(extra),'2026-08'),null)
  }
  assert.equal(previousEditorialSummary(previous(),'2026-13'),null)
  const artifact=previous({claims:[null,42,{summary:{raw:'bad'}},{text:'合法历史文字',unapproved:{secret:true}}]})
  const summary=previousEditorialSummary(artifact,'2026-08')
  assert.deepEqual(summary.claims,[{text:'合法历史文字'}])
  assert.equal(previousEditorialSummary({status:'complete',month:'2026-08'},'2026-08'),null)
})

test('history metadata is whitelisted and double projection remains idempotent', () => {
  const history={artifact_digest:'b'.repeat(64),generated_at:'2026-09-06T06:01:44Z',model:'gpt-5.6-sol',input_digest:'a'.repeat(64),archive_url:`/api/v1/editorial-history/2026-08/${'b'.repeat(64)}.json`,input_packet_status:'matched',full_artifact:{secret:'do-not-copy'}}
  const view=dashboardSnapshot({month:'2026-08',previous_editorial:previous(),editorial_history:[history,null]})
  assert.ok(!('full_artifact' in view.editorial_history[0]))
  assert.equal(view.editorial_history[0].input_packet_status,'matched')
  assert.deepEqual(dashboardSnapshot(view),view)
  assert.ok(!('previous_editorial_summary' in dashboardSnapshot({month:'2026-08'})))
  assert.ok(!('editorial_history' in dashboardSnapshot({month:'2026-08'})))
})
