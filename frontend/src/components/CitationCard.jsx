export default function CitationCard({ citation }) {
  const { page, text, preview: serverPreview, confidence } = citation;

  const barColor =
    confidence >= 80 ? "#22c55e" : confidence >= 50 ? "#f59e0b" : "#ef4444";

  const base = (serverPreview && serverPreview.trim()) || text || "—";
  const preview =
    base.length > 220 ? `${base.slice(0, 220).trim()}…` : base;

  return (
    <div className="citation-card">
      <div className="citation-header">
        <span className="page-label">Page {page}</span>
        <span className="confidence-label">{confidence}%</span>
      </div>
      <div className="confidence-bar-track">
        <div
          className="confidence-bar-fill"
          style={{ width: `${Math.min(100, Math.max(0, confidence))}%`, background: barColor }}
        />
      </div>
      <p className="citation-text">&ldquo;{preview}&rdquo;</p>
    </div>
  );
}
