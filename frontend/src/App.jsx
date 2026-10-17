import { useState, useEffect } from "react"
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom"
import Match from "./pages/Match"
import Predict from "./pages/Predict"
import Reconstruct from "./pages/Reconstruct"
import Figures from "./pages/Analyze"
import Chat from "./pages/Chat"
import Graph from "./pages/Graph"
import Locations from "./pages/Locations"
import Reverse from "./pages/Reverse"
import Relics from "./pages/Relics"
import Benchmark from "./pages/Benchmark"
import Cluster from "./pages/Cluster"

export const API = import.meta.env.VITE_API_URL || ""

const NAV_GROUPS = [
  {
    label: null,
    items: [{ path: "/figures", label: "Database" }],
  },
  {
    label: "Find ME",
    items: [
      { path: "/", label: "Match" },
      { path: "/reverse", label: "Reverse" },
    ],
  },
  {
    label: "Fake History",
    items: [
      { path: "/predict", label: "Predict" },
      { path: "/reconstruct", label: "Reconstruct" },
      { path: "/chat", label: "Chat" },
    ],
  },
  {
    label: "Explore",
    items: [
      { path: "/graph", label: "Graph" },
      { path: "/locations", label: "Locations" },
      { path: "/relics", label: "Relics" },
      { path: "/cluster", label: "Map" },
      { path: "/benchmark", label: "Benchmark" },
    ],
  },
]

export default function App() {
  // index.html already resolved the theme before first paint (saved value or the
  // OS preference), so read it back instead of assuming light.
  const [dark, setDark] = useState(
    () => document.documentElement.getAttribute("data-theme") === "dark"
  )

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light")
    localStorage.setItem("hps_theme", dark ? "dark" : "light")
  }, [dark])

  const navLinkStyle = ({ isActive }) => ({
    display: "inline-block",
    padding: "6px 12px",
    fontSize: 13,
    fontWeight: isActive ? 600 : 400,
    color: isActive ? "var(--text)" : "var(--text3)",
    textDecoration: "none",
    borderBottom: isActive ? "2px solid var(--text)" : "2px solid transparent",
    whiteSpace: "nowrap",
    transition: "color 0.15s",
  })

  return (
    <BrowserRouter>
      <div style={{ maxWidth: 780, margin: "0 auto", padding: "0 24px 80px" }}>
        <div style={{ padding: "28px 0 0", borderBottom: "1px solid var(--border)", marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <span style={{ fontSize: 17, fontWeight: 700, color: "var(--text)", letterSpacing: "-0.4px" }}>
                Historical Persona System
              </span>
              <span style={{ fontSize: 12, color: "var(--text4)" }}>Behavioural DNA across civilisations</span>
            </div>
            <button
              onClick={() => setDark(d => !d)}
              style={{
                fontSize: 11, padding: "4px 10px", borderRadius: 20,
                border: "1px solid var(--border)", background: "var(--bg2)",
                color: "var(--text3)", cursor: "pointer", flexShrink: 0,
                marginLeft: 16,
              }}
            >
              {dark ? "☀ Light" : "☾ Dark"}
            </button>
          </div>

          <nav style={{ display: "flex", gap: 0, overflowX: "auto", alignItems: "center" }}>
            {NAV_GROUPS.map((group, gi) => (
              <div key={gi} style={{ display: "flex", alignItems: "center" }}>
                {gi > 0 && (
                  <span style={{ color: "var(--border)", fontSize: 16, padding: "0 4px", userSelect: "none" }}>│</span>
                )}
                {group.label && (
                  <span style={{
                    fontSize: 10, fontWeight: 700, color: "var(--text4)",
                    letterSpacing: 1.5, textTransform: "uppercase",
                    padding: "6px 8px 6px 4px", whiteSpace: "nowrap",
                  }}>
                    {group.label}
                  </span>
                )}
                {group.items.map(n => (
                  <NavLink key={n.path} to={n.path} end={n.path === "/"} style={navLinkStyle}>
                    {n.label}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        </div>

        <Routes>
          <Route path="/" element={<Match />} />
          <Route path="/predict" element={<Predict />} />
          <Route path="/reconstruct" element={<Reconstruct />} />
          <Route path="/figures" element={<Figures />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/graph" element={<Graph />} />
          <Route path="/locations" element={<Locations />} />
          <Route path="/reverse" element={<Reverse />} />
          <Route path="/relics" element={<Relics />} />
          <Route path="/benchmark" element={<Benchmark />} />
          <Route path="/cluster" element={<Cluster />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
