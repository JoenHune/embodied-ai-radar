<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { publicationEventDate } from '../lib/dates'
import ResearchFeed from './ResearchFeed.vue'

const organizations = ref<any[]>([])
const selected = ref('all')
const page = ref(0)
const pageSize = 30
const publishedEvents = ref<any[]>([])
const eventLabels: Record<string, string> = { paper: '论文', preprint: '预印本', technical_report: '技术报告', model_release: '模型发布', repository: '开源仓库', code: '代码', dataset: '数据集', deployment: '部署', demo: '演示', accepted: '同行评审确认', published: '正式出版', acceptance: '同行评审确认', accepted_peer_reviewed: '同行评审确认', publication: '正式出版', published_proceedings: '正式出版', independent_replication: '独立复现' }
const strategicTypes = new Set(['demo', 'deployment', 'hiring', 'personnel_change', 'organization_change', 'funding'])
;['strategic_partnership', 'deployment_update', 'technology_deployment_update'].forEach(type => strategicTypes.add(type))
const contextTypes = new Set(['research_explainer', 'code_release'])
Object.assign(eventLabels, { strategic_partnership: '战略合作', deployment_update: '部署进展（公司披露）', technology_deployment_update: '技术栈与部署观察', research_explainer: '既有研究解读', code_release: '软件版本更新' })
onMounted(async () => {
  try { const response = await fetch(withBase('/api/v1/organization-overview.json')); if (response.ok) organizations.value = (await response.json()).rows || [] } catch { /* Individual event sources remain accessible. */ }
  try {
    const response = await fetch(withBase('/api/v1/evidence-events.json'))
    if (response.ok) { const body = await response.json(); publishedEvents.value = Array.isArray(body) ? body : body.events || [] }
  } catch { /* The registered organization snapshots remain available offline. */ }
})
const events = computed(() => {
  const seen = new Set<string>()
  const orgById = new Map(organizations.value.map(org => [org.organization_id, org]))
  const sourcedEvents = publishedEvents.value.map(event => ({ ...event, organization_name: event.organization_name || orgById.get(event.organization_id)?.name || event.organization_id, tier: event.tier || orgById.get(event.organization_id)?.tier }))
  return [...organizations.value.flatMap((org: any) => (org.updates || []).map((event: any) => ({ ...event, organization_name: org.name, tier: org.tier }))), ...sourcedEvents]
    .filter((event: any) => {
      if (seen.has(event.event_id)) return false
      seen.add(event.event_id)
      const strategic = strategicTypes.has(event.event_type) && ['G1', 'G2'].includes(event.attribution_grade)
      const context = contextTypes.has(event.event_type) && event.review_status === 'verified' && ['G1', 'G2'].includes(event.attribution_grade)
      const pending = !context && (event.review_required || event.research_eligible === false || !['G1', 'G2'].includes(event.attribution_grade))
      if (selected.value === 'review') return pending && !strategic
      if (pending && !strategic) return false
      return selected.value === 'all' || (selected.value === 'research' ? !strategic && !context : selected.value === 'context' ? context : selected.value === 'strategic' ? strategic : selected.value === 'preprint' ? ['paper', 'preprint'].includes(event.event_type) : selected.value === 'validation' ? ['accepted', 'published', 'acceptance', 'accepted_peer_reviewed', 'publication', 'published_proceedings', 'independent_replication'].includes(event.event_type) : event.event_type === selected.value)
    })
    .sort((left: any, right: any) => (right.occurred_at || right.published_at || '').localeCompare(left.occurred_at || left.published_at || ''))
})
const shownEvents = computed(() => events.value.slice(page.value * pageSize, (page.value + 1) * pageSize))
const selectType = (value: string) => { selected.value = value; page.value = 0 }
</script>

<template>
  <div class="v3-pulse">
    <header class="v3-page-heading">
      <div>
        <p class="v3-eyebrow">WEEKLY RESEARCH PULSE</p>
        <h1>动态观察</h1>
        <p>官方研究发布、开源资产和公司战略变化分层呈现；社交热度不进入正式趋势计数。</p>
      </div>
      <a :href="withBase('/monthly/')">进入月度研究账本</a>
    </header>
    <ResearchFeed title="图文研究流" :limit="9" />
    <details class="visual-event-archive"><summary>完整发布记录、证据升级与战略观察</summary>
    <div class="v3-pulse-note">
      本页不依赖付费 X API。若存在公开、可核验的社交讨论快照，只作为传播旁证，并与论文和技术报告分开。
    </div>
    <div class="v3-pulse-filters" aria-label="动态类型筛选">
      <button v-for="item in [['all','全部'],['research','研究发布'],['validation','证据升级'],['preprint','论文/预印本'],['technical_report','技术报告'],['model_release','模型发布'],['repository','开源仓库'],['context','版本更新与解读'],['strategic','战略观察'],['review','待核验记录']]" :key="item[0]" type="button" :aria-pressed="selected === item[0]" @click="selectType(item[0])">{{ item[1] }}</button>
    </div>
    <div class="v3-pagination"><span role="status">共 {{ events.length }} 项 · 第 {{ page + 1 }} / {{ Math.max(1, Math.ceil(events.length / pageSize)) }} 页</span><button type="button" :disabled="page === 0" @click="page--">上一页</button><button type="button" :disabled="(page + 1) * pageSize >= events.length" @click="page++">下一页</button></div>
    <section class="v3-pulse-list" aria-live="polite">
      <article v-for="event in shownEvents" :key="event.event_id">
        <time>{{ publicationEventDate(event) }}</time>
        <div>
          <span>{{ event.tier || '公开验证' }} · {{ event.organization_name || event.venue || '研究事件' }}{{ ['supported_by', 'officially_supports_development'].includes(event.attribution_relation) ? '（支持关系）' : '' }} · {{ eventLabels[event.event_type] || event.event_type }}</span><strong v-if="strategicTypes.has(event.event_type)" class="v3-strategic-label">战略观察</strong>
          <h2><a :href="event.url || event.source_url" target="_blank" rel="noreferrer">{{ event.title || event.summary_zh || '查看事件官方证据' }}</a></h2>
          <p v-if="selected === 'review'">待复核记录，不计入正式研究趋势。</p><p>{{ event.summary_zh }}</p>
          <p v-if="contextTypes.has(event.event_type)">已核实的后续更新，不重复计为新论文或新模型。</p><p v-if="['supported_by', 'officially_supports_development'].includes(event.attribution_relation)">组织关系：官方支持；不等同于该公司独立完成研究。</p><ul v-if="event.limitations_zh?.length"><li v-for="limitation in event.limitations_zh" :key="limitation">{{ limitation }}</li></ul>
          <small>{{ event.direction_codes?.join(' · ') || '方向待核验' }}<template v-if="event.claim_status"> · {{ event.claim_status }}</template></small>
          <a v-if="event.work_id" :href="withBase(`/database/?ids=${encodeURIComponent(event.work_id)}`)" class="v3-pulse-evidence-link">对应研究及全部版本</a>
        </div>
      </article>
      <p v-if="!events.length" class="v3-empty">当前筛选下没有已核验变化。</p>
    </section>
    </details>
  </div>
</template>
