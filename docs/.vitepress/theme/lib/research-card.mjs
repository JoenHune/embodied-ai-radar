export const directionShortNames = { D1: '基础模型', D2: '规划与记忆', D3: '世界模型', D4: '灵巧操作', D5: '全身控制', D6: '导航与移动', D7: '人机协作', D8: '策略学习', D9: '数据与人类视频', D10: '仿真与迁移', D11: '空间感知', D12: '评测与安全', D13: '持续学习', D14: '多机器人', D15: '触觉与力觉' }
import { decodeCardArray } from './work-status.mjs'
import { sourceConflictState } from './source-conflicts.mjs'

export function safeOriginalUrl(value) {
  if (typeof value !== 'string') return ''
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : '' } catch { return '' }
}
export function originalSourceUrl(work, manifestations = work?.manifestations || []) {
  const explicit = safeOriginalUrl(work?.original_url || work?.meta?.original_url)
  if (explicit) return explicit
  const report = manifestations.find(row => row.kind === 'technical_report' && safeOriginalUrl(row.url))
  if (report) return safeOriginalUrl(report.url)
  const arxiv = work?.identifiers?.arxiv || (/^arxiv:/.test(work?.work_id || '') ? work.work_id.slice(6) : '')
  if (/^(?:\d{4}\.\d{4,5}|[a-z.-]+\/\d{7})(?:v\d+)?$/i.test(arxiv)) return `https://arxiv.org/abs/${arxiv}`
  const doi = work?.identifiers?.doi || (/^doi:/.test(work?.work_id || '') ? work.work_id.slice(4) : '')
  if (/^10\.\d{4,9}\/.+/.test(doi)) return `https://doi.org/${doi}`
  return safeOriginalUrl(manifestations.find(row => safeOriginalUrl(row.url))?.url || work?.url)
}
export function researchOutputLabel(work) {
  const kinds = work.output_types || (work.manifestations || []).map(row => row.kind)
  if (kinds.includes('technical_report')) return '企业技术报告'
  if (work.company_self_report) return '企业研究发布'
  if (work.strict_peer_reviewed) return '同行评审已核验'
  if (kinds.includes('preprint')) return '预印本'
  if (work.strategic_only) return '战略观察'
  return '公开研究'
}
export function searchCardFromResult(row) {
  const meta = row.meta
  const conflicts = sourceConflictState(meta.source_conflicts, { workId: meta.work_id })
  return {
    work_id: meta.work_id, title: meta.title, title_zh: meta.title_zh,
    original_url: meta.original_url, summary: meta.summary || row.excerpt,
    summary_kind: meta.summary ? 'source_bound_editorial' : 'original_excerpt',
    first_public_date: meta.date, first_public_date_precision: meta.date_precision,
    primary_direction: meta.direction, directions: meta.direction ? [meta.direction] : [],
    evidence_grade: meta.evidence, relevance_status: meta.relevance,
    strict_peer_reviewed: meta.peer_reviewed === 'true',
    output_types: (meta.output_types || '').split(' · ').filter(Boolean),
    organizations: meta.organizations ? [{ name: meta.organizations }] : [],
    text_notice: meta.text_status === 'unversioned_catalog_text' ? '摘要版次未核验' : '',
    publication_records: decodeCardArray(meta.publication_records),
    source_conflicts: conflicts.rows,
    source_conflicts_unknown: conflicts.unknown,
    research_status: meta.research_status ? { status: meta.research_status, validation_eligible: meta.research_validation_eligible !== 'false', notices: decodeCardArray(meta.research_status_notices) } : null,
  }
}
export function filterResearchCards(rows, { direction = '', kind = 'all', organization = '' } = {}) {
  return rows.filter(row => (!direction || row.primary_direction === direction)
    && (!organization || (row.organizations || []).some(org => org.organization_id === organization))
    && (kind === 'strategic' ? row.strategic_only : !row.strategic_only && (kind === 'all' || (kind === 'reports' ? row.output_types?.includes('technical_report') : row.output_types?.some(type => ['preprint', 'conference', 'journal', 'paper'].includes(type))))))
}
