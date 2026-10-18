import { useState, useEffect } from "react"
import axios from "axios"
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts"
import { API } from "../App"
import { loadVectors, saveVectors } from "../services/vectorStore"

const DIMS = [
  "reaction_to_oppression", "group_dependency", "principle_vs_interest",
  "interpersonal_trust", "change_orientation", "emotional_stability",
  "core_motivation", "historical_mission", "response_to_injustice", "expression_style",
]

function computeBenchmark(figures) {
  if (!figures.length) return null
  const sums = new Array(10).fill(0)
  for (const fig of figures) fig.vector.forEach((v, i) => { sums[i] += v })
  const dimension_averages = {}
  DIMS.forEach((d, i) => { dimension_averages[d] = Math.round(sums[i] / figures.length * 1000) / 1000 })
  return {
    total_figures: figures.length,
    dimension_averages,
    insights: {
      high_mission_driven:  figures.filter(f => f.vector[7] > 0.7).length,
      high_change_oriented: figures.filter(f => f.vector[4] > 0.7).length,
      lone_wolves:          figures.filter(f => f.vector[1] < 0.3).length,
    },
  }
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
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  row:  { display: "flex", gap: 10, marginBottom: 24 },
  stat: { flex: 1, padding: 16, border: "1px solid var(--border)", borderRadius: 8, textAlign: "center", background: "var(--bg2)" },
  statNum:   { fontSize: 28, fontWeight: 600, color: "var(--text)" },
  statLabel: { fontSize: 12, color: "var(--text3)", marginTop: 4 },
  err: { fontSize: 13, color: "#dc2626", padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, marginBottom: 16 },
}

export default function Benchmark() {
  const [allFigures, setAllFigures] = useState([])
  const [era, setEra]         = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState("")

  useEffect(() => {
    getFigures()
      .then(figs => { if (Array.isArray(figs)) setAllFigures(figs) })
      .catch(() => setError("Could not load figures. Make sure the backend is running and go to Match to cache figures."))
      .finally(() => setLoading(false))
  }, [])

  const filtered = era
    ? allFigures.filter(f => f.period === era)
    : allFigures

  const countFor = p => allFigures.filter(f => f.period === p).length

  const result = computeBenchmark(filtered)

  const radarData = result
    ? Object.entries(result.dimension_averages).map(([key, val]) => ({
        dimension: key.replace(/_/g, " "),
        value: val,
      }))
    : []

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Behavioural Benchmark</h2>
      <p style={S.desc}>Global distribution of behavioural patterns across all historical figures in the database.</p>

      {error && <div style={S.err}>{error}</div>}

      <div style={S.row}>
        <select value={era} onChange={e => setEra(e.target.value)} style={{ flex: 1 }}>
          <option value="">All eras ({allFigures.length} figures)</option>
          <option value="ancient">古代 Ancient · before 476 ({countFor("ancient")})</option>
          <option value="medieval">中世纪 Medieval · 476–1499 ({countFor("medieval")})</option>
          <option value="early_modern">近代 Early modern · 1500–1916 ({countFor("early_modern")})</option>
          <option value="modern">现代 Modern · 1917–1944 ({countFor("modern")})</option>
          <option value="contemporary">当代 Contemporary · 1945+ ({countFor("contemporary")})</option>
          <option value="unknown">Unclassified ({countFor("unknown")})</option>
        </select>
      </div>

      {loading && (
        <div>
          <div className="skeleton" style={{ height: 320, borderRadius: 8, marginBottom: 24 }} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 8 }} />)}
          </div>
        </div>
      )}

      {!loading && result && (
        <div>
          <p style={{ fontSize: 13, color: "var(--text3)", marginBottom: 20 }}>
            {result.total_figures} figures analysed
          </p>

          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: "var(--text3)" }} />
              <Radar dataKey="value" stroke="var(--text)" fill="var(--text)" fillOpacity={0.12} strokeWidth={1.5} />
            </RadarChart>
          </ResponsiveContainer>

          <h2 style={{ marginTop: 32, marginBottom: 16 }}>Insights</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <div style={S.stat}>
              <div style={S.statNum}>{result.insights.high_mission_driven}</div>
              <div style={S.statLabel}>Mission-driven</div>
            </div>
            <div style={S.stat}>
              <div style={S.statNum}>{result.insights.high_change_oriented}</div>
              <div style={S.statLabel}>Change-oriented</div>
            </div>
            <div style={S.stat}>
              <div style={S.statNum}>{result.insights.lone_wolves}</div>
              <div style={S.statLabel}>Lone wolves</div>
            </div>
          </div>
        </div>
      )}

      {!loading && !result && !error && (
        <p style={{ color: "var(--text4)", fontSize: 13 }}>No figures loaded yet. Go to Match to cache figures.</p>
      )}
    </div>
  )
}
