import { isDeepStrictEqual } from 'node:util'

/** Only audited status/effective-validation fields overlay authority text. */
export function applySearchStatus(work, status, detail) {
  if (!status) return work
  if (status.work_id !== work.work_id || detail?.work_id !== work.work_id || !isDeepStrictEqual(detail.research_status, status)) {
    throw new Error(`Search status/detail identity mismatch: ${work.work_id}`)
  }
  if (detail.research_status_as_of !== status.as_of) throw new Error('Search status cutoff mismatch')
  return { ...work, research_status: status, research_status_as_of: status.as_of,
    ...Object.fromEntries(['evidence_grade', 'evidence_flags', 'strict_peer_reviewed'].map(key => [key, detail[key]])) }
}
