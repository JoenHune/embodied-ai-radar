<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'

const clockLabel = (value: unknown, precision: 'day' | 'second'): string => {
  const pattern = precision === 'day' ? /^\d{4}-\d{2}-\d{2}$/ : /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/
  if (typeof value !== 'string' || !pattern.test(value)) return ''
  const date = new Date(precision === 'day' ? value + 'T00:00:00Z' : value)
  const width = precision === 'day' ? 10 : 19
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, width) !== value.slice(0, width)) return ''
  return eventDate(value, precision)
}

type Judgment = { text_zh: string; source_pages: number[] }
type Reading = { reading_id: string; work_id: string; title: string; relevance_status: string; source_url: string; edition_label: string; page_count: number; read_pages: number[]; visual_pages_checked: number[]; read_completed_at: string; checked_table_count: number; findings_zh: Judgment[]; limitations_zh: Judgment[] }
const props = defineProps<{ expectedVersion: string; dictionaryHash: string; cohort: 'all_works' | 'included' }>()
const records = ref<Reading[]>([])
const clockMetadata = ref<{ data_through?: string; source_review_as_of?: string }>({})
const analysisClock = computed(() => clockLabel(clockMetadata.value.data_through, 'day'))
const reviewClock = computed(() => clockLabel(clockMetadata.value.source_review_as_of, 'second'))
const loading = ref(true)
const error = ref('')
const loadedVersion = ref('')
const loadedDictionary = ref('')
const shown = ref(8)
let controller: AbortController | undefined
let disposed = false
let serial = 0
const filtered = computed(() => records.value.filter(row => props.cohort !== 'included' || row.relevance_status === 'included'))
const mismatch = computed(() => Boolean(loadedVersion.value && (loadedVersion.value !== props.expectedVersion || loadedDictionary.value !== props.dictionaryHash)))
const sourceAllowed = (value: unknown) => {
  try {
    const url = new URL(String(value))
    if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash || (url.port && url.port !== '443')) return false
    return (['arxiv.org', 'www.arxiv.org'].includes(url.hostname) && /^\/pdf\/[A-Za-z0-9./-]+v[1-9]\d*$/.test(url.pathname)) ||
      (['roboticsproceedings.org', 'www.roboticsproceedings.org'].includes(url.hostname) && /^\/rss\d+\/p\d+\.pdf$/.test(url.pathname)) ||
      (url.hostname === 'raw.githubusercontent.com' && /^\/mlresearch\/[^?#]+\.pdf$/.test(url.pathname)) ||
      (url.hostname === 'proceedings.mlr.press' && url.pathname.endsWith('.pdf'))
  } catch { return false }
}
const pagesValid = (pages: any, total: number, allowEmpty = false) => Array.isArray(pages) && (allowEmpty || pages.length > 0) && new Set(pages).size === pages.length && pages.every(page => Number.isInteger(page) && page >= 1 && page <= total)
const judgmentsValid = (rows: any, total: number) => Array.isArray(rows) && rows.length > 0 && rows.every(row => typeof row.text_zh === 'string' && row.text_zh.trim() && pagesValid(row.source_pages, total))
const pageUrl = (row: Reading, page: number) => `${row.source_url}#page=${page}`
const workUrl = (id: string) => withBase(`/database/?${new URLSearchParams({ work: id, relevance: 'all' })}`)
const relevanceLabels: Record<string, string> = { included: '已纳入', candidate: '候选', manual_review: '分类待复核', excluded: '已排除' }
const load = async () => {
  const request = ++serial
  controller?.abort(); controller = new AbortController()
  loading.value = true; error.value = ''; records.value = []; loadedVersion.value = ''; loadedDictionary.value = ''
  clockMetadata.value = {}
  try {
    const response = await fetch(withBase('/api/v1/equipment/coverage-pdf-readings.json'), { signal: controller.signal, cache: 'no-cache' })
    if (!response.ok) throw new Error('unavailable')
    const data = await response.json()
    if (disposed || request !== serial) return
    if (data.schema_version !== '1' || data.dataset_version !== props.expectedVersion || data.dictionary_hash !== props.dictionaryHash) throw new Error('version')
    if (data.source_format !== 'pdf' || data.assurance !== 'self_attested_AI_reading_not_human_review' || data.human_reviewed !== false || data.private_source_reverified !== false || !Array.isArray(data.records)) throw new Error('invalid')
    for (const row of data.records) {
      if (!row.reading_id || !row.work_id || !row.title || !row.edition_label || row.source_format !== 'pdf' || row.reader_kind !== 'AI' || row.reading_status !== 'completed' || row.human_reviewed !== false || row.supplementary_materials_inspected !== false || row.text_scope !== 'complete_available_pdf_text' || !sourceAllowed(row.source_url) || !Number.isInteger(row.page_count) || row.page_count <= 0 || !pagesValid(row.read_pages, row.page_count) || row.read_pages.length !== row.page_count || !pagesValid(row.visual_pages_checked, row.page_count, true) || !Number.isInteger(row.checked_table_count) || row.checked_table_count < 0 || !judgmentsValid(row.findings_zh, row.page_count) || !judgmentsValid(row.limitations_zh, row.page_count)) throw new Error('invalid')
    }
    if (new Set(data.records.map((row: Reading) => row.reading_id)).size !== data.records.length) throw new Error('invalid')
    records.value = [...data.records].sort((a, b) => b.read_completed_at.localeCompare(a.read_completed_at) || a.work_id.localeCompare(b.work_id))
    loadedVersion.value = data.dataset_version; loadedDictionary.value = data.dictionary_hash
    clockMetadata.value = { data_through: data.data_through, source_review_as_of: data.source_review_as_of }
  } catch (cause) {
    if (!disposed && request === serial) error.value = cause instanceof Error && cause.message === 'version' ? 'PDF阅读记录与覆盖统计版本不一致，已停止混合展示。' : 'PDF阅读记录暂不可读，当前状态未知；不显示为零。'
  } finally { if (!disposed && request === serial) loading.value = false }
}
onMounted(() => { void load() })
onBeforeUnmount(() => { disposed = true; serial++; controller?.abort() })
</script>

<template>
  <section class="pdf-readings" aria-label="PDF原文阅读发现与限制">
    <p class="pdf-boundary">PDF原文按文件页码定位，正式会议版不伪造arXiv版本号。以下是AI文字阅读记录，不是人工审稿或独立复现；只看首页、取得文件或提取文字都不计为通读。与HTML可能对应同一研究，数量不能直接相加。</p>
    <p v-if="loading" role="status">正在读取PDF原文发现…</p>
    <div v-else-if="error || mismatch" role="alert"><p>{{ mismatch ? 'PDF阅读记录版本已过期，当前状态未知。' : error }}</p><button type="button" @click="load">重新读取</button></div>
    <template v-else>
      <p v-if="reviewClock" class="pdf-meta">语料分析截至 {{ analysisClock || '日期待核验' }} · 来源/阅读核验记录可见截至 {{ reviewClock }}</p>
      <p class="pdf-count" aria-live="polite">当前范围 {{ new Set(filtered.map(row => row.work_id)).size }} 项研究 · {{ filtered.length }} 份PDF阅读记录</p>
      <article v-for="row in filtered.slice(0, shown)" :key="row.reading_id">
        <h3><a :href="workUrl(row.work_id)">{{ row.title }}</a></h3>
        <p class="pdf-meta">{{ relevanceLabels[row.relevance_status] || '相关性状态待确认' }} · {{ row.edition_label }} · {{ row.page_count }} 页文字已读 · 已查看 {{ row.visual_pages_checked.length }} / {{ row.page_count }} 页版面 · 已核对 {{ row.checked_table_count }} 张表</p>
        <p class="pdf-meta">AI阅读 {{ eventDate(row.read_completed_at) }} · 外部视频与补充材料未检查；未列入版面检查的页不声称图片已看。</p>
        <h4>正文新增发现</h4>
        <ul><li v-for="(claim, i) in row.findings_zh" :key="i">{{ claim.text_zh }} <a v-for="page in claim.source_pages" :key="page" :href="pageUrl(row, page)" target="_blank" rel="noopener noreferrer">PDF第{{ page }}页 ↗</a></li></ul>
        <div class="pdf-limitations"><h4>限制与待确认</h4><ul><li v-for="(claim, i) in row.limitations_zh" :key="i">{{ claim.text_zh }} <a v-for="page in claim.source_pages" :key="page" :href="pageUrl(row, page)" target="_blank" rel="noopener noreferrer">PDF第{{ page }}页 ↗</a></li></ul></div>
        <a class="pdf-original" :href="row.source_url" target="_blank" rel="noopener noreferrer">打开所读官方PDF ↗</a>
      </article>
      <p v-if="!filtered.length">当前范围尚无已登记PDF通读记录；文件已取得不等于已读。</p>
      <button v-if="shown < filtered.length" type="button" @click="shown += 8">再显示8份PDF阅读记录（{{ Math.min(shown, filtered.length) }} / {{ filtered.length }}）</button>
    </template>
  </section>
</template>

<style scoped>
.pdf-readings { min-width: 0; margin-top: 16px; }
.pdf-boundary, .pdf-count, .pdf-meta { font-size: 12px; color: var(--vp-c-text-2); line-height: 1.8; }
.pdf-readings article { margin: 14px 0; padding: 18px; border: 1px solid var(--vp-c-divider); border-radius: 10px; overflow-wrap: anywhere; }
.pdf-readings h3 { margin: 0; font-size: 17px; line-height: 1.5; }
.pdf-readings h4 { margin: 14px 0 6px; font-size: 13px; }
.pdf-readings ul { margin: 0; padding-left: 19px; font-size: 13px; line-height: 1.8; }
.pdf-readings li { margin: 6px 0; }
.pdf-readings a { color: var(--vp-c-brand-1); }
.pdf-readings li a { display: inline-block; font-size: 11px; margin-left: 6px; }
.pdf-limitations { border-left: 3px solid var(--vp-c-warning-1); padding: 0 12px; margin: 15px 0; }
.pdf-original { display: inline-block; font-size: 12px; margin-top: 10px; }
.pdf-readings button { min-height: 44px; padding: 8px 12px; border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); color: var(--vp-c-text-1); cursor: pointer; }
.pdf-readings :is(a, button):focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 3px; }
@media (max-width: 640px) { .pdf-readings article { padding: 14px; } .pdf-readings h3 { font-size: 16px; } }
</style>
