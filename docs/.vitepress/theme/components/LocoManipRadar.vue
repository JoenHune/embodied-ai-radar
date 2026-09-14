<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, withBase } from 'vitepress'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { AriaComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ChartFrame from './ChartFrame.vue'
import ResearchCard from './ResearchCard.vue'
import { chartTokens, useEChart } from '../composables/useEChart'
import { eventDate } from '../lib/dates'

echarts.use([BarChart, AriaComponent, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])
type Scope = 'core' | 'support' | 'candidates' | 'excluded'
type Work = { work_id: string; title: string; first_public_date?: string; [key: string]: any }
type Review = { work_id: string; scope: string; effective_scope?: string; relevance_status?: string; review_status?: string; candidate_reason?: string | null; coordination?: string; validation?: string; source_url?: string; source_locator?: string; statement?: string; observed_at?: string; project_id?: string }
type Month = { month: string; provisional: boolean; core: number; support: number; candidates: number }
type Observation = { claim_id: string; title: string; summary: string; supporting_ids: string[]; counterevidence_ids: string[]; source_urls: string[]; review_status?: string; candidate_work_ids?: string[]; supporting_work_status?: Record<string, { relevance_status?: string; review_status?: string; effective_scope?: string }> }
type LocoData = { schema_version: string; dataset_version: string; source_version?: string; data_through?: string; window?: { complete_months?: string[]; provisional_month?: string }; counts: Record<Scope, number>; monthly: Month[]; observations: Observation[]; reviews: Review[]; work_ids: Record<Scope, string[]> }
const groups: { key: Scope; title: string; note: string }[] = [
  { key: 'core', title: '核心', note: '直接研究身体或移动与接触操作的联合协调；真机闭环、真机回放与仿真分别标示，核心分组不自动代表真机闭环。' },
  { key: 'support', title: '支撑', note: '为联合操作提供方法、数据或控制支撑；不等同已经完成核心任务验证。' },
  { key: 'candidates', title: '候选', note: '定义、协调机制或验证环境尚待确认，不计入核心与支撑的已核验集合。' },
  { key: 'excluded', title: '排除', note: '保留边界案例与具体排除依据；排除的是本专题范围，不是论文质量。' },
]
const validationLabels: Record<string, string> = { closed_loop_real: '真机闭环', replay_only_real: '真机仅回放', simulation_only: '仅仿真', unclear: '验证方式未明确' }
const relevanceLabels: Record<string, string> = { included: '研究库已纳入', manual_review: '研究库分类待复核', candidate: '研究库候选', excluded: '研究库已排除', unknown: '研究纳排未明确' }
const candidateReasonLabels: Record<string, string> = { catalog_not_included: '研究库尚未正式纳入；专题范围意见不能自动升级研究纳排。', scope_review_pending: '专题范围审阅尚未通过；保留原始意见等待复核。' }
const coordinationLabels: Record<string, string> = { joint: '联合协调', coupled: '耦合协调', whole_body: '全身协调', loco_manipulation: '移动与操作联合', sequential: '顺序拼接', fixed_base: '固定底座', unclear: '协调机制待明确', none: '未建立联合协调' }
const data = ref<LocoData | null>(null)
const rows = ref<Work[]>([])
const scope = ref<Scope>('core')
const month = ref('')
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
const workMap = computed(() => new Map(rows.value.map(work => [work.work_id, work])))
const reviewsByWork = computed(() => {
  const result = new Map<string, Review[]>()
  for (const review of data.value?.reviews || []) result.set(review.work_id, [...(result.get(review.work_id) || []), review])
  return result
})
const monthOf = (work?: Work) => !['year', 'unknown'].includes(work?.first_public_date_precision) && /^\d{4}-(0[1-9]|1[0-2])(?:$|-)/.test(work?.first_public_date || '') ? work!.first_public_date!.slice(0, 7) : 'unknown'
const provisionalMonth = computed(() => data.value?.window?.provisional_month || data.value?.monthly.find(row => row.provisional)?.month || '')
const monthly = computed(() => (data.value?.monthly || []).filter(row => /^\d{4}-(0[1-9]|1[0-2])$/.test(row.month)).slice().sort((a, b) => a.month.localeCompare(b.month)))
const months = computed(() => [...new Set([...monthly.value.map(row => row.month), ...(data.value?.window?.complete_months || []), ...rows.value.map(monthOf)].filter(value => /^\d{4}-(0[1-9]|1[0-2])$/.test(value)))].sort().reverse())
const groupIds = (key: Scope) => [...new Set(data.value?.work_ids[key] || [])]
const groupItems = (key: Scope) => groupIds(key).map(id => ({ id, work: workMap.value.get(id), reviews: reviewsByWork.value.get(id) || [] })).filter(item => !month.value || monthOf(item.work) === month.value).sort((a, b) => (b.work?.first_public_date || '').localeCompare(a.work?.first_public_date || '') || (a.work?.title || a.id).localeCompare(b.work?.title || b.id, 'zh-CN'))
const filtered = computed(() => groupItems(scope.value))
const visible = computed(() => filtered.value.slice(0, shown.value))
const activeGroup = computed(() => groups.find(group => group.key === scope.value)!)
const missingWorkCount = computed(() => [...new Set(groups.flatMap(group => groupIds(group.key)))].filter(id => !workMap.value.has(id)).length)
const workUrl = (id: string) => withBase(`/database/?${new URLSearchParams({ work: id, relevance: 'all' })}`)
const workTitle = (id: string) => workMap.value.get(id)?.title_zh || workMap.value.get(id)?.title || id
const sources = (observation: Observation) => [...new Set(observation.source_urls || [])].filter(url => publicUrl(url))
const observationIsCandidate = (observation: Observation) => observation.review_status !== 'verified' || Boolean(observation.candidate_work_ids?.length) || Object.values(observation.supporting_work_status || {}).some(status => status.relevance_status !== 'included' || status.review_status !== 'verified' || status.effective_scope === 'candidates')
const dependencyStatus = (observation: Observation, id: string) => {
  const status = observation.supporting_work_status?.[id]
  if (!status) return '纳排与审阅状态待核验'
  return `${relevanceLabels[status.relevance_status || 'unknown'] || status.relevance_status} · ${status.review_status === 'verified' ? '范围审阅已登记' : '范围审阅待确认'}`
}
const reviewIsCandidate = (review: Review) => review.effective_scope === 'candidates' || review.review_status !== 'verified' || Boolean(review.relevance_status && review.relevance_status !== 'included')
const candidateReason = (review: Review) => candidateReasonLabels[review.candidate_reason || ''] || review.candidate_reason || '研究纳排或范围审阅仍待确认，不作已验证结论。'
const readUrl = () => {
  const params = new URLSearchParams(window.location.search)
  const nextScope = params.get('scope') || ''
  scope.value = groups.some(group => group.key === nextScope) ? nextScope as Scope : 'core'
  const nextMonth = params.get('month') || ''
  month.value = nextMonth === 'unknown' || /^\d{4}-(0[1-9]|1[0-2])$/.test(nextMonth) ? nextMonth : ''
  const amount = Number(params.get('shown') || 12)
  shown.value = Number.isFinite(amount) ? Math.max(12, Math.min(12000, Math.floor(amount / 12) * 12)) : 12
}
const writeUrl = (reset = true) => {
  if (reset) shown.value = 12
  const url = new URL(window.location.href)
  scope.value === 'core' ? url.searchParams.delete('scope') : url.searchParams.set('scope', scope.value)
  month.value ? url.searchParams.set('month', month.value) : url.searchParams.delete('month')
  shown.value > 12 ? url.searchParams.set('shown', String(shown.value)) : url.searchParams.delete('shown')
  if (url.href !== window.location.href) window.history.pushState(window.history.state, '', url)
}
const selectGroup = (key: Scope) => { scope.value = key; writeUrl() }
const reset = () => { scope.value = 'core'; month.value = ''; writeUrl() }
const more = async () => {
  const firstNew = visible.value.length
  shown.value += 12
  writeUrl(false)
  await nextTick()
  list.value?.querySelectorAll<HTMLElement>('.loco-work')[firstNew]?.focus({ preventScroll: true })
}
const load = async () => {
  const request = ++requestId
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = ''
  data.value = null
  rows.value = []
  try {
    const responses = await Promise.all(['/api/v1/equipment/loco-manip.json', '/api/v1/equipment/works.json'].map(path => fetch(withBase(path), { signal: controller!.signal, cache: 'no-cache' })))
    if (responses.some(response => !response.ok)) throw new Error('unavailable')
    const [loco, works] = await Promise.all(responses.map(response => response.json()))
    if (disposed || request !== requestId) return
    if (loco.schema_version !== '1' || works.schema_version !== '1' || !Array.isArray(loco.monthly) || !Array.isArray(loco.reviews) || !Array.isArray(loco.observations) || !Array.isArray(works.rows) || !loco.work_ids || groups.some(group => !Array.isArray(loco.work_ids[group.key]))) throw new Error('invalid')
    if (!loco.dataset_version || loco.dataset_version !== works.dataset_version || ((loco.source_version != null || works.source_version != null) && loco.source_version !== works.source_version)) throw new Error('version')
    if (works.rows.some((work: Work) => !work.work_id || !work.title)) throw new Error('invalid')
    data.value = loco
    rows.value = Array.from(new Map<string, Work>(works.rows.map((work: Work) => [work.work_id, work])).values())
    readUrl()
  } catch (cause) {
    if (!disposed && request === requestId) error.value = cause instanceof Error && cause.message === 'version' ? '专题分组与研究卡片来自不同数据版本，已停止混合展示。请重新读取。' : '专题定义、研究与核验证据暂时无法读取，未把读取失败解释成没有相关研究。请重试。'
  } finally { if (!disposed && request === requestId) loading.value = false }
}
const chart = useEChart(() => {
  const tokens = chartTokens()
  return {
    animation: false, aria: { enabled: true, description: '核心与支撑的已核验样本分月分布；候选不进入趋势柱。暂行月份用虚线边框，不代表全领域增长。' },
    legend: { top: 0, textStyle: { color: tokens.muted } },
    tooltip: { trigger: 'axis', confine: true, backgroundColor: tokens.background, borderColor: tokens.divider, textStyle: { color: tokens.text } },
    grid: { left: 40, right: 20, top: 46, bottom: 56 },
    xAxis: { type: 'category', data: monthly.value.map(row => `${row.month}${row.provisional ? ' 暂行' : ''}`), axisLabel: { color: tokens.muted, formatter: (value: string) => value.replace(/^(\d{4})-/, '$1\n'), interval: monthly.value.length > 8 ? 1 : 0, showMaxLabel: true }, axisTick: { show: false }, axisLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } },
    series: (['core', 'support'] as const).map((key, i) => ({ name: key === 'core' ? '核心已核验' : '支撑已核验', type: 'bar', barMaxWidth: 22, data: monthly.value.map(row => ({ value: row[key], itemStyle: { color: tokens.palette[i], opacity: row.provisional ? .55 : 1, borderType: row.provisional ? 'dashed' : 'solid', borderWidth: row.provisional ? 2 : 0, borderColor: tokens.palette[i] } })) })),
  }
})
onMounted(() => {
  const pathname = window.location.pathname
  const previous = router.onBeforePageLoad
  const guard = (href: string) => { if (new URL(href, window.location.href).pathname === pathname) { readUrl(); return false }; return previous?.(href) }
  router.onBeforePageLoad = guard
  releaseRouteGuard = () => { if (router.onBeforePageLoad === guard) router.onBeforePageLoad = previous }
  readUrl()
  window.addEventListener('popstate', readUrl)
  void load()
})
onBeforeUnmount(() => { disposed = true; requestId++; controller?.abort(); releaseRouteGuard(); window.removeEventListener('popstate', readUrl) })
</script>

<template>
  <div class="v3-dashboard loco-radar">
    <header class="v3-page-heading"><div><p class="v3-eyebrow">LOCOMOTION × MANIPULATION</p><h1>移动与全身操作</h1><p>跟踪身体、移动与接触操作如何真正联合起来。</p></div></header>
    <aside class="loco-definition"><h2>本专题的边界</h2><p>关注身体姿态或移动与接触操作的联合协调：不是机器人有腿、有轮子或装了手臂就自动入选。固定底座操作、单独行走、动作回放与仅仿真结果需要分别核验，不冒充真机闭环联合操作。</p><p>核心、支撑、候选、排除是研究范围与证据的分流，不是质量排名；多篇论文也不自动等同多个独立项目。</p></aside>
    <p v-if="loading" role="status">正在读取专题样本与范围核验记录…</p>
    <div v-if="error" role="alert" class="loco-notice"><p>{{ error }}</p><button type="button" @click="load">重新读取</button></div>
    <template v-if="data && !loading && !error">
      <div class="loco-context"><span>数据截至 {{ eventDate(data.data_through) }}</span><span>版本 {{ data.dataset_version }}</span><a :href="withBase('/methods/equipment-loco')">范围与样本口径</a><a :href="withBase('/api/v1/equipment/loco-manip.json')">范围判断与来源数据</a><a :href="withBase('/api/v1/equipment/works.json')">研究卡片数据</a></div>
      <p v-if="provisionalMonth" class="loco-period-note"><span class="loco-provisional">{{ provisionalMonth }} 暂行</span> 当前月尚未结束，单独展示；以下数字只描述已登记样本，不宣称全领域增长或降温。</p>
      <ChartFrame title="已核验样本 · 分月分布" description="按研究首次公开月份组织当前已核验的核心与支撑样本；候选不进入趋势柱。图表保留完整窗口，不随下方分组筛选改变；不是历史当时已知快照，不提供全领域份额或增长率。" :height="310" compact>
        <div :ref="chart.element" role="img" aria-label="各月份核心与支撑已核验样本分布，候选不进入趋势柱，暂行月份单独标记" />
        <template #table><table><thead><tr><th>首次公开月份</th><th>窗口状态</th><th>核心已核验</th><th>支撑已核验</th></tr></thead><tbody><tr v-for="row in monthly" :key="row.month" :class="{ 'is-provisional': row.provisional }"><th>{{ row.month }}</th><td>{{ row.provisional ? '暂行' : '完整月份' }}</td><td>{{ row.core }}</td><td>{{ row.support }}</td></tr></tbody></table></template>
      </ChartFrame>
      <p v-if="!monthly.length" class="loco-notice">尚无可用的逐月样本分布，不将缺失月份填为零。</p>
      <section v-if="data.observations.length" class="loco-observations" aria-labelledby="loco-observations-heading"><h2 id="loco-observations-heading">观察、来源与待确认依赖</h2><p class="loco-muted">判断与来源并列保留；单个成功案例不能代表整个方向已解决。</p><article v-for="observation in data.observations" :key="observation.claim_id" :class="{ 'is-candidate': observationIsCandidate(observation) }"><h3>{{ observation.title }}</h3><p v-if="observationIsCandidate(observation)" class="loco-candidate-notice" role="note"><strong>候选判断 · 不能升级为已验证结论。</strong>依赖研究的纳排或范围审阅仍待确认，以下为带来源的待审观察。</p><p>{{ observation.summary }}</p><div class="loco-proof-columns"><div><h4>支持引用与当前状态</h4><ul v-if="observation.supporting_ids?.length"><li v-for="id in observation.supporting_ids" :key="id"><a :href="workUrl(id)">{{ workTitle(id) }}</a><small>{{ dependencyStatus(observation, id) }}</small></li></ul><p v-else class="loco-muted">尚未绑定具体研究，须结合原文继续核验。</p></div><div><h4>反证与边界</h4><ul v-if="observation.counterevidence_ids?.length"><li v-for="id in observation.counterevidence_ids" :key="id"><a :href="workUrl(id)">{{ workTitle(id) }}</a><small>{{ dependencyStatus(observation, id) }}</small></li></ul><p v-else class="loco-muted">未登记反证，不代表不存在反例。</p></div></div><p v-if="observation.candidate_work_ids?.length" class="loco-pending-dependencies">待确认依赖：<a v-for="id in observation.candidate_work_ids" :key="id" :href="workUrl(id)">{{ workTitle(id) }}</a></p><footer><a v-for="(url, i) in sources(observation)" :key="url" :href="url" target="_blank" rel="noopener noreferrer">观察来源 {{ i + 1 }} ↗</a><span v-if="!sources(observation).length" class="loco-muted">直接来源链接待补</span></footer></article></section>
      <section class="loco-browser" aria-labelledby="loco-browser-heading"><h2 id="loco-browser-heading">逐项查看范围与验证</h2>
        <div class="loco-toolbar"><label>研究首次公开月份<select v-model="month" @change="writeUrl()"><option value="">全部已登记月份</option><option v-for="value in months" :key="value" :value="value">{{ value }}{{ value === provisionalMonth ? ' · 暂行' : '' }}</option><option value="unknown">日期待核验</option></select></label><button type="button" @click="reset">恢复全部月份与核心组</button></div>
        <div class="loco-groups" role="group" aria-label="专题样本分组"><button v-for="group in groups" :key="group.key" type="button" :aria-pressed="scope === group.key" aria-controls="loco-work-list" @click="selectGroup(group.key)"><span>{{ group.title }}</span><strong>{{ groupItems(group.key).length }}</strong><small>{{ group.key === 'candidates' ? '待核验，不并入核心' : group.key === 'excluded' ? '保留排除依据' : '已核验范围样本' }}</small></button></div>
        <p class="loco-group-note" aria-live="polite">{{ activeGroup.title }} · {{ activeGroup.note }}{{ month ? ' 上方分组数量已按所选月份筛选。' : '' }}</p>
        <p v-if="missingWorkCount" class="loco-notice" role="status">{{ missingWorkCount }} 项范围记录尚缺同版本研究卡片，保留ID与核验来源，不使用其他版本内容代替。缺日期条目仅在全部月份或日期待核验筛选中显示。</p>
        <div id="loco-work-list" ref="list" class="loco-work-list">
          <article v-for="item in visible" :key="item.id" class="loco-work" tabindex="-1" :class="{ 'is-provisional': monthOf(item.work) === provisionalMonth, 'is-excluded': scope === 'excluded' }">
            <p v-if="monthOf(item.work) === provisionalMonth" class="loco-provisional">{{ provisionalMonth }} 暂行样本</p>
            <ResearchCard v-if="item.work" :work="item.work" compact />
            <div v-else class="loco-missing-card"><h3><a :href="workUrl(item.id)">{{ item.id }}</a></h3><p>同版本研究卡片尚未提供；范围判断与原文依据保留如下。</p></div>
            <section class="loco-reviews" :aria-label="`${item.work?.title || item.id}的范围与验证依据`"><h3>{{ scope === 'excluded' ? '为什么排除于本专题' : scope === 'candidates' ? '还需要核实什么' : '范围判断与真实验证' }}</h3>
              <article v-for="(review, i) in item.reviews" :key="`${review.work_id}-${i}`"><p v-if="reviewIsCandidate(review)" class="loco-candidate-notice"><strong>候选范围记录。</strong>{{ candidateReason(review) }}<br />{{ relevanceLabels[review.relevance_status || 'unknown'] || review.relevance_status }}；原范围意见保留，不代表当前已纳入。</p><div class="loco-review-meta"><strong>{{ validationLabels[review.validation || 'unclear'] || review.validation }}</strong><span v-if="review.coordination">协同机制：{{ coordinationLabels[review.coordination] || review.coordination }}</span><span v-if="review.project_id">项目线：{{ review.project_id }}</span></div><p>{{ review.statement || '判断说明待补充，不从研究标题自动推断验证范围。' }}</p><footer><a v-if="publicUrl(review.source_url)" :href="review.source_url" target="_blank" rel="noopener noreferrer">核对判断原文 ↗</a><span v-else>原文链接未提供</span><span>原文位置：{{ review.source_locator || '未提供定位' }}</span><span>核验于 {{ eventDate(review.observed_at) }}</span></footer></article>
              <p v-if="!item.reviews.length" class="loco-muted">尚未登记逐项范围判断。{{ scope === 'candidates' ? '等待核实身体/移动是否与接触操作联合，以及是否有真机闭环证据。' : '当前分组保留；不以标题、机器人形态或宣传演示代替原文证据。' }}</p>
            </section>
          </article>
        </div>
        <p v-if="!filtered.length" class="loco-empty">当前筛选没有登记到此组样本，不代表领域没有相关工作，也不代表其他组已获得更强验证。</p>
        <div v-if="filtered.length" class="loco-more"><p aria-live="polite">已展示 {{ visible.length }} / {{ filtered.length }} 项{{ activeGroup.title }}样本</p><button v-if="visible.length < filtered.length" type="button" @click="more">再加载 12 项研究</button><p v-else>已展示当前分组与月份的全部登记样本。</p></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.loco-radar { min-width: 0; }
.loco-radar :is(p, h1, h2, h3, h4, li, a, span) { overflow-wrap: anywhere; }
.loco-radar :is(button, select) { min-height: 44px; padding: 8px 12px; border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.loco-radar button, .loco-radar summary { cursor: pointer; }
.loco-radar :is(button, select, a, [tabindex]):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.loco-definition, .loco-notice { margin: 20px 0; padding: 15px 18px; background: var(--vp-c-bg-soft); border-left: 3px solid var(--vp-c-brand-1); font-size: 14px; line-height: 1.8; }
.loco-definition h2 { border: 0; margin: 0 0 8px; font-size: 16px; }
.loco-definition p, .loco-notice p { margin: 5px 0; }
.loco-context { display: flex; flex-wrap: wrap; gap: 8px 18px; color: var(--vp-c-text-2); font-size: 13px; }
.loco-period-note { color: var(--vp-c-text-2); font-size: 14px; line-height: 1.8; margin: 20px 0; }
.loco-provisional { display: inline-block; border: 1px dashed var(--vp-c-warning-1); background: var(--vp-c-warning-soft); color: var(--vp-c-text-1); padding: 3px 9px; font-size: 12px; border-radius: 5px; }
.loco-radar tr.is-provisional { background: var(--vp-c-warning-soft); }
.loco-observations { margin: 32px 0; }
.loco-observations > h2, .loco-browser > h2 { font-size: 23px; margin-bottom: 10px; }
.loco-muted, .loco-group-note, .loco-empty { color: var(--vp-c-text-2); font-size: 14px; line-height: 1.8; }
.loco-observations > article { border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 20px; margin-top: 16px; }
.loco-observations h3 { margin: 0 0 10px; font-size: 18px; }
.loco-observations p { font-size: 14px; line-height: 1.8; }
.loco-observations > article.is-candidate { border-left: 3px dashed var(--vp-c-warning-1); }
.loco-candidate-notice { padding: 10px 12px; background: var(--vp-c-warning-soft); border-radius: 5px; color: var(--vp-c-text-1); }
.loco-proof-columns small { display: block; color: var(--vp-c-text-2); margin-top: 3px; }
.loco-pending-dependencies { display: flex; flex-wrap: wrap; gap: 5px 12px; }
.loco-proof-columns { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; margin-top: 14px; }
.loco-proof-columns h4 { margin: 0 0 8px; font-size: 13px; }
.loco-proof-columns ul { padding-left: 18px; font-size: 13px; line-height: 1.75; }
.loco-observations footer, .loco-reviews footer { display: flex; flex-wrap: wrap; gap: 8px 18px; margin-top: 12px; font-size: 12px; color: var(--vp-c-text-2); }
.loco-toolbar { display: flex; flex-wrap: wrap; gap: 14px; align-items: end; margin: 20px 0; }
.loco-toolbar label { display: grid; gap: 7px; font-size: 13px; min-width: 0; }
.loco-toolbar select { max-width: 100%; }
.loco-groups { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.loco-groups button { display: flex; align-items: start; flex-direction: column; gap: 8px; padding: 16px; text-align: left; }
.loco-groups button[aria-pressed="true"] { border-color: var(--vp-c-brand-1); box-shadow: inset 0 0 0 1px var(--vp-c-brand-1); background: var(--vp-c-brand-soft); }
.loco-groups strong { font-size: 25px; font-weight: 600; }
.loco-groups small { color: var(--vp-c-text-2); font-size: 12px; }
.loco-work-list { display: grid; gap: 28px; margin-top: 22px; }
.loco-work { min-width: 0; border-radius: 14px; }
.loco-work.is-provisional { padding-left: 14px; border-left: 3px dashed var(--vp-c-warning-1); }
.loco-work > .loco-provisional { margin: 0 0 10px; }
.loco-missing-card { border: 1px solid var(--vp-c-divider); border-radius: 12px 12px 0 0; padding: 20px; }
.loco-missing-card h3 { font-size: 17px; margin: 0 0 8px; }
.loco-missing-card p { color: var(--vp-c-text-2); font-size: 14px; }
.loco-reviews { border: 1px solid var(--vp-c-divider); border-top: 0; border-radius: 0 0 12px 12px; padding: 16px 20px; background: var(--vp-c-bg-soft); }
.loco-reviews > h3 { font-size: 14px; margin: 0 0 12px; }
.loco-reviews > article + article { padding-top: 16px; margin-top: 16px; border-top: 1px solid var(--vp-c-divider); }
.loco-review-meta { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 13px; align-items: baseline; }
.loco-review-meta span { color: var(--vp-c-text-2); }
.loco-reviews p { font-size: 14px; line-height: 1.8; }
.loco-work.is-excluded .loco-reviews { border-left: 3px solid var(--vp-c-text-3); }
.loco-more { text-align: center; color: var(--vp-c-text-2); font-size: 14px; padding: 20px 0; }
.loco-empty { padding: 24px 0; }
@media (max-width: 700px) { .loco-groups { grid-template-columns: repeat(2, minmax(0, 1fr)); } .loco-proof-columns { grid-template-columns: 1fr; gap: 14px; } }
@media (max-width: 500px) { .loco-toolbar { display: grid; grid-template-columns: 1fr; } .loco-toolbar select { width: 100%; font-size: 16px; } .loco-observations > article, .loco-reviews { padding: 16px; } .loco-groups button { padding: 12px; } }
</style>
