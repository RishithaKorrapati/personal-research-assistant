import { useState } from "react";
import UploadZone from "./components/UploadZone";
import SummaryMap from "./components/SummaryMap";
import ChatPanel from "./components/ChatPanel";
import "./App.css";

export default function App() {
  const [docId, setDocId] = useState(null);
  const [docTitle, setDocTitle] = useState("");
  const [summaryMap, setSummaryMap] = useState(null);
  const [qaHistory, setQaHistory] = useState([]);

  const handleUpload = (data) => {
    setDocId(data.doc_id);
    setDocTitle(data.title);
    setSummaryMap(data.sections);
    setQaHistory([]);
  };

  const handleNewDoc = () => {
    setDocId(null);
    setDocTitle("");
    setSummaryMap(null);
    setQaHistory([]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <span className="logo">Research assistant</span>
        {docId && (
          <button type="button" className="btn btn-ghost" onClick={handleNewDoc}>
            Upload another PDF
          </button>
        )}
      </header>

      <main className="app-main">
        {!docId ? (
          <UploadZone onUpload={handleUpload} />
        ) : (
          <div className="workspace">
            <SummaryMap sections={summaryMap} title={docTitle} />
            <ChatPanel
              docId={docId}
              docTitle={docTitle}
              qaHistory={qaHistory}
              setQaHistory={setQaHistory}
            />
          </div>
        )}
      </main>
    </div>
  );
}
