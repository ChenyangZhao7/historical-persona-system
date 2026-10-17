import { useState, useEffect } from "react"
import axios from "axios"
import { API } from "../App"

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  noProfile: {
    padding: "14px 16px", background: "var(--bg2)", border: "1px solid var(--border)",
    borderRadius: 8, fontSize: 13, color: "var(--text3)", marginBottom: 20,
  },
  profileBadge: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)",
    borderRadius: 6, fontSize: 13, color: "var(--text2)", marginBottom: 16,
  },
  tag: (type) => ({
    display: "inline-block", fontSize: 10, fontWeight: 700,
    letterSpacing: 1, textTransform: "uppercase",
    padding: "2px 7px", borderRadius: 3,
    background: type === "ancient" ? "var(--bg3)" : "var(--text)",
    color: type === "ancient" ? "var(--text3)" : "var(--primary-inv)",
    marginLeft: 8,
  }),
  figureCard: {
    border: "1px solid var(--border)", borderRadius: 10, marginBottom: 20,
    overflow: "hidden",
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
  response: {
    padding: "14px 16px", fontSize: 13, lineHeight: 1.85, color: "var(--text2)",
    whiteSpace: "pre-wrap", borderLeft: "2px solid var(--border)",
    margin: "0 16px 16px", marginTop: 12,
  },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginTop: 16 },
  sectionLabel: { fontSize: 11, fontWeight: 700, color: "var(--text4)", letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 12, marginTop: 28 },
}

export default function Predict() {
  const [question, setQuestion] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [savedProfile, setSavedProfile] = useState(null)

  useEffect(() => {
    try {
      const p = JSON.parse(localStorage.getItem("hps_profile"))
      if (p?.vector?.length === 10) setSavedProfile(p)
    } catch {}
  }, [])

  const handlePredict = async () => {
    if (!question.trim() || !savedProfile) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await axios.post(`${API}/predict/`, {
        question: question.trim(),
        user_vector: savedProfile.vector,
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Request failed. Make sure the backend is running.")
    }
    setLoading(false)
  }

  const ancient = result?.figures?.filter(f => f.type === "ancient") || []
  const modern  = result?.figures?.filter(f => f.type === "modern")  || []

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Predict — Ask History</h2>
      <p style={S.desc}>
        Based on your behavioural profile, the system finds the most similar ancient and modern figures.
        Each one answers your question from their own lived experience.
      </p>

      {!savedProfile ? (
        <div style={S.noProfile}>
          No saved profile found. Go to <strong>Match</strong> first to build your behavioural profile — then come back here.
        </div>
      ) : (
        <div style={S.profileBadge}>
          <span>Using your saved profile from Match</span>
          <button className="secondary" style={{ fontSize: 11, padding: "3px 9px" }}
            onClick={() => { setSavedProfile(null); localStorage.removeItem("hps_profile") }}>
            Clear
          </button>
        </div>
      )}

      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, display: "block" }}>
        Your question
      </span>
      <textarea
        value={question}
        onChange={e => setQuestion(e.target.value)}
        placeholder="e.g. I'm facing betrayal from a close ally — what should I do? / Should I abandon stability for a risky but meaningful path?"
        style={{ width: "100%", height: 110, marginBottom: 12 }}
        disabled={!savedProfile}
      />
      <button className="primary" onClick={handlePredict} disabled={loading || !savedProfile}>
        {loading ? "Asking history…" : "Ask History"}
      </button>

      {error && <div style={S.err}>{error}</div>}

      {loading && (
        <div style={{ marginTop: 32 }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} style={{ ...S.figureCard, marginBottom: 16 }}>
              <div style={{ ...S.figureHeader }}>
                <div className="skeleton" style={{ height: 14, width: "35%", borderRadius: 4 }} />
                <div className="skeleton" style={{ height: 12, width: "12%", borderRadius: 4 }} />
              </div>
              <div style={{ padding: "12px 16px" }}>
                <div className="skeleton" style={{ height: 12, width: "100%", borderRadius: 4, marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 12, width: "85%", borderRadius: 4, marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 12, width: "70%", borderRadius: 4 }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 40 }}>
          {ancient.length > 0 && (
            <>
              <div style={S.sectionLabel}>Ancient figures · before 1800</div>
              {ancient.map((fig, i) => (
                <FigureCard key={i} fig={fig} delay={i + 1} />
              ))}
            </>
          )}
          {modern.length > 0 && (
            <>
              <div style={S.sectionLabel}>Modern figures · after 1800</div>
              {modern.map((fig, i) => (
                <FigureCard key={i} fig={fig} delay={ancient.length + i + 1} />
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}

function FigureCard({ fig, delay }) {
  const eraStr = fig.era < 0 ? `${Math.abs(fig.era)} BC` : `${fig.era} AD`
  return (
    <div className={`fade-up fade-up-delay-${Math.min(delay, 5)}`} style={S.figureCard}>
      <div style={S.figureHeader}>
        <div>
          <span style={S.figureName}>{fig.name}</span>
          <span style={S.tag(fig.type)}>{fig.type}</span>
        </div>
        <span style={S.figureEra}>{eraStr}</span>
      </div>
      <div style={{ padding: "10px 16px 4px" }}>
        <div style={S.scoreBar}><div style={S.scoreFill(fig.score * 100)} /></div>
        <div style={{ fontSize: 11, color: "var(--text4)", marginTop: 4 }}>
          {(fig.score * 100).toFixed(1)}% behavioural similarity
        </div>
      </div>
      <div style={S.response}>{fig.response}</div>
    </div>
  )
}
