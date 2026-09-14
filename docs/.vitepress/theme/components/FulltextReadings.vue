<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'

type Judgment = { text_zh: string; source_locator: string }
type Reading = { reading_id: string; work_id: string; title: string; relevance_status: string; source_url: string; versioned_source_url?: string; version: string; read_completed_at: string; article_normalization?: string; checked_table_count: number; findings_zh: Judgment[]; limitations_zh: Judgment[] }
const props = defineProps<{ expectedVersion: string; dictionaryHash: string; cohort: 'all_works' | 'included' }>()
const readings = ref<Reading[]>([])
const loadedVersion = ref('')
const loadedDictionary = ref('')
const loading = ref(true)
const error = ref('')
const shown = ref(12)
let controller: AbortController | undefined
let serial = 0
let disposed = false
const sourceAllowed = (value: unknown) => {
  try { const u = new URL(String(value)); return u.protocol === 'https:' && ['arxiv.org', 'www.arxiv.org'].includes(u.hostname) && /^\/html\/[a-zA-Z0-9./-]+v[1-9]\d*$/.test(u.pathname) && !u.username && !u.password && !u.search && !u.hash }
  catch { return false }
}
const readingUrl = (row: Reading) => row.versioned_source_url || row.source_url
const readingSourceAllowed = (row: Reading) => {
  if (!row.versioned_source_url) return sourceAllowed(row.source_url)
  if (sourceAllowed(row.source_url) || !sourceAllowed(row.versioned_source_url) || !/^v[1-9]\d*$/.test(row.version)) return false
  try {
    const original = new URL(row.source_url)
    if (original.protocol !== 'https:' || !['arxiv.org', 'www.arxiv.org'].includes(original.hostname) || original.username || original.password || original.port || original.search || original.hash) return false
    return row.versioned_source_url === 'https://arxiv.org' + original.pathname.replace(/\/+$/, '') + row.version
  } catch { return false }
}
const validJudgments = (value: any) => Array.isArray(value) && value.length > 0 && value.every(row => typeof row.text_zh === 'string' && row.text_zh.trim() && typeof row.source_locator === 'string' && row.source_locator.trim())
const versionMismatch = computed(() => Boolean(loadedVersion.value && (loadedVersion.value !== props.expectedVersion || loadedDictionary.value !== props.dictionaryHash)))
const filtered = computed(() => readings.value.filter(row => props.cohort !== 'included' || row.relevance_status === 'included'))
const visible = computed(() => filtered.value.slice(0, shown.value))
const sourceParts = (judgment: Judgment) => judgment.source_locator.split(';').map(part => part.trim()).filter(Boolean)
const locationUrl = (row: Reading, locator: string) => readingUrl(row) + '#' + encodeURIComponent(locator)
const workUrl = (id: string) => withBase(`/database/?${new URLSearchParams({ work: id, relevance: 'all' })}`)
const labels: Record<string, string> = { included: '已纳入', candidate: '候选', manual_review: '分类待复核', excluded: '已排除' }
const load = async () => {
  const request = ++serial
  controller?.abort(); controller = new AbortController()
  loading.value = true; error.value = ''; readings.value = []; loadedVersion.value = ''; loadedDictionary.value = ''
  try {
    const response = await fetch(withBase('/api/v1/equipment/coverage-readings.json'), { signal: controller.signal, cache: 'no-cache' })
    if (!response.ok) throw new Error('unavailable')
    const data = await response.json()
    if (disposed || request !== serial) return
    if (data.schema_version !== '1' || data.dataset_version !== props.expectedVersion || data.dictionary_hash !== props.dictionaryHash) throw new Error('version')
    if (data.assurance !== 'self_attested_AI_reading_not_human_review' || !Array.isArray(data.records) || data.records.some((row: any) => !row.reading_id || !row.work_id || !row.title || row.reader_kind !== 'AI' || row.reading_status !== 'completed' || row.human_reviewed !== false || row.images_inspected !== false || row.supplementary_materials_inspected !== false || row.text_scope !== 'complete_available_article_text' || !readingSourceAllowed(row) || !Number.isInteger(row.checked_table_count) || row.checked_table_count < 0 || !validJudgments(row.findings_zh) || !validJudgments(row.limitations_zh))) throw new Error('invalid')
    if (new Set(data.records.map((row: Reading) => row.reading_id)).size !== data.records.length) throw new Error('invalid')
    readings.value = [...data.records].sort((a, b) => b.read_completed_at.localeCompare(a.read_completed_at) || a.work_id.localeCompare(b.work_id))
    loadedVersion.value = data.dataset_version; loadedDictionary.value = data.dictionary_hash
  } catch (cause) {
    if (!disposed && request === serial) error.value = cause instanceof Error && cause.message === 'version' ? '阅读记录与覆盖统计版本不一致，已停止组合展示，请刷新页面。' : '原文阅读记录暂不可读；这不代表尚无阅读记录。'
  } finally { if (!disposed && request === serial) loading.value = false }
}
onMounted(() => { void load() })
onBeforeUnmount(() => { disposed = true; serial++; controller?.abort() })
</script>

<template>
  <section class="fulltext-readings" aria-label="原文阅读发现与限制">
    <p class="reading-boundary">以下是AI对可用HTML文字的通读记录，非人工审稿或独立复现。图片、视频和外部补充材料仍未检查；文字和表格中的矛盾保留为待确认，不替作者补猜。</p>
    <p v-if="loading" role="status">正在读取原文发现与限制…</p>
    <div v-else-if="error || versionMismatch" role="alert"><p>{{ versionMismatch ? '阅读记录与覆盖统计版本不一致，当前记录状态未知。' : error }}</p><button type="button" @click="load">重新读取</button></div>
    <template v-else>
      <p class="reading-count" aria-live="polite">当前范围 {{ new Set(filtered.map(row => row.work_id)).size }} 项研究 · {{ filtered.length }} 份版本阅读记录</p>
      <article v-for="row in visible" :key="row.reading_id" class="reading-card">
        <header><h3><a :href="workUrl(row.work_id)">{{ row.title }}</a></h3><p>{{ labels[row.relevance_status] || '相关性状态待确认' }} · {{ row.version }} · {{ row.article_normalization === 'reading-packet-blocks-v1' ? '结构化全文' : '全文文字' }} · AI阅读 {{ eventDate(row.read_completed_at) }} · 已核对 {{ row.checked_table_count }} 个表格结构</p></header>
        <h4>正文新增发现</h4>
        <ul><li v-for="(claim, i) in row.findings_zh" :key="i">{{ claim.text_zh }} <span class="reading-citations"><a v-for="locator in sourceParts(claim)" :key="locator" :href="locationUrl(row, locator)" target="_blank" rel="noopener noreferrer">{{ locator }} ↗</a></span></li></ul>
        <div class="reading-limitations"><h4>限制与待确认</h4><ul><li v-for="(claim, i) in row.limitations_zh" :key="i">{{ claim.text_zh }} <span class="reading-citations"><a v-for="locator in sourceParts(claim)" :key="locator" :href="locationUrl(row, locator)" target="_blank" rel="noopener noreferrer">{{ locator }} ↗</a></span></li></ul></div>
        <a class="reading-original" :href="readingUrl(row)" target="_blank" rel="noopener noreferrer">打开所读原文 {{ row.version }} ↗</a>
      </article>
      <p v-if="!filtered.length">当前范围没有已登记的AI通读记录，未将正文采集或名称扫描当作已读。</p>
      <button v-if="visible.length < filtered.length" type="button" @click="shown += 12">再显示 12 份阅读记录（{{ visible.length }} / {{ filtered.length }}）</button>
    </template>
  </section>
</template>

<style scoped>
.fulltext-readings { min-width: 0; margin-top: 16px; }
.reading-boundary, .reading-count, .reading-card header p { color: var(--vp-c-text-2); font-size: 12px; line-height: 1.7; }
.reading-card { margin: 14px 0; padding: 18px; border: 1px solid var(--vp-c-divider); border-radius: 10px; overflow-wrap: anywhere; }
.reading-card h3 { margin: 0; font-size: 17px; line-height: 1.5; }
.reading-card h4 { margin: 14px 0 6px; font-size: 13px; }
.reading-card ul { margin: 0; padding-left: 19px; font-size: 13px; line-height: 1.8; }
.reading-card li { margin: 6px 0; }
.reading-card a { color: var(--vp-c-brand-1); }
.reading-limitations { border-left: 3px solid var(--vp-c-warning-1); padding: 0 12px; margin: 15px 0; }
.reading-citations { font-size: 11px; }
.reading-citations a { display: inline-block; margin-left: 6px; }
.reading-original { display: inline-block; font-size: 12px; margin-top: 10px; }
.fulltext-readings button { min-height: 44px; padding: 8px 12px; border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); color: var(--vp-c-text-1); cursor: pointer; }
.fulltext-readings :is(a, button):focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 3px; }
@media (max-width: 640px) { .reading-card { padding: 14px; } .reading-card h3 { font-size: 16px; } }
</style>
