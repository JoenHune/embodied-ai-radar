// Source-channel disagreements are not publication/retraction status, and
// never change the work population, evidence grade or reading receipt.
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value)
const privatePath = /file:\/\/|\/Users\/|\/home\/|\/private\/|\.research\/|[A-Za-z]:\\/
const text = (value, maximum = 2000) => typeof value === 'string' && value.trim() && value.length <= maximum &&
  !/[\x00-\x1f\x7f-\x9f]/.test(value) && !privatePath.test(value)
const time = value => text(value, 64) && /^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?$/.test(value) && Number.isFinite(Date.parse(value))
const fail = () => { throw new Error('source_conflict_contract_invalid') }

export function safeConflictUrl(value) {
  if (!text(value, 2048)) return ''
  try {
    const url = new URL(value)
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : ''
  } catch { return '' }
}

export function compactSourceConflicts(value) {
  if (value === undefined) return []
  if (!Array.isArray(value)) fail()
  const ids = new Set()
  return value.map(row => {
    if (!object(row) || !text(row.conflict_id, 256) || !text(row.work_id, 256) || !/^v[1-9]\d*$/.test(row.version || '') ||
        !['open', 'resolved'].includes(row.status) || row.experimental_use !== (row.status === 'open' ? 'hold' : 'released') ||
        !text(row.summary_zh) || !time(row.detected_at) || !Array.isArray(row.issue_types) || row.issue_types.some(item => !text(item, 128)) ||
        !Array.isArray(row.source_urls) || !row.source_urls.length || row.source_urls.some(url => !safeConflictUrl(url)) || ids.has(row.conflict_id)) fail()
    ids.add(row.conflict_id)
    return { conflict_id: row.conflict_id, work_id: row.work_id, version: row.version, status: row.status,
      experimental_use: row.experimental_use, summary_zh: row.summary_zh, detected_at: row.detected_at,
      issue_types: [...row.issue_types], source_urls: [...new Set(row.source_urls.map(safeConflictUrl))] }
  }).sort((a, b) => a.work_id.localeCompare(b.work_id) || a.conflict_id.localeCompare(b.conflict_id))
}

export function sourceConflictIndex(envelope, expectedVersion) {
  if (!object(envelope) || envelope.schema_version !== '1' || !text(expectedVersion, 256) ||
      envelope.dataset_version !== expectedVersion || !time(envelope.as_of) || !Array.isArray(envelope.conflicts)) fail()
  const index = new Map()
  for (const row of compactSourceConflicts(envelope.conflicts)) {
    if (!index.has(row.work_id)) index.set(row.work_id, [])
    index.get(row.work_id).push(row)
  }
  return index
}

export function conflictsForWork(index, workId, version) {
  return compactSourceConflicts(index.get(workId) || []).filter(row => version === undefined || row.version === version)
}

export function applySourceConflicts(work, index) {
  return { ...work, source_conflicts: conflictsForWork(index, work.work_id) }
}

export function sourceConflictState(value, { workId, version } = {}) {
  try {
    const rows = compactSourceConflicts(typeof value === 'string' ? JSON.parse(value) : value)
    if (workId && rows.some(row => row.work_id !== workId)) fail()
    return { unknown: false, rows: rows.filter(row => row.status === 'open' && row.experimental_use === 'hold' &&
      (version === undefined || row.version === version)) }
  } catch { return { unknown: true, rows: [] } }
}
