import { originalSourceUrl, safeOriginalUrl } from './research-card.mjs'

// A frequency is a distinct canonical work, never mentions, versions, devices
// purchased, or a sum of real/sim/role counts. Identity merging is upstream.
const allowedCategories = new Set(['robot_platform', 'robot_arm', 'dexterous_hand', 'gripper', 'compute_platform', 'data_collection', 'tactile_sensor', 'force_sensor', 'vision_sensor'])
const computeRoles = new Set(['training_compute', 'inference_compute', 'control_compute', 'model_fitting_compute', 'experiment_compute'])
const allowedRoles = new Set(['real_robot', 'simulated_robot', 'training_compute', 'inference_compute', 'control_compute', 'model_fitting_compute', 'experiment_compute', 'data_collection', 'sensing', 'dataset_source'])
export function hardwareMonth(work) {
  return ['day', 'month'].includes(work?.first_public_date_precision) && /^\d{4}-(0[1-9]|1[0-2])(?:$|-)/.test(work.first_public_date || '') ? work.first_public_date.slice(0, 7) : 'unknown'
}

function sourceUrl(value) {
  const safe = safeOriginalUrl(value)
  if (!safe) return ''
  const host = new URL(safe).hostname
  return host === 'localhost' || /^(?:127\.|10\.|192\.168\.|169\.254\.|172\.(?:1[6-9]|2\d|3[01])\.)/i.test(host) || /^\[?::1\]?$/.test(host) || host.endsWith('.local') ? '' : safe
}

export function hardwareFrequency(devices = [], works = [], filters = {}) {
  const byDevice = new Map(devices.filter(d => d.hardware_id && allowedCategories.has(d.category)).map(d => [d.hardware_id, d]))
  const grouped = new Map()
  for (const work of works) {
    const id = work.canonical_work_id || work.work_id
    if (!id || !work.title || work.relevance_status !== 'included') continue
    if (filters.month && hardwareMonth(work) !== filters.month) continue
    for (const usage of work.hardware_usage || []) {
      const device = byDevice.get(usage.hardware_id)
      if (!device || usage.review_status !== 'verified' || !allowedRoles.has(usage.role) || device.category !== usage.category || !sourceUrl(usage.source_url) || !usage.statement?.trim()) continue
      if (computeRoles.has(usage.role) && device.category !== 'compute_platform') continue
      if (filters.device && device.hardware_id !== filters.device) continue
      if (filters.category && device.category !== filters.category) continue
      if (filters.role && usage.role !== filters.role) continue
      if (filters.setting && usage.setting !== filters.setting) continue
      const group = grouped.get(device.hardware_id) || { ...device, byWork: new Map() }
      const source = group.byWork.get(id) || { work_id: id, title: work.title, first_public_date: work.first_public_date, first_public_date_precision: work.first_public_date_precision, original_url: originalSourceUrl(work), usages: [], seen: new Set() }
      const signature = JSON.stringify([usage.source_url, usage.source_locator, usage.role, usage.setting, usage.usage_scope, usage.statement, usage.configuration, usage.validation_context])
      if (!source.seen.has(signature)) { source.usages.push({ ...usage }); source.seen.add(signature) }
      group.byWork.set(id, source)
      grouped.set(device.hardware_id, group)
    }
  }
  const rows = [...grouped.values()].map(group => {
    const { byWork, ...device } = group
    const sources = [...byWork.values()].map(({ seen, ...source }) => source).sort((a, b) => (b.first_public_date || '').localeCompare(a.first_public_date || '') || a.work_id.localeCompare(b.work_id))
    const count = predicate => sources.filter(source => source.usages.some(predicate)).length
    return { ...device, work_count: sources.length,
      real_work_count: count(usage => usage.setting === 'real'),
      simulation_work_count: count(usage => usage.setting === 'simulation'),
      baseline_work_count: count(usage => usage.usage_scope === 'baseline'),
      calibration_work_count: count(usage => usage.usage_scope === 'calibration'),
      source_count: new Set(sources.flatMap(source => source.usages.map(usage => `${source.work_id}|${usage.source_url}`))).size,
      sources }
  }).sort((a, b) => b.work_count - a.work_count || a.name.localeCompare(b.name, 'en') || a.hardware_id.localeCompare(b.hardware_id))
  return { models: rows.filter(row => row.identity_level === 'model_specified'), unresolved: rows.filter(row => row.identity_level !== 'model_specified') }
}
