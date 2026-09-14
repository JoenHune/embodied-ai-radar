<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

type Counts = Record<string, number | null>
type Group = { first_public_month?: string; primary_direction?: string; relevance_status?: string; all_works: Counts; included: Counts }
type CoverageSummary = { schema_version: string; dataset_version: string; dictionary_hash: string; dictionary_version?: string; data_through: string; all_works: Counts; included: Counts; by_direction: Group[]; by_month: Group[]; by_relevance: Group[]; downloads?: { coverage?: string } }
type Model = { dictionary_id: string; name: string; category: string; identity_level: string; evidence_status: string; usage_inference: string; metadata_work_count: number; body_work_count: number; candidate_work_count: number; included_candidate_work_count: number; metadata_work_ids: string[]; body_work_ids: string[]; work_ids: string[] }
type ModelIndex = { schema_version: string; dataset_version: string; dictionary_hash: string; models: Model[] }
type WorkCoverage = { work_id: string; metadata_hits: number; body_source_state: string; body_scan_status: string; body_hits: number; verified_count: number; full_text_scanned: boolean; partial_text_scanned: boolean; relevance: string }
const props = withDefaults(defineProps<{ compact?: boolean; expectedVersion?: string }>(), { compact: false })
const summary = ref<CoverageSummary | null>(null)
const loading = ref(true)
const error = ref('')
const cohort = ref<'all_works' | 'included'>('all_works')
const dimension = ref<'by_direction' | 'by_month' | 'by_relevance'>('by_direction')
const modelIndex = ref<ModelIndex | null>(null)
const modelsLoading = ref(false)
const modelsError = ref('')
const modelQuery = ref('')
const modelCategory = ref('')
const onlyMentions = ref(true)
const shownModels = ref(12)
const openModels = ref(new Set<string>())
const shownWorks = ref<Record<string, number>>({})
const workInput = ref('')
const workResult = ref<WorkCoverage | null>(null)
const workStatus = ref<'idle' | 'loading' | 'found' | 'missing' | 'error'>('idle')
const workError = ref('')
const queriedId = ref('')
const queryHeading = ref<HTMLElement | null>(null)
const titles = ref<Record<string, string>>({})
const titleErrors = ref<Record<string, string>>({})
const titleLoading = ref(new Set<string>())
const titleShards = new Map<string, Promise<Record<string, string>>>()
let manifestPromise: Promise<string> | undefined
let controller: AbortController | undefined
let workController: AbortController | undefined
let serial = 0
let workSerial = 0
let disposed = false
const prefix = props.compact ? 'hardware-coverage-compact' : 'hardware-coverage'
const categoryLabels: Record<string, string> = { robot_platform: '人形与移动机器人', robot_arm: '机械臂', dexterous_hand: '灵巧手', gripper: '夹爪', compute_platform: '算力平台', data_collection: '数采与遥操作', tactile_sensor: '触觉传感器', force_sensor: '力与力矩传感器', vision_sensor: '视觉与空间传感器' }
const relevanceLabels: Record<string, string> = { included: '已纳入', manual_review: '待人工复核', candidate: '候选', excluded: '已排除', unknown: '状态未明确' }
const directionLabels: Record<string, string> = { D1: '基础模型', D2: '规划与记忆', D3: '世界模型', D4: '灵巧操作', D5: '全身控制', D6: '导航与移动', D7: '人机协作', D8: '策略学习', D9: '数据与人类视频', D10: '仿真与迁移', D11: '空间感知', D12: '评测与安全', D13: '持续学习', D14: '多机器人', D15: '触觉与力觉', unassigned: '方向未归类' }
const sourceLabels: Record<string, string> = { full_text_available: '正文主文文本可用', partial_text: '仅取得部分正文文本', unavailable: '正文暂不可取得', blocked: '来源访问受限', identity_mismatch: '来源身份不一致', not_attempted: '尚未尝试取得正文' }
const scanLabels: Record<string, string> = { current_dictionary_scanned: '正文主文已按当前字典扫描', pending_current_dictionary_scan: '正文已取得，待当前字典扫描', partial_text_only_scanned: '仅扫描了部分正文文本', partial_text_pending_scan: '部分正文待扫描', source_failed: '来源获取失败，未完成正文扫描', not_attempted: '尚未进行正文扫描' }
const countFields = ['denominator', 'metadata_screened_work_count', 'metadata_missing_abstract_work_count', 'full_text_available_work_count', 'full_text_screened_current_dictionary_work_count', 'verified_relationship_work_count', 'verified_usage_relationship_count', 'full_text_not_attempted_work_count', 'full_text_failed_work_count', 'partial_text_available_work_count', 'full_text_available_pending_scan_work_count']
const isCount = (value: unknown): value is number => typeof value === 'number' && Number.isInteger(value) && value >= 0
const validCounts = (value: any) => value && countFields.every(field => isCount(value[field]))
const number = (value: unknown) => isCount(value) ? value.toLocaleString('zh-CN') : '未知'
const selected = computed(() => summary.value?.[cohort.value] || null)
const revisionMismatch = computed(() => Boolean(props.expectedVersion && summary.value && props.expectedVersion !== summary.value.dataset_version))
const cohortLabel = computed(() => cohort.value === 'all_works' ? '全库研究' : '已纳入研究')
const groups = computed(() => [...(summary.value?.[dimension.value] || [])].sort((a, b) => {
  if (dimension.value === 'by_month') return a.first_public_month === 'unknown' ? 1 : b.first_public_month === 'unknown' ? -1 : (b.first_public_month || '').localeCompare(a.first_public_month || '')
  if (dimension.value === 'by_direction') return (a.primary_direction || '').localeCompare(b.primary_direction || '', 'en', { numeric: true })
  const order = ['included', 'manual_review', 'candidate', 'excluded', 'unknown']
  return order.indexOf(a.relevance_status || 'unknown') - order.indexOf(b.relevance_status || 'unknown')
}))
const groupLabel = (group: Group) => dimension.value === 'by_month' ? group.first_public_month === 'unknown' ? '月份待核验' : group.first_public_month : dimension.value === 'by_relevance' ? relevanceLabels[group.relevance_status || 'unknown'] || group.relevance_status : `${group.primary_direction === 'unassigned' ? '' : group.primary_direction + ' · '}${directionLabels[group.primary_direction || 'unassigned'] || '未归类'}`
const searchKey = (value: string) => value.normalize('NFKC').toLocaleLowerCase().replace(/[\s_:\-/]+/g, '')
const filteredModels = computed(() => (modelIndex.value?.models || []).filter(model => (!onlyMentions.value || model.candidate_work_count > 0) && (!modelCategory.value || model.category === modelCategory.value) && (!modelQuery.value.trim() || searchKey(model.name + ' ' + model.dictionary_id).includes(searchKey(modelQuery.value.trim())))).sort((a, b) => b.candidate_work_count - a.candidate_work_count || a.name.localeCompare(b.name)))
const visibleModels = computed(() => filteredModels.value.slice(0, shownModels.value))
const workUrl = (id: string) => withBase(`/database/?${new URLSearchParams({ work: id, relevance: 'all' })}`)
const downloadHref = computed(() => withBase(summary.value?.downloads?.coverage?.startsWith('/downloads/') ? summary.value.downloads.coverage : '/downloads/equipment/hardware-coverage.jsonl.gz'))
const identityLabel = (value: string) => value === 'model_specified' ? '具体型号' : value === 'family_only' ? '系列 / 配置未明' : '型号未明确'
const visibleWorkIds = (model: Model) => model.work_ids.slice(0, shownWorks.value[model.dictionary_id] || 12)
const resetModels = () => { shownModels.value = 12 }
const toggleModel = (id: string) => { const next = new Set(openModels.value); next.has(id) ? next.delete(id) : next.add(id); openModels.value = next }
const moreWorks = (id: string) => { shownWorks.value = { ...shownWorks.value, [id]: (shownWorks.value[id] || 12) + 12 } }
const shardFor = async (id: string) => new Uint8Array(await crypto.subtle.digest('SHA-1', new TextEncoder().encode(id)))[0].toString(16).padStart(2, '0')
const matchingRevision = (value: any) => value?.schema_version === '1' && value.dataset_version === summary.value?.dataset_version && value.dictionary_hash === summary.value?.dictionary_hash

const loadModels = async () => {
  if (props.compact || !summary.value) return
  const request = serial
  modelsLoading.value = true
  modelsError.value = ''
  modelIndex.value = null
  try {
    const response = await fetch(withBase('/api/v1/equipment/coverage-model-candidates.json'), { signal: controller?.signal, cache: 'no-cache' })
    if (!response.ok) throw new Error('unavailable')
    const value = await response.json()
    if (disposed || request !== serial) return
    if (!matchingRevision(value)) throw new Error('version')
    if (!Array.isArray(value.models) || value.models.some((model: any) => !model.dictionary_id || !model.name || model.evidence_status !== 'unverified_mention' || model.usage_inference !== 'none' || ![model.metadata_work_count, model.body_work_count, model.candidate_work_count, model.included_candidate_work_count].every(isCount) || ![model.work_ids, model.metadata_work_ids, model.body_work_ids].every(ids => Array.isArray(ids) && ids.every(id => typeof id === 'string')))) throw new Error('invalid')
    modelIndex.value = value
  } catch (cause) {
    if (!disposed && request === serial) modelsError.value = cause instanceof Error && cause.message === 'version' ? '型号线索与覆盖统计的数据版本不一致，已停止混合展示。请重新读取覆盖数据。' : '型号线索暂时无法读取；线索数量未知，不显示为零。'
  } finally { if (!disposed && request === serial) modelsLoading.value = false }
}
const loadSummary = async () => {
  const request = ++serial
  controller?.abort()
  workController?.abort()
  workSerial++
  controller = new AbortController()
  loading.value = true
  error.value = ''
  summary.value = null
  modelIndex.value = null
  modelsError.value = ''
  workResult.value = null
  workStatus.value = 'idle'
  titles.value = {}
  titleErrors.value = {}
  titleLoading.value = new Set()
  titleShards.clear()
  manifestPromise = undefined
  try {
    const response = await fetch(withBase('/api/v1/equipment/coverage-summary.json'), { signal: controller.signal, cache: 'no-cache' })
    if (!response.ok) throw new Error('unavailable')
    const value = await response.json()
    if (disposed || request !== serial) return
    if (value.schema_version !== '1' || value.metadata_scope !== 'metadata_only' || !value.dataset_version || !value.dictionary_hash || !validCounts(value.all_works) || !validCounts(value.included) || !['by_direction', 'by_month', 'by_relevance'].every(key => Array.isArray(value[key]) && value[key].every((group: Group) => validCounts(group.all_works) && validCounts(group.included)))) throw new Error('invalid')
    summary.value = value
    if (!props.compact) void loadModels()
  } catch { if (!disposed && request === serial) error.value = '覆盖数据暂时无法读取，当前进度未知；读取失败不等于零覆盖。' }
  finally { if (!disposed && request === serial) loading.value = false }
}
const lookupWork = async () => {
  const id = workInput.value.trim()
  if (!summary.value) return
  const request = ++workSerial
  workController?.abort()
  workController = new AbortController()
  const signal = workController.signal
  workResult.value = null
  workError.value = ''
  queriedId.value = id
  if (!id || id.length > 300 || /\s/.test(id) || !id.includes(':')) { workStatus.value = 'error'; workError.value = '请输入完整且不含空格的研究ID，例如 arxiv:2609.07859。这里只查询精确ID，不猜测或合并别名。'; return }
  workStatus.value = 'loading'
  try {
    const shard = await shardFor(id)
    if (disposed || request !== workSerial) return
    const response = await fetch(withBase(`/api/v1/equipment/coverage/works/${shard}.json`), { signal, cache: 'no-cache' })
    if (!response.ok) throw new Error('unavailable')
    const value = await response.json()
    if (disposed || request !== workSerial) return
    if (!matchingRevision(value)) throw new Error('version')
    if (!value.by_work || typeof value.by_work !== 'object' || Array.isArray(value.by_work)) throw new Error('invalid')
    const row = value.by_work[id]
    if (!row) { workStatus.value = 'missing'; return }
    if (row.work_id !== id || ![row.metadata_hits, row.body_hits, row.verified_count].every(isCount) || typeof row.full_text_scanned !== 'boolean' || typeof row.partial_text_scanned !== 'boolean' || !Object.hasOwn(sourceLabels, row.body_source_state) || !Object.hasOwn(scanLabels, row.body_scan_status)) throw new Error('invalid')
    workResult.value = row
    workStatus.value = 'found'
  } catch (cause) {
    if (!disposed && request === workSerial) { workStatus.value = 'error'; workError.value = cause instanceof Error && cause.message === 'version' ? '此研究覆盖记录与统计摘要版本不一致，状态未知。请重新读取覆盖数据。' : '此研究的覆盖记录暂时无法读取，状态未知；未判定为没有使用设备。' }
  }
}
const inspectWork = async (id: string) => { workInput.value = id; await lookupWork(); await nextTick(); queryHeading.value?.focus() }
const loadTitle = async (id: string) => {
  if (!summary.value || titles.value[id] || titleLoading.value.has(id)) return
  const request = serial
  const version = summary.value.dataset_version
  titleLoading.value = new Set([...titleLoading.value, id])
  titleErrors.value = { ...titleErrors.value, [id]: '' }
  try {
    if (!manifestPromise) manifestPromise = fetch(withBase('/api/v1/catalog-manifest.json'), { signal: controller?.signal, cache: 'no-cache' }).then(async response => { if (!response.ok) throw new Error('unavailable'); return (await response.json()).dataset_version }).catch(cause => { manifestPromise = undefined; throw cause })
    if (await manifestPromise !== version) throw new Error('version')
    const shard = await shardFor(id)
    if (!titleShards.has(shard)) titleShards.set(shard, fetch(withBase(`/api/v1/works/${shard}.json`), { signal: controller?.signal, cache: 'no-cache' }).then(async response => {
      if (!response.ok) throw new Error('unavailable')
      const values = await response.json()
      if (!Array.isArray(values)) throw new Error('invalid')
      return Object.fromEntries(values.filter((row: any) => typeof row.work_id === 'string' && typeof row.title === 'string').map((row: any) => [row.work_id, row.title]))
    }).catch(cause => { titleShards.delete(shard); throw cause }))
    const title = (await titleShards.get(shard))?.[id]
    if (!title) throw new Error('missing')
    if (!disposed && request === serial) titles.value = { ...titles.value, [id]: title }
  } catch { if (!disposed && request === serial) titleErrors.value = { ...titleErrors.value, [id]: '标题暂不可读，保留精确ID链接。' } }
  finally { if (!disposed && request === serial) { const next = new Set(titleLoading.value); next.delete(id); titleLoading.value = next } }
}
onMounted(() => { void loadSummary() })
onBeforeUnmount(() => { disposed = true; serial++; workSerial++; controller?.abort(); workController?.abort() })
</script>

<template>
  <section class="hardware-coverage" :class="{ 'coverage-compact': props.compact, 'v3-dashboard': !props.compact }" :aria-labelledby="`${prefix}-heading`">
    <header class="coverage-heading"><div><p class="coverage-eyebrow">HARDWARE · REVIEW COVERAGE</p><component :is="props.compact ? 'h2' : 'h1'" :id="`${prefix}-heading`">全库硬件核验进度</component><p>先分清：哪些研究只筛过标题摘要，哪些取得了正文文本，哪些已有使用证据。</p></div><a v-if="props.compact" :href="withBase('/hardware/coverage')">查看全部覆盖记录 →</a></header>
    <p class="coverage-boundary">元数据筛查 ≠ 正文文本扫描 ≠ 设备使用关系核验。没有名称命中，不代表没有使用设备。</p>
    <p v-if="loading" class="coverage-status" role="status">正在读取全库覆盖状态…</p>
    <div v-else-if="error || revisionMismatch" class="coverage-error" role="alert"><strong>当前进度未知</strong><p>{{ revisionMismatch ? '设备频次与覆盖统计的数据版本不一致，已停止组合展示；请刷新页面重试。' : error }}</p><button type="button" @click="loadSummary">重新读取</button></div>
    <template v-else-if="summary">
      <div class="coverage-context"><span>截至 {{ summary.data_through }}</span><span>全库 {{ number(summary.all_works.denominator) }} 项 · 已纳入 {{ number(summary.included.denominator) }} 项</span><a :href="withBase('/methods/equipment-loco')">范围与方法 ↗</a></div>
      <div class="coverage-toggle" role="group" aria-label="覆盖统计范围"><button type="button" :aria-pressed="cohort === 'all_works'" @click="cohort = 'all_works'">全库 · 所有相关性状态</button><button type="button" :aria-pressed="cohort === 'included'" @click="cohort = 'included'">仅已纳入研究</button></div>
      <div class="coverage-metrics" aria-live="polite">
        <article><span>{{ cohortLabel }}分母</span><strong>{{ number(selected?.denominator) }}</strong><small>同一研究去重后只计一次</small></article>
        <article><span>标题 / 摘要已筛查</span><strong>{{ number(selected?.metadata_screened_work_count) }} <i>/ {{ number(selected?.denominator) }}</i></strong><small>仅元数据；{{ number(selected?.metadata_missing_abstract_work_count) }} 项缺少摘要</small></article>
        <article><span>正文主文文本可用</span><strong>{{ number(selected?.full_text_available_work_count) }} <i>/ {{ number(selected?.denominator) }}</i></strong><small>主文结构检查通过，非逐篇读完</small></article>
        <article><span>正文文本 · 当前字典已扫</span><strong>{{ number(selected?.full_text_screened_current_dictionary_work_count) }} <i>/ {{ number(selected?.denominator) }}</i></strong><small>正文与字典版本均须匹配</small></article>
        <article class="coverage-verified"><span>已有已核验使用关系的研究</span><strong>{{ number(selected?.verified_relationship_work_count) }} <i>/ {{ number(selected?.denominator) }}</i></strong><small>{{ number(selected?.verified_usage_relationship_count) }} 条使用关系；不代表整篇审完</small></article>
      </div>
      <p class="coverage-denominators">已核验关系涉及研究：全库 {{ number(summary.all_works.verified_relationship_work_count) }} / {{ number(summary.all_works.denominator) }}；已纳入 {{ number(summary.included.verified_relationship_work_count) }} / {{ number(summary.included.denominator) }}。两个分母不混用。</p>
      <p class="coverage-source-states" aria-live="polite">{{ cohortLabel }}：正文尚未尝试 {{ number(selected?.full_text_not_attempted_work_count) }} · 获取失败 / 受限 / 身份不符 {{ number(selected?.full_text_failed_work_count) }} · 仅部分正文可用 {{ number(selected?.partial_text_available_work_count) }} · 主文待当前字典扫描 {{ number(selected?.full_text_available_pending_scan_work_count) }}</p>
      <p class="coverage-limit">正文文本不包含图片、音视频或补充材料的人工检查；引用、仿真设备与真实使用仍须逐项区分。未核验不是“无硬件”。</p>

      <template v-if="!props.compact">
        <section class="coverage-section" :aria-labelledby="`${prefix}-groups`"><header><h2 :id="`${prefix}-groups`">分组覆盖记录</h2><p>以下表格使用上方选定的{{ cohortLabel }}分母。按主方向每项只计一次；月份按首次公开时间，日期不明不补猜。</p></header>
          <div class="coverage-toggle" role="group" aria-label="覆盖分组方式"><button type="button" :aria-pressed="dimension === 'by_direction'" @click="dimension = 'by_direction'">研究方向</button><button type="button" :aria-pressed="dimension === 'by_month'" @click="dimension = 'by_month'">首次公开月份</button><button type="button" :aria-pressed="dimension === 'by_relevance'" @click="dimension = 'by_relevance'">相关性状态</button></div>
          <div class="coverage-table-wrap" tabindex="0" aria-label="可横向滚动的分组覆盖表"><table class="coverage-table"><thead><tr><th scope="col">分组</th><th scope="col">研究分母</th><th scope="col">元数据已筛</th><th scope="col">主文文本可用</th><th scope="col">主文当前字典已扫</th><th scope="col">已核验使用研究</th><th scope="col">正文未尝试</th><th scope="col">获取失败</th></tr></thead><tbody><tr v-for="(group, i) in groups" :key="`${dimension}-${i}`"><th scope="row">{{ groupLabel(group) }}</th><td>{{ number(group[cohort].denominator) }}</td><td>{{ number(group[cohort].metadata_screened_work_count) }}</td><td>{{ number(group[cohort].full_text_available_work_count) }}</td><td>{{ number(group[cohort].full_text_screened_current_dictionary_work_count) }}</td><td>{{ number(group[cohort].verified_relationship_work_count) }}</td><td>{{ number(group[cohort].full_text_not_attempted_work_count) }}</td><td>{{ number(group[cohort].full_text_failed_work_count) }}</td></tr></tbody></table></div>
        </section>

        <section class="coverage-section coverage-lookup" :aria-labelledby="`${prefix}-query`"><h2 :id="`${prefix}-query`" ref="queryHeading" tabindex="-1">按研究ID查询覆盖状态</h2><p>精确查询一项记录，只读取对应分片，不下载整个研究库。</p><form @submit.prevent="lookupWork"><label :for="`${prefix}-work-id`">Canonical work ID</label><div class="coverage-query-controls"><input :id="`${prefix}-work-id`" v-model="workInput" type="search" maxlength="300" placeholder="例如 arxiv:2609.07859" autocomplete="off" spellcheck="false" /><button type="submit" :disabled="workStatus === 'loading'">查询状态</button></div></form>
          <p v-if="workStatus === 'loading'" role="status">正在读取该研究的覆盖记录…</p>
          <p v-if="workStatus === 'error'" role="alert" class="coverage-error">{{ workError }}</p>
          <p v-if="workStatus === 'missing'" role="status">本次覆盖记录中未找到精确ID「{{ queriedId }}」。这不表示论文不存在或未使用硬件；可在<a :href="workUrl(queriedId)">研究库检查标识符</a>。</p>
          <article v-if="workStatus === 'found' && workResult" class="coverage-work-result"><header><a :href="workUrl(workResult.work_id)">{{ titles[workResult.work_id] || workResult.work_id }}</a><span>{{ relevanceLabels[workResult.relevance] || workResult.relevance }}</span><button v-if="!titles[workResult.work_id]" type="button" :disabled="titleLoading.has(workResult.work_id)" @click="loadTitle(workResult.work_id)">{{ titleLoading.has(workResult.work_id) ? '读取标题…' : '按需读取标题' }}</button></header><p v-if="titleErrors[workResult.work_id]" class="coverage-muted">{{ titleErrors[workResult.work_id] }}</p><dl><div><dt>标题 / 摘要名称命中</dt><dd>{{ number(workResult.metadata_hits) }} 条 · 仅元数据线索</dd></div><div><dt>正文获取状态</dt><dd>{{ sourceLabels[workResult.body_source_state] }}</dd></div><div><dt>正文扫描状态</dt><dd>{{ scanLabels[workResult.body_scan_status] }}</dd></div><div><dt>正文名称命中</dt><dd v-if="workResult.full_text_scanned || workResult.partial_text_scanned">{{ number(workResult.body_hits) }} 条 · 仅当前已扫描文本的线索，未自动核验</dd><dd v-else>尚未完成正文文本扫描，命中数未知</dd></div><div><dt>已有已核验使用关系</dt><dd>{{ number(workResult.verified_count) }} 条<span v-if="workResult.verified_count === 0"> · 尚未建立，不等于没有使用</span></dd></div></dl></article>
        </section>

        <section class="coverage-section" :aria-labelledby="`${prefix}-models`"><header><h2 :id="`${prefix}-models`">设备名称线索 · 待逐篇核验</h2><p>本区保留全库候选出处，另列已纳入数量，不随上方统计范围隐藏其他记录。名称提及不是设备使用频次，不能直接作采购、部署或市场份额判断。</p></header>
          <p v-if="modelsLoading" role="status">正在读取全库型号线索…</p><div v-else-if="modelsError" class="coverage-error" role="alert"><p>{{ modelsError }}</p><button type="button" @click="loadModels">重试型号线索</button></div>
          <template v-else-if="modelIndex"><div class="coverage-model-filters"><label>搜索名称或字典ID<input v-model="modelQuery" type="search" maxlength="160" placeholder="Unitree G1、RTX 4090…" @input="resetModels" /></label><label>设备类别<select v-model="modelCategory" @change="resetModels"><option value="">全部类别</option><option v-for="(label, code) in categoryLabels" :key="code" :value="code">{{ label }}</option></select></label><label class="coverage-checkbox"><input v-model="onlyMentions" type="checkbox" @change="resetModels" />仅显示有名称线索的条目</label></div><p class="coverage-muted" aria-live="polite">{{ number(filteredModels.length) }} / {{ number(modelIndex.models.length) }} 个字典条目。按全库候选研究数排列，每项研究在一个条目下去重一次；不是已核验使用排名。</p>
            <div class="coverage-model-list"><article v-for="model in visibleModels" :key="model.dictionary_id" class="coverage-model"><header><div><h3>{{ model.name }}</h3><p>{{ categoryLabels[model.category] || model.category }} · {{ identityLabel(model.identity_level) }} · <strong class="coverage-candidate">未核验提及</strong></p></div><button type="button" :aria-expanded="openModels.has(model.dictionary_id)" @click="toggleModel(model.dictionary_id)">{{ openModels.has(model.dictionary_id) ? '收起出处' : `展开 ${number(model.candidate_work_count)} 项全库出处` }}</button></header><p class="coverage-model-counts">全库候选研究 {{ number(model.candidate_work_count) }} · 其中已纳入 {{ number(model.included_candidate_work_count) }} · 标题 / 摘要线索 {{ number(model.metadata_work_count) }} · 正文文本线索 {{ number(model.body_work_count) }}</p>
              <div v-if="openModels.has(model.dictionary_id)" class="coverage-model-sources"><p class="coverage-muted">以下均为全库名称候选；正文线索也可能来自部分正文、引用或仿真，须进入原文核对用途。</p><p v-if="!model.work_ids.length">当前字典未找到名称线索，不表示没有研究使用该设备。</p><ul v-else><li v-for="id in visibleWorkIds(model)" :key="id"><div><a :href="workUrl(id)">{{ titles[id] || id }}</a><small>{{ model.metadata_work_ids.includes(id) ? '标题 / 摘要' : '' }}{{ model.metadata_work_ids.includes(id) && model.body_work_ids.includes(id) ? ' + ' : '' }}{{ model.body_work_ids.includes(id) ? '正文文本' : '' }}</small></div><div class="coverage-source-actions"><button type="button" @click="inspectWork(id)">查询覆盖</button><button v-if="!titles[id]" type="button" :disabled="titleLoading.has(id)" @click="loadTitle(id)">{{ titleLoading.has(id) ? '读取中…' : '读取标题' }}</button></div><small v-if="titleErrors[id]">{{ titleErrors[id] }}</small></li></ul><button v-if="visibleWorkIds(model).length < model.work_ids.length" type="button" @click="moreWorks(model.dictionary_id)">再显示 12 项出处（已显示 {{ number(visibleWorkIds(model).length) }} / {{ number(model.work_ids.length) }}）</button></div>
            </article></div><p v-if="!filteredModels.length" role="status">此筛选条件下没有匹配的字典条目；不据此判断设备是否被使用。</p><button v-if="visibleModels.length < filteredModels.length" type="button" class="coverage-more" @click="shownModels += 12">再显示 12 个字典条目</button>
          </template>
        </section>
        <footer class="coverage-footer"><a :href="downloadHref" download>下载完整覆盖表（JSONL.GZ）</a><a :href="withBase('/api/v1/equipment/coverage-summary.json')">覆盖统计 JSON</a><a :href="withBase('/methods/equipment-loco')">方法与证据边界</a><a :href="withBase('/hardware/')">已核验使用关系 →</a><p>下载包含逐研究覆盖状态及来源/hash定位，不公开论文正文摘录或本机缓存路径。字典版本 {{ summary.dictionary_version || '未标注' }}；所有计数以当前数据版本为准。</p></footer>
      </template>
    </template>
  </section>
</template>

<style scoped>
.hardware-coverage { color: var(--vp-c-text-1); }
.coverage-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 20px; }
.coverage-heading h1, .coverage-heading h2 { margin: 3px 0 10px; padding: 0; border: 0; letter-spacing: -.025em; }
.coverage-heading h1 { font-size: clamp(26px, 3vw, 38px); line-height: 1.2; }
.coverage-heading p, .coverage-section header p { margin: 0; color: var(--vp-c-text-2); font-size: 14px; line-height: 1.65; }
.coverage-heading .coverage-eyebrow { font-size: 11px; font-weight: 650; letter-spacing: .12em; color: var(--vp-c-brand-1); }
.coverage-heading > a { white-space: nowrap; font-size: 13px; margin-top: 12px; }
.coverage-boundary { margin: 12px 0 18px; padding: 12px 15px; border-left: 3px solid var(--vp-c-warning-1); background: var(--vp-c-warning-soft); font-size: 14px; line-height: 1.6; border-radius: 0 8px 8px 0; }
.coverage-context, .coverage-source-states, .coverage-denominators, .coverage-limit, .coverage-muted { color: var(--vp-c-text-2); font-size: 12px; line-height: 1.7; }
.coverage-context { display: flex; flex-wrap: wrap; gap: 8px 20px; margin-bottom: 12px; }
.hardware-coverage button, .hardware-coverage input, .hardware-coverage select { border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); color: var(--vp-c-text-1); font: inherit; }
.hardware-coverage button { padding: 7px 11px; font-size: 12px; cursor: pointer; line-height: 1.5; }
.hardware-coverage button:hover { border-color: var(--vp-c-brand-1); }
.hardware-coverage button:disabled { cursor: progress; opacity: .6; }
.hardware-coverage :is(button, a, input, select, [tabindex]):focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 3px; }
.coverage-toggle { display: flex; flex-wrap: wrap; gap: 6px; margin: 13px 0; }
.coverage-toggle button[aria-pressed="true"] { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); background: var(--vp-c-brand-soft); }
.coverage-metrics { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; margin: 16px 0 12px; }
.coverage-metrics article { padding: 16px 13px; background: var(--vp-c-bg-soft); border: 1px solid var(--vp-c-divider); border-radius: 10px; min-width: 0; }
.coverage-metrics span, .coverage-metrics small { display: block; color: var(--vp-c-text-2); font-size: 11px; line-height: 1.6; }
.coverage-metrics strong { display: block; margin: 9px 0 7px; font-size: clamp(21px, 2.4vw, 30px); line-height: 1.2; letter-spacing: -.035em; font-variant-numeric: tabular-nums; }
.coverage-metrics i { font-size: 12px; font-weight: 400; font-style: normal; letter-spacing: 0; color: var(--vp-c-text-2); white-space: nowrap; }
.coverage-metrics .coverage-verified { border-color: var(--vp-c-brand-1); }
.coverage-metrics .coverage-verified strong { color: var(--vp-c-brand-1); }
.coverage-denominators { margin: 10px 0 6px; font-weight: 550; }
.coverage-source-states { margin: 6px 0; }
.coverage-limit { margin: 8px 0 0; }
.coverage-section { margin-top: 40px; padding-top: 25px; border-top: 1px solid var(--vp-c-divider); }
.coverage-section h2 { border: 0; margin: 0 0 9px; padding: 0; font-size: 22px; }
.coverage-table-wrap { overflow-x: auto; margin-top: 15px; border: 1px solid var(--vp-c-divider); border-radius: 8px; }
.coverage-table { display: table; width: 100%; margin: 0; border-collapse: collapse; font-size: 12px; line-height: 1.5; }
.coverage-table :is(th, td) { padding: 11px 12px; border: 0; border-bottom: 1px solid var(--vp-c-divider); text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.coverage-table th:first-child { text-align: left; }
.coverage-table thead { background: var(--vp-c-bg-soft); }
.coverage-table tbody tr:last-child :is(th, td) { border-bottom: 0; }
.coverage-lookup > p, .coverage-lookup label { font-size: 13px; color: var(--vp-c-text-2); }
.coverage-lookup label { display: block; margin-bottom: 6px; }
.coverage-query-controls { display: flex; gap: 8px; max-width: 650px; }
.coverage-query-controls input { min-width: 0; flex: 1; padding: 9px 11px; font-size: 14px; }
.coverage-work-result { margin-top: 16px; padding: 17px; border: 1px solid var(--vp-c-divider); border-radius: 10px; }
.coverage-work-result header { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; font-size: 13px; }
.coverage-work-result header > a { overflow-wrap: anywhere; }
.coverage-work-result header > span { color: var(--vp-c-text-2); }
.coverage-work-result dl { margin: 14px 0 0; display: grid; gap: 9px; font-size: 13px; }
.coverage-work-result dl > div { display: grid; grid-template-columns: 170px 1fr; gap: 10px; }
.coverage-work-result dt { color: var(--vp-c-text-2); }
.coverage-work-result dd { margin: 0; }
.coverage-model-filters { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 18px; align-items: flex-end; }
.coverage-model-filters > label { display: grid; gap: 5px; font-size: 12px; color: var(--vp-c-text-2); }
.coverage-model-filters input[type="search"], .coverage-model-filters select { padding: 8px 10px; min-width: 180px; font-size: 13px; }
.coverage-model-filters .coverage-checkbox { display: flex; gap: 7px; align-items: center; min-height: 37px; }
.coverage-checkbox input { accent-color: var(--vp-c-brand-1); }
.coverage-model-list { display: grid; gap: 12px; margin-top: 14px; }
.coverage-model { padding: 17px; border: 1px solid var(--vp-c-divider); border-radius: 10px; }
.coverage-model > header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.coverage-model h3 { margin: 0 0 6px; font-size: 16px; line-height: 1.4; }
.coverage-model header p { margin: 0; font-size: 12px; }
.coverage-model header button { flex-shrink: 0; }
.coverage-candidate { color: var(--vp-c-warning-1); font-weight: 500; }
.coverage-model-counts { font-size: 12px; color: var(--vp-c-text-2); margin: 12px 0 0; line-height: 1.7; }
.coverage-model-sources { margin-top: 15px; padding-top: 10px; border-top: 1px solid var(--vp-c-divider); font-size: 13px; }
.coverage-model-sources ul { margin: 10px 0; padding: 0; list-style: none; }
.coverage-model-sources li { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 8px 15px; padding: 10px 0; border-bottom: 1px solid var(--vp-c-divider); }
.coverage-model-sources li > div:first-child { flex: 1; min-width: 170px; overflow-wrap: anywhere; }
.coverage-model-sources li small { display: block; color: var(--vp-c-text-2); margin-top: 3px; }
.coverage-source-actions { display: flex; gap: 5px; }
.coverage-source-actions button { padding: 3px 7px; }
.coverage-more { margin-top: 18px; }
.coverage-footer { display: flex; flex-wrap: wrap; gap: 10px 22px; margin-top: 35px; padding-top: 20px; border-top: 1px solid var(--vp-c-divider); font-size: 13px; }
.coverage-footer p { flex-basis: 100%; color: var(--vp-c-text-2); font-size: 12px; line-height: 1.7; margin: 0; }
.coverage-error { margin: 15px 0; padding: 13px; border: 1px solid var(--vp-c-danger-1); background: var(--vp-c-danger-soft); border-radius: 8px; font-size: 13px; line-height: 1.7; }
.coverage-error p { margin: 5px 0 10px; }
.coverage-compact { padding: 22px; margin: 18px 0 30px; border: 1px solid var(--vp-c-divider); border-radius: 13px; }
.coverage-compact .coverage-heading h2 { font-size: 22px; }
.coverage-compact .coverage-heading { margin-bottom: 12px; }
@media (max-width: 1050px) { .coverage-metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 640px) { .coverage-heading { display: block; } .coverage-heading > a { display: inline-block; } .coverage-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } .coverage-metrics article:last-child { grid-column: span 2; } .coverage-compact { padding: 16px; } .coverage-work-result dl > div { grid-template-columns: 1fr; gap: 2px; } .coverage-model > header { display: block; } .coverage-model header button { margin-top: 12px; } .coverage-query-controls input { width: 100%; } .coverage-model-filters > label, .coverage-model-filters input[type="search"], .coverage-model-filters select { width: 100%; } }
</style>
