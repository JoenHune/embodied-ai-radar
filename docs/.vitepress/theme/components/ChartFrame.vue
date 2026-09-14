<script setup lang="ts">
defineProps<{
  title: string
  description: string
  height?: number
  compact?: boolean
}>()
</script>

<template>
  <section class="v3-chart-frame" :class="{ 'is-compact': compact }">
    <header>
      <div>
        <h2>{{ title }}</h2>
        <p>{{ description }}</p>
      </div>
      <slot name="actions" />
    </header>
    <div class="v3-chart-canvas" :style="{ '--chart-height': `${height || 420}px` }">
      <slot />
    </div>
    <details v-if="$slots.table" class="v3-chart-table">
      <summary>查看可访问数据表</summary>
      <div class="v3-table-scroll" tabindex="0" :aria-label="`${title}数据表，可横向滚动`"><slot name="table" /></div>
    </details>
  </section>
</template>
