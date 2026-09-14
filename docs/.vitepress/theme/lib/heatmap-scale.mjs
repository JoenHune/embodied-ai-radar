// Heatmap tuples are [x, y, value, ...tooltipMetadata]. Never let an added
// tooltip field silently become the visual-map dimension.
export function heatmapScale(rows) {
  return { dimension: 2, min: 0, max: Math.ceil(Math.max(1, ...rows.map(row => Number(row[2]) || 0))) }
}
