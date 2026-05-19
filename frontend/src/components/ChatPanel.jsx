import { useState } from "react";
import { queryDoc } from "../api/client";
import CitationCard from "./CitationCard";
import ExportButton from "./ExportButton";

function formatAxiosError(err) {
  const d = err.response?.data;
  if (!d) return err.message || "Request failed";
  if (typeof d.detail === "string") return d.detail;
  if (Array.isArray(d.detail)) {
    return d.detail.map((x) => x.msg || x).join("; ");
  }
  return "Query failed";
}

export default function ChatPanel({
  docId,
  docTitle,
  qaHistory,
  setQaHistory,
}) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || !docId) return;
    setError(null);
    setBusy(true);
    try {
      const { data } = await queryDoc(docId, q);
      setQaHistory((prev) => [
        ...prev,
        {
          question: q,
          answer: data.answer,
          citations: data.citations,
        },
      ]);
      setQuestion("");
    } catch (err) {
      setError(formatAxiosError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="chat-panel card">
      <header className="chat-header">
        <div>
          <h2>Ask the document</h2>
          <p className="muted">{docTitle}</p>
        </div>
        <ExportButton
          docId={docId}
          docTitle={docTitle}
          qaHistory={qaHistory}
          disabled={busy}
        />
      </header>

      <div className="chat-messages">
        {qaHistory.length === 0 && (
          <p className="muted chat-empty">Ask a question to start the conversation.</p>
        )}
        {qaHistory.map((item, i) => (
          <div key={i} className="qa-block">
            <div className="qa-q">
              <span className="qa-label">Q{i + 1}</span>
              <p>{item.question}</p>
            </div>
            <div className="qa-a">
              <span className="qa-label">Answer</span>
              <p className="answer-body">{item.answer}</p>
            </div>
            {item.citations?.length > 0 && (
              <div className="citations-list">
                <span className="qa-label">Sources</span>
                <div className="citation-cards">
                  {item.citations.map((c, j) => (
                    <CitationCard key={`${c.page}-${j}`} citation={c} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {error && <p className="error-banner">{error}</p>}

      <form className="chat-form" onSubmit={submit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask a question about this PDF…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={busy}
        />
        <button type="submit" className="btn btn-primary" disabled={busy || !question.trim()}>
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>
    </section>
  );
}
