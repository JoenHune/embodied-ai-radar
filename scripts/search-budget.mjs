// Full native Pagefind bundle, summed with per-file gzip transfer estimates.
// The catalogue adapter is measured separately; corpus coverage is never
// reduced to satisfy this capacity gate.
export const SEARCH_INDEX_BUDGET_BYTES = 21_000_000
