import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import './custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ router }) {
    if (typeof window === 'undefined') return
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
    router.onAfterRouteChanged = () => window.setTimeout(initSortableTables, 80)
    window.addEventListener('load', () => window.setTimeout(initSortableTables, 80))
  },
} satisfies Theme
