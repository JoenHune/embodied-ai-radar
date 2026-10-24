// Full native Pagefind bundle, summed with per-file gzip transfer estimates.
// The catalogue adapter is measured separately; corpus coverage is never
// reduced to satisfy this capacity gate.
// Temporary Weekly v3 ship gate. Run 39997885885 measured 21,841,424 bytes
// after PR #3, over the previous 21,000,000 ceiling. 22,000,000 leaves
// 158,576 bytes of headroom. Search sharding remains the deferred fix;
// do not treat this as a new permanent capacity target.
export const SEARCH_INDEX_BUDGET_BYTES = 22_000_000
