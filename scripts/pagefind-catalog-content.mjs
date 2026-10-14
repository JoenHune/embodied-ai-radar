// The deployed catalogue adapter owns facet filtering and calendar ordering.
// Pagefind supplies only weighted text matches and the ordinal identity map.
export const NATIVE_CATALOG_LAYOUT='catalog-facets-date-sort-v1'
export function nativeSearchContent(content) {
  const body=content.match(/<body data-pagefind-body>[\s\S]*?<\/body>/)?.[0]
  if(!body)throw Error('Virtual search record body missing')
  const result=content
    .replace(/<meta data-pagefind-filter="[^"<>]+\[content\]" content="[^"<>]*">/g,'')
    .replace(/<meta data-pagefind-sort="date\[content\]" content="[^"<>]*">/g,'')
  if(result.match(/<body data-pagefind-body>[\s\S]*?<\/body>/)?.[0]!==body)throw Error('Indexed search body changed')
  if(/data-pagefind-filter=|data-pagefind-sort="date\[/.test(result))throw Error('Unexpected native facet/date format')
  if(!result.includes('data-pagefind-sort="ordinal[content]"'))throw Error('Ordinal mapping sort missing')
  return result
}
