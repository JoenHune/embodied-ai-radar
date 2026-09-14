import { onMounted, shallowRef } from 'vue'
import { withBase } from 'vitepress'

const evidence = shallowRef<Record<string, any[]>>({})
let request: Promise<void> | undefined
export function useEquipmentEvidence() {
  onMounted(() => {
    request ||= Promise.all([
      fetch(withBase('/api/v1/equipment/card-usage.json')).then(r => { if (!r.ok) throw Error('equipment unavailable'); return r.json() }),
      fetch(withBase('/api/v1/catalog-manifest.json')).then(r => { if (!r.ok) throw Error('catalog unavailable'); return r.json() }),
    ]).then(([body, manifest]) => {
      if (body.schema_version !== '1' || !body.by_work || body.dataset_version !== manifest.dataset_version) throw Error('equipment version mismatch')
      evidence.value = body.by_work
    }).catch(() => { evidence.value = {}; request = undefined })
  })
  return evidence
}
