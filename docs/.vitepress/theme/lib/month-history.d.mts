export type MonthNavigationSource = 'selection' | 'restore' | 'hydrate'
export function resolveMonthFromUrl(href: string, availableMonths: readonly string[], defaultMonth: string): string
export function monthHistoryTarget(href: string, month: string, options: {
  availableMonths: readonly string[]
  defaultMonth: string
  source?: MonthNavigationSource
}): string | null
export function monthRequestIsCurrent(state: {
  request: number
  currentRequest: number
  disposed: boolean
  requestPath: string
  currentPath: string
}): boolean
