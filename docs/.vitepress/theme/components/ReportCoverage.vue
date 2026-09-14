<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'
const props = defineProps<{ organizationId?: string }>()
const coverage = ref<any>(null)
const error = ref('')
const scope = ref('priority')
const query = ref('')
const view = ref<'as_of' | 'current'>('as_of')
const selected = ref('')
const priority = ['org:genesis-ai', 'org:generalist-ai', 'org:figure-ai', 'org:dyna-robotics', 'org:sunday-robotics']
const strata: Record<string, string> = { included: '已纳入', candidate: '候选', review: '待复核', excluded: '已排除' }
const rows = computed<any[]>(() => (coverage.value?.organizations || []).filter((row: any) => {
  if (props.organizationId) return row.organization_id === props.organizationId
  const matches = scope.value === 'all' || scope.value === row.tier || (scope.value === 'roots' && row.is_root) || (scope.value === 'priority' && priority.includes(row.organization_id))
  return matches && `${row.name} ${row.slug}`.toLowerCase().includes(query.value.toLowerCase())
}).sort((a: any, b: any) => a.name.localeCompare(b.name, 'zh-CN')))
const selectedRow = computed(() => (coverage.value?.organizations || []).find((row: any) => row.organization_id === (props.organizationId || selected.value)))
const ratio = (row: any, key: string) => row.counts.report_canonical_count ? `${row.counts[`${key}_${view.value}`] || 0} / ${row.counts.report_canonical_count}` : '未登记'
const textStatus = (report: any) => {
  const value = report.text[view.value]
  return [value.report_excerpt_available && '历史短摘录', value.arxiv_abstract_available && '版本摘要'].filter(Boolean).join(' + ') || (value.status === 'retrospective_only' ? '晚于截止日' : value.status === 'conflicting_snapshots' ? '来源冲突' : '正文未补齐')
}
const workUrl = (id: string) => withBase(`/database/?work=${encodeURIComponent(id)}&relevance=all`)
const sync = () => {
  const url = new URL(location.href)
  for (const [key, value, fallback] of [['report_scope', scope.value, 'priority'], ['report_q', query.value, ''], ['report_view', view.value, 'as_of'], ['report_org', selected.value, '']]) {
    if (value === fallback) url.searchParams.delete(key); else url.searchParams.set(key, value)
  }
  if (url.href !== location.href) history.pushState({}, '', url)
}
const restore = () => {
  const params = new URLSearchParams(location.search)
  scope.value = ['priority', 'all', 'T0', 'T1', 'roots'].includes(params.get('report_scope') || '') ? params.get('report_scope')! : 'priority'
  query.value = params.get('report_q') || ''
  view.value = params.get('report_view') === 'current' ? 'current' : 'as_of'
  selected.value = params.get('report_org') || ''
}
const choose = (row: any) => { selected.value = row.organization_id; sync() }
const load = async () => {
  error.value = ''
  try {
    const response = await fetch(withBase('/api/v1/report-coverage.json'))
    if (!response.ok) throw new Error('Unavailable')
    coverage.value = await response.json()
  } catch { error.value = '报告覆盖数据暂时不可用，请重试。' }
}
onMounted(() => { restore(); window.addEventListener('popstate', restore); load() })
onBeforeUnmount(() => window.removeEventListener('popstate', restore))
</script>

<template>
  <section class="report-coverage" aria-label="技术报告覆盖矩阵">
    <header><p class="v3-eyebrow">REPORT COVERAGE</p><h2>关键报告，哪些已收录、哪些仍未读透</h2><p>按已登记报告逐项追踪，不把“有链接”当作“完成实验阅读”。母机构仅上卷有来源的子组报告，不改变论文归属。</p></header>
    <p v-if="error" role="alert">{{ error }} <button type="button" @click="load">重试</button></p><p v-else-if="!coverage" role="status">正在载入报告覆盖……</p>
    <template v-if="coverage">
      <div class="report-controls"><template v-if="!organizationId"><label>组织范围<select v-model="scope" @change="sync"><option value="priority">指定关键公司</option><option value="T0">全部 T0 核心</option><option value="T1">全部 T1 前沿</option><option value="roots">母机构 / 根实体</option><option value="all">全部矩阵节点</option></select></label><label>查找组织<input v-model="query" type="search" placeholder="公司或研究组名称" @input="sync"></label></template><label>正文与实验视角<select v-model="view" @change="sync"><option value="as_of">截至 {{ coverage.data_through }}</option><option value="current">最新登记观察 · {{ coverage.current_as_of }}</option></select></label></div>
      <p class="report-note">全球去重 {{ coverage.global_summary.report_canonical_count }} 项报告、{{ coverage.global_summary.report_manifestation_count }} 个版本。合作组可重复展示，不能把各行相加；数量包含全部纳排状态。最新观察日期不表示全部来源都检查到了当天。</p>
      <table><caption>可用摘录与版本摘要均不等于完整正文；{{ rows.length }} 个矩阵节点</caption><thead><tr><th scope="col">组织</th><th scope="col">纳入 / 登记报告</th><th scope="col">历史短摘录</th><th scope="col">版本摘要</th><th scope="col">实验线索</th><th scope="col">官方评审</th><th scope="col">来源检查</th><th scope="col">逐项证据</th></tr></thead><tbody><tr v-for="row in rows" :key="row.organization_id">
        <th scope="row"><a :href="withBase(`/organizations/${row.slug}`)">{{ row.name }}</a><small>{{ row.tier || '根实体' }}{{ row.is_root ? ' · 根实体' : '' }}</small></th>
        <td data-label="纳入 / 登记报告">{{ row.by_relevance.included.report_canonical_count }} / {{ row.counts.report_canonical_count }}</td><td data-label="历史短摘录">{{ ratio(row, 'report_excerpt_available') }}</td><td data-label="版本摘要">{{ ratio(row, 'arxiv_abstract_available') }}</td><td data-label="实验线索">{{ ratio(row, 'experiment_fact_work_count') }}</td><td data-label="官方评审">{{ ratio(row, 'strict_peer_reviewed') }}</td>
        <td data-label="来源检查"><span :class="{ 'report-warning': row.source_checks.stale || row.source_checks.failed }">近期成功 {{ row.source_checks.healthy }}/{{ row.source_checks.registered }}</span><small>未知 {{ row.source_checks.unknown }} · 失败 {{ row.source_checks.failed }} · 过期 {{ row.source_checks.stale }}</small></td><td data-label="逐项证据"><button type="button" :aria-label="`展开 ${row.name} 的报告覆盖`" @click="choose(row)">展开 {{ row.counts.report_canonical_count }} 项</button></td>
      </tr></tbody></table>
      <p v-if="!rows.length">当前筛选没有矩阵节点；这不是该组织没有研究产出的证据。</p>
      <p class="report-note">“实验线索”仅表示已登记来源自报的真机／跨本体／长时序／部署事实或数值观测，不等于完整实验审阅、同行评审或独立复现。“未登记”不表示公司没有报告。</p>
      <section v-if="selectedRow" class="report-detail" aria-live="polite"><h3>{{ selectedRow.name }} · 逐项覆盖</h3><p v-if="!selectedRow.reports.length">尚未登记可靠归属的技术报告；仍需检查官方发布，不能判断为没有报告。</p>
        <article v-for="report in selectedRow.reports" :key="report.work_id"><h4><a :href="workUrl(report.work_id)">{{ report.title }}</a></h4><p>{{ strata[report.relevance] }} · {{ eventDate(report.first_public_date, report.first_public_date_precision) }}</p><div class="report-badges"><span>{{ textStatus(report) }}</span><span>{{ report.experiment_facts[view].has_fact ? '有来源自报实验线索' : '实验事实未整理' }}</span><span>{{ report.peer_review[view].strict_peer_reviewed ? '有官方评审版本' : '评审未核验' }}</span></div><p><a v-for="url in report.urls" :key="url" :href="url" target="_blank" rel="noopener noreferrer">报告原始来源</a> · <a :href="workUrl(report.work_id)">全部版本与证据</a></p>
          <details><summary>版本、归属和时间边界</summary><ul><li v-for="version in report.manifestations" :key="version.manifestation_id"><a :href="version.url" target="_blank" rel="noopener noreferrer">报告版本</a> · {{ eventDate(version.published_at, version.date_precision) }} · <code>{{ version.manifestation_id }}</code></li><li v-for="(proof, index) in report.attribution_evidence" :key="index">{{ proof.evidence_grade }} · {{ proof.scope === 'direct_g1_g2' ? '直接归属' : '有来源的子组聚合' }} <a :href="proof.evidence_url" target="_blank" rel="noopener noreferrer">核对归属</a><ul v-if="proof.parent_path.length"><li v-for="step in proof.parent_path" :key="step.child_id"><a :href="step.evidence_url" target="_blank" rel="noopener noreferrer">{{ step.child_id }} → {{ step.parent_id }}</a></li></ul></li></ul><p>截止 {{ view === 'as_of' ? coverage.data_through : coverage.current_as_of }}；只使用有时间与来源证明的短摘录或摘要。全文与完整实验审阅没有据此自动标记完成。</p></details>
        </article><details v-if="selectedRow.source_checks.sources.length"><summary>逐来源检查状态</summary><ul><li v-for="source in selectedRow.source_checks.sources" :key="source.source_id"><a :href="source.url" target="_blank" rel="noopener noreferrer">{{ source.kind || '官方登记来源' }}</a> · {{ eventDate(source.last_checked) }} · {{ source.check_state === 'healthy' ? '近期成功' : source.check_state === 'failed' ? '读取失败' : '尚未确认' }}{{ source.stale_warning ? ' · 已过期' : '' }}</li></ul></details>
      </section>
      <details v-if="coverage.unattributed_reports.length || coverage.attribution_review_queue.length"><summary>不能静默遗漏：待归属报告 {{ coverage.global_summary.unattributed_report_works }} 项／归属线索 {{ coverage.attribution_review_queue.length }} 条</summary><ul><li v-for="report in coverage.unattributed_reports" :key="report.work_id"><a :href="workUrl(report.work_id)">{{ report.title }}</a> · 具体组归属待核验</li><li v-for="(item, index) in coverage.attribution_review_queue" :key="index"><a :href="workUrl(item.work_id)">{{ item.title }}</a> · {{ item.organization_id || '未知组织' }} · {{ item.attribution.evidence_grade || '未知证据' }}（不计可靠归属）</li></ul></details>
      <p><a :href="withBase('/api/v1/report-coverage.json')">下载可复算覆盖矩阵</a> · <a :href="withBase('/methods/coverage')">完整来源与归属审计</a></p>
    </template>
  </section>
</template>

<style scoped>
.report-coverage { margin: 32px 0; overflow-wrap: anywhere; }
.report-coverage h2 { margin: 8px 0 12px; font-size: clamp(22px, 3vw, 30px); font-weight: 650; line-height: 1.35; }
.report-coverage p { line-height: 1.7; }
.report-controls { display: flex; flex-wrap: wrap; gap: 16px; margin: 18px 0; }
.report-controls label { display: grid; gap: 6px; min-width: 0; max-width: 100%; }
.report-coverage :is(input,select,button) { min-height: 44px; max-width: 100%; padding: 8px 12px; border: 1px solid var(--vp-c-divider); border-radius: 6px; background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.report-coverage button, .report-coverage summary { cursor: pointer; }
.report-coverage :is(a,button,input,select,summary):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
.report-coverage small { display: block; font-size: 12px; color: var(--vp-c-text-2); }
.report-coverage table { width: 100%; border-collapse: collapse; font-size: 13px; }
.report-coverage :is(th,td) { padding: 12px 9px; border-bottom: 1px solid var(--vp-c-divider); text-align: left; }
.report-coverage caption { text-align: left; padding: 8px 0; color: var(--vp-c-text-2); }
.report-note { color: var(--vp-c-text-2); font-size: 13px; }
.report-detail { padding: 18px; margin: 14px 0; border: 1px solid var(--vp-c-divider); border-radius: 10px; }
.report-detail article { padding: 16px 0; border-bottom: 1px solid var(--vp-c-divider); }
.report-detail h4 { margin: 4px 0 8px; font-size: 17px; }
.report-coverage summary { padding: 12px 0; min-height: 44px; }
.report-coverage li { margin: 8px 0; }
.report-coverage code { white-space: normal; overflow-wrap: anywhere; font-size: 12px; }
.report-badges { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.report-badges span { background: var(--vp-c-bg-soft); border-radius: 4px; padding: 4px 8px; font-size: 13px; }
.report-warning { color: var(--vp-c-warning-1); }
@media(max-width:1023px) { .report-controls { display: grid; } .report-coverage table,.report-coverage tbody { display: block; } .report-coverage thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); } .report-coverage tr { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid var(--vp-c-divider); border-radius: 8px; margin: 12px 0; padding: 8px; } .report-coverage th[scope=row] { grid-column: 1 / -1; } .report-coverage td { min-width: 0; } .report-coverage td::before { content: attr(data-label); display: block; font-weight: 600; margin-bottom: 6px; } }
</style>
