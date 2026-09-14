<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { withBase } from 'vitepress'
import ResearchCard from './ResearchCard.vue'
import { directionShortNames, filterResearchCards } from '../lib/research-card.mjs'

const props = withDefaults(defineProps<{ title?: string; month?: string; direction?: string; organizationSlug?: string; limit?: number; controls?: boolean; lockedMonth?: boolean }>(), { title: '研究与企业报告', month: '', direction: '', organizationSlug: '', limit: 9, controls: true, lockedMonth: false })
const emit = defineEmits<{ direction: [value: string]; month: [value: string] }>()
const manifest = ref<any>(null)
const rows = ref<any[]>([])
const selectedMonth = ref(props.month || (props.organizationSlug ? 'organization' : 'featured'))
const selectedDirection = ref(props.direction)
const selectedKind = ref('all')
const page = ref(0)
const loading = ref(false)
const error = ref('')
let disposed = false
let serial = 0
const filtered = computed(() => filterResearchCards(rows.value, { direction: selectedDirection.value, kind: selectedKind.value }))
const visible = computed(() => filtered.value.slice(page.value * props.limit, (page.value + 1) * props.limit))
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / props.limit)))
const monthValid = (value: string) => value === 'featured' || value === 'organization' && Boolean(props.organizationSlug) || manifest.value?.months.some((row: any) => row.month === value)
const writeState = () => {
  const url = new URL(window.location.href)
  for (const [key, value, fallback] of [['feed_month', selectedMonth.value, props.organizationSlug ? 'organization' : 'featured'], ['feed_direction', selectedDirection.value, ''], ['feed_kind', selectedKind.value, 'all']]) {
    if (value === fallback) url.searchParams.delete(key)
    else url.searchParams.set(key, value)
  }
  if (url.href !== window.location.href) window.history.pushState(window.history.state, '', url)
}
const load = async () => {
  if (!manifest.value) return
  const request = ++serial
  loading.value = true
  error.value = ''
  rows.value = []
  page.value = 0
  const resource = selectedMonth.value === 'organization' ? `organizations/${props.organizationSlug}.json` : selectedMonth.value === 'featured' ? 'featured.json' : `monthly/${selectedMonth.value}.json`
  try {
    const response = await fetch(withBase(`/api/v1/visual-feed/${resource}`))
    if (!response.ok) throw new Error('feed unavailable')
    const result = await response.json()
    if (disposed || request !== serial) return
    if (result.schema_version !== '1' || result.dataset_version !== manifest.value.dataset_version || !Array.isArray(result.rows)) throw new Error('feed version mismatch')
    let nextRows = result.rows
    if (props.organizationSlug && selectedMonth.value !== 'organization') {
      const scopeResponse = await fetch(withBase(`/api/v1/visual-feed/organizations/${props.organizationSlug}.json`))
      if (!scopeResponse.ok) throw new Error('organization scope unavailable')
      const scope = await scopeResponse.json()
      if (scope.dataset_version !== manifest.value.dataset_version || !Array.isArray(scope.rows)) throw new Error('organization scope mismatch')
      const allowed = new Set(scope.rows.map((row: any) => row.work_id))
      nextRows = nextRows.filter((row: any) => allowed.has(row.work_id))
    }
    if (disposed || request !== serial) return
    rows.value = nextRows
    page.value = 0
  } catch { if (!disposed && request === serial) error.value = '图文内容暂时无法读取；原始研究库仍可访问。' }
  finally { if (!disposed && request === serial) loading.value = false }
}
const selectMonth = () => { writeState(); emit('month', selectedMonth.value); void load() }
const selectDirection = () => { page.value = 0; writeState(); emit('direction', selectedDirection.value) }
const selectKind = (kind: string) => { selectedKind.value = kind; page.value = 0; writeState() }
const restore = () => {
  const params = new URLSearchParams(window.location.search)
  const month = props.month || params.get('feed_month') || (props.organizationSlug ? 'organization' : 'featured')
  selectedMonth.value = monthValid(month) ? month : (props.organizationSlug ? 'organization' : 'featured')
  selectedDirection.value = props.direction || (Object.hasOwn(directionShortNames, params.get('feed_direction') || '') ? params.get('feed_direction')! : '')
  selectedKind.value = ['all', 'papers', 'reports', 'strategic'].includes(params.get('feed_kind') || '') ? params.get('feed_kind')! : 'all'
  void load()
}
const initialize = async () => {
  try {
    const response = await fetch(withBase('/api/v1/visual-feed/index.json'))
    if (!response.ok) throw new Error('missing feed manifest')
    const value = await response.json()
    if (!disposed) { manifest.value = value; restore() }
  } catch { if (!disposed) error.value = '图文目录暂时无法读取。' }
}
watch(() => props.month, value => { const next = value || (props.organizationSlug ? 'organization' : 'featured'); if (manifest.value && monthValid(next) && next !== selectedMonth.value) { selectedMonth.value = next; void load() } })
watch(() => props.direction, value => { selectedDirection.value = value; page.value = 0 })
watch(() => props.organizationSlug, () => { if (manifest.value) { selectedMonth.value = props.month || (props.organizationSlug ? 'organization' : 'featured'); void load() } })
onMounted(() => { void initialize(); window.addEventListener('popstate', restore) })
onBeforeUnmount(() => { disposed = true; serial++; window.removeEventListener('popstate', restore) })
</script>

<template>
  <section class="research-feed" aria-label="研究图文信息流">
    <header class="research-feed-heading"><div><p class="research-feed-kicker">RESEARCH, IN CONTEXT</p><h2>{{ title }}</h2><p>{{ selectedMonth === 'featured' ? '有官方配图的代表性工作；不是研究排名。按月浏览可查看完整收录。' : selectedMonth === 'organization' ? '近 12 个完整月，已核验归属到该组织的研究。' : `${selectedMonth} · 以首次公开月份组织；图片和标题直达原文。` }}</p></div><a :href="withBase('/database/')">完整研究库 ↗</a></header>
    <div v-if="controls" class="research-feed-controls"><div class="research-feed-tabs" aria-label="内容类型"><button v-for="item in [['all','研究与报告'],['papers','研究论文'],['reports','企业报告'],['strategic','战略观察']]" :key="item[0]" type="button" :aria-pressed="selectedKind === item[0]" @click="selectKind(item[0])">{{ item[1] }}</button></div><label><span class="sr-only">图文流月份</span><select v-model="selectedMonth" :disabled="lockedMonth" @change="selectMonth"><option v-if="organizationSlug" value="organization">该组织 · 近12月</option><option value="featured">图文精选</option><option v-for="row in [...(manifest?.months || [])].reverse()" :key="row.month" :value="row.month">{{ row.month }}{{ row.status === 'provisional' ? ' · 暂行' : '' }}</option></select></label><label><span class="sr-only">图文流方向</span><select v-model="selectedDirection" @change="selectDirection"><option value="">全部方向</option><option v-for="(name, code) in directionShortNames" :key="code" :value="code">{{ name }}</option></select></label></div>
    <p v-if="error" class="v3-error" role="alert">{{ error }} <button type="button" @click="initialize">重试</button></p>
    <p v-if="loading" role="status">正在读取研究与原文入口…</p>
    <p v-else class="research-feed-count" aria-live="polite">{{ filtered.length }} 项{{ selectedDirection ? ` · 主方向：${directionShortNames[selectedDirection]}` : '' }}{{ selectedMonth === 'featured' ? ' · 官方配图样本' : '' }}</p>
    <div class="research-feed-grid"><ResearchCard v-for="work in visible" :key="work.work_id" :work="work" /></div>
    <p v-if="!loading && !error && !filtered.length" class="v3-empty">当前筛选下未登记相关条目。可切换月份或在完整研究库中继续查看。</p>
    <nav v-if="pages > 1" class="research-feed-pagination" aria-label="图文流分页"><button type="button" :disabled="page === 0" @click="page--">上一页</button><span>{{ page + 1 }} / {{ pages }}</span><button type="button" :disabled="page + 1 >= pages" @click="page++">下一页</button></nav>
  </section>
</template>

<style scoped>
.research-feed { margin: 36px 0; scroll-margin-top: 90px; }
.research-feed-heading { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 20px; }
.research-feed-heading h2 { margin: 4px 0 8px; font-size: 28px; letter-spacing: -.02em; }
.research-feed-heading p { font-size: 14px; color: var(--vp-c-text-2); line-height: 1.6; margin: 0; }
.research-feed-heading .research-feed-kicker { font-size: 11px; letter-spacing: .15em; font-weight: 600; }
.research-feed-heading > a { flex: none; font-size: 14px; }
.research-feed-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 12px; }
.research-feed-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin-right: auto; }
.research-feed-tabs button { padding: 8px 12px; border-radius: 6px; color: var(--vp-c-text-2); font-size: 14px; }
.research-feed-tabs button[aria-pressed='true'] { color: var(--vp-c-brand-1); background: var(--vp-c-brand-soft); }
.research-feed-controls select { max-width: 100%; border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); border-radius: 6px; color: var(--vp-c-text-1); padding: 8px 10px; font-size: 14px; }
.research-feed-count { font-size: 13px; color: var(--vp-c-text-2); margin: 8px 0 16px; }
.research-feed-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; align-items: start; }
.research-feed-pagination { display: flex; gap: 20px; align-items: center; justify-content: center; margin: 24px 0; font-size: 14px; }
.research-feed-pagination button { padding: 8px 14px; border: 1px solid var(--vp-c-divider); border-radius: 6px; }
.research-feed-pagination button:disabled { opacity: .45; }
@media (max-width: 1050px) { .research-feed-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 650px) { .research-feed-grid { grid-template-columns: 1fr; } .research-feed-heading { display: block; } .research-feed-heading > a { display: inline-block; margin-top: 12px; } .research-feed-controls label { flex: 1; min-width: 0; } .research-feed-controls select { width: 100%; font-size: 16px; } .research-feed-tabs { width: 100%; } }
</style>
