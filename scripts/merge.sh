#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

OUTPUT="embodied-ai-radar-report.md"

strip_frontmatter() {
  awk 'BEGIN{skip=0}
    NR==1 && /^---$/ {skip=1; next}
    skip==1 && /^---$/ {skip=0; next}
    skip==0 {print}' "$1"
}

downgrade_headings() {
  awk '{ if (/^#{1,5} /) print "#" $0; else print }'
}

cat > "$OUTPUT" <<'HEADER'
# 具身智能研究雷达

> **数据截点**：2026 年 8 月 24 日<br>
> **主分析期**：2025 年 7 月—2026 年 6 月 · **7 月完整月** · **8 月前瞻快照**：1–24 日

---

HEADER

PAGES=(
  "docs/analysis/executive-summary.md"
  "docs/monthly/index.md"
  "docs/monthly/2025-07.md"
  "docs/monthly/2025-08.md"
  "docs/monthly/2025-09.md"
  "docs/monthly/2025-10.md"
  "docs/monthly/2025-11.md"
  "docs/monthly/2025-12.md"
  "docs/monthly/2026-01.md"
  "docs/monthly/2026-02.md"
  "docs/monthly/2026-03.md"
  "docs/monthly/2026-04.md"
  "docs/monthly/2026-05.md"
  "docs/monthly/2026-06.md"
  "docs/monthly/2026-07.md"
  "docs/monthly/2026-08.md"
  "docs/quarterly/index.md"
  "docs/analysis/annual.md"
  "docs/analysis/weak-signals.md"
  "docs/questions/index.md"
  "docs/questions/blind-spots.md"
  "docs/groups/index.md"
  "docs/groups/weekly/index.md"
  "docs/groups/organizations.md"
  "docs/groups/collaboration.md"
  "docs/frontiers/index.md"
  "docs/frontiers/foundation-models.md"
  "docs/frontiers/reasoning-planning.md"
  "docs/frontiers/world-models.md"
  "docs/frontiers/dexterous-manipulation.md"
  "docs/frontiers/humanoid-whole-body.md"
  "docs/frontiers/navigation-mobile-manipulation.md"
  "docs/frontiers/human-robot-interaction.md"
  "docs/frontiers/policy-learning.md"
  "docs/frontiers/data-engines.md"
  "docs/frontiers/simulation-transfer.md"
  "docs/frontiers/spatial-perception.md"
  "docs/frontiers/safety-evaluation.md"
  "docs/frontiers/continual-deployment-learning.md"
  "docs/frontiers/multi-robot-coordination.md"
  "docs/frontiers/embodied-multisensory.md"
  "docs/analysis/peer-review.md"
  "docs/analysis/institutions.md"
  "docs/analysis/benchmarks.md"
  "docs/database/index.md"
  "docs/methods/index.md"
  "docs/methods/expansion-protocol.md"
  "docs/methods/inclusion.md"
  "docs/methods/research-question-layer.md"
  "docs/methods/research-groups.md"
  "docs/references.md"
)

for page in "${PAGES[@]}"; do
  if [[ -f "$page" ]]; then
    strip_frontmatter "$page" | downgrade_headings >> "$OUTPUT"
    printf '\n---\n\n' >> "$OUTPUT"
  else
    echo "Missing generated page: $page" >&2
    exit 1
  fi
done

# Keep exactly one newline at EOF for clean diffs.
perl -0pi -e 's/\n+\z/\n/' "$OUTPUT"
cp "$OUTPUT" docs/public/
echo "Merged $OUTPUT ($(wc -l < "$OUTPUT") lines)"
