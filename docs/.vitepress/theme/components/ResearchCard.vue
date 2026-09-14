<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import SourceImage from './SourceImage.vue'
import { useVisualMedia } from '../composables/useVisualMedia'
import { useEquipmentEvidence } from '../composables/useEquipmentEvidence'
import { eventDate } from '../lib/dates'
import { directionShortNames, originalSourceUrl, researchOutputLabel } from '../lib/research-card.mjs'
import { publicationRecords, statusNotices } from '../lib/work-status.mjs'

const props = withDefaults(defineProps<{ work: any; compact?: boolean; detailButton?: boolean }>(), { compact: false, detailButton: false })
const emit = defineEmits<{ details: [workId: string] }>()
const media = useVisualMedia()
const equipment = useEquipmentEvidence()
const hardware = computed<any[]>(() => props.work.hardware_usage || equipment.value[props.work.work_id] || [])
const hardwareNames = computed(() => [...new Set(hardware.value.map(row => row.name))].slice(0, 3))
const usageLabels: Record<string, string> = { real_robot: '真机使用', simulated_robot: '仿真使用', training_compute: '训练算力', inference_compute: '推理算力', control_compute: '控制计算', model_fitting_compute: '模型参数拟合', experiment_compute: '实验计算（环节未细分）', data_collection: '数据采集', sensing: '感知', dataset_source: '数据来源' }
const settingLabels: Record<string, string> = { real: '真实设备', simulation: '仿真环境', dataset: '数据集', unknown: '环境未明确' }
const asset = computed(() => media.value[props.work.work_id])
const original = computed(() => originalSourceUrl(props.work))
const report = computed(() => props.work.output_types?.includes('technical_report') || props.work.manifestations?.some((row: any) => row.kind === 'technical_report'))
const blocked = computed(() => props.work.research_status?.validation_eligible === false || props.work.research_validation_eligible === false)
const publications = computed(() => publicationRecords(props.work))
const notices = computed(() => statusNotices(props.work))
const relevanceLabels: Record<string, string> = { candidate: '候选', manual_review: '待复核', excluded: '已排除' }
const details = computed(() => withBase(`/database/?${new URLSearchParams({ work: props.work.work_id, relevance: 'all' })}`))
</script>

<template>
  <article class="research-card" :class="{ compact, 'has-image': asset, 'is-report': report, 'is-blocked': blocked }">
    <a v-if="asset && original" class="research-card-image" :href="original" target="_blank" rel="noopener noreferrer" :aria-label="`阅读原文：${work.title}`"><SourceImage :entity-id="work.work_id" :name="work.title" :interactive="false" /><span>{{ asset.contains_generated_visuals ? '含模型生成示意' : report ? '企业报告' : '研究配图' }} ↗</span></a>
    <div class="research-card-copy">
      <div class="research-card-meta"><span :class="{ 'report-label': report }">{{ researchOutputLabel(work) }}</span><time>首次公开 {{ eventDate(work.first_public_date, work.first_public_date_precision) }}</time><span v-if="relevanceLabels[work.relevance_status]">{{ relevanceLabels[work.relevance_status] }}</span><span v-if="work.text_notice">{{ work.text_notice }}</span></div>
      <div v-if="notices.length" class="research-card-alert" :class="{ 'status-not-blocking': !blocked }"><p v-for="(notice, i) in notices" :key="i"><strong>{{ notice.label }}</strong><span v-if="notice.date"> · {{ eventDate(notice.date, notice.date_precision) }}</span><span v-if="blocked"> · 结果不作验证</span><br v-if="notice.summary" />{{ notice.summary }} <a v-if="notice.url" :href="notice.url" target="_blank" rel="noopener noreferrer">官方通知 ↗</a></p></div>
      <ul v-if="publications.length" class="research-card-publications" aria-label="会议与期刊收录状态"><li v-for="publication in publications" :key="publication.venue"><a :href="publication.url" target="_blank" rel="noopener noreferrer"><strong>{{ publication.venue }}</strong> · {{ publication.state }} ↗</a></li></ul>
      <h3><a v-if="original" :href="original" target="_blank" rel="noopener noreferrer">{{ work.title_zh || work.title }}</a><span v-else>{{ work.title_zh || work.title }}</span></h3>
      <p v-if="work.title_zh && work.title_zh !== work.title" class="research-original-title">{{ work.title }}</p>
      <p v-if="work.summary" class="research-card-summary">{{ work.summary }}</p>
      <div class="research-card-topics"><a v-for="direction in (work.directions || [work.primary_direction]).filter(Boolean).slice(0, 3)" :key="direction" :href="withBase(`/database/?directions=${direction}`)">{{ directionShortNames[direction] || direction }}</a></div>
      <p v-if="work.organizations?.length" class="research-card-organizations"><template v-for="(organization, i) in work.organizations.slice(0, 3)" :key="organization.organization_id || organization.name"><span v-if="i"> · </span><a v-if="organization.organization_id" :href="withBase(`/database/?organizations=${encodeURIComponent(organization.organization_id)}`)">{{ organization.name }}</a><span v-else>{{ organization.name }}</span></template></p>
      <div v-if="work.people?.length" class="research-card-people"><a v-for="person in work.people.slice(0, 3)" :key="person.person_id" :href="withBase(`/organizations/people/?person=${person.slug}`)"><SourceImage :entity-id="person.person_id" :name="person.name" portrait /><span>{{ person.name }}</span></a></div>
      <p v-if="report || work.company_self_report" class="research-card-boundary">公司自行披露；不等于独立验证。</p>
      <details v-if="hardware.length" class="research-hardware"><summary>研究设备 · {{ hardwareNames.join(' · ') }}{{ new Set(hardware.map(row => row.hardware_id)).size > 3 ? ' 等' : '' }}</summary><ul><li v-for="usage in hardware" :key="usage.usage_id"><a :href="withBase(`/hardware/?device=${encodeURIComponent(usage.hardware_id)}`)">{{ usage.name }}</a> · {{ usageLabels[usage.role] || usage.role }} · {{ settingLabels[usage.setting] || usage.setting }}<strong v-if="usage.usage_scope === 'baseline'"> · 仅对照基线</strong><strong v-if="usage.usage_scope === 'calibration'"> · 校准用途</strong><p>{{ usage.statement }}</p><small v-if="usage.configuration">{{ usage.configuration }} · </small><a :href="usage.source_url" target="_blank" rel="noopener noreferrer">原文证据 ↗</a></li></ul><small>只登记有直接证据的设备；设备使用不等同于闭环自主能力验证。</small></details>
      <footer><a v-if="original" class="research-original-action" :href="original" target="_blank" rel="noopener noreferrer">{{ report ? '阅读报告' : '阅读原文' }} ↗</a><button v-if="detailButton" type="button" @click="emit('details', work.work_id)">证据与版本</button><a v-else :href="details">证据与版本</a></footer>
      <details v-if="asset" class="research-image-source"><summary>配图来源</summary><a :href="asset.source_page" target="_blank" rel="noopener noreferrer">{{ asset.credit || '官方项目或发布页' }}</a><p>{{ asset.caption || '原网站配图' }} · 使用许可{{ asset.rights_status === 'unknown' ? '未声明' : '请查看原站说明' }}；配图不提升研究证据等级。</p><p>配图核验 {{ asset.observed_at?.slice(0, 10) }}；当前素材不代表历史版本。</p></details>
    </div>
  </article>
</template>

<style scoped>
.research-card { min-width: 0; display: flex; flex-direction: column; background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 14px; overflow: hidden; }
.research-card-image { position: relative; display: block; aspect-ratio: 16 / 9; overflow: hidden; background: var(--vp-c-bg-soft); }
.research-card-image :deep(.source-image) { height: 100%; width: 100%; }
.research-card-image > span { position: absolute; bottom: 10px; left: 12px; padding: 4px 8px; background: var(--vp-c-bg); color: var(--vp-c-text-1); border-radius: 4px; font-size: 12px; }
.research-card-copy { display: flex; flex-direction: column; flex: 1; padding: 20px; }
.research-card-meta { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: baseline; color: var(--vp-c-text-2); font-size: 13px; margin-bottom: 10px; }
.research-card-meta .report-label { color: var(--vp-c-brand-1); }
.research-card h3 { font-size: 19px; line-height: 1.45; margin: 0 0 10px; font-weight: 600; letter-spacing: -.015em; }
.research-card h3 a { color: var(--vp-c-text-1); }
.research-card h3 a:hover { color: var(--vp-c-brand-1); }
.research-card-summary { font-size: 15px; line-height: 1.65; margin: 0 0 14px; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; color: var(--vp-c-text-2); }
.research-original-title { font-size: 13px; color: var(--vp-c-text-2); margin: 0 0 10px; }
.research-card-topics { display: flex; flex-wrap: wrap; gap: 7px; margin: 2px 0 10px; }
.research-card-topics a { background: var(--vp-c-bg-soft); color: var(--vp-c-text-2); padding: 3px 7px; font-size: 12px; border-radius: 4px; }
.research-card-organizations, .research-card-boundary { color: var(--vp-c-text-2); font-size: 13px; line-height: 1.6; margin: 4px 0 10px; }
.research-card-organizations a { color: inherit; }
.research-card-people { display: flex; flex-wrap: wrap; gap: 12px; margin: 4px 0 14px; }
.research-card-people > a { display: flex; align-items: center; gap: 6px; color: var(--vp-c-text-2); font-size: 12px; }
.research-card-people :deep(.portrait) { width: 26px; height: 26px; border-radius: 50%; }
.research-card-people :deep(.portrait-fallback span) { font-size: 10px; }
.research-card footer { display: flex; align-items: center; flex-wrap: wrap; gap: 18px; padding-top: 14px; margin-top: auto; font-size: 14px; }
.research-original-action { font-weight: 600; }
.research-image-source { margin-top: 12px; color: var(--vp-c-text-2); font-size: 12px; }
.research-image-source p { line-height: 1.5; }
.research-card-alert { background: var(--vp-c-danger-soft); color: var(--vp-c-danger-1); font-size: 14px; padding: 10px; margin-bottom: 12px; }
.research-card-alert.status-not-blocking { background: var(--vp-c-warning-soft); color: var(--vp-c-text-1); }
.research-card-alert p { margin: 0 0 6px; line-height: 1.6; }
.research-card-publications { list-style: none; padding: 10px 12px; margin: 0 0 14px; border-left: 3px solid var(--vp-c-brand-1); background: var(--vp-c-bg-soft); font-size: 14px; line-height: 1.6; }
.research-card-publications li + li { margin-top: 5px; }
.research-hardware { margin: 8px 0 12px; font-size: 12px; color: var(--vp-c-text-2); overflow-wrap: anywhere; }
.research-hardware summary { cursor: pointer; line-height: 1.6; }
.research-hardware ul { padding-left: 18px; }
.research-hardware li { margin: 10px 0; }
.research-hardware p { margin: 3px 0; line-height: 1.6; }
.compact.has-image { display: grid; grid-template-columns: minmax(160px, .8fr) minmax(0, 1.5fr); }
.compact .research-card-image { aspect-ratio: auto; min-height: 200px; }
.compact h3 { font-size: 18px; }
@media (max-width: 600px) { .compact.has-image { display: flex; } .compact .research-card-image { aspect-ratio: 16 / 9; min-height: 0; } .research-card-copy { padding: 16px; } }
</style>
