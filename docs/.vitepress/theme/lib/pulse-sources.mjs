export const createPulseSource = () => ({ rows: [], loaded: false, loading: false, error: '', request: 0 })

export async function loadPulseSource(state, url, kind, { fetcher = fetch, signal } = {}) {
  const request = ++state.request
  const current = () => request === state.request && !signal?.aborted
  state.loading = true
  state.error = ''
  try {
    const response = await fetcher(url, { signal })
    if (!response.ok) throw new Error('source unavailable')
    const body = await response.json()
    const rows = kind === 'organizations' ? body?.rows : Array.isArray(body) ? body : body?.events
    if (!Array.isArray(rows) || rows.some(row => !row || typeof row !== 'object' || Array.isArray(row)
      || (kind === 'organizations' ? typeof row.organization_id !== 'string' || row.updates != null && !Array.isArray(row.updates) : typeof row.event_id !== 'string'))) throw new Error('invalid source')
    if (!current()) return
    state.rows = rows
    state.loaded = true
  } catch {
    if (!current()) return
    state.error = `${kind === 'organizations' ? '组织发布记录' : '证据升级记录'}暂时无法读取${state.loaded ? '，保留上次成功载入的数据' : ''}。`
  } finally {
    if (request === state.request) state.loading = false
  }
}
