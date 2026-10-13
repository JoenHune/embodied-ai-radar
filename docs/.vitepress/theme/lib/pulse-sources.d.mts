export type PulseSource = { rows: any[]; loaded: boolean; loading: boolean; error: string; request: number }
export function createPulseSource(): PulseSource
export function loadPulseSource(state: PulseSource, url: string, kind: 'organizations' | 'events', options?: { fetcher?: typeof fetch; signal?: AbortSignal }): Promise<void>
