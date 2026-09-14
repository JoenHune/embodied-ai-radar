<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'

const props = defineProps<{ month: string }>()
const panel = ref<HTMLDetailsElement | null>(null)
const records = ref<any[] | null>(null)
const loading = ref(false)
const error = ref(false)
const selected = computed(() => (records.value || []).filter((row) => row.generated_month === props.month && row.review_status === 'draft'))
const stanceLabel: Record<string, string> = { supports: '待审支持', contradicts: '待审反证', neutral: '中性／边界证据' }
const reviewerLabel = (name: string) => name === 'Codex AI source check; not a human review' ? 'AI 原文核对（非人工审核）' : name
const load = async () => {
  if (loading.value || records.value !== null) return
  loading.value = true
  error.value = false
  try {
    const response = await fetch(withBase('/api/v1/signal-evidence.json'))
    if (!response.ok) throw new Error('unavailable')
    const body = await response.json()
    if (!Array.isArray(body.records)) throw new Error('invalid')
    records.value = body.records
  } catch { error.value = true } finally { loading.value = false }
}
const toggle = (event: Event) => { if ((event.currentTarget as HTMLDetailsElement).open) void load() }
// Native SSR details can be opened before Vue attaches the toggle listener.
// Recover that user action when hydration completes instead of leaving a
// permanently empty open panel that needs a second close/open cycle.
onMounted(() => { if (panel.value?.open) void load() })
const workUrl = (id: string) => withBase(`/database/?work=${encodeURIComponent(id)}&relevance=all`)
</script>

<template>
  <section class="v3-analysis-section v3-reading-queue" aria-label="待审核的原文阅读证据">
    <header><h2>原文阅读与待审证据</h2><p>逐项保留研究判断、原文短摘录与解释边界。草稿不参与已验证支持数量或趋势成熟度。</p></header>
    <details ref="panel" @toggle="toggle">
      <summary>展开 {{ month }} 的待审证据</summary>
      <p v-if="loading" role="status">正在读取证据草稿…</p>
      <p v-else-if="error" role="alert">证据草稿暂时无法读取，不能据此判断该月没有证据。<button type="button" @click="load">重试读取</button></p>
      <template v-else-if="records !== null">
        <p role="status">{{ selected.length }} 份待审记录；这是阅读进度，不是独立论文或已验证结论数量。</p>
        <article v-for="row in selected" :key="row.record_id" class="v3-note-row">
          <h3><a :href="workUrl(row.work_id)">{{ row.source_text_snapshot?.title || row.work_id }}</a></h3>
          <p><strong>{{ row.signal_id }} · {{ stanceLabel[row.stance] || '待核查' }}</strong> · 原文公开：{{ row.public_at ? eventDate(row.public_at, row.public_at_precision) : '时间尚未核验' }}</p>
          <p>{{ row.statement }}</p>
          <dl>
            <div><dt>摘要中已绑定的实验条件</dt><dd>{{ row.experiment?.setting || '本卡未从摘要提取，需查看全文' }}</dd></div>
            <div><dt>摘要中已绑定的对照</dt><dd>{{ row.experiment?.baseline || '本卡未提取，不代表原文没有对照' }}</dd></div>
            <div><dt>摘要中已绑定的指标</dt><dd>{{ row.experiment?.metric || '本卡未提取，不代表没有实验指标' }}</dd></div>
          </dl>
          <details><summary>查看原文短摘录与阅读记录</summary>
            <ul><li v-for="(span, index) in row.source_spans" :key="index"><q lang="en">{{ span.quote }}</q></li></ul>
            <p v-for="review in row.review_history" :key="review.review_id"><strong>{{ reviewerLabel(review.reviewer) }}</strong> · {{ eventDate(review.reviewed_at) }}<br />{{ review.note }}</p>
            <p v-if="!row.review_history?.length">自动生成草稿，尚无单独阅读记录。</p>
          </details>
          <a :href="row.source_url" target="_blank" rel="noreferrer">打开所引用的原文版本</a>
        </article>
        <p v-if="!selected.length" class="v3-empty">该月尚无已保存的待审阅读记录；不等于相关研究或反例不存在。</p>
      </template>
    </details>
    <a :href="withBase('/api/v1/signal-evidence.json')">下载全部命题证据与草稿</a>
  </section>
</template>

<style scoped>
.v3-reading-queue { overflow-wrap: anywhere; }
.v3-reading-queue summary { cursor: pointer; padding: 10px 0; }
.v3-reading-queue dl { display: grid; gap: 10px; padding: 14px; border: 1px solid var(--vp-c-divider); border-radius: 10px; }
.v3-reading-queue dt { font-weight: 600; }
.v3-reading-queue dd { margin: 4px 0 0; }
.v3-reading-queue button { margin-left: 12px; text-decoration: underline; }
.v3-reading-queue article > a { display: inline-block; margin-top: 12px; }
</style>
