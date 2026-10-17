import { useState, useEffect, useRef } from "react"
import axios from "axios"
import { API } from "../App"
import { loadVectors, saveVectors } from "../services/vectorStore"

// Mid-tone colours so a dot is legible on both the light and the dark theme.
const PERIOD_COLORS = {
  ancient: "#6b7280",
  medieval: "#8b5cf6",
  "early modern": "#0ea5e9",
  modern: "#f59e0b",
  contemporary: "#10b981",
  unknown: "#9ca3af",
}

// The backend stores lowercase periods ("ancient", "modern", "unknown"), so the
// old capitalised keys never matched and every dot fell through to the default.
function getColor(period) {
  const key = (period || "").trim().toLowerCase()
  if (PERIOD_COLORS[key]) return PERIOD_COLORS[key]
  for (const [name, color] of Object.entries(PERIOD_COLORS)) {
    if (key.includes(name)) return color
  }
  return PERIOD_COLORS.unknown
}

function formatEra(era) {
  if (era === null || era === undefined || Number.isNaN(era)) return "era unknown"
  return era < 0 ? `${Math.abs(era)} BC` : `${era} AD`
}

function pca2d(vectors) {
  const n = vectors.length
  const d = vectors[0].length

  const mean = new Array(d).fill(0)
  for (const v of vectors) v.forEach((x, j) => { mean[j] += x / n })
  const X = vectors.map(v => v.map((x, j) => x - mean[j]))

  const cov = Array.from({ length: d }, (_, i) =>
    Array.from({ length: d }, (_, j) =>
      X.reduce((s, row) => s + row[i] * row[j], 0) / (n - 1)
    )
  )

  function powerIter(mat, steps = 200) {
    // Fixed start vector: a random one made the projection (and the axis
    // signs) change on every render.
    let v = new Array(d).fill(0).map((_, i) => (i === 0 ? 1 : 0.5 ** i))
    for (let s = 0; s < steps; s++) {
      const mv = mat.map(row => row.reduce((s, x, j) => s + x * v[j], 0))
      const norm = Math.sqrt(mv.reduce((s, x) => s + x * x, 0)) || 1
      v = mv.map(x => x / norm)
    }
    return v
  }

  const pc1 = powerIter(cov)
  const lambda1 = pc1.reduce((s, x, i) => s + x * cov[i].reduce((t, y, j) => t + y * pc1[j], 0), 0)
  const deflated = cov.map((row, i) =>
    row.map((x, j) => x - lambda1 * pc1[i] * pc1[j])
  )
  const pc2 = powerIter(deflated)

  return X.map(row => [
    row.reduce((s, x, j) => s + x * pc1[j], 0),
    row.reduce((s, x, j) => s + x * pc2[j], 0),
  ])
}

async function getFigures() {
  const cached = await loadVectors()
  if (cached.length > 0) return cached
  const res = await axios.get(`${API}/figures/?evidence=false`)
  if (Array.isArray(res.data) && res.data.length > 0) {
    await saveVectors(res.data)
    return res.data
  }
  return []
}

const S = {
  desc:       { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  legend:     { display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 20 },
  legendItem: { display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text2)" },
  dot:        (color) => ({ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 }),
  tooltip:    { position: "fixed", background: "var(--text)", color: "var(--primary-inv)", padding: "6px 10px", borderRadius: 6, fontSize: 12, pointerEvents: "none", zIndex: 100, whiteSpace: "nowrap" },
  controls:   { display: "flex", gap: 10, marginBottom: 16, alignItems: "center" },
}

export default function Cluster() {
  const [figures, setFigures] = useState([])
  const [coords,  setCoords]  = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState("")
  const [tooltip, setTooltip] = useState(null)
  const [search,  setSearch]  = useState("")
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    getFigures()
      .then(figs => {
        if (!Array.isArray(figs) || figs.length < 3) {
          setError("Not enough figures. Go to Search data to add figures, or go to Match to cache them.")
          return
        }
        const vectors = figs.map(f => f.vector)
        const pts = pca2d(vectors)
        setFigures(figs)
        setCoords(pts)
      })
      .catch(() => setError("Could not load figures. Make sure the backend is running."))
      .finally(() => setLoading(false))
  }, [])

  const recompute = () => {
    if (!figures.length) return
    setCoords(pca2d(figures.map(f => f.vector)))
  }

  const W = 680, H = 480, PAD = 32
  const xs = coords.map(p => p[0])
  const ys = coords.map(p => p[1])
  const minX = Math.min(...xs), maxX = Math.max(...xs)
  const minY = Math.min(...ys), maxY = Math.max(...ys)
  const rangeX = maxX - minX || 1
  const rangeY = maxY - minY || 1
  const scaleX = x => PAD + ((x - minX) / rangeX) * (W - PAD * 2)
  const scaleY = y => PAD + ((y - minY) / rangeY) * (H - PAD * 2)

  const searchLower = search.toLowerCase()

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Behavioural Map</h2>
      <p style={S.desc}>
        {figures.length > 0
          ? `${figures.length} figures projected to 2D using PCA. Proximity = behavioural similarity.`
          : "Figures projected to 2D. Proximity = behavioural similarity."}
      </p>

      {error && <div style={{ fontSize: 13, color: "#dc2626", padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, marginBottom: 16 }}>{error}</div>}

      {loading && (
        <div className="skeleton" style={{ height: 480, borderRadius: 8 }} />
      )}

      {!loading && coords.length > 0 && (
        <>
          <div style={S.legend}>
            {Object.entries(PERIOD_COLORS).filter(([k]) => k).map(([period, color]) => (
              <div key={period} style={S.legendItem}>
                <div style={S.dot(color)} />{period}
              </div>
            ))}
          </div>

          <div style={S.controls}>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Highlight a figure…"
              style={{ width: 200, padding: "6px 12px", fontSize: 13 }}
            />
            <button className="secondary" style={{ fontSize: 12, padding: "6px 12px" }} onClick={recompute}>
              Recompute
            </button>
          </div>

          <div style={{ border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden", background: "var(--bg2)" }}>
            <svg width={W} height={H} style={{ display: "block" }}>
              {figures.map((fig, i) => {
                const x = scaleX(coords[i][0])
                const y = scaleY(coords[i][1])
                const color = getColor(fig.period)
                const highlighted = search && fig.name.toLowerCase().includes(searchLower)
                const isSelected = selected?.id === fig.id
                return (
                  <g key={fig.id}>
                    <circle
                      cx={x} cy={y}
                      r={highlighted || isSelected ? 7 : 4}
                      fill={highlighted || isSelected ? "var(--text)" : color}
                      fillOpacity={highlighted || isSelected ? 1 : 0.7}
                      stroke={isSelected ? "var(--text)" : "none"}
                      strokeWidth={2}
                      style={{ cursor: "pointer" }}
                      onMouseEnter={e => setTooltip({ x: e.clientX + 12, y: e.clientY - 8, name: fig.name, era: fig.era, period: fig.period })}
                      onMouseLeave={() => setTooltip(null)}
                      onClick={() => setSelected(isSelected ? null : fig)}
                    />
                    {highlighted && (
                      <text x={x + 8} y={y + 4} fontSize={10} fill="var(--text)" fontWeight={600}>{fig.name}</text>
                    )}
                  </g>
                )
              })}
            </svg>
          </div>

          {selected && (
            <div style={{ marginTop: 12, padding: "10px 16px", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13, background: "var(--bg2)" }}>
              <strong style={{ color: "var(--text)" }}>{selected.name}</strong>
              <span style={{ color: "var(--text3)", marginLeft: 10 }}>
                {formatEra(selected.era)}
              </span>
              {selected.period && <span style={{ color: "var(--text4)", marginLeft: 8 }}>{selected.period}</span>}
            </div>
          )}
        </>
      )}

      {tooltip && (
        <div style={{ ...S.tooltip, left: tooltip.x, top: tooltip.y }}>
          {tooltip.name} · {formatEra(tooltip.era)}
        </div>
      )}
    </div>
  )
}
