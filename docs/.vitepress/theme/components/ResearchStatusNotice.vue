<script setup lang="ts">
import { eventDate } from '../lib/dates'
defineProps<{ value: any; title?: string; context?: string }>()
const labels: Record<string, string> = { withdrawn: '作者撤回', retracted: '撤稿', corrected: '更正', expression_of_concern: '关注声明', reinstated: '恢复', active: '当前未被状态通知阻断' }
</script>

<template>
  <section v-if="value?.notices?.length || value?.information_gaps?.length" class="research-status-notice" :class="{ blocked: value.validation_eligible === false }" aria-label="研究状态通知">
    <h3>{{ title || '研究状态与适用边界' }} · {{ !value.notices?.length ? '待核验线索' : labels[value.status] || value.status }}</h3>
    <p v-if="context">{{ context }}</p>
    <p v-if="value.validation_eligible === false">受影响的实验结果不再用于支持研究命题或提升证据成熟度。原始记录、公开资产和历史月份仍保留；公开资产存在不等于结果有效。</p>
    <p v-if="value.information_gaps?.length">存在未核实、时间不明确或相互冲突的状态线索，已保留复核标记；不能据此推断论文没有问题或已被撤稿。</p>
    <ul><li v-for="notice in value.notices" :key="notice.notice_id">
      <strong>{{ labels[notice.event_type] || notice.event_type }} · {{ eventDate(notice.public_at, notice.date_precision) }}</strong>
      <p>{{ notice.summary_zh }}</p>
      <a :href="notice.source_url" target="_blank" rel="noopener noreferrer">核对官方状态记录</a>
    </li></ul>
  </section>
</template>

<style scoped>
.research-status-notice { margin: 18px 0; padding: 16px 18px; border: 1px solid var(--vp-c-divider); border-left: 4px solid var(--vp-c-warning-1); border-radius: 8px; background: var(--vp-c-bg-soft); overflow-wrap: anywhere; }
.research-status-notice h3 { margin: 0 0 10px; font-size: 1rem; line-height: 1.5; }
.research-status-notice p, .research-status-notice li { margin: 8px 0; font-size: .85rem; line-height: 1.7; }
.research-status-notice ul { margin: 10px 0 0; padding-left: 20px; }
.research-status-notice a { display: inline-block; padding: 6px 0; text-decoration: underline; }
.research-status-notice.blocked { border-left-color: var(--vp-c-danger-1); }
</style>
