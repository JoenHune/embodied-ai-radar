<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, AriaComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ChartFrame from './ChartFrame.vue'
import { chartTokens, useEChart } from '../composables/useEChart'
import { directionShortNames } from '../lib/research-card.mjs'

echarts.use([BarChart, GridComponent, TooltipComponent, AriaComponent, CanvasRenderer])
const props = defineProps<{ snapshot: any }>()
const emit = defineEmits<{ direction: [code: string] }>()
const total = computed(() => props.snapshot.coverage?.included_works || 0)
const segments = computed(() => {
  const top = [...props.snapshot.directions].sort((a, b) => b.primary_count - a.primary_count).slice(0, 5)
  return [...top.map(row => ({ code: row.code, label: directionShortNames[row.code] || row.label, count: row.primary_count })),
    { code: 'other', label: '其他方向', count: Math.max(0, total.value - top.reduce((n, row) => n + row.primary_count, 0)) }]
})
const percent = (count: number) => total.value ? `${(count / total.value * 100).toFixed(1)}%` : '暂无数据'
const chart = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false, aria: { enabled: true, description: `${props.snapshot.month}已收录${total.value}项工作的主方向构成；非互联网全量科研份额。` },
    color: [...tokens.palette.slice(0, 5), tokens.divider],
    grid: { top: 4, bottom: 4, left: 0, right: 0 },
    tooltip: { confine: true, backgroundColor: tokens.background, borderColor: tokens.divider, textStyle: { color: tokens.text }, formatter: (item: any) => `${item.seriesName} · ${percent(item.value)}<br/>${item.value} / ${total.value} 项${item.seriesIndex < 5 ? '<br/>点击查看相关研究' : ''}` },
    xAxis: { type: 'value', max: Math.max(total.value, 1), show: false }, yAxis: { type: 'category', data: [props.snapshot.month], show: false },
    series: segments.value.map(row => ({ name: row.label, type: 'bar', stack: 'composition', data: [row.count], barWidth: 28 })),
  }
}, chart => chart.on('click', (item: any) => { const row = segments.value[item.seriesIndex]; if (row && row.code !== 'other') emit('direction', row.code) }))
</script>

<template>
  <ChartFrame class="direction-share-overview" :title="`${snapshot.month} · 已收录研究的方向构成`" :description="`${total} 项工作，每项只计一个主方向。点击方向，查看对应论文与报告。`" :height="40" compact>
    <div :ref="chart.element" role="img" aria-label="本月主要研究方向的占比构成" />
    <template #actions><a :href="withBase('/trends/')">12 个月变化 ↗</a></template>
    <template #table><table><thead><tr><th>主方向</th><th>工作数</th><th>当月占比</th></tr></thead><tbody><tr v-for="row in snapshot.directions" :key="row.code"><th>{{ row.label }}</th><td>{{ row.primary_count }}</td><td>{{ percent(row.primary_count) }}</td></tr></tbody></table></template>
  </ChartFrame>
  <div class="share-overview-legend"><template v-for="(row, i) in segments" :key="row.code"><button v-if="row.code !== 'other'" type="button" @click="emit('direction', row.code)"><i :style="{ background: `var(--radar-series-${i + 1})` }" /><span>{{ row.label }}</span><strong>{{ percent(row.count) }}</strong></button><span v-else class="other-directions"><i />{{ row.label }} <strong>{{ percent(row.count) }}</strong></span></template></div>
</template>

<style scoped>
.direction-share-overview { margin-bottom: 0; }
.direction-share-overview :deep(header) { margin-bottom: 8px; }
.direction-share-overview :deep(h2) { font-size: 20px; }
.share-overview-legend { display: flex; gap: 12px 20px; flex-wrap: wrap; margin: 12px 0 24px; font-size: 13px; }
.share-overview-legend button, .other-directions { display: inline-flex; align-items: center; gap: 7px; padding: 4px 0; }
.share-overview-legend i { width: 9px; height: 9px; border-radius: 2px; background: var(--vp-c-divider); }
.share-overview-legend strong { font-weight: 500; }
</style>
