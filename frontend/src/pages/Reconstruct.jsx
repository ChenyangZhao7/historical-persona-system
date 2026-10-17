import { useState, useEffect } from "react"
import axios from "axios"
import { API } from "../App"

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  modeRow: { display: "flex", gap: 8, marginBottom: 20 },
  modeBtn: (active) => ({
    flex: 1, padding: "10px 14px", borderRadius: 8, cursor: "pointer",
    border: `1px solid ${active ? "var(--text)" : "var(--border)"}`,
    background: active ? "var(--text)" : "var(--bg2)",
    color: active ? "var(--primary-inv)" : "var(--text3)",
    fontSize: 13, fontWeight: active ? 600 : 400, textAlign: "center",
    transition: "all 0.15s",
  }),
  label: { fontSize: 12, fontWeight: 600, color: "var(--text3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, display: "block" },
  noProfile: {
    padding: "12px 14px", background: "var(--bg2)", border: "1px solid var(--border)",
    borderRadius: 6, fontSize: 13, color: "var(--text3)", marginBottom: 16,
  },
  profileBadge: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)",
    borderRadius: 6, fontSize: 13, color: "var(--text2)", marginBottom: 16,
  },
  figureCard: {
    border: "1px solid var(--border)", borderRadius: 10, marginBottom: 24, overflow: "hidden",
  },
  figureHeader: {
    padding: "12px 16px", background: "var(--bg2)",
    display: "flex", justifyContent: "space-between", alignItems: "center",
    borderBottom: "1px solid var(--border)",
  },
  figureName: { fontSize: 14, fontWeight: 600, color: "var(--text)" },
  figureEra: { fontSize: 12, color: "var(--text3)" },
  scoreBar: { background: "var(--bg3)", borderRadius: 3, height: 3, marginTop: 6 },
  scoreFill: (pct) => ({ width: `${pct}%`, background: "var(--text)", height: "100%", borderRadius: 3 }),
  narrative: {
    padding: "14px 16px", fontSize: 13, lineHeight: 1.9, color: "var(--text2)",
    whiteSpace: "pre-wrap",
  },
  fabricatedLabel: {
    fontSize: 10, fontWeight: 700, letterSpacing: 1.5, textTransform: "uppercase",
    color: "var(--text4)", padding: "8px 16px", borderBottom: "1px solid var(--border)",
    background: "var(--bg3)",
  },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginTop: 12 },
}

export default function Reconstruct() {
  const [mode, setMode] = useState("user") // "user" | "figure"
  const [action, setAction] = useState("")
  const [figureName, setFigureName] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState("")
  const [error, setError] = useState("")
  const [savedProfile, setSavedProfile] = useState(null)

  useEffect(() => {
    try {
      const p = JSON.parse(localStorage.getItem("hps_profile"))
      if (p?.vector?.length === 10) setSavedProfile(p)
    } catch {}
  }, [])

  const handleReconstruct = async () => {
    if (!action.trim()) return
    if (mode === "user" && !savedProfile) return
    if (mode === "figure" && !figureName.trim()) return

    setLoading(true)
    setError("")
    setResult(null)

    let source_vector = null

    if (mode === "user") {
      source_vector = savedProfile.vector
    } else {
      setLoadingStep("Looking up figure profile…")
      try {
        const res = await axios.post(`${API}/analyze/`, { name: figureName.trim() })
        source_vector = res.data.profile.vector
      } catch (err) {
        setError(err.response?.data?.detail || `Could not find profile for "${figureName}". Make sure they are in the database.`)
        setLoading(false)
        return
      }
    }

    setLoadingStep("Reconstructing history…")
    try {
      const res = await axios.post(`${API}/reconstruct/`, {
        action: action.trim(),
        source_vector,
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Reconstruction failed. Please try again.")
    }

    setLoadingStep("")
    setLoading(false)
  }

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Reconstruct — Fabricate History</h2>
      <p style={S.desc}>
        Describe a real action or decision. The system finds ancient figures who share the same
        behavioural DNA and writes a plausible historical account of them taking an equivalent
        action in their own time — adapting for era, geography, gender, and social structure.
      </p>

      <div style={S.modeRow}>
        <div style={S.modeBtn(mode === "user")} onClick={() => setMode("user")}>
          <div style={{ fontWeight: 600, marginBottom: 2 }}>Use my profile</div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>Based on your Match result</div>
        </div>
        <div style={S.modeBtn(mode === "figure")} onClick={() => setMode("figure")}>
          <div style={{ fontWeight: 600, marginBottom: 2 }}>Use a modern figure</div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>Use a documented modern person</div>
        </div>
      </div>

      {mode === "user" && (
        savedProfile ? (
          <div style={S.profileBadge}>
            <span>Using your saved behavioural profile from Match</span>
            <button className="secondary" style={{ fontSize: 11, padding: "3px 9px" }}
              onClick={() => { setSavedProfile(null); localStorage.removeItem("hps_profile") }}>
              Remove
            </button>
          </div>
        ) : (
          <div style={S.noProfile}>
            No saved profile. Go to <strong>Match</strong> first, then return here.
          </div>
        )
      )}

      {mode === "figure" && (
        <div style={{ marginBottom: 16 }}>
          <span style={S.label}>Modern figure name</span>
          <input
            value={figureName}
            onChange={e => setFigureName(e.target.value)}
            placeholder="e.g. Nelson Mandela, Steve Jobs, Marie Curie"
            style={{ marginBottom: 0 }}
          />
          <div style={{ fontSize: 11, color: "var(--text4)", marginTop: 6 }}>
            Must exist in the database (or will be fetched from Wikipedia)
          </div>
        </div>
      )}

      <span style={S.label}>Action / decision to reconstruct</span>
      <textarea
        value={action}
        onChange={e => setAction(e.target.value)}
        placeholder={
          mode === "user"
            ? "Describe something you actually did or decided — e.g. 'I left a stable career to start something from scratch, accepting poverty for the chance at meaning.'"
            : "Describe what this modern figure did — e.g. 'They chose imprisonment over renouncing their beliefs, knowing it would cost them decades of freedom.'"
        }
        style={{ width: "100%", height: 120, marginBottom: 12 }}
        disabled={mode === "user" && !savedProfile}
      />

      <button
        className="primary"
        onClick={handleReconstruct}
        disabled={loading || (mode === "user" && !savedProfile)}
      >
        {loading ? (loadingStep || "Reconstructing…") : "Fabricate History"}
      </button>

      {error && <div style={S.err}>{error}</div>}

      {loading && !result && (
        <div style={{ marginTop: 32 }}>
          {[1, 2, 3].map(i => (
            <div key={i} style={{ ...S.figureCard, marginBottom: 20 }}>
              <div style={S.figureHeader}>
                <div className="skeleton" style={{ height: 14, width: "30%", borderRadius: 4 }} />
                <div className="skeleton" style={{ height: 12, width: "10%", borderRadius: 4 }} />
              </div>
              <div style={{ padding: "12px 16px" }}>
                {[100, 85, 70, 90, 60].map((w, j) => (
                  <div key={j} className="skeleton" style={{ height: 12, width: `${w}%`, borderRadius: 4, marginBottom: 8 }} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 40 }}>
          <div style={{ fontSize: 13, color: "var(--text3)", marginBottom: 20 }}>
            Action: <em>"{result.action}"</em>
          </div>
          {(result.figures || []).map((fig, i) => (
            <div key={i} className={`fade-up fade-up-delay-${i + 1}`} style={S.figureCard}>
              <div style={S.figureHeader}>
                <div>
                  <span style={S.figureName}>{fig.name}</span>
                  {fig.period && (
                    <span style={{ fontSize: 11, color: "var(--text4)", marginLeft: 8 }}>{fig.period}</span>
                  )}
                </div>
                <span style={S.figureEra}>
                  {fig.era < 0 ? `${Math.abs(fig.era)} BC` : `${fig.era} AD`}
                </span>
              </div>
              <div style={{ padding: "8px 16px 4px" }}>
                <div style={S.scoreBar}><div style={S.scoreFill(fig.score * 100)} /></div>
                <div style={{ fontSize: 11, color: "var(--text4)", marginTop: 4 }}>
                  {(fig.score * 100).toFixed(1)}% behavioural similarity
                </div>
              </div>
              <div style={S.fabricatedLabel}>Fabricated History</div>
              <div style={S.narrative}>{fig.narrative}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
