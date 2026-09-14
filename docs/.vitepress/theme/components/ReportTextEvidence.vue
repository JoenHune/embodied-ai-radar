<script setup lang="ts">
import { eventDate } from '../lib/dates'
defineProps<{ value: any; title?: string }>()
const numberLabel = (row: any) => `${row.value}${row.unit === 'percentage' ? '%' : row.unit === 'percentage_points' ? ' 个百分点' : ''}`
const regimes = (snapshot: any) => {
  const groups = new Map<string, any[]>()
  for (const row of snapshot.observations || []) groups.set(row.context, [...(groups.get(row.context) || []), row])
  return [...groups].map(([context, observations]) => ({ context, observations }))
}
</script>

<template>
  <section class="report-text-evidence" :aria-label="title ? `${title} · 历史短摘录` : '公司报告历史短摘录'">
    <h3>{{ title || '公司报告的历史短摘录' }}</h3>
    <p>以下为公司自报的原文证据与已提取语境，不代表同行评审或独立复现；不同数据和适配预算不能直接横比。</p>
    <template v-if="value?.status === 'available'">
      <article v-for="snapshot in value.snapshots" :key="snapshot.snapshot_id" class="report-text-snapshot">
        <dl class="report-text-dates">
          <div><dt>报告标注日期</dt><dd>{{ eventDate(snapshot.report_published_at, snapshot.report_date_precision) }}</dd></div>
          <div><dt>正文最迟已知存在</dt><dd>{{ eventDate(snapshot.available_at, snapshot.date_precision) }}</dd></div>
        </dl>
        <p class="report-text-note">第二个时间是有内容证据的保守上界，不是报告正文的精确首次公开时间。摘录来自所列来源，未保存整篇报告版式或全部图表。</p>
        <div class="report-observations">
          <article v-for="regime in regimes(snapshot)" :key="regime.context" class="report-observation">
            <h4>{{ regime.context }}</h4>
            <dl><div v-for="observation in regime.observations" :key="observation.id"><dt>{{ observation.label }}</dt><dd><strong class="report-observation-value">{{ numberLabel(observation) }}</strong></dd></div></dl>
          </article>
        </div>
        <p class="report-text-note">条件说明是 AI 从来源提取的语境，不是逐字引文；数值和原文短摘录单独绑定。此处未列出完整实验和误差统计，请结合原报告阅读。</p>
        <details>
          <summary>查看短摘录、定位与来源证明</summary>
          <ul><li v-for="excerpt in snapshot.excerpts" :key="excerpt.excerpt_id"><q lang="en">{{ excerpt.text }}</q><small>{{ excerpt.locator }} · 字符 {{ excerpt.start }}–{{ excerpt.end }}</small></li></ul>
          <dl><div><dt>本次核查</dt><dd>{{ eventDate(snapshot.verified_at) }} · 源内容核对，非人工语义批准</dd></div><div><dt>提取文本指纹</dt><dd><code>{{ snapshot.content_sha256 }}</code></dd></div><div><dt>摘录指纹</dt><dd><code>{{ snapshot.excerpt_digest }}</code></dd></div></dl>
          <p>仅提供必要短摘录，不授予整篇报告的再发布许可，也不继承 arXiv 元数据的 CC0 标签。</p>
        </details>
        <nav aria-label="报告摘录来源"><a :href="snapshot.source_url" target="_blank" rel="noopener noreferrer">实际摘录来源</a><a :href="snapshot.report_url" target="_blank" rel="noopener noreferrer">报告页面</a><a v-for="link in value.proof_links?.[snapshot.snapshot_id] || []" :key="link.url" :href="link.url" target="_blank" rel="noopener noreferrer">{{ link.label }}</a></nav>
      </article>
    </template>
    <p v-else-if="value?.status === 'retrospective_only'">已登记的正文证据晚于所选截止时间；此视角只保留发布信息，不展示后来的正文或数值。</p>
    <p v-else-if="value?.status === 'conflicting_snapshots'">来源版本存在冲突，暂不据此展示实验数值。</p>
    <p v-else>尚无符合所选截止时间的正文摘录；报告标题或页面发布日期不能替代历史原文。</p>
  </section>
</template>

<style scoped>
.report-text-evidence { margin: 24px 0; overflow-wrap: anywhere; }
.report-text-evidence h3 { margin: 0 0 12px; }
.report-text-evidence p { line-height: 1.7; }
.report-text-snapshot { margin: 16px 0; padding: 18px; border: 1px solid var(--vp-c-divider); border-radius: 10px; }
.report-text-evidence dl { display: grid; gap: 12px; margin: 14px 0; }
.report-text-evidence dt { font-weight: 600; }
.report-text-evidence dd { margin: 3px 0 0; }
.report-observations { display: grid; grid-template-columns: repeat(auto-fit,minmax(min(100%,230px),1fr)); gap: 12px; }
.report-observation { min-width: 0; padding: 14px; border-radius: 8px; background: var(--vp-c-bg-soft); }
.report-observation h4 { margin: 0 0 8px; font-size: 14px; }
.report-observation-value { display: block; font-size: 24px; font-variant-numeric: tabular-nums; }
.report-text-note { font-size: 13px; color: var(--vp-c-text-2); }
.report-text-evidence summary { min-height: 44px; display: flex; align-items: center; cursor: pointer; font-weight: 600; }
.report-text-evidence li { margin: 12px 0; }
.report-text-evidence small { display: block; color: var(--vp-c-text-2); }
.report-text-evidence code { white-space: normal; overflow-wrap: anywhere; }
.report-text-evidence nav { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 12px; }
.report-text-evidence :is(a,summary):focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
</style>
