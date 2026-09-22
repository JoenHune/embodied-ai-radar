<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

type Candidate = { dictionary_id: string; name: string; category: string; candidate_work_count: number }
type Summary = {
  schema_version: string; assurance: string; article_read_complete: boolean; usage_verified: boolean
  records_sha256: string; total_records: number; candidate_work_count: number; candidate_mention_count: number
  source_states: Record<string, number>; processing_states: Record<string, number>
  candidate_frequency: Candidate[]; latest_observed_at: string | null; latest_url: string; download_url: string
}
type Row = {
  work_id: string; observed_at: string | null; source_url: string | null; source_state: string
  process_state: string; candidate_names: string[]; candidate_name_count: number
  article_read_complete: boolean; usage_verified: boolean
}
type Latest = { schema_version: string; records_sha256: string; total_records: number; rows: Row[] }

const summary = ref<Summary | null>(null)
const latest = ref<Row[]>([])
const loading = ref(true)
const error = ref('')
let controller: AbortController | undefined
let requestSerial = 0

const number = (value: number) => value.toLocaleString('zh-CN')
const clock = (value: string | null | undefined) => value ? `${value.replace('T', ' ').slice(0, 16)} UTC` : '尚无来源时间'
const stateLabels: Record<string, string> = {
  extracted_not_read: '已提取文字，尚未精读', pending: '等待文字提取', source_needed: '待补充来源',
  extraction_failed: '提取失败', full_text_available: '已取得正文来源', partial_text: '来源文字不完整',
  not_fetched: '尚未抓取', external_source_needed: '待补充外部来源', blocked: '来源访问受限',
}
const state = (value: string) => stateLabels[value] || value.replaceAll('_', ' ')
const sourceLink = (value: string | null): string | undefined => {
  if (!value) return undefined
  try {
    const url = new URL(value)
    return url.protocol === 'https:' && !url.username && !url.password ? value : undefined
  } catch { return undefined }
}
const workLink = (id: string) => withBase(`/database/?${new URLSearchParams({ work: id, relevance: 'all' })}`)

const load = async () => {
  const request = ++requestSerial
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = ''
  try {
    const [summaryResponse, latestResponse] = await Promise.all([
      fetch(withBase('/api/v1/token-free/summary.json'), { cache: 'no-cache', signal: controller.signal }),
      fetch(withBase('/api/v1/token-free/latest.json'), { cache: 'no-cache', signal: controller.signal }),
    ])
    if (!summaryResponse.ok || !latestResponse.ok) throw new Error('unavailable')
    const [overview, recent] = await Promise.all([summaryResponse.json() as Promise<Summary>, latestResponse.json() as Promise<Latest>])
    if (request !== requestSerial) return
    if (overview.schema_version !== '1' || overview.assurance !== 'machine_extracted_unverified' ||
        overview.article_read_complete !== false || overview.usage_verified !== false ||
        !/^[0-9a-f]{64}$/.test(overview.records_sha256) || !Number.isSafeInteger(overview.total_records) ||
        !Number.isSafeInteger(overview.candidate_work_count) || !Number.isSafeInteger(overview.candidate_mention_count) ||
        !Array.isArray(overview.candidate_frequency) || overview.latest_url !== '/api/v1/token-free/latest.json' ||
        overview.download_url !== '/downloads/token-free/records.jsonl.gz' ||
        recent.schema_version !== '1' || recent.records_sha256 !== overview.records_sha256 ||
        recent.total_records !== overview.total_records || !Array.isArray(recent.rows) ||
        recent.rows.some(row => row.article_read_complete !== false || row.usage_verified !== false || !Array.isArray(row.candidate_names))) {
      throw new Error('version')
    }
    summary.value = overview
    latest.value = recent.rows
  } catch (cause) {
    if (request !== requestSerial) return
    if (cause instanceof Error && cause.name === 'AbortError') return
    error.value = '采集进度暂时无法核对，当前状态未知。请稍后重试。'
    summary.value = null
    latest.value = []
  } finally {
    if (request === requestSerial) loading.value = false
  }
}
onMounted(() => { void load() })
onBeforeUnmount(() => { requestSerial++; controller?.abort() })
</script>

<template>
  <section class="research-progress" aria-labelledby="research-progress-title">
    <header class="research-progress-header">
      <p class="research-progress-eyebrow">ORIGINAL TEXT · COLLECTION</p>
      <h1 id="research-progress-title">原文采集与候选提及进度</h1>
      <p>这里定期公开机器提取的来源覆盖和设备名称线索。候选提及可能出现在引用、背景、仿真或否定语境中；它不证明论文实际使用了该设备。</p>
    </header>

    <p v-if="loading" role="status">正在读取最新进度…</p>
    <p v-else-if="error" class="research-progress-error" role="alert">{{ error }} <button type="button" @click="load">重新读取</button></p>
    <template v-else-if="summary">
      <div class="research-progress-stats" aria-label="公开处理进度">
        <div><strong>{{ number(summary.total_records) }}</strong><span>已公开处理记录</span></div>
        <div><strong>{{ number(summary.processing_states.extracted_not_read || 0) }}</strong><span>已提取文字，尚未精读</span></div>
        <div><strong>{{ number(summary.candidate_work_count) }}</strong><span>出现设备候选提及的研究</span></div>
      </div>
      <p class="research-progress-meta">最新来源观察：{{ clock(summary.latest_observed_at) }}。以上是当前公开批次的数量，未公开或待补缺的工作不计为零。</p>

      <section aria-labelledby="progress-states">
        <h2 id="progress-states">处理状态</h2>
        <div v-if="summary.total_records" class="research-progress-states">
          <div v-for="(count, key) in summary.processing_states" :key="key"><span>{{ state(String(key)) }}</span><strong>{{ number(count) }}</strong></div>
        </div>
        <p v-else>尚无已公开的处理记录。</p>
      </section>

      <section v-if="summary.candidate_frequency.length" aria-labelledby="progress-candidates">
        <h2 id="progress-candidates">设备名称候选</h2>
        <p>按出现该名称的不同研究数排列。仅统计非背景段落的机器命中，仍可能包含仿真、否定或其他非使用语境；这不是设备使用量或市场份额。</p>
        <div class="research-progress-table"><table><thead><tr><th scope="col">名称</th><th scope="col">候选研究数</th></tr></thead><tbody>
          <tr v-for="item in summary.candidate_frequency" :key="`${item.dictionary_id}:${item.name}`"><td>{{ item.name }}</td><td>{{ number(item.candidate_work_count) }}</td></tr>
        </tbody></table></div>
      </section>

      <section aria-labelledby="progress-latest">
        <h2 id="progress-latest">最近公开的来源记录</h2>
        <p>展示最多 100 条，完整的候选与来源定位可下载。页面不提供论文全文或摘录。</p>
        <div v-if="latest.length" class="research-progress-list">
          <article v-for="row in latest" :key="row.work_id">
            <h3><a :href="workLink(row.work_id)">{{ row.work_id }}</a></h3>
            <p>{{ state(row.process_state) }} · {{ clock(row.observed_at) }}</p>
            <p v-if="row.candidate_names.length">设备名称候选：{{ row.candidate_names.join('、') }}{{ row.candidate_name_count > row.candidate_names.length ? ` 等 ${row.candidate_name_count} 种` : '' }}</p>
            <p v-else>未提取到非背景设备名称候选；不能据此断言论文没有使用设备。</p>
            <a v-if="sourceLink(row.source_url)" :href="sourceLink(row.source_url)" target="_blank" rel="noopener noreferrer">打开原始来源 ↗</a>
          </article>
        </div>
        <p v-else>尚无可展示的来源记录。</p>
      </section>

      <footer class="research-progress-footer">
        <a :href="withBase(summary.download_url)" download>下载完整公开记录（JSONL.GZ）</a>
        <a :href="withBase('/api/v1/token-free/summary.json')">进度统计 JSON</a>
        <p>所有记录均为机器提取，未形成完整阅读回执或设备使用核验。数据校验值：<code>{{ summary.records_sha256 }}</code></p>
      </footer>
    </template>
  </section>
</template>

<style scoped>
.research-progress { max-width: 1120px; margin: 0 auto 80px; color: var(--vp-c-text-1); }
.research-progress-header { padding: 34px 0 25px; border-bottom: 1px solid var(--vp-c-divider); }
.research-progress-eyebrow { margin: 0 0 8px; color: var(--vp-c-brand-1); font-size: 12px; font-weight: 700; letter-spacing: .13em; }
.research-progress h1 { margin: 0 0 14px; font-size: clamp(28px, 4vw, 42px); line-height: 1.2; }
.research-progress h2 { margin: 42px 0 10px; font-size: 22px; }
.research-progress h3 { margin: 0 0 8px; font-size: 16px; }
.research-progress p { line-height: 1.75; color: var(--vp-c-text-2); }
.research-progress-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin: 28px 0 14px; }
.research-progress-stats div { display: flex; flex-direction: column; padding: 20px; background: var(--vp-c-bg-soft); border: 1px solid var(--vp-c-divider); border-radius: 10px; }
.research-progress-stats strong { font-size: 27px; line-height: 1.2; }
.research-progress-stats span, .research-progress-meta { font-size: 13px; }
.research-progress-states { display: flex; flex-wrap: wrap; gap: 10px; }
.research-progress-states div { display: flex; gap: 12px; align-items: center; padding: 9px 12px; border: 1px solid var(--vp-c-divider); border-radius: 8px; font-size: 13px; }
.research-progress-table { overflow-x: auto; }
.research-progress table { width: 100%; border-collapse: collapse; font-size: 14px; }
.research-progress th, .research-progress td { padding: 10px 12px; border-bottom: 1px solid var(--vp-c-divider); text-align: left; }
.research-progress-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.research-progress-list article { padding: 17px; border: 1px solid var(--vp-c-divider); border-radius: 10px; overflow-wrap: anywhere; }
.research-progress-list article p { margin: 6px 0; font-size: 13px; }
.research-progress-list article a, .research-progress-footer a { color: var(--vp-c-brand-1); }
.research-progress-footer { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--vp-c-divider); font-size: 14px; }
.research-progress-footer p { flex-basis: 100%; font-size: 12px; overflow-wrap: anywhere; }
.research-progress-error { padding: 16px; border: 1px solid var(--vp-c-danger-1); border-radius: 8px; }
.research-progress button { padding: 7px 12px; border: 1px solid var(--vp-c-divider); border-radius: 6px; cursor: pointer; }
@media (max-width: 700px) { .research-progress-stats { grid-template-columns: 1fr; } .research-progress-list { grid-template-columns: 1fr; } }
</style>
