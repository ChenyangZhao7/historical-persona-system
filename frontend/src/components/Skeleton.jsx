export function SkeletonCard() {
  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: "12px 16px", marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
        <div className="skeleton" style={{ height: 14, width: "40%", borderRadius: 4 }} />
        <div className="skeleton" style={{ height: 12, width: "15%", borderRadius: 4 }} />
      </div>
      <div className="skeleton" style={{ height: 5, width: "100%", borderRadius: 3 }} />
      <div className="skeleton" style={{ height: 10, width: "25%", borderRadius: 4, marginTop: 6 }} />
    </div>
  )
}

export function SkeletonList({ count = 5 }) {
  return (
    <div>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}

export function SkeletonText({ lines = 3 }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ height: 13, width: i === lines - 1 ? "60%" : "100%", borderRadius: 4 }}
        />
      ))}
    </div>
  )
}
