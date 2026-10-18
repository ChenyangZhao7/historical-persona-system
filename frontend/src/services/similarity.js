import { DIMENSION_KEYS } from "./dimensions"

const DIMS = DIMENSION_KEYS.length

export function cosine(a, b) {
  let dot = 0, magA = 0, magB = 0
  for (let i = 0; i < DIMS; i++) {
    dot += a[i] * b[i]
    magA += a[i] * a[i]
    magB += b[i] * b[i]
  }
  if (magA === 0 || magB === 0) return 0
  return dot / (Math.sqrt(magA) * Math.sqrt(magB))
}

export function weightedCosine(a, b, weights) {
  const wa = a.map((v, i) => v * (weights?.[i] ?? 1))
  const wb = b.map((v, i) => v * (weights?.[i] ?? 1))
  return cosine(wa, wb)
}

// Mirrors services/matcher.dimension_breakdown so the Profile Explorer shows
// the same numbers as the server-side match.
export function dimensionBreakdown(query, figure, queryConfidence = null, figureConfidence = null) {
  return DIMENSION_KEYS.map((key, i) => {
    const q = query[i] ?? 0
    const f = figure[i] ?? 0
    const gap = Math.abs(q - f)
    return {
      dimension: key,
      query: Math.round(q * 1000) / 1000,
      figure: Math.round(f * 1000) / 1000,
      gap: Math.round(gap * 1000) / 1000,
      closeness: Math.round(Math.max(0, 1 - gap) * 1000) / 1000,
      query_confidence: queryConfidence ? queryConfidence[i] ?? null : null,
      figure_confidence: figureConfidence ? figureConfidence[i] ?? null : null,
    }
  })
}

// Confidence- and weight-aware, so dimensions a figure says nothing about do
// not count as agreement, and dimensions the user weighted down count for
// less. See services/matcher.mean_closeness.
export function meanCloseness(breakdown, weights = null) {
  let weighted = 0, totalWeight = 0
  breakdown.forEach((dim, i) => {
    const userWeight = weights ? (weights[i] ?? 1) : 1
    const confidence = dim.figure_confidence === null || dim.figure_confidence === undefined
      ? 1
      : dim.figure_confidence
    const weight = userWeight * confidence
    weighted += dim.closeness * weight
    totalWeight += weight
  })
  if (totalWeight === 0) return weights ? meanCloseness(breakdown) : 0
  return Math.round((weighted / totalWeight) * 10000) / 10000
}

// Mirrors services/matcher.MIN_KNOWN_DIMENSIONS: a profile needs evidence on
// most of the ten dimensions before a similarity claim means anything.
export const MIN_KNOWN_DIMENSIONS = 6

export function knownDimensions(breakdown) {
  return breakdown.filter(
    d => d.figure_confidence === null || d.figure_confidence === undefined || d.figure_confidence > 0
  ).length
}

// weights = user-defined, confidence = figure's data quality.
// Ordered by `closeness`, the number the interface prints.
export function findMatches(queryVector, figures, topK = 5, weights = null) {
  const results = []
  for (const fig of figures) {
    const combined = fig.confidence
      ? fig.confidence.map((c, i) => c * (weights?.[i] ?? 1))
      : (weights ?? Array(DIMS).fill(1))
    const breakdown = dimensionBreakdown(queryVector, fig.vector, null, fig.confidence ?? null)
    const known = knownDimensions(breakdown)
    if (known < MIN_KNOWN_DIMENSIONS) continue
    const wq = queryVector.map((v, i) => v * combined[i])
    const wf = fig.vector.map((v, i) => v * combined[i])
    results.push({
      ...fig,
      score: Math.round(cosine(wq, wf) * 10000) / 10000,
      closeness: meanCloseness(breakdown, weights),
      known_dimensions: known,
      dimensions: breakdown,
    })
  }

  results.sort((a, b) => b.closeness - a.closeness)
  return results.slice(0, topK)
}
