<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'

const props = defineProps<{ edition: string }>()
const status = ref<any>(null)
const definition = ref<any>(null)
const changes = ref<any>(null)
const failure = ref('')
const changesFailure = ref('')
const selectedTrack = ref('main')
const selectedCategory = ref('all')
const page = ref(0)
const pageSize = 20
let request = 0
const countLabel = (value: number | null | undefined) => value === null || value === undefined ? '未知' : new Intl.NumberFormat('zh-CN').format(value)
const coverageLabels: Record<string, string> = { complete: '来源分页已对账', partial: '已取得部分证据', unknown: '尚无可用接收集合' }
const reasonLabels: Record<string, string> = {
  canonical_identity_unresolved: '接收记录尚未唯一绑定 canonical work',
  first_publication_date_unknown: '首次公开日期或精度未知',
  first_publication_lacks_dated_source: '首次公开日期尚缺直接来源',
  earlier_public_version_requires_date_review: '存在更早公开版本，需要复核首次公开日期',
  release_window_unknown: '放榜观察窗口缺少官方日期依据',
  observation_cutoff_unknown: '会议观察截止时间未知',
  individual_acceptance_date_unknown_or_conflicting: '逐篇接收日期未知或相互冲突',
  conference_track_unknown: '主会或 Workshop 归属尚未核实',
  public_date_not_yet_fully_observed: '日期精度尚不能确认在观察截止前公开',
  observation_precedes_release_window: '观察时间早于放榜窗口',
  first_discovery_after_observation_cutoff: '首次发现日期超出本次观察截止',
  first_discovery_or_prior_catalog_baseline_unknown: '缺少可信首次发现日期或放榜前目录基线',
  public_date_precision_overlaps_release_boundary: '粗粒度公开日期跨越放榜边界，不能猜测',
}
const activeTrack = computed(() => changes.value?.tracks?.find((row: any) => row.track === selectedTrack.value))
const filteredItems = computed(() => (activeTrack.value?.items || []).filter((row: any) => selectedCategory.value === 'all' || row.category === selectedCategory.value))
const pages = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / pageSize)))
const visibleItems = computed(() => filteredItems.value.slice(page.value * pageSize, (page.value + 1) * pageSize))
const exactIds = computed<string[]>(() => [...new Set<string>(filteredItems.value.map((row: any) => row.work_id).filter(Boolean))])
const databasePath = (ids: string[]) => withBase('/database/?' + new URLSearchParams({ ids: ids.join(','), relevance: 'all' }))
const mainSearch = computed(() => definition.value ? withBase('/database/?' + new URLSearchParams({ venue: definition.value.venue, year: String(definition.value.year), track: 'main_conference', publication_status: 'accepted_peer_reviewed', relevance: 'all' })) : '')
const categoryLabel = (category: string) => activeTrack.value?.categories?.find((row: any) => row.category === category)?.label || category
const discoveredLabel = (item: any) => item.discovery_basis === 'historical_baseline'
  ? `目录基线已收录（截至 ${eventDate(item.baseline_as_of)}）`
  : item.first_seen_at ? eventDate(item.first_seen_at) : '首次发现未核实'

async function load() {
  const current = ++request
  page.value = 0
  failure.value = ''
  changesFailure.value = ''
  status.value = definition.value = changes.value = null
  try {
    const [statusResponse, definitionResponse, changesResponse] = await Promise.all([
      fetch(withBase('/api/v1/conferences.json')),
      fetch(withBase('/api/v1/conference-editions.json')),
      fetch(withBase(`/api/v1/conference-changes/${encodeURIComponent(props.edition)}.json`)),
    ])
    if (!statusResponse.ok || !definitionResponse.ok) throw new Error('会议来源状态暂不可读取')
    const [statuses, definitions] = await Promise.all([statusResponse.json(), definitionResponse.json()])
    if (current !== request) return
    status.value = statuses.find((row: any) => row.edition_id === props.edition)
    definition.value = definitions.editions.find((row: any) => row.edition_id === props.edition)
    if (!status.value || !definition.value) throw new Error('尚未登记此会议版次的来源状态')
    if (changesResponse.ok) {
      const value = await changesResponse.json()
      if (current !== request) return
      if (value.edition_id !== props.edition || !Array.isArray(value.tracks)) throw new Error('会议变化数据与当前版次不匹配')
      changes.value = value
    } else {
      changesFailure.value = '放榜变化明细暂不可用，来源状态仍可查看；不能据此解释为零篇接收。'
    }
  } catch (error) {
    if (current === request) failure.value = error instanceof Error ? error.message : '加载失败'
  }
}
watch([selectedTrack, selectedCategory], () => { page.value = 0 })
watch(() => props.edition, load)
onMounted(load)
onBeforeUnmount(() => { request++ })
</script>

<template>
  <section class="v3-analysis-section conference-radar" aria-label="会议接收与放榜变化">
    <p v-if="failure" role="alert">{{ failure }} <button type="button" @click="load">重新读取</button></p>
    <template v-if="status && definition">
      <h2>{{ definition.venue }} {{ definition.year }}：放榜改变了什么</h2>
      <p v-if="!status.complete" class="conference-warning" role="status">名单覆盖尚未完成。{{ status.status === 'access_blocked' ? '官方论文接口要求访问验证，已核实的旧记录继续保留。' : '当前来源仅为部分覆盖。' }}读取受限不是接收零篇，不能据此推算全会研究分布。</p>
      <p v-else>此来源公开接收记录的分页采集与对账已完成；逐项身份、日期和研究相关性仍各自核验。</p>
      <dl class="conference-status">
        <div><dt>来源核验时间</dt><dd>{{ eventDate(status.checked_at) }}</dd></div>
        <div><dt>官方公布总量</dt><dd>{{ status.expected_count ?? '尚未取得可独立核验的总量' }}</dd></div>
        <div><dt>本次取得的记录</dt><dd>{{ !status.complete && !status.fetched_count ? '未取得可用记录' : `${status.fetched_count} 条采集记录（不是 canonical work 数）` }}</dd></div>
      </dl>
      <p>接收是一条新的验证事件，不是重新发表一篇新研究。例如五月公开的预印本九月获接收，五月新 work 数不变，九月增加接收事件。没有可信首次发现记录或历史目录基线时，不猜测它早已被本雷达收录。</p>
      <p class="conference-links"><a :href="definition.official_url" target="_blank" rel="noreferrer">会议官网</a><a :href="`https://openreview.net/group?id=${encodeURIComponent(definition.openreview_group_id)}`" target="_blank" rel="noreferrer">官方 OpenReview</a><a :href="definition.notification_date_source" target="_blank" rel="noreferrer">放榜日程来源</a><a :href="mainSearch">检索已入库的主会接收版本</a></p>
    </template>
    <p v-else-if="!failure" role="status">正在读取会议来源状态……</p>
    <p v-if="changesFailure" role="status">{{ changesFailure }}</p>

    <section v-if="changes && activeTrack" class="conference-change-panel" aria-label="放榜变化分流">
      <header>
        <div><h3>研究首次出现，与后来获得的验证</h3><p>放榜窗口始于 {{ eventDate(changes.release_window.from) }}；观察截至 {{ eventDate(changes.observation_as_of) }}。全会通知日不代替逐篇接收日期。</p></div>
        <label>会议轨道<select v-model="selectedTrack"><option v-for="track in changes.tracks" :key="track.track" :value="track.track">{{ track.label }} · {{ coverageLabels[track.coverage_status] }}</option></select></label>
      </header>
      <p class="conference-sample-note" role="status">{{ coverageLabels[activeTrack.coverage_status] }}。下列数字{{ activeTrack.coverage_status === 'complete' ? '按已对账来源中的唯一 work 和接收事件分别计算' : '只描述已取得样本；未知不填零，不显示全会份额' }}。主会与 Workshop 不混算，接收不自动改变相关性或证据成熟度。</p>
      <div class="conference-counts">
        <div><strong>{{ countLabel(activeTrack.display_work_count) }}</strong><span>已唯一定位的 work</span></div>
        <div><strong>{{ countLabel(activeTrack.display_event_count) }}</strong><span>官方接收事件</span></div>
        <div><strong>{{ activeTrack.unresolved_identity_events || activeTrack.display_event_count !== null ? countLabel(activeTrack.unresolved_identity_events) : '未知' }}</strong><span>身份未解析的接收事件</span></div>
      </div>
      <div class="conference-category-grid" role="group" aria-label="按放榜变化分类筛选">
        <button v-for="category in activeTrack.categories" :key="category.category" type="button" :aria-pressed="selectedCategory === category.category" @click="selectedCategory = selectedCategory === category.category ? 'all' : category.category">
          <span>{{ category.label }}</span><strong>{{ countLabel(category.item_count) }}</strong><small>{{ category.item_count === null ? '覆盖未知' : `${category.event_count} 个接收事件；这是样本记录分组` }}</small>
        </button>
      </div>
      <div class="conference-toolbar">
        <button type="button" :disabled="selectedCategory === 'all'" @click="selectedCategory = 'all'">查看全部分组</button>
        <a v-if="exactIds.length" :href="databasePath(exactIds)">展开此集合的 {{ exactIds.length }} 项全部研究</a>
        <a :href="withBase(`/api/v1/conference-changes/${encodeURIComponent(edition)}.json`)">下载完整分类与来源 JSON</a>
      </div>

      <p v-if="!filteredItems.length" class="conference-empty">{{ activeTrack.coverage_status === 'unknown' ? '还没有足够的公开接收证据形成这张分流表。来源可访问后仍需按原始日期和身份核验，不使用空名单表示零篇。' : '已取得样本中暂无此类记录；不是对未取得记录的判断。' }}</p>
      <div v-else class="conference-table-wrap" tabindex="0" aria-label="放榜变化明细，可横向滚动">
        <table>
          <caption>{{ activeTrack.label }} · {{ selectedCategory === 'all' ? '全部分组' : categoryLabel(selectedCategory) }} · 每页 {{ pageSize }} 条</caption>
          <thead><tr><th>研究与分组</th><th>首次公开</th><th>首次发现 / 基线</th><th>接收</th><th>事件与证据</th></tr></thead>
          <tbody><tr v-for="item in visibleItems" :key="item.item_id">
            <td><a v-if="item.database_path" :href="withBase(item.database_path)">{{ item.title }}</a><strong v-else>{{ item.title }}</strong><p>{{ categoryLabel(item.category) }}</p><small>相关性：{{ item.relevance }}</small><ul v-if="item.reasons.length"><li v-for="reason in item.reasons" :key="reason">{{ reasonLabels[reason] || reason }}</li></ul></td>
            <td>{{ eventDate(item.first_public_date, item.first_public_date_precision) }}</td>
            <td>{{ discoveredLabel(item) }}</td>
            <td>{{ eventDate(item.accepted_at, item.accepted_date_precision) }}</td>
            <td>{{ item.event_count }} 个事件<p v-for="url in item.official_urls" :key="url"><a :href="url" target="_blank" rel="noreferrer">官方接收记录</a></p><p v-for="url in item.public_source_urls" :key="url"><a :href="url" target="_blank" rel="noreferrer">首发日期来源</a></p></td>
          </tr></tbody>
        </table>
      </div>
      <div class="conference-mobile-cards">
        <article v-for="item in visibleItems" :key="item.item_id">
          <p>{{ categoryLabel(item.category) }} · {{ item.event_count }} 个接收事件</p>
          <h4><a v-if="item.database_path" :href="withBase(item.database_path)">{{ item.title }}</a><span v-else>{{ item.title }}</span></h4>
          <dl><div><dt>首次公开</dt><dd>{{ eventDate(item.first_public_date, item.first_public_date_precision) }}</dd></div><div><dt>首次发现 / 基线</dt><dd>{{ discoveredLabel(item) }}</dd></div><div><dt>接收日期</dt><dd>{{ eventDate(item.accepted_at, item.accepted_date_precision) }}</dd></div></dl>
          <ul v-if="item.reasons.length"><li v-for="reason in item.reasons" :key="reason">{{ reasonLabels[reason] || reason }}</li></ul>
          <p>相关性：{{ item.relevance }}；不因接收自动升级。</p>
          <p class="conference-links"><a v-for="url in item.official_urls" :key="url" :href="url" target="_blank" rel="noreferrer">官方接收</a><a v-for="url in item.public_source_urls" :key="url" :href="url" target="_blank" rel="noreferrer">首发来源</a></p>
        </article>
      </div>
      <nav v-if="filteredItems.length" class="conference-pagination" aria-label="放榜变化分页"><button type="button" :disabled="page === 0" @click="page--">上一页</button><span aria-live="polite">第 {{ page + 1 }} / {{ pages }} 页 · 共 {{ filteredItems.length }} 条样本</span><button type="button" :disabled="page + 1 >= pages" @click="page++">下一页</button></nav>
      <p v-if="changes.acceptance_review_queue.length" class="conference-warning">另有 {{ changes.acceptance_review_queue.length }} 条记录尚未满足官方接收证据要求或不在观察截止内，保留于下载文件的复核队列，不计入上方接收事件。</p>
      <p class="conference-sample-note">同一 forum 的重复采集只计一次接收事件；同一 work 可对应多个官方事件。四类分组用于解释发现与验证，不是论文质量排名，也不是研究组或方向的录取率。</p>
    </section>
  </section>
</template>

<style scoped>
.conference-radar { min-width: 0; }
.conference-radar :is(a, p, li, dd, td, th, h3, h4) { overflow-wrap: anywhere; }
.conference-radar button, .conference-radar select { min-height: 44px; padding: 8px 12px; border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.conference-radar button { cursor: pointer; }
.conference-radar button:disabled { opacity: .5; cursor: default; }
.conference-radar :is(button, select, a, [tabindex]):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.conference-warning { padding: 12px 16px; border-left: 3px solid var(--radar-series-4); background: var(--radar-surface); }
.conference-status { display: grid; gap: 12px; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 20px 0; }
.conference-status > div { min-width: 0; }
.conference-status dt, .conference-mobile-cards dt { color: var(--vp-c-text-2); font-size: .78rem; }
.conference-status dd { margin: 6px 0 0; font-size: .86rem; }
.conference-links { display: flex; flex-wrap: wrap; gap: 10px 18px; font-size: .82rem; }
.conference-change-panel { margin-top: 32px; }
.conference-change-panel > header { display: flex; justify-content: space-between; gap: 20px; align-items: end; }
.conference-change-panel header h3 { margin: 0; }
.conference-change-panel header p, .conference-sample-note { font-size: .83rem; line-height: 1.75; color: var(--vp-c-text-2); }
.conference-change-panel header > div { min-width: 0; }
.conference-change-panel header label { display: grid; gap: 6px; min-width: 0; font-size: .78rem; }
.conference-change-panel select { width: 100%; max-width: 100%; min-width: 0; }
.conference-counts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; padding: 16px 0; border-block: 1px solid var(--vp-c-divider); }
.conference-counts strong, .conference-counts span { display: block; }
.conference-counts strong { font-size: 1.55rem; font-weight: 550; }
.conference-counts span { margin-top: 6px; font-size: .78rem; color: var(--vp-c-text-2); }
.conference-category-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 20px 0; }
.conference-category-grid button { display: flex; flex-direction: column; align-items: start; text-align: left; gap: 10px; padding: 15px; }
.conference-category-grid button[aria-pressed="true"] { border-color: var(--vp-c-brand-1); box-shadow: inset 0 0 0 1px var(--vp-c-brand-1); }
.conference-category-grid span { font-size: .84rem; }
.conference-category-grid strong { font-size: 1.35rem; }
.conference-category-grid small { font-size: .72rem; line-height: 1.6; color: var(--vp-c-text-2); }
.conference-toolbar, .conference-pagination { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 18px; margin: 18px 0; font-size: .8rem; }
.conference-table-wrap { overflow-x: auto; max-width: 100%; }
.conference-table-wrap table { width: 100%; border-collapse: collapse; font-size: .78rem; }
.conference-table-wrap caption { text-align: left; margin: 8px 0; color: var(--vp-c-text-2); }
.conference-table-wrap th, .conference-table-wrap td { text-align: left; vertical-align: top; padding: 12px; border-bottom: 1px solid var(--vp-c-divider); }
.conference-table-wrap td:first-child { min-width: 220px; width: 35%; }
.conference-table-wrap p { margin: 6px 0; }
.conference-table-wrap ul { padding-left: 16px; font-size: .73rem; }
.conference-mobile-cards { display: none; }
.conference-empty { padding: 24px 0; color: var(--vp-c-text-2); }
@media (max-width: 1023px) {
  .conference-category-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 639px) {
  .conference-status { grid-template-columns: 1fr; }
  .conference-change-panel > header { flex-direction: column; align-items: stretch; }
  .conference-counts { gap: 10px; }
  .conference-counts strong { font-size: 1.3rem; }
  .conference-category-grid { grid-template-columns: 1fr; }
  .conference-table-wrap { display: none; }
  .conference-mobile-cards { display: grid; gap: 14px; }
  .conference-mobile-cards article { min-width: 0; border: 1px solid var(--vp-c-divider); border-radius: 8px; padding: 15px; }
  .conference-mobile-cards article > p, .conference-mobile-cards li { font-size: .77rem; line-height: 1.7; color: var(--vp-c-text-2); }
  .conference-mobile-cards h4 { margin: 8px 0; }
  .conference-mobile-cards dl > div { margin: 10px 0; }
  .conference-mobile-cards dd { margin: 4px 0 0; }
}
</style>
