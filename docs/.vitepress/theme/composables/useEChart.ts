import { nextTick, onBeforeUnmount, onMounted, ref, watch, watchEffect, type Ref } from 'vue'
import * as echarts from 'echarts/core'
import type { EChartsType } from 'echarts/core'

export const cssToken = (name: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim()

export const chartTokens = () => ({
  text: cssToken('--vp-c-text-1'),
  muted: cssToken('--vp-c-text-2'),
  divider: cssToken('--vp-c-divider'),
  background: cssToken('--vp-c-bg-elv'),
  palette: Array.from({ length: 6 }, (_, index) => cssToken(`--radar-series-${index + 1}`)),
})

export function useEChart(optionFactory: () => any, onReady?: (chart: EChartsType) => void) {
  const element: Ref<HTMLDivElement | null> = ref(null)
  let chart: EChartsType | undefined
  let resizeObserver: ResizeObserver | undefined
  let themeObserver: MutationObserver | undefined
  let visibilityObserver: IntersectionObserver | undefined
  let disposed = false
  let stopElementWatch: (() => void) | undefined

  const render = () => {
    if (!chart || !element.value?.clientWidth) return
    chart.setOption(optionFactory(), true)
  }

  const initialize = () => {
    if (disposed || !element.value?.clientWidth || !element.value.clientHeight) return
    if (!chart) {
      chart = echarts.init(element.value)
      onReady?.(chart)
    }
    chart.resize()
    render()
  }

  onMounted(async () => {
    await nextTick()
    if (disposed) return
    // A chart may first appear after an API response or a conditional view.
    // Observe the actual element lifetime, not only the component mount.
    stopElementWatch = watch(element, (target) => {
      visibilityObserver?.disconnect()
      resizeObserver?.disconnect()
      chart?.dispose()
      chart = undefined
      if (!target) return
      visibilityObserver = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) initialize()
      }, { rootMargin: '200px' })
      visibilityObserver.observe(target)
      resizeObserver = new ResizeObserver(() => { if (chart) { chart.resize(); render() } })
      resizeObserver.observe(target)
    }, { immediate: true, flush: 'post' })
    themeObserver = new MutationObserver(render)
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  })

  watchEffect(() => {
    if (typeof window === 'undefined') return
    optionFactory()
    render()
  })

  onBeforeUnmount(() => {
    disposed = true
    stopElementWatch?.()
    visibilityObserver?.disconnect()
    resizeObserver?.disconnect()
    themeObserver?.disconnect()
    chart?.dispose()
  })

  return { element, render, getChart: () => chart }
}
