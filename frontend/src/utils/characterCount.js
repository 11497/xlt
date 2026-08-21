const segmenter = typeof Intl !== 'undefined' && Intl.Segmenter
  ? new Intl.Segmenter(undefined, { granularity: 'grapheme' })
  : null

const splitCharacters = (value) => {
  const text = value || ''
  if (!segmenter) return Array.from(text)
  return Array.from(segmenter.segment(text), ({ segment }) => segment)
}

export const countCharacters = (value) => splitCharacters(value).length

export const truncateCharacters = (value, maxLength) => {
  if (maxLength <= 0) return ''
  return splitCharacters(value).slice(0, maxLength).join('')
}
