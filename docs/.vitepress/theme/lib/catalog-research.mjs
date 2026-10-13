const filterLabels = {
  q: '关键词', from: '始于', to: '截至', direction: '方向', question: '问题', organization: '组织',
  outputType: '产出', evidence: '证据', relevance: '纳排', venue: '会议 / 期刊', year: '出版年份',
  track: 'Track', acceptance: '接收', publicationStatus: '发表', ids: '证据集合',
  peerReviewed: '严格同行评审', realRobot: '真机证据', openAssets: '开放资产',
}
const valueLabels = { all: '全库', included: '已纳入', candidate: '候选', manual_review: '待复核', excluded: '已排除', unknown: '待核验', unattributed: '尚未归属', accepted: '已接收', published: '正式出版', preprint: '预印本', main: '主会', technical_report: '技术报告', paper: '论文', code: '代码', model: '模型', dataset: '数据集' }
const multiFields = new Set(['direction', 'question', 'organization', 'outputType', 'evidence', 'venue', 'year', 'track', 'acceptance', 'publicationStatus'])
const valuesOf = value => [...new Set(String(value).split(',').map(item => item.trim()).filter(Boolean))]

export function activeSearchFilters(filters, options = {}) {
  return Object.entries(filterLabels).flatMap(([key, label]) => {
    const value = filters[key]
    if (!value || key === 'relevance' && value === 'included') return []
    if (value === true) return [{ key, label }]
    if (key === 'ids') return [{ key, label: `${label}：${valuesOf(value).length} 项` }]
    const lookup = new Map((options[{ direction: 'directions', question: 'questions', organization: 'organizations' }[key]] || []).map(item => [item.value, item.label]))
    return (multiFields.has(key) ? valuesOf(value) : [String(value)]).map(item => ({
      key, value: multiFields.has(key) ? item : undefined,
      label: `${key === 'direction' && filters.directionMatch === 'all' ? '共同命中方向' : label}：${lookup.get(item) || (['relevance', 'outputType', 'acceptance', 'publicationStatus', 'track', 'organization'].includes(key) ? valueLabels[item] : '') || item}`,
    }))
  })
}

export function clearedSearchFilter(filters, chip) {
  if (!Object.hasOwn(filterLabels, chip.key)) return {}
  const value = chip.value && multiFields.has(chip.key) ? valuesOf(filters[chip.key]).filter(item => item !== chip.value).join(',') : chip.key === 'relevance' ? 'included' : typeof filters[chip.key] === 'boolean' ? false : ''
  return { [chip.key]: value, ...(chip.key === 'direction' && !value ? { directionMatch: 'any' } : {}) }
}

export const readSearchSort = params => ['newest', 'oldest'].includes(params.get('sort')) ? params.get('sort') : 'auto'
export function writeSearchSort(url, sort) {
  const result = new URL(url)
  if (sort === 'newest' || sort === 'oldest') result.searchParams.set('sort', sort)
  else result.searchParams.delete('sort')
  return result
}

function dateParts(value, precision) {
  if (precision === 'unknown' || typeof value !== 'string') return []
  const match = /^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?:T.*)?$/.exec(value)
  if (!match || Number(match[1]) < 1) return []
  const parts = match.slice(1).filter(Boolean).map(Number)
  if (parts.length > 1 && (parts[1] < 1 || parts[1] > 12)) return []
  if (parts.length > 2 && (parts[2] < 1 || parts[2] > new Date(Date.UTC(parts[0], parts[1], 0)).getUTCDate())) return []
  return parts.slice(0, precision === 'year' ? 1 : precision === 'month' ? 2 : 3)
}

export function compareResearchDates(leftDate, leftPrecision, leftId, rightDate, rightPrecision, rightId, sort = 'newest') {
  const left = dateParts(leftDate, leftPrecision), right = dateParts(rightDate, rightPrecision)
  if (!left.length || !right.length) return left.length ? -1 : right.length ? 1 : leftId.localeCompare(rightId)
  // A month/year belongs to its known period; unknown finer precision follows
  // fully dated records in that period, never borrowing the stored placeholder.
  for (let index = 0; index < Math.max(left.length, right.length); index++) {
    if (left[index] === undefined || right[index] === undefined) return left[index] === undefined ? 1 : -1
    if (left[index] !== right[index]) return (left[index] - right[index]) * (sort === 'oldest' ? 1 : -1)
  }
  return leftId.localeCompare(rightId)
}

export function orderSearchPositions(positions, lookup, sort, hasTextQuery) {
  if (sort === 'auto' && hasTextQuery) return [...positions]
  return [...positions].sort((left, right) => compareResearchDates(
    lookup.dates[left], lookup.date_precisions?.[left], lookup.work_ids[left],
    lookup.dates[right], lookup.date_precisions?.[right], lookup.work_ids[right], sort,
  ))
}

export function createSearchRestorer({ invalidateSearch, readState, flush, setRestoring, restoreWork, search }) {
  let revision = 0
  return {
    async restore() {
      const request = ++revision
      invalidateSearch()
      setRestoring(true)
      let state
      try {
        state = readState()
        await flush()
      } finally {
        if (request === revision) setRestoring(false)
      }
      if (request !== revision) return
      // Detail latency must not delay search or suppress later filter changes.
      await Promise.all([restoreWork(state.work), search(state.page)])
    },
    cancel() { revision++; setRestoring(false) },
  }
}
