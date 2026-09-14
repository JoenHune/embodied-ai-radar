import test from 'node:test'
import assert from 'node:assert/strict'
import { publicMediaUrl, visualMediaCatalog } from '../scripts/lib/visual-media.mjs'

const people = [{ person_id: 'person:a', identity_status: 'profile_verified' }, { person_id: 'person:b', identity_status: 'candidate' }]
const asset = { entity_type: 'person', entity_id: 'person:a', image_url: 'https://example.edu/a.jpg', source_page: 'https://example.edu/a', rights_status: 'unknown', observed_at: '2026-09-07T01:00:00Z', verification_note: 'Official caption names this person', image_kind: 'portrait', alt: 'A' }
test('media URLs reject script, credentials, private hosts and signed access tokens', () => {
  for (const url of ['javascript:alert(1)', 'data:image/png,a', 'https://user:secret@example.org/a', 'https://localhost/a', 'https://127.0.0.1/a', 'https://example.org/a?access_token=secret']) assert.equal(publicMediaUrl(url, true), false)
  assert.equal(publicMediaUrl('https://image.mux.com/public/thumbnail.webp?time=1', true), true)
})
test('unresolved identity cannot receive another persons photograph', () => {
  assert.throws(() => visualMediaCatalog([{ ...asset, entity_id: 'person:b' }], people, []), /unresolved_person_photo/)
})
test('source metadata never grants image rights or validates a research result', () => {
  const result = visualMediaCatalog([asset], people, [])
  assert.equal(result.assets['person:a'].rights_status, 'unknown')
  assert.equal(result.assets['person:a'].media_is_research_validation, false)
})
test('large images are deferred; missing pictures remain missing', () => {
  const result = visualMediaCatalog([{ ...asset, byte_size: 5_000_000 }, { entity_type: 'person', entity_id: 'person:b', image_url: null }], people, [])
  assert.equal(result.assets['person:a'].defer_large, true)
  assert.equal(result.assets['person:b'], undefined)
})
test('unknown work and duplicate identity fail rather than silently attaching art', () => {
  assert.throws(() => visualMediaCatalog([asset, asset], people, []), /duplicate/)
  assert.throws(() => visualMediaCatalog([{ ...asset, entity_type: 'work', entity_id: 'work:missing', original_url: 'https://example.edu/paper' }], people, []), /unknown_media_work/)
})
test('generated imagery disclosure must be explicit, never inferred from other art', () => {
  assert.equal(visualMediaCatalog([asset], people, []).assets['person:a'].contains_generated_visuals, false)
  const work = { ...asset, entity_type: 'work', entity_id: 'arxiv:2608.00001', original_url: 'https://example.edu/paper', contains_generated_visuals: true }
  assert.equal(visualMediaCatalog([work], people, [work.entity_id]).assets[work.entity_id].contains_generated_visuals, true)
})
