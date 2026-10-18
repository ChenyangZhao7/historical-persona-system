import { useState } from "react"
import axios from "axios"
import { API } from "../App"
import { formatEra } from "../services/format"
import { MatchScore } from "../components/Similarity"

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  label: { fontSize: 12, fontWeight: 600, color: "var(--text3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, display: "block" },
  card: { border: "1px solid var(--border)", borderRadius: 8, padding: "12px 16px", marginBottom: 8 },
  cardRow: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  name: { fontSize: 14, fontWeight: 600, color: "var(--text)" },
  era: { fontSize: 12, color: "var(--text3)" },
  bar: { background: "var(--bg3)", borderRadius: 3, height: 5, marginTop: 10 },
  fill: (pct) => ({ width: `${pct}%`, background: "var(--primary)", height: "100%", borderRadius: 3 }),
  sim: { fontSize: 12, color: "var(--text3)", marginTop: 6 },
  reasoning: { fontSize: 13, color: "var(--text2)", lineHeight: 1.8, padding: "12px 16px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, marginBottom: 24 },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginTop: 12 },
}

export default function Relics() {
  const [description, setDescription] = useState("")
  const [material, setMaterial] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleMatch = async () => {
    if (!description.trim()) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await axios.post(`${API}/relics/match/`, { description, material })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed. Please try again.")
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Relic Attribution</h2>
      <p style={S.desc}>Describe an artefact. The system will build its behavioural profile and match it to historical figures with similar patterns.</p>

      <span style={S.label}>Material</span>
      <input
        value={material}
        onChange={e => setMaterial(e.target.value)}
        placeholder="e.g. bronze, jade, iron, stone"
        style={{ width: "100%", marginBottom: 16 }}
      />

      <span style={S.label}>Description</span>
      <textarea
        value={description}
        onChange={e => setDescription(e.target.value)}
        placeholder="Describe the relic — its form, symbols, purpose, scale, and context…"
        style={{ width: "100%", height: 120, marginBottom: 12 }}
      />
      <button className="primary" onClick={handleMatch} disabled={loading}>
        {loading ? "Analysing…" : "Match Relic"}
      </button>

      {error && <div style={S.err}>{error}</div>}

      {result && (
        <div style={{ marginTop: 32 }}>
          <h2 style={{ marginBottom: 12 }}>Relic Analysis</h2>
          <div style={S.reasoning}>{result.relic_profile?.reasoning}</div>

          <h2 style={{ marginBottom: 16 }}>Closest Historical Matches</h2>
          {(result.matches || []).map((match, i) => (
            <div key={i} className={`card-hover fade-up fade-up-delay-${i + 1}`} style={S.card}>
              <div style={S.cardRow}>
                <span style={S.name}>{match.name}</span>
                <span style={S.era}>{formatEra(match.era)}</span>
              </div>
              <MatchScore match={match} aLabel="Relic" bLabel="Figure" subject="the relic" defaultOpen={i === 0} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
