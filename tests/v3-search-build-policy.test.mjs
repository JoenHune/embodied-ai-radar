import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import { SEARCH_INDEX_BUDGET_BYTES } from '../scripts/search-budget.mjs'
import { configuredBuildSource } from '../scripts/build-pagefind-policy.mjs'
const original=fs.readFileSync(new URL('../scripts/build-pagefind-index.mjs',import.meta.url),'utf8')
const source=configuredBuildSource(original,'file:///fixture/helper.mjs','/fixture/helper.mjs')
const gate=source.slice(source.indexOf('metrics.index_budget_bytes ='))
function check(bytes){
 const metrics={index_gzip_bytes:bytes}
 vm.runInNewContext(gate,{metrics,fs:{writeFileSync(){}},path:{join(){return '/fixture/metrics'}},output:'',process:{stdout:{write(){}}}})
 return metrics
}
test('the official builder uses the temporary decimal 22 MB ship gate',()=>{
 assert.equal(SEARCH_INDEX_BUDGET_BYTES,22_000_000)
 assert.match(source,/index_budget_bytes = 22_000_000/)
 assert.match(source,/nativeSearchContent\(record\.content\)/)
 assert.match(source,/if \(!metrics\.index_budget_pass\) throw/)
})
test('the verified full corpus passes the actual builder gate',()=>assert.equal(check(20_228_485).index_budget_pass,true))
test('the measured 2026-10-23 index passes and one byte past the temporary gate still fails',()=>{
 assert.equal(check(21_841_424).index_budget_pass,true)
 assert.equal(check(22_000_000).index_budget_pass,true)
 assert.throws(()=>check(22_000_001),/exceeds 22 MB: 22000001 bytes/)
})
test('an unexpected builder cannot silently bypass identity or size integration',()=>{
 assert.throws(()=>configuredBuildSource(original.replace('if (!metrics.index_budget_pass) throw','if (false) throw'),'file:///fixture/helper','/fixture/helper'),/integration changed/)
})
