<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'

type Row = Record<string, any>
const props = defineProps<{ snapshot: Row }>()
const object = (value: unknown): value is Row => Boolean(value && typeof value === 'object' && !Array.isArray(value))
const text = (value: unknown): value is string => typeof value === 'string' && Boolean(value.trim())
const hash = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value)
const validMonth = (value: unknown): value is string => typeof value === 'string' && /^20\d{2}-(0[1-9]|1[0-2])$/.test(value)
const month = computed(() => validMonth(props.snapshot.month) ? props.snapshot.month : '')
const sections = [
  ['claims', '旧版执行结论'], ['direction_summaries', '旧版方向摘要'],
  ['question_summaries', '旧版问题轴摘要'], ['counterevidence', '旧版反例与边界'], ['watchlist', '旧版观察清单'],
]
const previous = computed<Row | null>(() => {
  const row = props.snapshot.previous_editorial_summary || props.snapshot.previous_editorial
  if (!month.value || !object(row) || row.month !== month.value ||
      !['historical_not_current', 'complete'].includes(row.status) || !hash(row.input_digest) ||
      !text(row.model) || !text(row.generated_at) || !Number.isFinite(Date.parse(row.generated_at))) return null
  return row
})
const groups = computed(() => sections.map(([key, label]) => ({ key, label,
  rows: (Array.isArray(previous.value?.[key]) ? previous.value![key] : [])
    .filter((row: unknown) => object(row) && (text(row.summary) || text(row.text))) as Row[],
})).filter(group => group.rows.length))
const reason = computed(() => ({
  input_digest_changed: '研究证据包已更新，旧稿尚未按新证据重新生成或核验。',
  model_changed: '当前编辑模型配置已变化，旧稿未通过本版匹配检查。',
  saved_editorial_validation_failed: '旧稿未通过当前结构或引用校验。',
} as Record<string, string>)[props.snapshot.editorial_unavailable_reason] || '这是保留供对照的历史编辑，不代表当前证据支持的结论。')
const references = (row: Row): string[] => [...new Set<string>(['supporting_ids', 'counterevidence_ids']
  .flatMap(key => Array.isArray(row[key]) ? row[key].filter(text) : []))]
const rowTitle = (row: Row) => [text(row.code) ? row.code : '', text(row.title) ? row.title : ''].filter(Boolean).join(' · ')
const rowText = (row: Row) => text(row.summary) ? row.summary : row.text
const packetStatusLabel = (status: unknown) => status === 'available'
  ? '原始请求证据包已留存'
  : status === 'missing_before_archive_feature'
    ? '旧稿原始请求包未留存，不能完整重放'
    : '请求包状态待核验'
const archives = computed(() => {
  if (!month.value || !Array.isArray(props.snapshot.editorial_history)) return []
  const seen = new Set<string>()
  return props.snapshot.editorial_history.flatMap((row: unknown) => {
    if (!object(row) || !hash(row.artifact_digest) || !hash(row.input_digest) || !text(row.model) ||
        !text(row.generated_at) || !Number.isFinite(Date.parse(row.generated_at))) return []
    const path = `/api/v1/editorial-history/${month.value}/${row.artifact_digest}.json`
    // Only exact local archive paths; reject foreign hosts, other months,
    // query strings, encoded traversal and user-supplied arbitrary links.
    if (![path, withBase(path)].includes(row.archive_url) || seen.has(row.artifact_digest)) return []
    seen.add(row.artifact_digest)
    return [{ artifact_digest: row.artifact_digest, generated_at: row.generated_at, model: row.model,
      input_digest: row.input_digest, packet_status_label: packetStatusLabel(row.input_packet_status), url: withBase(path) }]
  })
})
const hasContent = computed(() => groups.value.length > 0 || archives.value.length > 0)
</script>

<template>
  <section v-if="hasContent" class="historical-editorial" aria-label="旧版月度研究摘要">
    <details :key="month">
      <summary>旧版摘要（依据已变化，不作为当前结论）</summary>
      <div class="historical-editorial-body">
        <p class="historical-boundary" role="note">{{ reason }}旧稿不计入本月摘要完成状态，也不替换当前统计、方向判断或反例。</p>
        <p v-if="previous && groups.length" class="historical-meta">{{ previous.month }} · 生成于 {{ eventDate(previous.generated_at) }} · {{ previous.model }} · 历史版本</p>
        <p v-if="previous && groups.length" class="historical-digest">旧稿证据包标识：<code>{{ previous.input_digest }}</code></p>
        <section v-for="group in groups" :key="group.key" class="historical-group" :aria-label="group.label">
          <h3>{{ group.label }}</h3>
          <article v-for="(row, index) in group.rows" :key="row.claim_id || `${group.key}-${index}`">
            <h4 v-if="rowTitle(row)">{{ rowTitle(row) }}</h4>
            <p>{{ rowText(row) }}</p>
            <details v-if="references(row).length" class="historical-references">
              <summary>旧稿引用 {{ references(row).length }} 条（未按当前证据复核）</summary>
              <ul><li v-for="id in references(row)" :key="id"><code>{{ id }}</code></li></ul>
            </details>
          </article>
        </section>
        <section v-if="archives.length" class="historical-archives" aria-label="完整旧稿下载">
          <h3>完整旧稿</h3>
          <p>下载保留的完整编辑与原始依据标识；归档可查不表示内容已通过当前证据校验。</p>
          <ul><li v-for="archive in archives" :key="archive.artifact_digest">
            <a :href="archive.url" download>下载旧稿 · {{ eventDate(archive.generated_at) }} · {{ archive.model }}</a>
            <small>版本 {{ archive.artifact_digest.slice(0, 12) }} · 证据包 {{ archive.input_digest.slice(0, 12) }}</small>
            <small>{{ archive.packet_status_label }}</small>
          </li></ul>
        </section>
      </div>
    </details>
  </section>
</template>

<style scoped>
.historical-editorial { margin: 24px 0; border: 1px solid var(--vp-c-divider); border-left: 4px solid var(--vp-c-warning-1); border-radius: 10px; background: var(--vp-c-bg-soft); min-width: 0; overflow-wrap: anywhere; }
.historical-editorial summary { cursor: pointer; padding: 14px 18px; min-height: 44px; font-weight: 600; line-height: 1.7; }
.historical-editorial-body { padding: 0 18px 18px; }
.historical-editorial p { line-height: 1.8; }
.historical-boundary, .historical-meta, .historical-digest, .historical-archives p { font-size: 13px; color: var(--vp-c-text-2); }
.historical-editorial code { white-space: normal; overflow-wrap: anywhere; font-size: 11px; }
.historical-group { margin-top: 22px; }
.historical-editorial h3 { font-size: 16px; margin: 18px 0 12px; }
.historical-group article { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--vp-c-divider); }
.historical-group h4 { font-size: 14px; margin: 0 0 6px; }
.historical-group article > p { font-size: 14px; margin: 0; white-space: pre-line; }
.historical-references summary { padding: 8px 0; font-size: 12px; color: var(--vp-c-text-2); font-weight: 400; }
.historical-references ul, .historical-archives ul { padding-left: 20px; margin: 8px 0; }
.historical-archives a { display: inline-flex; align-items: center; min-height: 44px; color: var(--vp-c-brand-1); text-decoration: underline; }
.historical-archives small { display: block; color: var(--vp-c-text-2); }
.historical-editorial :is(a, summary):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 2px; }
@media (max-width: 640px) { .historical-editorial > details > summary { padding: 12px; } .historical-editorial-body { padding: 0 12px 14px; } }
</style>
