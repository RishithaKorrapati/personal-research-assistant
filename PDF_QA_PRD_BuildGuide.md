# PDF Research Q&A App — Product Requirements Document & Cursor Build Guide

---

## 1. Project Overview

A web application that allows users to upload research PDF documents and ask natural language questions. The app returns answers with exact page number citations, a confidence score per citation, an auto-generated document summary map on upload, and an export feature that produces a formatted Word/PDF report of the full Q&A session.

### Goals
- Demonstrate RAG (Retrieval-Augmented Generation) pipeline implementation
- Showcase prompt engineering, vector search, and citation accuracy
- Portfolio-quality project: clean UI, three differentiating features not found in existing tools

### Tech Stack

| Layer | Tool | Cost |
|---|---|---|
| PDF parsing | `pdfplumber` | Free |
| Chunking | `LangChain RecursiveCharacterTextSplitter` | Free |
| Vector store | `ChromaDB` (local) | Free |
| Embeddings | OpenAI `text-embedding-3-small` | ~$0.001 per doc |
| Summary map | OpenAI `gpt-4o-mini` | ~$0.01 per doc |
| Q&A answers | OpenAI `gpt-4o` | ~$0.01 per question |
| Export (Word) | `python-docx` | Free |
| Export (PDF) | `fpdf2` | Free |
| Backend | `FastAPI` | Free |
| Frontend | `React + Vite` | Free |

---

## 2. Project Structure

```
pdf-qa-app/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/
│   │   ├── upload.py            # PDF upload + processing endpoint
│   │   ├── query.py             # Q&A endpoint
│   │   └── export.py            # Report export endpoint
│   ├── services/
│   │   ├── pdf_parser.py        # pdfplumber extraction
│   │   ├── chunker.py           # LangChain chunking logic
│   │   ├── embedder.py          # OpenAI embeddings + ChromaDB
│   │   ├── retriever.py         # Vector search + confidence scores
│   │   ├── llm.py               # GPT-4o Q&A + GPT-4o-mini summary
│   │   └── exporter.py          # Word + PDF report builder
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── storage/
│   │   └── chroma_store/        # ChromaDB persisted locally here
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── UploadZone.jsx   # PDF drag-and-drop upload
│   │   │   ├── SummaryMap.jsx   # Feature 1: document map
│   │   │   ├── ChatPanel.jsx    # Q&A conversation UI
│   │   │   ├── CitationCard.jsx # Answer + confidence bars
│   │   │   └── ExportButton.jsx # Feature 3: download report
│   │   ├── api/
│   │   │   └── client.js        # Axios calls to FastAPI
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .env                         # API keys (never commit)
├── .env.example
└── README.md
```

---

## 3. Environment Setup

### 3.1 .env file
```
OPENAI_API_KEY=sk-...
CHROMA_PERSIST_DIR=./backend/storage/chroma_store
MAX_CHUNK_SIZE=300
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
```

### 3.2 Backend dependencies — backend/requirements.txt
```
fastapi
uvicorn[standard]
python-multipart
pdfplumber
langchain
langchain-text-splitters
chromadb
openai
python-docx
fpdf2
python-dotenv
pydantic
```

### 3.3 Frontend dependencies
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install axios react-dropzone
```

---

## 4. Backend — Full Implementation

### 4.1 main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, query, export
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PDF Q&A API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(export.router, prefix="/api")
```

---

### 4.2 models/schemas.py
```python
from pydantic import BaseModel
from typing import List, Optional

class ChunkMetadata(BaseModel):
    page: int
    chunk_id: int
    source: str

class CitedChunk(BaseModel):
    page: int
    text: str
    confidence: int          # 0–100, derived from cosine similarity

class QueryRequest(BaseModel):
    doc_id: str
    question: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[CitedChunk]

class SummarySection(BaseModel):
    theme: str
    summary: str
    key_terms: List[str]
    pages: str

class SummaryMapResponse(BaseModel):
    doc_id: str
    title: str
    sections: List[SummarySection]

class QAPair(BaseModel):
    question: str
    answer: str
    citations: List[CitedChunk]

class ExportRequest(BaseModel):
    doc_id: str
    doc_title: str
    qa_pairs: List[QAPair]
    format: str              # "docx" or "pdf"
```

---

### 4.3 services/pdf_parser.py
```python
import pdfplumber
from typing import List, Dict

def extract_pages(pdf_path: str) -> List[Dict]:
    """
    Extract text from each page of a PDF.
    Returns list of { page_num, text } dicts.
    Skips pages with no extractable text (e.g. image-only pages).
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "page_num": page_num,
                    "text": text.strip()
                })
    return pages
```

---

### 4.4 services/chunker.py
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict
import os

CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", 300))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]  # priority order
)

def chunk_pages(pages: List[Dict], source: str) -> List[Dict]:
    """
    Split each page's text into overlapping chunks.
    Preserves page number as metadata on every chunk.
    Returns list of { text, metadata: { page, chunk_id, source } }
    """
    all_chunks = []
    chunk_id = 0

    for page in pages:
        page_num = page["page_num"]
        page_text = page["text"]
        chunks = splitter.split_text(page_text)

        for chunk_text in chunks:
            all_chunks.append({
                "text": chunk_text,
                "metadata": {
                    "page": page_num,
                    "chunk_id": chunk_id,
                    "source": source
                }
            })
            chunk_id += 1

    return all_chunks
```

---

### 4.5 services/embedder.py
```python
import chromadb
import openai
import os
from typing import List, Dict

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./storage/chroma_store")
client = chromadb.PersistentClient(path=PERSIST_DIR)
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_collection(doc_id: str):
    return client.get_or_create_collection(
        name=doc_id,
        metadata={"hnsw:space": "cosine"}  # cosine similarity
    )

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Call OpenAI text-embedding-3-small for a batch of texts."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]

def store_chunks(doc_id: str, chunks: List[Dict]) -> None:
    """
    Embed all chunks and store in ChromaDB with metadata.
    Processes in batches of 100 to avoid API limits.
    """
    collection = get_collection(doc_id)
    batch_size = 100

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        ids = [f"{doc_id}_chunk_{c['metadata']['chunk_id']}" for c in batch]
        embeddings = embed_texts(texts)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
```

---

### 4.6 services/retriever.py
```python
import openai
import os
from typing import List, Dict
from .embedder import get_collection, embed_texts

TOP_K = int(os.getenv("TOP_K_RESULTS", 5))

def retrieve_chunks(doc_id: str, question: str) -> List[Dict]:
    """
    Embed the question, search ChromaDB for top-k similar chunks.
    Returns list of { text, page, confidence } sorted by confidence desc.

    Confidence formula:
    ChromaDB cosine distance is 0 (identical) to 2 (opposite).
    Convert: confidence = round((1 - distance / 2) * 100)
    """
    collection = get_collection(doc_id)
    question_embedding = embed_texts([question])[0]

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        confidence = round((1 - distance / 2) * 100)
        chunks.append({
            "text": text,
            "page": metadata["page"],
            "confidence": confidence
        })

    # Sort highest confidence first
    return sorted(chunks, key=lambda x: x["confidence"], reverse=True)
```

---

### 4.7 services/llm.py
```python
import openai
import json
import os
from typing import List, Dict

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def answer_question(question: str, chunks: List[Dict]) -> str:
    """
    Send retrieved chunks + question to GPT-4o.
    Instructs the model to cite page numbers inline.
    """
    context = ""
    for chunk in chunks:
        context += f"[Page {chunk['page']}]\n{chunk['text']}\n\n"

    prompt = f"""You are a research assistant answering questions about a document.
Answer ONLY using the context provided below. Do not use any outside knowledge.
Always cite page numbers inline like (Page 5) immediately after the relevant information.
If the context does not contain enough information to answer, say so clearly.

Context:
{context}

Question: {question}

Answer:"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # low temperature for factual accuracy
        max_tokens=600
    )
    return response.choices[0].message.content


def generate_summary_map(pages: List[Dict]) -> List[Dict]:
    """
    Use GPT-4o-mini to generate a structured summary map of the document.
    Groups pages into sections of ~5 pages each.
    Returns list of section summaries with theme, summary, key_terms, pages.
    """
    sections = []
    group_size = 5  # pages per section

    for i in range(0, len(pages), group_size):
        group = pages[i:i + group_size]
        start_page = group[0]["page_num"]
        end_page = group[-1]["page_num"]
        combined_text = "\n".join([p["text"] for p in group])[:3000]  # cap tokens

        prompt = f"""Analyze this section of a research document (pages {start_page}–{end_page}).
Return ONLY valid JSON, no markdown, no explanation:
{{
  "theme": "main topic in 3-5 words",
  "summary": "one clear sentence summarising the key point",
  "key_terms": ["term1", "term2", "term3"],
  "pages": "{start_page}-{end_page}"
}}

Document section:
{combined_text}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )

        raw = response.choices[0].message.content.strip()
        try:
            section = json.loads(raw)
            sections.append(section)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            sections.append({
                "theme": f"Pages {start_page}–{end_page}",
                "summary": "Could not generate summary for this section.",
                "key_terms": [],
                "pages": f"{start_page}-{end_page}"
            })

    return sections
```

---

### 4.8 services/exporter.py
```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from typing import List, Dict
import os

def export_docx(doc_title: str, qa_pairs: List[Dict], output_path: str) -> str:
    """
    Build a Word document with:
    - Cover heading (document title)
    - Each Q&A pair as a numbered section
    - Citations formatted as footnote-style captions
    - Confidence score noted per citation
    """
    doc = Document()

    # Title
    title = doc.add_heading(f"Research Q&A Report", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph(f"Source document: {doc_title}")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")  # spacer

    for i, qa in enumerate(qa_pairs, start=1):
        # Question heading
        doc.add_heading(f"Q{i}: {qa['question']}", level=2)

        # Answer body
        answer_para = doc.add_paragraph(qa["answer"])
        answer_para.style.font.size = Pt(11)

        # Citations as styled caption paragraphs
        if qa.get("citations"):
            doc.add_paragraph("Sources used:", style="Caption")
            for citation in qa["citations"]:
                cite_text = (
                    f"  Page {citation['page']}  —  "
                    f"Confidence: {citation['confidence']}%  —  "
                    f"\"{citation['text'][:120]}...\""
                )
                cite_para = doc.add_paragraph(cite_text, style="Caption")

        doc.add_paragraph("")  # spacer between Q&A pairs

    doc.save(output_path)
    return output_path


def export_pdf(doc_title: str, qa_pairs: List[Dict], output_path: str) -> str:
    """
    Build a clean PDF with FPDF2.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Research Q&A Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Source: {doc_title}", ln=True, align="C")
    pdf.ln(8)

    for i, qa in enumerate(qa_pairs, start=1):
        # Question
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, f"Q{i}: {qa['question']}")
        pdf.ln(2)

        # Answer
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 7, qa["answer"])
        pdf.ln(3)

        # Citations
        if qa.get("citations"):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            for citation in qa["citations"]:
                cite_text = (
                    f"Page {citation['page']}  |  "
                    f"Confidence: {citation['confidence']}%  |  "
                    f"\"{citation['text'][:100]}...\""
                )
                pdf.multi_cell(0, 6, cite_text)
            pdf.set_text_color(0, 0, 0)

        pdf.ln(5)

    pdf.output(output_path)
    return output_path
```

---

### 4.9 routers/upload.py
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_parser import extract_pages
from services.chunker import chunk_pages
from services.embedder import store_chunks
from services.llm import generate_summary_map
from models.schemas import SummaryMapResponse
import uuid
import os
import shutil

router = APIRouter()
UPLOAD_DIR = "./storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=SummaryMapResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    doc_id = str(uuid.uuid4())
    save_path = f"{UPLOAD_DIR}/{doc_id}.pdf"

    # Save uploaded file
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract pages
    pages = extract_pages(save_path)
    if not pages:
        raise HTTPException(status_code=422, detail="No extractable text found in PDF.")

    # Chunk and embed into ChromaDB
    chunks = chunk_pages(pages, source=file.filename)
    store_chunks(doc_id, chunks)

    # Generate summary map (Feature 1)
    summary_sections = generate_summary_map(pages)

    return SummaryMapResponse(
        doc_id=doc_id,
        title=file.filename.replace(".pdf", ""),
        sections=summary_sections
    )
```

---

### 4.10 routers/query.py
```python
from fastapi import APIRouter, HTTPException
from services.retriever import retrieve_chunks
from services.llm import answer_question
from models.schemas import QueryRequest, QueryResponse, CitedChunk

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Retrieve top-k relevant chunks with confidence scores (Feature 2)
    chunks = retrieve_chunks(request.doc_id, request.question)

    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant content found.")

    # Get GPT-4o answer with page citations
    answer = answer_question(request.question, chunks)

    cited_chunks = [
        CitedChunk(
            page=c["page"],
            text=c["text"],
            confidence=c["confidence"]
        )
        for c in chunks
    ]

    return QueryResponse(answer=answer, citations=cited_chunks)
```

---

### 4.11 routers/export.py
```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from services.exporter import export_docx, export_pdf
from models.schemas import ExportRequest
import os

router = APIRouter()
EXPORT_DIR = "./storage/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

@router.post("/export")
async def export_report(request: ExportRequest):
    output_path = f"{EXPORT_DIR}/{request.doc_id}_report.{request.format}"
    qa_pairs = [qa.dict() for qa in request.qa_pairs]

    if request.format == "docx":
        export_docx(request.doc_title, qa_pairs, output_path)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif request.format == "pdf":
        export_pdf(request.doc_title, qa_pairs, output_path)
        media_type = "application/pdf"
    else:
        raise HTTPException(status_code=400, detail="Format must be 'docx' or 'pdf'.")

    return FileResponse(
        path=output_path,
        media_type=media_type,
        filename=f"report.{request.format}"
    )
```

---

## 5. Frontend — Component Guide

### 5.1 api/client.js
```javascript
import axios from "axios";

const BASE = "http://localhost:8000/api";

export const uploadPDF = (file) => {
  const form = new FormData();
  form.append("file", file);
  return axios.post(`${BASE}/upload`, form);
};

export const queryDoc = (doc_id, question) =>
  axios.post(`${BASE}/query`, { doc_id, question });

export const exportReport = (payload) =>
  axios.post(`${BASE}/export`, payload, { responseType: "blob" });
```

---

### 5.2 App.jsx — State flow
```jsx
import { useState } from "react";
import UploadZone from "./components/UploadZone";
import SummaryMap from "./components/SummaryMap";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const [docId, setDocId] = useState(null);
  const [docTitle, setDocTitle] = useState("");
  const [summaryMap, setSummaryMap] = useState(null);
  const [qaHistory, setQaHistory] = useState([]);

  const handleUpload = (data) => {
    setDocId(data.doc_id);
    setDocTitle(data.title);
    setSummaryMap(data.sections);
  };

  return (
    <div className="app">
      {!docId ? (
        <UploadZone onUpload={handleUpload} />
      ) : (
        <>
          <SummaryMap sections={summaryMap} title={docTitle} />
          <ChatPanel
            docId={docId}
            docTitle={docTitle}
            qaHistory={qaHistory}
            setQaHistory={setQaHistory}
          />
        </>
      )}
    </div>
  );
}
```

---

### 5.3 CitationCard.jsx — Confidence bars (Feature 2)
```jsx
export default function CitationCard({ citation }) {
  const { page, text, confidence } = citation;

  const barColor =
    confidence >= 80 ? "#22c55e"   // green
    : confidence >= 50 ? "#f59e0b"  // amber
    : "#ef4444";                    // red

  return (
    <div className="citation-card">
      <div className="citation-header">
        <span className="page-label">Page {page}</span>
        <span className="confidence-label">{confidence}%</span>
      </div>
      <div className="confidence-bar-track">
        <div
          className="confidence-bar-fill"
          style={{ width: `${confidence}%`, background: barColor }}
        />
      </div>
      <p className="citation-text">"{text.slice(0, 160)}..."</p>
    </div>
  );
}
```

---

### 5.4 ExportButton.jsx — Feature 3
```jsx
import { exportReport } from "../api/client";

export default function ExportButton({ docId, docTitle, qaHistory }) {
  const handleExport = async (format) => {
    const payload = {
      doc_id: docId,
      doc_title: docTitle,
      qa_pairs: qaHistory,
      format,
    };
    const res = await exportReport(payload);
    const url = URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement("a");
    a.href = url;
    a.download = `report.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="export-buttons">
      <button onClick={() => handleExport("docx")}>Export as Word</button>
      <button onClick={() => handleExport("pdf")}>Export as PDF</button>
    </div>
  );
}
```

---

## 6. Running the App

### Start backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Start frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## 7. Feature Summary

### Feature 1 — Auto-generated summary map
- Triggered on every PDF upload automatically
- Groups pages into sections of 5, sends each to `gpt-4o-mini`
- Returns structured JSON: theme, one-line summary, key terms, page range
- Displayed as a visual card grid before the user asks any questions
- Cost: ~$0.01 per document (runs once)

### Feature 2 — Confidence scoring on citations
- Every citation returned from a query includes a confidence % (0–100)
- Derived from ChromaDB cosine similarity distance — no extra API calls
- Displayed as a colour-coded bar: green (≥80%), amber (50–79%), red (<50%)
- Signals to the user how strongly each page supports the answer
- Cost: zero (uses existing vector search result)

### Feature 3 — Export as annotated report
- User can export full Q&A session as `.docx` or `.pdf`
- Each Q&A pair is a numbered section
- Citations appear as caption-style footnotes with page number and confidence %
- Uses `python-docx` (Word) and `fpdf2` (PDF) — no API calls needed
- Cost: zero

---

## 8. Cost Estimate Per Session

| Action | Model | Approx. cost |
|---|---|---|
| Upload + embed 50-page paper | text-embedding-3-small | $0.002 |
| Generate summary map | gpt-4o-mini | $0.010 |
| Answer 10 questions | gpt-4o | $0.100 |
| Export report | No API | $0.000 |
| **Total per session** | | **~$0.11** |

---

## 9. Cursor-Specific Instructions

When building this project in Cursor, follow this order:

1. Create the full folder structure first
2. Set up `.env` and `requirements.txt`
3. Build `pdf_parser.py` → `chunker.py` → `embedder.py` in that order (each depends on the previous)
4. Build `retriever.py` → `llm.py`
5. Build all three routers (`upload`, `query`, `export`)
6. Build `exporter.py`
7. Test backend with `uvicorn` before touching frontend
8. Build frontend components in this order: `UploadZone` → `SummaryMap` → `CitationCard` → `ChatPanel` → `ExportButton`
9. Wire `App.jsx` last

Use `@codebase` in Cursor chat when asking it to connect components — it will have the full project context.

If an endpoint fails, check `OPENAI_API_KEY` is loaded and ChromaDB `persist_dir` exists before debugging further.

---

## 10. Known Edge Cases to Handle

- **Scanned PDFs**: `pdfplumber` returns empty text for image-only pages. Detect and warn the user.
- **Very large PDFs** (200+ pages): Embedding will take 30–60 seconds. Add a loading state on the frontend.
- **Repeated uploads**: Each upload generates a new `doc_id` and ChromaDB collection. Add a cleanup job or size limit if storage is a concern.
- **JSON parse failure in summary map**: Handled with a fallback in `llm.py` — always wrap `json.loads()` in try/except.
- **Citation hallucination**: GPT-4o is prompted with `ONLY use the context provided`. Still — the confidence score gives users a signal to distrust low-confidence citations.
