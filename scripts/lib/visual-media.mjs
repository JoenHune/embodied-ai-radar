import crypto from 'node:crypto'

export function publicMediaUrl(value, image = false) {
  if (typeof value !== 'string') return false
  try {
    const url = new URL(value)
    if (!(image ? ['https:'] : ['https:', 'http:']).includes(url.protocol) || url.username || url.password) return false
    if (/^(localhost|127\.|10\.|192\.168\.|0\.|\[::1\])|\.local$/i.test(url.hostname)) return false
    return ![...url.searchParams.keys()].some(key => /^(access_token|auth_token|x-amz-signature|x-goog-credential)$/i.test(key))
  } catch { return false }
}

export function visualMediaCatalog(records, persons, workIds) {
  const people = new Map(persons.map(person => [person.person_id, person]))
  const works = new Set(workIds)
  const seen = new Set()
  const assets = {}
  for (const record of records) {
    const key = record.entity_id
    if (!key || seen.has(key)) throw Error(`duplicate_or_missing_media_entity:${key}`)
    seen.add(key)
    if (record.entity_type === 'person') {
      if (!people.has(key)) throw Error(`unknown_media_person:${key}`)
      if (record.image_url && people.get(key).identity_status !== 'profile_verified') throw Error(`unresolved_person_photo:${key}`)
    } else if (record.entity_type === 'work') {
      if (!works.has(key)) throw Error(`unknown_media_work:${key}`)
      if (!publicMediaUrl(record.original_url)) throw Error(`media_original_url_invalid:${key}`)
    } else throw Error(`unknown_media_kind:${key}`)
    if (!record.image_url) continue
    if (!publicMediaUrl(record.image_url, true) || !publicMediaUrl(record.source_page)) throw Error(`media_source_url_invalid:${key}`)
    if (!record.observed_at || !record.rights_status || !record.verification_note) throw Error(`media_provenance_required:${key}`)
    const size = Number.isFinite(record.byte_size) ? record.byte_size : null
    assets[key] = {
      entity_id: key, entity_type: record.entity_type, image_url: record.image_url,
      source_page: record.source_page, original_url: record.original_url || null,
      alt: record.alt || record.caption || record.title || record.name,
      caption: record.caption || null, credit: record.credit || null,
      image_kind: record.image_kind, rights_status: record.rights_status,
      observed_at: record.observed_at, byte_size: size,
      defer_large: size !== null && size > (record.entity_type === 'person' ? 4_000_000 : 2_000_000),
      animated: Boolean(record.animated || /\.gif(?:\?|$)/i.test(record.image_url)),
      width: record.width || record.dimensions?.width || null,
      height: record.height || record.dimensions?.height || null,
      media_is_research_validation: false,
      company_self_report: record.company_self_report === true,
      contains_generated_visuals: record.contains_generated_visuals === true,
    }
  }
  return {
    schema_version: '1', registry_hash: crypto.createHash('sha256').update(JSON.stringify(records)).digest('hex'),
    assets, counts: { registered: records.length, available: Object.keys(assets).length,
      portraits: Object.values(assets).filter(row => row.entity_type === 'person').length,
      work_images: Object.values(assets).filter(row => row.entity_type === 'work').length },
    policy: 'Official source-linked imagery; no local copy, permission inference, or evidence-grade promotion. Lazy-loaded portraits over 4 MB and research images over 2 MB are deferred until explicitly opened.',
  }
}
