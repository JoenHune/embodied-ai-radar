<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { withBase, useRouter } from 'vitepress'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, ScatterChart } from 'echarts/charts'
import { AriaComponent, GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ChartFrame from './ChartFrame.vue'
import ResearchStatusNotice from './ResearchStatusNotice.vue'
import SourceImage from './SourceImage.vue'
import ResearchCard from './ResearchCard.vue'
import { chartTokens, useEChart } from '../composables/useEChart'
import { eventDate } from '../lib/dates'
import { activitySummary, directionNames, escapeChartText, filterPeople, metricText, peopleStateFromUrl, peopleUrl, personDetailMatchesIndex, verifiedCollaborators, verifiedDirectionCount, type PeopleState } from '../lib/people-view.mjs'
import { PEOPLE_BATCH_SIZE, nextPeopleCount, peopleStreamKey, observePeopleEnd, preservePeoplePage } from '../lib/people-stream.mjs'
import { personWorkList } from '../lib/people-view.mjs'

echarts.use([BarChart, LineChart, ScatterChart, AriaComponent, GridComponent, TooltipComponent, CanvasRenderer])
const index = ref<any>(null)
const router = useRouter()
const detail = ref<any>(null)
const state = ref<PeopleState>({ q: '', direction: '', lens: 'contribution', sort: 'name', person: '' })
const loading = ref(true)
const detailLoading = ref(false)
const error = ref('')
const detailError = ref('')
const visibleCount = ref(PEOPLE_BATCH_SIZE)
const streamEnd = ref<HTMLElement | null>(null)
const peopleGrid = ref<HTMLElement | null>(null)
const heading = ref<HTMLElement | null>(null)
const personDialog = ref<HTMLDialogElement | null>(null)
const highlights = ref<Record<string, any[]>>({})
let returnFocus: HTMLElement | null = null
let stopStreamObserver = () => {}
let releasePageGuard = () => {}
let disposed = false
let detailRequest = 0
const people = computed<any[]>(() => index.value?.people || [])
const months = computed<string[]>(() => index.value?.window?.months || [])
const filtered = computed(() => filterPeople(people.value, state.value, months.value))
const streamKey = computed(() => peopleStreamKey(state.value))
const visible = computed(() => filtered.value.slice(0, visibleCount.value))
const hasMore = computed(() => visible.value.length < filtered.value.length)
const selected = computed<any>(() => people.value.find(person => person.slug === state.value.person) || null)
const profile = computed<any>(() => detail.value?.slug === state.value.person ? detail.value : selected.value)
const workScope = ref<'window' | 'all'>('window')
const allVerifiedWorks = computed<any[]>(() => detail.value?.slug === state.value.person ? detail.value.verified_works || [] : [])
const verifiedWorks = computed<any[]>(() => personWorkList(allVerifiedWorks.value, workScope.value))
const windowVerifiedCount = computed(() => allVerifiedWorks.value.filter(work => work.in_complete_window).length)
const candidates = computed<any[]>(() => detail.value?.slug === state.value.person ? detail.value.candidate_works || [] : [])
const collaborators = computed(() => verifiedCollaborators(profile.value, people.value, index.value?.coauthorships || []))
const influenceRecords = computed<any[]>(() => detail.value?.slug === state.value.person ? detail.value.influence_evidence || [] : [])
const gapLabels: Record<string, string> = {
  contribution_roles_not_inferred: '贡献角色仅按官方声明登记，不从作者顺序推断。',
  person_identity_unresolved_not_in_verified_statistics: '身份尚有同名冲突，不进入已核验个人统计。',
  profile_verified_but_no_verified_authorship: '已登记身份线索，具体作品归属仍待核验。',
  same_name_candidate_works_not_counted: '同名候选单独保留，不计已核验参与。',
  historical_author_version_unavailable_for_some_verified_works: '部分已核验作品缺少可用的历史版本署名；官网关系与版本证据分别保存。',
  citations_not_fully_measured: '引用尚未在同一来源、同一日期完成窗口内作品全覆盖。',
  adoption_not_measured: '独立采用尚无完整测量，不解释为零。',
}
const roleLabels: Record<string, string> = { equal_contribution: '共同贡献', corresponding_author: '通讯作者', project_lead: '项目负责人', equal_advising: '共同指导', supervision: '研究指导', writing: '论文写作' }
const influenceLabels: Record<string, string> = { citation_count: '引用快照', independent_adoption: '独立采用', independent_replication: '独立复现' }
const gapText = (gap: any) => typeof gap === 'string' ? gapLabels[gap] || gap : gap.message || gap.reason || ''
const peerText = (work: any): string => work.validation_eligible === false ? '结果不作当前验证' : work.strict_peer_reviewed ? '本时点已有正式评审证据' : (work.manifestations || []).some((row: any) => row.peer_reviewed) ? '评审已登记，日期或版本仍待核验' : '尚未登记可核验的正式评审'
const lenses = [
  { key: 'contribution', title: '方向内持续贡献', note: '先看已核实的作品参与与持续月份。独立项目线仍需逐项核验，不把论文数当项目数。' },
  { key: 'impact', title: '成果外部影响', note: '引用、独立采用和复现分开核验；尚未采集不是零影响，当前不据缺失指标排序。' },
  { key: 'recent', title: '近期研究变化', note: '比较最近三个月与此前三个月的已核验公开工作数；样本变化不直接命名为上升或降温。' },
  { key: 'roles', title: '关键成果贡献者', note: '逐篇查看官方贡献证据；个人官网职务、首位署名和论文主导贡献分别处理。' },
]
const lens = computed(() => lenses.find(item => item.key === state.value.lens) || lenses[0])
const period = computed(() => months.value.length ? `${months.value[0]}—${months.value.at(-1)}` : '最近 12 个完整月')
const summary = (person: any) => activitySummary(person, months.value)
const personHighlights = (person: any) => highlights.value[person.person_id] || []
const directionHighlights = (person: any) => personHighlights(person).filter((work: any) => !state.value.direction || work.primary_direction === state.value.direction)
const cardWork = (work: any) => ({ ...(personHighlights(profile.value).find((row: any) => row.work_id === work.work_id) || {}), ...work,
  output_types: (work.manifestations || []).map((row: any) => row.kind) })
const workUrl = (ids: string[]) => withBase(`/database/?${new URLSearchParams({ ids: [...new Set(ids)].join(','), relevance: 'all' })}`)
const singleWorkUrl = (id: string) => withBase(`/database/?${new URLSearchParams({ work: id, relevance: 'all' })}`)
const profileHref = (slug: string) => peopleUrl(withBase('/organizations/people/'), { ...state.value, person: slug })
const publicUrl = (value: any): string | undefined => typeof value === 'string' && /^https?:\/\//i.test(value) ? value : undefined
const profileLinks = (person: any): any[] => (person?.official_profiles || []).map((row: any) => typeof row === 'string' ? { url: row, label: '官方主页' } : row).filter((row: any) => publicUrl(row.url))
const identityText = (person: any) => person.identity_status === 'profile_verified' ? '个人主页已核验' : '身份待补充核验'
const personOrganization = (person: any) => [...new Set((person.official_roles || []).map((role: any) => role.organization_name).filter(Boolean))].slice(0, 2).join(' · ')
const shortDirections: Record<string, string> = { D1: '基础模型', D2: '规划与记忆', D3: '世界模型', D4: '灵巧操作', D5: '全身控制', D6: '导航与移动', D7: '人机协作', D8: '策略学习', D9: '数据与人类视频', D10: '仿真与迁移', D11: '空间感知', D12: '评测与安全', D13: '持续学习', D14: '多机器人', D15: '触觉与力觉' }
const evidenceLinks = (work: any): any[] => {
  const raw = work.authorship_evidence || []
  return (Array.isArray(raw) ? raw : raw.evidence || []).flatMap((row: any) => Array.isArray(row.evidence) ? row.evidence : [row]).filter((row: any) => publicUrl(row.url || row.source_url))
}
const changeLens = (value: string) => { state.value.lens = value; commit() }
const commit = (replace = false, resetStream = true) => {
  if (resetStream && streamKey.value !== peopleStreamKey(peopleStateFromUrl(window.location.href))) visibleCount.value = PEOPLE_BATCH_SIZE
  const target = peopleUrl(window.location.href, state.value)
  if (target === window.location.pathname + window.location.search + window.location.hash) return
  window.history[replace ? 'replaceState' : 'pushState'](window.history.state, '', target)
}
const loadDetail = async (slug: string, focus = false) => {
  if (detail.value?.slug !== slug) workScope.value = 'window'
  const request = ++detailRequest
  detail.value = null
  detailError.value = ''
  if (!slug || !people.value.some(person => person.slug === slug)) { detailLoading.value = false; return }
  detailLoading.value = true
  try {
    const response = await fetch(withBase(`/api/v1/people/${encodeURIComponent(slug)}.json`))
    if (!response.ok) throw new Error('person unavailable')
    const value = await response.json()
    if (disposed || request !== detailRequest) return
    const normalized = value.person ? { ...value.person, ...value } : value
    if (!personDetailMatchesIndex(normalized, index.value, slug)) {
      detailError.value = '索引与详情来自不同数据版本，已停止混合展示。请重新读取人物数据。'
      return
    }
    detail.value = normalized
    if (focus) {
      await nextTick()
      window.requestAnimationFrame(() => {
        if (!disposed && request === detailRequest && state.value.person === slug) {
          // Resolve the mounted heading after the async component/profile swap.
          // Keep keyboard users at the profile rather than the old result link.
          ;(heading.value || document.getElementById('person-heading'))?.focus()
        }
      })
    }
  } catch { if (!disposed && request === detailRequest) detailError.value = '人物详情暂时无法读取。索引仍保留；请重试，不使用其他同名人物代替。' }
  finally { if (!disposed && request === detailRequest) detailLoading.value = false }
}
const openPerson = (slug: string) => { if (!state.value.person) returnFocus = document.activeElement as HTMLElement; state.value.person = slug; commit(false, false); void loadDetail(slug, true) }
const closePerson = () => { personDialog.value?.close(); state.value.person = ''; detailRequest++; detail.value = null; detailLoading.value = false; detailError.value = ''; commit(false, false); void nextTick().then(() => { if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true }) }) }
const restore = () => {
  const next = peopleStateFromUrl(window.location.href)
  if (peopleStreamKey(next) !== streamKey.value) visibleCount.value = PEOPLE_BATCH_SIZE
  state.value = next
  void loadDetail(state.value.person)
}
const loadMorePeople = (focusNext = false) => {
  if (disposed || loading.value || profile.value || !hasMore.value) return
  const firstNewIndex = visible.value.length
  visibleCount.value = nextPeopleCount(visibleCount.value, filtered.value.length)
  if (focusNext) void nextTick().then(() => {
    peopleGrid.value?.querySelectorAll<HTMLAnchorElement>('article h3 a')[firstNewIndex]?.focus()
  })
}
const loadIndex = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(withBase('/api/v1/people/index.json'))
    if (!response.ok) throw new Error('index unavailable')
    const value = await response.json()
    if (disposed) return
    if (value.schema_version !== '1' || !Array.isArray(value.people)) throw new Error('index invalid')
    index.value = value
    void fetch(withBase('/api/v1/visual-feed/people-highlights.json')).then(async response => {
      if (!response.ok) return
      const result = await response.json()
      if (!disposed && result.dataset_version === index.value?.dataset_version) highlights.value = result.people || {}
    }).catch(() => { /* All verified source links remain available in details. */ })
    restore()
  } catch { if (!disposed) error.value = '人物数据暂时无法读取，请重试。已登记论文和组织档案仍可从原入口浏览。' }
  finally { if (!disposed) loading.value = false }
}

const timeline = useEChart(() => {
  const tokens = chartTokens()
  const values = new Map((profile.value?.monthly_activity || []).map((row: any) => [row.month, row.count]))
  return {
    animation: false, aria: { enabled: true, description: '已核验个人归属工作的首次公开月份，不是个人全部发文记录。' },
    tooltip: { trigger: 'axis', confine: true, backgroundColor: tokens.background, borderColor: tokens.divider, textStyle: { color: tokens.text } },
    grid: { left: 42, right: 16, top: 20, bottom: 42 },
    xAxis: { type: 'category', data: months.value, axisLabel: { color: tokens.muted, formatter: (value: string) => value.slice(2).replace('-', '.'), interval: 2, showMaxLabel: true }, axisTick: { show: false }, axisLine: { lineStyle: { color: tokens.divider } } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { color: tokens.muted }, splitLine: { lineStyle: { color: tokens.divider } } },
    series: [{ name: '已核验参与工作', type: 'bar', data: months.value.map(month => values.get(month) || 0), barMaxWidth: 30, itemStyle: { color: tokens.palette[0] } }],
  }
})
const network = useEChart(() => {
  const tokens = chartTokens()
  const related = collaborators.value.slice(0, 12)
  return {
    animation: false, aria: { enabled: true, description: '局部共同署名网络；只有双方都核实到同一工作的关系才显示。共同署名不代表独立采用或导师关系。' },
    tooltip: { confine: true, backgroundColor: tokens.background, borderColor: tokens.divider, textStyle: { color: tokens.text }, formatter: (item: any) => escapeChartText(item.data?.tooltip || item.name) },
    grid: { left: '24%', right: '32%', top: 38, bottom: 30 },
    xAxis: { type: 'value', min: -.15, max: 1.1, show: false },
    yAxis: { type: 'value', min: -.5, max: Math.max(related.length - .5, .5), show: false },
    series: [
      ...related.map((person: any, i: number) => ({ type: 'line', silent: true, symbol: 'none', data: [[0, (related.length - 1) / 2], [1, i]], lineStyle: { color: tokens.divider, width: 1 } })),
      { type: 'scatter', data: [{ id: profile.value?.person_id, name: profile.value?.name || '', value: [0, (related.length - 1) / 2] }], symbolSize: 22, itemStyle: { color: tokens.palette[0] }, label: { show: true, formatter: '{b}', position: 'top', color: tokens.text, fontSize: 12 } },
      { type: 'scatter', data: related.map((person: any, i: number) => ({ id: person.person_id, name: person.name, tooltip: `${person.name} · ${person.shared_work_ids.length} 项已核验共同署名`, value: [1, i] })), symbolSize: 13, itemStyle: { color: tokens.palette[1] }, label: { show: true, formatter: '{b}', position: 'right', color: tokens.text, fontSize: 12 } },
    ],
  }
}, chart => chart.on('click', (item: any) => { const person = people.value.find(row => row.person_id === item.data?.id); if (person && person.person_id !== profile.value?.person_id) openPerson(person.slug) }))

watch(profile, async value => { await nextTick(); if (disposed) return; if (value && personDialog.value && !personDialog.value.open) personDialog.value.showModal(); else if (!value) personDialog.value?.close() }, { flush: 'post' })
watch([streamEnd, streamKey, visibleCount, hasMore, loading, () => Boolean(profile.value)], () => {
  stopStreamObserver()
  if (!streamEnd.value || profile.value || !hasMore.value || loading.value) return
  stopStreamObserver = observePeopleEnd(streamEnd.value,
    () => !disposed && !loading.value && !profile.value && hasMore.value,
    () => loadMorePeople())
}, { flush: 'post' })
onMounted(() => { releasePageGuard = preservePeoplePage(router, window.location.pathname, restore); void loadIndex() })
onBeforeUnmount(() => { disposed = true; detailRequest++; stopStreamObserver(); personDialog.value?.close(); releasePageGuard() })
</script>

<template>
  <div class="v3-dashboard people-radar">
    <header class="v3-page-heading"><div><p class="v3-eyebrow">PEOPLE & RESEARCH</p><h1>人物与研究</h1><p>按研究方向看人，从代表作走进具体工作。</p></div></header>
    <p v-if="loading" role="status">正在读取人物与逐篇归属证据…</p>
    <p v-if="error" role="alert" class="v3-error">{{ error }} <button @click="loadIndex">重试</button></p>
    <template v-if="index">
      <div class="people-context"><span>{{ period }}</span><span>{{ index.counts.profile_verified_persons }} 位已核验 · {{ index.counts.candidate_identity_persons }} 位待消歧</span><a :href="withBase('/organizations/')">研究组 ↗</a><details><summary>核验口径与缺口</summary><p>人物主页核验不等于同名作品全部归属已核验。方向和数量仅根据逐篇核实的作品，不能作为完整学术影响力排名。未知指标不记成零。</p><a :href="withBase('/methods/people')">完整方法与来源 →</a></details></div>
      <details class="people-advanced" :open="state.lens !== 'contribution' || state.sort !== 'name'"><summary>观察维度与浏览顺序</summary>
      <div class="people-lenses" aria-label="人物观察视角"><button v-for="item in lenses" :key="item.key" type="button" :aria-pressed="state.lens === item.key" @click="changeLens(item.key)">{{ item.title }}</button></div>
      <p class="people-lens-note" aria-live="polite">{{ lens.note }}</p>
      <label class="people-sort-option">浏览顺序<select v-model="state.sort" @change="commit()"><option value="name">姓名 · 不排名</option><option value="verified">已核验参与工作数</option><option value="active">已核验活跃月份</option></select></label>
      </details>
      <div class="people-filters">
        <label>人物姓名<input v-model="state.q" type="search" placeholder="姓名或已登记别名" @input="commit(true)" /></label>
        <label>研究方向<select v-model="state.direction" @change="commit()"><option value="">全部方向</option><option v-for="(name, code) in directionNames" :key="code" :value="code">{{ code }} · {{ name }}</option></select></label>
      </div>
      <p class="people-scope-note">方向来自已核实作品；大图在档案内加载，未核实照片使用姓名缩写。</p>

      <dialog ref="personDialog" class="people-detail-dialog" aria-labelledby="person-heading" @cancel.prevent="closePerson" @click="($event.target === personDialog) && closePerson()">
      <section v-if="profile" class="people-profile">
        <button type="button" class="people-dialog-close" aria-label="关闭人物详情" autofocus @click="closePerson">关闭 ×</button>
        <div class="people-profile-identity"><SourceImage :entity-id="profile.person_id" :name="profile.name" portrait expanded source-note /><div><h2 id="person-heading" ref="heading" tabindex="-1">{{ profile.name }}<span v-if="profile.name_zh"> · {{ profile.name_zh }}</span></h2><p>{{ personOrganization(profile) || identityText(profile) }}</p></div></div>
        <p>{{ identityText(profile) }} · <span v-if="profile.identity_status === 'profile_verified'">{{ metricText(profile.metrics?.verified_works_window) }} 项窗口内工作已核实到本人</span><span v-else>未进入个人工作统计</span></p>
        <p v-if="profile.candidate_review?.checked" class="people-review-progress">本轮已核对 {{ profile.candidate_review.checked }} 项同名候选：确认 {{ profile.candidate_review.confirmed }} 项，仍待确认 {{ profile.candidate_review.unresolved }} 项（含窗口外作品）。<span v-if="profile.candidate_review.last_checked">核验于 {{ eventDate(profile.candidate_review.last_checked) }}。</span></p>
        <details v-if="profile.notes?.length" :open="profile.identity_status === 'candidate'" class="people-profile-notes"><summary>身份登记与早期核验备注</summary><p>保留初次登记时的说明；当前作品归属以逐项核验结果为准。</p><aside :class="profile.identity_status === 'candidate' ? 'v3-warning' : 'v3-muted'" role="note"><ul><li v-for="(note, i) in profile.notes" :key="i">{{ typeof note === 'string' ? note : note.statement || note.message }}</li></ul></aside></details>
        <div class="people-source-links"><a v-for="source in profileLinks(profile)" :key="source.url" :href="source.url" target="_blank" rel="noopener noreferrer">{{ source.label || '官方身份来源' }}<span v-if="source.observed_at"> · {{ eventDate(source.observed_at) }}</span></a><a :href="withBase(`/api/v1/people/${profile.slug}.json`)">公开人物数据</a></div>
        <details v-if="profile.official_roles?.length"><summary>官网身份与组织角色 · 不等于论文贡献</summary><ul><li v-for="(role, i) in profile.official_roles" :key="i">{{ role.organization_name || role.organization_id }} · {{ role.title }} <a :href="role.source_url" target="_blank" rel="noopener noreferrer">官方依据</a><span v-if="!role.valid_from && !role.valid_to"> · 历史任期未登记</span><span v-else> · {{ role.valid_from || '起始未知' }}—{{ role.valid_to || '结束未登记' }}</span></li></ul></details>
        <p v-if="detailLoading" role="status">正在读取逐篇作者与版本证据…</p>
        <p v-if="detailError" role="alert" class="v3-error">{{ detailError }} <button @click="loadIndex">重新读取人物数据</button></p>
        <details v-if="profile.identity_status === 'profile_verified'" class="people-profile-history" :open="state.lens === 'recent'"><summary>已核验研究的 12 个月轨迹</summary>
        <ChartFrame title="最近 12 个完整月 · 已核验参与" description="按研究首次公开月份计数；零表示没有登记到的核验关联，不代表本人没有发表。" :height="240" compact>
          <div :ref="timeline.element" role="img" :aria-label="`${profile.name}已核验参与工作月度时间线`" />
          <template #table><table><thead><tr><th>月份</th><th>已核验参与工作</th></tr></thead><tbody><tr v-for="row in profile.monthly_activity || []" :key="row.month"><th>{{ row.month }}</th><td>{{ row.count }}</td></tr></tbody></table></template>
        </ChartFrame>
        </details>
        <p v-else class="v3-warning">身份尚未唯一确认，暂不计算个人活动时间线。</p>
        <section class="v3-analysis-section"><header><h3>已核验署名作品</h3><p>图片与标题直达原文；署名确认不等于贡献角色或研究结论已获验证。</p><label class="people-work-scope">展示范围<select v-model="workScope"><option value="window">近 12 个月已纳入研究 · {{ windowVerifiedCount }} 项</option><option value="all">全部已核验署名 · {{ allVerifiedWorks.length }} 项</option></select></label></header>
          <article v-for="work in verifiedWorks" :key="work.work_id" class="people-work">
            <ResearchStatusNotice v-if="work.research_status" :value="work.research_status" :context="`最新状态截至 ${eventDate(work.research_status.as_of || detail.research_status_as_of)}；保留历史参与，受阻断的结果不取得当前验证加分。`" />
            <ResearchCard :work="cardWork(work)" compact />
            <details class="person-work-provenance" :open="state.lens === 'roles'"><summary>作者关系、角色与版本</summary>
            <p>{{ eventDate(work.first_public_date, work.first_public_date_precision) }} · {{ work.primary_direction || '待分类' }} · {{ work.evidence_grade || '证据待核验' }} · {{ peerText(work) }}</p>
            <p class="v3-muted">研究证据截至 {{ eventDate(work.historical_evidence_as_of || work.evidence_as_of) }}；后续状态单独核验。{{ work.in_complete_window ? '计入本次完整月窗口' : '窗口外作品，仅作背景' }}。</p>
            <div class="people-source-links"><a v-if="publicUrl(work.url)" :href="work.url" target="_blank" rel="noopener noreferrer">作品原文</a><a v-for="(proof, i) in evidenceLinks(work)" :key="i" :href="proof.url || proof.source_url" target="_blank" rel="noopener noreferrer">个人归属依据 {{ i + 1 }}</a></div>
            <p v-if="!work.roles?.length" class="v3-muted">具体贡献角色尚未核验；不根据首位或末位署名推断。</p>
            <ul v-else><li v-for="(role, i) in work.roles" :key="i">{{ role.label || roleLabels[role.role] || role.role || role.title }} · {{ role.scope === 'project' ? '项目声明' : '论文声明' }} <a v-if="role.source_url" :href="role.source_url" target="_blank" rel="noopener noreferrer">贡献依据</a><p v-if="role.statement">{{ role.statement }}</p></li></ul>
            <details><summary>署名版本与全部发表载体</summary><p>{{ work.version_authorship?.status || '版本署名待补' }}<span v-if="work.version_authorship?.version"> · {{ work.version_authorship.version }}</span> · 署名名单不作个人贡献排序</p><p class="people-byline">{{ (work.version_authorship?.authors || work.raw_authors || []).join(' · ') }}</p><ul><li v-for="manifestation in work.manifestations || []" :key="manifestation.manifestation_id"><a :href="manifestation.url" target="_blank" rel="noopener noreferrer">{{ manifestation.kind }} · {{ manifestation.venue || '' }} {{ manifestation.year || '' }}</a></li></ul></details>
            </details>
          </article>
          <p v-if="!detailLoading && !verifiedWorks.length" class="v3-empty">{{ allVerifiedWorks.length ? '本窗口暂无符合纳入条件的已核验作品；可切换为全部已核验署名。' : profile.identity_status === 'profile_verified' ? '目前已核验个人主页，具体作品归属仍待核验。' : '身份尚未唯一确认，具体作品关系保留待核验。' }}未将同名论文自动归入。</p>
        </section>
        <details v-if="candidates.length" class="people-candidates"><summary>{{ candidates.length }} 项归属仍待确认 · 查看逐项核验原因</summary><p>未确认项不计入个人研究统计；官网缺失或暂不可访问不代表作品不是本人所作。</p><ul><li v-for="work in candidates" :key="work.work_id"><a :href="singleWorkUrl(work.work_id)">{{ work.title }}</a><p>{{ work.authorship_evidence?.verification_audit?.reason || '尚未取得官方身份与具体作品的可靠对应证据。' }}</p><details v-if="work.authorship_evidence?.verification_audit?.checked_sources?.length"><summary>已检查来源 · {{ eventDate(work.authorship_evidence.verification_audit.checked_at) }}</summary><ul><li v-for="source in work.authorship_evidence.verification_audit.checked_sources" :key="source"><a :href="source" target="_blank" rel="noopener noreferrer">{{ source }}</a></li></ul></details></li></ul></details>
        <details v-if="collaborators.length" class="people-profile-network"><summary>共同署名关系 · {{ collaborators.length }} 位研究者</summary>
        <ChartFrame title="局部共同署名网络" description="双方均核实到同一工作才连线；不是独立采用、贡献比例或指导关系。图最多展开 12 位，表格保留全部。" :height="Math.max(250, Math.min(collaborators.length, 12) * 50)">
          <div :ref="network.element" class="v3-desktop-chart" role="img" :aria-label="`${profile.name}的已核验共同署名网络`" />
          <div class="v3-mobile-org-list"><a class="vp-raw" v-for="person in collaborators" :key="person.person_id" :href="profileHref(person.slug)" @click.prevent="openPerson(person.slug)">{{ person.name }} · {{ person.shared_work_ids.length }} 项共同工作</a></div>
          <template #table><table><thead><tr><th>共同署名者</th><th>双方已核验工作</th></tr></thead><tbody><tr v-for="person in collaborators" :key="person.person_id"><th><a class="vp-raw" :href="profileHref(person.slug)" @click.prevent="openPerson(person.slug)">{{ person.name }}</a></th><td><a :href="workUrl(person.shared_work_ids)">{{ person.shared_work_ids.length }} 项证据</a></td></tr></tbody></table></template>
        </ChartFrame>
        </details>
        <details class="v3-analysis-section" :open="state.lens === 'impact'"><summary>引用、外部影响与数据缺口</summary>
          <p>引用：{{ metricText(profile.metrics?.citations) }} · 已登记独立采用团队：{{ metricText(profile.metrics?.adoption) }} · 独立复现工作：{{ metricText(profile.metrics?.independent_replication_works_window) }} · 独立项目线：{{ metricText(profile.metrics?.independent_projects) }}</p>
          <p v-if="profile.metrics?.citation_coverage" class="v3-muted">引用测量覆盖 {{ profile.metrics.citation_coverage.measured_works }} / {{ profile.metrics.citation_coverage.required_works }} 项窗口内工作；仅同一来源、同一日期全部覆盖时汇总。汇总是逐作品引用数之和，不是去重后的引用论文数。<span v-if="profile.metrics.citation_coverage.provider">来源 {{ profile.metrics.citation_coverage.provider }} · 截至 {{ profile.metrics.citation_coverage.as_of }}</span></p>
          <article v-for="record in influenceRecords" :key="record.evidence_id" class="people-work"><h4>{{ influenceLabels[record.dimension] || record.dimension }} · {{ record.review_status === 'verified' ? '来源已核验' : '待核验，不计正式指标' }}</h4><p>{{ record.statement }}</p><p>测量截至 {{ record.as_of }}<span v-if="record.count !== undefined"> · {{ record.count }} 次引用（{{ record.provider }}）</span><span v-if="record.adopter_name"> · 采用方 {{ record.adopter_name }}</span></p><p v-if="record.independence_statement">独立性依据：{{ record.independence_statement }}</p><div class="people-source-links"><a :href="record.source_url" target="_blank" rel="noopener noreferrer">测量或采用来源</a><a v-if="record.independence_source_url" :href="record.independence_source_url" target="_blank" rel="noopener noreferrer">团队独立性来源</a><a :href="singleWorkUrl(record.canonical_work_id || record.work_id)">对应研究</a></div></article>
          <p v-if="!influenceRecords.length" class="v3-muted">尚未登记可展开的引用／采用／复现测量，不能解释为没有外部影响。</p>
          <ul><li v-for="(gap, i) in profile.data_gaps || []" :key="i">{{ gapText(gap) }}</li></ul>
        </details>
      </section>
      </dialog>
      <p v-if="!profile && state.person && !loading" role="status" class="v3-warning">此人物标识尚未登记。请从清单选择，不自动替换为相近姓名。</p>

      <section class="people-list" aria-label="人物候选与已核验覆盖"><header><h2>{{ state.lens === 'contribution' ? '相关研究者' : lens.title }}</h2><p>{{ filtered.length }} 位 · {{ state.direction ? directionNames[state.direction] : '全部方向' }}</p></header>
        <div ref="peopleGrid" class="people-grid"><article v-for="person in visible" :key="person.person_id">
          <div class="people-card-identity"><a class="vp-raw" :href="profileHref(person.slug)" :aria-label="`查看 ${person.name} 的代表作`" @click.prevent="openPerson(person.slug)"><SourceImage :entity-id="person.person_id" :name="person.name" portrait /></a><div><h3><a class="vp-raw" :href="profileHref(person.slug)" @click.prevent="openPerson(person.slug)">{{ person.name }}</a></h3><p v-if="person.name_zh" class="people-chinese-name">{{ person.name_zh }}</p><p class="people-affiliation" :title="personOrganization(person)">{{ personOrganization(person) || identityText(person) }}</p></div></div>
          <template v-if="person.identity_status !== 'profile_verified'"><p>姓名冲突待消歧，未进入个人统计。</p></template>
          <template v-else-if="state.lens === 'contribution'"><p class="people-card-stat">{{ state.direction ? '本方向已核实' : '已核实' }} <strong>{{ metricText(verifiedDirectionCount(person, state.direction)) }}</strong> 项作品 · {{ state.direction ? '全方向活跃' : '活跃' }} {{ summary(person).active }} 个月</p></template>
          <template v-else-if="state.lens === 'impact'"><p>引用：{{ metricText(person.metrics?.citations) }}</p><p>独立采用：{{ metricText(person.metrics?.adoption) }}</p><p class="v3-muted">不以未覆盖值判定影响力高低。</p></template>
          <template v-else-if="state.lens === 'recent'"><p>近三月 <strong>{{ summary(person).recent }}</strong> 项 · 此前三月 {{ summary(person).prior }} 项</p><p class="v3-muted">已核验作品，全方向口径；不是增长趋势评级。</p></template>
          <template v-else><p>有贡献声明的工作：{{ metricText(person.metrics?.role_verified_work_count) }}</p><p class="v3-muted">展开逐篇来源；不由署名顺序推断主导。</p></template>
          <p class="people-directions"><span v-for="row in (person.directions || []).filter((row: any) => row.count > 0)" :key="row.code" :title="`${directionNames[row.code]} · ${row.count} 项已核实作品`">{{ shortDirections[row.code] || row.code }}</span><span v-if="!(person.directions || []).some((row: any) => row.count > 0)">方向待核验</span></p>
          <p v-if="directionHighlights(person).length" class="people-card-work"><span>{{ state.direction ? '本方向代表作' : '代表作' }}</span><a :href="directionHighlights(person)[0].original_url" target="_blank" rel="noopener noreferrer">{{ directionHighlights(person)[0].title_zh || directionHighlights(person)[0].title }} ↗</a></p>
          <div class="people-card-footer"><a class="vp-raw" :href="profileHref(person.slug)" @click.prevent="openPerson(person.slug)">代表作与研究轨迹 →</a><span v-if="person.identity_status === 'candidate'">待消歧</span><span v-else>{{ metricText(person.metrics?.candidate_works_window) }} 项待核实</span></div>
        </article></div>
        <p v-if="!filtered.length" class="v3-empty">当前筛选下没有已登记人物。试试全部方向；未命中不表示这个方向没有重要研究者。</p>
        <div v-if="filtered.length" ref="streamEnd" class="people-stream-end">
          <p role="status" aria-live="polite">已展示 {{ visible.length }} / {{ filtered.length }} 位<span v-if="!hasMore"> · 已全部展示</span></p>
          <template v-if="hasMore"><span class="v3-muted">继续向下滚动，自动显示更多人物</span><button type="button" @click="loadMorePeople(true)">继续加载</button></template>
        </div>
      </section>
      <section class="v3-analysis-section people-team-note"><h2>个人未署名，团队仍保留</h2><p>Genesis、Generalist、Figure、Dyna、Sunday 等企业技术报告继续在组织雷达展示。没有个人署名的报告不会自动分配给创始人、CEO 或当前负责人。</p><a :href="withBase('/organizations/')">查看企业技术报告与团队来源覆盖</a></section>
      <details class="people-limitations"><summary>核验覆盖与方法边界</summary><ul><li v-for="(note, i) in index.limitations || []" :key="i">{{ note }}</li></ul><a :href="withBase('/api/v1/people/index.json')">下载人物索引与统计</a></details>
    </template>
  </div>
</template>

<style scoped>
.people-radar { padding-top: 24px; }
.people-detail-dialog { position: fixed; inset: 0 0 0 auto; width: min(800px, 100vw); max-width: 100vw; height: 100dvh; max-height: 100dvh; margin: 0; padding: 0; border: 0; background: var(--vp-c-bg); color: var(--vp-c-text-1); box-shadow: -16px 0 50px color-mix(in srgb, var(--vp-c-text-1) 12%, transparent); }
.people-detail-dialog::backdrop { background: color-mix(in srgb, var(--vp-c-text-1) 30%, transparent); }
.people-detail-dialog .people-profile { border-top: 0; margin: 0; padding: 24px 28px 48px; }
.people-dialog-close { position: sticky; top: 12px; z-index: 2; margin-left: auto; display: block; }
.people-detail-dialog summary { cursor: pointer; font-size: 14px; padding: 10px 0; }
.people-profile-history, .people-profile-network { margin: 18px 0; padding: 10px 0; border-top: 1px solid var(--vp-c-divider); }
.people-card-work { padding: 12px 0 0; border-top: 1px solid var(--vp-c-divider); display: grid; gap: 5px; }
.people-card-work > span { color: var(--vp-c-text-2); font-size: 12px; }
.people-card-work a { font-size: 14px; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.person-work-provenance { padding: 10px 4px; }
.people-context { display: flex; gap: 16px; align-items: baseline; flex-wrap: wrap; margin: 4px 0 20px; color: var(--vp-c-text-2); font-size: 14px; }
.people-context details { margin-left: auto; max-width: 520px; }
.people-context summary { cursor: pointer; }
.people-context p { margin: 8px 0; line-height: 1.6; }
.people-advanced { margin: 12px 0 16px; color: var(--vp-c-text-2); font-size: 14px; }
.people-advanced summary { cursor: pointer; }
.people-advanced .people-lenses { margin-top: 12px; }
.people-sort-option { display: flex; align-items: center; gap: 12px; margin: 10px 0; }
.people-sort-option select { border: 1px solid var(--vp-c-divider); padding: 6px 10px; border-radius: 6px; background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.people-scope-note { font-size: 13px; color: var(--vp-c-text-2); }
.people-radar .v3-page-heading { margin-bottom: 20px; }
.people-radar .v3-page-heading h1 { font-size: clamp(28px, 3.4vw, 42px); line-height: 1.2; margin: 8px 0 12px; }
.people-radar .v3-page-heading p:not(.v3-eyebrow) { font-size: 16px; line-height: 1.6; }
.people-lenses { display: flex; flex-wrap: wrap; gap: 8px; margin: 24px 0 12px; }
.people-lenses button, .people-stream-end button, .people-profile > button { padding: 10px 14px; border: 1px solid var(--vp-c-divider); border-radius: 6px; color: var(--vp-c-text-1); background: var(--vp-c-bg); }
.people-lenses button[aria-pressed='true'] { background: var(--vp-c-brand-soft); border-color: var(--vp-c-brand-1); }
.people-lens-note { color: var(--vp-c-text-2); font-size: 14px; line-height: 1.6; margin: 8px 0; }
.people-filters { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 14px 0; }
.people-filters label { display: grid; gap: 6px; font-size: 14px; }
.people-filters input, .people-filters select { padding: 10px; min-width: 0; width: 100%; border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-1); border-radius: 6px; font-size: 16px; }
.people-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.people-grid article { min-width: 0; padding: 22px; border: 1px solid var(--vp-c-divider); border-radius: 14px; background: var(--vp-c-bg); transition: border-color .15s, box-shadow .15s; }
.people-grid article:hover { border-color: var(--vp-c-brand-1); box-shadow: 0 8px 28px color-mix(in srgb, var(--vp-c-text-1) 5%, transparent); }
.people-card-identity, .people-profile-identity { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
.people-card-identity > div { min-width: 0; }
.people-card-identity h3 { font-size: 18px; line-height: 1.3; margin: 0 0 5px; }
.people-card-identity h3 a { color: var(--vp-c-text-1); }
.people-card-identity .people-affiliation { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; color: var(--vp-c-text-2); font-size: 13px; line-height: 1.4; }
.people-chinese-name { color: var(--vp-c-text-2); }
.people-profile-identity { margin-top: 18px; align-items: start; padding-bottom: 24px; }
.people-profile-identity :deep(.portrait) { width: 112px; height: 112px; }
.people-grid h3 { margin: 0 0 10px; }
.people-grid p { margin: 8px 0; font-size: 14px; }
.people-grid strong { font-size: 18px; font-weight: 600; }
.people-directions { display: flex; flex-wrap: wrap; gap: 6px 12px; }
.people-directions span { padding: 3px 8px; border-radius: 5px; background: var(--vp-c-bg-soft); font-size: 13px; }
.people-card-footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-top: 20px; padding-top: 14px; border-top: 1px solid var(--vp-c-divider); font-size: 14px; }
.people-card-footer span { color: var(--vp-c-text-2); font-size: 12px; }
.people-profile { margin: 30px 0 38px; padding-top: 24px; border-top: 2px solid var(--vp-c-brand-1); }
.people-profile h2 { margin: 18px 0; }
.people-source-links { display: flex; gap: 10px 20px; flex-wrap: wrap; margin: 10px 0 18px; }
.people-work { padding: 18px 0; border-bottom: 1px solid var(--vp-c-divider); }
.people-work h4 { margin: 0; font-size: 16px; }
.people-work details { margin-top: 12px; }
.people-byline { overflow-wrap: anywhere; }
.people-candidates, .people-limitations { margin: 24px 0; }
.people-profile li, .people-limitations li { margin: 8px 0; }
.people-stream-end { display: flex; flex-direction: column; gap: 10px; align-items: center; justify-content: center; min-height: 90px; margin: 24px 0; font-size: 14px; text-align: center; }
.people-stream-end p { margin: 0; color: var(--vp-c-text-2); }
.people-work-scope { display: grid; gap: 6px; margin: 12px 0; font-size: 14px; }
.people-work-scope select { max-width: 100%; padding: 9px; color: var(--vp-c-text-1); background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 6px; }
.people-review-progress { font-size: 14px; line-height: 1.7; padding: 12px; background: var(--vp-c-bg-soft); }
.people-list > header { margin: 24px 0 16px; }
.people-team-note { margin-top: 32px; }
.people-radar a { overflow-wrap: anywhere; }
.people-profile .v3-mobile-org-list a { display: block; padding: 12px 0; border-bottom: 1px solid var(--vp-c-divider); }
@media (max-width: 1000px) { .people-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 600px) { .people-grid, .people-filters { grid-template-columns: 1fr; } .people-lenses button { flex: 1 1 45%; min-height: 44px; } .people-lens-note { min-height: 0; } .people-source-links { flex-direction: column; } }
</style>
