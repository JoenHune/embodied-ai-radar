const publicationKinds = new Set(['conference', 'journal', 'peer_reviewed_paper'])
const safeUrl = value => {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : '' } catch { return '' }
}
const readArray = value => { try { const rows = typeof value === 'string' ? JSON.parse(value) : value; return Array.isArray(rows) ? rows : [] } catch { return [] } }

export function venueLabel(venue, year, kind) {
  const raw = String(venue || '').trim()
  if (!raw || /^(unknown|arxiv|n\/a)$/i.test(raw)) return ''
  const normalized = { 'T-RO': 'TRO', 'IEEE Transactions on Robotics': 'TRO', 'Science Robotics': 'Science Robotics', 'RA-L': 'RA-L', 'IEEE Robotics and Automation Letters': 'RA-L' }[raw] || raw
  const validYear = /^20\d{2}$/.test(String(year || '')) ? String(year) : ''
  return validYear ? kind === 'conference' ? `${normalized}'${validYear.slice(-2)}` : `${normalized} · ${validYear}` : normalized
}

export function publicationRecords(work, manifestations = work.manifestations || []) {
  if (!manifestations.length && work.publication_records) return readArray(work.publication_records)
    .filter(row => row && typeof row.venue === 'string' && typeof row.state === 'string' && safeUrl(row.url))
    .map(row => ({ ...row, url: safeUrl(row.url) }))
  const records = []
  for (const row of manifestations) {
    if (!publicationKinds.has(row.kind)) continue
    const baseVenue = venueLabel(row.venue, row.year, row.kind)
    const venue = baseVenue && /workshop/i.test(row.track || '') ? `${baseVenue} · Workshop` : baseVenue
    const url = safeUrl(row.url)
    if (!venue || !url) continue
    let state, rank
    const officialAccepted = ['official_accepted_pending_proceedings', 'peer_reviewed_official_acceptance', 'accepted_peer_reviewed', 'official_accepted'].includes(row.status)
    if (row.peer_reviewed === true && ['published_proceedings', 'published', 'published_journal'].includes(row.publication_status)) { state = '已正式出版'; rank = 4 }
    else if (officialAccepted || row.peer_reviewed === true && (row.acceptance_status === 'accepted' || row.publication_status === 'accepted')) { state = '已接收'; rank = 3 }
    else if (row.status === 'official_program_only') { state = '官方会议程序收录'; rank = 2 }
    else if (row.peer_reviewed === true) { state = '正式评审已核验，出版进度待核验'; rank = 3 }
    else { state = '发表信息待官方核验'; rank = 1 }
    const accepted = state === '已接收'
    records.push({ venue, state, url, date: accepted ? row.accepted_at || null : rank === 4 ? row.public_at || row.published_at || null : null,
      date_precision: accepted ? row.accepted_date_precision || 'unknown' : row.date_precision || 'unknown',
      peer_reviewed: row.peer_reviewed === true, rank })
  }
  // Show the strongest supported state per venue edition, not a DOI-based guess.
  const unique = new Map()
  for (const record of records) if (!unique.has(record.venue) || unique.get(record.venue).rank < record.rank) unique.set(record.venue, record)
  return [...unique.values()].sort((a, b) => b.rank - a.rank || a.venue.localeCompare(b.venue)).map(({ rank, ...record }) => record)
}

const noticeLabels = { withdrawn: '作者撤回', retracted: '撤稿', corrected: '更正', expression_of_concern: '关注声明', reinstated: '恢复' }
export function statusNotices(work) {
  const status = work.research_status
  const notices = readArray(status?.notices).filter(row => noticeLabels[row.event_type]).map(row => ({
    label: noticeLabels[row.event_type], summary: row.summary_zh || '', date: row.public_at || null,
    date_precision: row.date_precision || 'unknown', url: safeUrl(row.source_url),
  }))
  if (notices.length) return notices
  // An empty active state is the normal default, not a later event.
  if (noticeLabels[status?.status]) return [{ label: noticeLabels[status.status], summary: '具体通知请查看证据与版本。', date: null, date_precision: 'unknown', url: '' }]
  return []
}

export function decodeCardArray(value) { return readArray(value) }
