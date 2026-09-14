import { createHash } from 'node:crypto'
import { normalizeSearchBoundaries, piModelNames, searchText } from '../../docs/.vitepress/theme/lib/search-text.mjs'
import { isArxivWork, prepareSearchWork } from './versioned-search-text.mjs'
import { originalSourceUrl } from '../../docs/.vitepress/theme/lib/research-card.mjs'
import { publicationRecords } from '../../docs/.vitepress/theme/lib/work-status.mjs'
import { compactSourceConflicts } from '../../docs/.vitepress/theme/lib/source-conflicts.mjs'

export const SEARCH_DICTIONARY_VERSION = '3.4.0'
const CARD_META_KEYS = new Set(['title', 'title_zh', 'work_id', 'date', 'date_precision', 'direction', 'evidence', 'relevance', 'peer_reviewed', 'summary', 'organizations', 'output_types', 'venues', 'shard', 'record_type', 'text_status', 'text_version', 'text_available_at', 'text_cutoff', 'text_version_status', 'text_cutoff_applicability', 'title_role', 'localization_status', 'publication_metadata_scope', 'research_status', 'research_validation_eligible', 'research_status_as_of', 'original_url'])
CARD_META_KEYS.add('publication_records')
CARD_META_KEYS.add('research_status_notices')
CARD_META_KEYS.add('source_conflicts')
export function compactResultCard(row) {
  // Empty-query browse pages repeat all/status lists. Keep all visible card
  // fields, but don't duplicate full author/version arrays already available
  // in result shards and canonical detail APIs. No indexed text is removed.
  return { ...row, meta: Object.fromEntries(Object.entries(row.meta).filter(([key]) => CARD_META_KEYS.has(key))) }
}
const terms = {
  D1: ['VLA', 'vision language action', '视觉语言动作', '具身基础模型'],
  D2: ['大小脑', '快慢系统', 'fast slow', 'system 1 system 2', '分层推理'],
  D3: ['世界模型', 'world model', '预测控制', 'action conditioned video'],
  D4: ['灵巧操作', 'dexterous manipulation', '双臂', '接触操作'],
  D5: ['人形机器人', 'humanoid', 'locomotion', '全身控制'],
  D6: ['导航', 'navigation', '移动操作', 'mobile manipulation'],
  D7: ['人机协作', 'human robot interaction', '交互学习'],
  D8: ['策略学习', 'policy learning', 'diffusion policy', 'flow policy'],
  D9: ['人类视频', 'human video', '数据引擎', 'egocentric'],
  D10: ['仿真', 'simulation', 'sim-to-real', '合成数据'],
  D11: ['空间感知', 'spatial perception', '三维表征'],
  D12: ['评测', 'evaluation', '安全', 'safety', '故障恢复'],
  D13: ['持续学习', 'continual learning', '部署学习', '自改进'],
  D14: ['多机器人', 'multi-robot', '群体智能'],
  D15: ['触觉', '力觉', 'tactile', 'visuotactile'],
}
const strings = (value) => value == null ? [] : typeof value === 'string' || typeof value === 'number' ? [String(value)] : Array.isArray(value) ? value.flatMap(strings) : Object.values(value).flatMap(strings)
const unique = (values) => [...new Set(strings(values).filter(Boolean))]
const normalize = (value) => String(value ?? '').normalize('NFKC')
const escape = (value) => normalize(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;')
const normalizedIdentifier = (value) => {
  const result = normalize(value).toLowerCase().replace(/^https?:\/\/(?:dx\.)?doi\.org\//, '').replace(/^(doi|arxiv):/, '')
  return /^\d{4}\.\d{4,5}v\d+$/.test(result) ? result.replace(/v\d+$/, '') : result
}
const assetTerms = (value) => unique(value).flatMap((text) => {
  if (!/^https?:\/\//.test(text)) return [text]
  try {
    const url = new URL(text)
    return [url.hostname.replace(/^(www|github|huggingface)\./, ''), ...decodeURIComponent(url.pathname).split('/')].filter((part) => part && !/^[\d._-]+$/.test(part) && !['abs', 'pdf', 'html', 'document', 'doi'].includes(part))
  } catch { return [] }
})
export function indexAbstractText(value, alreadyIndexed = []) {
  // Normalize separators before removing repeats: never turn Cross-embodiment
  // into -embodiment. Numeric-leading tokens such as 3D also remain atomic.
  // Keep mixed-Unicode, apostrophe and dotted compounds intact rather than
  // deleting an ASCII fragment from an otherwise unnormalized word.
  const token = /(?<![\p{L}\p{N}.'’])[A-Za-z0-9]*[A-Za-z][A-Za-z0-9]*(?![\p{L}\p{N}'’]|\.[\p{L}\p{N}])/gu
  const seen = new Set(strings(alreadyIndexed).flatMap((text) => normalizeSearchBoundaries(text).match(token) || []).map((word) => word.toLowerCase()))
  return normalizeSearchBoundaries(value).replace(token, (word) => {
    const key = word.toLowerCase()
    if (seen.has(key)) return ' '
    seen.add(key)
    return word
  })
}

export function identityAliases(work, organizationIds = []) {
  const aliases = []
  if (organizationIds.includes('org:physical-intelligence')) aliases.push('PI', 'Physical Intelligence')
  const models = piModelNames([work.title, work.project_series, work.model_name].filter(Boolean).join(' '))
  if (models.length) aliases.push('π0', 'pi0', 'pi-0')
  for (const model of models) aliases.push(model.replace(/^pi/, 'π'), model, model.replace(/^pi/, 'pi-'))
  return [...new Set(aliases)]
}

export function publicationTuple(row) {
  const verified = row.peer_reviewed === true
  const status = row.publication_status || (verified ? 'published' : row.status === 'accepted' || row.accepted_at ? 'accepted' : row.kind === 'preprint' ? 'preprint' : row.status || 'unknown')
  const acceptance = row.acceptance_status || (verified || row.accepted_at || row.status === 'accepted' ? 'accepted' : 'unknown')
  return [String(row.venue || 'unknown'), String(row.year || row.published_at?.slice(0, 4) || 'unknown'), String(row.track || 'unknown'), String(acceptance), String(status)]
}

export function workSearchRecord(work, { manifestations = [], organizationIds = [], organizationNames = [], organizationDisplayNames, base = '/', explicitChinese = true, ordinal = 0, dataThrough, snapshots = [], localization, legacyNote, identityReviews = [], reportText } = {}) {
  let localizationState = 'not_checked'
  if (dataThrough !== undefined) {
    const prepared = prepareSearchWork(work, { dataThrough, snapshots, localization, legacyNote, identityReviews, reportText })
    work = prepared.work
    localizationState = prepared.localization_status
    if (isArxivWork(work)) {
      const provenTitles = new Set([work.title, ...(work.title_aliases || [])])
      // Publication metadata is the latest registered knowledge, not capped by
      // the arXiv corpus coverage date. Later CoRL acceptance remains searchable.
      // Only preprint titles need the selected version's text-date guarantee.
      manifestations = manifestations.map((row) => ({ ...row, title: row.kind === 'preprint' && !provenTitles.has(row.title) ? '' : row.title }))
    }
  }
  const datedMonth = !['year', 'unknown'].includes(work.first_public_date_precision) && /^\d{4}-\d{2}/.test(work.first_public_date || '') ? work.first_public_date.slice(0, 7) : 'unknown'
  const outputTypes = unique(manifestations.map((row) => row.kind))
  const publications = manifestations.map(publicationTuple)
  const displayByOrganization = new Map()
  for (const [index, name] of (organizationDisplayNames ?? organizationNames).entries()) {
    const id = organizationIds[index] || name
    if (name && !displayByOrganization.has(id)) displayByOrganization.set(id, name)
  }
  const shard = createHash('sha1').update(work.work_id).digest('hex').slice(0, 2)
  const aliases = unique([...(work.directions || []).flatMap((code) => terms[code] || []), ...identityAliases(work, organizationIds)])
  const assets = assetTerms([work.repositories, work.urls, manifestations.map((row) => row.url)])
  const publicationText = manifestations.map((row) => [row.title, row.venue, row.year, row.project_series])
  const fields = [
    [8, unique([work.title, work.title_zh]), work.title_role || 'registered_source_title'],
    [5, unique([work.project_series, work.model_name, ...identityAliases(work, organizationIds)])],
    [3, unique([work.authors, organizationNames, work.keywords_zh])],
    [1.5, unique([work.title_aliases, work.author_aliases]), 'identity_aliases_not_experimental_body'],
    [2, unique([work.summary_zh, work.facets, work.directions, work.questions])],
    [1, unique([assets, publicationText, outputTypes, work.report_text?.snapshots?.flatMap(row=>row.excerpts.map(excerpt=>excerpt.text))])],
  ]
  // Full title/author phrases and their weights remain untouched. The abstract
  // need not repeat an English word already emitted by another actual body
  // field; filter-only metadata is deliberately NOT used as a substitute.
  // Keep English abstract words at weight 1 when their only other occurrence
  // is a 0.5-weight taxonomy synonym. Compact that synonym below instead.
  const abstractText = indexAbstractText(work.abstract, fields.flatMap(([, values]) => values))
  fields[fields.length - 1][1].unshift(abstractText)
  // This second pass removes duplicate low-weight English synonyms (including
  // repetitions inside the synonym bank), never any Chinese or title labels.
  fields.push([0.5, [indexAbstractText(aliases.join('\n'), fields.flatMap(([, values]) => values))]])
  const withUnknown = (values) => values.length ? unique(values) : ['unknown']
  const filters = {
    record_type: ['work'], work_id: unique([work.work_id, work.aliases]), relevance: [work.relevance?.status || 'manual_review'],
    identifier: unique([work.work_id, work.identifiers, work.aliases]).map(normalizedIdentifier),
    source_url: unique([work.repositories, work.urls, manifestations.map((row) => row.url), work.report_text?.snapshots?.map(row=>row.source_url)]).filter((value) => /^https?:\/\//.test(value)).map((value) => value.toLowerCase().replace(/\/$/, '')),
    identity: [...(organizationIds.includes('org:physical-intelligence') ? ['company:physical-intelligence'] : []), ...identityAliases(work).filter((alias) => /^pi0(?:\.\d+)?$/.test(alias)).map((alias) => `model:${alias}`)],
    direction: withUnknown(work.directions || []), question: withUnknown(work.questions || []),
    organization: organizationIds.length ? organizationIds : ['unattributed'], output_type: withUnknown(outputTypes),
    evidence: [work.evidence_grade || 'E0'], peer_reviewed: [String(work.strict_peer_reviewed === true)],
    real_robot: [String(work.evidence_flags?.real_robot === true)],
    open_assets: [String(Boolean(work.evidence_flags?.open_code || work.evidence_flags?.open_data || work.evidence_flags?.open_model))],
    month: [datedMonth],
    venue: withUnknown(publications.map((row) => row[0])), year: withUnknown(publications.map((row) => row[1])),
    track: withUnknown(publications.map((row) => row[2])), acceptance: withUnknown(publications.map((row) => row[3])),
    publication_status: withUnknown(publications.map((row) => row[4])),
    publication: withUnknown(publications.map((row) => JSON.stringify(row))),
  }
  const publicationDetails = publicationRecords(work, manifestations)
  const meta = {
    ...(work.source_conflicts?.length ? { source_conflicts: JSON.stringify(compactSourceConflicts(work.source_conflicts)) } : {}),
    ...(publicationDetails.length ? { publication_records: JSON.stringify(publicationDetails) } : {}),
    ...(work.research_status?.notices?.length ? { research_status_notices: JSON.stringify(work.research_status.notices.map(({ event_type, public_at, date_precision, summary_zh, source_url }) => ({ event_type, public_at, date_precision, summary_zh, source_url }))) } : {}),
    original_url: originalSourceUrl(work, manifestations),
    ...(work.research_status?.notices?.length ? { research_status: work.research_status.status, research_validation_eligible: String(work.research_status.validation_eligible !== false), research_status_as_of: work.research_status_as_of || work.research_status.as_of || '' } : {}),
    title: work.title, title_zh: work.title_zh || '', work_id: work.work_id, date: work.first_public_date || '',
    date_precision: work.first_public_date_precision || 'day',
    direction: work.primary_direction || '', evidence: work.evidence_grade || 'E0', relevance: work.relevance?.status || 'manual_review',
    peer_reviewed: String(work.strict_peer_reviewed === true), summary: work.summary_zh || '', organizations: [...displayByOrganization.values()].join(' · '),
    output_types: outputTypes.join(' · '), venues: unique(publications.map((row) => row[0])).filter((venue) => venue.trim().toLowerCase() !== 'unknown').join(' · '), shard, record_type: 'work',
    text_status: work.text_status || 'not_version_selected', text_version: work.text_version || '', text_available_at: work.text_available_at || '',
    text_version_status: work.text_version_status || 'not_version_selected', text_cutoff_applicability: work.text_cutoff_applicability || 'not_requested',
    authors: unique(work.authors).join(' · '), localization_status: localizationState,
    title_role: work.title_role || 'registered_source_title', identifier_title: work.identifier_title || work.title,
    identifier_metadata_scope: work.identifier_metadata_scope || 'registered_source_title',
    identifier_review_dates: unique(work.identifier_review_dates).join(' · '), identifier_publication_dates: unique(work.identifier_publication_dates).join(' · '),
    text_cutoff: dataThrough || '', publication_metadata_scope: 'latest_registered',
    publication_dates: unique(manifestations.flatMap((row) => [row.accepted_at && `accepted:${row.accepted_at} [${row.accepted_date_precision || row.date_precision || 'unknown'}]`, (row.public_at || row.published_at) && `published:${row.public_at || row.published_at} [${row.date_precision || 'unknown'}]`])).join(' · '),
  }
  const sort = { date: (work.first_public_date || '0000-00-00').replaceAll('-', ''), ordinal: String(ordinal) }
  const attributes = [
    ...Object.entries(meta).map(([key, value]) => `<meta data-pagefind-meta="${key}[content]" content="${escape(value)}">`),
    ...Object.entries(filters).flatMap(([key, values]) => values.map((value) => `<meta data-pagefind-filter="${key}[content]" content="${escape(value)}">`)),
    ...Object.entries(sort).map(([key, value]) => `<meta data-pagefind-sort="${key}[content]" content="${escape(value)}">`),
  ].join('')
  return {
    url: `${base.replace(/\/?$/, '/')}database/?work=${encodeURIComponent(work.work_id)}`,
    content: `<html lang="${explicitChinese ? 'en' : 'zh'}"><head>${attributes}</head><body data-pagefind-body>${fields.map(([weight, values, role = 'search_context']) => `<p data-pagefind-weight="${weight}" data-radar-field-role="${role}">${values.map((value) => escape(searchText(value, explicitChinese))).join('\n')}</p>`).join('')}</body></html>`,
    filters, meta, excerpt: work.summary_zh || work.abstract?.slice(0, 260) || '',
    index_info: { historical_title_aliases: unique(work.historical_title_aliases || work.title_aliases).length, historical_author_aliases: unique(work.author_aliases).length, registered_title_aliases: unique(work.registered_title_aliases).length },
  }
}
