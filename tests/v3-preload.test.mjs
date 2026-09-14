import test from 'node:test'
import assert from 'node:assert/strict'
import config from '../docs/.vitepress/config.ts'

const chunks = ['RadarDashboard', 'PeopleRadar', 'HardwareRadar', 'HardwareCoverage', 'LocoManipRadar', 'DatabaseExplorer', 'PulseFeed', 'ConferenceRadar', 'OrganizationCoverage', 'ReportCoverage', 'VPLocalSearchBox', 'echarts', 'v3-overview', 'runtime-core.esm-bundler', 'app']
const retained = async (page) => {
  const head = chunks.map((name) => ['link', { rel: 'modulepreload', href: `/embodied-ai-radar/assets/chunks/${name}.fixture.js` }])
  await config.transformHead({ page, head })
  return head.map(([, { href }]) => chunks.find((name) => href.endsWith(`/${name}.fixture.js`)))
}
test('ordinary routes do not eagerly fetch the radar or its large data/chart dependencies', async () => {
  assert.deepEqual(await retained('database/index.md'), ['DatabaseExplorer', 'runtime-core.esm-bundler', 'app'])
  assert.deepEqual(await retained('methods/inclusion.md'), ['runtime-core.esm-bundler', 'app'])
})
test('rendered routes retain their actual dependencies', async () => {
  assert.deepEqual(await retained('monthly/index.md'), ['RadarDashboard', 'echarts', 'v3-overview', 'runtime-core.esm-bundler', 'app'])
  assert.deepEqual(await retained('pulse/index.md'), ['PulseFeed', 'runtime-core.esm-bundler', 'app'])
  assert.deepEqual(await retained('methods/coverage.md'), ['OrganizationCoverage', 'runtime-core.esm-bundler', 'app'])
})
test('report coverage is loaded only on organization profiles and overview', async () => {
  assert.ok((await retained('organizations/index.md')).includes('ReportCoverage'))
  assert.ok((await retained('organizations/generalist-ai.md')).includes('ReportCoverage'))
  assert.ok(!(await retained('organizations/collaboration.md')).includes('ReportCoverage'))
  assert.ok(!(await retained('index.md')).includes('ReportCoverage'))
  assert.ok(!(await retained('organizations/people/index.md')).includes('ReportCoverage'))
})
test('people route loads its own charts without the full organization overview', async () => {
  assert.deepEqual(await retained('organizations/people/index.md'), ['PeopleRadar', 'echarts', 'runtime-core.esm-bundler', 'app'])
})
test('equipment routes load only their own component and shared charts', async () => {
  assert.deepEqual(await retained('hardware/index.md'), ['HardwareRadar', 'HardwareCoverage', 'echarts', 'runtime-core.esm-bundler', 'app'])
  assert.deepEqual(await retained('hardware/coverage.md'), ['HardwareCoverage', 'runtime-core.esm-bundler', 'app'])
  assert.deepEqual(await retained('trends/loco-manip/index.md'), ['LocoManipRadar', 'echarts', 'runtime-core.esm-bundler', 'app'])
  assert.deepEqual(await retained('methods/equipment-loco.md'), ['runtime-core.esm-bundler', 'app'])
})
test('equipment routes keep card/chart helpers but not dashboard-specific trend or feed dependencies', async () => {
  const names = ['ChartFrame', 'useEChart', 'ResearchCard', 'SourceImage', 'DirectionTrendGrid', 'DirectionTrendChart', 'monthlySeries', 'ResearchFeed', 'DirectionShareOverview']
  for (const page of ['hardware/index.md', 'trends/loco-manip/index.md']) {
    const head = names.map(name => ['link', { rel: 'modulepreload', href: `/embodied-ai-radar/assets/${name}.fixture.js` }])
    await config.transformHead({ page, head })
    assert.deepEqual(head.map(([, { href }]) => names.find(name => href.endsWith(`/${name}.fixture.js`))), ['ChartFrame', 'useEChart', 'ResearchCard', 'SourceImage'])
  }
})
