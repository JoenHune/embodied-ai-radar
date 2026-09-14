import test from 'node:test'
import assert from 'node:assert/strict'
import { compactResultCard } from '../scripts/lib/search-records.mjs'

test('browse cards preserve rendered fields and identity without duplicating detail metadata', () => {
  const original = { id: 'handle', url: '/database/?work=a', excerpt: 'Original excerpt', meta: {
    work_id: 'a', original_url: 'https://example.edu/paper', title: 'Complete original title', title_zh: '中文标题', summary: '摘要', date: '2026-08', date_precision: 'month',
    evidence: 'E1', direction: 'D1', organizations: 'Lab', output_types: 'technical_report', venues: '', peer_reviewed: 'false',
    text_cutoff: '2026-08-31', text_status: 'available', text_version: 'v2', text_version_status: 'archived_text_selected', text_cutoff_applicability: 'applied_to_selected_text', authors: 'Large author list', publication_dates: '[many versions]',
  } }
  const before = structuredClone(original)
  const card = compactResultCard(original)
  for (const key of ['work_id', 'title', 'title_zh', 'summary', 'date', 'date_precision', 'evidence', 'direction', 'organizations', 'output_types', 'venues', 'peer_reviewed', 'text_cutoff', 'text_status', 'text_version', 'text_version_status', 'text_cutoff_applicability']) assert.equal(card.meta[key], original.meta[key])
  assert.equal(card.url, original.url)
  assert.equal(card.meta.original_url, 'https://example.edu/paper')
  assert.equal(card.excerpt, original.excerpt)
  assert.equal(card.meta.authors, undefined)
  assert.equal(card.meta.publication_dates, undefined)
  assert.deepEqual(original, before, 'Complete result shard must remain intact')
})
