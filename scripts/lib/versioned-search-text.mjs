// Search-side equivalent of scripts/versioned_text.py. No IO or index writes.
import { createHash } from 'node:crypto'

const object = (value) => value !== null && typeof value === 'object' && !Array.isArray(value)
const sorted = (value) => Array.isArray(value) ? value.map(sorted) : object(value) ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, sorted(value[key])])) : value
export const textHash = (value) => createHash('sha256').update(JSON.stringify(sorted(value))).digest('hex')
export const sourceTextDigest = (work) => textHash({ title: work.title || '', abstract: work.abstract || '',
  ...(work.report_text?.status === 'available' ? {report_text_snapshots: work.report_text.snapshots.map(row => [row.snapshot_id,row.excerpt_digest]).sort((a,b)=>a[0].localeCompare(b[0]))} : {}) })
const unique = (values) => [...new Set(values.filter((value) => typeof value === 'string' && value))]

function utcDay(year, month, day) {
  if (year < 1) return null
  const value = new Date(0)
  value.setUTCFullYear(year, month - 1, day)
  value.setUTCHours(0, 0, 0, 0)
  return value.getUTCFullYear() === year && value.getUTCMonth() === month - 1 && value.getUTCDate() === day ? value.getTime() : null
}

// Microseconds preserve Python's inclusive 23:59:59.999999 boundary, including
// same-day versions. Modern radar dates use Shanghai UTC+08 (no DST since 1991).
export function availabilityUpper(value, precision) {
  if (typeof value !== 'string' || !value || precision === 'unknown') return null
  let match
  if ((match = /^(\d{4})-(\d{2})$/.exec(value)) || precision === 'month') {
    match ||= /^(\d{4})-(\d{2})/.exec(value)
    if (!match) return null
    const year = Number(match[1]), month = Number(match[2])
    if (year < 1 || month < 1 || month > 12) return null
    const next = month === 12 ? utcDay(year + 1, 1, 1) : utcDay(year, month + 1, 1)
    return BigInt(next - 8 * 60 * 60 * 1000) * 1000n - 1n
  }
  if ((match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value))) {
    const day = utcDay(Number(match[1]), Number(match[2]), Number(match[3]))
    return day === null ? null : BigInt(day + 16 * 60 * 60 * 1000) * 1000n - 1n
  }
  match = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?(Z|[+-]\d{2}:\d{2})$/.exec(value)
  if (!match) return null // Never assume a timezone for naive timestamps.
  const [, y, m, d, h, minute, s = '0', fraction = '', zone] = match
  const day = utcDay(Number(y), Number(m), Number(d))
  if (day === null || Number(h) > 23 || Number(minute) > 59 || Number(s) > 59) return null
  const offsetHours = zone === 'Z' ? 0 : Number(zone.slice(1, 3))
  const offsetMinutes = zone === 'Z' ? 0 : Number(zone.slice(4, 6))
  if (offsetHours > 23 || offsetMinutes > 59) return null
  const offset = (offsetHours * 60 + offsetMinutes) * (zone.startsWith('-') ? -1 : 1)
  return BigInt(day + ((Number(h) * 60 + Number(minute) - offset) * 60 + Number(s)) * 1000) * 1000n + BigInt(fraction.padEnd(6, '0') || '0')
}

export function validTextSnapshot(row, work) {
  const required = ['snapshot_id', 'work_id', 'source_record_id', 'version', 'title', 'abstract', 'authors', 'available_at', 'date_precision', 'source_url', 'content_digest', 'basis']
  if (!object(row) || required.some((key) => !(key in row)) || row.work_id !== work.work_id || !(work.source_record_ids || []).includes(row.source_record_id)) return false
  if (typeof row.title !== 'string' || !row.title.trim() || typeof row.abstract !== 'string' || !Array.isArray(row.authors) || row.authors.some((author) => typeof author !== 'string')) return false
  if (row.content_digest !== textHash({ title: row.title, abstract: row.abstract, authors: row.authors })) return false
  if (!['second', 'day', 'month', 'unknown'].includes(row.date_precision) || (row.available_at === null) !== (row.date_precision === 'unknown')) return false
  if (row.available_at !== null && availabilityUpper(row.available_at, row.date_precision) === null) return false
  return row.version === null || (typeof row.version === 'string' && /^v[1-9]\d*$/.test(row.version))
}

const versionNumber = (row) => Number((row.version || 'v0').slice(1))
export function textAsOf(work, snapshots, cutoff) {
  const until = availabilityUpper(cutoff)
  if (until === null) throw new Error('known_cutoff_required')
  const empty = { title: null, abstract: null, authors: [], source_ids: [], status: 'unavailable', available_at: null, version: null, snapshot_ids: [] }
  const valid = snapshots.filter((row) => validTextSnapshot(row, work))
  const eligible = valid.filter((row) => {
    const when = availabilityUpper(row.available_at, row.date_precision)
    return when !== null && when <= until
  })
  if (!eligible.length) {
    const future = valid.filter((row) => availabilityUpper(row.available_at, row.date_precision) !== null).map((row) => row.snapshot_id)
    return { ...empty, status: future.length ? 'retrospective_only' : 'unavailable', retrospective_snapshot_ids: future }
  }
  const known = eligible.filter((row) => row.version)
  const chosen = (known.length ? known : eligible).reduce((best, row) => {
    const difference = versionNumber(row) - versionNumber(best)
    return difference > 0 || (difference === 0 && availabilityUpper(row.available_at, row.date_precision) > availabilityUpper(best.available_at, best.date_precision)) ? row : best
  })
  const peers = eligible.filter((row) => row.version === chosen.version && availabilityUpper(row.available_at, row.date_precision) === availabilityUpper(chosen.available_at, chosen.date_precision))
  if (new Set(peers.map((row) => row.content_digest)).size > 1) return { ...empty, status: 'conflicting_snapshots', snapshot_ids: peers.map((row) => row.snapshot_id) }
  return { title: chosen.title, abstract: chosen.abstract, authors: [...chosen.authors], available_at: chosen.available_at, version: chosen.version, date_precision: chosen.date_precision,
    source_ids: unique(peers.map((row) => row.source_record_id)).sort(), snapshot_ids: unique(peers.map((row) => row.snapshot_id)).sort(), status: chosen.version ? 'available' : 'available_unversioned' }
}

export function isArxivWork(work) {
  return Boolean(work.identifiers?.arxiv || work.work_id?.startsWith('arxiv:') || work.aliases?.some((alias) => typeof alias === 'string' && alias.startsWith('arxiv:')))
}

function historicalLabels(work, snapshots, cutoff, selected) {
  const until = availabilityUpper(cutoff)
  const candidates = snapshots.filter((row) => validTextSnapshot(row, work) && availabilityUpper(row.available_at, row.date_precision) !== null && availabilityUpper(row.available_at, row.date_precision) <= until)
  const groups = new Map()
  for (const row of candidates) {
    const key = `${row.version || ''}:${availabilityUpper(row.available_at, row.date_precision)}`
    const values = groups.get(key) || []
    values.push(row)
    groups.set(key, values)
  }
  // A conflicting version is not a trustworthy title/author alias either.
  const unambiguous = [...groups.values()].filter((rows) => new Set(rows.map((row) => row.content_digest)).size === 1).flat()
  return { title_aliases: unique(unambiguous.map((row) => row.title)).filter((title) => title !== selected.title),
    author_aliases: unique(unambiguous.flatMap((row) => row.authors)).filter((name) => !selected.authors.includes(name)) }
}

export function localizationStatus(row, work, selectedSourceIds = work.source_record_ids || []) {
  if (!row || row.work_id !== work.work_id || !['title_zh', 'summary_zh'].every((key) => typeof row[key] === 'string' && row[key].trim())) return 'invalid'
  if (!row.source_content_digest) return 'legacy_source_review_required'
  if (row.source_content_digest !== sourceTextDigest(work)) return 'source_changed'
  if (!Array.isArray(row.source_ids) || !row.source_ids.length || !row.source_ids.every((id) => selectedSourceIds.includes(id))) return 'invalid_source'
  return 'current'
}

export function prepareSearchWork(work, { snapshots = [], dataThrough, localization, legacyNote, identityReviews = [], reportText } = {}) {
  if (availabilityUpper(dataThrough) === null) throw new Error('Search requires the same known data cutoff as the exported catalogue')
  const selected = isArxivWork(work) ? textAsOf(work, snapshots, dataThrough) : null
  let prepared = { ...work }
  delete prepared.report_text // A raw work cannot self-assert an audited report view.
  if (selected) {
    const available = ['available', 'available_unversioned'].includes(selected.status)
    const unversionedCatalog = snapshots.length === 0
    const historical = historicalLabels(work, snapshots, dataThrough, selected)
    const reviews = identityReviews.filter((review) => review.work_id === work.work_id && review.relation === 'merged_into' && review.review_id && availabilityUpper(review.reviewed_at) !== null)
    const registeredTitles = unique([work.title, ...(work.title_aliases || []), ...reviews.map((review) => review.prior_canonical_record?.title)])
    const title = available ? selected.title : work.title || work.work_id
    prepared = { ...prepared, title, abstract: available ? selected.abstract : unversionedCatalog ? work.abstract || '' : '', authors: available ? selected.authors : unversionedCatalog ? [...(work.authors || [])] : [],
      title_zh: '', summary_zh: '', keywords_zh: [], ...historical,
      title_aliases: unique([...historical.title_aliases, ...registeredTitles]).filter((value) => value !== title),
      historical_title_aliases: historical.title_aliases, registered_title_aliases: registeredTitles.filter((value) => value !== title),
      identifier_title: work.title || work.work_id, identifier_metadata_scope: 'latest_registered_names_not_historical_text',
      identifier_review_dates: unique(reviews.map((review) => review.reviewed_at)),
      identifier_publication_dates: unique(reviews.map((review) => {
        const old = review.prior_canonical_record
        return old?.first_public_date ? `${old.first_public_date} [${old.first_public_date_precision || 'unknown'}]` : null
      })),
      text_status: unversionedCatalog ? 'unversioned_catalog_text' : selected.status, text_version: selected.version, text_available_at: selected.available_at,
      text_version_status: unversionedCatalog ? 'version_not_verified' : available ? 'archived_text_selected' : selected.status,
      text_cutoff_applicability: unversionedCatalog ? 'not_applicable_unversioned_catalog_text' : available ? 'applied_to_selected_text' : 'blocked_no_available_text',
      text_snapshot_ids: selected.snapshot_ids, text_source_ids: selected.source_ids, title_is_current_identifier: !available,
      title_role: available ? 'selected_version_text' : unversionedCatalog ? 'unversioned_catalog_title' : 'latest_identifier_metadata' }
    // Current-canonical free-text hints have no version date. The selected
    // title/abstract carry any provable model names; avoid future name leakage.
    prepared.project_series = ''
    prepared.model_name = ''
  } else {
    if (!prepared.summary_zh && legacyNote) prepared.summary_zh = legacyNote.contribution_zh || ''
    prepared.text_status = 'non_arxiv_source_text'
    prepared.title_role = 'registered_source_title'
    prepared.text_version_status = 'not_arxiv_versioned'
    prepared.text_cutoff_applicability = 'not_applicable_non_arxiv_source_text'
    if (reportText) {
      if (reportText.as_of !== dataThrough || reportText.canonical_work_id !== work.work_id) throw new Error('report_search_cutoff_or_identity_mismatch')
      if (reportText.status === 'available') {
        const until = availabilityUpper(dataThrough)
        if (!reportText.snapshots?.length || reportText.snapshots.some(row => {
          const when = availabilityUpper(row.available_at,row.date_precision)
          const {snapshot_id,...original}=row
          return !(work.source_record_ids || []).includes(row.source_record_id) || when === null || when > until
            || row.excerpt_digest !== textHash(row.excerpts) || snapshot_id !== `report-text:${textHash(original).slice(0,24)}`
        })) throw new Error('report_search_snapshot_invalid')
        prepared.report_text=reportText
        prepared.abstract=''
        prepared.summary_zh='已保存报告历史短摘录；公司自报的数值与实验条件请查看详情。'
        prepared.title_zh=''
        prepared.keywords_zh=[]
        prepared.text_status='report_excerpt_available'
        prepared.text_cutoff_applicability='applied_to_report_excerpts'
        prepared.text_source_ids=unique(reportText.snapshots.map(row=>row.source_record_id)).sort()
      }
    }
  }
  const unversionedCatalog = prepared.text_status === 'unversioned_catalog_text'
  const status = (selected && !unversionedCatalog && !['available', 'available_unversioned'].includes(selected.status)) || (reportText && reportText.status !== 'available') ? 'historical_text_unavailable' : localizationStatus(localization, prepared, prepared.report_text ? prepared.text_source_ids : unversionedCatalog ? work.source_record_ids : selected?.source_ids)
  if (status === 'current') for (const key of ['title_zh', 'summary_zh', 'keywords_zh']) if (localization[key]) prepared[key] = Array.isArray(localization[key]) ? [...localization[key]] : localization[key]
  return { work: prepared, text: selected, localization_status: status }
}
