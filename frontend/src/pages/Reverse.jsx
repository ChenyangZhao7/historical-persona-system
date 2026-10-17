import { useState } from "react"
import axios from "axios"
import { API } from "../App"

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  row: { display: "flex", gap: 10, marginBottom: 12 },
  card: { border: "1px solid var(--border)", borderRadius: 8, padding: "12px 16px", marginBottom: 8 },
  cardRow: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  name: { fontSize: 14, fontWeight: 600, color: "var(--text)" },
  era: { fontSize: 12, color: "var(--text3)" },
  bar: { background: "var(--bg3)", borderRadius: 3, height: 5, marginTop: 10 },
  fill: (pct) => ({ width: `${pct}%`, background: "var(--primary)", height: "100%", borderRadius: 3 }),
  sim: { fontSize: 12, color: "var(--text3)", marginTop: 6 },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginTop: 12 },
}

export default function Reverse() {
  const [name, setName] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSearch = async () => {
    if (!name.trim()) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await axios.get(`${API}/reverse/${encodeURIComponent(name.trim())}?top_k=5`)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Figure not found. Check the name matches a figure in the database.")
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Cross-Civilisation Equivalents</h2>
      <p style={S.desc}>Enter a historical figure to find their behavioural counterparts across different civilisations and eras.</p>

      <div style={S.row}>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSearch()}
          placeholder="e.g. Napoleon Bonaparte, Confucius, Cleopatra"
          style={{ flex: 1 }}
        />
        <button className="primary" onClick={handleSearch} disabled={loading}>
          {loading ? "Searching…" : "Find Equivalents"}
        </button>
      </div>

      {error && <div style={S.err}>{error}</div>}

      {result && (
        <div style={{ marginTop: 32 }}>
          <h2 style={{ marginBottom: 16 }}>Similar to {result.query}</h2>
          {(result.matches || []).map((match, i) => (
            <div key={i} className={`card-hover fade-up fade-up-delay-${i + 1}`} style={S.card}>
              <div style={S.cardRow}>
                <span style={S.name}>{match.name}</span>
                <span style={S.era}>{match.era < 0 ? `${Math.abs(match.era)} BC` : `${match.era} AD`}</span>
              </div>
              <div style={S.bar}><div style={S.fill(match.score * 100)} /></div>
              <div style={S.sim}>{(match.score * 100).toFixed(1)}% behavioural similarity</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
