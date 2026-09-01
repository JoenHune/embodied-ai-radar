import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const read = (file, fallback = null) => {
  const target = path.join(root, file)
  return fs.existsSync(target) ? JSON.parse(fs.readFileSync(target, 'utf8')) : fallback
}

const topicByLabel = {
  具身基础模型: 'foundation',
  大小脑与双系统: 'dual_system',
  灵巧操作: 'dexterous',
  世界模型: 'world_model',
  通用机器人学习: 'general_learning',
}
const currentToLegacyTopic = {
  foundation_models: 'foundation',
  reasoning_planning: 'dual_system',
  world_models: 'world_model',
  dexterous_manipulation: 'dexterous',
  humanoid_whole_body: 'general_learning',
  navigation_mobile_manipulation: 'general_learning',
  human_robot_interaction: 'general_learning',
  policy_learning: 'general_learning',
  data_engines: 'general_learning',
  simulation_transfer: 'general_learning',
  spatial_perception: 'general_learning',
  safety_evaluation: 'general_learning',
  continual_deployment_learning: 'general_learning',
  multi_robot_coordination: 'general_learning',
  embodied_multisensory: 'dexterous',
}

const normalizeStatus = (value) => {
  if (typeof value === 'boolean') return value
  if (value && typeof value === 'object') {
    if ('value' in value) return value.value === true
    if ('status' in value) return value.status === 'yes'
  }
  return false
}

const normalizeInstitutions = (institutions = []) =>
  [...new Set(institutions.map((item) => typeof item === 'string' ? item : item?.name).filter(Boolean))]

const curatedRecord = (record, existing = {}) => {
  const signals = record.signals ?? {}
  const openAssets = signals.open_assets ?? signals.open_code_data_model ?? {}
  const hasTypedOpenAssets = ['code', 'data', 'model'].some((key) => key in openAssets)
  const legacyOpenStatus = !hasTypedOpenAssets && normalizeStatus(openAssets)
  const urls = record.project_or_code_urls ?? []
  const currentPrimaryTopic = record.current_primary_topic
    ?? (record.primary_topic in currentToLegacyTopic ? record.primary_topic : null)
  const primaryTopic = topicByLabel[record.primary_direction]
    ?? currentToLegacyTopic[record.primary_topic]
    ?? record.primary_topic
  const confidenceValue = Number(record.classification_confidence ?? 0.9)
  return {
    id: record.arxiv_id,
    title: record.title ?? existing.title,
    authors: record.authors ?? existing.authors ?? [],
    institutions: normalizeInstitutions(record.institutions ?? existing.institutions),
    first_submitted: record.v1_date ?? existing.first_submitted,
    updated: (record.updated_date ?? record.updated_at ?? record.v1_date)?.slice(0, 10),
    abstract: record.abstract ?? existing.abstract ?? '',
    categories: record.categories ?? existing.categories ?? [],
    primary_topic: primaryTopic,
    current_primary_topic: currentPrimaryTopic ?? existing.current_primary_topic ?? null,
    topics: [primaryTopic],
    tags: record.horizontal_tags ?? record.cross_tags ?? [],
    confidence: confidenceValue >= 0.84 ? 'high' : confidenceValue >= 0.68 ? 'medium' : 'low',
    confidence_score: confidenceValue,
    arxiv_url: record.arxiv_url ?? `https://arxiv.org/abs/${record.arxiv_id}`,
    doi: record.doi ?? null,
    official_url: null,
    code_url: urls.find((url) => url.includes('github.com')) ?? null,
    project_url: urls.find((url) => !url.includes('github.com')) ?? null,
    peer_review: null,
    evidence: {
      real_robot: normalizeStatus(signals.real_robot),
      multi_task: normalizeStatus(signals.multi_task),
      cross_embodiment: normalizeStatus(signals.cross_embodiment),
      long_horizon: normalizeStatus(signals.long_horizon),
      open_code: openAssets.code === true || legacyOpenStatus,
      open_data: openAssets.data === true || legacyOpenStatus,
      open_model: openAssets.model === true || legacyOpenStatus,
    },
    contribution_zh: record.contribution_zh ?? record.one_sentence_contribution_zh ?? '',
    limitation_zh: record.limitation_zh ?? record.one_sentence_limitation_zh ?? '',
    selection_reason_zh: record.selection_reason_zh ?? '经主题检索与 arXiv ID/标题/v1 日期复核的月度高信号样本。',
    curated: true,
    included: true,
    verification: record.verification ?? null,
    date_precision: 'day',
    source: 'curated + arXiv API verified',
  }
}

const candidates = read('data/processed/semantic-scholar-candidates.json', [])
const currentPreprints = read('data/preprints.json', [])
const currentPreprintById = new Map(currentPreprints.map((paper) => [paper.arxiv_id, paper]))
const papers = new Map(
  candidates.map((paper) => [
    paper.id,
    {
      ...paper,
      institutions: normalizeInstitutions(paper.institutions),
      curated: false,
      included: paper.confidence !== 'low',
      confidence_score: paper.confidence === 'high' ? 0.82 : paper.confidence === 'medium' ? 0.68 : 0.45,
    },
  ]),
)

for (const file of [
  'data/curated-2025h2.json',
  'data/curated-2026h1.json',
  'data/curated-2026-07-extra.json',
  'data/curated-2026-07-late.json',
  'data/curated-2026-08.json',
]) {
  const dataset = read(file, { records: [] })
  for (const record of dataset.records ?? []) {
    const preprint = currentPreprintById.get(record.arxiv_id) ?? {}
    const existing = papers.get(record.arxiv_id) ?? {
      title: preprint.title,
      authors: preprint.authors,
      institutions: preprint.institutions,
      first_submitted: preprint.first_submitted,
      updated: preprint.updated,
      abstract: preprint.abstract,
      categories: preprint.categories,
    }
    const normalized = curatedRecord(record, existing)
    papers.set(normalized.id, {
      ...existing,
      ...normalized,
      topics: [...new Set([...(existing.topics ?? []), ...(normalized.topics ?? [])])],
      tags: [...new Set([...(existing.tags ?? []), ...(normalized.tags ?? [])])],
      institutions: normalized.institutions.length ? normalized.institutions : (existing.institutions ?? []),
    })
  }
}

const peerDataset = read('data/peer-review.json', read('.research/peer-review.json', { records: [] }))
for (const review of peerDataset.records ?? peerDataset.works ?? []) {
  const arxivId = review.arxiv_id ?? review.id
  let paper = arxivId ? papers.get(arxivId) : null
  if (!paper && review.title) {
    const normalizedTitle = review.title.toLowerCase().replace(/[^a-z0-9]+/g, '')
    paper = [...papers.values()].find((candidate) =>
      candidate.title.toLowerCase().replace(/[^a-z0-9]+/g, '') === normalizedTitle)
  }
  if (!paper) continue
  paper.peer_review = {
    venue: review.venue,
    year: Number(review.year),
    status: review.status ?? 'published',
    official_url: review.official_url,
    evidence: review.evidence_note ?? review.evidence ?? '官方页面已核验',
    independent_team: review.independent_team ?? null,
  }
  paper.official_url = review.official_url
  if (!paper.institutions?.length && review.institutions?.length) {
    paper.institutions = normalizeInstitutions(review.institutions)
  }
}

const output = [...papers.values()]
  .filter((paper) => paper.id && paper.title && paper.first_submitted)
  .map((paper) => {
    const encodedMonth = `${paper.id.slice(0, 2) >= '90' ? '19' : '20'}${paper.id.slice(0, 2)}-${paper.id.slice(2, 4)}`
    const v1Month = paper.curated ? paper.first_submitted.slice(0, 7) : encodedMonth
    const period = v1Month >= '2024-07' && v1Month <= '2025-06'
      ? 'baseline'
      : v1Month >= '2025-07' && v1Month <= '2026-06'
        ? 'analysis'
        : v1Month >= '2026-07' && v1Month <= '2026-08'
          ? 'extension'
          : 'outside'
    return { ...paper, v1_month: v1Month, period }
  })
  .sort((left, right) => left.id.localeCompare(right.id))

fs.mkdirSync(path.join(root, 'data'), { recursive: true })
fs.writeFileSync(path.join(root, 'data/papers.json'), `${JSON.stringify(output, null, 2)}\n`)

const csvEscape = (value) => {
  const text = Array.isArray(value) ? value.join('|') : String(value ?? '')
  return `"${text.replaceAll('"', '""')}"`
}
const csvFields = [
  'id', 'title', 'first_submitted', 'v1_month', 'primary_topic', 'topics', 'tags',
  'confidence', 'curated', 'institutions', 'authors', 'arxiv_url', 'doi',
]
const csv = [
  csvFields.join(','),
  ...output.map((paper) => csvFields.map((field) => csvEscape(paper[field])).join(',')),
].join('\n')
fs.writeFileSync(path.join(root, 'data/papers.csv'), `${csv}\n`)

const curatedCount = output.filter((paper) => paper.curated).length
const includedCount = output.filter((paper) => paper.included).length
console.log(`Prepared ${output.length} records (${includedCount} included; ${curatedCount} curated).`)
