<script setup lang="ts">
import { computed, ref } from 'vue'
import { withBase } from 'vitepress'
import radar from '../../data/research-groups.json'

const query = ref('')
const category = ref('')
const region = ref('')
const direction = ref('')
const question = ref('')
const health = ref('')
const evidence = ref('')
const order = ref('recent')

const categoryLabels: Record<string, string> = {
  corporate: '企业/独立研究组织',
  academic: '学术实验室/PI 组',
  platform: '研究院/开放平台',
  deployment_watch: '部署与早期观察',
}

const values = (key: 'region' | 'direction_codes' | 'question_codes') => {
  const result = new Set<string>()
  radar.groups.forEach((group) => {
    const value = group[key]
    if (Array.isArray(value)) value.forEach((item) => result.add(item))
    else if (value) result.add(value)
  })
  return [...result].sort((left, right) => left.localeCompare(right, 'zh-CN', { numeric: true }))
}
const regions = values('region')
const directions = values('direction_codes')
const questions = values('question_codes')

const filtered = computed(() => {
  const needle = query.value.trim().toLowerCase()
  const rows = radar.groups.filter((group) => {
    const haystack = [group.display_name, group.short_name, group.summary_zh, ...group.parent_names, ...group.direction_codes, ...group.question_codes].join(' ').toLowerCase()
    if (needle && !haystack.includes(needle)) return false
    if (category.value && group.tracking_category !== category.value) return false
    if (region.value && group.region !== region.value) return false
    if (direction.value && !group.direction_codes.includes(direction.value)) return false
    if (question.value && !group.question_codes.includes(question.value)) return false
    if (health.value && group.source_health !== health.value) return false
    if (evidence.value && Number(group.evidence_counts[evidence.value as keyof typeof group.evidence_counts] ?? 0) === 0) return false
    return true
  })
  return rows.sort((left, right) => order.value === 'name'
    ? left.display_name.localeCompare(right.display_name, 'zh-CN')
    : String(right.last_changed ?? '').localeCompare(String(left.last_changed ?? '')) || left.display_name.localeCompare(right.display_name, 'zh-CN'))
})

const reset = () => {
  query.value = ''; category.value = ''; region.value = ''; direction.value = ''; question.value = ''; health.value = ''; evidence.value = ''; order.value = 'recent'
}
</script>

<template>
  <section class="group-explorer">
    <div class="group-filters" aria-label="研究组筛选">
      <label class="group-filter group-search"><span>搜索</span><input v-model="query" type="search" placeholder="研究组、母机构、方向…"></label>
      <label class="group-filter"><span>组织类型</span><select v-model="category"><option value="">全部</option><option v-for="(label, key) in categoryLabels" :key="key" :value="key">{{ label }}</option></select></label>
      <label class="group-filter"><span>地区</span><select v-model="region"><option value="">全部</option><option v-for="item in regions" :key="item" :value="item">{{ item }}</option></select></label>
      <label class="group-filter"><span>研究方向</span><select v-model="direction"><option value="">全部</option><option v-for="item in directions" :key="item" :value="item">{{ item }}</option></select></label>
      <label class="group-filter"><span>问题轴</span><select v-model="question"><option value="">全部</option><option v-for="item in questions" :key="item" :value="item">{{ item }}</option></select></label>
      <label class="group-filter"><span>证据</span><select v-model="evidence"><option value="">全部</option><option value="G1">G1 直接证据</option><option value="G2">G2 时间重建</option></select></label>
      <label class="group-filter"><span>来源健康</span><select v-model="health"><option value="">全部</option><option value="healthy">healthy</option><option value="partial">partial</option><option value="stale">stale</option><option value="unverified">unverified</option></select></label>
      <label class="group-filter"><span>排序</span><select v-model="order"><option value="recent">最近变化</option><option value="name">名称</option></select></label>
      <button type="button" class="group-reset" @click="reset">清除筛选</button>
    </div>
    <p class="group-result-count">显示 {{ filtered.length }} / {{ radar.tracking_group_count }} 个研究组</p>
    <div class="group-grid">
      <article v-for="group in filtered" :key="group.organization_id" class="group-card">
        <header><a :href="withBase(`/groups/${group.slug}`)">{{ group.display_name }}</a><span class="group-health" :data-health="group.source_health">{{ group.source_health }}</span></header>
        <p class="group-meta">{{ categoryLabels[group.tracking_category] }} · {{ group.region }} / {{ group.country }}</p>
        <p>{{ group.summary_zh }}</p>
        <div class="group-tags"><span v-for="item in group.direction_codes.slice(0, 6)" :key="item">{{ item }}</span><span v-for="item in group.question_codes.slice(0, 4)" :key="item" class="question-tag">{{ item }}</span></div>
        <footer><span>本周 {{ group.latest_week_count }}</span><span>12 月 {{ group.current_12m_count }}</span><span>更新 {{ group.last_changed || '—' }}</span></footer>
      </article>
    </div>
  </section>
</template>
