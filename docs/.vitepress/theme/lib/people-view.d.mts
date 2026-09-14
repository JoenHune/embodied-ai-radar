export const peopleLenses: string[]
export const peopleSorts: string[]
export const directionNames: Record<string, string>
export interface PeopleState { q: string; direction: string; lens: string; sort: string; person: string }
export function peopleStateFromUrl(value: string): PeopleState
export function peopleUrl(value: string, state: PeopleState): string
export function verifiedDirectionCount(person: any, direction: string): number | null
export function personWorkList(works: any[], scope?: 'window' | 'all'): any[]
export function activitySummary(person: any, months: string[]): { active: number; recent: number; prior: number }
export function filterPeople(people: any[], state: PeopleState, months?: string[]): any[]
export function verifiedCollaborators(person: any, people: any[], coauthorships?: any[]): any[]
export function personDetailMatchesIndex(detail: any, index: any, slug: string): boolean
export function metricText(value: unknown): string
export function escapeChartText(value: unknown): string
