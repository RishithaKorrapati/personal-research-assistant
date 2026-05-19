import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { uploadPDF } from "../api/client";

function formatAxiosError(err) {
  const d = err.response?.data;
  if (!d) return err.message || "Request failed";
  if (typeof d.detail === "string") return d.detail;
  if (Array.isArray(d.detail)) {
    return d.detail.map((x) => x.msg || x).join("; ");
  }
  return "Upload failed";
}

export default function UploadZone({ onUpload }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(
    async (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (!file) return;
      setError(null);
      setBusy(true);
      try {
        const { data } = await uploadPDF(file);
        onUpload(data);
      } catch (e) {
        setError(formatAxiosError(e));
      } finally {
        setBusy(false);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: busy,
  });

  return (
    <div className="upload-screen">
      <div className="upload-hero">
        <h1>PDF research Q&amp;A</h1>
        <p className="muted">
          Upload a research PDF. You will get a summary map, then you can ask
          questions with page-level citations.
        </p>
      </div>
      <div
        {...getRootProps()}
        className={`dropzone card ${isDragActive ? "dropzone-active" : ""} ${busy ? "dropzone-busy" : ""}`}
      >
        <input {...getInputProps()} />
        {busy ? (
          <p className="dropzone-msg">Processing PDF… this can take a minute.</p>
        ) : isDragActive ? (
          <p className="dropzone-msg">Drop the PDF here</p>
        ) : (
          <>
            <p className="dropzone-msg">
              Drag and drop a PDF here, or click to choose a file
            </p>
            <p className="dropzone-hint muted">Text-based PDFs only (not scanned images)</p>
          </>
        )}
      </div>
      {error && <p className="error-banner">{error}</p>}
    </div>
  );
}
