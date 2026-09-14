import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { dashboardSnapshot } from '../scripts/lib/editorial-coverage.mjs'

const source=fs.readFileSync(new URL('../docs/.vitepress/theme/components/HistoricalEditorial.vue',import.meta.url),'utf8')
const descriptor=parse(source).descriptor
const digest='a'.repeat(64), artifactDigest='b'.repeat(64)
const artifact=(extra={})=>({month:'2026-08',status:'complete',model:'gpt-5.6-sol',generated_at:'2026-09-06T06:01:44Z',input_digest:digest,
  claims:[{title:'旧判断',summary:'仍可读的旧稿',supporting_ids:['arxiv:2608.00001'],counterevidence_ids:['arxiv:2608.00002']}],
  direction_summaries:[{code:'D1',summary:'旧方向摘要'}],question_summaries:[{code:'Q0',summary:'旧问题摘要'}],
  counterevidence:[{summary:'旧反例'}],watchlist:[{summary:'旧观察'}],...extra})
const history=(extra={})=>({artifact_digest:artifactDigest,generated_at:'2026-09-06T06:01:44Z',model:'gpt-5.6-sol',input_digest:digest,
  archive_url:`/api/v1/editorial-history/2026-08/${artifactDigest}.json`,input_packet_status:'matched',...extra})
const snapshot=(extra={})=>({month:'2026-08',editorial_status:'data_only',editorial_unavailable_reason:'input_digest_changed',previous_editorial:artifact(),editorial_history:[history()],...extra})
function harness(value=snapshot()) {
  const props={snapshot:value}
  const ctx={Date,Set,defineProps:()=>props,computed:fn=>({get value(){return fn()}}),withBase:path=>'/embodied-ai-radar'+path,eventDate:value=>value}
  vm.runInNewContext(ts.transpile(descriptor.scriptSetup.content.replace(/^import .*$/gm,'')+'\nglobalThis.view={month,previous,groups,reason,references,rowTitle,rowText,archives,hasContent};',{target:ts.ScriptTarget.ES2022}),ctx)
  return {...ctx.view,props}
}

test('historical view compiles, is monthly-only and is keyboard-expandable without auto-opening',()=>{
  const script=compileScript(descriptor,{id:'historical-editorial'})
  assert.deepEqual(compileTemplate({id:'historical-editorial',source:descriptor.template.content,compilerOptions:{bindingMetadata:script.bindings}}).errors,[])
  assert.match(source,/<details :key="month">/)
  assert.doesNotMatch(source,/<details[^>]*\bopen\b/)
  assert.match(source,/旧版摘要（依据已变化，不作为当前结论）/)
  assert.match(source,/旧稿不计入本月摘要完成状态/)
  assert.match(source,/focus-visible/)
  assert.doesNotMatch(source,/v-html|fetch\(/)
  const parent=fs.readFileSync(new URL('../docs/.vitepress/theme/components/RadarDashboard.vue',import.meta.url),'utf8')
  const monthly=parent.slice(parent.indexOf('<template v-if="mode === \'monthly\'">'),parent.indexOf('<template v-if="mode === \'organizations\' || mode === \'collaboration\'">'))
  assert.match(monthly,/<HistoricalEditorial :key="monthlySnapshot\.month" :snapshot="monthlySnapshot"/)
})

test('raw monthly JSON and compact overview display the same historical five sections',()=>{
  const raw=snapshot(),before=structuredClone(raw)
  const a=harness(raw),b=harness(dashboardSnapshot(raw))
  assert.equal(a.groups.value.length,5)
  assert.deepEqual(JSON.parse(JSON.stringify(a.groups.value)),JSON.parse(JSON.stringify(b.groups.value)))
  assert.equal(a.previous.value.model,'gpt-5.6-sol')
  assert.equal(a.hasContent.value,true)
  assert.match(a.reason.value,/证据包已更新/)
  assert.deepEqual(Array.from(a.references(a.groups.value[0].rows[0])),['arxiv:2608.00001','arxiv:2608.00002'])
  assert.equal(raw.editorial_status,'data_only')
  assert.deepEqual(raw,before)
})

test('archive links bind the exact month and artifact digest and stay on site',()=>{
  const valid=harness()
  assert.equal(valid.archives.value[0].url,`/embodied-ai-radar/api/v1/editorial-history/2026-08/${artifactDigest}.json`)
  const base=history().archive_url
  const based=harness(snapshot({editorial_history:[history({archive_url:'/embodied-ai-radar'+base})]}))
  assert.equal(based.archives.value.length,1)
  for(const url of ['https://example.com'+base,'//example.com'+base,'javascript:alert(1)',base+'?token=secret',base+'#part',base.replace('2026-08','2026-07'),base.replace(artifactDigest,'c'.repeat(64)),base.replace('2026-08','%2e%2e')]) {
    const view=harness(snapshot({editorial_history:[history({archive_url:url})]}))
    assert.equal(view.archives.value.length,0,url)
  }
  assert.equal(harness(snapshot({editorial_history:[history(),history()]})).archives.value.length,1)
  assert.match(source,/:href="archive\.url" download/)
})

test('schema gaps, other-month prose and failed artifacts are not shown as valid old summaries',()=>{
  for(const extra of [{status:'failed'},{month:'2026-07'},{input_digest:'missing'},{generated_at:'unknown'},{model:null}]) {
    const view=harness(snapshot({previous_editorial:artifact(extra),editorial_history:[]}))
    assert.equal(view.previous.value,null)
    assert.equal(view.hasContent.value,false)
  }
  const historyOnly=harness(snapshot({previous_editorial:null}))
  assert.equal(historyOnly.groups.value.length,0)
  assert.equal(historyOnly.archives.value.length,1)
  assert.equal(historyOnly.hasContent.value,true)
})

test('archive download and input hash never imply that its original request packet survives',()=>{
  for(const [status,label] of [['available','原始请求证据包已留存'],
    ['missing_before_archive_feature','旧稿原始请求包未留存，不能完整重放'],
    [undefined,'请求包状态待核验'],['unexpected','请求包状态待核验']]) {
    const view=harness(snapshot({editorial_history:[history({input_packet_status:status})]}))
    assert.equal(view.archives.value.length,1)
    assert.equal(view.archives.value[0].input_digest,digest)
    assert.equal(view.archives.value[0].packet_status_label,label)
  }
  assert.match(source,/archive\.packet_status_label/)
})

test('no history means no fabricated warning; changing month never displays stale previous content',()=>{
  const empty=harness({month:'2026-08'})
  assert.equal(empty.hasContent.value,false)
  const view=harness();view.props.snapshot={...snapshot(),month:'2026-07',editorial_history:[]}
  assert.equal(view.hasContent.value,false)
  const bad=harness(snapshot({editorial_unavailable_reason:'/Users/private/key'}))
  assert.doesNotMatch(bad.reason.value,/Users/)
})
