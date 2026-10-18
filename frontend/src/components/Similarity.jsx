import { useState } from "react"
import { dimensionLabel } from "../services/dimensions"

// How similar a figure is to what you described, reported two ways:
//
//   * `closeness`   — the confidence-weighted average of 1 - |difference| over
//                     the ten dimensions: the absolute agreement between the
//                     two profiles. This is the number the interface shows.
//   * `dimensions`  — the same thing per dimension, so you can see which
//                     specific traits you share with whom, and which
//                     dimensions a figure's profile simply does not cover.
//
// There is deliberately no rank or percentile. "Top 3% of 447 figures" is a
// property of the corpus, not of the pair: import another thousand figures and
// the same two profiles would print a different number. Raw cosine is not
// shown either — over uncentred 0..1 vectors it sits near 0.95 for almost
// every pair, which is what made the old "95% similar" meaningless.

const clamp = (pct) => Math.max(0, Math.min(100, pct))

const S = {
  bar: { background: "var(--bg3)", borderRadius: 3, height: 5, marginTop: 8 },
  fill: (pct) => ({ width: `${clamp(pct)}%`, background: "var(--primary)", height: "100%", borderRadius: 3 }),
  line: { fontSize: 12, color: "var(--text3)", marginTop: 6, lineHeight: 1.6 },
  closeness: { fontWeight: 600, color: "var(--text2)" },
  unknown: { color: "var(--text4)", fontStyle: "italic" },
  toggle: {
    marginTop: 10, padding: 0, background: "none", border: "none", cursor: "pointer",
    fontSize: 11, color: "var(--text3)", textDecoration: "underline",
  },
  table: { marginTop: 10, borderTop: "1px solid var(--border)", paddingTop: 8 },
  grid: { display: "grid", gridTemplateColumns: "92px 44px 44px 1fr 40px", gap: 8, alignItems: "center" },
  head: { fontSize: 10, color: "var(--text4)", textTransform: "uppercase", letterSpacing: 0.6, marginBottom: 4 },
  row: { padding: "3px 0", fontSize: 12 },
  dimName: { color: "var(--text2)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  num: { color: "var(--text3)", textAlign: "right", fontVariantNumeric: "tabular-nums" },
  numMuted: { color: "var(--text4)", textAlign: "right", fontVariantNumeric: "tabular-nums" },
  track: { background: "var(--bg3)", borderRadius: 3, height: 6, overflow: "hidden" },
  pct: { color: "var(--text3)", textAlign: "right", fontVariantNumeric: "tabular-nums" },
  flag: { color: "#d97706", fontSize: 10, marginLeft: 3 },
}

function fin(value) {
  return typeof value === "number" && Number.isFinite(value)
}

// A figure's own confidence in a dimension. 0 means "no evidence at all", so
// the value must not be read as a real 0.0.
function isKnown(dim) {
  return dim.figure_confidence === null || dim.figure_confidence === undefined
    ? true
    : dim.figure_confidence > 0
}

export function closenessColor(closeness) {
  if (closeness >= 0.8) return "var(--primary)"
  if (closeness >= 0.6) return "#d97706"
  return "#dc2626"
}

export function DimensionCompare({ dimensions, aLabel = "You", bLabel = "Them" }) {
  if (!dimensions?.length) return null
  return (
    <div style={S.table}>
      <div style={{ ...S.grid, ...S.head }}>
        <span>Dimension</span>
        <span style={S.num}>{aLabel}</span>
        <span style={S.num}>{bLabel}</span>
        <span>Agreement</span>
        <span style={S.pct}>Match</span>
      </div>
      {dimensions.map((dim) => {
        const known = isKnown(dim)
        const conf = dim.figure_confidence
        // Only "no evidence" is flagged. Almost every documented dimension in
        // the corpus carries a confidence between 0.3 and 0.8, so flagging
        // anything below 0.5 put a question mark on every single row.
        const confTitle = conf === null || conf === undefined
          ? "No confidence data"
          : `Profile confidence ${conf}`
        return (
          <div key={dim.dimension} style={{ ...S.grid, ...S.row }}>
            <span style={S.dimName} title={dim.dimension}>{dimensionLabel(dim.dimension)}</span>
            <span style={S.num}>{dim.query.toFixed(2)}</span>
            <span style={known ? S.num : S.numMuted} title={confTitle}>
              {dim.figure.toFixed(2)}
              {!known && <span style={S.flag} title="No evidence for this dimension — left out of the score">?</span>}
            </span>
            <div style={S.track}>
              {known && <div style={{ ...S.fill(dim.closeness * 100), background: closenessColor(dim.closeness) }} />}
            </div>
            <span style={S.pct}>{known ? `${Math.round(dim.closeness * 100)}%` : "n/a"}</span>
          </div>
        )
      })}
    </div>
  )
}

export function MatchScore({
  match,
  aLabel = "You",
  bLabel = "Them",
  subject = "your profile",
  defaultOpen = false,
}) {
  const [open, setOpen] = useState(defaultOpen)
  const { closeness, known_dimensions: known, dimensions: dims } = match

  return (
    <>
      {fin(closeness) && (
        <>
          <div style={S.bar}>
            <div style={S.fill(closeness * 100)} />
          </div>
          <div style={S.line}>
            <span style={S.closeness}>{Math.round(closeness * 100)}% similarity to {subject}</span>
            {fin(known) && (
              <> · <span style={S.unknown}>based on {known} of 10 dimensions</span></>
            )}
          </div>
        </>
      )}

      {dims?.length > 0 && (
        <>
          <button style={S.toggle} onClick={() => setOpen((o) => !o)}>
            {open ? "Hide" : "Show"} 10-dimension comparison
          </button>
          {open && <DimensionCompare dimensions={dims} aLabel={aLabel} bLabel={bLabel} />}
        </>
      )}
    </>
  )
}
