<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
const coverage = ref<any>(null)
const error = ref('')
const page = ref(0)
const candidatesPage = ref(0)
const pending = computed(() => coverage.value?.high_signal_unattributed.slice(page.value * 20, (page.value + 1) * 20) || [])
const candidates = computed(() => coverage.value?.t2_candidates.slice(candidatesPage.value * 20, (candidatesPage.value + 1) * 20) || [])
onMounted(async () => {
  try {
    const response = await fetch(withBase('/api/v1/organization-coverage.json'))
    if (!response.ok) throw new Error('暂时无法读取研究组覆盖数据')
    coverage.value = await response.json()
  } catch (cause) { error.value = cause instanceof Error ? cause.message : '加载失败' }
})
</script>

<template>
  <section v-if="coverage" aria-label="研究组覆盖审计">
    <p>统计窗口 {{ coverage.window.from }}—{{ coverage.window.to }}。{{ coverage.scope_note }}</p>
    <section v-if="coverage.collection_coverage" aria-label="周更采集覆盖">
      <h2>周更采集状态</h2>
      <p v-if="coverage.collection_coverage.status === 'not_run'">尚无真实周更采集运行记录；现有迁移数据不代表自动周更已启用。</p>
      <template v-else>
        <p>可用数据截止 {{ coverage.collection_coverage.available_data_through || '未知' }}；全部登记来源确认完整至 {{ coverage.collection_coverage.complete_through || '尚未确认' }}。两者不能互相替代。</p>
        <p>本次仍未完整核验的来源：{{ coverage.collection_coverage.incomplete_sources?.join('、') || '无' }}。</p>
      </template>
      <p><a :href="withBase('/api/v1/source-coverage.json')">逐来源采集窗口、数量和状态</a></p>
    </section>
    <table><thead><tr><th>指标</th><th>已核验 / 分母</th></tr></thead><tbody>
      <tr><td>核心组可见</td><td>{{ coverage.metrics.core_groups_visible }} / {{ coverage.metrics.core_groups }}</td></tr>
      <tr><td>研究跟踪来源近期检查成功</td><td>{{ coverage.metrics.verified_healthy_tracking_sources }} / {{ coverage.metrics.registered_tracking_sources }}</td></tr>
      <tr><td>高信号工作研究组归属</td><td>{{ coverage.metrics.high_signal_attributed_works }} / {{ coverage.metrics.high_signal_works }}（{{ coverage.metrics.high_signal_attribution_rate == null ? '未测量' : (coverage.metrics.high_signal_attribution_rate * 100).toFixed(1) + '%' }}）</td></tr>
      <tr><td>来源过期警告</td><td>{{ coverage.metrics.stale_sources }}</td></tr>
      <tr><td>全球官方发布召回率</td><td>尚未测量；没有全量独立清单作为分母</td></tr>
    </tbody></table>
    <section v-if="coverage.recall_sample">
      <h2>独立官方发布回归样本</h2>
      <p>先从官方页面冻结样本，再与数据库对账；覆盖 {{ coverage.recall_sample.sampled_organizations }} / {{ coverage.recall_sample.total_core_groups }} 个核心组，不代表全球全部发布的召回率。</p>
      <table><thead><tr><th>指标</th><th>已关联 / 冻结分母</th></tr></thead><tbody>
        <tr><td>研究发布的唯一版本链接</td><td>{{ coverage.recall_sample.research_artifacts.manifestation_linked }} / {{ coverage.recall_sample.research_artifacts.denominator }}</td></tr>
        <tr><td>研究工作已在 included 默认集合</td><td>{{ coverage.recall_sample.research_artifacts.formal_visible }} / {{ coverage.recall_sample.research_artifacts.denominator }}</td></tr>
        <tr><td>部署 / 视频观察的版本链接</td><td>{{ coverage.recall_sample.observational_releases.manifestation_linked }} / {{ coverage.recall_sample.observational_releases.denominator }}</td></tr>
      </tbody></table>
      <p v-if="coverage.recall_sample.regression_gate">冻结样本发布检查：{{ coverage.recall_sample.regression_gate.status === 'passed' ? '通过' : '未通过' }}；研究发布链接召回门槛 {{ coverage.recall_sample.regression_gate.minimum * 100 }}%。分类正确性、全体来源覆盖和实验验证另行核查。</p>
      <p><a :href="withBase('/api/v1/coverage-gold-releases.json')">冻结样本及官方来源</a> · <a :href="withBase('/api/v1/release-recall.json')">逐条对账结果</a></p>
      <ul v-if="coverage.recall_sample.pending_classification?.length"><li v-for="item in coverage.recall_sample.pending_classification" :key="item.gold_id"><a :href="withBase(`/database/?ids=${encodeURIComponent(item.matched_work_ids.join(','))}&relevance=all`)">{{ item.title }}</a>：已采集，主分类待复核；未计入确定分类的趋势。</li></ul>
    </section>
    <h2>高信号待归属队列</h2>
    <p>这些研究仍在数据库中可查；不会因缺少可靠实验室归属而消失。</p>
    <ol><li v-for="work in pending" :key="work.work_id"><a :href="withBase(`/database/?work=${encodeURIComponent(work.work_id)}`)">{{ work.title }}</a> · {{ work.evidence_grade }} · {{ work.directions.join(' / ') }}</li></ol>
    <div class="coverage-controls"><button type="button" :disabled="page === 0" @click="page--">上一页</button><span>{{ page + 1 }} / {{ Math.max(1, Math.ceil(coverage.high_signal_unattributed.length / 20)) }}</span><button type="button" :disabled="(page + 1) * 20 >= coverage.high_signal_unattributed.length" @click="page++">下一页</button></div>
    <h2>T2 发现池</h2><p>仅由论文 affiliation 发现的候选；主页、负责人及具体研究组关系尚需官方证据。</p>
    <ul><li v-for="candidate in candidates" :key="candidate.candidate_id">{{ candidate.name }} · {{ candidate.evidence_work_ids?.length || 0 }} 项相关记录 <a v-if="candidate.evidence_work_ids?.length" :href="withBase(`/database/?ids=${encodeURIComponent(candidate.evidence_work_ids.join(','))}`)">查看来源研究</a></li></ul>
    <div class="coverage-controls"><button type="button" :disabled="candidatesPage === 0" @click="candidatesPage--">上一批</button><span>{{ candidatesPage + 1 }} / {{ Math.max(1, Math.ceil(coverage.t2_candidates.length / 20)) }}</span><button type="button" :disabled="(candidatesPage + 1) * 20 >= coverage.t2_candidates.length" @click="candidatesPage++">下一批</button></div>
  </section>
  <p v-else :role="error ? 'alert' : 'status'">{{ error || '正在读取覆盖审计……' }}</p>
</template>

<style scoped>
.coverage-controls{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:20px 0}
.coverage-controls button{padding:8px 14px;min-height:44px;border:1px solid var(--vp-c-divider);border-radius:6px}
.coverage-controls button:disabled{opacity:.5}
li{overflow-wrap:anywhere}
</style>
