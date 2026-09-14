import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { defineAsyncComponent } from 'vue'
import './custom.css'
import './visual-radar.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app, router }) {
    app.component('HardwareCoverage', defineAsyncComponent(
      () => import('./components/HardwareCoverage.vue'),
    ))
    app.component('HardwareRadar', defineAsyncComponent(
      () => import('./components/HardwareRadar.vue'),
    ))
    app.component('LocoManipRadar', defineAsyncComponent(
      () => import('./components/LocoManipRadar.vue'),
    ))
    app.component('PeopleRadar', defineAsyncComponent(
      () => import('./components/PeopleRadar.vue'),
    ))
    app.component('RadarDashboard', defineAsyncComponent(
      () => import('./components/RadarDashboard.vue'),
    ))
    app.component('DatabaseExplorer', defineAsyncComponent(
      () => import('./components/DatabaseExplorer.vue'),
    ))
    app.component('PulseFeed', defineAsyncComponent(
      () => import('./components/PulseFeed.vue'),
    ))
    app.component('ConferenceRadar', defineAsyncComponent(
      () => import('./components/ConferenceRadar.vue'),
    ))
    app.component('OrganizationCoverage', defineAsyncComponent(
      () => import('./components/OrganizationCoverage.vue'),
    ))
    if (typeof window === 'undefined') return
    let disposePageEnhancements = () => {}

    const initSortableTables = () => {
      document.querySelectorAll<HTMLTableElement>('.vp-doc table').forEach((table) => {
        const thead = table.querySelector('thead')
        if (!thead || table.classList.contains('sortable-init')) return
        table.classList.add('sortable-init')
        const headers = thead.querySelectorAll('th')
        headers.forEach((header, column) => {
          header.tabIndex = 0
          header.title = '按回车、空格或点击排序'
          header.scope = 'col'
          header.setAttribute('aria-label', `${header.textContent?.trim() || '此列'}：回车或空格排序`)
          header.insertAdjacentHTML('beforeend', '<span class="sort-indicator" aria-hidden="true"> ⇅</span>')
          let ascending = true
          const sort = () => {
            const tbody = table.querySelector('tbody')
            if (!tbody) return
            const rows = Array.from(tbody.querySelectorAll('tr'))
            rows.sort((a, b) => {
              const left = a.children[column]?.textContent?.trim() ?? ''
              const right = b.children[column]?.textContent?.trim() ?? ''
              const leftNumber = Number(left.replace(/[,%篇项]/g, ''))
              const rightNumber = Number(right.replace(/[,%篇项]/g, ''))
              const comparison = Number.isFinite(leftNumber) && Number.isFinite(rightNumber)
                ? leftNumber - rightNumber
                : left.localeCompare(right, 'zh-CN', { numeric: true })
              return ascending ? comparison : -comparison
            })
            rows.forEach((row) => tbody.appendChild(row))
            headers.forEach((cell) => {
              const indicator = cell.querySelector('.sort-indicator')
              if (indicator) indicator.textContent = ' ⇅'
            })
            const indicator = header.querySelector('.sort-indicator')
            if (indicator) indicator.textContent = ascending ? ' ↑' : ' ↓'
            headers.forEach((cell) => cell.removeAttribute('aria-sort'))
            header.setAttribute('aria-sort', ascending ? 'ascending' : 'descending')
            ascending = !ascending
          }
          header.addEventListener('click', sort)
          header.addEventListener('keydown', (event) => {
            if (event.target !== header) return
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault()
              sort()
            }
          })
        })
      })
    }

    const initFloatingHeaders = () => {
      const tables = Array.from(document.querySelectorAll<HTMLTableElement>('.vp-doc table'))
        .filter((table) => table.querySelector('thead'))
      if (!tables.length) return () => {}

      const controller = new AbortController()
      const resizeObserver = new ResizeObserver(scheduleUpdate)
      const entries = tables.map((table) => {
        table.classList.add('floating-header-source')
        const floating = document.createElement('div')
        floating.className = 'floating-table-header'
        floating.setAttribute('aria-hidden', 'true')
        const clone = document.createElement('table')
        const clonedHead = table.querySelector('thead')?.cloneNode(true) as HTMLTableSectionElement
        clonedHead.removeAttribute('id')
        clonedHead.querySelectorAll('[id]').forEach((element) => element.removeAttribute('id'))
        const excludeCloneFocus = () => {
          clonedHead.querySelectorAll<HTMLElement>('[tabindex], a, button, input, select, textarea').forEach((element) => { element.tabIndex = -1 })
        }
        excludeCloneFocus()
        clone.appendChild(clonedHead)
        floating.appendChild(clone)
        document.body.appendChild(floating)

        const originalHeaders = Array.from(table.querySelectorAll<HTMLTableCellElement>('thead th'))
        const clonedHeaders = Array.from(clone.querySelectorAll<HTMLTableCellElement>('th'))
        clonedHeaders.forEach((header, index) => {
          header.addEventListener('click', () => {
            originalHeaders[index]?.click()
            clonedHeaders.forEach((cell, cellIndex) => {
              cell.innerHTML = originalHeaders[cellIndex]?.innerHTML ?? cell.innerHTML
            })
            excludeCloneFocus()
          }, { signal: controller.signal })
        })

        table.addEventListener('scroll', scheduleUpdate, { passive: true, signal: controller.signal })
        resizeObserver.observe(table)
        return { table, floating, clone, originalHeaders, clonedHeaders }
      })

      let frame = 0
      function scheduleUpdate() {
        if (frame) return
        frame = window.requestAnimationFrame(() => {
          frame = 0
          const navBottom = Math.max(
            document.querySelector<HTMLElement>('.VPNav')?.getBoundingClientRect().bottom ?? 0,
            0,
          )
          entries.forEach(({ table, floating, clone, originalHeaders, clonedHeaders }) => {
            const rect = table.getBoundingClientRect()
            const left = Math.max(0, rect.left)
            const right = Math.min(window.innerWidth, rect.right)

            clone.style.width = `${table.scrollWidth}px`
            clone.style.transform = `translateX(${-table.scrollLeft}px)`
            originalHeaders.forEach((header, index) => {
              const width = header.getBoundingClientRect().width
              const clonedHeader = clonedHeaders[index]
              if (!clonedHeader) return
              clonedHeader.style.width = `${width}px`
              clonedHeader.style.minWidth = `${width}px`
              clonedHeader.style.maxWidth = `${width}px`
            })

            const headerHeight = clone.getBoundingClientRect().height
            const visible = rect.top < navBottom && rect.bottom > navBottom + headerHeight && right > left
            floating.style.display = visible ? 'block' : 'none'
            if (!visible) return
            floating.style.top = `${navBottom}px`
            floating.style.left = `${left}px`
            floating.style.width = `${right - left}px`
          })
        })
      }

      window.addEventListener('scroll', scheduleUpdate, { passive: true, signal: controller.signal })
      window.addEventListener('resize', scheduleUpdate, { passive: true, signal: controller.signal })
      scheduleUpdate()

      return () => {
        controller.abort()
        resizeObserver.disconnect()
        if (frame) window.cancelAnimationFrame(frame)
        entries.forEach(({ table, floating }) => {
          table.classList.remove('floating-header-source')
          floating.remove()
        })
      }
    }

    const initPageEnhancements = () => {
      disposePageEnhancements()
      initSortableTables()
      disposePageEnhancements = initFloatingHeaders()
    }
    let enhancementTimer = 0
    const scheduleInit = () => {
      window.clearTimeout(enhancementTimer)
      enhancementTimer = window.setTimeout(initPageEnhancements, 80)
    }
    // Data-backed Vue tables may arrive after the route's initial mount.
    // Observe only new, uninitialized documentation tables; our decorative
    // floating copies live outside .vp-doc and cannot trigger a feedback loop.
    const tableObserver = new MutationObserver((records) => {
      const addedTable = records.some((record) => Array.from(record.addedNodes).some((node) => {
        if (!(node instanceof Element)) return false
        return node.matches('.vp-doc table:not(.sortable-init)') || Boolean(node.querySelector('.vp-doc table:not(.sortable-init)'))
      }))
      if (addedTable) scheduleInit()
    })
    tableObserver.observe(document.body, { childList: true, subtree: true })
    window.addEventListener('pagehide', () => {
      tableObserver.disconnect()
      window.clearTimeout(enhancementTimer)
      disposePageEnhancements()
    })
    window.addEventListener('pageshow', (event) => {
      if (!event.persisted) return
      tableObserver.observe(document.body, { childList: true, subtree: true })
      scheduleInit()
    })
    router.onAfterRouteChanged = scheduleInit
    window.addEventListener('load', scheduleInit, { once: true })
    scheduleInit()
  },
} satisfies Theme
