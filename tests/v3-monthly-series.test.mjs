import test from 'node:test'
import assert from 'node:assert/strict'
import { completeMonthRange, monthlyValueLabel, splitMonthlySeries } from '../docs/.vitepress/theme/lib/monthlySeries.ts'

const complete = Array.from({ length: 12 }, (_, index) => {
  const date = new Date(Date.UTC(2025, 8 + index, 1))
  return date.toISOString().slice(0, 7)
})
const months = [...complete, '2026-09']
const values = [...Array(11).fill(0.1), 0.174359, 0]

test('uncollected September does not create a plunge from August', () => {
  const result = splitMonthlySeries(months, values, complete, '2026-09', false)
  assert.equal(result.complete[11], 0.174359)
  assert.equal(result.complete[12], null)
  assert.equal(result.provisional[12], null)
  assert.equal(result.display[12], null)
  assert.equal(monthlyValueLabel(result.display[12], 'shares'), '未知（暂无采集数据）')
})
test('observed provisional data remains an isolated series, including a real zero', () => {
  for (const value of [0, 0.07]) {
    const result = splitMonthlySeries(months, [...values.slice(0, 12), value], complete, '2026-09', true)
    assert.equal(result.complete[12], null)
    assert.equal(result.provisional[12], value)
    assert.ok(result.provisional.slice(0, 12).every((entry) => entry === null))
  }
})
test('missing complete-month data stays missing while measured zero stays zero', () => {
  const result = splitMonthlySeries(['2026-06', '2026-07', '2026-08'], [0, undefined, NaN], ['2026-06', '2026-07', '2026-08'], '2026-09', false)
  assert.deepEqual(result.complete, [0, null, null])
  assert.equal(monthlyValueLabel(0, 'counts'), '0')
})
test('caption ends the complete interval in August and identifies the extra September column', () => {
  assert.equal(completeMonthRange(complete, '2026-09'), '2025-09—2026-08 完整月；2026-09 暂行月独立展示')
})
