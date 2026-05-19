import axios from "axios";

const BASE =
  import.meta.env.VITE_API_BASE?.replace(/\/$/, "") ||
  "http://localhost:8000/api";

export const uploadPDF = (file) => {
  const form = new FormData();
  form.append("file", file);
  return axios.post(`${BASE}/upload`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const queryDoc = (doc_id, question) =>
  axios.post(`${BASE}/query`, { doc_id, question });

export const exportReport = (payload) =>
  axios.post(`${BASE}/export`, payload, { responseType: "blob" });
