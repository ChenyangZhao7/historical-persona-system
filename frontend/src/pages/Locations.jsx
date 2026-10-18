import { useState } from "react"
import axios from "axios"
import { API } from "../App"
import { formatEra } from "../services/format"

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  row: { display: "flex", gap: 10, marginBottom: 12 },
  err: { padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginTop: 12 },
  profile: { padding: "12px 16px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, marginBottom: 24 },
  profileName: { fontSize: 15, fontWeight: 600, color: "var(--text)", marginBottom: 4 },
  profileEra: { fontSize: 12, color: "var(--text3)" },
  locCard: { border: "1px solid var(--border)", borderRadius: 8, padding: "12px 16px", marginBottom: 8 },
  locRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start" },
  locName: { fontSize: 14, fontWeight: 600, color: "var(--text)" },
  locType: { fontSize: 11, color: "var(--text4)", background: "var(--bg3)", padding: "2px 8px", borderRadius: 4 },
  locDesc: { fontSize: 13, color: "var(--text2)", marginTop: 6, lineHeight: 1.7 },
  locPeriod: { fontSize: 12, color: "var(--text3)", marginTop: 4 },
}

export default function Locations() {
  const [name, setName] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleFetch = async () => {
    if (!name.trim()) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await axios.post(`${API}/locations/`, { name: name.trim() })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Figure not found. Check the name matches a figure in the database.")
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Historical Locations</h2>
      <p style={S.desc}>Enter a historical figure to see the key locations of their life — where they were born, where they acted, and where their influence spread.</p>

      <div style={S.row}>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleFetch()}
          placeholder="e.g. Alexander the Great, Genghis Khan, Joan of Arc"
          style={{ flex: 1 }}
        />
        <button className="primary" onClick={handleFetch} disabled={loading}>
          {loading ? "Loading…" : "Get Locations"}
        </button>
      </div>

      {error && <div style={S.err}>{error}</div>}

      {result && (
        <div style={{ marginTop: 32 }}>
          <div style={S.profile}>
            <div style={S.profileName}>{result.name || result.figure}</div>
            {result.era !== undefined && (
              <div style={S.profileEra}>
                {formatEra(result.era)}
              </div>
            )}
          </div>

          <h2 style={{ marginBottom: 16 }}>Key Locations</h2>
          {(result.locations || []).map((loc, i) => (
            <div key={i} style={S.locCard}>
              <div style={S.locRow}>
                <span style={S.locName}>{loc.name || loc.location}</span>
                {loc.type && <span style={S.locType}>{loc.type}</span>}
              </div>
              {loc.description && <div style={S.locDesc}>{loc.description}</div>}
              {loc.period && <div style={S.locPeriod}>{loc.period}</div>}
              {loc.significance && <div style={S.locDesc}>{loc.significance}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
