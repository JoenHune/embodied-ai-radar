<script setup lang="ts">
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'

defineProps<{ device: any; categoryLabel?: string; expanded?: boolean; provisionalMonth?: string }>()
const emit = defineEmits<{ papers: [hardwareId: string]; sources: [open: boolean] }>()
const roleLabels: Record<string, string> = { real_robot: '真机使用', simulated_robot: '仿真机器人', training_compute: '训练算力', inference_compute: '推理算力', control_compute: '控制计算', model_fitting_compute: '模型参数拟合', experiment_compute: '实验计算（环节未细分）', data_collection: '数据采集', sensing: '感知', dataset_source: '数据来源' }
const settingLabels: Record<string, string> = { real: '真实设备', simulation: '仿真环境', dataset: '数据集', unknown: '环境未说明' }
const scopeLabels: Record<string, string> = { baseline: '仅对照基线', calibration: '仅标定 / 校准', replay: '仅轨迹回放', replay_only: '仅轨迹回放' }
const validationLabels: Record<string, string> = { closed_loop_real: '真机闭环', replay_only_real: '真机仅回放', simulation_only: '仅仿真', unclear: '验证方式未明确' }
const validationContextLabels: Record<string, string> = { real_to_sim_trajectory_replay: '真实轨迹采集→仿真回放，不等于策略真机闭环', real_robot_closed_loop: '真机闭环', real_robot_closed_loop_offline_reference: '真机闭环；离线参考', real_robot_closed_loop_with_operator_supervision: '真机闭环；操作员监督', real_robot_trajectory_replay: '真机轨迹回放，不等于真机闭环策略验证', simulation_and_real_trajectory_replay: '仿真与真机轨迹回放，不等于真机闭环策略验证', simulation_and_real_robot_closed_loop: '仿真与真机闭环', simulation_only: '仅仿真' }
const hasContext = (device: any, contexts: string[]) => device.sources.some((source: any) => source.usages.some((usage: any) => contexts.includes(usage.validation_context)))
const roleWorkCount = (device: any, role: string) => device.sources.filter((source: any) => source.usages.some((usage: any) => usage.role === role)).length
const computeRoles = ['training_compute', 'inference_compute', 'control_compute', 'model_fitting_compute', 'experiment_compute']
const publicUrl = (value: unknown): string | undefined => typeof value === 'string' && /^https?:\/\//i.test(value) ? value : undefined
const workUrl = (source: any) => publicUrl(source.original_url) || withBase(`/database/?${new URLSearchParams({ work: source.work_id, relevance: 'all' })}`)
const configurationText = (value: unknown) => value == null || value === '' ? '' : typeof value === 'string' ? value : JSON.stringify(value)
</script>

<template>
  <article class="hardware-model" :class="{ 'is-unresolved': device.identity_level !== 'model_specified' }" tabindex="-1">
    <header>
      <div class="model-identity"><h3>{{ device.name }}</h3><p>{{ categoryLabel || device.category }}<span v-if="device.vendor"> · {{ device.vendor }}</span></p></div>
      <div class="model-frequency"><strong>{{ device.work_count }}</strong><span>项研究使用</span></div>
    </header>
    <p v-if="device.identity_level !== 'model_specified'" class="identity-boundary"><strong>{{ device.identity_level === 'family_only' ? '系列 · 具体版本待明确' : '型号未公开' }}</strong> · 不计入具体型号榜，不根据当前产品名补推代际。</p>
    <div class="model-settings"><template v-if="device.category === 'compute_platform'"><template v-for="role in computeRoles" :key="role"><span v-if="roleWorkCount(device, role)">{{ roleLabels[role] }} {{ roleWorkCount(device, role) }}</span></template><span v-if="!computeRoles.some(role => roleWorkCount(device, role))">计算设备使用 {{ device.work_count }}</span></template><template v-else><span>真机 / 真实设备 {{ device.real_work_count }}</span><span>仿真 {{ device.simulation_work_count }}</span></template><span v-if="device.baseline_work_count">含对照基线 {{ device.baseline_work_count }}</span><span v-if="device.calibration_work_count">含校准 {{ device.calibration_work_count }}</span><span v-if="hasContext(device, ['real_robot_trajectory_replay', 'simulation_and_real_trajectory_replay'])">含真机轨迹回放</span><span v-if="hasContext(device, ['real_robot_closed_loop_offline_reference'])">含离线参考条件</span></div>
    <div class="model-actions"><button type="button" @click="emit('papers', device.hardware_id)">查看 {{ device.work_count }} 项研究卡片</button><a v-if="publicUrl(device.official_url)" :href="device.official_url" target="_blank" rel="noopener noreferrer">身份依据 ↗</a></div>
    <details class="model-sources" :open="expanded" @toggle="emit('sources', ($event.target as HTMLDetailsElement).open)">
      <summary>完整论文出处与使用证据 · {{ device.sources.length }} 项研究 / {{ device.source_count }} 条来源</summary>
      <p v-if="device.aliases?.length" class="model-aliases">检索别名：{{ device.aliases.join(' · ') }}</p>
      <ol class="source-list">
        <li v-for="source in device.sources" :key="source.work_id">
          <h4><a :href="workUrl(source)" :target="publicUrl(source.original_url) ? '_blank' : undefined" rel="noopener noreferrer">{{ source.title || source.work_id }}</a></h4>
          <p class="source-date">首次公开 {{ eventDate(source.first_public_date, source.first_public_date_precision) }}<span v-if="source.first_public_date?.slice(0, 7) === provisionalMonth" class="provisional-label">暂行月份</span></p>
          <section v-for="(usage, i) in source.usages" :key="usage.usage_id || i" class="source-usage">
            <p class="usage-meta"><span>{{ roleLabels[usage.role] || usage.role || '用途未明确' }}</span><span>{{ settingLabels[usage.setting] || settingLabels.unknown }}</span><strong v-if="scopeLabels[usage.usage_scope]">{{ scopeLabels[usage.usage_scope] }}</strong><strong v-if="validationLabels[usage.validation]">{{ validationLabels[usage.validation] }}</strong></p>
            <p v-if="usage.validation_context" class="validation-context">实验背景：{{ validationContextLabels[usage.validation_context] || usage.validation_context }}</p>
            <p class="source-statement">{{ usage.statement || '原文说明待补充' }}</p>
            <p v-if="configurationText(usage.configuration)" class="source-configuration">配置 / 条件：{{ configurationText(usage.configuration) }}</p>
            <p class="source-location">原文定位：{{ usage.source_locator || '未提供定位' }}<span v-if="usage.reviewed_at"> · 复核 {{ eventDate(usage.reviewed_at) }}</span><span v-else-if="usage.observed_at"> · 记录日期 {{ eventDate(usage.observed_at) }}</span></p>
            <p v-if="usage.reviewed_at && usage.observed_at" class="source-location">来源记录 {{ eventDate(usage.observed_at) }}<span v-if="usage.extends_review_id"> · 后续增补复核，原记录保留</span></p>
            <a v-if="publicUrl(usage.source_url)" class="source-url" :href="usage.source_url" target="_blank" rel="noopener noreferrer">{{ usage.source_url }} ↗</a>
            <p v-else class="source-location">原文链接暂未提供，不从设备名称补猜。</p>
          </section>
        </li>
      </ol>
      <p class="source-note">保留原文中的基线、标定、数据采集或轨迹回放条件；“真机使用”不自动等于自主闭环验证。</p>
    </details>
  </article>
</template>

<style scoped>
.hardware-model { min-width: 0; border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 18px 20px; background: var(--vp-c-bg); scroll-margin-top: 100px; }
.hardware-model :is(h3, h4, p, a, span, summary) { overflow-wrap: anywhere; }
.hardware-model > header { display: flex; gap: 20px; align-items: flex-start; justify-content: space-between; }
.model-identity { min-width: 0; }
.model-identity h3 { font-size: 20px; margin: 0 0 6px; line-height: 1.4; }
.model-identity p { margin: 0; font-size: 12px; color: var(--vp-c-text-2); }
.model-frequency { display: flex; flex-direction: column; align-items: flex-end; flex: none; }
.model-frequency strong { font-size: 30px; line-height: 1.2; font-weight: 600; color: var(--vp-c-brand-1); }
.model-frequency span { margin-top: 4px; font-size: 12px; color: var(--vp-c-text-2); }
.model-settings, .model-actions, .usage-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 7px 15px; }
.model-settings { margin: 14px 0 6px; font-size: 12px; color: var(--vp-c-text-2); }
.model-settings span { background: var(--vp-c-bg-soft); border-radius: 4px; padding: 3px 7px; }
.model-actions { font-size: 13px; }
.model-actions button { cursor: pointer; min-height: 44px; padding: 5px 0; color: var(--vp-c-brand-1); }
.model-actions a { display: inline-flex; align-items: center; min-height: 44px; }
.model-sources { border-top: 1px solid var(--vp-c-divider); margin-top: 6px; }
.model-sources summary { cursor: pointer; padding: 12px 0 2px; min-height: 44px; font-size: 13px; line-height: 1.7; }
.identity-boundary { margin: 12px 0 4px; color: var(--vp-c-text-2); font-size: 12px; line-height: 1.7; }
.identity-boundary strong { font-weight: 500; color: var(--vp-c-text-1); background: var(--vp-c-warning-soft); padding: 3px 6px; border-radius: 4px; }
.hardware-model.is-unresolved { border-left: 3px dashed var(--vp-c-warning-1); }
.model-aliases, .source-note { font-size: 12px; color: var(--vp-c-text-2); line-height: 1.7; }
.source-list { padding-left: 21px; margin: 14px 0 0; }
.source-list > li { padding: 0 0 18px 4px; margin-bottom: 18px; border-bottom: 1px solid var(--vp-c-divider); }
.source-list > li:last-child { margin-bottom: 0; }
.source-list h4 { font-size: 15px; line-height: 1.6; margin: 0 0 5px; }
.source-date, .source-location, .source-configuration { font-size: 12px; line-height: 1.7; color: var(--vp-c-text-2); margin: 5px 0; }
.source-usage { padding: 10px 13px; margin-top: 10px; background: var(--vp-c-bg-soft); border-radius: 6px; }
.usage-meta { font-size: 12px; margin: 0; color: var(--vp-c-text-2); }
.usage-meta strong { color: var(--vp-c-text-1); font-weight: 600; }
.source-statement { font-size: 13px; line-height: 1.75; margin: 8px 0; }
.validation-context { font-size: 12px; line-height: 1.7; margin: 7px 0; color: var(--vp-c-text-1); }
.source-url { display: block; font-size: 12px; line-height: 1.7; margin-top: 5px; }
.provisional-label { margin-left: 7px; padding: 2px 5px; border: 1px dashed var(--vp-c-warning-1); border-radius: 3px; }
.hardware-model :is(button, a, summary, [tabindex]):focus-visible, .hardware-model:focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
@media (max-width: 550px) { .hardware-model { padding: 15px; } .model-identity h3 { font-size: 18px; } .model-frequency strong { font-size: 26px; } .model-frequency span { max-width: 66px; text-align: right; } .source-usage { padding: 10px; } }
</style>
