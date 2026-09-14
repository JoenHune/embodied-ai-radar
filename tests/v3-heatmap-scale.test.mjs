import test from 'node:test'
import assert from 'node:assert/strict'
import * as echarts from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { GridComponent, VisualMapComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'
import { heatmapScale } from '../docs/.vitepress/theme/lib/heatmap-scale.mjs'

echarts.use([HeatmapChart, GridComponent, VisualMapComponent, SVGRenderer])

test('heatmap scale ignores counts and extra tooltip dimensions', () => {
  assert.deepEqual(heatmapScale([[0, 0, 2.5, 400, 9000], [0, 1, 0.2, 5, 100]]), { dimension: 2, min: 0, max: 3 })
})

test('real ECharts rendering maps equal shares to equal colors regardless of tooltip counts', () => {
  const data = [[0, 0, 2, 300, 4000], [0, 1, 2, 1, 3], [0, 2, 0.2, 9999, 99999]]
  const chart = echarts.init(null, null, { renderer: 'svg', ssr: true, width: 320, height: 240 })
  try {
    chart.setOption({ animation: false, xAxis: { type: 'category', data: ['Aug'] }, yAxis: { type: 'category', data: ['A', 'B', 'C'] },
      visualMap: { ...heatmapScale(data), show: false, inRange: { color: ['#ffffff', '#0000ff'] } }, series: [{ type: 'heatmap', data }] })
    const color = index => chart.getVisual({ seriesIndex: 0, dataIndex: index }, 'color')
    assert.ok(color(0))
    assert.equal(color(0), color(1))
    assert.notEqual(color(0), color(2))
    assert.match(chart.renderToSVGString(), /<svg/)
  } finally { chart.dispose() }
})
