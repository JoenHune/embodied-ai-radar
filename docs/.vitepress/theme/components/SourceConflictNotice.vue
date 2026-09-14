<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'
import { sourceConflictState } from '../lib/source-conflicts.mjs'

const props = withDefaults(defineProps<{ value?: unknown; workId?: string; version?: string; unknown?: boolean; compact?: boolean; monthly?: boolean }>(), { unknown: false, compact: false, monthly: false })
const state = computed(() => sourceConflictState(props.value, { workId: props.workId, version: props.version }))
const workUrl = (id: string) => withBase(`/database/?${new URLSearchParams({ work: id, relevance: 'all' })}`)
</script>

<template>
  <aside v-if="unknown || state.unknown || state.rows.length" class="source-conflict-notice" :class="{ compact }" role="note" aria-label="来源内容待核">
    <strong>{{ unknown || state.unknown ? '来源冲突状态未知' : '来源待核' }}</strong>
    <p v-if="unknown || state.unknown">来源冲突记录暂不可用或与当前数据版本不一致；不能按“无冲突”理解，已读记录也不等于实验结论已验证。</p>
    <template v-else>
      <p>元数据与正文等来源渠道存在待核差异；不是撤稿通知，也未判定哪一方错误。受影响内容暂不作为确定实验结论，不改变论文登记数量。</p>
      <p v-if="monthly">这是当前登记的来源提醒，发现时间不等于当月已知；保留的月报原文供追溯，不将冲突来源用于当前确定性实验判断。</p>
      <ul><li v-for="row in state.rows" :key="row.conflict_id">
        <a v-if="!workId" :href="workUrl(row.work_id)">{{ row.work_id }}</a><span v-else>{{ row.version }}</span>
        <span v-if="!workId"> · {{ row.version }}</span><span> · 发现于 {{ eventDate(row.detected_at) }}</span>
        <p>{{ row.summary_zh }}</p>
        <div v-if="!compact" class="source-conflict-links"><a v-for="(url, index) in row.source_urls" :key="url" :href="url" target="_blank" rel="noopener noreferrer">核对来源 {{ Number(index) + 1 }} ↗</a><small>记录：{{ row.conflict_id }}</small></div>
      </li></ul>
      <a v-if="compact && workId" :href="workUrl(workId)">查看来源差异与版本</a>
    </template>
  </aside>
</template>

<style scoped>
.source-conflict-notice { margin: 14px 0; padding: 14px 16px; border: 1px solid var(--vp-c-warning-1); border-left-width: 4px; border-radius: 8px; background: var(--vp-c-warning-soft); color: var(--vp-c-text-1); font-size: 13px; line-height: 1.7; overflow-wrap: anywhere; }
.source-conflict-notice p { margin: 6px 0; }
.source-conflict-notice ul { padding-left: 18px; margin: 8px 0; }
.source-conflict-notice li + li { margin-top: 10px; }
.source-conflict-links { display: flex; gap: 8px 14px; flex-wrap: wrap; }
.source-conflict-links small { width: 100%; color: var(--vp-c-text-2); }
.source-conflict-notice a { text-decoration: underline; }
.source-conflict-notice a:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 3px; }
.source-conflict-notice.compact { padding: 10px 12px; font-size: 12px; margin: 0 0 12px; }
</style>
