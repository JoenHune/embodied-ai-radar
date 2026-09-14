import { piModelQuery, searchText } from './search-text.mjs'

export type CatalogFilters = {
  q: string; from: string; to: string; direction: string; question: string; organization: string;
  outputType: string; evidence: string; relevance: string; venue: string; year: string; track: string;
  acceptance: string; publicationStatus: string; ids: string; peerReviewed: boolean; realRobot: boolean; openAssets: boolean;
}
export const defaultFilters = (): CatalogFilters => ({ q: '', from: '', to: '', direction: '', question: '', organization: '', outputType: '', evidence: '', relevance: 'included', venue: '', year: '', track: '', acceptance: '', publicationStatus: '', ids: '', peerReviewed: false, realRobot: false, openAssets: false })
const keys: Record<keyof CatalogFilters, string> = { q: 'q', from: 'from', to: 'to', direction: 'directions', question: 'questions', organization: 'organizations', outputType: 'output_types', evidence: 'evidence', relevance: 'relevance', venue: 'venue', year: 'year', track: 'track', acceptance: 'acceptance', publicationStatus: 'publication_status', ids: 'ids', peerReviewed: 'peer_reviewed', realRobot: 'real_robot', openAssets: 'open_assets' }
const booleans = new Set(['peerReviewed', 'realRobot', 'openAssets'])
export const splitValues = (value: string): string[] => [...new Set(value.split(',').map((item) => item.trim()).filter(Boolean))]

export function readSearchUrl(params: URLSearchParams) {
  const filters = defaultFilters()
  for (const [key, param] of Object.entries(keys)) {
    const value = params.get(param)
    if (value !== null) (filters as Record<string, string | boolean>)[key] = booleans.has(key) ? value === 'true' : value
  }
  // Evidence drilldowns must not silently drop candidate/manual-review records.
  if (filters.ids && !params.has('relevance')) filters.relevance = 'all'
  const page = Math.max(1, Number.parseInt(params.get('page') || '1', 10) || 1)
  return { filters, page, work: params.get('work') || '' }
}

export function writeSearchUrl(url: URL, filters: CatalogFilters, page: number, work: string): URL {
  const result = new URL(url)
  for (const [key, param] of Object.entries(keys)) {
    const value = filters[key as keyof CatalogFilters]
    if (value && !(key === 'relevance' && value === 'included' && !filters.ids)) result.searchParams.set(param, String(value))
    else result.searchParams.delete(param)
  }
  if (page > 1) result.searchParams.set('page', String(page)); else result.searchParams.delete('page')
  if (work) result.searchParams.set('work', work); else result.searchParams.delete('work')
  return result
}

export function searchOptions(filters: CatalogFilters, months: string[], publicationValues: string[], language = 'zh') {
  const selected: Record<string, string | { any: string[] }> = { record_type: 'work' }
  if (filters.relevance && filters.relevance !== 'all') selected.relevance = filters.relevance
  for (const [field, name] of [['direction', 'direction'], ['question', 'question'], ['organization', 'organization'], ['outputType', 'output_type'], ['evidence', 'evidence'], ['ids', 'work_id']] as const) {
    if (filters[field]) selected[name] = { any: splitValues(filters[field]) }
  }
  for (const [field, name] of [['peerReviewed', 'peer_reviewed'], ['realRobot', 'real_robot'], ['openAssets', 'open_assets']] as const) if (filters[field]) selected[name] = 'true'
  let empty = Boolean(filters.from && filters.to && filters.from > filters.to)
  if (filters.from || filters.to) {
    const matching = months.filter((month) => /^\d{4}-\d{2}$/.test(month) && (!filters.from || month >= filters.from) && (!filters.to || month <= filters.to))
    empty ||= !matching.length
    selected.month = { any: matching }
  }
  const publicationFilters = [filters.venue, filters.year, filters.track, filters.acceptance, filters.publicationStatus]
  if (publicationFilters.some(Boolean)) {
    // All venue constraints must match one manifestation, not different versions of the same work.
    const matching = publicationValues.filter((value) => {
      try { const tuple = JSON.parse(value); return Array.isArray(tuple) && publicationFilters.every((filter, index) => !filter || splitValues(filter).includes(tuple[index])) } catch { return false }
    })
    selected.publication = { any: matching }
    empty ||= !matching.length
  }
  let query: string | null = filters.q.normalize('NFKC').trim() || null
  let identifier = query?.toLowerCase().replace(/^https?:\/\/(?:dx\.)?doi\.org\//, '').replace(/^https?:\/\/arxiv\.org\/(abs|pdf)\//, '').replace(/^(doi|arxiv):/, '').replace(/\.pdf$/, '')
  if (identifier && /^\d{4}\.\d{4,5}v\d+$/.test(identifier)) identifier = identifier.replace(/v\d+$/, '')
  if (identifier && (/^10\.\d{4,9}\/.+/.test(identifier) || /^\d{4}\.\d{4,5}$/.test(identifier))) {
    selected.identifier = identifier
    query = null
  } else if (query && /^https?:\/\//i.test(query)) {
    selected.source_url = query.toLowerCase().replace(/\/$/, '')
    query = null
  } else if (query && /^[a-z][a-z0-9_-]*:[^\s]+$/i.test(query)) {
    selected.identifier = query.toLowerCase()
    query = null
  } else if (query && /^pi$/i.test(query)) {
    selected.identity = 'company:physical-intelligence'
    query = null
  } else if (query && piModelQuery(query)) {
    selected.identity = `model:${piModelQuery(query)}`
    query = null
  }
  const normalizedQuery = query ? searchText(query, true) : null
  return { empty: empty || Boolean(query && !normalizedQuery), query: normalizedQuery, filters: selected }
}

export type SearchLookup = { ids: string[]; work_ids: string[]; dates: string[]; identity_shards?: string[]; postings: Record<string, Record<string, number[]>> }
export function filterCatalog(lookup: SearchLookup, filters: Record<string, string | { any: string[] }>): Set<number> {
  let allowed: Set<number> | undefined
  for (const [name, value] of Object.entries(filters)) {
    if (name === 'record_type') continue
    const values = typeof value === 'string' ? [value] : value.any
    const matching = new Set(values.flatMap((item) => lookup.postings[name]?.[item] || []))
    allowed = allowed ? new Set([...allowed].filter((index) => matching.has(index))) : matching
  }
  return allowed || new Set(lookup.work_ids.map((_, index) => index))
}

export type ResultHandle = { id: string; data: () => Promise<any> }
export async function loadResultPage(handles: ResultHandle[], page: number, size = 20) {
  const count = Math.max(1, Math.ceil(handles.length / size))
  const actualPage = Math.min(count, Math.max(1, page))
  const slice = handles.slice((actualPage - 1) * size, actualPage * size)
  const rows = await Promise.all(slice.map(async (handle) => {
    const data = await handle.data()
    if (data.meta?.record_type !== 'work' || !data.meta?.work_id) throw new Error('索引含非研究记录，请重新构建数据库索引。')
    return { id: handle.id, url: data.url, excerpt: data.plain_excerpt || '', meta: data.meta }
  }))
  return { rows, page: actualPage, pageCount: count, total: handles.length }
}
