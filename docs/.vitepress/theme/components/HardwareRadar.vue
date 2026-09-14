<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, withBase } from 'vitepress'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { AriaComponent, GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ChartFrame from './ChartFrame.vue'
import ResearchCard from './ResearchCard.vue'
import HardwareFrequencyRow from './HardwareFrequencyRow.vue'
import { chartTokens, useEChart } from '../composables/useEChart'
import { eventDate } from '../lib/dates'
import { hardwareFrequency, hardwareMonth } from '../lib/hardware-frequency.mjs'
import HardwareCoverage from './HardwareCoverage.vue'

echarts.use([BarChart, AriaComponent, GridComponent, TooltipComponent, CanvasRenderer])
type Work = { work_id: string; title: string; first_public_date?: string; first_public_date_precision?: string; hardware_usage?: any[]; [key: string]: any }
type Device = { hardware_id: string; slug: string; name: string; aliases?: string[]; vendor?: string; category: string; identity_level?: string; official_url?: string; work_ids?: string[] }
type FrequencyDevice = Device & { work_count: number; real_work_count: number; simulation_work_count: number; baseline_work_count: number; calibration_work_count: number; source_count: number; sources: { work_id: string; title: string; first_public_date?: string; first_public_date_precision?: string; original_url?: string; usages: any[] }[] }
type EquipmentIndex = { schema_version: string; dataset_version: string; source_version?: string; data_through?: string; window?: { complete_months?: string[]; provisional_month?: string }; counts: { devices: number; usage_links: number; works: number; hardware_candidates: number }; categories: { code: string; label: string; devices: number; works: number }[]; devices: Device[] }
type Filters = { category: string; device: string; setting: string; role: string; month: string }
const allowedCategories = new Set(['robot_platform', 'robot_arm', 'dexterous_hand', 'gripper', 'compute_platform', 'data_collection', 'tactile_sensor', 'force_sensor', 'vision_sensor'])
const settingLabels: Record<string, string> = { real: '真机 / 真实设备', simulation: '仿真环境', dataset: '数据集', unknown: '环境未说明' }
const roleLabels: Record<string, string> = { real_robot: '真机使用', simulated_robot: '仿真机器人', training_compute: '训练算力', inference_compute: '推理算力', control_compute: '控制计算', model_fitting_compute: '模型参数拟合', experiment_compute: '实验计算（环节未细分）', data_collection: '数据采集', sensing: '感知', dataset_source: '数据来源' }
const initial = (): Filters => ({ category: '', device: '', setting: '', role: '', month: '' })
const index = ref<EquipmentIndex | null>(null)
const rows = ref<Work[]>([])
const filters = ref<Filters>(initial())
const modelQuery = ref('')
const shown = ref(12)
const unresolvedShown = ref(12)
const researchShown = ref(12)
const showResearch = ref(false)
const openSources = ref(new Set<string>())
const loading = ref(true)
const error = ref('')
const modelList = ref<HTMLElement | null>(null)
const unresolvedList = ref<HTMLElement | null>(null)
const researchList = ref<HTMLElement | null>(null)
const researchHeading = ref<HTMLElement | null>(null)
const router = useRouter()
let controller: AbortController | undefined
let requestId = 0
let disposed = false
let releaseRouteGuard = () => {}
const categoryLabels = computed<Record<string, string>>(() => Object.fromEntries((index.value?.categories || []).filter(category => allowedCategories.has(category.code)).map(category => [category.code, category.label])))
const knownCategory = (value: string) => Object.hasOwn(categoryLabels.value, value)
const devices = computed(() => (index.value?.devices || []).filter(device => knownCategory(device.category)))
const deviceMap = computed(() => new Map(devices.value.map(device => [device.hardware_id, device])))
const workMap = computed(() => new Map(rows.value.map(work => [work.work_id, work])))
const monthOf = (work: Work) => hardwareMonth(work)
const provisionalMonth = computed(() => index.value?.window?.provisional_month || '')
const months = computed(() => [...new Set([...(index.value?.window?.complete_months || []), provisionalMonth.value, ...rows.value.filter(work => work.hardware_usage?.length).map(monthOf)].filter(month => /^\d{4}-\d{2}$/.test(month)))].sort().reverse())
const frequency = computed(() => hardwareFrequency(devices.value, rows.value, filters.value) as { models: FrequencyDevice[]; unresolved: FrequencyDevice[] })
// Model-name search is a presentation filter, not an extra authority/helper filter.
const searchKey = (value: string) => value.normalize('NFKC').toLocaleLowerCase().replace(/[\s_:\-/]+/g, '')
const matchesModel = (device: Device) => {
  const tokens = modelQuery.value.trim().split(/\s+/).map(searchKey).filter(Boolean)
  const labels = [device.name, device.vendor || '', device.slug, device.hardware_id, ...(device.aliases || [])].map(searchKey)
  return tokens.every(token => labels.some(label => label.includes(token)))
}
const models = computed(() => frequency.value.models.filter(matchesModel))
const unresolved = computed(() => frequency.value.unresolved.filter(matchesModel))
const topModels = computed(() => models.value.slice(0, 12))
const visibleModels = computed(() => models.value.slice(0, shown.value))
const visibleUnresolved = computed(() => unresolved.value.slice(0, unresolvedShown.value))
const matchedWorkCount = computed(() => new Set([...models.value, ...unresolved.value].flatMap(device => device.sources.map(source => source.work_id))).size)
const selectedDevice = computed(() => deviceMap.value.get(filters.value.device))
const selectedFrequency = computed(() => [...frequency.value.models, ...frequency.value.unresolved].find(device => device.hardware_id === filters.value.device))
const selectedWorks = computed(() => (selectedFrequency.value?.sources || []).map(source => workMap.value.get(source.work_id)).filter((work): work is Work => Boolean(work)))
const visibleWorks = computed(() => selectedWorks.value.slice(0, researchShown.value))
const selectableDevices = computed(() => devices.value.filter(device => !filters.value.category || device.category === filters.value.category).slice().sort((a, b) => a.name.localeCompare(b.name, 'zh-CN')))
const chartHeight = computed(() => Math.max(170, topModels.value.length * 30 + 48))
const rowId = (device: Device) => 'hardware-model-' + device.slug
const countFromUrl = (value: string | null) => {
  const amount = Number(value || 12)
  return Number.isFinite(amount) ? Math.max(12, Math.min(12000, Math.floor(amount / 12) * 12)) : 12
}
const revealSearchMatches = () => {
  if (!modelQuery.value.trim()) return
  const next = new Set(openSources.value)
  for (const device of unresolved.value) next.add(device.hardware_id)
  openSources.value = next
}
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
  modelQuery.value = (params.get('model_q') || '').slice(0, 200)
  shown.value = countFromUrl(params.get('shown'))
  unresolvedShown.value = countFromUrl(params.get('unresolved_shown'))
  researchShown.value = countFromUrl(params.get('research_shown'))
  showResearch.value = params.get('view') === 'research' && Boolean(filters.value.device)
  openSources.value = new Set(filters.value.device ? [filters.value.device] : [])
  revealSearchMatches()
}
const writeUrl = (reset = true, replace = false) => {
  if (reset) { shown.value = 12; unresolvedShown.value = 12; researchShown.value = 12 }
  const url = new URL(window.location.href)
  for (const [key, value] of Object.entries(filters.value)) value ? url.searchParams.set(key, value) : url.searchParams.delete(key)
  for (const [key, count] of [['shown', shown.value], ['unresolved_shown', unresolvedShown.value], ['research_shown', researchShown.value]] as const) count > 12 ? url.searchParams.set(key, String(count)) : url.searchParams.delete(key)
  modelQuery.value.trim() ? url.searchParams.set('model_q', modelQuery.value.trim()) : url.searchParams.delete('model_q')
  showResearch.value && filters.value.device ? url.searchParams.set('view', 'research') : url.searchParams.delete('view')
  if (url.href !== window.location.href) window.history[replace ? 'replaceState' : 'pushState'](window.history.state, '', url)
}
const changeFilter = () => { showResearch.value = false; writeUrl(); revealSearchMatches() }
const searchModels = () => { showResearch.value = false; writeUrl(true, true); revealSearchMatches() }
const changeCategory = () => { if (!selectableDevices.value.some(device => device.hardware_id === filters.value.device)) filters.value.device = ''; changeFilter() }
const chooseDevice = async (id: string, papers = false) => {
  filters.value.device = id
  modelQuery.value = ''
  showResearch.value = papers
  openSources.value = new Set([id])
  writeUrl()
  await nextTick()
  if (disposed) return
  if (papers) researchHeading.value?.focus()
  else {
    const device = deviceMap.value.get(id)
    if (device) document.getElementById(rowId(device))?.focus()
  }
}
const selectDevice = () => { openSources.value = new Set(filters.value.device ? [filters.value.device] : []); changeFilter() }
const clearDevice = () => { filters.value.device = ''; showResearch.value = false; openSources.value = new Set(); writeUrl() }
const reset = () => { filters.value = initial(); modelQuery.value = ''; showResearch.value = false; openSources.value = new Set(); writeUrl() }
const setSourceOpen = (id: string, open: boolean) => {
  if (openSources.value.has(id) === open) return
  const next = new Set(openSources.value)
  open ? next.add(id) : next.delete(id)
  openSources.value = next
}
const moreModels = async (isUnresolved = false) => {
  const firstNew = isUnresolved ? visibleUnresolved.value.length : visibleModels.value.length
  if (isUnresolved) unresolvedShown.value += 12
  else shown.value += 12
  writeUrl(false)
  await nextTick()
  ;(isUnresolved ? unresolvedList.value : modelList.value)?.querySelectorAll<HTMLElement>('.hardware-model')[firstNew]?.focus({ preventScroll: true })
}
const moreResearch = async () => {
  const firstNew = visibleWorks.value.length
  researchShown.value += 12
  writeUrl(false)
  await nextTick()
  researchList.value?.querySelectorAll<HTMLElement>('.hardware-work')[firstNew]?.focus({ preventScroll: true })
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
    if (!disposed && request === requestId) error.value = cause instanceof Error && cause.message === 'version' ? '设备索引与论文出处来自不同数据版本，已停止混合展示。请重新读取。' : '设备与使用证据暂时无法读取，未将读取失败显示为零使用。请重试。'
  } finally { if (!disposed && request === requestId) loading.value = false }
}
const chart = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false, aria: { enabled: true, description: '按去重研究数降序排列的前十二个具体型号。一次表示一项有明确使用证据的研究，不是采购量、设备销量或产品质量排名。' },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText', backgroundColor: tokens.background, borderColor: tokens.divider, textStyle: { color: tokens.text } },
    grid: { left: 170, right: 35, top: 10, bottom: 32 },
    xAxis: { type: 'value', minInterval: 1, axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'category', inverse: true, data: topModels.value.map(device => device.name), axisLabel: { color: tokens.text, width: 150, overflow: 'truncate', fontSize: 12 }, axisTick: { show: false }, axisLine: { show: false } },
    series: [{ name: '有使用证据的去重研究', type: 'bar', barMaxWidth: 20, itemStyle: { color: tokens.palette[0] }, label: { show: true, position: 'right', color: tokens.text }, data: topModels.value.map(device => ({ value: device.work_count, hardware_id: device.hardware_id })) }],
  }
}, chart => chart.on('click', (item: any) => { if (item.data?.hardware_id) void chooseDevice(item.data.hardware_id) }))
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
    <header class="v3-page-heading"><div><p class="v3-eyebrow">HARDWARE MODEL FREQUENCY</p><h1>研究设备 · 型号频次</h1><p>先看具体型号被多少项研究使用，再展开完整论文出处。</p></div></header>
    <HardwareCoverage compact :expected-version="index?.dataset_version" />
    <p v-if="loading" role="status">正在读取型号频次与论文出处…</p>
    <div v-if="error" class="hardware-notice" role="alert"><p>{{ error }}</p><button type="button" @click="load">重新读取</button></div>
    <template v-if="index && !loading && !error">
      <div class="hardware-context"><span>截至 {{ eventDate(index.data_through) }}</span><a :href="withBase('/methods/equipment-loco')">范围与统计口径 ↗</a><span v-if="provisionalMonth" class="hardware-provisional">{{ provisionalMonth }} 暂行</span></div>
      <p class="hardware-scope">一次 = 一项去重研究；真机与仿真可重叠。只计明确使用，未登记不代表未使用，不作销量或质量排名。</p>
      <div class="hardware-primary-filters">
        <label class="hardware-model-search">搜索型号或别名<input v-model="modelQuery" type="search" maxlength="200" placeholder="例如 Unitree G1、PiPER-X、WUJI" @input="searchModels" /></label>
        <label>设备类别<select v-model="filters.category" @change="changeCategory"><option value="">全部类别</option><option v-for="(label, code) in categoryLabels" :key="code" :value="code">{{ label }}</option></select></label>
        <label>使用环境<select v-model="filters.setting" @change="changeFilter"><option value="">全部环境</option><option v-for="(label, code) in settingLabels" :key="code" :value="code">{{ label }}</option></select></label>
      </div>
      <div class="hardware-filter-tools"><details class="hardware-advanced" :open="Boolean(filters.role || filters.month)"><summary>型号、用途与月份筛选</summary><div class="hardware-extra-filters"><label>指定设备<select v-model="filters.device" @change="selectDevice"><option value="">全部设备</option><option v-for="device in selectableDevices" :key="device.hardware_id" :value="device.hardware_id">{{ device.name }}</option></select></label><label>设备用途<select v-model="filters.role" @change="changeFilter"><option value="">全部用途</option><option v-for="(label, code) in roleLabels" :key="code" :value="code">{{ label }}</option></select></label><label>研究首次公开月份<select v-model="filters.month" @change="changeFilter"><option value="">全部已登记月份</option><option v-for="month in months" :key="month" :value="month">{{ month }}{{ month === provisionalMonth ? ' · 暂行' : '' }}</option><option value="unknown">日期待核验</option></select></label></div></details><button class="hardware-clear" type="button" @click="reset">清除筛选</button></div>
      <p v-if="selectedDevice" class="hardware-selection">{{ selectedDevice.name }} <button type="button" @click="clearDevice">查看全部型号 ×</button></p>
      <p class="hardware-result-count" aria-live="polite">{{ models.length }} 个具体型号 · {{ unresolved.length }} 条系列 / 未明型号 · {{ matchedWorkCount }} 项关联研究</p>
      <ChartFrame v-if="topModels.length && !filters.device" title="具体型号使用频次 · 前 12 项" description="按有明确使用证据的去重研究数排序。点击横条查看该型号的完整出处；同次数按名称稳定排列。" :height="chartHeight" compact>
        <div :ref="chart.element" role="img" aria-label="前十二个具体硬件型号的去重研究使用频次" />
        <template #table><table><thead><tr><th>具体型号</th><th>使用研究数</th><th>真机 / 真实设备</th><th>仿真</th></tr></thead><tbody><tr v-for="device in models" :key="device.hardware_id"><th><button type="button" @click="chooseDevice(device.hardware_id)">{{ device.name }}</button></th><td>{{ device.work_count }}</td><td>{{ device.category === 'compute_platform' ? '算力用途见出处' : device.real_work_count }}</td><td>{{ device.category === 'compute_platform' ? '算力用途见出处' : device.simulation_work_count }}</td></tr></tbody></table></template>
      </ChartFrame>

      <section v-if="models.length" class="hardware-model-section" aria-labelledby="hardware-models-heading"><header><h2 id="hardware-models-heading">具体型号完整列表</h2><p>使用频次由高到低；每项可展开全部论文和原文定位。</p></header><div ref="modelList" class="hardware-frequency-list"><HardwareFrequencyRow v-for="device in visibleModels" :id="rowId(device)" :key="device.hardware_id" :device="device" :category-label="categoryLabels[device.category]" :expanded="openSources.has(device.hardware_id)" :provisional-month="provisionalMonth" @papers="chooseDevice($event, true)" @sources="setSourceOpen(device.hardware_id, $event)" /></div><div class="hardware-more"><p aria-live="polite">已显示 {{ visibleModels.length }} / {{ models.length }} 个具体型号</p><button v-if="visibleModels.length < models.length" type="button" @click="moreModels()">再加载 12 个型号</button></div></section>

      <section v-if="unresolved.length" class="hardware-model-section hardware-unresolved-section" aria-labelledby="hardware-unresolved-heading"><header><h2 id="hardware-unresolved-heading">系列与未明型号</h2><p>这些记录有使用出处，但具体版本尚未确认；单列频次，不并入具体型号榜。WUJI等系列名不推定为当前产品代际。</p></header><div ref="unresolvedList" class="hardware-frequency-list"><HardwareFrequencyRow v-for="device in visibleUnresolved" :id="rowId(device)" :key="device.hardware_id" :device="device" :category-label="categoryLabels[device.category]" :expanded="openSources.has(device.hardware_id)" :provisional-month="provisionalMonth" @papers="chooseDevice($event, true)" @sources="setSourceOpen(device.hardware_id, $event)" /></div><div class="hardware-more"><p aria-live="polite">已显示 {{ visibleUnresolved.length }} / {{ unresolved.length }} 条系列与未明型号</p><button v-if="visibleUnresolved.length < unresolved.length" type="button" @click="moreModels(true)">再加载 12 条记录</button></div></section>

      <p v-if="!models.length && !unresolved.length" class="hardware-empty">当前筛选没有匹配的已核验使用记录，不表示设备未用于研究。可尝试别名，或清除其他筛选。</p>
      <section v-if="showResearch && selectedFrequency" class="hardware-research-section" aria-labelledby="hardware-research-heading"><h2 id="hardware-research-heading" ref="researchHeading" tabindex="-1">{{ selectedFrequency.name }} · 原研究卡片</h2><p class="hardware-scope">这里只展开当前型号关联的研究；该型号的完整使用出处仍保留在上方列表。</p><div ref="researchList" class="hardware-work-list"><article v-for="work in visibleWorks" :key="work.work_id" class="hardware-work" tabindex="-1"><ResearchCard :work="work" compact /></article></div><div class="hardware-more"><p aria-live="polite">已显示 {{ visibleWorks.length }} / {{ selectedWorks.length }} 项研究</p><button v-if="visibleWorks.length < selectedWorks.length" type="button" @click="moreResearch">再加载 12 项研究</button></div></section>
      <details class="hardware-data-details"><summary>公开数据与核验版本</summary><p><a :href="withBase('/api/v1/equipment/index.json')">设备索引</a> · <a :href="withBase('/api/v1/equipment/works.json')">完整研究与使用证据</a> · <a :href="withBase('/methods/equipment-loco')">方法与样本局限</a></p><p>版本 {{ index.dataset_version }}</p><p>另有 {{ index.counts.hardware_candidates ?? '未提供数量的' }} 条提及候选，未作为实际使用计入。完整月份与暂行月份不混作增长判断。</p></details>
    </template>
  </div>
</template>

<style scoped>
.hardware-radar { min-width: 0; }
.hardware-radar :is(p, h1, h2, h3, dd, a, span, summary) { overflow-wrap: anywhere; }
.hardware-radar :is(button, select, input) { color: var(--vp-c-text-1); }
.hardware-radar :is(select, input) { min-height: 44px; padding: 8px 11px; border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); width: 100%; min-width: 0; }
.hardware-radar button, .hardware-radar summary { cursor: pointer; }
.hardware-radar :is(button, select, input, a, summary, [tabindex]):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.hardware-context { display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; color: var(--vp-c-text-2); font-size: 13px; }
.hardware-scope, .hardware-result-count { color: var(--vp-c-text-2); font-size: 13px; line-height: 1.8; margin: 10px 0 16px; }
.hardware-provisional { display: inline-block; padding: 2px 7px; border: 1px dashed var(--vp-c-warning-1); border-radius: 4px; font-size: 12px; }
.hardware-notice { margin: 18px 0; padding: 14px 18px; border-left: 3px solid var(--vp-c-brand-1); background: var(--vp-c-bg-soft); font-size: 14px; line-height: 1.8; }
.hardware-notice button, .hardware-more button { min-height: 44px; padding: 8px 15px; border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); }
.hardware-primary-filters { display: grid; grid-template-columns: minmax(0, 1.6fr) repeat(2, minmax(0, 1fr)); gap: 14px; align-items: end; }
.hardware-primary-filters label, .hardware-extra-filters label { display: grid; gap: 7px; font-size: 12px; min-width: 0; }
.hardware-filter-tools { display: flex; flex-wrap: wrap; align-items: start; gap: 10px 20px; margin: 8px 0 0; font-size: 12px; }
.hardware-advanced { flex: 1; min-width: 0; }
.hardware-advanced summary { padding: 11px 0; min-height: 44px; }
.hardware-extra-filters { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 4px 0 14px; }
.hardware-clear { min-height: 44px; color: var(--vp-c-brand-1); }
.hardware-selection { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; font-size: 14px; margin: 4px 0; }
.hardware-selection button { color: var(--vp-c-brand-1); min-height: 44px; font-size: 12px; }
.hardware-model-section { margin-top: 24px; }
.hardware-model-section > header { margin-bottom: 14px; }
.hardware-model-section h2, .hardware-research-section > h2 { font-size: 23px; margin: 0 0 6px; border: 0; line-height: 1.5; }
.hardware-model-section > header p { margin: 0; font-size: 13px; color: var(--vp-c-text-2); line-height: 1.75; }
.hardware-frequency-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-items: start; }
.hardware-unresolved-section { border-top: 1px solid var(--vp-c-divider); padding-top: 26px; }
.hardware-more { text-align: center; margin: 14px 0 20px; font-size: 13px; color: var(--vp-c-text-2); }
.hardware-more p { margin: 10px 0; }
.hardware-empty { padding: 25px 0; font-size: 14px; line-height: 1.8; color: var(--vp-c-text-2); }
.hardware-research-section { margin-top: 30px; }
.hardware-research-section > h2 { scroll-margin-top: 100px; }
.hardware-work-list { display: grid; gap: 20px; margin-top: 18px; }
.hardware-work { min-width: 0; border-radius: 12px; }
.hardware-data-details { margin: 25px 0; padding-top: 12px; border-top: 1px solid var(--vp-c-divider); color: var(--vp-c-text-2); font-size: 12px; line-height: 1.8; }
.hardware-data-details summary { min-height: 44px; padding: 10px 0; }
@media (max-width: 800px) { .hardware-primary-filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } .hardware-model-search { grid-column: 1 / -1; } .hardware-frequency-list { grid-template-columns: 1fr; } }
@media (max-width: 550px) { .hardware-radar :is(input, select) { font-size: 16px; } .hardware-extra-filters { grid-template-columns: 1fr; } .hardware-filter-tools { gap: 5px 12px; } .hardware-model-section h2 { font-size: 21px; } }
</style>
