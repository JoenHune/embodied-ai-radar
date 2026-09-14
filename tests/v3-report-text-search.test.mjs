import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { prepareSearchWork, textHash, sourceTextDigest } from '../scripts/lib/versioned-search-text.mjs'
import { workSearchRecord } from '../scripts/lib/search-records.mjs'

const snapshot=JSON.parse(fs.readFileSync(new URL('../data/report-text-additions.jsonl',import.meta.url),'utf8').trim())
const work={work_id:snapshot.work_id,title:'GEN-1.5',abstract:'',authors:[],aliases:[],source_record_ids:[snapshot.source_record_id],directions:['D1'],questions:['Q6'],facets:{},relevance:{status:'included'},first_public_date:'2026-08-19',first_public_date_precision:'day',strict_peer_reviewed:false,evidence_grade:'E1'}
const view={status:'available',canonical_work_id:work.work_id,as_of:'2026-08-31',snapshot_ids:[snapshot.snapshot_id],snapshots:[snapshot],available_at:snapshot.available_at,date_precision:snapshot.date_precision}

test('audited report excerpts are indexed separately without fabricating the original abstract',()=>{
  const result=workSearchRecord(work,{dataThrough:'2026-08-31',reportText:view})
  assert.equal(work.abstract,'')
  assert.equal(result.meta.text_status,'report_excerpt_available')
  assert.ok(result.content.includes('59%'))
  assert.ok(result.content.includes('10 gradient steps'))
  assert.ok(result.filters.source_url.includes(snapshot.source_url))
  assert.deepEqual(result.filters.peer_reviewed,['false'])
  assert.deepEqual(result.filters.evidence,['E1'])
})

test('future cutoff, foreign source and changed excerpt bytes cannot enter the report index',()=>{
  assert.throws(()=>prepareSearchWork(work,{dataThrough:'2026-08-20',reportText:{...view,as_of:'2026-08-20'}}),/snapshot_invalid/)
  assert.throws(()=>prepareSearchWork(work,{dataThrough:'2026-08-31',reportText:{...view,as_of:'2026-09-01'}}),/cutoff_or_identity/)
  assert.throws(()=>prepareSearchWork({...work,source_record_ids:[]},{dataThrough:'2026-08-31',reportText:view}),/snapshot_invalid/)
  const changed=structuredClone(view)
  changed.snapshots[0].excerpts[0].text='A fabricated excerpt'
  assert.throws(()=>prepareSearchWork(work,{dataThrough:'2026-08-31',reportText:changed}),/snapshot_invalid/)
})

test('report localization uses selected snapshot identity, content and source ownership',()=>{
  const source=prepareSearchWork(work,{dataThrough:'2026-08-31',reportText:view}).work
  const localized={work_id:work.work_id,title_zh:'通才策略少样本适配',summary_zh:'公司自报的一种适配方法。',source_ids:[snapshot.source_record_id],source_content_digest:sourceTextDigest(source)}
  assert.equal(prepareSearchWork(work,{dataThrough:'2026-08-31',reportText:view,localization:localized}).localization_status,'current')
  assert.equal(prepareSearchWork(work,{dataThrough:'2026-08-31',reportText:view,localization:{...localized,source_content_digest:textHash({title:work.title,abstract:''})}}).localization_status,'source_changed')
  assert.equal(prepareSearchWork(work,{dataThrough:'2026-08-31',reportText:view,localization:{...localized,source_ids:['foreign']}}).localization_status,'invalid_source')
})

test('raw work cannot self-assert report text and unavailable selections expose no later excerpt',()=>{
  const selfAsserted=prepareSearchWork({...work,report_text:view},{dataThrough:'2026-08-31'})
  assert.equal(selfAsserted.work.report_text,undefined)
  const future={...view,status:'retrospective_only',snapshots:[],snapshot_ids:[],as_of:'2026-08-20'}
  const result=prepareSearchWork(work,{dataThrough:'2026-08-20',reportText:future})
  assert.equal(result.work.report_text,undefined)
  assert.equal(result.localization_status,'historical_text_unavailable')
})
