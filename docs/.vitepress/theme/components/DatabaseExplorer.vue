<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'
import ReportTextEvidence from './ReportTextEvidence.vue'
import ResearchStatusNotice from './ResearchStatusNotice.vue'
import ResearchCard from './ResearchCard.vue'
import { searchCardFromResult as researchCard } from '../lib/research-card.mjs'
import { defaultFilters, filterCatalog, loadResultPage, readSearchUrl, searchOptions, writeSearchUrl, type ResultHandle, type SearchLookup } from '../lib/catalog-search'

type SearchRow = { id: string; url: string; excerpt: string; meta: Record<string, string> }
const manifest = ref<any>(null)
const rows = ref<SearchRow[]>([])
const handles = shallowRef<ResultHandle[]>([])
const total = ref(0)
const page = ref(1)
const pageInput = ref(1)
const pageSize = 20
const loading = ref(true)
const error = ref('')
const engineReady = ref(false)
const engineFilters = ref<Record<string, Record<string, number>>>({})
const filters = reactive(defaultFilters())
const expandedFilters = ref(false)
const dialog = ref<HTMLDialogElement | null>(null)
const queryInput = ref<HTMLInputElement | null>(null)
const detail = ref<any>(null)
const detailLoading = ref(false)
const detailError = ref('')
const versionText = ref<any>(null)
const currentTextMetadata = computed(() => detail.value?.text_versions?.find((row: any) => row.snapshot_id === detail.value?.current_text?.snapshot_ids?.[0]))
const detailHeading = computed(() => (detail.value?.localization_status === 'current' && detail.value?.title_zh) || currentTextMetadata.value?.title || detail.value?.title_zh || detail.value?.title || '研究详情')
const detailResearchStatusContext = computed(() => `已登记的最新研究状态截至 ${eventDate(detail.value?.research_status?.as_of)}，与下方正文版本的时间范围分开。摘要与版本原文保留供追溯；请先核对状态通知，再使用其中的实验结论。这是工作级状态，不是研究组归属或独立复现判断。`)
const versionLoading = ref(false)
const versionError = ref('')
let versionSerial = 0
const textCache = new Map<string, Promise<any[]>>()
const currentWork = ref('')
const evidenceEvents = computed<any[]>(() => Array.isArray(detail.value?.evidence_events) ? detail.value.evidence_events.filter((event: any) => !event.research_status_notice_id) : [])
const reportTags: Record<string, string> = {
  deployment_feedback: '部署反馈学习', generalist_policy: '通才策略', dexterous_bimanual: '灵巧 / 双臂操作',
  real_robot: '真机', production: '生产部署', human_video: '人类视频', hierarchical_control: '分层控制',
  rl_post_training: '强化学习后训练', world_action_model: '世界动作模型', cross_embodiment: '跨本体',
  simulation_synthetic: '仿真 / 合成数据', long_horizon: '长时序', open_assets: '开放资产',
  teleoperation: '遥操作', tactile_force: '触觉 / 力觉', whole_body: '全身控制',
  internal_evaluation: '内部评测', simulation: '仿真', date_conflict: '日期存在冲突',
  code: '代码', model: '模型', dataset: '数据集', data: '数据', benchmark: 'Benchmark',
}
const stringItems = (value: unknown): string[] => (Array.isArray(value) ? value : [value]).filter((item): item is string => typeof item === 'string' && Boolean(item.trim()))
const reportIsCompanyClaim = (event: any) => event.claim_status === 'company_self_report' || event.metric_owner === 'company' || event.source_type === 'official_company_report'
const reportClaimLabel = (event: any) => event.source_type === 'official_peer_review' && ['accepted', 'published'].includes(event.event_type) ? '官方同行评审记录（不等于独立复现）' : reportIsCompanyClaim(event) ? '公司自报' : event.claim_status === 'author_self_report' ? '作者自报' : event.claim_status === 'independently_validated' ? '已记录独立验证声明' : '来源自述 · 声明类型待核验'
const validationLabel = (event: any) => event.independent_validation === true ? '独立验证：已有记录，请核对来源' : event.independent_validation === false ? '独立验证：尚未核验' : '独立验证：情况未披露'
const metricValue = (value: unknown) => value === null || value === undefined || typeof value === 'boolean' || (typeof value === 'number' && !Number.isFinite(value)) || /^(?:\s*|unknown|n\/?a|null|not disclosed)$/i.test(String(value)) ? '未披露' : String(value)
const evidenceSources = (event: any): { url: string; label: string }[] => {
  const candidates = [event.url, event.evidence_url, event.source_url, ...(Array.isArray(event.sources) ? event.sources : []), ...(Array.isArray(event.evidence_links) ? event.evidence_links : [])]
  const seen = new Set<string>()
  return candidates.flatMap((item) => {
    const url = typeof item === 'string' ? item : item?.url
    if (typeof url !== 'string' || !/^https?:\/\//i.test(url) || seen.has(url)) return []
    seen.add(url)
    return [{ url, label: typeof item === 'object' ? item.label || item.title || '查看证据原文' : '查看证据原文' }]
  })
}
const disclosedAssets = (value: unknown): { label: string; url: string }[] => (Array.isArray(value) ? value : []).flatMap((item) => {
  if (typeof item === 'string') return [{ label: reportTags[item] || item, url: /^https?:\/\//i.test(item) ? item : '' }]
  if (!item || typeof item !== 'object') return []
  const url = typeof item.url === 'string' && /^https?:\/\//i.test(item.url) ? item.url : ''
  return [{ label: item.label || item.title || reportTags[item.kind] || item.kind || '公开资产', url }]
})
const resultsSection = ref<HTMLElement | null>(null)
let opener: HTMLElement | null = null
let pagefind: any
let searchLanguage = 'zh'
let directBrowse = false
let lookupPromise: Promise<SearchLookup> | undefined
let lookupPositions: Map<string, number>
const resultShardCache = new Map<string, Promise<SearchRow[]>>()
const identityCache = new Map<string, Promise<Record<string, number[]>>>()
let searchSerial = 0
let detailSerial = 0
let restoring = false
let debounceTimer: number | undefined
let destroyed = false
const shardCache = new Map<string, Promise<any[]>>()
let aliasCache: Promise<Record<string, string>> | undefined
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const activeFilterCount = computed(() => Object.entries(filters).filter(([key, value]) => key !== 'q' && value && !(key === 'relevance' && value === 'included')).length)
const options = (name: string) => Object.keys(engineFilters.value[name] || {}).sort((a, b) => name === 'year' ? b.localeCompare(a) : a.localeCompare(b))
const optionLabel = (value: string) => ({ unknown: '待核验', included: '已纳入', candidate: '候选', manual_review: '待复核', excluded: '已排除', accepted: '已接收', published: '正式出版', preprint: '预印本', main: '主会', workshop: 'Workshop' }[value] || value)
const resultResearchStatusLabel = (value: string) => ({ withdrawn: '已撤回', retracted: '已撤稿', corrected: '已更正', expression_of_concern: '关注声明', active: '有状态通知' }[value] || '研究状态通知')
const facetFields = [
  { key: 'venue', source: 'venue', label: '会议 / 期刊' }, { key: 'year', source: 'year', label: '会议 / 出版年份' },
  { key: 'track', source: 'track', label: 'Track' }, { key: 'acceptance', source: 'acceptance', label: '接收状态' },
  { key: 'publicationStatus', source: 'publication_status', label: '发表状态' },
] as const

const syncUrl = () => {
  if (restoring || destroyed) return
  const target = writeSearchUrl(new URL(window.location.href), filters, page.value, currentWork.value)
  if (target.href !== window.location.href) window.history.pushState({ radarSearch: true }, '', target)
}

const getLookup = () => {
  if (!lookupPromise) lookupPromise = fetch(withBase('/api/v1/search/lookup.json')).then(async (response) => {
    if (!response.ok) throw new Error('Search catalogue unavailable')
    const value = await response.json() as SearchLookup
    lookupPositions = new Map(value.ids.map((id, index) => [id, index]))
    return value
  }).catch((cause) => { lookupPromise = undefined; throw cause })
  return lookupPromise
}
const resultFor = async (workId: string) => {
  const digest = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(workId))
  const shard = new Uint8Array(digest)[0].toString(16).padStart(2, '0')
  if (!resultShardCache.has(shard)) resultShardCache.set(shard, fetch(withBase(`/api/v1/search/results/${shard}.json`)).then(async (response) => { if (!response.ok) throw new Error('Search results unavailable'); return response.json() }).catch((cause) => { resultShardCache.delete(shard); throw cause }))
  const result = (await resultShardCache.get(shard))?.find((row) => row.meta.work_id === workId)
  if (!result) throw new Error('Search result missing from catalogue')
  return { ...result, plain_excerpt: result.excerpt }
}
const loadIdentities = async (lookup: SearchLookup, selected: Record<string, string | { any: string[] }>) => {
  for (const field of lookup.identity_shards || []) {
    const filter = selected[field]
    if (!filter) continue
    const values = typeof filter === 'string' ? [filter] : filter.any
    await Promise.all(values.map(async (value) => {
      const digest = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(value))
      const shard = new Uint8Array(digest)[0].toString(16).padStart(2, '0')
      const key = `${field}/${shard}`
      if (!identityCache.has(key)) identityCache.set(key, fetch(withBase(`/api/v1/search/identity/${key}.json`)).then(async (response) => { if (response.status === 404) return {}; if (!response.ok) throw new Error('Identifier index unavailable'); return response.json() }).catch((cause) => { identityCache.delete(key); throw cause }))
      lookup.postings[field] ||= {}
      Object.assign(lookup.postings[field], await identityCache.get(key))
    }))
  }
}
const getEngine = async () => {
  if (!pagefind) {
    try {
      pagefind = await import(/* @vite-ignore */ withBase('/pagefind/pagefind.js'))
      await pagefind.options({ bundlePath: withBase('/pagefind/'), language: searchLanguage })
      await pagefind.init()
    } catch (cause) { pagefind?.destroy?.(); pagefind = undefined; throw cause }
  }
  return pagefind
}

const displayPage = async (target: number, serial: number) => {
  if (directBrowse) {
    const status = filters.relevance || 'all'
    const count = status === 'all' ? Object.values(engineFilters.value.relevance || {}).reduce((sum, value) => sum + value, 0) : engineFilters.value.relevance?.[status] || 0
    const actual = Math.max(1, Math.min(target, Math.max(1, Math.ceil(count / pageSize))))
    const response = await fetch(withBase(`/api/v1/search/browse/${encodeURIComponent(status)}/${actual}.json`))
    if (!response.ok) throw new Error('Browse page unavailable')
    const result = await response.json()
    if (serial !== searchSerial || destroyed) return
    rows.value = result.rows
    total.value = result.total
    page.value = actual
    pageInput.value = actual
    return
  }
  const result = await loadResultPage(handles.value, target, pageSize)
  if (serial !== searchSerial || destroyed) return
  rows.value = result.rows
  page.value = result.page
  pageInput.value = result.page
  total.value = result.total
}

const runSearch = async (targetPage = 1, updateUrl = true) => {
  if (!engineReady.value || !manifest.value) return
  if (debounceTimer) window.clearTimeout(debounceTimer)
  const serial = ++searchSerial
  loading.value = true
  error.value = ''
  rows.value = []
  try {
    const search = searchOptions(filters, manifest.value.available_months || [], options('publication'), searchLanguage)
    directBrowse = !search.empty && !search.query && (!filters.relevance || filters.relevance === 'all' || filters.relevance in (engineFilters.value.relevance || {})) && Object.keys(search.filters).every((name) => ['record_type', 'relevance'].includes(name))
    if (!directBrowse) {
      if (search.empty) handles.value = []
      else {
        const lookup = await getLookup()
        await loadIdentities(lookup, search.filters)
        const allowed = filterCatalog(lookup, search.filters)
        let positions: number[]
        if (search.query) {
          const engine = await getEngine()
          const response = await engine.search(search.query)
          positions = response.results.map((row: ResultHandle) => lookupPositions.get(row.id)).filter((position: number | undefined): position is number => position !== undefined && allowed.has(position))
        } else positions = [...allowed].sort((a, b) => lookup.dates[b].localeCompare(lookup.dates[a]) || lookup.work_ids[a].localeCompare(lookup.work_ids[b]))
        if (serial !== searchSerial || destroyed) return
        handles.value = positions.map((position) => ({ id: lookup.ids[position], data: () => resultFor(lookup.work_ids[position]) }))
      }
    }
    if (serial !== searchSerial || destroyed) return
    await displayPage(targetPage, serial)
    if (serial === searchSerial && updateUrl) syncUrl()
  } catch {
    if (serial !== searchSerial || destroyed) return
    handles.value = []
    total.value = 0
    error.value = '检索暂时不可用，请重试。若持续失败，可下载完整数据库；筛选条件已保留。'
  } finally { if (serial === searchSerial && !destroyed) loading.value = false }
}

const goToPage = async (target: number) => {
  if (loading.value || target < 1 || target > pageCount.value) return
  const serial = ++searchSerial
  loading.value = true
  error.value = ''
  try {
    await displayPage(target, serial)
    syncUrl()
    await nextTick()
    resultsSection.value?.focus({ preventScroll: true })
    resultsSection.value?.scrollIntoView({ block: 'start', behavior: 'instant' })
  } catch { error.value = '这一页载入失败，请重试；其他结果仍可浏览。' }
  finally { if (serial === searchSerial) loading.value = false }
}

const scheduleSearch = () => {
  if (restoring || !engineReady.value) return
  // Invalidate an earlier request immediately, before the debounce starts.
  searchSerial += 1
  if (debounceTimer) window.clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(() => runSearch(), 250)
}

const openWork = async (workId: string, updateUrl = true) => {
  const serial = ++detailSerial
  if (!dialog.value?.open) opener = document.activeElement as HTMLElement | null
  currentWork.value = workId
  detailLoading.value = true
  detailError.value = ''
  detail.value = null
  versionSerial += 1
  versionText.value = null
  versionError.value = ''
  versionLoading.value = false
  if (!dialog.value?.open) dialog.value?.showModal()
  if (updateUrl) syncUrl()
  try {
    if (!aliasCache) aliasCache = fetch(withBase('/api/v1/aliases.json')).then(async (response) => { if (!response.ok) throw new Error('Alias map unavailable'); return response.json() }).catch(() => { aliasCache = undefined; return {} })
    const aliases = await aliasCache
    const canonicalId = aliases[workId] || workId
    const digest = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(canonicalId))
    const shard = new Uint8Array(digest)[0].toString(16).padStart(2, '0')
    if (!shardCache.has(shard)) shardCache.set(shard, fetch(withBase(`/api/v1/works/${shard}.json`)).then(async (response) => { if (!response.ok) throw new Error('Unable to load work'); return response.json() }).catch((cause) => { shardCache.delete(shard); throw cause }))
    const values = await shardCache.get(shard)
    if (serial !== detailSerial || destroyed) return
    detail.value = values?.find((row: any) => row.work_id === canonicalId || row.aliases?.includes(workId))
    if (!detail.value) detailError.value = '这项研究尚未找到，可能已合并或链接有误。可通过标题或标识符搜索。'
    else if (['available', 'available_unversioned'].includes(detail.value.current_text?.status) && detail.value.current_text.snapshot_ids?.length) void openTextVersion(detail.value.current_text.snapshot_ids[0])
  } catch { if (serial === detailSerial) detailError.value = '详情暂时无法载入，请重试。' }
  finally { if (serial === detailSerial && !destroyed) detailLoading.value = false }
}

const openTextVersion = async (snapshotId: string) => {
  if (!detail.value?.text_versions?.some((row: any) => row.snapshot_id === snapshotId)) return
  const serial = ++versionSerial
  const workId = detail.value.work_id
  versionLoading.value = true
  versionError.value = ''
  versionText.value = null
  try {
    const digest = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(snapshotId))
    const shard = new Uint8Array(digest)[0].toString(16).padStart(2, '0')
    if (!textCache.has(shard)) textCache.set(shard, fetch(withBase(`/api/v1/text/${shard}.json`)).then(async response => {
      if (!response.ok) throw new Error('Missing text archive')
      return response.json()
    }).catch(error => { textCache.delete(shard); throw error }))
    const rows = await textCache.get(shard)
    if (serial !== versionSerial || destroyed || workId !== detail.value?.work_id) return
    versionText.value = rows?.find(row => row.snapshot_id === snapshotId && row.work_id === workId)
    if (!versionText.value) throw new Error('Text archive identity mismatch')
  } catch { if (serial === versionSerial) versionError.value = '版本原文暂时无法读取，请重试或打开官方版本来源。' }
  finally { if (serial === versionSerial) versionLoading.value = false }
}

const closeDetail = (updateUrl = true) => {
  const wasOpen = Boolean(dialog.value?.open)
  detailSerial += 1
  versionSerial += 1
  dialog.value?.close()
  detail.value = null
  detailLoading.value = false
  currentWork.value = ''
  if (updateUrl) syncUrl()
  if (wasOpen) {
    if (opener?.isConnected && opener !== document.body) opener.focus()
    else queryInput.value?.focus({ preventScroll: true })
  }
}

const restoreLocation = async () => {
  restoring = true
  if (debounceTimer) window.clearTimeout(debounceTimer)
  const state = readSearchUrl(new URLSearchParams(window.location.search))
  Object.assign(filters, state.filters)
  await nextTick()
  if (state.work) await openWork(state.work, false)
  else closeDetail(false)
  await runSearch(state.page, false)
  restoring = false
}
const reset = async () => {
  restoring = true
  Object.assign(filters, defaultFilters())
  await nextTick()
  restoring = false
  await runSearch()
}
const initialize = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(withBase('/api/v1/catalog-manifest.json'))
    if (!response.ok) throw new Error('Missing catalog manifest')
    manifest.value = await response.json()
    // Facet labels are small; Pagefind.filters() would eagerly download every identifier/URL filter.
    const facetResponse = await fetch(withBase('/pagefind/radar-facets.json'))
    if (!facetResponse.ok) throw new Error('Missing search facets')
    engineFilters.value = await facetResponse.json()
    const configResponse = await fetch(withBase('/pagefind/radar-config.json'))
    if (!configResponse.ok) throw new Error('Missing search configuration')
    searchLanguage = (await configResponse.json()).language || 'zh'
    engineReady.value = true
    await restoreLocation()
  } catch { error.value = '数据库尚未载入，请重试。完整数据库仍可通过上方链接下载。'; loading.value = false }
}
onMounted(() => {
  expandedFilters.value = activeFilterCount.value > 0
  window.addEventListener('popstate', restoreLocation)
  initialize()
})
onBeforeUnmount(() => {
  destroyed = true
  searchSerial += 1
  detailSerial += 1
  window.removeEventListener('popstate', restoreLocation)
  if (debounceTimer) window.clearTimeout(debounceTimer)
  dialog.value?.close()
})
watch(filters, scheduleSearch, { deep: true })
</script>

<template>
  <div class="v3-database">
    <header class="v3-page-heading">
      <div><p class="v3-eyebrow">RESEARCH CATALOG</p><h1>研究证据库</h1>
        <p v-if="manifest">{{ manifest.counts.works.toLocaleString('zh-CN') }} 项归并记录 · {{ manifest.counts.manifestations.toLocaleString('zh-CN') }} 个公开版本 · 数据截至 {{ manifest.data_through }}</p>
        <p v-if="manifest?.research_status_as_of && manifest.research_status_as_of > manifest.data_through">已登记状态通知另行更新至 {{ manifest.research_status_as_of }}；不把后续状态倒灌到旧月份的研究证据。</p>
        <p v-if="manifest">默认展示 {{ manifest.counts.included.toLocaleString('zh-CN') }} 项已纳入研究；候选、待复核和排除记录可通过相关性筛选查看。</p>
      </div><a :href="withBase('/downloads/radar.sqlite')" download>下载完整数据库</a>
    </header>
    <form class="v3-search" @submit.prevent="runSearch()">
      <label class="v3-search-box"><span class="sr-only">搜索标题、摘要、作者、机构、标识符或代码</span><input ref="queryInput" v-model="filters.q" type="search" placeholder="大小脑、world model、π0、作者、DOI……"><button type="submit">搜索</button></label>
      <p class="search-help">支持中英文关键词、作者与完整 DOI / 来源链接；留空可浏览研究库。</p>
      <details class="search-filter-drawer" :open="expandedFilters" @toggle="expandedFilters = ($event.target as HTMLDetailsElement).open">
        <summary>筛选研究 <span v-if="activeFilterCount">· {{ activeFilterCount }} 项已启用</span></summary>
        <div v-if="manifest" class="v3-filter-grid">
          <label>首次公开起始月<input v-model="filters.from" type="month" :min="manifest.available_months[0]" :max="manifest.provisional_month"></label>
          <label>首次公开结束月<input v-model="filters.to" type="month" :min="manifest.available_months[0]" :max="manifest.provisional_month"></label>
          <label>主 / 关联方向<select v-model="filters.direction"><option value="">全部方向</option><option v-if="filters.direction.includes(',')" :value="filters.direction">{{ filters.direction }}</option><option v-for="item in manifest.filter_options.directions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label>问题轴<select v-model="filters.question"><option value="">全部问题</option><option v-if="filters.question.includes(',')" :value="filters.question">{{ filters.question }}</option><option v-for="item in manifest.filter_options.questions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label>组织<select v-model="filters.organization"><option value="">全部组织</option><option v-if="filters.organization.includes(',')" :value="filters.organization">多组联合筛选</option><option value="unattributed">尚未归属</option><option v-for="item in manifest.filter_options.organizations" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label>产出类型<select v-model="filters.outputType"><option value="">全部类型</option><option v-for="item in options('output_type')" :key="item" :value="item">{{ optionLabel(item) }}</option></select></label>
          <label v-for="field in facetFields" :key="field.key">{{ field.label }}<select v-model="filters[field.key]"><option value="">全部</option><option v-for="item in options(field.source)" :key="item" :value="item">{{ optionLabel(item) }}</option></select></label>
          <label>证据等级<select v-model="filters.evidence"><option value="">全部等级</option><option v-for="item in manifest.filter_options.evidence" :key="item" :value="item">{{ item }}</option></select></label>
          <label>纳排状态<select v-model="filters.relevance"><option value="all">全库（含候选与待复核）</option><option v-for="item in manifest.filter_options.relevance" :key="item" :value="item">{{ optionLabel(item) }}</option></select></label>
        </div>
        <div class="v3-filter-switches"><label><input v-model="filters.peerReviewed" type="checkbox"> 严格同行评审</label><label><input v-model="filters.realRobot" type="checkbox"> 真机证据</label><label><input v-model="filters.openAssets" type="checkbox"> 开放模型 / 数据 / 代码</label><button type="button" @click="reset">清除筛选</button></div>
      </details>
      <p v-if="filters.ids" class="exact-evidence-note">当前限定 {{ filters.ids.split(',').length }} 项证据。<button type="button" @click="filters.ids = ''">解除证据集合限制</button></p>
      <p v-if="filters.from && filters.to && filters.from > filters.to" role="alert">起始月份不能晚于结束月份。</p>
    </form>
    <div class="v3-result-status" aria-live="polite"><span v-if="loading">正在检索……</span><span v-else-if="error" role="alert">{{ error }}</span><span v-else>找到 {{ total.toLocaleString('zh-CN') }} 项<span v-if="total"> · 正在显示 {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, total) }} 项</span></span><button v-if="error" type="button" @click="engineReady ? runSearch(page) : initialize()">重试</button></div>
    <section ref="resultsSection" class="visual-search-results" aria-label="研究工作搜索结果" :aria-busy="loading" tabindex="-1">
      <ResearchCard v-for="row in rows" :key="row.id" :work="researchCard(row)" compact detail-button @details="openWork" />
      <p v-if="!loading && !error && !rows.length" class="v3-empty">没有符合条件的记录。可切换到“全库”，或放宽月份、组织与证据筛选。</p>
    </section>
    <nav v-if="pageCount > 1" class="v3-pagination" aria-label="结果分页"><button type="button" :disabled="page === 1 || loading" @click="goToPage(page - 1)">上一页</button><span>第 {{ page }} / {{ pageCount }} 页</span><button type="button" :disabled="page === pageCount || loading" @click="goToPage(page + 1)">下一页</button><form @submit.prevent="goToPage(Number(pageInput))"><label><span class="sr-only">跳转页码</span><input v-model.number="pageInput" type="number" min="1" :max="pageCount" aria-label="跳转页码"></label><button type="submit" :disabled="loading">跳转</button></form></nav>
    <dialog ref="dialog" class="v3-work-detail search-work-dialog" aria-labelledby="work-detail-title" @cancel.prevent="closeDetail()" @click="($event.target === dialog) && closeDetail()">
      <div class="search-detail-content"><button class="v3-detail-close" type="button" aria-label="关闭详情" autofocus @click="closeDetail()">关闭</button><h2 id="work-detail-title">{{ detailHeading }}</h2>
        <p v-if="detailLoading" role="status">正在载入研究与公开版本……</p><div v-else-if="detailError" role="alert"><p>{{ detailError }}</p><button type="button" @click="openWork(currentWork, false)">重试</button></div>
        <template v-else-if="detail">
          <ResearchStatusNotice v-if="detail.research_status" :value="detail.research_status" title="请先核对研究状态" :context="detailResearchStatusContext" />
          <p v-if="detail.research_status?.information_gaps?.length" class="work-status-gap" role="status">研究状态的日期、来源或通知顺序仍有待核验项；缺少确定信息不等于已经撤回，也不等于已经恢复。下方原始内容保留供核对。</p>
          <p class="v3-eyebrow">{{ detail.primary_direction || '待分类' }} · {{ detail.evidence_grade }} · {{ optionLabel(detail.relevance?.status) }}</p><p v-if="detail.title_zh || detailHeading !== detail.title" class="v3-original-title">入库原题：{{ detail.title }}</p><p v-if="detail.summary_zh"><small v-if="detail.editorial_source === 'legacy_editorial'">历史编辑摘要（未按当前版次重新审核）：</small>{{ detail.summary_zh }}</p><details v-if="detail.abstract" class="work-original-abstract" :open="!detail.summary_zh && !detail.text_versions?.length"><summary>入库原始摘要</summary><p>{{ detail.abstract }}</p><p>这段保留原始入库文本；有版本档案时，请以下方带日期的版本原文为准。</p></details><p v-else-if="!detail.summary_zh">暂无摘要，可通过原文来源了解研究内容。</p>
          <dl><div><dt>首次公开</dt><dd>{{ eventDate(detail.first_public_date, detail.first_public_date_precision) }}</dd></div><div><dt>{{ currentTextMetadata ? '截至日版本作者' : '入库作者记录' }}</dt><dd>{{ (currentTextMetadata?.authors || detail.authors)?.join(' · ') || '待补' }}</dd></div><div><dt>方向</dt><dd>{{ detail.directions?.join(' · ') || '待分类' }}</dd></div><div><dt>问题轴</dt><dd>{{ detail.questions?.join(' · ') || '待归类' }}</dd></div><div><dt>组织</dt><dd>{{ detail.organization_details?.map((org: any) => org.name).join(' · ') || detail.organizations?.join(' · ') || '待归属' }}</dd></div><div><dt>证据</dt><dd>{{ detail.strict_peer_reviewed ? '严格同行评审' : '暂无已核验的同行评审记录' }} · {{ detail.evidence_grade }}</dd></div></dl>
          <details v-if="currentTextMetadata && JSON.stringify(currentTextMetadata.authors) !== JSON.stringify(detail.authors)"><summary>查看保留的入库作者记录</summary><p>{{ detail.authors?.join(' · ') || '未记录' }}</p></details>
          <section v-if="detail.organization_attributions?.length"><h3>研究组归属证据</h3><ul><li v-for="(link, index) in detail.organization_attributions" :key="index"><strong>{{ link.name }}</strong> · {{ link.evidence_grade }} · {{ link.evidence_grade === 'G1' ? '直接来源' : link.evidence_grade === 'G2' ? '按论文日期重建归属' : link.evidence_grade === 'G0' ? '仅母机构，不归入具体组' : '待核验线索' }} <a v-if="link.evidence_url" :href="link.evidence_url" target="_blank" rel="noopener noreferrer">核对归属原文</a><p v-if="link.membership_evidence">{{ link.membership_evidence.author }} · 证据覆盖 {{ eventDate(link.membership_evidence.valid_from) }}—{{ link.membership_evidence.valid_to ? eventDate(link.membership_evidence.valid_to) : '所记录的在组期间' }} <a :href="link.membership_evidence.source_url" target="_blank" rel="noopener noreferrer">成员关系来源</a></p></li></ul></section>
          <section v-if="detail.text_versions?.length"><h3>版本原文与修订日期</h3><p>下列日期表示该版文本何时可用，不是把后续修订写回首次公开月份。</p><ul><li v-for="version in detail.text_versions" :key="version.snapshot_id"><button type="button" @click="openTextVersion(version.snapshot_id)">{{ version.version || '版本号未记录' }} · {{ eventDate(version.available_at, version.date_precision) }} · 查看摘要</button> <a :href="version.source_url" target="_blank" rel="noopener noreferrer">官方来源</a></li></ul><p v-if="versionLoading" role="status">正在读取版本原文……</p><p v-if="versionError" role="alert">{{ versionError }}</p><article v-if="versionText"><h4>{{ versionText.title }}</h4><p>{{ versionText.authors.join(' · ') }}</p><p>{{ versionText.abstract || '该版本未保存摘要。' }}</p></article></section>
          <ReportTextEvidence v-if="detail.report_text_versions?.length" :value="detail.current_report_text" />
          <section v-if="detail.evidence_flag_evidence?.length"><h3>实验事实与适用范围</h3><p>以下核查确认来源如何描述实验，不等于独立复现或专家对技术结论的认可。</p><article v-for="record in detail.evidence_flag_evidence" :key="record.record_id"><h4>{{ reportTags[record.flag] || record.flag }} · {{ eventDate(record.public_at, record.date_precision) }}</h4><p>{{ record.observation_scope }}</p><p><a :href="record.source_url" target="_blank" rel="noopener noreferrer">核对原始来源</a></p></article></section>
          <section v-if="evidenceEvents.length" class="work-report-evidence" aria-label="发布记录与技术报告证据">
            <h3>发布记录与技术报告证据</h3>
            <p class="report-comparability-note">指标按原报告的条件展示。不同任务、硬件、评测样本与人工干预条件不能直接横向比较；未披露的数值显示为“未披露”。</p>
            <p class="report-comparability-note">以下保留历史采集记录，部分标题可能是索引卡片原文；旧技术标签尚未逐项绑定原文证据，不能仅凭梯度更新等措辞推断采用了强化学习。历史正文请优先查看上方有日期与指纹的摘录。</p>
            <article v-for="(event, eventIndex) in evidenceEvents" :key="event.event_id || event.update_id || `${event.url || 'event'}-${eventIndex}`" class="work-report-event">
              <header><p class="report-event-date">{{ eventDate(event.published_at || event.occurred_at || event.date, event.date_precision) }}</p><h4>{{ event.title_zh || event.title || '证据记录' }}</h4><p v-if="event.title_zh && event.title && event.title_zh !== event.title" class="v3-original-title">{{ event.title }}</p></header>
              <div class="report-claim-labels"><strong :class="{ 'company-claim': reportIsCompanyClaim(event) }">{{ reportClaimLabel(event) }}</strong><span>{{ validationLabel(event) }}</span></div>
              <p v-if="reportIsCompanyClaim(event)" class="report-self-report-note">以下为公司自行披露的结果。同行评审状态与独立复现情况需分别核对。</p>
              <p v-if="event.summary_zh">{{ event.summary_zh }}</p>
              <dl class="report-context">
                <div><dt>旧技术标签（待核验）</dt><dd>{{ stringItems(event.technical_stack_tags).map((tag) => reportTags[tag] || tag).join(' · ') || '尚未披露 / 待整理' }}</dd></div>
                <div><dt>验证场景</dt><dd>{{ stringItems(event.validation_tags).map((tag) => reportTags[tag] || tag).join(' · ') || '尚未披露 / 待整理' }}</dd></div>
                <div><dt>开放资产</dt><dd><template v-if="disclosedAssets(event.open_assets).length"><template v-for="(asset, assetIndex) in disclosedAssets(event.open_assets)" :key="`${asset.label}-${assetIndex}`"><span v-if="assetIndex"> · </span><a v-if="asset.url" :href="asset.url" target="_blank" rel="noopener noreferrer">{{ asset.label }}</a><span v-else>{{ asset.label }}（入口见原文）</span></template></template><span v-else>当前记录未列出可核验的开放资产</span></dd></div>
              </dl>
              <details :open="Boolean(event.report_metrics?.length)" class="report-metric-details"><summary>指标与适用条件 <span v-if="event.report_metrics?.length">（{{ event.report_metrics.length }} 项）</span></summary>
                <div v-if="event.report_metrics?.length" class="report-metrics">
                  <article v-for="(metric, metricIndex) in event.report_metrics" :key="`${metric.label}-${metricIndex}`" class="report-metric">
                    <h5>{{ metric.label || '未命名指标' }}</h5>
                    <p class="report-metric-value">{{ metricValue(metric.value) }} <span v-if="metricValue(metric.value) !== '未披露' && metric.unit">{{ metric.unit }}</span></p>
                    <dl><div><dt>适用范围 / 实验条件</dt><dd>{{ metric.scope || '条件未披露，无法确认可比性' }}</dd></div><div><dt>限定与备注</dt><dd>{{ metric.note || '当前记录未提取补充说明，请查阅原报告' }}</dd></div></dl>
                  </article>
                </div><p v-else>当前记录尚未提取可对照的数值指标，请查阅原文。未披露项不按零值处理。</p>
              </details>
              <div v-if="stringItems(event.limitation_zh || event.limitations).length" class="report-limitations"><h5>这项证据的局限</h5><p v-for="(limitation, limitationIndex) in stringItems(event.limitation_zh || event.limitations)" :key="limitationIndex">{{ limitation }}</p></div>
              <footer class="report-evidence-sources"><a v-for="source in evidenceSources(event)" :key="source.url" :href="source.url" target="_blank" rel="noopener noreferrer">{{ source.label }}<small>{{ source.url }}</small></a><p v-if="!evidenceSources(event).length">原文链接尚待补充，暂不据此作独立验证判断。</p></footer>
            </article>
          </section>
          <section v-if="stringItems(detail.limitation_zh).length" class="work-limitations"><h3>研究局限与信息缺口</h3><p v-for="(limitation, limitationIndex) in stringItems(detail.limitation_zh)" :key="limitationIndex">{{ limitation }}</p></section>
          <section><h3>公开版本与研究资产</h3><a v-for="item in detail.manifestations" :key="item.manifestation_id" :href="item.url" target="_blank" rel="noopener noreferrer"><span>{{ item.kind }} · {{ item.venue || item.status || '公开来源' }}<span v-if="item.track"> · {{ item.track }}</span></span><strong>{{ eventDate(item.accepted_at || item.published_at || (item.year ? String(item.year) : null), item.accepted_at ? item.accepted_date_precision : item.date_precision) }}</strong></a><p v-if="!detail.manifestations?.length">公开版本正在补充。</p></section>
          <section v-if="detail.events?.length"><h3>验证与发布事件</h3><a v-for="item in detail.events" :key="item.event_id" :href="item.evidence_url || item.url" target="_blank" rel="noopener noreferrer"><span>{{ item.title || item.event_type || item.kind }}</span><strong>{{ eventDate(item.occurred_at || item.published_at || item.date, item.date_precision) }}</strong></a></section><code>{{ detail.work_id }}</code>
        </template>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
.search-filter-drawer summary { cursor: pointer; padding: 14px 0; font-weight: 600; }
.search-help { margin: 8px 0 0; font-size: 12px; color: var(--vp-c-text-2); }
.search-filter-drawer .v3-filter-grid { margin-top: 0; }
.exact-evidence-note { font-size: 13px; }
.exact-evidence-note button { color: var(--vp-c-brand-1); text-decoration: underline; margin-left: 8px; }
.v3-pagination { flex-wrap: wrap; }
.v3-pagination form { display: flex; gap: 8px; align-items: center; }
.v3-pagination input { width: 70px; min-height: 44px; border: 1px solid var(--vp-c-divider); border-radius: 8px; padding: 8px; }
.v3-result-status button, .v3-pagination button, .v3-filter-switches button { min-height: 44px; }
.search-work-dialog { position: fixed; inset: 0 0 0 auto; margin: 0; max-height: 100dvh; height: 100dvh; max-width: min(780px, 100vw); border: 0; background: var(--vp-c-bg); color: var(--vp-c-text-1); padding: 0; z-index: 100; }
.search-work-dialog:not([open]) { display: none; }
.search-work-dialog::backdrop { background: rgb(0 0 0 / 48%); }
.search-detail-content { padding: 32px; min-height: 100%; overflow-wrap: anywhere; }
.search-work-dialog h2 { padding-right: 60px; }
.search-work-dialog .v3-detail-close { position: sticky; top: 0; float: right; min-height: 44px; background: var(--vp-c-bg); }
.search-work-dialog dl { margin: 24px 0; }
.search-work-dialog code, .v3-results footer code { overflow-wrap: anywhere; white-space: normal; }
.v3-results { scroll-margin-top: 80px; }
.v3-database :is(a, button, input, select, summary):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.v3-filter-grid input, .v3-filter-grid select { min-height: 44px; }
.v3-results article h2 button { text-align: left; }
.work-original-abstract summary, .report-metric-details summary { min-height: 44px; display: flex; align-items: center; gap: 6px; cursor: pointer; font-weight: 550; }
.work-original-abstract p { white-space: pre-line; line-height: 1.75; }
.report-comparability-note, .report-self-report-note { color: var(--vp-c-text-2); font-size: 13px; line-height: 1.7; }
.work-report-event { border: 1px solid var(--vp-c-divider); border-radius: 10px; padding: 20px; margin: 18px 0; }
.work-report-event h4 { font-size: 17px; line-height: 1.5; margin: 5px 0 10px; }
.report-event-date { margin: 0; color: var(--vp-c-text-2); font-size: 12px; }
.report-claim-labels { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; font-size: 12px; }
.report-claim-labels strong { padding: 4px 8px; border: 1px solid var(--vp-c-divider); border-radius: 5px; font-weight: 600; }
.report-claim-labels .company-claim { color: var(--vp-c-warning-1); border-color: var(--vp-c-warning-1); }
.report-claim-labels span { color: var(--vp-c-text-2); }
.search-work-dialog .report-context { margin: 16px 0; }
.search-work-dialog .report-context > div { grid-template-columns: 70px minmax(0, 1fr); gap: 10px; }
.report-metrics { display: grid; gap: 12px; }
.report-metric { padding: 14px; border-radius: 7px; background: var(--vp-c-bg-soft); min-width: 0; }
.report-metric h5, .report-limitations h5 { margin: 0 0 7px; font-size: 14px; line-height: 1.6; font-weight: 600; }
.report-metric-value { margin: 8px 0 10px; font-size: 22px; line-height: 1.4; font-weight: 600; }
.report-metric-value span { font-size: 13px; font-weight: 400; color: var(--vp-c-text-2); }
.search-work-dialog .report-metric dl { margin: 0; }
.search-work-dialog .report-metric dl > div { display: block; padding: 6px 0; border: 0; }
.report-metric dd { margin-top: 4px; line-height: 1.65; }
.report-limitations { margin-top: 18px; }
.report-evidence-sources { border-top: 1px solid var(--vp-c-divider); padding-top: 12px; margin-top: 16px; }
.report-evidence-sources a { display: block; margin: 8px 0; font-size: 13px; min-height: 44px; }
.report-evidence-sources small { display: block; color: var(--vp-c-text-2); line-height: 1.5; overflow-wrap: anywhere; }
.work-limitations { border-left: 3px solid var(--vp-c-warning-1); padding-left: 16px; }
.work-status-gap { padding: 12px 16px; border: 1px solid var(--vp-c-warning-1); border-radius: 8px; background: var(--vp-c-bg-soft); line-height: 1.7; }
.search-research-status { border: 1px solid var(--vp-c-warning-1); border-radius: 4px; padding: 3px 6px; background: var(--vp-c-bg-soft); }
.search-research-status.blocked { border-color: var(--vp-c-danger-1); color: var(--vp-c-danger-1); font-weight: 600; }
@media (max-width: 767px) {
  .search-filter-drawer summary { min-height: 48px; }
  .v3-search:has(.search-filter-drawer[open]) { position: static; }
  .v3-search-box input { min-width: 0; }
  .v3-filter-grid { grid-template-columns: minmax(0, 1fr); }
  .search-detail-content { padding: 20px; }
  .search-work-dialog { width: 100%; max-width: 100%; }
  .v3-result-status { flex-wrap: wrap; }
  .work-report-event { padding: 14px; }
  .report-metric { padding: 12px; }
}
</style>
