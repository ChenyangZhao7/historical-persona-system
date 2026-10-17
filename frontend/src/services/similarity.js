const DIMS = 10

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

// weights = user-defined, confidence = figure's data quality
export function findMatches(queryVector, figures, topK = 5, weights = null) {
  const results = figures.map(fig => {
    const combined = fig.confidence
      ? fig.confidence.map((c, i) => c * (weights?.[i] ?? 1))
      : (weights ?? Array(DIMS).fill(1))
    const wq = queryVector.map((v, i) => v * combined[i])
    const wf = fig.vector.map((v, i) => v * combined[i])
    return { ...fig, score: Math.round(cosine(wq, wf) * 10000) / 10000 }
  })
  results.sort((a, b) => b.score - a.score)
  return results.slice(0, topK)
}
