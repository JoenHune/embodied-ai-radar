const chineseSegmenter = new Intl.Segmenter('zh', { granularity: 'word' })
const stopWords = new Set('a an the of to and in for with on at by from as is are was were be been being we our ours this these that those it its which who whom whose have has had having can could would should will shall may might do does did doing than then there here where when while into onto out over under through about between among such very more most also both each other any all some'.split(' '))

export const SEARCH_TEXT_CONTRACT = Object.freeze({
  version: 'separator-boundaries-v2-decimal-atoms',
  separators: 'hyphens_and_underscores_are_word_boundaries',
  dotted_numbers: 'digit-dot chains use reserved zzqnumx...q atoms; 1.5, 15, 1.52 and 1.5.2 remain distinguishable',
  joined_spelling: 'not_implicitly_equivalent_unless_present_in_source_or_explicit_alias',
  full_title_query: 'paste_original_title_as_normal_fulltext; character_exact_quoted_punctuation_is_not_guaranteed',
  identity_queries: 'DOI_URL_work_id_and_pi_model_identity_are_resolved_before_fulltext_normalization',
  original_metadata: 'unchanged',
})

/** Normalize only the derived full-text representation, never raw metadata.
 * cross-embodiment, cross_embodiment and cross embodiment share query terms.
 * crossembodiment is a different spelling, not a synthetic compound alias.
 */
export function normalizeSearchBoundaries(value) {
  return String(value ?? '').normalize('NFKC')
    // Pagefind's zh index segmenter and query tokenizer treat bare decimals
    // differently (1.5 can become 1 + 5 in one and 15 in the other). Encode the
    // whole digit-dot chain in BOTH paths, without changing original metadata.
    // Surrounding spaces handle π0.5 and 1.5ms; the terminal q prevents prefix
    // matching from conflating the encoded 1.5 with 1.52 or version 1.5.2.
    .replace(/\d+(?:\.\d+)+/g, (number) => ` zzqnumx${number.replaceAll('.', 'x')}q `)
    .replace(/[-_\u2010-\u2015\u2212]+/g, ' ')
}

const piNotation = (value) => String(value ?? '').normalize('NFKC').toLowerCase().replace(/\\pi(?![a-z])/g, 'π')

/** Read model identity from title/project metadata, including TeX subscripts. */
export function piModelNames(value) {
  const text = piNotation(value)
  const names = [...text.matchAll(/(?:π|(?<![a-z0-9])pi)\s*(?:[_-]\s*)?(?:\{\s*)?(0(?:\s*\.\s*\d+)?)\s*(?:\})?(?![a-z0-9.])/g)]
    .map((match) => `pi${match[1].replace(/\s/g, '')}`)
  return [...new Set(names)]
}

/** Only a standalone model-name query becomes an exact model identity filter. */
export function piModelQuery(value) {
  const text = piNotation(value).replace(/\\[()[\]]/g, '').replace(/[$\s{}_]/g, '')
  const match = text.match(/^(?:π|pi-?)(0(?:\.\d+)?)$/)
  return match ? `pi${match[1]}` : null
}

/** Keep Chinese word boundaries identical for indexing and querying with English stemming. */
export function searchText(value, explicitChinese = false) {
  let result = normalizeSearchBoundaries(value).replace(/\b[a-zA-Z]+\b/g, (word) => stopWords.has(word.toLowerCase()) ? ' ' : word)
  if (explicitChinese) result = result.replace(/[\p{Script=Han}]+/gu, (run) => [...chineseSegmenter.segment(run)].map((part) => part.segment).join(' '))
  return result.replace(/\s+/g, ' ').trim()
}
