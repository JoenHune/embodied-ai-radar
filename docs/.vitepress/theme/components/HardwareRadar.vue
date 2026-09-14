<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, withBase } from 'vitepress'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { AriaComponent, GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ChartFrame from './ChartFrame.vue'
import ResearchCard from './ResearchCard.vue'
import { chartTokens, useEChart } from '../composables/useEChart'
import { eventDate } from '../lib/dates'

echarts.use([BarChart, AriaComponent, GridComponent, TooltipComponent, CanvasRenderer])
type Usage = { hardware_id: string; name: string; category: string; role: string; setting: string; source_url: string; source_locator?: string; statement: string; observed_at?: string; configuration?: unknown }
type Work = { work_id: string; title: string; first_public_date?: string; hardware_usage?: Usage[]; [key: string]: any }
type Device = { hardware_id: string; slug: string; name: string; vendor?: string; category: string; identity_level?: string; official_url?: string; work_ids?: string[] }
type EquipmentIndex = { schema_version: string; dataset_version: string; source_version?: string; data_through?: string; window?: { complete_months?: string[]; provisional_month?: string }; counts: { devices: number; usage_links: number; works: number; hardware_candidates: number }; categories: { code: string; label: string; devices: number; works: number }[]; devices: Device[] }
type Filters = { category: string; device: string; setting: string; role: string; month: string }
const allowedCategories = new Set(['robot_platform', 'robot_arm', 'dexterous_hand', 'gripper', 'compute_platform', 'data_collection', 'tactile_sensor', 'force_sensor', 'vision_sensor'])
const settingLabels: Record<string, string> = { real: '真实设备', simulation: '仿真环境', dataset: '数据集', unknown: '环境未说明' }
const roleLabels: Record<string, string> = { real_robot: '真机执行', simulated_robot: '仿真机器人', training_compute: '训练算力', inference_compute: '推理算力', data_collection: '数据采集', sensing: '感知', dataset_source: '数据来源' }
const identityLabels: Record<string, string> = { model_specified: '具体型号已明确', family_only: '仅确认型号系列', unspecified: '型号未公开', unknown: '身份粒度未说明' }
const initial = (): Filters => ({ category: '', device: '', setting: '', role: '', month: '' })
const index = ref<EquipmentIndex | null>(null)
const rows = ref<Work[]>([])
const filters = ref<Filters>(initial())
const shown = ref(12)
const loading = ref(true)
const error = ref('')
const list = ref<HTMLElement | null>(null)
const router = useRouter()
let controller: AbortController | undefined
let requestId = 0
let disposed = false
let releaseRouteGuard = () => {}
const publicUrl = (value: unknown): string | undefined => typeof value === 'string' && /^https?:\/\//i.test(value) ? value : undefined
const categoryLabels = computed<Record<string, string>>(() => Object.fromEntries((index.value?.categories || []).filter(category => allowedCategories.has(category.code)).map(category => [category.code, category.label])))
const knownCategory = (value: string) => Object.hasOwn(categoryLabels.value, value)
const devices = computed(() => (index.value?.devices || []).filter(device => knownCategory(device.category)).slice().sort((a, b) => a.name.localeCompare(b.name, 'zh-CN')))
const deviceMap = computed(() => new Map(devices.value.map(device => [device.hardware_id, device])))
const monthOf = (work: Work) => /^\d{4}-(0[1-9]|1[0-2])/.test(work.first_public_date || '') ? work.first_public_date!.slice(0, 7) : 'unknown'
const provisionalMonth = computed(() => index.value?.window?.provisional_month || '')
const months = computed(() => [...new Set([...(index.value?.window?.complete_months || []), provisionalMonth.value, ...usableWorks.value.map(monthOf)].filter(month => /^\d{4}-\d{2}$/.test(month)))].sort().reverse())
// An indexed device alone is not evidence that a work used it.
const usages = (work: Work): Usage[] => (work.hardware_usage || []).filter(usage => deviceMap.value.has(usage.hardware_id) && knownCategory(usage.category) && usage.category === deviceMap.value.get(usage.hardware_id)?.category && publicUrl(usage.source_url) && Boolean(usage.statement?.trim()))
const usableWorks = computed(() => rows.value.filter(work => usages(work).length))
const incompleteLinks = computed(() => rows.value.reduce((sum, work) => sum + (work.hardware_usage || []).filter(usage => knownCategory(usage.category)).length - usages(work).length, 0))
const matchUsage = (usage: Usage) => (!filters.value.category || usage.category === filters.value.category) && (!filters.value.device || usage.hardware_id === filters.value.device) && (!filters.value.setting || (settingLabels[usage.setting] ? usage.setting : 'unknown') === filters.value.setting) && (!filters.value.role || usage.role === filters.value.role)
const filtered = computed(() => usableWorks.value.filter(work => (!filters.value.month || monthOf(work) === filters.value.month) && usages(work).some(matchUsage)).slice().sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || '') || a.title.localeCompare(b.title, 'zh-CN')))
const visible = computed(() => filtered.value.slice(0, shown.value))
const currentLinks = computed(() => filtered.value.flatMap(work => usages(work).filter(matchUsage)))
const currentDeviceIds = computed(() => new Set(currentLinks.value.map(usage => usage.hardware_id)))
const currentDevices = computed(() => devices.value.filter(device => currentDeviceIds.value.has(device.hardware_id)))
const selectableDevices = computed(() => devices.value.filter(device => device.work_ids?.length && (!filters.value.category || device.category === filters.value.category)))
const categorySummary = computed(() => Object.entries(categoryLabels.value).map(([code, label]) => ({ code, label, devices: new Set(currentLinks.value.filter(usage => usage.category === code).map(usage => usage.hardware_id)).size, works: filtered.value.filter(work => usages(work).some(usage => usage.category === code && matchUsage(usage))).length })))
const totalDevices = computed(() => new Set(usableWorks.value.flatMap(work => usages(work).map(usage => usage.hardware_id))).size)
const relationCount = (hardwareId: string) => filtered.value.filter(work => usages(work).some(usage => usage.hardware_id === hardwareId && matchUsage(usage))).length
const configurationText = (value: unknown) => value == null || value === '' ? '' : typeof value === 'string' ? value : JSON.stringify(value)
const readUrl = () => {
  const params = new URLSearchParams(window.location.search)
  const category = params.get('category') || ''
  const device = params.get('device') || ''
  const month = params.get('month') || ''
  filters.value = {
    category: knownCategory(category) ? category : '',
    device: devices.value.some(row => row.hardware_id === device && (!knownCategory(category) || row.category === category)) ? device : '',
    setting: Object.hasOwn(settingLabels, params.get('setting') || '') ? params.get('setting')! : '',
    role: Object.hasOwn(roleLabels, params.get('role') || '') ? params.get('role')! : '',
    month: month === 'unknown' || /^\d{4}-(0[1-9]|1[0-2])$/.test(month) ? month : '',
  }
  const amount = Number(params.get('shown') || 12)
  shown.value = Number.isFinite(amount) ? Math.max(12, Math.min(12000, Math.floor(amount / 12) * 12)) : 12
}
const writeUrl = (reset = true) => {
  if (reset) shown.value = 12
  const url = new URL(window.location.href)
  for (const [key, value] of Object.entries(filters.value)) value ? url.searchParams.set(key, value) : url.searchParams.delete(key)
  shown.value > 12 ? url.searchParams.set('shown', String(shown.value)) : url.searchParams.delete('shown')
  if (url.href !== window.location.href) window.history.pushState(window.history.state, '', url)
}
const changeCategory = () => { if (!selectableDevices.value.some(device => device.hardware_id === filters.value.device)) filters.value.device = ''; writeUrl() }
const chooseDevice = (id: string) => { filters.value.device = filters.value.device === id ? '' : id; writeUrl() }
const reset = () => { filters.value = initial(); writeUrl() }
const more = async () => {
  const firstNew = visible.value.length
  shown.value += 12
  writeUrl(false)
  await nextTick()
  list.value?.querySelectorAll<HTMLElement>('.hardware-work')[firstNew]?.focus({ preventScroll: true })
}
const load = async () => {
  const request = ++requestId
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = ''
  index.value = null
  rows.value = []
  try {
    const responses = await Promise.all(['/api/v1/equipment/index.json', '/api/v1/equipment/works.json'].map(path => fetch(withBase(path), { signal: controller!.signal, cache: 'no-cache' })))
    if (responses.some(response => !response.ok)) throw new Error('unavailable')
    const [catalog, works] = await Promise.all(responses.map(response => response.json()))
    if (disposed || request !== requestId) return
    if (catalog.schema_version !== '1' || works.schema_version !== '1' || !Array.isArray(catalog.devices) || !Array.isArray(catalog.categories) || !Array.isArray(works.rows) || !catalog.counts) throw new Error('invalid')
    if (!catalog.dataset_version || catalog.dataset_version !== works.dataset_version || ((catalog.source_version != null || works.source_version != null) && catalog.source_version !== works.source_version)) throw new Error('version')
    if (works.rows.some((work: Work) => !work.work_id || !work.title || (work.hardware_usage != null && !Array.isArray(work.hardware_usage)))) throw new Error('invalid')
    index.value = catalog
    rows.value = Array.from(new Map<string, Work>(works.rows.map((work: Work) => [work.work_id, work])).values())
    readUrl()
  } catch (cause) {
    if (!disposed && request === requestId) error.value = cause instanceof Error && cause.message === 'version' ? '硬件索引与研究证据来自不同数据版本，已停止混合展示。请重新读取。' : '硬件与使用证据暂时无法读取，未将读取失败显示为零使用。请重试。'
  } finally { if (!disposed && request === requestId) loading.value = false }
}
const chart = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false, aria: { enabled: true, description: '当前筛选下按设备类别登记的研究使用关系。每类按研究去重，跨类可以重复，不是设备使用率或排名。' },
    tooltip: { trigger: 'axis', confine: true, backgroundColor: tokens.background, borderColor: tokens.divider, textStyle: { color: tokens.text } },
    grid: { left: 112, right: 32, top: 14, bottom: 32 },
    xAxis: { type: 'value', minInterval: 1, axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'category', inverse: true, data: categorySummary.value.map(row => row.label), axisLabel: { color: tokens.text }, axisTick: { show: false }, axisLine: { show: false } },
    series: [{ name: '有明确使用依据的研究', type: 'bar', barMaxWidth: 24, itemStyle: { color: tokens.palette[0] }, data: categorySummary.value.map(row => row.works) }],
  }
})
onMounted(() => {
  const pathname = window.location.pathname
  const previous = router.onBeforePageLoad
  const guard = (href: string) => { if (new URL(href, window.location.href).pathname === pathname) { if (index.value) readUrl(); return false }; return previous?.(href) }
  router.onBeforePageLoad = guard
  releaseRouteGuard = () => { if (router.onBeforePageLoad === guard) router.onBeforePageLoad = previous }
  window.addEventListener('popstate', readUrl)
  void load()
})
onBeforeUnmount(() => { disposed = true; requestId++; controller?.abort(); releaseRouteGuard(); window.removeEventListener('popstate', readUrl) })
</script>

<template>
  <div class="v3-dashboard hardware-radar">
    <header class="v3-page-heading"><div><p class="v3-eyebrow">HARDWARE IN RESEARCH</p><h1>硬件与研究</h1><p>哪些研究明确使用了哪些设备，以及它们承担什么工作。</p></div></header>
    <p v-if="loading" role="status">正在读取设备档案与逐项使用证据…</p>
    <div v-if="error" class="hardware-notice" role="alert"><p>{{ error }}</p><button type="button" @click="load">重新读取</button></div>
    <template v-if="index && !loading && !error">
      <div class="hardware-context"><span>数据截至 {{ eventDate(index.data_through) }}</span><span>版本 {{ index.dataset_version }}</span><a :href="withBase('/api/v1/equipment/index.json')">公开硬件索引</a><a :href="withBase('/api/v1/equipment/works.json')">使用关系与原文证据</a></div>
      <aside class="hardware-boundary"><p>仅统计有原文依据的设备—研究使用关系。未登记不代表未使用；没有明确型号时保留原有身份粒度，不从视频外观猜测。未明型号条目不是一个独立已知产品。范围限机器人、机械臂、灵巧手、平行夹爪、算力和采集/感知设备；夹爪不并为灵巧手，不展开电机、模组与电路。</p><p v-if="provisionalMonth"><span class="hardware-provisional">{{ provisionalMonth }} 暂行</span> 与完整月份分开标记，不能将未结束月份直接比较为增长或下降。</p></aside>
      <dl class="hardware-counts"><div><dt>有使用依据的硬件条目（含未明型号）</dt><dd>{{ totalDevices }}</dd></div><div><dt>有明确使用依据的研究</dt><dd>{{ usableWorks.length }}</dd></div><div><dt>另存的硬件候选</dt><dd>{{ index.counts.hardware_candidates ?? '未提供' }}</dd></div></dl>
      <p v-if="incompleteLinks" class="hardware-notice" role="status">另有 {{ incompleteLinks }} 条已登记关系缺少匹配的设备身份、类别或可读原文声明，未计入下方已核验使用集合。</p>
      <div class="hardware-filters" aria-label="硬件研究筛选">
        <label>设备类别<select v-model="filters.category" @change="changeCategory"><option value="">全部类别</option><option v-for="(label, code) in categoryLabels" :key="code" :value="code">{{ label }}</option></select></label>
        <label>具体设备<select v-model="filters.device" @change="writeUrl()"><option value="">全部设备</option><option v-for="device in selectableDevices" :key="device.hardware_id" :value="device.hardware_id">{{ device.name }}</option></select></label>
        <label>使用环境<select v-model="filters.setting" @change="writeUrl()"><option value="">全部环境</option><option v-for="(label, code) in settingLabels" :key="code" :value="code">{{ label }}</option></select></label>
        <label>设备用途<select v-model="filters.role" @change="writeUrl()"><option value="">全部用途</option><option v-for="(label, code) in roleLabels" :key="code" :value="code">{{ label }}</option></select></label>
        <label>研究首次公开月份<select v-model="filters.month" @change="writeUrl()"><option value="">全部已登记月份</option><option v-for="month in months" :key="month" :value="month">{{ month }}{{ month === provisionalMonth ? ' · 暂行' : '' }}</option><option value="unknown">日期待核验</option></select></label>
        <button type="button" @click="reset">清除筛选</button>
      </div>
      <p class="hardware-result-count" aria-live="polite">当前筛选：{{ currentDeviceIds.size }} 条硬件记录关联 {{ filtered.length }} 项研究。按研究首次公开日期浏览，不排名。</p>
      <ChartFrame title="设备类别与已核验研究" description="随筛选更新；每类按研究去重，同一研究可使用多类设备，类别之间不可相加为研究总量。" :height="290" compact>
        <div :ref="chart.element" role="img" aria-label="各设备类别具有原文使用依据的研究数量" />
        <template #table><table><thead><tr><th>类别</th><th>硬件条目（含未明型号）</th><th>关联研究数</th></tr></thead><tbody><tr v-for="row in categorySummary" :key="row.code"><th>{{ row.label }}</th><td>{{ row.devices }}</td><td>{{ row.works }}</td></tr></tbody></table></template>
      </ChartFrame>
      <details v-if="currentDevices.length" class="hardware-device-list"><summary>当前设备档案 · {{ currentDevices.length }} 条</summary><div class="hardware-device-grid"><article v-for="device in currentDevices" :key="device.hardware_id"><h2>{{ device.name }}</h2><p>{{ device.vendor || '厂商未说明' }} · {{ categoryLabels[device.category] }}</p><p>身份粒度：{{ identityLabels[device.identity_level || 'unknown'] || device.identity_level }} · {{ relationCount(device.hardware_id) }} 项筛选内研究</p><a v-if="publicUrl(device.official_url)" :href="device.official_url" target="_blank" rel="noopener noreferrer">设备官方资料 ↗</a><button type="button" :aria-pressed="filters.device === device.hardware_id" @click="chooseDevice(device.hardware_id)">{{ filters.device === device.hardware_id ? '取消此设备筛选' : '查看关联研究' }}</button></article></div></details>
      <div ref="list" class="hardware-work-list">
        <article v-for="work in visible" :key="work.work_id" class="hardware-work" tabindex="-1" :class="{ 'is-provisional': monthOf(work) === provisionalMonth }">
          <p v-if="monthOf(work) === provisionalMonth" class="hardware-provisional">{{ provisionalMonth }} 暂行样本</p>
          <ResearchCard :work="work" compact />
          <section class="hardware-evidence" :aria-label="`${work.title}的硬件使用证据`"><h2>设备如何用于这项研究</h2><article v-for="(usage, i) in usages(work).filter(matchUsage)" :key="`${usage.hardware_id}-${i}`"><div class="hardware-evidence-meta"><strong>{{ deviceMap.get(usage.hardware_id)?.name || usage.name }}</strong><span>{{ roleLabels[usage.role] || '用途未归类' }}</span><span>{{ settingLabels[usage.setting] || settingLabels.unknown }}</span></div><p>{{ usage.statement }}</p><p v-if="configurationText(usage.configuration)" class="hardware-configuration">配置：{{ configurationText(usage.configuration) }}</p><footer><a :href="usage.source_url" target="_blank" rel="noopener noreferrer">核对使用原文 ↗</a><span>原文位置：{{ usage.source_locator || '未提供定位' }}</span><span>核验于 {{ eventDate(usage.observed_at) }}</span></footer></article></section>
        </article>
      </div>
      <p v-if="!filtered.length" class="hardware-empty">当前筛选没有已登记且证据完整的使用关系，不表示这些设备没有用于研究。可放宽筛选查看其他已核验样本。</p>
      <div v-if="filtered.length" class="hardware-more"><p aria-live="polite">已展示 {{ visible.length }} / {{ filtered.length }} 项</p><button v-if="visible.length < filtered.length" type="button" @click="more">再加载 12 项研究</button><p v-else>已展示当前筛选的全部登记样本。</p></div>
    </template>
  </div>
</template>

<style scoped>
.hardware-radar { min-width: 0; }
.hardware-radar :is(p, h1, h2, h3, dd, a, span) { overflow-wrap: anywhere; }
.hardware-radar :is(button, select) { min-height: 44px; padding: 8px 12px; color: var(--vp-c-text-1); background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 7px; }
.hardware-radar button { cursor: pointer; }
.hardware-radar :is(button, select, a, [tabindex]):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.hardware-context { display: flex; flex-wrap: wrap; gap: 8px 18px; color: var(--vp-c-text-2); font-size: 13px; }
.hardware-boundary, .hardware-notice { margin: 20px 0; padding: 12px 18px; border-left: 3px solid var(--vp-c-brand-1); background: var(--vp-c-bg-soft); font-size: 14px; line-height: 1.8; }
.hardware-boundary p, .hardware-notice p { margin: 4px 0; }
.hardware-provisional { display: inline-block; padding: 3px 9px; border: 1px dashed var(--vp-c-warning-1); border-radius: 5px; color: var(--vp-c-text-1); background: var(--vp-c-warning-soft); font-size: 12px; }
.hardware-counts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; padding: 18px 0; border-block: 1px solid var(--vp-c-divider); }
.hardware-counts dt { font-size: 13px; color: var(--vp-c-text-2); }
.hardware-counts dd { margin: 6px 0 0; font-size: 28px; }
.hardware-filters { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: end; gap: 14px; margin: 24px 0 14px; }
.hardware-filters label { display: grid; gap: 7px; font-size: 13px; min-width: 0; }
.hardware-filters select { width: 100%; min-width: 0; }
.hardware-result-count, .hardware-more, .hardware-empty { color: var(--vp-c-text-2); font-size: 14px; line-height: 1.8; }
.hardware-device-list { margin: 22px 0; }
.hardware-device-list summary { cursor: pointer; min-height: 44px; padding: 10px 0; }
.hardware-device-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.hardware-device-grid article { min-width: 0; border: 1px solid var(--vp-c-divider); border-radius: 10px; padding: 15px; }
.hardware-device-grid h2 { margin: 0 0 8px; border: 0; font-size: 16px; }
.hardware-device-grid p { color: var(--vp-c-text-2); font-size: 12px; }
.hardware-device-grid a { display: block; font-size: 13px; margin: 10px 0; }
.hardware-device-grid button { font-size: 13px; }
.hardware-device-grid button[aria-pressed="true"] { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); }
.hardware-work-list { display: grid; gap: 28px; margin-top: 28px; }
.hardware-work { min-width: 0; border-radius: 14px; }
.hardware-work.is-provisional { border-left: 3px dashed var(--vp-c-warning-1); padding-left: 14px; }
.hardware-work > .hardware-provisional { margin: 0 0 10px; }
.hardware-evidence { padding: 16px 20px; border: 1px solid var(--vp-c-divider); border-top: 0; border-radius: 0 0 12px 12px; background: var(--vp-c-bg-soft); }
.hardware-evidence h2 { font-size: 14px; margin: 0 0 12px; border: 0; }
.hardware-evidence > article + article { border-top: 1px solid var(--vp-c-divider); margin-top: 15px; padding-top: 15px; }
.hardware-evidence-meta { display: flex; flex-wrap: wrap; gap: 8px 14px; font-size: 13px; align-items: baseline; }
.hardware-evidence-meta span { color: var(--vp-c-text-2); }
.hardware-evidence p { font-size: 14px; line-height: 1.75; margin: 10px 0; }
.hardware-evidence .hardware-configuration { color: var(--vp-c-text-2); font-size: 12px; white-space: pre-wrap; }
.hardware-evidence footer { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 12px; color: var(--vp-c-text-2); }
.hardware-more { text-align: center; padding: 20px 0; }
.hardware-empty { padding: 24px 0; }
@media (max-width: 850px) { .hardware-filters, .hardware-device-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 550px) { .hardware-filters, .hardware-device-grid { grid-template-columns: 1fr; } .hardware-counts { grid-template-columns: 1fr; gap: 12px; } .hardware-counts > div { display: flex; justify-content: space-between; align-items: center; gap: 15px; } .hardware-counts dd { margin: 0; font-size: 23px; } .hardware-filters select { font-size: 16px; } .hardware-evidence { padding: 16px; } }
</style>
