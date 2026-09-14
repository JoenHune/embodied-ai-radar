<script setup lang="ts">
import { computed, ref } from 'vue'
import DirectionTrendChart from './DirectionTrendChart.vue'
import { completeMonthRange, monthlyValueLabel, splitMonthlySeries } from '../lib/monthlySeries'

type Series = { code: string; label: string; counts: number[]; shares: number[]; multi_label_counts: number[] }
const props = defineProps<{ series: Series[]; months: string[]; completeMonths: string[]; provisionalMonth: string; provisionalHasData: boolean; ledger: any[] }>()
const ledgerByCode = computed(() => new Map(props.ledger.map((row) => [row.code, row])))
const metric = ref<'shares' | 'counts' | 'multi_label_counts'>('shares')
const metricLabels = { shares: '主方向份额', counts: '主方向工作数', multi_label_counts: '多标签工作数' }
const displayValues = (row: Series) => splitMonthlySeries(props.months, row[metric.value], props.completeMonths, props.provisionalMonth, props.provisionalHasData).display
</script>

<template>
  <div class="v3-trend-metric"><label>比较口径<select v-model="metric"><option v-for="(label, value) in metricLabels" :key="value" :value="value">{{ label }}</option></select></label><p>{{ completeMonthRange(completeMonths, provisionalMonth) }}。{{ provisionalHasData ? '暂行值仅画灰色空心点，不与完整月连线。' : '暂行月尚无采集数据，显示未知而不是零。' }}</p></div>
  <div class="v3-small-multiples" :aria-label="`D1 到 D15 的月度${metricLabels[metric]}小多图`">
    <DirectionTrendChart v-for="row in series" :key="row.code" :code="row.code" :label="row.label" :values="row[metric]" :metric="metric" :metric-label="metricLabels[metric]" :months="months" :complete-months="completeMonths" :provisional-month="provisionalMonth" :provisional-has-data="provisionalHasData" :momentum="ledgerByCode.get(row.code)?.momentum" />
  </div>
  <details class="v3-chart-table"><summary>查看全部方向月度数据</summary><div class="v3-table-scroll" tabindex="0" aria-label="全部方向月度数据，可横向滚动"><table><thead><tr><th>方向 · {{ metricLabels[metric] }}</th><th v-for="month in months" :key="month">{{ month }}{{ month === provisionalMonth ? ' · 暂行' : '' }}</th></tr></thead><tbody><tr v-for="row in series" :key="row.code"><th>{{ row.code }} {{ row.label }}</th><td v-for="(value, index) in displayValues(row)" :key="index">{{ monthlyValueLabel(value, metric) }}</td></tr></tbody></table></div></details>
</template>
