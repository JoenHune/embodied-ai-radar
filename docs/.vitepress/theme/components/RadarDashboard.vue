<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { withBase } from 'vitepress'
import * as echarts from 'echarts/core'
import { BarChart, HeatmapChart, LineChart, ScatterChart } from 'echarts/charts'
import { AriaComponent, GridComponent, LegendComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ChartFrame from './ChartFrame.vue'
import DirectionTrendGrid from './DirectionTrendGrid.vue'
import EvidenceReadingQueue from './EvidenceReadingQueue.vue'
import ReportTextEvidence from './ReportTextEvidence.vue'
import ResearchStatusNotice from './ResearchStatusNotice.vue'
const ReportCoverage = defineAsyncComponent(() => import('./ReportCoverage.vue'))
const HistoricalEditorial = defineAsyncComponent(() => import('./HistoricalEditorial.vue'))
const ResearchFeed = defineAsyncComponent(() => import('./ResearchFeed.vue'))
const DirectionShareOverview = defineAsyncComponent(() => import('./DirectionShareOverview.vue'))
import { chartTokens, useEChart } from '../composables/useEChart'
import rawOverview from '../../data/v3-overview.json'
import { eventDate, eventMonth, publicationEventDate } from '../lib/dates'
import { completeMonthRange, monthlyValueLabel, splitMonthlySeries } from '../lib/monthlySeries'
import { heatmapScale } from '../lib/heatmap-scale.mjs'
import { evidenceIds, evidenceSearchParams } from '../lib/evidence-links.mjs'
import { monthHistoryTarget, monthRequestIsCurrent, resolveMonthFromUrl, type MonthNavigationSource } from '../lib/month-history.mjs'

echarts.use([
  BarChart,
  HeatmapChart,
  LineChart,
  ScatterChart,
  AriaComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

const props = withDefaults(defineProps<{ mode?: 'home' | 'trends' | 'monthly' | 'organizations' | 'collaboration'; organization?: string }>(), { mode: 'home', organization: '' })
const overview: any = reactive(rawOverview)
const manifest = overview.manifest
const trends = overview.trends
const latestComplete = overview.latestComplete
const defaultMonth: string = manifest.complete_months.at(-1)
const selectedMonth = ref(defaultMonth)
const selectedDirection = ref('D1')
const visualFeedDirection = ref('')
const visualFeedMonth = ref('')
const chartMetric = ref<'shares' | 'counts'>('shares')
const selectedTier = ref('T0')
const selectedOrgSlug = ref(props.organization)
const organizationSort = ref('changed')
const organizationSearch = ref('')
const organizationPage = ref(0)
const organizationDetail = ref<any>(null)
const organizationLoading = ref(false)
const loadError = ref('')
const monthlySnapshot = ref<any>(latestComplete)
const monthlyLoading = ref(false)
const evidenceView = ref<'as_of_month' | 'retrospective'>('as_of_month')
const hasMonthEvidence = computed(() => monthlySnapshot.value.temporal_basis === 'as_of_month' && Boolean(monthlySnapshot.value.evidence_as_of))
const hasRetrospectiveEvidence = computed(() => Boolean(monthlySnapshot.value.retrospective_evidence))
const selectedEvidence = computed<any>(() => evidenceView.value === 'retrospective'
  ? monthlySnapshot.value.retrospective_evidence || null
  : hasMonthEvidence.value ? monthlySnapshot.value : null)
const evidenceCutoff = computed(() => evidenceView.value === 'retrospective'
  ? monthlySnapshot.value.retrospective_evidence?.as_of
  : monthlySnapshot.value.evidence_as_of)
const evidenceViewLabel = computed(() => evidenceView.value === 'retrospective' ? '今天回看' : '当月可用证据')
const peerReviewedCount = computed(() => selectedEvidence.value?.strict_peer_reviewed ?? selectedEvidence.value?.coverage?.strict_peer_reviewed)
const evidenceGrades = computed(() => selectedEvidence.value?.evidence_grades || {})
const directionLabels = new Map(trends.directions.map((row: any) => [row.code, row.label]))
const momentumLabel: Record<string, string> = { rising: '上升', stable: '稳定', cooling: '降温' }
const lifecycleLabel: Record<string, string> = { candidate: '候选', emerging: '新兴', consolidating: '巩固', established: '成熟', contested: '有争议', dormant: '休眠', unassessed: '待判断' }
const eventLabels: Record<string, string> = { preprint: '预印本', paper: '论文', accepted: '接收', acceptance: '同行评审确认', accepted_peer_reviewed: '同行评审确认', publication: '正式出版', published_proceedings: '正式出版', technical_report: '技术报告', model_release: '模型发布', model: '模型', dataset: '数据集', code: '代码', repository: '代码', benchmark: '评测基准', deployment: '部署', project: '项目', demo: '演示', independent_replication: '独立复现' }
const databaseUrl = (ids: string[] = [], params: Record<string, string> = {}) => {
  const query = evidenceSearchParams(ids, monthlySnapshot.value.evidence_id_to_work_id || {}, params)
  return withBase(`/database/?${query}`)
}
const signalIsReviewed = (row: any) => row.assessment_status !== 'retrieval_only' && evidenceIds(row).length > 0
const displayText = (value: any): string => typeof value === 'string' ? value : value?.text || value?.summary_zh || value?.summary || value?.question || value?.title || value?.label || ''
const coverageFieldLabels: Record<string, string> = { included_works: '纳入工作', strict_peer_reviewed: '同行评审', technical_reports: '技术报告', classification_pending: '待分类', works_with_abstract: '有摘要工作', candidate_works: '候选工作', excluded_works: '排除工作' }
const revisionCoverageChanges = (row: any) => Object.entries(row.differences?.coverage || {}).map(([field, values]: [string, any]) => `${coverageFieldLabels[field] || field}：${values.before ?? '未登记'} → ${values.after ?? '未登记'}`)
const revisionWorkIds = (row: any, kind: 'added' | 'removed'): string[] => row.differences?.[`${kind}_work_ids`] || row[`${kind}_work_ids`] || []
const revisionClaimIds = (row: any): string[] => row.differences?.changed_claim_ids || row.changed_claim_ids || []
const orgChanged = (row: any) => row.last_changed || (row.updates || []).map((event: any) => event.published_at || '').sort().at(-1) || ''

const number = (value: number) => new Intl.NumberFormat('zh-CN').format(value || 0)
const percent = (value: number) => `${(value * 100).toFixed(1)}%`
const shortMonth = (value: string) => `${value.slice(2, 4)}.${value.slice(5)}`
const latestRows = computed(() => latestComplete.high_signal_works || [])
const trendSignals = computed(() => selectedEvidence.value?.trend_ledger || [])
const activeOrganizations = computed(() => overview.organizations
  .filter((row: any) => (selectedTier.value === 'all' || row.tier === selectedTier.value) && `${row.name} ${row.short_name} ${row.summary_zh || ''}`.toLocaleLowerCase().includes(organizationSearch.value.toLocaleLowerCase()))
  .sort((left: any, right: any) => (organizationSort.value === 'changed' ? orgChanged(right).localeCompare(orgChanged(left)) : 0) || left.name.localeCompare(right.name, 'zh-CN')))
const topOrganizations = computed(() => activeOrganizations.value.slice(organizationPage.value * 21, (organizationPage.value + 1) * 21))
const organizationPages = computed(() => Math.max(1, Math.ceil(activeOrganizations.value.length / 21)))
const selectedOrganization = computed(() => organizationDetail.value?.slug === selectedOrgSlug.value ? organizationDetail.value : overview.organizations.find((row: any) => row.slug === selectedOrgSlug.value))
const selectedOrganizationWorkIds = computed<string[]>(() => [...new Set<string>(selectedOrganization.value?.work_ids || [])])
const selectedOrganizationPendingIds = computed<string[]>(() => [...new Set<string>([
  ...(selectedOrganization.value?.pending_work_ids || []),
  ...(selectedOrganization.value?.attribution_pending_work_ids || []),
  ...(selectedOrganization.value?.review_work_ids || []),
])])
const selectedCollaborators = computed(() => {
  if (!selectedOrganization.value) return []
  const ids = new Set(selectedOrganization.value.work_ids || [])
  return overview.organizations.filter((row: any) => row.slug !== selectedOrgSlug.value)
    .map((row: any) => ({ ...row, shared_work_ids: (row.work_ids || []).filter((id: string) => ids.has(id)) }))
    .filter((row: any) => row.shared_work_ids.length)
    .sort((a: any, b: any) => b.shared_work_ids.length - a.shared_work_ids.length)
})
const startupReportCount = computed(() => new Set(startups.value.flatMap((org: any) => (org.updates || []).filter((event: any) => event.event_type === 'technical_report').map((event: any) => event.work_id || event.event_id))).size)
const monthlyLedger = computed(() => selectedEvidence.value?.trend_ledger || [])
const counterevidence = computed(() => monthlySnapshot.value.counterevidence || [])
const watchlist = computed(() => monthlySnapshot.value.watchlist || monthlySnapshot.value.next_month_watchlist || [])
const informationGaps = computed(() => monthlySnapshot.value.information_gaps || [])
const capabilityEvidence = computed(() => {
  const source = selectedEvidence.value?.capability_evidence || []
  return Array.isArray(source) ? source : Object.entries(source).map(([label, value]) => typeof value === 'number' ? { label, count: value } : { label, ...(value as any) })
})
const monthlyEvents = computed(() => monthlySnapshot.value.evidence_events || [])
// Research status projections: begin. These only select presentation data;
// never rewrite monthly prose, counts, or work-to-organization attribution.
const researchStatusLabels: Record<string, string> = { withdrawn: '作者撤回', retracted: '撤稿', corrected: '更正', expression_of_concern: '关注声明', reinstated: '恢复', active: '未被状态通知阻断' }
const editorialSectionLabels: Record<string, string> = { claims: '总判断', direction_summaries: '方向摘要', question_summaries: '问题轴摘要', organization_changes: '组织解读', counterevidence: '反例与边界', watchlist: '观察清单' }
const statusRows = (value: any): any[] => Array.isArray(value) ? value : []
const noticeKey = (workId: string, noticeId: string) => `${workId}|${noticeId}`
const historicalStatusNoticeKeys = computed(() => new Set(statusRows(monthlySnapshot.value.research_status).flatMap(row => statusRows(row.notices).map(notice => noticeKey(row.work_id, notice.notice_id)))))
const selectedResearchStatuses = computed(() => statusRows(selectedEvidence.value?.research_status))
const currentResearchStatuses = computed(() => Array.isArray(monthlySnapshot.value.research_status_current)
  ? monthlySnapshot.value.research_status_current : statusRows(monthlySnapshot.value.retrospective_evidence?.research_status))
// Presentation-only interval end, matching the conservative Shanghai calendar
// cutoff. A month/year precision never borrows a placeholder's exact day.
const statusTimeUpper = (value: any, precision?: string): number | null => {
  if (typeof value !== 'string' || !value || precision === 'unknown') return null
  const match = /^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/.exec(value)
  if (match) {
    const year = Number(match[1]), month = Number(match[2] || 1), day = Number(match[3] || 1)
    const checked = new Date(Date.UTC(year, month - 1, day))
    if (checked.getUTCFullYear() !== year || checked.getUTCMonth() !== month - 1 || checked.getUTCDate() !== day) return null
    if (precision === 'year' || !match[2]) return Date.UTC(year + 1, 0, 1) - 8 * 3600000 - 1
    if (precision === 'month' || !match[3]) return Date.UTC(year, month, 1) - 8 * 3600000 - 1
    return Date.UTC(year, month - 1, day + 1) - 8 * 3600000 - 1
  }
  if (!/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)) return null
  const instant = Date.parse(value)
  return Number.isFinite(instant) ? instant : null
}
const noticeExceedsSelectedCutoff = (notice: any): boolean => {
  const when = statusTimeUpper(notice.public_at, notice.date_precision)
  const until = statusTimeUpper(evidenceCutoff.value)
  return when !== null && until !== null && when > until
}
const currentStatusCutoff = computed(() => {
  const dates = currentResearchStatuses.value.map((row: any) => row.as_of).filter((value: any) => statusTimeUpper(value) !== null)
  return dates.sort((left: string, right: string) => statusTimeUpper(right)! - statusTimeUpper(left)!)[0]
    || (!Array.isArray(monthlySnapshot.value.research_status_current) ? monthlySnapshot.value.retrospective_evidence?.as_of : null)
})
const monthlyStatusEvents = computed(() => statusRows(monthlySnapshot.value.research_status_changes).filter(notice =>
  notice.work_id && notice.notice_id && ['day', 'month', 'second'].includes(notice.date_precision) && eventMonth(notice.public_at) === monthlySnapshot.value.month))
const followUpResearchStatuses = computed(() => currentResearchStatuses.value
  .map((row: any) => ({ ...row, notices: statusRows(row.notices).filter(noticeExceedsSelectedCutoff) }))
  .filter((row: any) => row.notices.length))
const editorialStatusDependencies = computed(() => statusRows(monthlySnapshot.value.editorial_status_dependencies))
const statusNoticeLookup = computed(() => {
  const lookup = new Map<string, any>()
  for (const notice of statusRows(monthlySnapshot.value.research_status_changes)) lookup.set(noticeKey(notice.work_id, notice.notice_id), notice)
  for (const row of [...statusRows(monthlySnapshot.value.research_status), ...statusRows(monthlySnapshot.value.retrospective_evidence?.research_status), ...currentResearchStatuses.value]) {
    for (const notice of statusRows(row.notices)) lookup.set(noticeKey(row.work_id, notice.notice_id), notice)
  }
  return lookup
})
const dependencyNoticeSources = (dependency: any): any[] => [...new Set<string>(statusRows(dependency.notice_ids))]
  .map(id => statusNoticeLookup.value.get(noticeKey(dependency.work_id, id)))
  .filter(notice => notice && typeof notice.source_url === 'string' && /^https?:\/\//i.test(notice.source_url))
const dependencyIsLater = (dependency: any): boolean => statusRows(dependency.notice_ids).some(id => statusNoticeLookup.value.has(noticeKey(dependency.work_id, id)) && !historicalStatusNoticeKeys.value.has(noticeKey(dependency.work_id, id)))
const dependencyExceedsSelectedCutoff = (dependency: any): boolean => dependencyNoticeSources(dependency).some(noticeExceedsSelectedCutoff)
const statusWorkUrl = (workId: string): string => withBase(`/database/?${new URLSearchParams({ work: workId, relevance: 'all' })}`)
const selectedStatusContext = computed(() => `${evidenceViewLabel.value} · 状态截至 ${eventDate(evidenceCutoff.value)}；仅针对 ${monthlySnapshot.value.month} 首次公开的同一批研究，不改变首次公开数量。`)
const followUpStatusContext = (row: any): string => `后续补充提醒：这些通知不在所选证据截止 ${eventDate(evidenceCutoff.value)} 的可用范围，不计入所选证据。该工作已登记的最新综合状态截至 ${eventDate(row.as_of || currentStatusCutoff.value)}；原始编辑文本仍保留。`
// Research status projections: end.
const startups = computed(() => overview.organizations
  .filter((row: any) => row.startup_frontier || ['org:figure-ai', 'org:dyna-robotics', 'org:sunday-robotics'].includes(row.organization_id))
  .sort((left: any, right: any) => (right.updates?.[0]?.published_at || '').localeCompare(left.updates?.[0]?.published_at || '')))

const provisionalHasData = computed(() => {
  const index = trends.months.indexOf(manifest.provisional_month)
  return index >= 0 && trends.directions.some((row: any) => row.counts[index] > 0 || row.multi_label_counts[index] > 0)
})
const splitDirectionSeries = (values: number[]) => splitMonthlySeries(trends.months, values, manifest.complete_months, manifest.provisional_month, provisionalHasData.value)
const trendRangeCaption = computed(() => `${completeMonthRange(manifest.complete_months, manifest.provisional_month)}；${provisionalHasData.value ? '暂行值不参与完整月连线' : '暂行月暂无采集数据，未知不记为零'}`)

const heatmapData = computed(() => trends.directions.flatMap((row: any, y: number) =>
  splitDirectionSeries(row[chartMetric.value]).display.flatMap((value, x) => value === null ? [] : [[x, y, chartMetric.value === 'shares' ? Number((value * 100).toFixed(2)) : value, row.counts[x], row.multi_label_counts[x]]]),
))
const inspectDirection = (direction: string, month?: string) => {
  selectedDirection.value = direction
  visualFeedDirection.value = direction
  if (month) visualFeedMonth.value = month
  if (typeof window !== 'undefined') {
    const url = new URL(window.location.href)
    url.searchParams.set('feed_direction', direction)
    if (month) url.searchParams.set('feed_month', month)
    if (url.href !== window.location.href) window.history.pushState(window.history.state, '', url)
    document.getElementById('research-feed')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
  }
}

const commonTooltip = () => {
  const tokens = chartTokens()
  return {
    backgroundColor: tokens.background,
    borderColor: tokens.divider,
    textStyle: { color: tokens.text },
    confine: true,
  }
}

const heatmap = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    aria: { enabled: true, description: 'D1 到 D15 在最近十二个完整月和当前暂行月的主方向份额热力图。' },
    tooltip: {
      ...commonTooltip(),
      formatter: (params: any) => {
        const [x, y, value, count, multi] = params.data
        const direction = trends.directions[y]
        return `<strong>${direction.code} · ${direction.label}</strong><br/>${trends.months[x]}：${chartMetric.value === 'shares' ? value.toFixed(1) + '%' : value + ' 项'}<br/>主方向 ${count} 项 · 多标签 ${multi} 项<br/>点击查看组成研究`
      },
    },
    // Reserve separate space for rotated month labels and the color legend.
    grid: { left: 142, right: 28, top: 18, bottom: 80 },
    xAxis: {
      type: 'category',
      data: trends.months.map(shortMonth),
      axisLabel: { color: tokens.muted, interval: 0, rotate: 34 },
      axisLine: { lineStyle: { color: tokens.divider } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category',
      data: trends.directions.map((row: any) => `${row.code} ${row.label.replace('与', '·').slice(0, 9)}`),
      axisLabel: { color: tokens.muted, fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    visualMap: {
      ...heatmapScale(heatmapData.value),
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      calculable: false,
      text: [chartMetric.value === 'shares' ? '占比高' : '数量多', '低'],
      textStyle: { color: tokens.muted },
      inRange: { color: [tokens.background, tokens.palette[1], tokens.palette[0]] },
    },
    series: [{ type: 'heatmap', data: heatmapData.value, emphasis: { itemStyle: { shadowBlur: 8, shadowColor: tokens.divider } } }],
  }
}, (chart) => {
  chart.on('click', (params: any) => {
    const direction = trends.directions[params.data?.[1]]?.code
    const month = trends.months[params.data?.[0]]
    if (direction) inspectDirection(direction, month)
  })
})

const selectedSeries = computed(() => trends.directions.find((row: any) => row.code === selectedDirection.value) || trends.directions[0])
const selectedMonthlySeries = computed(() => splitDirectionSeries(selectedSeries.value[chartMetric.value]))
const mobileLine = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false,
    aria: { enabled: true, description: `${selectedSeries.value.label}的月度研究份额。${trendRangeCaption.value}` },
    tooltip: { ...commonTooltip(), trigger: 'axis', formatter: (items: any[]) => { const index = items[0]?.data?.monthIndex ?? items[0]?.dataIndex; return index === undefined ? '' : `${trends.months[index]}${trends.months[index] === manifest.provisional_month ? '（暂行）' : ''}<br/>${monthlyValueLabel(selectedMonthlySeries.value.display[index], chartMetric.value)}` } },
    grid: { left: 48, right: 18, top: 22, bottom: 38 },
    xAxis: { type: 'category', data: trends.months.map((month: string) => month === manifest.provisional_month ? `${shortMonth(month)}*` : shortMonth(month)), axisLabel: { color: tokens.muted, interval: 2, showMaxLabel: true }, axisLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'value', axisLabel: { color: tokens.muted, formatter: (value: number) => chartMetric.value === 'shares' ? `${Math.round(value * 100)}%` : `${value}` }, splitLine: { lineStyle: { color: tokens.divider } } },
    series: [
      { name: '完整月', type: 'line', data: selectedMonthlySeries.value.complete, connectNulls: false, smooth: 0.25, symbol: 'circle', symbolSize: 6, lineStyle: { color: tokens.palette[0], width: 2 }, itemStyle: { color: tokens.palette[0] }, areaStyle: { color: tokens.palette[0], opacity: 0.12 } },
      { name: '暂行月（独立观测）', type: 'scatter', data: selectedMonthlySeries.value.provisional.flatMap((value, index) => value === null ? [] : [{ value: [index, value], monthIndex: index }]), symbol: 'emptyCircle', symbolSize: 9, itemStyle: { color: tokens.muted, borderColor: tokens.muted, borderWidth: 2 } },
    ],
  }
})

const bubbleRows = computed(() => trends.ledger.map((ledger: any) => {
  const series = trends.directions.find((row: any) => row.code === ledger.code)
  const completeShares = series.shares.slice(0, manifest.complete_months.length)
  const latest = completeShares.at(-1) || 0
  const prior = completeShares.slice(-4, -1)
  const average = prior.reduce((sum: number, value: number) => sum + value, 0) / Math.max(prior.length, 1)
  return {
    ...ledger,
    growth: average ? (latest / average - 1) * 100 : 0,
    grade: Number((ledger.evidence_grade || 'E0').slice(1)),
  }
}))
const bubble = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    aria: { enabled: true, description: '各方向相对过去三个月的动量与证据成熟度。' },
    tooltip: {
      ...commonTooltip(),
      formatter: (params: any) => `<strong>${params.data.code} · ${params.data.label}</strong><br/>相对三月均值 ${params.data.growth > 0 ? '+' : ''}${params.data.growth.toFixed(1)}%<br/>${momentumLabel[params.data.momentum]} · 已登记最高 ${params.data.evidence_grade}<br/>两月 ${params.data.rolling_two_month_works} 项 / ${params.data.independent_clusters} 个证据簇<br/>方向聚合不代表具体命题已成熟`,
    },
    grid: { left: 54, right: 22, top: 18, bottom: 48 },
    xAxis: { type: 'value', name: '相对前三月均值', nameLocation: 'middle', nameGap: 34, axisLabel: { color: tokens.muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'value', min: -0.3, max: 4.3, interval: 1, name: '证据等级', axisLabel: { color: tokens.muted, formatter: (value: number) => Number.isInteger(value) ? `E${value}` : '' }, splitLine: { lineStyle: { color: tokens.divider } } },
    series: [{
      type: 'scatter',
      data: bubbleRows.value.map((row: any) => ({ ...row, value: [Number(row.growth.toFixed(2)), row.grade, row.rolling_two_month_works] })),
      symbolSize: (value: number[]) => Math.max(12, Math.min(46, 10 + Math.sqrt(value[2]) * 3)),
      itemStyle: { color: (params: any) => ({ rising: tokens.palette[0], stable: tokens.palette[1], cooling: tokens.palette[3] } as Record<string, string>)[params.data.momentum] || tokens.palette[5], opacity: 0.82 },
      label: { show: true, formatter: (params: any) => params.data.code, color: tokens.text, fontSize: 11, position: 'top' },
    }],
  }
}, (chart) => chart.on('click', (params: any) => { if (params.data?.code) window.location.href = databaseUrl(evidenceIds(params.data), { directions: params.data.code }) }))

const cooccurrenceRows = computed(() => {
  const values = new Map(trends.cooccurrence.map((row: any) => [`${row.source}|${row.target}`, row.count]))
  return trends.directions.flatMap((left: any, y: number) => trends.directions.map((right: any, x: number) => {
    if (left.code === right.code) return [x, y, 0]
    return [x, y, values.get(`${left.code}|${right.code}`) || values.get(`${right.code}|${left.code}`) || 0]
  }))
})
const cooccurrence = useEChart(() => {
  const tokens = chartTokens()
  const max = Math.max(...cooccurrenceRows.value.map((row: any) => row[2]), 1)
  return {
    animation: false,
    aria: { enabled: true, description: '同一工作命中的方向共现矩阵，不代表方向迁移。' },
    tooltip: { ...commonTooltip(), formatter: (params: any) => `${trends.directions[params.data[1]].code} × ${trends.directions[params.data[0]].code}：${params.data[2]} 项` },
    grid: { left: 48, right: 22, top: 18, bottom: 48 },
    xAxis: { type: 'category', data: trends.directions.map((row: any) => row.code), axisLabel: { color: tokens.muted, rotate: 35 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'category', data: trends.directions.map((row: any) => row.code), axisLabel: { color: tokens.muted }, axisLine: { show: false }, axisTick: { show: false } },
    visualMap: { show: false, dimension: 2, min: 0, max, inRange: { color: [tokens.background, tokens.palette[2]] } },
    series: [{ type: 'heatmap', data: cooccurrenceRows.value }],
  }
}, (chart) => chart.on('click', (params: any) => {
  const [x, y] = params.data || []
  if (x !== undefined && x !== y) window.location.href = databaseUrl([], { directions: `${trends.directions[x].code},${trends.directions[y].code}` })
}))

const monthDelta = useEChart(() => {
  const tokens = chartTokens()
  const rows = [...monthlySnapshot.value.directions].sort((left: any, right: any) => left.share_delta - right.share_delta)
  return {
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    aria: { enabled: true, description: `${monthlySnapshot.value.month}各方向相较上月的研究份额变化。` },
    tooltip: { ...commonTooltip(), formatter: (params: any) => `${params.name}<br/>${params.value > 0 ? '+' : ''}${params.value.toFixed(1)} 个百分点` },
    grid: { left: 148, right: 32, top: 12, bottom: 28 },
    xAxis: { type: 'value', axisLabel: { color: tokens.muted, formatter: '{value}pp' }, splitLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'category', data: rows.map((row: any) => `${row.code} ${row.label.slice(0, 8)}`), axisLabel: { color: tokens.muted }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{ type: 'bar', data: rows.map((row: any) => ({ value: Number((row.share_delta * 100).toFixed(2)), itemStyle: { color: row.share_delta >= 0 ? tokens.palette[0] : tokens.palette[3] } })), barMaxWidth: 18 }],
  }
})

const questionChart = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false,
    aria: { enabled: true, description: `${monthlySnapshot.value.month}的 Q0 到 Q10 问题轴覆盖。` },
    tooltip: { ...commonTooltip(), formatter: (params: any) => `${params.name}<br/>${params.value} 项多标签命中` },
    grid: { left: 44, right: 18, top: 14, bottom: 42 },
    xAxis: { type: 'category', data: monthlySnapshot.value.questions.map((row: any) => row.code), axisLabel: { color: tokens.muted }, axisLine: { lineStyle: { color: tokens.divider } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } },
    series: [{ type: 'bar', data: monthlySnapshot.value.questions.map((row: any) => row.count), itemStyle: { color: tokens.palette[2] }, barMaxWidth: 26 }],
  }
})

const evidenceChart = useEChart(() => {
  const tokens = chartTokens()
  const grades = ['E0', 'E1', 'E2', 'E3', 'E4']
  return {
    animation: false,
    aria: { enabled: true, description: `${monthlySnapshot.value.month}研究工作的证据成熟度分布。` },
    tooltip: { ...commonTooltip(), trigger: 'axis' },
    grid: { left: 46, right: 18, top: 18, bottom: 36 },
    xAxis: { type: 'category', data: grades, axisLabel: { color: tokens.muted }, axisLine: { lineStyle: { color: tokens.divider } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } },
    series: [{ type: 'bar', data: grades.map((grade, index) => ({ value: evidenceGrades.value[grade] || 0, itemStyle: { color: tokens.palette[Math.min(index, 5)] } })), barMaxWidth: 44 }],
  }
})

const organizationHeatRows = computed(() => topOrganizations.value.flatMap((org: any, y: number) =>
  trends.directions.map((direction: any, x: number) => [x, y, org.actual_direction_counts?.[direction.code] || 0]),
))
const organizationHeatmap = useEChart(() => {
  const tokens = chartTokens()
  const max = Math.max(...organizationHeatRows.value.map((row: any) => row[2]), 1)
  return {
    animation: false,
    aria: { enabled: true, description: `${selectedTier.value}组织最近十二个月的方向覆盖热力图。` },
    tooltip: { ...commonTooltip(), formatter: (params: any) => `${topOrganizations.value[params.data[1]]?.name}<br/>${trends.directions[params.data[0]].code}：${params.data[2]} 项` },
    grid: { left: 168, right: 18, top: 16, bottom: 46 },
    xAxis: { type: 'category', data: trends.directions.map((row: any) => row.code), axisLabel: { color: tokens.muted, rotate: 35 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'category', data: topOrganizations.value.map((row: any) => row.short_name || row.name), axisLabel: { color: tokens.muted, width: 148, overflow: 'truncate' }, axisLine: { show: false }, axisTick: { show: false } },
    visualMap: { show: false, dimension: 2, min: 0, max, inRange: { color: [tokens.background, tokens.palette[1], tokens.palette[0]] } },
    series: [{ type: 'heatmap', data: organizationHeatRows.value }],
  }
}, (chart) => chart.on('click', (params: any) => {
  const [x, y] = params.data || []
  const org = topOrganizations.value[y]
  if (org) window.location.href = databaseUrl([], { organizations: org.organization_id, directions: trends.directions[x].code })
}))

const organizationTimelineRows = computed(() => {
  const months = trends.months
  const values = new Map<string, { paper: number; report: number; release: number }>(months.map((month: string) => [month, { paper: 0, report: 0, release: 0 }]))
  for (const org of activeOrganizations.value) {
    for (const update of org.updates || []) {
      const month = eventMonth(update.published_at)
      if (!values.has(month)) continue
      const bucket = values.get(month)!
      if (['preprint', 'paper'].includes(update.event_type)) bucket.paper += 1
      else if (update.event_type === 'technical_report') bucket.report += 1
      else bucket.release += 1
    }
  }
  return months.map((month: string) => ({ month, ...values.get(month)! }))
})
const organizationTimeline = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false,
    aria: { enabled: true, description: `${selectedTier.value}组织的论文、技术报告和其他研究发布月度变化。` },
    color: [tokens.palette[0], tokens.palette[3], tokens.palette[1]],
    legend: { top: 0, textStyle: { color: tokens.muted } },
    tooltip: { ...commonTooltip(), trigger: 'axis' },
    grid: { left: 44, right: 18, top: 48, bottom: 36 },
    xAxis: { type: 'category', data: organizationTimelineRows.value.map((row: any) => shortMonth(row.month)), axisLabel: { color: tokens.muted, interval: 1 }, axisLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'value', axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } },
    series: [
      { name: '论文/预印本', type: 'bar', stack: 'events', data: organizationTimelineRows.value.map((row: any) => row.paper) },
      { name: '企业技术报告', type: 'bar', stack: 'events', data: organizationTimelineRows.value.map((row: any) => row.report) },
      { name: '模型/数据/项目', type: 'bar', stack: 'events', data: organizationTimelineRows.value.map((row: any) => row.release) },
    ],
  }
})

const validationTimeline = useEChart(() => {
  const tokens = chartTokens()
  const rows = overview.evidenceTimeline || []
  return {
    animation: false, aria: { enabled: true, description: '研究首次出现与后续接收、出版、独立复现按发生月分别计数。' },
    color: [tokens.palette[1], tokens.palette[0], tokens.palette[2], tokens.palette[3]],
    legend: { top: 0, textStyle: { color: tokens.muted } }, tooltip: { ...commonTooltip(), trigger: 'axis' },
    grid: { left: 45, right: 45, top: 65, bottom: 40 },
    xAxis: { type: 'category', data: rows.map((row: any) => shortMonth(row.month)), axisLabel: { color: tokens.muted, interval: 1 } },
    yAxis: [{ type: 'value', name: '新研究', axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } }, { type: 'value', name: '证据升级', axisLabel: { color: tokens.muted }, splitLine: { show: false } }],
    series: [{ name: '新研究', type: 'bar', data: rows.map((row: any) => row.new_works), itemStyle: { opacity: .3 }, barMaxWidth: 28 }, ...[['accepted', '接收确认'], ['published', '正式出版'], ['replicated', '独立复现']].map(([key, name]) => ({ name, type: 'line', yAxisIndex: 1, data: rows.map((row: any) => row[key]), connectNulls: false }))],
  }
})

const updateQuery = (key: string, value: string) => {
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  if (value) url.searchParams.set(key, value)
  else url.searchParams.delete(key)
  window.history.replaceState(window.history.state, '', url)
}

const selectOrganization = (org: any) => {
  selectedOrgSlug.value = org.slug
  selectedTier.value = org.tier
  updateQuery('org', org.slug)
  loadOrganization(org.slug)
  window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
}

let organizationRequest = 0
const loadOrganization = async (slug: string) => {
  const request = ++organizationRequest
  organizationLoading.value = true
  loadError.value = ''
  try {
    const response = await fetch(withBase(`/api/v1/organizations/${encodeURIComponent(slug)}.json`))
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const value = await response.json()
    if (request === organizationRequest) organizationDetail.value = value
  } catch { if (request === organizationRequest) loadError.value = '完整组织档案暂时读取失败，下方仍显示已保存的公开信息。' }
  finally { if (request === organizationRequest) organizationLoading.value = false }
}

const clearOrganization = () => {
  if (props.organization) { window.location.href = withBase(`/organizations/?tier=${selectedTier.value}`); return }
  selectedOrgSlug.value = ''
  const url = new URL(window.location.href)
  url.searchParams.delete('org')
  window.history.replaceState(window.history.state, '', url)
}

let monthRequest = 0
let monthDisposed = false
let monthNavigationSource: MonthNavigationSource = 'selection'
const loadMonth = async (month: string, source: MonthNavigationSource = 'selection') => {
  if (monthDisposed || !manifest.available_months.includes(month)) return
  const request = ++monthRequest
  const requestPath = window.location.pathname
  const isCurrent = () => monthRequestIsCurrent({ request, currentRequest: monthRequest, disposed: monthDisposed, requestPath, currentPath: window.location.pathname })
  monthlyLoading.value = true
  loadError.value = ''
  try {
    const response = await fetch(withBase(`/api/v1/monthly/${month}.json`))
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const value = await response.json()
    if (isCurrent()) {
      monthlySnapshot.value = value
      const target = monthHistoryTarget(window.location.href, month, { availableMonths: manifest.available_months, defaultMonth, source })
      if (target) window.history.pushState(window.history.state, '', target)
    }
  } catch { if (isCurrent()) loadError.value = '该月数据暂时读取失败，请重试；当前保留上次成功加载的月份。' } finally {
    if (isCurrent()) monthlyLoading.value = false
  }
}

// Synchronous capture distinguishes a user selection from URL hydration/popstate.
watch(selectedMonth, (month) => { void loadMonth(month, monthNavigationSource) }, { flush: 'sync' })
watch(evidenceView, (value) => updateQuery('evidence_view', value))
watch(() => props.organization, (slug) => {
  selectedOrgSlug.value = slug
  if (slug) loadOrganization(slug)
})
watch(selectedDirection, (value) => updateQuery('directions', value))
watch(chartMetric, (value) => updateQuery('metric', value))
watch([selectedTier, organizationSearch, organizationSort], () => { organizationPage.value = 0; updateQuery('tier', selectedTier.value) })
const restoreQuery = (event?: PopStateEvent) => {
  const params = new URLSearchParams(window.location.search)
  const month = resolveMonthFromUrl(window.location.href, manifest.available_months, defaultMonth)
  // Even an unchanged selection must invalidate a pending user-origin load.
  monthRequest += 1
  monthlyLoading.value = false
  monthNavigationSource = event ? 'restore' : 'hydrate'
  try {
    if (selectedMonth.value !== month) selectedMonth.value = month
    else if (monthlySnapshot.value.month !== month) void loadMonth(month, monthNavigationSource)
  } finally { monthNavigationSource = 'selection' }
  evidenceView.value = params.get('evidence_view') === 'retrospective' ? 'retrospective' : 'as_of_month'
  const direction = params.get('directions')
  selectedDirection.value = direction && directionLabels.has(direction) ? direction : 'D1'
  chartMetric.value = params.get('metric') === 'counts' ? 'counts' : 'shares'
  visualFeedDirection.value = directionLabels.has(params.get('feed_direction')) ? params.get('feed_direction')! : ''
  visualFeedMonth.value = manifest.available_months.includes(params.get('feed_month')) ? params.get('feed_month')! : ''
  const tier = params.get('tier')
  selectedTier.value = tier && ['T0', 'T1', 'T2', 'all'].includes(tier) ? tier : 'T0'
  const organization = overview.organizations.find((row: any) => row.slug === (params.get('org') || props.organization))
  if (organization) {
    selectedOrgSlug.value = organization.slug
    selectedTier.value = organization.tier
    loadOrganization(organization.slug)
  } else if (!props.organization) {
    selectedOrgSlug.value = ''
    organizationDetail.value = null
    organizationRequest += 1
    organizationLoading.value = false
  }
}
onMounted(() => {
  restoreQuery()
  window.addEventListener('popstate', restoreQuery)
  if (props.mode === 'organizations' || props.mode === 'collaboration') {
    if (props.organization) void loadOrganization(props.organization)
    void fetch(withBase('/api/v1/organization-overview.json')).then(async response => {
      if (!response.ok) throw new Error('organization directory unavailable')
      const value = await response.json()
      if (value.dataset_version !== manifest.dataset_version) throw new Error('organization directory version mismatch')
      if (!monthDisposed) { overview.organizations = value.rows; restoreQuery() }
    }).catch(() => { if (!monthDisposed) loadError.value = '组织目录暂时无法读取，单组原始档案与研究库仍可访问。' })
  }
})
onBeforeUnmount(() => {
  monthDisposed = true
  monthRequest += 1
  organizationRequest += 1
  window.removeEventListener('popstate', restoreQuery)
})
</script>

<template>
  <div class="v3-dashboard" :data-mode="mode">
    <header v-if="mode === 'home'" class="v3-hero">
      <div>
        <p class="v3-eyebrow">EMBODIED AI RESEARCH INTELLIGENCE</p>
        <h1>具身智能研究雷达</h1>
        <p class="v3-hero-copy">看清研究方向如何变化，沿着图文与人物回到原始证据。</p>
      </div>
      <div class="v3-hero-actions">
        <a class="v3-primary-action" :href="withBase('/trends/')">查看研究趋势</a>
        <a :href="withBase('/database/')">检索 {{ number(manifest.counts.works) }} 项工作</a>
      </div>
    </header>

    <nav v-if="mode === 'home'" class="v3-research-shortcuts" aria-label="近期研究与专题入口">
      <a :href="withBase(`/monthly/?month=${manifest.provisional_month}`)">本月 {{ manifest.provisional_month }} <span>暂行</span></a>
      <a :href="withBase('/hardware/')">研究设备与使用证据 →</a>
      <a :href="withBase('/trends/loco-manip/')">移动与全身操作 →</a>
    </nav>

    <div v-if="overview.editorialStatus.status !== 'llm_complete'" class="v3-status-banner" role="status">
      <template v-if="overview.editorialStatus.status === 'partial'">已生成并通过结构与引用校验的中文月报 {{ overview.editorialStatus.completed_months.length }} / {{ manifest.complete_months.length }} 个月；其余月份仍为数据版。内容校验不等于独立研究验证。</template>
      <template v-else>当前为数据版；统计与公开证据可查，自动中文研究总结尚未全部生成。覆盖缺口见各月说明。</template>
    </div>
    <p v-if="loadError" class="v3-error" role="alert">{{ loadError }} <button type="button" @click="loadError = ''">关闭提示</button></p>

    <section v-if="mode === 'home'" class="v3-metrics visual-summary-metrics" aria-label="数据库概况">
      <div><strong>{{ number(manifest.counts.included) }}</strong><span>正式纳入</span></div>
      <div><strong>{{ number(manifest.counts.strict_peer_reviewed) }}</strong><span>严格同行评审</span></div>
      <div><strong>{{ number(manifest.counts.technical_reports) }}</strong><span>企业技术报告</span></div>
      <div><strong>{{ number(manifest.counts.t0_organizations) }}</strong><span>T0 核心研究组</span></div>
    </section>
    <DirectionShareOverview v-if="mode === 'home'" :snapshot="latestComplete" @direction="(code: string) => inspectDirection(code, latestComplete.month)" />
    <ResearchFeed v-if="mode === 'home'" id="research-feed" title="值得展开看的研究与报告" :month="visualFeedMonth" :direction="visualFeedDirection" :limit="3" @month="(value: string) => visualFeedMonth = value === 'featured' ? '' : value" @direction="(value: string) => visualFeedDirection = value" />

    <div v-if="mode === 'monthly'" class="v3-page-heading">
      <div>
        <p class="v3-eyebrow">MONTHLY RESEARCH LEDGER</p>
        <h1>月度研究重点</h1>
        <p>完整覆盖 D1–D15、Q0–Q10、证据泳道和组织变化；暂行月不进入完整月趋势判定。</p>
      </div>
      <label>选择月份
        <select v-model="selectedMonth" :disabled="monthlyLoading">
          <option v-for="month in [...manifest.available_months].reverse()" :key="month" :value="month">
            {{ month }}{{ month === manifest.provisional_month ? ' · 暂行' : '' }}
          </option>
        </select>
      </label>
    </div>

    <div v-if="mode === 'organizations' || mode === 'collaboration'" class="v3-page-heading">
      <div>
        <p class="v3-eyebrow">GLOBAL ORGANIZATION RADAR</p>
        <h1>{{ props.organization && selectedOrganization ? selectedOrganization.name : mode === 'collaboration' ? '合作研究组与联合项目' : '关键公司与研究组' }}</h1>
        <p>按证据覆盖和最近实质变化浏览，不做综合排名。<a :href="withBase('/organizations/people/')">进入人物研究雷达 →</a></p>
      </div>
      <label>跟踪层级
        <select v-model="selectedTier">
          <option value="all">全部层级</option>
          <option value="T0">T0 · 核心</option>
          <option value="T1">T1 · 前沿</option>
          <option value="T2">T2 · 发现池</option>
        </select>
      </label>
    </div>

    <div v-if="mode === 'trends'" class="v3-page-heading">
      <div>
        <p class="v3-eyebrow">TREND ENGINE</p>
        <h1>研究趋势</h1>
        <p>观察哪些方向的占比在变化，再走进具体研究和验证证据。<a :href="withBase('/organizations/people/')">按方向看研究者 →</a></p>
      </div>
      <a class="v3-secondary-action" :href="withBase('/methods/#趋势判定')">查看判定口径</a>
    </div>

    <section v-if="mode === 'monthly' || mode === 'trends'" class="v3-temporal-panel" aria-label="研究证据时间视角">
      <div class="v3-temporal-controls">
        <label v-if="mode === 'trends'">命题观察月份<select v-model="selectedMonth" :disabled="monthlyLoading"><option v-for="month in [...manifest.available_months].reverse()" :key="month" :value="month">{{ month }}{{ month === manifest.provisional_month ? ' · 暂行' : '' }}</option></select></label>
        <fieldset><legend>证据视角</legend><label><input v-model="evidenceView" type="radio" value="as_of_month" /> 当月可用证据</label><label><input v-model="evidenceView" type="radio" value="retrospective" :disabled="!hasRetrospectiveEvidence" /> 今天回看</label></fieldset>
      </div>
      <p aria-live="polite"><strong>{{ evidenceViewLabel }}</strong> · {{ monthlySnapshot.month }} 首次公开的研究<span v-if="evidenceCutoff"> · 证据截至 {{ eventDate(evidenceCutoff) }}</span>。{{ evidenceView === 'retrospective' ? '纳入之后发生的评审、开源或复现；不改写该月研究首次出现数量。' : '仅使用当时已公开的证据；之后的验证不倒灌历史月份。' }}</p>
      <p v-if="!selectedEvidence" class="v3-warning" role="status">此快照的时点证据尚待重算，暂不展示旧版证据等级或评审数量。论文列表与方向数量仍可查。</p>
      <p v-if="mode === 'trends'" class="v3-muted">此切换作用于具体命题账本；议题数量与份额图始终保持最近 12 个完整月，气泡标示当前已登记的最高单项证据。</p>
    </section>

    <template v-if="mode === 'home' || mode === 'trends'">
      <ChartFrame title="过去 12 个完整月的研究重点" :description="trendRangeCaption" :height="530">
        <template #actions><div class="visual-chart-switch" aria-label="趋势图度量"><button type="button" :aria-pressed="chartMetric === 'shares'" @click="chartMetric = 'shares'">占比</button><button type="button" :aria-pressed="chartMetric === 'counts'" @click="chartMetric = 'counts'">数量</button></div></template>
        <div :ref="heatmap.element" class="v3-desktop-chart" role="img" :aria-label="`方向与月份研究${chartMetric === 'shares' ? '份额' : '数量'}热力图`" />
        <div class="v3-mobile-chart">
          <label>选择方向
            <select v-model="selectedDirection">
              <option v-for="row in trends.directions" :key="row.code" :value="row.code">{{ row.code }} · {{ row.label }}</option>
            </select>
          </label>
          <div :ref="mobileLine.element" role="img" :aria-label="`${selectedSeries.label}月度趋势图`" />
        </div>
        <template #table>
          <table>
            <thead><tr><th>方向</th><th v-for="month in trends.months" :key="month">{{ month }}{{ month === manifest.provisional_month ? ' · 暂行' : '' }}</th></tr></thead>
            <tbody><tr v-for="row in trends.directions" :key="row.code"><th>{{ row.code }}</th><td v-for="(value, index) in splitDirectionSeries(row[chartMetric]).display" :key="index">{{ monthlyValueLabel(value, chartMetric) }}</td></tr></tbody>
          </table>
        </template>
      </ChartFrame>

      <div class="v3-two-column">
        <ChartFrame title="议题发文动量 × 单项证据" description="当前全库的方向聚合，不是已验证趋势；最高单项证据不代表整个方向成熟" :height="390" compact>
          <div :ref="bubble.element" role="img" aria-label="方向动量和证据成熟度气泡图" />
          <template #table>
            <table><thead><tr><th>方向</th><th>动量</th><th>最高证据</th><th>独立簇</th></tr></thead><tbody><tr v-for="row in trends.ledger" :key="row.code"><td>{{ row.code }}</td><td>{{ momentumLabel[row.momentum] }}</td><td>{{ row.evidence_grade }}</td><td>{{ row.independent_clusters }}</td></tr></tbody></table>
          </template>
        </ChartFrame>
        <section class="v3-ledger-panel">
          <header><h2>具体研究命题</h2><p>{{ monthlySnapshot.month }} · {{ evidenceViewLabel }}；检索命中不是支持证据</p></header>
          <a v-for="row in trendSignals" :key="row.signal_id || row.id || row.code" :href="evidenceIds(row).length ? databaseUrl(evidenceIds(row)) : row.candidate_work_ids?.length ? databaseUrl(row.candidate_work_ids) : undefined" class="v3-signal-link">
            <strong>{{ row.title || row.question || row.label }}</strong><span>{{ signalIsReviewed(row) ? lifecycleLabel[row.lifecycle] || '待判断' : '待证据审阅' }}</span><span :data-momentum="signalIsReviewed(row) ? row.momentum : undefined">{{ signalIsReviewed(row) ? momentumLabel[row.momentum] || '待判断' : '不判定动量' }}</span><small>{{ evidenceIds(row).length ? `${row.evidence_grade} · ${evidenceIds(row).length} 项支持证据` : `${row.candidate_work_ids?.length || 0} 项相关检索，待证据审阅` }}</small>
          </a>
          <p v-if="!trendSignals.length" class="v3-empty">研究命题正在绑定支持证据与反例；可先按 D/Q 检索，避免将宏观发文数量直接解释为技术成熟。</p>
        </section>
      </div>
      <ChartFrame title="研究首次出现与后续验证" description="左轴为新工作；右轴为接收、出版与独立复现。事件缺失表示尚未登记，并非没有发生。" :height="370">
        <div :ref="validationTimeline.element" role="img" aria-label="新研究与后续证据升级双时间线" />
        <template #table><table><thead><tr><th>月份</th><th>新研究</th><th>接收确认</th><th>正式出版</th><th>独立复现</th></tr></thead><tbody><tr v-for="row in overview.evidenceTimeline || []" :key="row.month"><th>{{ row.month }}</th><td>{{ row.new_works }}</td><td>{{ row.accepted }}</td><td>{{ row.published }}</td><td>{{ row.replicated }}</td></tr></tbody></table></template>
      </ChartFrame>
    </template>

    <template v-if="mode === 'trends'">
      <ResearchFeed id="research-feed" title="从方向占比走进具体研究" :month="visualFeedMonth" :direction="visualFeedDirection" :limit="6" @month="(value: string) => visualFeedMonth = value === 'featured' ? '' : value" @direction="(value: string) => visualFeedDirection = value" />
      <section class="v3-section-heading"><div><p class="v3-eyebrow">ALL DIRECTIONS</p><h2>主方向数量与多标签密度</h2></div><p>每一行使用独立纵轴，避免大方向压扁低密度前沿。</p></section>
      <DirectionTrendGrid :series="trends.directions" :months="trends.months" :ledger="trends.ledger" :complete-months="manifest.complete_months" :provisional-month="manifest.provisional_month" :provisional-has-data="provisionalHasData" />
      <ChartFrame title="方向共现矩阵" description="同一工作命中的多方向关系；用于发现融合路线，不表示方向迁移" :height="560">
        <div :ref="cooccurrence.element" class="v3-desktop-chart" role="img" aria-label="D1 到 D15 共现矩阵" />
        <div class="v3-mobile-org-list">
          <a v-for="row in [...trends.cooccurrence].sort((a: any, b: any) => b.count - a.count)" :key="`${row.source}-${row.target}`" :href="databaseUrl([], { directions: `${row.source},${row.target}` })" class="v3-relation-row"><strong>{{ row.source }} × {{ row.target }}</strong><span>{{ number(row.count) }} 项共同命中</span></a>
        </div>
        <template #table><table><thead><tr><th>方向组合</th><th>共同命中工作</th></tr></thead><tbody><tr v-for="row in trends.cooccurrence" :key="`${row.source}-${row.target}`"><td>{{ row.source }} × {{ row.target }}</td><td><a :href="databaseUrl([], { directions: `${row.source},${row.target}` })">{{ number(row.count) }}</a></td></tr></tbody></table></template>
      </ChartFrame>
    </template>

    <template v-if="mode === 'monthly'">
      <section class="v3-month-summary">
        <div><span>状态</span><strong>{{ monthlySnapshot.status === 'provisional' ? '暂行月' : '完整月' }}</strong></div>
        <div><span>纳入工作</span><strong>{{ number(monthlySnapshot.coverage.included_works) }}</strong></div>
        <div><span>同行评审 · {{ evidenceViewLabel }}</span><strong>{{ peerReviewedCount === undefined ? '待重算' : number(peerReviewedCount) }}</strong></div>
        <div><span>企业技术报告</span><strong>{{ number(monthlySnapshot.coverage.technical_reports) }}</strong></div>
      </section>
      <div class="v3-coverage-note"><strong>{{ monthlySnapshot.month }} · 修订 {{ monthlySnapshot.revision || 1 }}</strong><span>数据截至 {{ eventDate(monthlySnapshot.data_through || manifest.data_through) }}</span><span>待明确主方向：{{ monthlySnapshot.coverage.classification_pending === undefined ? '统计待补' : `${number(monthlySnapshot.coverage.classification_pending)} 项` }}</span><span>有摘要 {{ number(monthlySnapshot.coverage.works_with_abstract || 0) }} 项</span></div>
      <aside v-if="editorialStatusDependencies.length" class="v3-status-dependencies" :class="{ blocked: editorialStatusDependencies.some((row: any) => row.validation_eligible === false) }" role="note" aria-labelledby="status-dependency-heading">
        <h2 id="status-dependency-heading">后续状态提醒：保留的研究判断存在受影响引用</h2>
        <p>下方原始编辑文本没有改写。请按通知实际发布日期区分当月信息与后来提醒；后来出现的撤回、更正等状态不表示当月已经知情，也不计入当月证据。</p>
        <ul><li v-for="dependency in editorialStatusDependencies" :key="`${dependency.claim_id || dependency.section + ':' + dependency.index}|${dependency.work_id}`">
          <strong>{{ editorialSectionLabels[dependency.section] || '历史判断' }} · {{ dependency.code || dependency.title || `第 ${Number(dependency.index) + 1} 条` }}</strong>
          <p><a :href="statusWorkUrl(dependency.work_id)">{{ dependency.work_title || dependency.work_id }}</a> · {{ researchStatusLabels[dependency.status] || '状态待核验' }} · 状态核验截至 {{ eventDate(dependency.as_of) }}</p>
          <p>{{ dependencyNoticeSources(dependency).length ? dependencyExceedsSelectedCutoff(dependency) ? '后续通知（不计入所选证据截止）' : dependencyIsLater(dependency) ? '原月之后的通知（已在所选回看范围内）' : '当月已公开的通知（原叙述仍需结合状态复核）' : '通知日期或来源定位仍待核验，请打开研究详情核对。' }}<span v-if="dependency.validation_eligible === false">；受影响结果不再用于支持命题或提升证据成熟度。</span></p>
          <div class="v3-status-links"><a :href="statusWorkUrl(dependency.work_id)">打开研究与全部状态记录</a><a v-for="notice in dependencyNoticeSources(dependency)" :key="notice.notice_id" :href="notice.source_url" target="_blank" rel="noopener noreferrer">官方{{ researchStatusLabels[notice.event_type] || '状态' }}通知 · {{ eventDate(notice.public_at, notice.date_precision) }}</a></div>
        </li></ul>
      </aside>
      <section class="v3-findings">
        <header><h2>本月总判断</h2><span>{{ monthlySnapshot.editorial_status === 'llm_complete' ? 'LLM 证据编辑' : '确定性数据摘要' }} · 保留快照原始视角</span></header>
        <p v-if="monthlySnapshot.editorial_completeness?.overall_status === 'needs_attention'" class="v3-warning">内容完整性待补：总判断 {{ monthlySnapshot.editorial_completeness.executive.count }} 条（目标 5–8 条）。缺失项已在检查中列明；未编辑不能解释为没有研究。<a :href="withBase(`/api/v1/monthly/${monthlySnapshot.month}.json`)">查看逐方向检查</a></p>
        <p v-if="monthlySnapshot.editorial_reviews?.length" class="v3-muted">本版有源绑定内容审校记录；AI 内容审校不等于人工专家批准、同行评审或独立复现。<a :href="withBase(`/api/v1/editorial-reviews/${monthlySnapshot.month}.json`)">查看修改前后、依据与记录者</a></p>
        <article v-for="(finding, index) in monthlySnapshot.executive_findings" :key="finding.claim_id || index">
          <strong>{{ String(Number(index) + 1).padStart(2, '0') }}</strong>
          <div class="v3-finding-copy"><h3 v-if="finding.title">{{ finding.title }}</h3><p>{{ finding.text }}</p></div>
          <a v-if="evidenceIds(finding).length" :href="databaseUrl(evidenceIds(finding))">查看全部 {{ evidenceIds(finding).length }} 条证据</a>
          <span v-else class="v3-muted">证据待补，暂不形成结论</span>
        </article>
        <p v-if="!monthlySnapshot.executive_findings.length" class="v3-empty">当前暂行月尚无足够工作形成研究判断。</p>
      </section>
      <HistoricalEditorial :key="monthlySnapshot.month" :snapshot="monthlySnapshot" />
      <section v-if="monthlySnapshot.historical_findings?.length" class="v3-analysis-section">
        <details :open="monthlySnapshot.editorial_status !== 'llm_complete'"><summary>历史版本的研究判断</summary><p>保留迁移前观点供对照；当前研究判断与证据边界以上方及本版数据为准。</p>
        <article v-for="finding in monthlySnapshot.historical_findings" :key="finding.claim_id" class="v3-note-row">
          <h3>{{ finding.title }}</h3><p>{{ finding.summary }}</p>
          <p v-if="finding.comparison">月际变化：{{ displayText(finding.comparison) }}</p>
          <p v-if="finding.bottleneck">研究瓶颈：{{ displayText(finding.bottleneck) }}</p>
          <p v-if="finding.evidence_review_required">部分引用仍在复核队列；本项保留为历史研究判断。</p>
          <a v-if="finding.supporting_ids?.length" :href="databaseUrl(finding.supporting_ids)">查看全部引用 {{ finding.supporting_ids.length }}</a>
        </article>
        </details>
      </section>
      <div class="v3-two-column">
        <ChartFrame title="相较上月的重点迁移" description="单位为主方向份额百分点；数量变化与份额变化分开解释" :height="520" compact>
          <div :ref="monthDelta.element" role="img" aria-label="各方向相对上月的份额变化条形图" />
          <template #table><table><thead><tr><th>方向</th><th>主方向数</th><th>份额</th><th>变化百分点</th></tr></thead><tbody><tr v-for="row in monthlySnapshot.directions" :key="row.code"><th>{{ row.code }} {{ row.label }}</th><td>{{ row.primary_count }}</td><td>{{ percent(row.share) }}</td><td>{{ (row.share_delta * 100).toFixed(2) }}</td></tr></tbody></table></template>
        </ChartFrame>
        <ChartFrame title="问题轴覆盖" description="Q0–Q10 是可重叠的问题层，不与主方向数量相加" :height="360" compact>
          <div :ref="questionChart.element" role="img" aria-label="月度问题轴覆盖条形图" />
          <template #table><table><thead><tr><th>问题轴</th><th>命中工作</th></tr></thead><tbody><tr v-for="row in monthlySnapshot.questions" :key="row.code"><th>{{ row.code }} {{ row.title }}</th><td>{{ row.count }}</td></tr></tbody></table></template>
        </ChartFrame>
      </div>
      <ResearchFeed id="research-feed" :title="`${monthlySnapshot.month} · 研究图文流`" :month="monthlySnapshot.month" :direction="visualFeedDirection" :limit="9" locked-month />
      <details class="visual-deep-dive"><summary>展开 15 个方向与 11 个问题轴的逐项解读</summary>
      <section class="v3-analysis-section"><header><h2>D1–D15 全方向研究重点</h2><p>主方向与交叉标签分别统计；有活动不等于命题已被验证。</p></header>
        <div class="v3-coverage-grid"><article v-for="row in monthlySnapshot.directions" :key="row.code">
          <h3>{{ row.code }} · {{ row.label }}</h3><p class="v3-direction-numbers"><strong>{{ row.primary_count }}</strong> 主方向 · {{ row.multi_label_count }} 多标签 · {{ percent(row.share) }}</p>
          <p>{{ row.summary_zh || row.summary || (row.primary_count ? '已有公开研究进入本月统计；具体机制、实验条件和争议请展开证据阅读。' : '本月没有可明确归入此主方向的新工作；交叉标签和待核验记录单独保留。') }}</p>
          <a :href="databaseUrl(evidenceIds(row), { from: monthlySnapshot.month, to: monthlySnapshot.month, ...(evidenceIds(row).length ? {} : { directions: row.code }) })">{{ evidenceIds(row).length ? `查看 ${evidenceIds(row).length} 项代表证据` : '查看方向工作' }}</a>
          <a :href="databaseUrl([], { from: monthlySnapshot.month, to: monthlySnapshot.month, directions: row.code })">完整方向集合</a>
        </article></div>
      </section>
      <section class="v3-analysis-section"><header><h2>Q0–Q10 问题轴</h2><p>研究试图解决什么，而不仅是哪类模型。</p></header><div class="v3-question-grid"><article v-for="row in monthlySnapshot.questions" :key="row.code"><h3>{{ row.code }} · {{ row.title }}</h3><p>{{ row.summary_zh || row.summary || (row.count ? '已有相关研究，需按实验条件判断解决程度。' : '本月无可核验新增证据。') }}</p><a :href="databaseUrl(evidenceIds(row), { from: monthlySnapshot.month, to: monthlySnapshot.month, questions: row.code })">{{ row.count }} 项相关工作</a></article></div></section>
      </details>
      <div class="v3-two-column">
        <ChartFrame v-if="selectedEvidence" :title="`证据成熟度 · ${evidenceViewLabel}`" :description="`证据截至 ${eventDate(evidenceCutoff)}；企业单方报告不能单独形成成熟趋势`" :height="330" compact>
          <div :ref="evidenceChart.element" role="img" aria-label="月度证据等级分布" />
          <template #table><table><thead><tr><th>证据等级</th><th>工作数量</th></tr></thead><tbody><tr v-for="grade in ['E0', 'E1', 'E2', 'E3', 'E4']" :key="grade"><th>{{ grade }}</th><td>{{ evidenceGrades[grade] || 0 }}</td></tr></tbody></table></template>
        </ChartFrame>
        <section class="v3-evidence-lanes">
          <header><h2>研究产出泳道</h2><p>保留本月快照口径；回看切换不改变首次公开数量</p></header>
          <div v-for="(count, kind) in monthlySnapshot.evidence_lanes" :key="kind"><a :href="databaseUrl([], { from: monthlySnapshot.month, to: monthlySnapshot.month, output_types: String(kind) })">{{ eventLabels[String(kind)] || kind }}</a><strong>{{ number(Number(count)) }}</strong></div>
        </section>
      </div>
      <section class="v3-analysis-section"><header><h2>研究出现与证据升级</h2><p>接收和出版记录在发生月份；首次公开月份保持不变。</p></header><div class="v3-event-timeline"><article v-for="event in monthlyEvents" :key="event.event_id"><time>{{ publicationEventDate(event) }}</time><div><strong>{{ eventLabels[event.event_type] || event.event_type }}</strong><p>{{ event.title || event.summary_zh }}</p><a v-if="event.work_id" :href="databaseUrl([event.work_id])">打开对应研究</a><a v-if="event.url || event.source_url" :href="event.url || event.source_url" target="_blank" rel="noreferrer">官方证据</a></div></article><p v-if="!monthlyEvents.length" class="v3-empty">本月尚未登记可核验的证据升级事件；这不表示没有接收或出版。</p></div></section>
      <section class="v3-analysis-section v3-research-status-lane" aria-labelledby="research-status-lane-heading">
        <header><h2 id="research-status-lane-heading">撤回、更正与后续状态</h2><p>按通知实际发布日期归档，工作可能首次公开于更早月份。这些是工作级状态通知，不作为研究组归属证据。</p></header>
        <h3>{{ monthlySnapshot.month }} 发布的通知</h3>
        <div class="v3-status-events"><article v-for="notice in monthlyStatusEvents" :key="`${notice.work_id}|${notice.notice_id}`">
          <time :datetime="notice.public_at">{{ eventDate(notice.public_at, notice.date_precision) }}</time>
          <h4>{{ researchStatusLabels[notice.event_type] || '状态通知' }} · {{ notice.work_title || notice.work_id }}</h4>
          <p>{{ notice.summary_zh }}</p>
          <p class="v3-muted">这是该日发布的通知；当前综合状态请查看研究详情，不能把旧通知单独当成最新状态。</p>
          <div class="v3-status-links"><a :href="statusWorkUrl(notice.work_id)">打开研究与全部状态记录</a><a :href="notice.source_url" target="_blank" rel="noopener noreferrer">核对官方通知原文</a></div>
        </article></div>
        <p v-if="!monthlyStatusEvents.length" class="v3-empty">本月尚未登记日期可定位的状态通知；不表示没有撤回或更正发生。</p>
        <div v-if="selectedResearchStatuses.length" class="v3-status-cohort">
          <h3>{{ evidenceViewLabel }} · 本月研究的状态</h3>
          <article v-for="row in selectedResearchStatuses" :key="row.work_id">
            <ResearchStatusNotice :value="row" :title="row.title || row.work_id" :context="selectedStatusContext" />
            <h4 v-if="!row.notices?.length">{{ row.title || row.work_id }}</h4>
            <p v-if="row.information_gaps?.length" class="v3-muted">状态日期、来源或通知顺序仍有待核验项；信息缺口本身不能证明撤回或恢复。</p>
            <a :href="statusWorkUrl(row.work_id)">核对研究详情与状态来源</a>
          </article>
        </div>
        <div v-if="followUpResearchStatuses.length" class="v3-status-followup" role="note">
          <h3>后续通知提醒 · 不计入所选证据截止</h3>
          <p>所选研究证据截至 {{ eventDate(evidenceCutoff) }}；已登记的最新状态检查截至 {{ eventDate(currentStatusCutoff) }}。这里单独展示超出所选截止口径的通知，不改写该时点已知信息与旧编辑文本。</p>
          <article v-for="row in followUpResearchStatuses" :key="row.work_id">
            <ResearchStatusNotice :value="row" :title="row.title || row.work_id" :context="followUpStatusContext(row)" />
            <a :href="statusWorkUrl(row.work_id)">打开研究与全部状态记录</a>
          </article>
        </div>
      </section>
      <section class="v3-analysis-section"><header><h2>具体研究命题账本</h2><p>每项判断保留支持证据、反例与适用条件。</p></header><div class="v3-coverage-grid"><article v-for="row in monthlyLedger" :key="row.trend_id || row.id || row.code"><h3>{{ row.title || row.question || row.label }}</h3><p>{{ signalIsReviewed(row) ? lifecycleLabel[row.lifecycle] || '待判断' : '待证据审阅' }} · {{ signalIsReviewed(row) ? momentumLabel[row.momentum] || '待判断' : '不判定动量' }} · {{ signalIsReviewed(row) ? row.evidence_grade || '待核验' : '证据未判定' }}</p><p>{{ row.summary_zh || row.summary || row.scope }}</p><a v-if="evidenceIds(row).length" :href="databaseUrl(evidenceIds(row))">全部支持证据 {{ evidenceIds(row).length }}</a><a v-else-if="row.candidate_work_ids?.length" :href="databaseUrl(row.candidate_work_ids)">相关研究 {{ row.candidate_work_ids.length }}（尚未逐项确认支持）</a><a v-if="row.counterevidence_ids?.length" :href="databaseUrl(row.counterevidence_ids)">反例 {{ row.counterevidence_ids.length }}</a></article></div><p v-if="!monthlyLedger.length" class="v3-empty">具体研究命题尚待证据绑定；大方向数量不能替代技术结论。</p></section>
      <EvidenceReadingQueue :month="monthlySnapshot.month" />
      <section v-if="selectedEvidence?.report_text_evidence?.length" class="v3-analysis-section">
        <header><h2>公司报告：当时能看到哪些原文</h2><p>{{ evidenceViewLabel }} · 原文摘录与报告发布日期分别核验；缺少正文的公司也列出，不静默遗漏。</p></header>
        <ReportTextEvidence v-for="row in selectedEvidence.report_text_evidence" :key="row.work_id" :title="row.title" :value="row.selection" />
      </section>
      <section class="v3-analysis-section"><header><h2>真机、跨本体、长时序及部署证据</h2><p>只展示已登记信息，缺少可比实验条件的指标不直接横向排名。</p></header><div class="v3-coverage-grid"><article v-for="(row, index) in capabilityEvidence" :key="row.code || row.label || index"><h3>{{ row.label || row.title || row.capability }}</h3><p v-if="row.count !== undefined">{{ row.count }} 项已登记工作</p><p>{{ row.summary_zh || row.summary || row.conditions || '实验条件请参见原始工作。' }}</p><a v-if="evidenceIds(row).length" :href="databaseUrl(evidenceIds(row))">展开能力证据 {{ evidenceIds(row).length }}</a></article></div><p v-if="!capabilityEvidence.length" class="v3-empty">当前快照尚未完成能力证据编码，不能从关键词直接断言能力已实现。</p></section>
      <section v-if="monthlySnapshot.organization_findings?.length" class="v3-analysis-section">
        <header><h2>关键组织的本月解读</h2><p>发布元数据与实验结果分开；每项引用均可展开到对应研究及全部事件。</p></header>
        <article v-for="finding in monthlySnapshot.organization_findings" :key="finding.claim_id" class="v3-note-row"><h3>{{ finding.title }}</h3><p>{{ finding.summary }}</p><a :href="databaseUrl(evidenceIds(finding))">查看发布与研究证据</a></article>
      </section>
      <section class="v3-change-list">
        <header><h2>关键组织变化</h2><span>{{ monthlySnapshot.organization_changes.length }} 项</span></header>
        <article v-for="event in monthlySnapshot.organization_changes" :key="event.event_id">
          <div><strong>{{ event.organization_name }}</strong><span>{{ event.tier }} · {{ event.event_type }} · {{ publicationEventDate(event) }}</span></div>
          <a :href="event.url" target="_blank" rel="noreferrer">{{ event.title }}</a>
          <p>{{ event.summary_zh }}</p>
        </article>
        <p v-if="!monthlySnapshot.organization_changes.length" class="v3-empty">本月尚无已核验的关键组织变化。</p>
      </section>
      <div class="v3-two-column">
        <section class="v3-analysis-section"><header><h2>反例、争议与证据边界</h2></header><article v-for="(row, index) in counterevidence" :key="row.claim_id || index" class="v3-note-row"><p>{{ displayText(row) }}</p><a v-if="evidenceIds(row).length" :href="databaseUrl(evidenceIds(row))">查看引用证据</a></article><p v-if="!counterevidence.length" class="v3-empty">尚未登记本月反例或争议；未登记不等于没有反例。</p></section>
        <section class="v3-analysis-section"><header><h2>下月观察清单</h2></header><article v-for="(row, index) in watchlist" :key="row.id || index" class="v3-note-row"><p>{{ displayText(row) }}</p><a v-if="evidenceIds(row).length" :href="databaseUrl(evidenceIds(row))">研究背景</a></article><p v-if="!watchlist.length" class="v3-empty">观察清单待生成，优先补齐高信号工作验证及关键组织披露。</p></section>
      </div>
      <section class="v3-analysis-section">
        <header><h2>信息缺口与修订记录</h2></header>
        <ul><li v-for="(row, index) in informationGaps" :key="index">{{ displayText(row) }}</li><li v-if="!informationGaps.length">来源覆盖与组织归属仍有缺口；纳入集合并非全部公开研究。</li></ul>
        <details v-if="monthlySnapshot.revisions?.length">
          <summary>查看 {{ monthlySnapshot.revisions.length }} 次修订</summary>
          <article v-for="(row, index) in monthlySnapshot.revisions" :key="row.revision || index" class="v3-note-row">
            <h3><a v-if="row.url" :href="withBase(row.url)">修订 {{ row.revision || Number(index) + 1 }} · 打开归档快照</a><span v-else>修订 {{ row.revision || Number(index) + 1 }}</span></h3>
            <p v-if="row.data_through">语料截至 {{ eventDate(row.data_through) }}</p>
            <p>{{ displayText(row) }}</p>
            <p v-if="revisionCoverageChanges(row).length">{{ revisionCoverageChanges(row).join('；') }}</p>
            <a v-if="revisionWorkIds(row, 'added').length" :href="databaseUrl(revisionWorkIds(row, 'added'), { relevance: 'all' })">新增 {{ revisionWorkIds(row, 'added').length }} 项工作</a>
            <a v-if="revisionWorkIds(row, 'removed').length" :href="databaseUrl(revisionWorkIds(row, 'removed'), { relevance: 'all' })">移出该快照 {{ revisionWorkIds(row, 'removed').length }} 项工作</a>
            <p v-if="revisionClaimIds(row).length">研究判断修订 {{ revisionClaimIds(row).length }} 项；具体判断 ID 及差异保留在归档 JSON。</p>
            <p v-if="!row.differences && row.revision > 1" class="v3-muted">此历史版本尚未登记结构化差异，可打开相邻快照核对。</p>
          </article>
        </details>
        <a :href="withBase(`/api/v1/monthly/${monthlySnapshot.month}.json`)">下载本月原始统计与证据</a>
      </section>
      <section class="v3-work-grid">
        <header><h2>高信号工作</h2><a :href="withBase(`/database/?from=${monthlySnapshot.month}&to=${monthlySnapshot.month}`)">查看本月全部工作</a></header>
        <article v-for="work in monthlySnapshot.high_signal_works" :key="work.work_id">
          <div><span>{{ work.primary_direction || '待分类' }}</span><span v-if="hasMonthEvidence && evidenceView === 'as_of_month'">{{ work.evidence_grade }}</span><span v-if="hasMonthEvidence && evidenceView === 'as_of_month' && work.strict_peer_reviewed">当月已有同行评审</span></div>
          <h3><a :href="withBase(`/database/?work=${encodeURIComponent(work.work_id)}`)">{{ work.title }}</a></h3>
          <p v-if="work.summary_zh">{{ work.summary_zh }}</p>
        </article>
      </section>
    </template>

    <template v-if="mode === 'organizations' || mode === 'collaboration'">
      <ResearchFeed v-if="mode === 'organizations' && (!props.organization || selectedOrganization)" title="公司与研究组的公开研究" :organization-slug="selectedOrganization?.slug || ''" :limit="6" />
      <details v-if="mode === 'organizations'" class="visual-deep-dive"><summary>报告覆盖、原文完整性与来源缺口</summary><ReportCoverage :organization-id="props.organization ? selectedOrganization?.organization_id : undefined" /></details>
      <div class="v3-org-tools"><label>搜索公司与研究组<input v-model="organizationSearch" type="search" placeholder="名称、简称或研究方向" /></label><label>浏览顺序<select v-model="organizationSort"><option value="changed">最近实质变化</option><option value="name">名称</option></select></label><a :href="withBase(mode === 'collaboration' ? '/organizations/' : '/organizations/collaboration')">{{ mode === 'collaboration' ? '返回研究组雷达' : '查看合作关系与联合项目' }}</a></div>
      <section v-if="selectedOrganization" class="v3-selected-org">
        <button type="button" @click="clearOrganization">返回组织全景</button>
        <div>
          <p class="v3-eyebrow">{{ selectedOrganization.tier }} · {{ selectedOrganization.entity_type }} · {{ selectedOrganization.region }}</p>
          <h2>{{ selectedOrganization.name }}</h2>
          <p>{{ selectedOrganization.summary_zh }}</p>
          <p><strong>官方自述方向：</strong>{{ selectedOrganization.declared_direction_codes?.join(' · ') || '待补' }}</p>
          <p><strong>近 12 月实际方向：</strong>{{ Object.entries(selectedOrganization.actual_direction_counts).sort((a: any, b: any) => b[1] - a[1]).map(([code, count]) => `${code} ${count}`).join(' · ') || '暂无正式归属工作' }}</p>
          <p><strong>最后核验：</strong>{{ eventDate(selectedOrganization.last_checked) }} · <strong>实质变化：</strong>{{ orgChanged(selectedOrganization) ? eventDate(orgChanged(selectedOrganization)) : '尚未登记' }}</p>
          <p :class="{ 'v3-warning': ['stale', 'failed', 'unavailable'].includes(selectedOrganization.source_health) }"><strong>来源状态：</strong>{{ selectedOrganization.source_health || '待核验' }}</p>
          <p v-if="organizationLoading" role="status">正在读取完整档案…</p>
          <p v-for="(leader, index) in selectedOrganization.leaders || []" :key="index"><strong>负责人：</strong>{{ leader.name || leader.person_name || displayText(leader) }} <span v-if="leader.valid_from || leader.active_from">{{ eventDate(leader.valid_from || leader.active_from) }}—{{ leader.valid_to || leader.active_to ? eventDate(leader.valid_to || leader.active_to) : '至今（结束日期未登记）' }}</span> <a v-if="leader.source_url || leader.evidence_url" :href="leader.source_url || leader.evidence_url" target="_blank" rel="noreferrer">官方来源</a></p>
          <a v-if="selectedOrganization.official_urls?.home" :href="selectedOrganization.official_urls.home" target="_blank" rel="noreferrer">打开官方主页</a>
          <a v-if="selectedOrganizationWorkIds.length" :href="databaseUrl(selectedOrganizationWorkIds, { relevance: 'all' })">查看完整已归属集合 · {{ selectedOrganizationWorkIds.length }} 项</a>
          <p v-else class="v3-muted">尚未登记具体工作归属；不表示该组没有研究发布。</p>
          <a v-if="selectedOrganizationPendingIds.length" class="v3-pending-link" :href="databaseUrl(selectedOrganizationPendingIds, { relevance: 'all' })">待核验归属 · {{ selectedOrganizationPendingIds.length }} 项（不计正式研究活动）</a>
          <a class="v3-pending-link" :href="withBase('/methods/coverage')">查看高信号待归属队列与覆盖缺口</a>
          <a :href="withBase(`/api/v1/organizations/${selectedOrganization.slug}.json`)">下载公开档案</a>
        </div>
        <ul>
          <li v-for="event in selectedOrganization.updates" :key="event.event_id"><span>{{ publicationEventDate(event) }} · {{ eventLabels[event.event_type] || event.event_type }} · {{ event.attribution_grade || '待核验' }}</span><a :href="event.url" target="_blank" rel="noreferrer">{{ event.title }}</a><a v-if="event.work_id" :href="databaseUrl([event.work_id])">查看研究与所有版本</a></li>
        </ul>
      </section>
      <section v-if="selectedOrganization" class="v3-analysis-section"><header><h2>合作关系与项目系列</h2><p>共同归属的 canonical work；合作不等于独立复现。</p></header><div class="v3-coverage-grid"><article v-for="org in selectedCollaborators" :key="org.organization_id"><h3><a :href="withBase(`/organizations/${org.slug}`)">{{ org.name }}</a></h3><a :href="databaseUrl(org.shared_work_ids)">{{ org.shared_work_ids.length }} 项联合研究</a></article></div><p v-if="!selectedCollaborators.length" class="v3-empty">当前归属证据尚未形成可确认的合作边；不代表不存在合作。</p><div v-for="(series, index) in selectedOrganization.project_series || []" :key="index" class="v3-note-row"><strong>{{ typeof series === 'string' ? series : series.name || series.title }}</strong><a v-if="series.work_ids?.length" :href="databaseUrl(series.work_ids)">项目系列全部工作</a></div><ul><li v-for="(gap, index) in selectedOrganization.information_gaps || []" :key="index">{{ displayText(gap) }}</li></ul></section>
      <ChartFrame v-if="mode === 'collaboration' && selectedOrganization && selectedCollaborators.length" title="联合研究网络" description="每条边都有联合 work 归属证据；不合并成持久组织，也不视为独立复现。" :height="Math.max(260, selectedCollaborators.length * 64 + 60)">
        <svg class="v3-collaboration-graph v3-desktop-chart" :viewBox="`0 0 900 ${Math.max(260, selectedCollaborators.length * 64 + 60)}`" role="img" :aria-label="`${selectedOrganization.name}与${selectedCollaborators.length}个研究组的联合研究网络`">
          <g v-for="(org, index) in selectedCollaborators" :key="org.organization_id"><path :d="`M 220 ${Math.max(260, selectedCollaborators.length * 64 + 60) / 2} C 440 ${Math.max(260, selectedCollaborators.length * 64 + 60) / 2}, 420 ${Number(index) * 64 + 42}, 620 ${Number(index) * 64 + 42}`" fill="none" stroke="var(--vp-c-divider)" :stroke-width="Math.min(6, org.shared_work_ids.length + 1)" /><a :href="databaseUrl(org.shared_work_ids)"><circle cx="620" :cy="Number(index) * 64 + 42" r="7" fill="var(--radar-series-2)" /><text x="637" :y="Number(index) * 64 + 45">{{ org.short_name || org.name }} · {{ org.shared_work_ids.length }}</text></a></g>
          <circle cx="220" :cy="Math.max(260, selectedCollaborators.length * 64 + 60) / 2" r="12" fill="var(--radar-series-1)" /><text x="20" :y="Math.max(260, selectedCollaborators.length * 64 + 60) / 2 - 24">{{ selectedOrganization.short_name || selectedOrganization.name }}</text>
        </svg>
        <div class="v3-mobile-org-list"><a v-for="org in selectedCollaborators" :key="org.organization_id" :href="databaseUrl(org.shared_work_ids)" class="v3-relation-row"><strong>{{ org.name }}</strong><span>{{ org.shared_work_ids.length }} 项联合研究</span></a></div>
        <template #table><table><thead><tr><th>中心研究组</th><th>合作研究组</th><th>联合工作</th></tr></thead><tbody><tr v-for="org in selectedCollaborators" :key="org.organization_id"><td>{{ selectedOrganization.name }}</td><td>{{ org.name }}</td><td><a :href="databaseUrl(org.shared_work_ids)">{{ org.shared_work_ids.length }} 项全部证据</a></td></tr></tbody></table></template>
      </ChartFrame>
      <section class="v3-org-summary">
        <div><strong>{{ activeOrganizations.length }}</strong><span>{{ selectedTier }} 组织</span></div>
        <div><strong>{{ activeOrganizations.filter((row: any) => row.source_health === 'healthy').length }}</strong><span>来源健康</span></div>
        <div><strong>{{ new Set(activeOrganizations.flatMap((row: any) => row.work_ids || [])).size }}</strong><span>归属研究（全局去重）</span></div>
      </section>
      <section v-if="mode === 'collaboration'" class="v3-analysis-section"><header><h2>选择组织展开合作关系</h2><p>仅使用 G1/G2 正式归属，选择下方任一组织查看联合工作集合。</p></header><div class="v3-collaboration-picker"><button v-for="org in activeOrganizations" :key="org.organization_id" type="button" :aria-pressed="selectedOrgSlug === org.slug" @click="selectOrganization(org)">{{ org.short_name || org.name }}</button></div></section>
      <template v-if="mode === 'organizations' && !props.organization">
      <ChartFrame title="组织 × 研究方向" :description="`${selectedTier} 层最近 12 个完整月；当前雇主不会覆盖历史归属`" :height="Math.max(520, topOrganizations.length * 25 + 90)">
        <template #actions><div class="v3-pagination"><button type="button" :disabled="organizationPage === 0" @click="organizationPage--" aria-label="上一页研究组">上一页</button><span aria-live="polite">{{ organizationPage + 1 }} / {{ organizationPages }} · 共 {{ activeOrganizations.length }} 组</span><button type="button" :disabled="organizationPage + 1 >= organizationPages" @click="organizationPage++" aria-label="下一页研究组">下一页</button></div></template>
        <div :ref="organizationHeatmap.element" class="v3-desktop-chart" role="img" aria-label="组织与研究方向覆盖热力图" />
        <div class="v3-mobile-org-list">
          <article v-for="org in topOrganizations" :key="org.organization_id">
            <a :href="withBase(`/organizations/${org.slug}`)"><strong>{{ org.name }}</strong></a><span>{{ org.recent_work_count }} 项</span>
            <p>{{ Object.entries(org.actual_direction_counts).sort((a: any, b: any) => b[1] - a[1]).slice(0, 4).map(([code, count]) => `${code} ${count}`).join(' · ') || '暂无正式归属工作' }}</p>
          </article>
        </div>
        <template #table><table><thead><tr><th>研究组</th><th v-for="direction in trends.directions" :key="direction.code">{{ direction.code }}</th></tr></thead><tbody><tr v-for="org in activeOrganizations" :key="org.organization_id"><th><a :href="withBase(`/organizations/${org.slug}`)">{{ org.name }}</a></th><td v-for="direction in trends.directions" :key="direction.code">{{ org.actual_direction_counts?.[direction.code] || 0 }}</td></tr></tbody></table></template>
      </ChartFrame>
      <ChartFrame title="组织发布节奏" description="论文/预印本、企业技术报告和模型/数据/项目分泳道累计" :height="380">
        <div :ref="organizationTimeline.element" role="img" aria-label="组织研究发布月度堆叠图" />
        <template #table><table><thead><tr><th>月份</th><th>论文/预印本</th><th>技术报告</th><th>其他发布</th></tr></thead><tbody><tr v-for="row in organizationTimelineRows" :key="row.month"><th>{{ row.month }}</th><td>{{ row.paper }}</td><td>{{ row.report }}</td><td>{{ row.release }}</td></tr></tbody></table></template>
      </ChartFrame>
      <section class="v3-startup-section">
        <header><div><p class="v3-eyebrow">STARTUP TECHNICAL REPORTS</p><h2>领先初创企业技术报告 · {{ startupReportCount }} 项</h2></div><p>展示全部已登记报告，不受最近月份与列表采样影响。</p></header>
        <article v-for="org in startups" :key="org.organization_id">
          <div class="v3-startup-name"><strong>{{ org.name }}</strong><span>{{ org.tier }} · {{ org.source_health }}</span></div>
          <p>{{ org.summary_zh }}</p>
          <ul>
            <li v-for="update in org.updates.filter((row: any) => row.event_type === 'technical_report')" :key="update.event_id">
              <a :href="update.url" target="_blank" rel="noreferrer">{{ update.title }}</a><span>{{ publicationEventDate(update) }} · 企业技术报告 · {{ update.independent_validation ? '有独立验证记录' : '第一方披露' }}</span><p>{{ update.summary_zh }}</p><a v-if="update.work_id" :href="databaseUrl([update.work_id])">证据及版本</a>
            </li>
            <li v-if="!org.updates.some((row: any) => row.event_type === 'technical_report')">尚未登记公开技术报告；请参见官方研究发布。</li>
          </ul>
        </article>
      </section>
      </template>
      <section v-if="!props.organization" class="v3-org-directory">
        <header><h2>{{ selectedTier }} 组织目录 · {{ activeOrganizations.length }}</h2><span>{{ organizationSort === 'changed' ? '最近实质变化优先' : '按名称浏览' }}</span></header>
        <a v-for="org in activeOrganizations" :key="org.organization_id" :href="withBase(`/organizations/${org.slug}`)">
          <div><strong>{{ org.name }}</strong><span>{{ org.entity_type }} · {{ org.region }}</span></div>
          <p>{{ org.summary_zh }}</p>
          <small>{{ org.recent_work_count }} 项工作 · {{ orgChanged(org) ? eventDate(orgChanged(org)) : '暂无登记变化' }} · 来源 {{ org.source_health }} · 核验 {{ eventDate(org.last_checked) }}</small>
        </a>
      </section>
    </template>

    <section v-if="mode === 'home'" class="v3-home-bottom">
      <div>
        <p class="v3-eyebrow">LATEST VERIFIED WORKS</p>
        <h2>{{ latestComplete.month }} 高信号工作</h2>
      </div>
      <div class="v3-latest-list">
        <a v-for="work in latestRows.slice(0, 8)" :key="work.work_id" :href="withBase(`/database/?work=${encodeURIComponent(work.work_id)}`)">
          <span>{{ work.primary_direction }}<template v-if="hasMonthEvidence"> · {{ work.evidence_grade }}</template></span><strong>{{ work.title }}</strong><small>{{ hasMonthEvidence && work.strict_peer_reviewed ? '当月已核实同行评审' : '公开研究信号' }}</small>
        </a>
      </div>
    </section>
  </div>
</template>

<style scoped>
.v3-research-shortcuts { display: flex; flex-wrap: wrap; gap: 6px 24px; margin: -4px 0 22px; font-size: 14px; }
.v3-research-shortcuts a { display: inline-flex; align-items: center; flex-wrap: wrap; gap: 7px; min-height: 44px; }
.v3-research-shortcuts span { color: var(--vp-c-text-2); border: 1px dashed var(--vp-c-divider); padding: 1px 6px; border-radius: 4px; font-size: 12px; }
.v3-research-shortcuts a:focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.v3-status-dependencies, .v3-status-followup { margin: 24px 0; padding: 18px 20px; border: 1px solid var(--vp-c-divider); border-left: 4px solid var(--vp-c-warning-1); border-radius: 10px; background: var(--vp-c-bg-soft); overflow-wrap: anywhere; }
.v3-status-dependencies.blocked { border-left-color: var(--vp-c-danger-1); }
.v3-status-dependencies h2 { margin: 0 0 12px; font-size: 1.1rem; line-height: 1.55; }
.v3-status-dependencies p, .v3-research-status-lane p { line-height: 1.75; }
.v3-status-dependencies ul { padding-left: 20px; }
.v3-status-dependencies li + li { margin-top: 20px; }
.v3-status-events { display: grid; gap: 14px; }
.v3-status-events article { min-width: 0; padding: 16px; border: 1px solid var(--vp-c-divider); border-radius: 8px; overflow-wrap: anywhere; }
.v3-status-events time { color: var(--vp-c-text-2); font-size: .85rem; }
.v3-status-events h4 { margin: 8px 0; line-height: 1.6; }
.v3-status-links { display: flex; flex-wrap: wrap; gap: 4px 16px; }
.v3-status-links a, .v3-status-cohort > article > a, .v3-status-followup > article > a { display: inline-flex; min-height: 44px; align-items: center; text-decoration: underline; overflow-wrap: anywhere; }
.v3-status-dependencies a:focus-visible, .v3-research-status-lane a:focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.v3-status-cohort { margin-top: 24px; }
@media (max-width: 767px) { .v3-status-dependencies, .v3-status-followup { padding: 14px; } .v3-status-events article { padding: 12px; } .v3-status-links { flex-direction: column; align-items: flex-start; } }
</style>
