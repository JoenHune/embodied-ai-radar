export function evidenceIds(row: unknown): string[]
export function evidenceWorkIds(ids: string[], eventToWork?: Record<string, string>): string[]
export function cooccurrenceParams(source: string, target: string, months: string[]): Record<string, string>
export function evidenceSearchParams(ids: string[], eventToWork?: Record<string, string>, params?: Record<string, string>): URLSearchParams
