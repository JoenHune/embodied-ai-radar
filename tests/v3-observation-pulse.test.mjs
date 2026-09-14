import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
const code = fs.readFileSync(new URL('../docs/.vitepress/theme/components/PulseFeed.vue', import.meta.url), 'utf8')
test('software support relationships never imply corporate research execution', () => {
  assert.ok(code.includes("['supported_by', 'officially_supports_development'].includes(event.attribution_relation)"))
  assert.ok(code.includes('（支持关系）'))
  assert.ok(code.includes('不等同于该公司独立完成研究'))
})
test('reviewed software and explainer updates remain outside new-research selection', () => {
  assert.ok(code.includes("new Set(['research_explainer', 'code_release'])"))
  assert.ok(code.includes("event.review_status === 'verified'"))
  assert.ok(code.includes("selected.value === 'research' ? !strategic && !context"))
  assert.ok(code.includes('不重复计为新论文或新模型'))
})
