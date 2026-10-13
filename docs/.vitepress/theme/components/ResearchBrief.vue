<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'

const props = defineProps<{ overview: any }>()
const brief = computed(() => props.overview.researchBrief || {})
const month = computed(() => props.overview.latestComplete)
const directions = computed(() => [...(month.value.directions || [])]
  .filter(row => Number.isFinite(row.share_delta) && Number.isFinite(row.share))
  .sort((a, b) => Math.abs(b.share_delta) - Math.abs(a.share_delta) || a.code.localeCompare(b.code)).slice(0, 4))
const questions = computed(() => (month.value.trend_ledger || []).slice(0, 3))
const sourceLabels: Record<string, string> = { arxiv: 'arXiv 论文', publications: '正式发表', official_groups: '团队官方来源', arxiv_research_status: '论文状态', corl: 'CoRL / OpenReview', corl_openreview: 'CoRL / OpenReview' }
const sourceLabel = (source: string) => sourceLabels[source] || source
const sourceStatus = (source: any) => source.complete ? '已确认完整' : ['failed', 'error'].includes(source.status) ? '获取失败' : ['not_run', 'not_checked_this_run'].includes(source.status) ? '本轮未检查' : '覆盖不完整'
const delta = (value: number) => `${value > 0 ? '+' : ''}${(value * 100).toFixed(1)}`
const directionUrl = (code: string) => withBase(`/database/?${new URLSearchParams({ from: month.value.month, to: month.value.month, directions: code, relevance: 'included' })}`)
const teamWorkUrl = (team: any) => team.work_id ? withBase(`/database/?${new URLSearchParams({ work: team.work_id, relevance: 'all' })}`) : team.url
const questionUrl = (question: any) => {
  const ids = [...new Set<string>(question.candidate_work_ids || [])]
  return ids.length ? withBase(`/database/?${new URLSearchParams({ ids: ids.join(','), relevance: 'all' })}`) : withBase('/trends/')
}
</script>

<template>
  <section class="research-brief" aria-label="研究决策概览">
    <div class="brief-freshness">
      <div><span>分析截止</span><strong>{{ brief.analysis_through || overview.manifest.data_through || '未登记' }}</strong></div>
      <div><span>已观察到的研究</span><strong>{{ brief.available_data_through || '未登记' }}</strong></div>
      <div><span>最近来源检查</span><strong>{{ brief.last_source_check || '未登记' }}</strong></div>
      <details class="brief-source-status">
        <summary :class="{ incomplete: !brief.complete }">{{ brief.complete ? '来源覆盖已确认' : '来源覆盖待补齐' }}</summary>
        <ul v-if="brief.sources?.length">
          <li v-for="source in brief.sources" :key="source.source"><span>{{ sourceLabel(source.source) }}</span><span>{{ sourceStatus(source) }}<small v-if="source.checked_at"> · {{ source.checked_at }}</small></span></li>
        </ul>
        <p v-else>尚无来源检查记录。</p>
        <a :href="withBase('/methods/coverage')">查看覆盖审计 →</a>
      </details>
    </div>

    <div class="brief-heading"><div><p class="brief-kicker">{{ month.month }} · 完整月观察</p><h2>本期研究观察</h2></div><a :href="withBase(`/monthly/?month=${month.month}`)">完整月报 →</a></div>
    <div class="brief-columns">
      <section class="brief-directions" aria-labelledby="brief-directions-title">
        <h3 id="brief-directions-title">研究重心的变化</h3>
        <p class="brief-note">按主方向份额变化幅度；相关研究包含多标签命中。</p>
        <ol>
          <li v-for="direction in directions" :key="direction.code">
            <a :href="directionUrl(direction.code)"><span class="brief-direction-code">{{ direction.code }}</span><strong>{{ direction.label }}</strong><span class="brief-delta" :class="direction.share_delta >= 0 ? 'up' : 'down'">{{ delta(direction.share_delta) }} <small>百分点</small></span></a>
            <div class="brief-direction-detail"><span>{{ direction.primary_count }} 项 · 主方向占比 {{ (direction.share * 100).toFixed(1) }}%</span><a :href="directionUrl(direction.code)">当月相关研究 →</a></div>
          </li>
        </ol>
        <p v-if="!directions.length" class="brief-note">本期尚无可比较的方向数据。</p>
      </section>
      <section class="brief-questions" aria-labelledby="brief-questions-title">
        <h3 id="brief-questions-title">接下来要验证什么</h3>
        <p class="brief-note">研究命题与反证条件，保留尚未完成的证据判断。</p>
        <ol>
          <li v-for="question in questions" :key="question.signal_id">
            <a class="brief-question-title" :href="questionUrl(question)">{{ question.title }} →</a>
            <p><span>反证条件：</span>{{ question.falsifier }}</p>
            <span class="brief-evidence-state">{{ question.reviewed_support_count > 0 ? '已有审阅支持' : '待逐篇核验' }} · 已审阅支持 {{ question.reviewed_support_count ?? 0 }} 项</span>
          </li>
        </ol>
        <p v-if="!questions.length" class="brief-note">本期尚未登记研究命题。</p>
      </section>
    </div>

    <section v-if="brief.teams?.length" class="brief-teams" aria-labelledby="brief-teams-title">
      <div class="brief-heading"><div><h2 id="brief-teams-title">团队与公司的研究发布</h2><p class="brief-note">{{ brief.team_window.from }} 至 {{ brief.team_window.through }} 已登记动态，按发布日期。</p></div><a :href="withBase('/organizations/')">全部研究组 →</a></div>
      <ul>
        <li v-for="team in brief.teams" :key="team.organization_id">
          <div class="brief-team-meta"><span>{{ team.tier }}</span><time :datetime="team.published_at">{{ team.published_at }}</time></div>
          <h3><a :href="withBase(`/organizations/${team.slug}`)">{{ team.name }}</a></h3>
          <a class="brief-team-work" :href="teamWorkUrl(team)">{{ team.title }}</a>
          <a class="brief-team-source" :href="team.url" target="_blank" rel="noopener noreferrer">发布来源 ↗</a>
        </li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.research-brief { margin-bottom: 32px; }
.brief-freshness { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)) minmax(180px, 1.3fr); gap: 16px; padding: 16px 0; border-top: 1px solid var(--vp-c-divider); border-bottom: 1px solid var(--vp-c-divider); margin-bottom: 28px; align-items: start; }
.brief-freshness > div { display: grid; gap: 5px; }
.brief-freshness > div > span, .brief-note, .brief-team-meta { color: var(--vp-c-text-2); font-size: 13px; line-height: 1.6; }
.brief-freshness strong { font-size: 15px; font-variant-numeric: tabular-nums; }
.brief-source-status { font-size: 13px; line-height: 1.6; }
.brief-source-status summary { cursor: pointer; color: var(--vp-c-green-1); font-weight: 600; min-height: 30px; }
.brief-source-status summary.incomplete { color: var(--vp-c-warning-1); }
.brief-source-status ul { margin: 6px 0 10px; padding: 0; list-style: none; }
.brief-source-status li { display: grid; gap: 2px; margin-bottom: 8px; }
.brief-source-status li > span:last-child { color: var(--vp-c-text-2); }
.brief-source-status small { font-size: inherit; }
.brief-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.brief-heading h2 { font-size: 23px; line-height: 1.4; margin: 0; }
.brief-heading > a { font-size: 13px; flex-shrink: 0; }
.brief-kicker { font-size: 13px; margin: 0 0 4px; color: var(--vp-c-text-2); }
.brief-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.brief-columns h3 { font-size: 17px; margin: 0 0 6px; }
.brief-note { margin: 0 0 10px; }
.brief-columns ol, .brief-teams ul { list-style: none; padding: 0; margin: 0; }
.brief-directions li { border-bottom: 1px solid var(--vp-c-divider); padding: 17px 0; }
.brief-directions li > a { display: grid; grid-template-columns: 28px 1fr auto; align-items: baseline; gap: 8px; }
.brief-direction-code { color: var(--vp-c-text-3); font-size: 12px; }
.brief-directions strong { font-size: 15px; line-height: 1.6; color: var(--vp-c-text-1); }
.brief-delta { white-space: nowrap; font-size: 17px; font-weight: 600; font-variant-numeric: tabular-nums; }
.brief-delta small { font-size: 11px; font-weight: 400; }
.brief-delta.up { color: var(--vp-c-green-1); }
.brief-delta.down { color: var(--vp-c-text-2); }
.brief-direction-detail { margin: 5px 0 0 36px; display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--vp-c-text-2); }
.brief-direction-detail a { white-space: nowrap; }
.brief-questions li { padding: 13px 0; border-bottom: 1px solid var(--vp-c-divider); }
.brief-question-title { font-size: 15px; font-weight: 600; }
.brief-questions li p { font-size: 13px; line-height: 1.7; margin: 5px 0; color: var(--vp-c-text-2); }
.brief-evidence-state { color: var(--vp-c-text-3); font-size: 12px; }
.brief-teams { padding-top: 32px; }
.brief-teams .brief-heading h2 { font-size: 20px; }
.brief-teams .brief-note { margin: 4px 0 0; }
.brief-teams ul { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 22px; }
.brief-teams li { min-width: 0; padding-top: 12px; border-top: 2px solid var(--vp-c-divider); display: flex; flex-direction: column; align-items: flex-start; }
.brief-team-meta { display: flex; justify-content: space-between; width: 100%; font-size: 12px; }
.brief-teams h3 { font-size: 16px; line-height: 1.5; margin: 10px 0 7px; }
.brief-team-work { color: var(--vp-c-text-2); font-size: 13px; line-height: 1.6; overflow-wrap: anywhere; }
.brief-team-source { margin-top: auto; padding-top: 10px; font-size: 12px; }
@media (max-width: 959px) { .brief-freshness { grid-template-columns: repeat(2, minmax(0, 1fr)); } .brief-columns { gap: 24px; } .brief-teams ul { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 639px) { .brief-columns { grid-template-columns: 1fr; gap: 24px; } .brief-heading { align-items: flex-start; } .brief-heading h2 { font-size: 21px; } .brief-teams ul { grid-template-columns: 1fr; gap: 16px; } .brief-freshness { gap: 14px 12px; } .brief-directions li > a { grid-template-columns: 24px 1fr; } .brief-delta { grid-column: 2; } .brief-direction-detail { margin-left: 32px; } }
</style>
