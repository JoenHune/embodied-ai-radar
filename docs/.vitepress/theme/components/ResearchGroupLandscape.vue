<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import * as echarts from 'echarts/core'
import { BarChart, GraphChart, ScatterChart } from 'echarts/charts'
import {
  AriaComponent, AxisPointerComponent, DataZoomComponent, GridComponent,
  LegendComponent, TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import radarData from '../../data/research-groups.json'

echarts.use([
  ScatterChart, BarChart, GraphChart,
  AriaComponent, AxisPointerComponent, DataZoomComponent, GridComponent,
  LegendComponent, TooltipComponent, CanvasRenderer,
])

const radar = radarData as any
const viz = radar.visualizations
const cohort = ref<'startup' | 'anchors' | 'all'>('startup')
const timelineElement = ref<HTMLDivElement | null>(null)
const evidenceElement = ref<HTMLDivElement | null>(null)
const networkElement = ref<HTMLDivElement | null>(null)
const selectedDirection = ref<any>(null)
const selectedStack = ref<any>(null)
const groupById = new Map(radar.groups.map((group: any) => [group.organization_id, group]))
const eventById = new Map(viz.activity_events.map((event: any) => [event.update_id, event]))
const cohortLabels = { startup: '领先初创', anchors: '研究锚点', all: '全部研究组' }

const cohortGroups = computed(() => viz.cohorts[cohort.value]
  .map((id: string) => groupById.get(id))
  .filter(Boolean))
const cohortIds = computed(() => new Set(cohortGroups.value.map((group: any) => group.organization_id)))
const directionCellMap = computed(() => new Map<string, any>(viz.group_direction_cells
  .filter((cell: any) => cohortIds.value.has(cell.organization_id))
  .map((cell: any) => [`${cell.organization_id}|${cell.direction_code}`, cell])))
const activityGroups = computed(() => cohortGroups.value
  .map((group: any) => ({
    ...group,
    activity_count: viz.activity_events.filter((event: any) => event.organization_id === group.organization_id).length,
  }))
  .filter((group: any) => group.activity_count > 0)
  .sort((left: any, right: any) => right.activity_count - left.activity_count || left.display_name.localeCompare(right.display_name))
  .slice(0, cohort.value === 'startup' ? 8 : 12))
const activityIds = computed(() => new Set(activityGroups.value.map((group: any) => group.organization_id)))
const activityEvents = computed(() => viz.activity_events.filter((event: any) => activityIds.value.has(event.organization_id)))
const evidenceRows = computed(() => activityGroups.value.map((group: any) => ({
  group,
  ...viz.evidence_mix.find((row: any) => row.organization_id === group.organization_id),
})))
const startupGroups = computed(() => viz.cohorts.startup.map((id: string) => groupById.get(id)).filter(Boolean))
const stackCellMap = new Map<string, any>(viz.startup_stack_cells.map((cell: any) => [`${cell.organization_id}|${cell.stack_key}`, cell]))
const directionEvents = computed(() => selectedDirection.value?.update_ids.map((id: string) => eventById.get(id)).filter(Boolean) ?? [])
const periodLabel = `${viz.period.from.slice(0, 7)}—${viz.period.until.slice(0, 7)}`

const directionCell = (organizationId: string, directionCode: string): any =>
  directionCellMap.value.get(`${organizationId}|${directionCode}`) ?? { recent_count: 0, declared: false, update_ids: [] }
const stackCell = (organizationId: string, key: string): any =>
  stackCellMap.get(`${organizationId}|${key}`) ?? { level: 0, sources: [] }
const stackLabel = (level: number) => level === 3 ? '3 · 正式报告' : level === 2 ? '2 · 项目/模型发布' : level === 1 ? '1 · Demo/公司声明' : '未发现公开证据'
const selectDirection = (group: any, direction: any) => {
  const cell = directionCell(group.organization_id, direction.code)
  selectedDirection.value = { ...cell, group, direction }
}
const selectStack = (group: any, column: any) => {
  selectedStack.value = { ...stackCell(group.organization_id, column.key), group, column }
}

let timelineChart: echarts.ECharts | undefined
let evidenceChart: echarts.ECharts | undefined
let networkChart: echarts.ECharts | undefined
let resizeObserver: ResizeObserver | undefined
let themeObserver: MutationObserver | undefined
let frame = 0

const cssValue = (name: string, fallback: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
const escapeHtml = (value: unknown) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[character] ?? character))
const tooltipStyle = () => ({
  backgroundColor: cssValue('--vp-c-bg-elv', '#fff'),
  borderColor: cssValue('--vp-c-divider', '#e5e7eb'),
  textStyle: { color: cssValue('--vp-c-text-1', '#111827'), fontSize: 12 },
})
const colors = () => ['#166534', '#2563eb', '#7c3aed', '#d97706', '#0891b2', '#db2777']
const artifactSymbols: Record<string, string> = {
  peer_reviewed: 'circle', preprint: 'emptyCircle', technical_report: 'diamond',
  model_data_code: 'rect', project_system: 'triangle', demo_deployment: 'emptyDiamond',
}

const renderTimeline = () => {
  if (!timelineChart) return
  const text = cssValue('--vp-c-text-2', '#4b5563')
  const divider = cssValue('--vp-c-divider', '#e5e7eb')
  const palette = colors()
  timelineChart.setOption({
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    color: palette,
    aria: { enabled: true, description: `研究组在 ${periodLabel} 内的公开研究动态。形状表示证据材料类型。` },
    legend: { type: 'scroll', top: 0, textStyle: { color: text }, itemWidth: 13, itemHeight: 9 },
    grid: { left: 118, right: 18, top: 58, bottom: 42 },
    tooltip: {
      ...tooltipStyle(), trigger: 'item', confine: true, triggerOn: 'mousemove|click',
      formatter: (params: any) => {
        const item = params.data
        return `<strong>${escapeHtml(item.title)}</strong><br/>${escapeHtml(item.group_name)} · ${escapeHtml(item.published_at)}<br/>${escapeHtml(item.artifact_label)} · ${escapeHtml(item.evidence_grade)}<br/>${item.claim_status === 'company_self_report' ? '<b>未同行评审·公司自报</b>' : escapeHtml(item.claim_status)}<br/>${escapeHtml(item.direction_codes.join(' · '))}`
      },
    },
    xAxis: {
      type: 'time', min: viz.period.from, max: viz.period.until,
      splitNumber: window.innerWidth < 480 ? 4 : 7,
      axisLabel: {
        color: text,
        hideOverlap: true,
        formatter: (value: number) => {
          const month = new Date(value).getUTCMonth() + 1
          if (window.innerWidth < 480 && ![2, 6, 10].includes(month)) return ''
          return echarts.time.format(value, '{MM}月', false)
        },
      },
      axisLine: { lineStyle: { color: divider } }, splitLine: { show: true, lineStyle: { color: divider } },
    },
    yAxis: {
      type: 'category', data: activityGroups.value.map((group: any) => group.short_name),
      axisLabel: { color: text, width: 104, overflow: 'truncate' }, axisTick: { show: false },
      axisLine: { lineStyle: { color: divider } },
    },
    dataZoom: [{ type: 'inside', filterMode: 'none', xAxisIndex: 0 }],
    series: viz.artifact_classes.map((artifact: any, index: number) => ({
      name: artifact.label,
      type: 'scatter',
      symbol: artifactSymbols[artifact.key] ?? 'circle',
      symbolSize: artifact.key === 'technical_report' ? 13 : 11,
      itemStyle: { color: palette[index % palette.length], borderWidth: 1.5 },
      emphasis: { scale: 1.5, focus: 'series' },
      data: activityEvents.value.filter((event: any) => event.artifact_class === artifact.key).map((event: any) => ({
        ...event,
        group_name: (groupById.get(event.organization_id) as any)?.display_name,
        value: [event.published_at, (groupById.get(event.organization_id) as any)?.short_name],
      })),
    })),
  }, true)
}

const renderEvidence = () => {
  if (!evidenceChart) return
  const text = cssValue('--vp-c-text-2', '#4b5563')
  const divider = cssValue('--vp-c-divider', '#e5e7eb')
  evidenceChart.setOption({
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    color: colors(),
    aria: { enabled: true, description: '各研究组最近十二个月公开动态按证据材料类型的百分比结构。' },
    legend: { type: 'scroll', top: 0, textStyle: { color: text }, itemWidth: 13, itemHeight: 9 },
    grid: { left: 118, right: 52, top: 62, bottom: 24 },
    tooltip: {
      ...tooltipStyle(), trigger: 'axis', axisPointer: { type: 'shadow' }, confine: true,
      formatter: (params: any[]) => {
        const total = params[0]?.data?.total ?? 0
        const rows = params.filter((item) => item.data.count > 0).map((item) => `${item.marker}${escapeHtml(item.seriesName)}：${item.data.count} 项`)
        return `<strong>${escapeHtml(params[0]?.axisValue)}</strong> · 共 ${total} 项<br/>${rows.join('<br/>')}`
      },
    },
    xAxis: { type: 'value', max: 100, axisLabel: { color: text, formatter: '{value}%' }, splitLine: { lineStyle: { color: divider } } },
    yAxis: { type: 'category', data: evidenceRows.value.map((row: any) => row.group.short_name), axisLabel: { color: text, width: 104, overflow: 'truncate' }, axisTick: { show: false } },
    series: viz.artifact_classes.map((artifact: any, index: number) => ({
      name: artifact.label, type: 'bar', stack: 'total', barMaxWidth: 24,
      label: index === viz.artifact_classes.length - 1 ? {
        show: true, position: 'right', color: text, formatter: (params: any) => `${params.data.total} 项`,
      } : { show: false },
      data: evidenceRows.value.map((row: any) => ({
        value: row.total ? Number((100 * row.counts[artifact.key] / row.total).toFixed(2)) : 0,
        count: row.counts[artifact.key], total: row.total,
      })),
    })),
  }, true)
}

const renderNetwork = () => {
  if (!networkChart) return
  const text = cssValue('--vp-c-text-1', '#111827')
  const categories = [...new Set(viz.collaboration_nodes.map((node: any) => node.category))]
  const degree = new Map<string, number>()
  viz.collaboration_edges.forEach((edge: any) => {
    degree.set(edge.source, (degree.get(edge.source) ?? 0) + edge.value)
    degree.set(edge.target, (degree.get(edge.target) ?? 0) + edge.value)
  })
  networkChart.setOption({
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    color: colors(),
    aria: { enabled: true, description: '合作边只来自同一 canonical work 上的多组 G1/G2 归属，不代表全球合作覆盖。' },
    tooltip: {
      ...tooltipStyle(), confine: true,
      formatter: (params: any) => params.dataType === 'edge'
        ? `${escapeHtml((groupById.get(params.data.source) as any)?.display_name)} × ${escapeHtml((groupById.get(params.data.target) as any)?.display_name)}<br/>${params.data.value} 项共同 canonical work`
        : `<strong>${escapeHtml(params.data.display_name)}</strong><br/>${params.data.degree} 项合作 work`,
    },
    legend: [{ data: categories, textStyle: { color: text }, top: 0 }],
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: false, top: 42, bottom: 12,
      categories: categories.map((name) => ({ name })),
      force: { repulsion: 260, edgeLength: [80, 150], gravity: 0.08 },
      emphasis: { focus: 'adjacency' },
      label: { show: true, color: text, fontSize: 11, position: 'right' },
      lineStyle: { color: 'source', curveness: 0.12, opacity: 0.5 },
      data: viz.collaboration_nodes.map((node: any) => ({
        ...node, display_name: (groupById.get(node.id) as any)?.display_name,
        category: categories.indexOf(node.category), degree: degree.get(node.id) ?? 0,
        symbolSize: 18 + Math.sqrt(degree.get(node.id) ?? 1) * 7,
      })),
      links: viz.collaboration_edges,
    }],
  }, true)
}

const renderCharts = () => { renderTimeline(); renderEvidence(); renderNetwork() }
const scheduleResize = () => {
  if (frame) return
  frame = window.requestAnimationFrame(() => {
    frame = 0
    timelineChart?.resize(); evidenceChart?.resize(); networkChart?.resize()
  })
}
const changeCohort = async () => { await nextTick(); renderTimeline(); renderEvidence() }

onMounted(async () => {
  await nextTick()
  if (timelineElement.value) timelineChart = echarts.init(timelineElement.value)
  if (evidenceElement.value) evidenceChart = echarts.init(evidenceElement.value)
  if (networkElement.value) networkChart = echarts.init(networkElement.value)
  timelineChart?.on('click', (params: any) => { if (params.data?.url) window.open(params.data.url, '_blank', 'noopener') })
  renderCharts()
  resizeObserver = new ResizeObserver(scheduleResize)
  ;[timelineElement.value, evidenceElement.value, networkElement.value].forEach((element) => element && resizeObserver?.observe(element))
  themeObserver = new MutationObserver(renderCharts)
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect(); themeObserver?.disconnect()
  if (frame) window.cancelAnimationFrame(frame)
  timelineChart?.dispose(); evidenceChart?.dispose(); networkChart?.dispose()
})
</script>

<template>
  <section class="group-landscape" aria-labelledby="group-landscape-heading">
    <header class="group-landscape-header">
      <div>
        <p class="group-landscape-kicker">KEY GROUP LANDSCAPE</p>
        <h2 id="group-landscape-heading">关键组工作全景</h2>
        <p>{{ periodLabel }} · 默认聚焦领先初创，可切换研究锚点或全部组。</p>
      </div>
      <label class="landscape-cohort">观察集
        <select v-model="cohort" @change="changeCohort">
          <option v-for="(label, key) in cohortLabels" :key="key" :value="key">{{ label }}</option>
        </select>
      </label>
    </header>

    <section class="landscape-panel" aria-labelledby="direction-matrix-heading">
      <header><h3 id="direction-matrix-heading">组 × 研究方向</h3><p>数字=近 12 个月有来源更新；○=组织自述方向但窗口内未见工作证据；空白≠不具备能力。</p></header>
      <div class="matrix-scroll" tabindex="0" aria-label="研究组和 D1 到 D15 方向矩阵">
        <div class="direction-matrix" :style="{ '--matrix-rows': cohortGroups.length }">
          <div class="matrix-corner">研究组</div>
          <div v-for="direction in viz.directions" :key="direction.code" class="matrix-column-heading" :title="direction.label">{{ direction.code }}</div>
          <template v-for="group in cohortGroups" :key="group.organization_id">
            <a class="matrix-row-heading" :href="withBase(`/groups/${group.slug}`)">{{ group.short_name }}</a>
            <button
              v-for="direction in viz.directions" :key="direction.code"
              class="direction-cell"
              :data-level="Math.min(directionCell(group.organization_id, direction.code).recent_count, 4)"
              :data-declared="directionCell(group.organization_id, direction.code).declared"
              :aria-label="`${group.display_name} ${direction.code} ${direction.label}：${directionCell(group.organization_id, direction.code).recent_count} 项近期更新`"
              @click="selectDirection(group, direction)"
            >{{ directionCell(group.organization_id, direction.code).recent_count || (directionCell(group.organization_id, direction.code).declared ? '○' : '·') }}</button>
          </template>
        </div>
      </div>
      <div v-if="selectedDirection" class="matrix-detail" aria-live="polite">
        <strong>{{ selectedDirection.group.display_name }} · {{ selectedDirection.direction.code }} {{ selectedDirection.direction.label }}</strong>
        <span v-if="!directionEvents.length">当前窗口未发现可追溯更新。</span>
        <a v-for="event in directionEvents" :key="event.update_id" :href="event.url" target="_blank" rel="noopener">{{ event.published_at }} · {{ event.title }}</a>
      </div>
    </section>

    <section class="landscape-panel" aria-labelledby="timeline-heading">
      <header><h3 id="timeline-heading">12 个月工作时间线</h3><p>每个点是一项更新；菱形=技术报告，圆=评审/预印本，矩形=模型数据代码，空心=部署/Demo。点选打开来源。</p></header>
      <div ref="timelineElement" class="landscape-chart timeline-chart" role="img" aria-label="研究组最近十二个月活动时间线" />
      <details class="radar-chart-data"><summary>查看时间线数据</summary>
        <ul><li v-for="event in activityEvents" :key="event.update_id"><a :href="event.url">{{ event.published_at }} · {{ (groupById.get(event.organization_id) as any)?.display_name }} · {{ event.title }}</a> — {{ event.artifact_label }}</li></ul>
      </details>
    </section>

    <section class="landscape-panel" aria-labelledby="stack-heading">
      <header><h3 id="stack-heading">领先初创技术栈矩阵</h3><p>3=正式技术报告/论文，2=模型或项目发布，1=官方 Demo/公司声明。数字表示材料类型，不是能力评分。</p></header>
      <div class="matrix-scroll" tabindex="0" aria-label="初创企业技术栈证据矩阵">
        <div class="startup-stack-matrix">
          <div class="matrix-corner">公司</div>
          <div v-for="column in viz.startup_stack_columns" :key="column.key" class="stack-column-heading"><small>{{ column.group }}</small><span>{{ column.label }}</span></div>
          <template v-for="group in startupGroups" :key="group.organization_id">
            <a class="matrix-row-heading" :href="withBase(`/groups/${group.slug}`)">{{ group.short_name }}</a>
            <button v-for="column in viz.startup_stack_columns" :key="column.key" class="stack-cell" :data-level="stackCell(group.organization_id, column.key).level" :aria-label="`${group.display_name} ${column.label}：${stackLabel(stackCell(group.organization_id, column.key).level)}`" @click="selectStack(group, column)">{{ stackCell(group.organization_id, column.key).level || '·' }}</button>
          </template>
        </div>
      </div>
      <div v-if="selectedStack" class="matrix-detail" aria-live="polite">
        <strong>{{ selectedStack.group.display_name }} · {{ selectedStack.column.label }} · {{ stackLabel(selectedStack.level) }}</strong>
        <span v-if="!selectedStack.sources.length">未发现公开证据，不代表不具备该能力。</span>
        <a v-for="source in selectedStack.sources" :key="source.url" :href="source.url" target="_blank" rel="noopener">{{ source.published_at }} · {{ source.title }} · {{ source.claim_status === 'company_self_report' ? '未同行评审·公司自报' : source.claim_status }}</a>
      </div>
    </section>

    <section class="landscape-panel" aria-labelledby="evidence-heading">
      <header><h3 id="evidence-heading">证据材料结构</h3><p>100% 横向堆叠，条尾是绝对更新数。优先使用 canonical 同行评审状态，不仅依赖页面类型。</p></header>
      <div ref="evidenceElement" class="landscape-chart evidence-chart" role="img" aria-label="研究组公开证据材料结构百分比堆叠条形图" />
    </section>

    <section class="landscape-panel" aria-labelledby="network-heading">
      <header><h3 id="network-heading">合作与联合发布网络</h3><p>当前仅显示同一 canonical work 上的多组 G1/G2 归属；节点少反映公开证据覆盖有限，不是研究影响力排名。</p></header>
      <div ref="networkElement" class="landscape-chart network-chart" role="img" aria-label="研究组 canonical work 合作网络" />
      <details class="radar-chart-data"><summary>查看合作邻接表</summary>
        <ul><li v-for="edge in viz.collaboration_edges" :key="`${edge.source}-${edge.target}`">{{ (groupById.get(edge.source) as any)?.display_name }} × {{ (groupById.get(edge.target) as any)?.display_name }}：{{ edge.value }} 项 canonical work</li></ul>
      </details>
    </section>
  </section>
</template>
