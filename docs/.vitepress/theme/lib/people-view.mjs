export const peopleLenses = ['contribution', 'impact', 'recent', 'roles']
export const peopleSorts = ['name', 'verified', 'active']
export const directionNames = {
  D1: '具身基础模型与通才策略', D2: '分层推理、规划与记忆', D3: '世界模型与预测控制',
  D4: '灵巧、双臂与接触操作', D5: '人形、运动与全身控制', D6: '导航与移动操作',
  D7: '人机协作与交互学习', D8: '策略学习与优化', D9: '数据引擎与人类视频学习',
  D10: '仿真、合成数据与 Sim-to-Real', D11: '动作关联的空间感知与表征',
  D12: '评测、安全、可靠性与故障恢复', D13: '持续学习、部署学习与自改进',
  D14: '多机器人协同与群体智能', D15: '触觉、力觉与多模态身体感知',
}

export function peopleStateFromUrl(value) {
  const params = new URL(value, 'https://radar.invalid').searchParams
  const direction = params.get('directions') || ''
  return {
    q: params.get('q') || '', direction: Object.hasOwn(directionNames, direction) ? direction : '',
    lens: peopleLenses.includes(params.get('lens')) ? params.get('lens') : 'contribution',
    sort: peopleSorts.includes(params.get('sort')) ? params.get('sort') : 'name',
    person: /^[a-z0-9][a-z0-9-]*$/.test(params.get('person') || '') ? params.get('person') : '',
  }
}

export function peopleUrl(value, state) {
  const url = new URL(value, 'https://radar.invalid')
  for (const [key, field, fallback] of [['q', 'q', ''], ['directions', 'direction', ''], ['lens', 'lens', 'contribution'], ['sort', 'sort', 'name'], ['person', 'person', '']]) {
    if (state[field] && state[field] !== fallback) url.searchParams.set(key, state[field])
    else url.searchParams.delete(key)
  }
  return url.pathname + url.search + url.hash
}

export function verifiedDirectionCount(person, direction) {
  if (!direction) return person.metrics?.verified_works_window ?? null
  return person.directions?.find(row => row.code === direction)?.count ?? 0
}

export function personWorkList(works, scope = 'window') {
  return works.filter(work => scope === 'all' || work.in_complete_window)
    .sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || '') || a.work_id.localeCompare(b.work_id))
}

export function activitySummary(person, months) {
  const values = new Map((person.monthly_activity || []).map(row => [row.month, row.count]))
  const sum = list => list.reduce((total, month) => total + (values.get(month) || 0), 0)
  return { active: months.filter(month => (values.get(month) || 0) > 0).length, recent: sum(months.slice(-3)), prior: sum(months.slice(-6, -3)) }
}

export function filterPeople(people, state, months = []) {
  const q = state.q.trim().toLocaleLowerCase()
  const filtered = people.filter(person =>
    (!state.direction || verifiedDirectionCount(person, state.direction) > 0)
    && `${person.name || ''} ${person.name_zh || ''} ${(person.aliases || []).map(alias => typeof alias === 'string' ? alias : alias.name || '').join(' ')}`.toLocaleLowerCase().includes(q))
  return [...filtered].sort((a, b) => {
    // Unknown metrics never become a synthetic zero influence score.
    const metric = person => state.sort === 'active' ? activitySummary(person, months).active : verifiedDirectionCount(person, state.direction)
    if (state.sort !== 'name') {
      const x = metric(a), y = metric(b)
      if (x === null && y !== null) return 1
      if (y === null && x !== null) return -1
      if (x !== null && y !== null && x !== y) return y - x
    }
    return (a.name || '').localeCompare(b.name || '', 'en', { sensitivity: 'base' })
  })
}

export function verifiedCollaborators(person, people, coauthorships = []) {
  const ids = new Set(person?.verified_work_ids || [])
  const windowPairs = new Map(coauthorships.filter(row => row.person_ids?.length === 2 && row.person_ids.includes(person?.person_id))
    .map(row => [row.person_ids.find(id => id !== person.person_id), new Set(row.work_ids || [])]))
  return people.filter(other => other.person_id !== person?.person_id)
    .map(other => ({ ...other, shared_work_ids: [...new Set(other.verified_work_ids || [])].filter(id => ids.has(id) && windowPairs.get(other.person_id)?.has(id)) }))
    .filter(other => other.shared_work_ids.length)
    .sort((a, b) => b.shared_work_ids.length - a.shared_work_ids.length || a.name.localeCompare(b.name))
}

export function personDetailMatchesIndex(detail, index, slug) {
  return detail?.slug === slug && detail?.schema_version === '1'
    && Boolean(index?.dataset_version) && detail.dataset_version === index.dataset_version
    && Boolean(index?.review_hash) && detail.review_hash === index.review_hash
}

export function metricText(value) {
  return typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('zh-CN').format(value) : '尚未核验'
}

export function escapeChartText(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char])
}
