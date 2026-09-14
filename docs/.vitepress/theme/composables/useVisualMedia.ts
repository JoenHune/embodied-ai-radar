import { onMounted, shallowRef } from 'vue'
import { withBase } from 'vitepress'

const media = shallowRef<Record<string, any>>({})
let request: Promise<void> | undefined
export function useVisualMedia() {
  onMounted(() => {
    request ||= fetch(withBase('/api/v1/visual-media.json'))
      .then(async response => {
        if (!response.ok) throw new Error('media unavailable')
        const result = await response.json()
        if (result.schema_version !== '1' || !result.assets) throw new Error('media schema')
        media.value = result.assets
      }).catch(() => { request = undefined })
  })
  return media
}
