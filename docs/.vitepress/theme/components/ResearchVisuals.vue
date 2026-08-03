<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, SankeyChart } from 'echarts/charts'
import { AriaComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import visualizationData from '../../data/home-visualizations.json'

echarts.use([
  LineChart,
  SankeyChart,
  AriaComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
])

const shareElement = ref<HTMLDivElement | null>(null)
const sankeyElement = ref<HTMLDivElement | null>(null)
const monthLabel = (month: string) => `${month.slice(2, 4)}.${month.slice(5)}`
const periodLabel = `${visualizationData.period.from.slice(0, 7)}—${visualizationData.period.until.slice(0, 7)}`
const tableRows = computed(() => visualizationData.shareTrend.months.map((month, index) => ({
  month,
  values: visualizationData.shareTrend.series.map((series) => series.shares[index]),
})))

let shareChart: echarts.ECharts | undefined
let sankeyChart: echarts.ECharts | undefined
let resizeObserver: ResizeObserver | undefined
let themeObserver: MutationObserver | undefined

const cssValue = (name: string, fallback: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback

const chartPalette = () => [
  cssValue('--radar-series-1', '#4f46e5'),
  cssValue('--radar-series-2', '#0891b2'),
  cssValue('--radar-series-3', '#7c3aed'),
  cssValue('--radar-series-4', '#d97706'),
  cssValue('--radar-series-5', '#059669'),
  cssValue('--radar-series-6', '#db2777'),
  cssValue('--radar-series-7', '#2563eb'),
  cssValue('--radar-series-8', '#64748b'),
]

const tooltipStyle = () => ({
  backgroundColor: cssValue('--vp-c-bg-elv', '#ffffff'),
  borderColor: cssValue('--vp-c-divider', '#e5e7eb'),
  textStyle: { color: cssValue('--vp-c-text-1', '#111827') },
})

const renderShareChart = () => {
  if (!shareChart) return
  const colors = chartPalette()
  const text = cssValue('--vp-c-text-2', '#4b5563')
  const divider = cssValue('--vp-c-divider', '#e5e7eb')
  shareChart.setOption({
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    color: colors,
    aria: {
      enabled: true,
      description: `最近十二个完整月各研究方向占全部直接候选论文的比例变化。`,
    },
    legend: {
      type: 'scroll',
      top: 0,
      left: 0,
      right: 0,
      itemWidth: 12,
      itemHeight: 8,
      textStyle: { color: text },
      pageTextStyle: { color: text },
    },
    grid: { left: 48, right: 18, top: 72, bottom: 42 },
    tooltip: {
      ...tooltipStyle(),
      trigger: 'axis',
      confine: true,
      formatter: (params: any[]) => {
        const index = params[0]?.dataIndex ?? 0
        const total = visualizationData.shareTrend.monthlyTotals[index]
        const lines = params
          .filter((item) => Number(item.value) > 0)
          .map((item) => `${item.marker}${item.seriesName}：${Number(item.value).toFixed(1)}%（${item.data.count} 篇）`)
        return `<strong>${visualizationData.shareTrend.months[index]}</strong> · 共 ${total} 篇<br/>${lines.join('<br/>')}`
      },
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: visualizationData.shareTrend.months.map(monthLabel),
      axisLine: { lineStyle: { color: divider } },
      axisTick: { show: false },
      axisLabel: { color: text, interval: 1 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '占比',
      nameTextStyle: { color: text },
      axisLabel: { color: text, formatter: '{value}%' },
      splitLine: { lineStyle: { color: divider, width: 1 } },
    },
    series: visualizationData.shareTrend.series.map((series, seriesIndex) => ({
      name: `${series.code} · ${series.name}`,
      type: 'line',
      stack: 'share',
      showSymbol: false,
      symbol: seriesIndex % 2 ? 'rect' : 'circle',
      lineStyle: { width: 1.2 },
      areaStyle: { opacity: 0.72 },
      emphasis: { focus: 'series' },
      data: series.shares.map((value, index) => ({ value, count: series.counts[index] })),
    })),
  }, true)
}

const renderSankeyChart = () => {
  if (!sankeyChart) return
  const colors = chartPalette()
  const topicColor = new Map(
    visualizationData.sankey.nodes.map((node) => [node.key, colors[(Number(node.code.slice(1)) - 1) % colors.length]]),
  )
  const text = cssValue('--vp-c-text-1', '#111827')
  sankeyChart.setOption({
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    aria: {
      enabled: true,
      description: `最近十二个完整月最强的二十四条研究方向共现关系。左侧是论文主方向，右侧是同一论文命中的关联方向。`,
    },
    tooltip: {
      ...tooltipStyle(),
      trigger: 'item',
      confine: true,
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          const source = visualizationData.sankey.nodes.find((node) => node.name === params.data.source)?.label
          const target = visualizationData.sankey.nodes.find((node) => node.name === params.data.target)?.label
          return `<strong>${source}</strong><br/>关联到 ${target}：${params.data.value} 篇`
        }
        return params.data.label
      },
    },
    series: [{
      type: 'sankey',
      left: 16,
      right: 16,
      top: 12,
      bottom: 12,
      nodeAlign: 'justify',
      nodeWidth: 12,
      nodeGap: 10,
      layoutIterations: 48,
      draggable: false,
      emphasis: { focus: 'adjacency' },
      lineStyle: { color: 'gradient', curveness: 0.52, opacity: 0.28 },
      label: { color: text, fontSize: 12 },
      data: visualizationData.sankey.nodes.map((node) => ({
        ...node,
        itemStyle: { color: topicColor.get(node.key) },
        label: {
          color: text,
          position: node.side === '主方向' ? 'right' : 'left',
          formatter: node.label,
        },
      })),
      links: visualizationData.sankey.links,
    }],
  }, true)
}

const renderCharts = () => {
  renderShareChart()
  renderSankeyChart()
}

onMounted(async () => {
  await nextTick()
  if (shareElement.value) shareChart = echarts.init(shareElement.value)
  if (sankeyElement.value) sankeyChart = echarts.init(sankeyElement.value)
  renderCharts()
  resizeObserver = new ResizeObserver(() => {
    shareChart?.resize()
    sankeyChart?.resize()
  })
  if (shareElement.value) resizeObserver.observe(shareElement.value)
  if (sankeyElement.value) resizeObserver.observe(sankeyElement.value)
  themeObserver = new MutationObserver(renderCharts)
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  shareChart?.dispose()
  sankeyChart?.dispose()
})
</script>

<template>
  <div class="home-research-visuals">
    <section class="radar-visual-section" aria-labelledby="share-trend-heading">
      <header class="radar-visual-heading">
        <h2 id="share-trend-heading">研究方向占比变化</h2>
        <p>{{ periodLabel }} · 最近 12 个完整月 · 前七大方向与其他方向合计</p>
      </header>
      <div
        ref="shareElement"
        class="radar-chart radar-share-chart"
        role="img"
        aria-label="最近十二个完整月研究方向论文占比堆叠面积图"
      />
      <details class="radar-chart-data">
        <summary>查看月度占比数据</summary>
        <table>
          <thead>
            <tr>
              <th>月份</th>
              <th v-for="series in visualizationData.shareTrend.series" :key="series.key">
                {{ series.code }} · {{ series.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in tableRows" :key="row.month">
              <td>{{ row.month }}</td>
              <td v-for="(value, index) in row.values" :key="index">{{ value.toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </details>
    </section>

    <section class="radar-visual-section" aria-labelledby="sankey-heading">
      <header class="radar-visual-heading">
        <h2 id="sankey-heading">研究方向共现桑基图</h2>
        <p>同一批论文中最强的 {{ visualizationData.sankey.linkCount }} 条“主方向 → 关联方向”关系；流量为论文数，不代表方向迁移</p>
      </header>
      <div
        ref="sankeyElement"
        class="radar-chart radar-sankey-chart"
        role="img"
        aria-label="研究论文主方向与关联方向共现关系桑基图"
      />
    </section>
  </div>
</template>
