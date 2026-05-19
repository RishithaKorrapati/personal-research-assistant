export default function SummaryMap({ sections, title }) {
  if (!sections?.length) return null;

  return (
    <section className="summary-map card">
      <header className="summary-map-header">
        <h2>Document map</h2>
        <p className="muted">{title}</p>
      </header>
      <div className="summary-grid">
        {sections.map((s, i) => (
          <article key={`${s.pages}-${i}`} className="summary-card">
            <div className="summary-card-meta">{s.pages}</div>
            <h3 className="summary-theme">{s.theme}</h3>
            <p className="summary-body">{s.summary}</p>
            {s.key_terms?.length > 0 && (
              <ul className="key-terms">
                {s.key_terms.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
