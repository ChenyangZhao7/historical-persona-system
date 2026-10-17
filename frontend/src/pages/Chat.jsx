import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { API } from "../App"

const S = {
  desc: { fontSize: 13, color: "var(--text3)", marginBottom: 20, lineHeight: 1.7 },
  thread: { minHeight: 280, border: "1px solid var(--border)", borderRadius: 8, padding: 16, marginBottom: 12, background: "var(--bg2)", overflowY: "auto", maxHeight: 480 },
  empty: { color: "#ccc", textAlign: "center", marginTop: 80, fontSize: 13 },
  bubble: (role) => ({
    display: "inline-block",
    maxWidth: "78%",
    padding: "10px 14px",
    borderRadius: 8,
    background: role === "user" ? "var(--primary)" : "var(--bg2)",
    color: role === "user" ? "var(--primary-inv)" : "var(--text)",
    border: role === "figure" ? "1px solid var(--border)" : "none",
    fontSize: 14,
    lineHeight: 1.6,
    textAlign: "left",
  }),
  msgWrap: (role) => ({ marginBottom: 14, textAlign: role === "user" ? "right" : "left" }),
  figureName: { fontSize: 11, color: "var(--text3)", marginBottom: 4 },
  row: { display: "flex", gap: 10 },
}

export default function Chat() {
  const [name, setName] = useState("")
  const [message, setMessage] = useState("")
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [history])

  const handleSend = async () => {
    if (!name.trim() || !message.trim()) return
    setLoading(true)
    setError("")
    const userMessage = message
    setMessage("")
    setHistory(h => [...h, { role: "user", text: userMessage }])
    try {
      const res = await axios.post(`${API}/chat/`, { name, message: userMessage })
      setHistory(h => [...h, { role: "figure", text: res.data.response, figure: res.data.figure }])
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to get response.")
      setHistory(h => h.slice(0, -1))
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 style={{ marginBottom: 6 }}>Persona Chat</h2>
      <p style={S.desc}>Enter a historical figure's name and ask them anything. They will respond as themselves — shaped by their actual behavioural profile.</p>

      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, display: "block" }}>Figure</span>
      <input
        value={name}
        onChange={e => { setName(e.target.value); setHistory([]) }}
        placeholder="e.g. Napoleon Bonaparte, Cleopatra, Confucius"
        style={{ width: "100%", marginBottom: 16 }}
      />

      <div style={S.thread}>
        {history.length === 0 && <p style={S.empty}>Your conversation will appear here</p>}
        {history.map((msg, i) => (
          <div key={i} style={S.msgWrap(msg.role)}>
            <div style={S.bubble(msg.role)}>
              {msg.role === "figure" && <div style={S.figureName}>{msg.figure}</div>}
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div style={S.msgWrap("figure")}>
            <div style={S.bubble("figure")}>
              <div style={S.figureName}>{name}</div>
              <span style={{ color: "var(--text4)" }}>…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div style={{ padding: "10px 14px", background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13, color: "#dc2626", marginBottom: 12 }}>
          {error}
        </div>
      )}

      <div style={S.row}>
        <input
          value={message}
          onChange={e => setMessage(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSend()}
          placeholder="Ask a question…"
          style={{ flex: 1 }}
          disabled={!name.trim()}
        />
        <button className="primary" onClick={handleSend} disabled={loading || !name.trim() || !message.trim()}>
          {loading ? "…" : "Send"}
        </button>
      </div>
    </div>
  )
}
