export type SourceConflict = { conflict_id: string; work_id: string; version: string; status: 'open' | 'resolved'; experimental_use: 'hold' | 'released'; summary_zh: string; detected_at: string; issue_types: string[]; source_urls: string[] }
export function safeConflictUrl(value: unknown): string
export function compactSourceConflicts(value: unknown): SourceConflict[]
export function sourceConflictIndex(envelope: unknown, expectedVersion: string): Map<string, SourceConflict[]>
export function conflictsForWork(index: Map<string, SourceConflict[]>, workId: string, version?: string): SourceConflict[]
export function applySourceConflicts<T extends { work_id: string }>(work: T, index: Map<string, SourceConflict[]>): T & { source_conflicts: SourceConflict[] }
export function sourceConflictState(value: unknown, options?: { workId?: string; version?: string }): { unknown: boolean; rows: SourceConflict[] }
