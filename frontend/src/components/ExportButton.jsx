import { exportReport } from "../api/client";

export default function ExportButton({ docId, docTitle, qaHistory, disabled }) {
  const handleExport = async (format) => {
    if (!docId || !qaHistory.length) return;
    const payload = {
      doc_id: docId,
      doc_title: docTitle,
      qa_pairs: qaHistory,
      format,
    };
    try {
      const res = await exportReport(payload);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      const msg =
        e.response?.data instanceof Blob
          ? "Export failed (see server logs)"
          : e.response?.data?.detail || e.message || "Export failed";
      window.alert(typeof msg === "string" ? msg : "Export failed");
    }
  };

  return (
    <div className="export-buttons">
      <button
        type="button"
        className="btn btn-secondary"
        disabled={disabled || !qaHistory.length}
        onClick={() => handleExport("docx")}
      >
        Export Word
      </button>
      <button
        type="button"
        className="btn btn-secondary"
        disabled={disabled || !qaHistory.length}
        onClick={() => handleExport("pdf")}
      >
        Export PDF
      </button>
    </div>
  );
}
