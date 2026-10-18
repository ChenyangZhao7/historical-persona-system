import { useState, useEffect } from "react"
import axios from "axios"
import { API } from "../App"
import { SkeletonList } from "../components/Skeleton"
import { formatEra } from "../services/format"

const DIMS = ["Oppression", "Group", "Principle", "Trust", "Change", "Emotion", "Motivation", "Mission", "Injustice", "Expression"]

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  row: { display: "flex", gap: 10, marginBottom: 12 },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginBottom: 16 },
  success: { padding: 16, background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, marginBottom: 24 },
  card: { border: "1px solid var(--border)", borderRadius: 8, marginBottom: 8, overflow: "hidden" },
  cardHeader: (expanded) => ({
    padding: "12px 16px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    cursor: "pointer",
    background: expanded ? "var(--bg2)" : "var(--bg)",
  }),
  cardBody: { padding: "0 16px 16px" },
  dimRow: { display: "flex", alignItems: "center", gap: 8, marginBottom: 4 },
  dimLabel: { width: 80, fontSize: 11, color: "var(--text3)", flexShrink: 0 },
  bar: { flex: 1, background: "var(--bg3)", borderRadius: 3, height: 5 },
  fill: (pct, low) => ({ width: `${pct}%`, background: low ? "var(--text4)" : "var(--text)", height: "100%", borderRadius: 3, transition: "width 0.4s" }),
  dimVal: { width: 30, fontSize: 11, color: "var(--text3)", textAlign: "right" },
}

function DimBars({ vector, confidence }) {
  return (
    <div style={{ marginTop: 8 }}>
      {DIMS.map((dim, i) => (
        <div key={i} style={S.dimRow}>
          <span style={S.dimLabel}>{dim}</span>
          <div style={S.bar}>
            <div style={S.fill((vector[i] ?? 0) * 100, confidence && confidence[i] < 0.3)} />
          </div>
          <span style={S.dimVal}>{(vector[i] ?? 0).toFixed(2)}</span>
        </div>
      ))}
    </div>
  )
}

function FigureCard({ figure, expanded, onToggle }) {
  const era = formatEra(figure.era)
  return (
    <div className="card-hover" style={S.card}>
      <div style={S.cardHeader(expanded)} onClick={onToggle}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>{figure.name}</span>
          <span style={{ fontSize: 12, color: "var(--text3)" }}>{era}</span>
          {figure.period && (
            <span style={{ fontSize: 11, color: "var(--text3)", background: "var(--bg3)", padding: "1px 6px", borderRadius: 4 }}>{figure.period}</span>
          )}
        </div>
        <span style={{ color: "var(--text4)", fontSize: 11 }}>{expanded ? "▲" : "▼"}</span>
      </div>
      {expanded && (
        <div style={S.cardBody}>
          <DimBars vector={figure.vector} confidence={figure.confidence} />
          {figure.evidence && (
            <details style={{ marginTop: 10 }}>
              <summary style={{ fontSize: 11, color: "var(--text4)", cursor: "pointer" }}>Evidence</summary>
              <ul style={{ fontSize: 11, color: "var(--text3)", marginTop: 6, paddingLeft: 16, lineHeight: 1.8 }}>
                {figure.evidence.map((e, i) => <li key={i}><strong>{DIMS[i]}:</strong> {e}</li>)}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

export default function Figures() {
  const [name, setName] = useState("")
  const [supplement, setSupplement] = useState("")
  const [showSupplement, setShowSupplement] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState("")
  const [figures, setFigures] = useState([])
  const [loadingList, setLoadingList] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [search, setSearch] = useState("")

  const loadFigures = async () => {
    setLoadingList(true)
    try {
      const res = await axios.get(`${API}/figures/`)
      if (Array.isArray(res.data)) {
        setFigures(res.data)
        setError("")
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load figures — is the API running?")
    }
    setLoadingList(false)
  }

  useEffect(() => { loadFigures() }, [])

  const handleAnalyze = async () => {
    if (!name.trim()) return
    setAnalyzing(true)
    setError("")
    setResult(null)
    try {
      const res = await axios.post(`${API}/analyze/`, {
        name: name.trim(),
        supplementary_text: supplement.trim()
      })
      setResult(res.data)
      setName("")
      setSupplement("")
      setShowSupplement(false)
      await loadFigures()
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed. Check the name is a valid Wikipedia entry.")
    }
    setAnalyzing(false)
  }

  const filtered = figures.filter(f => f.name.toLowerCase().includes(search.toLowerCase()))

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Search data</h2>
      <p style={S.desc}>
        Enter an English name exactly as it appears on Wikipedia. The system extracts their 10-dimensional behavioural profile and adds them to the database.
      </p>

      <div style={S.row}>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !showSupplement && handleAnalyze()}
          placeholder="e.g. Napoleon Bonaparte, Cao Cao, Alan Turing"
          style={{ flex: 1 }}
        />
        <button className="primary" onClick={handleAnalyze} disabled={analyzing} style={{ whiteSpace: "nowrap" }}>
          {analyzing ? "Analysing…" : "Analyse"}
        </button>
      </div>

      {/* Supplementary text toggle */}
      <div style={{ marginTop: 10, marginBottom: 4 }}>
        <button
          className="secondary"
          style={{ fontSize: 12, padding: "4px 10px" }}
          onClick={() => setShowSupplement(s => !s)}
        >
          {showSupplement ? "Hide supplementary source" : "+ Add supplementary source"}
        </button>
        {!showSupplement && supplement.trim() && (
          <span style={{ fontSize: 11, color: "var(--text3)", marginLeft: 10 }}>
            {supplement.trim().length} chars of supplementary text ready
          </span>
        )}
      </div>

      {showSupplement && (
        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, display: "block" }}>
            Supplementary source
          </span>
          <p style={{ fontSize: 12, color: "var(--text4)", marginBottom: 8, lineHeight: 1.6 }}>
            Paste any text — academic paper, book excerpt, primary source, biography passage. The system will combine it with Wikipedia before analysis.
            If this figure already exists in the database, providing supplementary text will trigger a re-analysis.
          </p>
          <textarea
            value={supplement}
            onChange={e => setSupplement(e.target.value)}
            placeholder="Paste additional source text here…"
            style={{ width: "100%", height: 140, fontSize: 13 }}
          />
        </div>
      )}

      {error && <div style={S.err}>{error}</div>}

      {result && (
        <div style={S.success}>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 8 }}>
            {result.reanalyzed ? "↻" : "✓"} {result.name} {result.reanalyzed ? "re-analysed" : result.cached ? "(cached)" : "added"}
          </div>
          <DimBars vector={result.profile.vector} confidence={result.profile.confidence} />
        </div>
      )}

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "24px 0" }} />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>
          Database
          <span style={{ fontSize: 13, fontWeight: 400, color: "var(--text3)", marginLeft: 8 }}>{figures.length} figures</span>
        </h2>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search…"
          style={{ width: 160, padding: "6px 12px", fontSize: 13 }}
        />
      </div>

      {loadingList ? (
        <SkeletonList count={6} />
      ) : figures.length === 0 ? (
        <p style={{ color: "var(--text4)", fontSize: 13 }}>No figures yet. Add someone above to get started.</p>
      ) : filtered.length === 0 ? (
        <p style={{ color: "var(--text4)", fontSize: 13 }}>No results for "{search}"</p>
      ) : (
        filtered.map(fig => (
          <FigureCard
            key={fig.id}
            figure={fig}
            expanded={expandedId === fig.id}
            onToggle={() => setExpandedId(expandedId === fig.id ? null : fig.id)}
          />
        ))
      )}
    </div>
  )
}
