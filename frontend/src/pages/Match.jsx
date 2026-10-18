import { useState, useEffect, useCallback } from "react"
import axios from "axios"
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts"
import { API } from "../App"
import DraggableRadar from "../components/DraggableRadar"
import { MatchScore } from "../components/Similarity"
import { findMatches } from "../services/similarity"
import { saveVectors, loadVectors, getLastUpdated } from "../services/vectorStore"
import { formatEra } from "../services/format"

const DIMS = ["Oppression", "Group", "Principle", "Trust", "Change", "Emotion", "Motivation", "Mission", "Injustice", "Expression"]

const PRESETS = {
  "Equal":        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  "Mission-first":[0.5, 0.5, 1, 0.5, 1, 0.5, 1.5, 2, 1, 0.5],
  "Leadership":   [1.5, 1.5, 1, 1, 1.5, 0.5, 1, 1.5, 1, 1.5],
  "Idealist":     [1, 1, 2, 1, 1.5, 1, 1, 2, 1.5, 1],
  "Emotion":      [1, 1.5, 0.5, 1, 0.5, 2, 1, 1, 1.5, 1.5],
}

const S = {
  label: { fontSize: 12, fontWeight: 600, color: "var(--text3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, display: "block" },
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 24, lineHeight: 1.7 },
  card: { border: "1px solid var(--border)", borderRadius: 8, padding: "10px 14px", marginBottom: 8 },
  row: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  name: { fontSize: 14, fontWeight: 600, color: "var(--text)" },
  era: { fontSize: 12, color: "var(--text3)" },
  bar: { background: "var(--bg3)", borderRadius: 3, height: 5, marginTop: 8 },
  fill: (pct) => ({ width: `${pct}%`, background: "var(--primary)", height: "100%", borderRadius: 3 }),
  sim: { fontSize: 12, color: "var(--text3)", marginTop: 4 },
  saved: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "var(--text2)", marginTop: 24 },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginTop: 16 },
  weightRow: { display: "flex", alignItems: "center", gap: 8, marginBottom: 6 },
  weightLabel: { width: 90, fontSize: 12, color: "var(--text2)", flexShrink: 0 },
  weightVal: { width: 28, fontSize: 12, color: "var(--text3)", textAlign: "right", flexShrink: 0 },
  presetBtn: (active) => ({ padding: "4px 10px", fontSize: 11, borderRadius: 4, border: "1px solid " + (active ? "var(--text)" : "var(--border)"), background: active ? "var(--primary)" : "var(--bg)", color: active ? "var(--primary-inv)" : "var(--text2)", cursor: "pointer" }),
  cacheNote: { fontSize: 11, color: "var(--text4)", marginLeft: 12 },
}

export default function Match() {
  const [description, setDescription] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [weights, setWeights] = useState([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
  const [activePreset, setActivePreset] = useState("Equal")
  const [showWeights, setShowWeights] = useState(false)
  const [localFigures, setLocalFigures] = useState([])
  const [cacheDate, setCacheDate] = useState(null)
  const [explorerVector, setExplorerVector] = useState(null)
  const [explorerMatches, setExplorerMatches] = useState([])

  useEffect(() => {
    loadVectors().then(figs => { if (figs.length > 0) setLocalFigures(figs) })
    getLastUpdated().then(ts => { if (ts) setCacheDate(new Date(ts).toLocaleString()) })
  }, [])

  const refreshCache = async () => {
    try {
      const res = await axios.get(`${API}/figures/?evidence=false`)
      if (!Array.isArray(res.data)) return
      await saveVectors(res.data)
      setLocalFigures(res.data)
      setCacheDate(new Date().toLocaleString())
    } catch (err) {
      setError(err.response?.data?.detail || "Could not refresh the figure cache — is the API running?")
    }
  }

  const applyPreset = (name) => { setActivePreset(name); setWeights(PRESETS[name]) }

  const handleMatch = async () => {
    if (!description.trim()) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await axios.post(`${API}/match/`, { description, top_k: 5, weights })
      if (!res.data.matches?.length) {
        setError("No matches found. Go to Figures and add historical figures first.")
      } else {
        setResult(res.data)
        const vec = res.data.user_profile?.vector ?? Array(10).fill(0.5)
        const conf = res.data.user_profile?.confidence ?? null
        setExplorerVector(vec)
        setExplorerMatches([])
        localStorage.setItem("hps_profile", JSON.stringify({ vector: vec, confidence: conf, description, timestamp: Date.now() }))
        if (localFigures.length === 0) refreshCache()
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed. Please try again.")
    }
    setLoading(false)
  }

  const handleExplorerChange = useCallback((newVector) => {
    setExplorerVector(newVector)
    if (localFigures.length > 0) {
      setExplorerMatches(findMatches(newVector, localFigures, 5, weights))
    }
  }, [localFigures, weights])

  const radarData = result ? DIMS.map((dim, i) => ({ dimension: dim, value: result.user_profile.vector[i] })) : []

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Find Your Historical Mirror</h2>
      <p style={S.desc}>Describe your decisions, instincts, and patterns. The system builds your 10-dimensional behavioural profile and matches you to historical figures.</p>

      <span style={S.label}>Your description</span>
      <textarea
        value={description}
        onChange={e => setDescription(e.target.value)}
        placeholder="e.g. I act on instinct rather than planning. I resist authority when I believe it's unjust, but I need people around me…"
        style={{ width: "100%", height: 130, marginBottom: 12 }}
      />

      {/* Weights */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: showWeights ? 10 : 0 }}>
          <span style={{ ...S.label, margin: 0 }}>Weights</span>
          <button className="secondary" style={{ fontSize: 11, padding: "2px 8px" }} onClick={() => setShowWeights(w => !w)}>
            {showWeights ? "Hide" : "Customize"}
          </button>
          {Object.keys(PRESETS).map(name => (
            <button key={name} style={S.presetBtn(activePreset === name)} onClick={() => applyPreset(name)}>{name}</button>
          ))}
        </div>
        {showWeights && (
          <div style={{ padding: "12px 16px", border: "1px solid var(--border)", borderRadius: 8, background: "var(--bg2)", marginTop: 8 }}>
            {DIMS.map((dim, i) => (
              <div key={i} style={S.weightRow}>
                <span style={S.weightLabel}>{dim}</span>
                <input type="range" min={0} max={2} step={0.1} value={weights[i]}
                  onChange={e => { const n = [...weights]; n[i] = parseFloat(e.target.value); setWeights(n); setActivePreset("") }}
                  style={{ flex: 1 }}
                />
                <span style={S.weightVal}>{weights[i].toFixed(1)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center" }}>
        <button className="primary" onClick={handleMatch} disabled={loading}>
          {loading ? "Analysing…" : "Find My Historical Mirror"}
        </button>
        {localFigures.length > 0 && (
          <span style={S.cacheNote}>
            {localFigures.length} figures cached ·{" "}
            <span style={{ cursor: "pointer", textDecoration: "underline" }} onClick={refreshCache}>Refresh</span>
          </span>
        )}
      </div>

      {error && <div style={S.err}>{error}</div>}

      {result && (
        <div style={{ marginTop: 40 }}>
          <h2 style={{ marginBottom: 20 }}>Your Behavioural Profile</h2>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="currentColor" strokeOpacity={0.25} />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: "#888" }} />
              <Radar dataKey="value" stroke="currentColor" fill="currentColor" fillOpacity={0.15} strokeWidth={1.5} />
            </RadarChart>
          </ResponsiveContainer>

          <h2 style={{ marginTop: 32, marginBottom: 16 }}>Historical Matches</h2>
          {result.matches.map((m, i) => (
            <div key={i} className={`card-hover fade-up fade-up-delay-${i + 1}`} style={S.card}>
              <div style={S.row}>
                <span style={S.name}>{m.name}</span>
                <span style={S.era}>{formatEra(m.era)}</span>
              </div>
              <MatchScore match={m} aLabel="You" bLabel="Them" defaultOpen={i === 0} />
            </div>
          ))}

          {/* Interactive explorer */}
          {localFigures.length > 0 && explorerVector && (
            <div style={{ marginTop: 40 }}>
              <h2 style={{ marginBottom: 6 }}>Profile Explorer</h2>
              <p style={{ ...S.desc, marginBottom: 16 }}>Drag the radar vertices to adjust your profile — matches update instantly.</p>
              <div style={{ display: "flex", gap: 32, alignItems: "flex-start", flexWrap: "wrap" }}>
                <DraggableRadar vector={explorerVector} onChange={handleExplorerChange} />
                <div style={{ flex: 1, minWidth: 200 }}>
                  {(explorerMatches.length > 0 ? explorerMatches : result.matches).map((m, i) => (
                    <div key={i} style={S.card}>
                      <div style={S.row}>
                        <span style={S.name}>{m.name}</span>
                        <span style={S.era}>{formatEra(m.era)}</span>
                      </div>
                      <MatchScore match={m} aLabel="You" bLabel="Them" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div style={S.saved}>
            Profile saved — use it in <strong>Predict</strong> and <strong>Reconstruct</strong> without re-entering.
          </div>
        </div>
      )}
    </div>
  )
}
