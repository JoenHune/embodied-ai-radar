import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { defineAsyncComponent } from 'vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app, router }) {
    app.component('ResearchVisuals', defineAsyncComponent(
      () => import('./components/ResearchVisuals.vue'),
    ))
    app.component('ResearchGroupExplorer', defineAsyncComponent(
      () => import('./components/ResearchGroupExplorer.vue'),
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
          header.title = '点击排序'
          header.setAttribute('role', 'button')
          header.insertAdjacentHTML('beforeend', '<span class="sort-indicator"> ⇅</span>')
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
            ascending = !ascending
          }
          header.addEventListener('click', sort)
          header.addEventListener('keydown', (event) => {
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
    const scheduleInit = () => {
      window.setTimeout(initPageEnhancements, 80)
    }
    router.onAfterRouteChanged = scheduleInit
    window.addEventListener('load', scheduleInit, { once: true })
    scheduleInit()
  },
} satisfies Theme
