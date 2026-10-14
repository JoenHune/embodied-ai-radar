import test from 'node:test'
import assert from 'node:assert/strict'
import * as pagefind from 'pagefind'
import { gzipSync } from 'node:zlib'
import { workSearchRecord } from '../scripts/lib/search-records.mjs'
import { nativeSearchContent } from '../scripts/pagefind-catalog-content.mjs'
import { defaultFilters, searchOptions, filterCatalog, loadResultPage } from '../docs/.vitepress/theme/lib/catalog-search.ts'

test('projection preserves the entire body, display metadata and ordinal sort',()=>{
 const record=workSearchRecord({work_id:'work:fixture',title:'Complete title phrase',abstract:'Complete abstract phrase',authors:['Complete Author'],first_public_date:'2026-09-02'})
 const compact=nativeSearchContent(record.content)
 assert.equal(compact.match(/<body[\s\S]*<\/body>/)[0],record.content.match(/<body[\s\S]*<\/body>/)[0])
 assert.deepEqual([...compact.matchAll(/<meta data-pagefind-meta=[^>]+>/g)].map(x=>x[0]),[...record.content.matchAll(/<meta data-pagefind-meta=[^>]+>/g)].map(x=>x[0]))
 assert.match(compact,/data-pagefind-sort="ordinal\[content\]"/)
 assert.doesNotMatch(compact,/data-pagefind-filter=|data-pagefind-sort="date\[/)
})

for(const language of ['zh','en'])test(`real ${language} WASM preserves queries, adapter facets, dates and pagination`,async t=>{
 const make=(id,fields={})=>({work_id:id,title:`Robot ${id}`,abstract:'Original robotics experiment description.',directions:['D8'],relevance:{status:'included'},first_public_date:'2026-08-01',...fields})
 const inputs=[
  [make('work:world',{title:'机器人世界模型的研究',directions:['D3'],first_public_date:'2026-09-01'}),{}],
  [make('work:cross',{title:'Cross-embodiment title phrase',abstract:'Uniqueabstractneedle cross-embodiment',authors:['Originalauthorneedle'],identifiers:{doi:'10.1234/fixture'},first_public_date:'2026-09-02'}),{}],
  [make('arxiv:2410.24164',{title:'π0: Vision-Language-Action Model',directions:['D1']}),{organizationIds:['org:physical-intelligence'],organizationNames:['Physical Intelligence']}],
  [make('arxiv:2504.16054',{title:'π0.5: Open-World Generalization',directions:['D1']}),{}],
  [make('work:excluded',{title:'Excludedneedle',relevance:{status:'excluded'}}),{}],
  [make('work:publication'),{manifestations:[{venue:'CoRL',year:2025,track:'main',kind:'conference',peer_reviewed:true},{venue:'ICRA',year:2026,track:'main',kind:'conference',peer_reviewed:true}]}],
  [make('work:undated',{first_public_date:'2026-01-01',first_public_date_precision:'year'}),{}],
 ]
 for(let n=0;n<603;n++)inputs.push([make(`bulk:${n}`,{first_public_date:`2026-08-${String(1+n%28).padStart(2,'0')}`}),{}])
 const records=inputs.map(([w,c],ordinal)=>workSearchRecord(w,{...c,ordinal,explicitChinese:true}))
 const postings={}
 for(const [position,r] of records.entries())for(const [name,values] of Object.entries(r.filters))for(const v of new Set(values)){
  (postings[name] ||= {})[v] ||= [];postings[name][v].push(position)
 }
 const months=Object.keys(postings.month),publications=Object.keys(postings.publication)
 async function build(projected){
  const {index,errors}=await pagefind.createIndex({forceLanguage:language,includeCharacters:'π'});assert.deepEqual(errors,[])
  try{
   for(const r of records)assert.deepEqual((await index.addHTMLFile({url:r.url,content:projected?nativeSearchContent(r.content):r.content})).errors,[])
   const {files,errors}=await index.getFiles();assert.deepEqual(errors,[]);return new Map(files.map(f=>[f.path,f.content]))
  }finally{await pagefind.close()}
 }
 const maps=[await build(false),await build(true)];const snapshots=[];const previousFetch=globalThis.fetch
 try{
  for(const [mode,files] of maps.entries()){
   globalThis.fetch=async input=>{const key=String(input).split('/pagefind/').at(-1).split('?')[0];const b=files.get(key);if(!b)throw Error(`Missing fixture asset: ${key}`);return new Response(b)}
   const engine=await import(`data:text/javascript;base64,${Buffer.from(files.get('pagefind.js')).toString('base64')}#native-adapter-${language}-${mode}`)
   await engine.options({bundlePath:'/pagefind/',language});await engine.init()
   const ordered=await engine.search(null,{sort:{ordinal:'asc'}})
   const orderedWorkIds=await Promise.all(ordered.results.map(async r=>(await r.data()).meta.work_id))
   assert.deepEqual(orderedWorkIds,records.map(r=>r.meta.work_id))
   const lookup={ids:ordered.results.map(r=>r.id),work_ids:orderedWorkIds,dates:records.map(r=>r.meta.date),postings}
   const positions=new Map(lookup.ids.map((id,i)=>[id,i]));const scenarios=[]
   const variations=[
    {q:'世界模型'},{q:'cross-embodiment'},{q:'Uniqueabstractneedle'},{q:'Originalauthorneedle'},
    {q:'π0'},{q:'pi0.5'},{q:'10.1234/fixture'},{q:'Excludedneedle',relevance:'all'},
    {q:'',from:'2026-09',to:'2026-09'},{q:'Robot',direction:'D8',from:'2026-08',to:'2026-08'},
    {q:'Robot',venue:'CoRL',year:'2025'},{q:'Robot',venue:'CoRL',year:'2026'},
    {q:'',organization:'org:physical-intelligence'},{q:'',ids:'work:excluded',relevance:'all'},
    {q:'',from:'2026-09',to:'2026-08'},{q:'',relevance:'all'},
   ]
   for(const v of variations){
    const config=searchOptions({...defaultFilters(),...v},months,publications,language)
    const allowed=filterCatalog(lookup,config.filters)
    let ids=config.empty?[]:config.query?(await engine.search(config.query)).results.map(r=>positions.get(r.id)).filter(i=>allowed.has(i)):[...allowed]
    if(!config.query)ids.sort((a,b)=>lookup.dates[b].localeCompare(lookup.dates[a])||lookup.work_ids[a].localeCompare(lookup.work_ids[b]))
    scenarios.push(ids.map(i=>lookup.work_ids[i]))
   }
   const all=filterCatalog(lookup,searchOptions({...defaultFilters(),relevance:'all'},months,publications).filters)
   const dateAsc=[...all].sort((a,b)=>lookup.dates[a].localeCompare(lookup.dates[b])||lookup.work_ids[a].localeCompare(lookup.work_ids[b])).map(i=>lookup.work_ids[i])
   const page=await loadResultPage([...all].map(i=>({id:lookup.ids[i],data:async()=>({meta:records[i].meta})})),26)
   assert.equal(page.rows.length,20)
   snapshots.push({scenarios,dateAsc,pageIds:page.rows.map(r=>r.meta.work_id),total:page.total})
  }
  assert.deepEqual(snapshots[1],snapshots[0])
  assert.deepEqual(snapshots[1].scenarios[0],['work:world']);assert.deepEqual(snapshots[1].scenarios[6],['work:cross'])
  assert.deepEqual(snapshots[1].scenarios[11],[])
  const sizes=maps.map(files=>[...files].filter(([name])=>!name.startsWith('filter/')&&!name.startsWith('fragment/')).reduce((n,[,b])=>n+gzipSync(b).length,0))
  t.diagnostic(JSON.stringify({fixture_works:records.length,scenarios:16,original_gzip_bytes:sizes[0],projected_gzip_bytes:sizes[1],full_body_preserved:true,query_order_filter_dates_and_page_26_equal:true}))
 }finally{globalThis.fetch=previousFetch}
})
