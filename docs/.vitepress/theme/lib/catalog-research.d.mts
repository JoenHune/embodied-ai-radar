export type SearchSort = 'auto' | 'newest' | 'oldest'
export type SearchFilterChip = { key: string; value?: string; label: string }
export function activeSearchFilters(filters: Record<string, string | boolean>, options?: Record<string, { value: string; label: string }[]>): SearchFilterChip[]
export function clearedSearchFilter(filters: Record<string, string | boolean>, chip: SearchFilterChip): Record<string, string | boolean>
export function readSearchSort(params: URLSearchParams): SearchSort
export function writeSearchSort(url: URL, sort: SearchSort): URL
export function compareResearchDates(leftDate: string, leftPrecision: string | undefined, leftId: string, rightDate: string, rightPrecision: string | undefined, rightId: string, sort?: SearchSort): number
export function orderSearchPositions(positions: number[], lookup: { dates: string[]; date_precisions?: string[]; work_ids: string[] }, sort: SearchSort, hasTextQuery: boolean): number[]
export function createSearchRestorer(callbacks: { invalidateSearch: () => void; readState: () => { work: string; page: number }; flush: () => Promise<unknown>; setRestoring: (value: boolean) => void; restoreWork: (work: string) => void | Promise<void>; search: (page: number) => Promise<void> }): { restore: () => Promise<void>; cancel: () => void }
