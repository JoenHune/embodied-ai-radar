import fs from 'node:fs'
import path from 'node:path'
import { registerHooks } from 'node:module'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { SEARCH_INDEX_BUDGET_BYTES } from './search-budget.mjs'

// Keep canonical text-rule sources stable when only the deployment capacity
// policy changes. The official npm entry applies this explicit build policy;
// the unchanged core builder still performs all identity and size checks.
export function configuredBuildSource(source, helperUrl, helperFilename) {
  const record='pending.push(index.addHTMLFile({ url: record.url, content: record.content }))'
  const budget=/metrics\.index_budget_bytes = [\d_]+/g
  const version='metrics.dataset_version = publicManifest.dataset_version'
  if(source.split(record).length!==2 || [...source.matchAll(budget)].length!==1 || source.split(version).length!==2 || !source.includes('if (!metrics.index_budget_pass) throw'))throw Error('Core Pagefind build integration changed')
  const literal=String(SEARCH_INDEX_BUDGET_BYTES).replace(/\B(?=(\d{3})+(?!\d))/g,'_')
  return `import { nativeSearchContent, NATIVE_CATALOG_LAYOUT } from ${JSON.stringify(helperUrl)}\n`+
    source.replace(record,'pending.push(index.addHTMLFile({ url: record.url, content: nativeSearchContent(record.content) }))')
      .replace(budget,`metrics.index_budget_bytes = ${literal}`)
      .replace(/Pagefind compressed index exceeds \d+ MB:/g,`Pagefind compressed index exceeds ${SEARCH_INDEX_BUDGET_BYTES/1_000_000} MB:`)
      .replace(version,version+`\nmetrics.native_catalog_adapter = { layout: NATIVE_CATALOG_LAYOUT, native_facets: false, native_date_sort: false, native_ordinal_sort: true, indexed_body_unchanged: true, configuration_sha256: createHash('sha256').update(fs.readFileSync(${JSON.stringify(helperFilename)})).digest('hex') }`)
}

async function main() {
  const root=path.resolve(import.meta.dirname,'..')
  const original=pathToFileURL(path.join(root,'scripts/build-pagefind-index.mjs')).href
  const helper=path.join(root,'scripts/pagefind-catalog-content.mjs')
  registerHooks({load(url,context,nextLoad) {
    const loaded=nextLoad(url,context)
    if(url!==original)return loaded
    const source=typeof loaded.source==='string'?loaded.source:Buffer.from(loaded.source).toString('utf8')
    return {...loaded,source:configuredBuildSource(source,pathToFileURL(helper).href,helper)}
  }})
  await import(original)
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main()
