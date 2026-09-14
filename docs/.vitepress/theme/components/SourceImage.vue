<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useVisualMedia } from '../composables/useVisualMedia'

const props = withDefaults(defineProps<{ entityId: string; name?: string; portrait?: boolean; expanded?: boolean; sourceNote?: boolean; interactive?: boolean }>(), { name: '', portrait: false, expanded: false, sourceNote: false, interactive: true })
const media = useVisualMedia()
const asset = computed<any>(() => media.value[props.entityId])
const failed = ref(false)
const requested = ref(false)
watch(() => [props.entityId, asset.value?.image_url], () => { failed.value = false; requested.value = false })
const allowed = computed(() => asset.value && !failed.value && (!asset.value.defer_large || props.expanded || requested.value) && (!asset.value.animated || requested.value))
const initials = computed(() => props.name.split(/\s+/).filter(Boolean).slice(0, 2).map(word => word[0]).join('').toUpperCase())
const status = computed(() => failed.value ? '图片暂不可用' : asset.value?.defer_large ? '原图较大，打开档案查看' : '照片尚未确认')
</script>

<template>
  <figure class="source-image" :class="{ portrait, 'is-missing': !allowed, diagram: /diagram|framework|evaluation|figure/.test(asset?.image_kind || '') }">
    <img v-if="allowed" :src="asset.image_url" :alt="asset.alt || name" loading="lazy" decoding="async" referrerpolicy="no-referrer" :width="portrait ? 160 : 640" :height="portrait ? 160 : 400" @error="failed = true" />
    <div v-else-if="portrait" class="portrait-fallback" role="img" :aria-label="`${name} · ${status}`"><span>{{ initials || '—' }}</span><small v-if="asset?.defer_large && !expanded && !failed">档案内查看照片</small></div>
    <div v-else class="media-fallback"><span>{{ failed ? '配图暂不可用' : asset?.defer_large ? '官方配图较大 · 原文查看' : '原文研究' }}</span><button v-if="asset && !failed && interactive" type="button" @click="requested = true">{{ asset.animated ? '查看动态预览' : '加载官方配图' }}</button></div>
    <figcaption v-if="sourceNote && asset"><span v-if="asset.credit">{{ asset.credit }} · </span><a :href="asset.source_page" target="_blank" rel="noopener noreferrer">图片来源</a><span class="rights-note"> · {{ asset.rights_status === 'unknown' ? '许可未声明' : '保留原摄影署名' }}</span></figcaption>
  </figure>
</template>

<style scoped>
.source-image { position: relative; margin: 0; min-width: 0; overflow: hidden; background: var(--vp-c-bg-soft); }
.source-image img { display: block; width: 100%; height: 100%; object-fit: cover; }
.source-image.diagram img { object-fit: contain; }
.source-image.diagram { background: #fff; }
.source-image.portrait { width: 88px; height: 88px; flex: none; border-radius: 16px; }
.source-image.portrait img { object-position: center 35%; }
.portrait-fallback { display: grid; place-items: center; height: 100%; color: var(--vp-c-text-2); background: var(--vp-c-bg-soft); }
.portrait-fallback span { font-size: 1.5rem; font-weight: 500; letter-spacing: .02em; }
.portrait-fallback small { font-size: 11px; padding: 0 4px; text-align: center; }
.media-fallback { display: grid; align-content: center; justify-items: center; gap: 12px; height: 100%; padding: 18px; color: var(--vp-c-text-2); font-size: 14px; }
.media-fallback button { padding: 6px 12px; border: 1px solid var(--vp-c-divider); border-radius: 6px; }
figcaption { padding: 8px 0; background: var(--vp-c-bg); color: var(--vp-c-text-2); font-size: 12px; line-height: 1.5; }
.source-image:has(figcaption) { overflow: visible; }
.source-image:has(figcaption) img { border-radius: inherit; }
.source-image.portrait:has(figcaption) { height: auto; }
.source-image.portrait:has(figcaption) img, .source-image.portrait:has(figcaption) .portrait-fallback { aspect-ratio: 1; height: auto; }
</style>
