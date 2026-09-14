<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import * as echarts from 'echarts/core'
import { LineChart, ScatterChart } from 'echarts/charts'
import { AriaComponent, GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ChartFrame from './ChartFrame.vue'
import { chartTokens, useEChart } from '../composables/useEChart'
import { completeMonthRange, monthlyValueLabel, splitMonthlySeries } from '../lib/monthlySeries'

echarts.use([LineChart, ScatterChart, AriaComponent, GridComponent, TooltipComponent, CanvasRenderer])
const props = defineProps<{
  code: string; label: string; values: number[]; metric: string; metricLabel: string;
  months: string[]; completeMonths: string[]; provisionalMonth: string; provisionalHasData: boolean;
  momentum?: string;
}>()
const series = computed(() => splitMonthlySeries(props.months, props.values, props.completeMonths, props.provisionalMonth, props.provisionalHasData))
const momentumLabels: Record<string, string> = { rising: '上升', stable: '稳定', cooling: '降温' }
const description = computed(() => `${props.metricLabel} · 完整月发文动量：${momentumLabels[props.momentum || ''] || '待判断'}；暂行月不连线`)
const chart = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false,
    aria: { enabled: true, description: `${props.label}。${completeMonthRange(props.completeMonths, props.provisionalMonth)}。${props.provisionalHasData ? '暂行值为空心点，不参与完整月折线。' : '暂行月数据未知，不作为零值。'}` },
    tooltip: { trigger: 'axis', confine: true, backgroundColor: tokens.background, borderColor: tokens.divider, textStyle: { color: tokens.text }, formatter: (items: any[]) => { const index = items[0]?.data?.monthIndex ?? items[0]?.dataIndex; return index === undefined ? '' : `${props.months[index]}${props.months[index] === props.provisionalMonth ? '（暂行）' : ''}<br/>${monthlyValueLabel(series.value.display[index], props.metric)}` } },
    grid: { left: 42, right: 12, top: 12, bottom: 34 },
    xAxis: { type: 'category', data: props.months.map((month) => month === props.provisionalMonth ? `${month.slice(5)}月*` : month.slice(2).replace('-', '.')), axisLabel: { color: tokens.muted, fontSize: 10, interval: 2, showMaxLabel: true }, axisTick: { show: false }, axisLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'value', min: 0, axisLabel: { color: tokens.muted, fontSize: 10, formatter: (value: number) => props.metric === 'shares' ? `${Math.round(value * 100)}%` : String(value) }, splitNumber: 3, splitLine: { lineStyle: { color: tokens.divider } } },
    series: [
      { name: '完整月', type: 'line', data: series.value.complete, connectNulls: false, showSymbol: false, lineStyle: { color: tokens.palette[0], width: 2 }, itemStyle: { color: tokens.palette[0] } },
      { name: '暂行月（独立观测）', type: 'scatter', data: series.value.provisional.flatMap((value, index) => value === null ? [] : [{ value: [index, value], monthIndex: index }]), symbol: 'emptyCircle', symbolSize: 8, itemStyle: { color: tokens.muted, borderColor: tokens.muted, borderWidth: 2 } },
    ],
  }
})
</script>

<template>
  <ChartFrame class="v3-direction-chart" :title="`${code} · ${label}`" :description="description" :height="150" compact>
    <div :ref="chart.element" role="img" :aria-label="`${label}月度${metricLabel}；暂行月独立展示`" />
    <template #table><table><thead><tr><th>月份</th><th>{{ metricLabel }}</th></tr></thead><tbody><tr v-for="(month, index) in months" :key="month"><th>{{ month }}{{ month === provisionalMonth ? ' · 暂行' : '' }}</th><td>{{ monthlyValueLabel(series.display[index], metric) }}</td></tr></tbody></table></template>
    <template #actions><div><a :href="withBase(`/database/?directions=${code}`)">查看工作</a> · <a :href="withBase(`/organizations/people/?directions=${code}`)">相关研究者</a></div></template>
  </ChartFrame>
</template>
