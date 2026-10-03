import test from 'node:test'
import assert from 'node:assert/strict'
import { emptyFilters, filterRows, sortRows, trendSeries, growthRanking, deviceSearch } from '../docs/.vitepress/theme/lib/hardware-explorer.mjs'
const match=(id,group='hands',extra={})=>({device_id:id,group,context_only:false,simulation:false,negation:false,usage_verified:false,...extra})
const row=(id,month,matches,citation=null)=>({id,title:id,date:month?month+'-01':null,month,process_state:'extracted_not_read',matches,citation})
test('facets OR within and AND across; no inferred internal hardware',()=>{
 const rows=[row('hand','2026-01',[match('hand')]),row('platform','2026-01',[match('g1','platform')]),row('two','2026-01',[match('hand'),match('cpu','compute')])]
 assert.deepEqual(filterRows(rows,{...emptyFilters(),devices:['hand','cpu']}).map(r=>r.id),['hand','two'])
 assert.deepEqual(filterRows(rows,{...emptyFilters(),categories:['compute'],devices:['hand']}).map(r=>r.id),[])
 assert.deepEqual(filterRows(rows,{...emptyFilters(),categories:['hands']}).map(r=>r.id),['hand','two'])
 assert.equal(filterRows(rows,{...emptyFilters(),evidence:'verified'}).length,0)
})
test('aliases searchable without merging neighboring model IDs',()=>{
 assert.ok(deviceSearch({name:'Universal Robots UR5e',aliases:['UR5e']},'UR5e'))
 assert.ok(!deviceSearch({name:'Universal Robots UR5',aliases:['UR5']},'UR5e'))
 assert.ok(deviceSearch({name:'Intel RealSense D435i',aliases:['D435i']},'D435i'))
})
test('known zero and missing citation differ; every sort has stable ties and unknown dates last',()=>{
 const rows=[row('unknown',null,[],null),row('zero','2026-01',[],{count:0}),row('high','2025-01',[],{count:9}),row('missing','2026-05',[],null)]
 assert.deepEqual(sortRows(rows,'citations').map(r=>r.id),['high','zero','missing','unknown'])
 assert.equal(sortRows(rows,'oldest').at(-1).id,'unknown')
 const ties=[row('b','2026-01',[]),row('a','2026-01',[])];assert.deepEqual(sortRows(ties,'recent').map(r=>r.id),['a','b'])
})
test('unique paper numerator; fixed entire analyzed denominator excludes unknown dates',()=>{
 const data={catalog_months:{'2026-01':10,'2026-02':10},rows:[row('a','2026-01',[match('h'),match('h'),match('cpu','compute')]),row('b','2026-01',[]),row('unknown',null,[match('h')])]}
 const series=trendSeries(data,{...emptyFilters(),devices:['h']},'month')
 assert.deepEqual(series[0],{period:'2026-01',count:1,analyzed:2,catalog:10,share:.5,coverage:.2})
 assert.equal(series[1].share,null)
 assert.equal(filterRows(data.rows,{...emptyFilters(),devices:['h']}).length,2)
 assert.equal(trendSeries(data,{...emptyFilters(),devices:['h','cpu']},'month')[0].count,1)
})
test('growth excludes incomplete quarter, requires coverage/sample; zero base is new not infinite',()=>{
 const rows=[];for(let i=0;i<10;i++){rows.push(row('a'+i,'2026-01',i<5?[match('h')]:[]));rows.push(row('b'+i,'2026-04',i<5?[match('new')]:[]));rows.push(row('c'+i,'2026-07',[match('new')]))}
 const data={data_through:'2026-08-31',catalog_months:{'2026-01':10,'2026-04':10,'2026-07':10},devices:[{id:'h',group:'hands'},{id:'new',group:'hands'}],rows}
 const ranking=growthRanking(data,emptyFilters())
 assert.deepEqual(ranking.periods,['2026 Q1','2026 Q2']);assert.equal(ranking.rows.find(r=>r.id==='new').growth,null)
 assert.equal(ranking.rows.find(r=>r.id==='new').count,5)
 data.catalog_months['2026-01']=100;assert.equal(growthRanking(data,emptyFilters()).rows.length,0)
})
test('pagination input changes yield stable slices and empty/reset scopes',()=>{
 const rows=Array.from({length:25},(_,i)=>row('w'+String(i).padStart(2,'0'),'2026-01',[match('h')]))
 const result=sortRows(filterRows(rows,emptyFilters()),'recent');assert.equal(result.slice(12,24).length,12)
 assert.equal(filterRows(rows,{...emptyFilters(),query:'never-existing-title'}).length,0)
 assert.equal(filterRows(rows,emptyFilters()).length,25)
})
test('clipped quarters cannot masquerade as equal complete periods',()=>{
 const data={data_through:'2026-08-31',catalog_months:{'2026-02':1,'2026-03':1,'2026-04':1,'2026-05':1,'2026-06':1},devices:[],rows:[]}
 assert.deepEqual(growthRanking(data,{...emptyFilters(),from:'2026-02'}).periods,['2026 Q2'])
})
