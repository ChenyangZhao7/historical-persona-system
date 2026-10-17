import { useState } from "react"
import axios from "axios"
import { API } from "../App"

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  row: { display: "flex", gap: 10, marginBottom: 12 },
  label: { fontSize: 12, fontWeight: 600, color: "var(--text3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, display: "block" },
  nodeCard: { border: "1px solid var(--border)", borderRadius: 8, padding: "12px 16px", marginBottom: 8 },
  nodeRow: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  nodeName: { fontSize: 14, fontWeight: 600, color: "var(--text)" },
  nodeEra: { fontSize: 12, color: "var(--text3)" },
  bar: { background: "var(--bg3)", borderRadius: 3, height: 5, marginTop: 10 },
  fill: (pct) => ({ width: `${pct}%`, background: "var(--primary)", height: "100%", borderRadius: 3 }),
  sim: { fontSize: 12, color: "var(--text3)", marginTop: 6 },
  edgeSection: { marginTop: 32 },
  edgeCard: { border: "1px solid var(--border)", borderRadius: 8, padding: "10px 16px", marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" },
  edgePair: { fontSize: 14, color: "var(--text)" },
  edgeScore: { fontSize: 12, color: "var(--text3)" },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginTop: 12 },
  center: { display: "inline-block", padding: "8px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "var(--text2)", marginBottom: 24 },
}

export default function Graph() {
  const [name, setName] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleGraph = async () => {
    if (!name.trim()) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await axios.post(`${API}/graph/`, { name: name.trim() })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Figure not found. Check the name matches a figure in the database.")
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Behavioural Graph</h2>
      <p style={S.desc}>Enter a historical figure to see their behavioural network — who they are most similar to, and how they are connected across civilisations.</p>

      <div style={S.row}>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleGraph()}
          placeholder="e.g. Julius Caesar, Genghis Khan, Marie Curie"
          style={{ flex: 1 }}
        />
        <button className="primary" onClick={handleGraph} disabled={loading}>
          {loading ? "Building…" : "Build Graph"}
        </button>
      </div>

      {error && <div style={S.err}>{error}</div>}

      {result && (
        <div style={{ marginTop: 32 }}>
          <div style={S.center}>Centre: <strong>{result.center}</strong></div>

          <h2 style={{ marginBottom: 16 }}>Connected Figures</h2>
          {(result.nodes || []).filter(n => n.type !== "target").map((node, i) => (
            <div key={i} style={S.nodeCard}>
              <div style={S.nodeRow}>
                <span style={S.nodeName}>{node.name}</span>
                <span style={S.nodeEra}>{node.era < 0 ? `${Math.abs(node.era)} BC` : `${node.era} AD`}</span>
              </div>
              {node.similarity !== undefined && (
                <>
                  <div style={S.bar}><div style={S.fill(node.similarity * 100)} /></div>
                  <div style={S.sim}>{(node.similarity * 100).toFixed(1)}% similarity</div>
                </>
              )}
            </div>
          ))}

          {result.edges && result.edges.length > 0 && (
            <div style={S.edgeSection}>
              <h2 style={{ marginBottom: 16 }}>Strongest Connections</h2>
              {result.edges.slice(0, 10).map((edge, i) => (
                <div key={i} style={S.edgeCard}>
                  <span style={S.edgePair}>{edge.source_name} — {edge.target_name}</span>
                  <span style={S.edgeScore}>{(edge.weight * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
