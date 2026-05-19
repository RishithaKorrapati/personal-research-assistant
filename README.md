# Personal Research Assistant

A full-stack **PDF research Q&A** app: upload a paper, get an auto-generated **document map**, ask questions with **page-level citations** and **confidence scores**, and export the session as Word or PDF.

Built as a portfolio RAG (retrieval-augmented generation) project with a FastAPI backend and React frontend.

![Stack](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?logo=openai&logoColor=white)

## Features

| Feature | Description |
|--------|-------------|
| **PDF upload & indexing** | Extract text with `pdfplumber`, chunk with LangChain `RecursiveCharacterTextSplitter`, embed with OpenAI `text-embedding-3-small`, store in local **ChromaDB**. |
| **Document map** | On upload, `gpt-4o-mini` summarizes the paper in ~5-page sections (theme, one-line summary, key terms). |
| **Grounded Q&A** | `gpt-4o` answers using **only retrieved chunks** (not the full PDF), with inline page citations. |
| **Confidence scores** | Each source shows a 0–100% score from Chroma cosine similarity (no extra API call). |
| **Readable source cards** | Short `preview` labels (heuristic + optional `gpt-4o-mini`) instead of raw PDF fragments in the UI. |
| **Export** | Download the full Q&A session as `.docx` or `.pdf`. |

## Architecture

```text
PDF upload → extract pages → chunk → embed → ChromaDB
                ↓
         summary map (gpt-4o-mini)

User question → embed query → top-k retrieval → gpt-4o answer + citations
```

**Important:** Each answer is generated from **retrieved chunks only** (default `TOP_K_RESULTS=8`), not the entire document.

## Project structure

```text
personal-research-assistant/
├── backend/
│   ├── main.py                 # FastAPI app + CORS
│   ├── routers/                # upload, query, export
│   ├── services/               # pdf, chunk, embed, retrieve, llm, export, citations
│   ├── models/schemas.py
│   ├── storage/                # chroma, uploads, exports (gitignored data)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   └── components/         # UploadZone, SummaryMap, ChatPanel, …
│   └── package.json
├── PDF_QA_PRD_BuildGuide.md    # Original build spec
└── README.md
```

## Prerequisites

- **Python 3.12+** (recommended; use a project venv)
- **Node.js 20+** (22.12+ if you upgrade to Vite 8 later; repo pins Vite 5 for broader compatibility)
- **OpenAI API key** with access to `gpt-4o`, `gpt-4o-mini`, and `text-embedding-3-small`

## Setup

### 1. Clone and create a Python virtual environment

```bash
git clone https://github.com/RishithaKorrapati/personal-research-assistant.git
cd personal-research-assistant
py -3.12 -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 2. Backend

```bash
pip install -r backend/requirements.txt
copy backend\.env.example backend\.env   # Windows
# cp backend/.env.example backend/.env   # macOS / Linux
```

Edit `backend/.env` and set your API key:

```env
OPENAI_API_KEY=sk-...
CHROMA_PERSIST_DIR=./storage/chroma_store
MAX_CHUNK_SIZE=300
CHUNK_OVERLAP=50
TOP_K_RESULTS=8
CITATION_PREVIEW_USE_LLM=true
```

Start the API (from `backend/`):

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

Optional: set `VITE_API_BASE=http://localhost:8000/api` in `frontend/.env` if the API runs elsewhere.

## Usage

1. Upload a **text-based PDF** (scanned image-only PDFs will fail or return empty text).
2. Review the **document map** (section-style summaries by page range).
3. Ask questions; check **answers**, **page citations**, and **confidence** bars.
4. **Export** the conversation when you are done.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required for embeddings and LLM calls |
| `CHROMA_PERSIST_DIR` | `./storage/chroma_store` | Local Chroma persistence |
| `MAX_CHUNK_SIZE` | `300` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Chunk overlap |
| `TOP_K_RESULTS` | `8` | Chunks sent to the answer model |
| `CITATION_PREVIEW_USE_LLM` | `true` | Readable citation labels via `gpt-4o-mini` |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload PDF → `doc_id`, title, summary sections |
| `POST` | `/api/query` | `{ doc_id, question }` → answer + citations |
| `POST` | `/api/export` | `{ doc_id, doc_title, qa_pairs, format }` → file download |

## Tech stack

| Layer | Tools |
|-------|--------|
| PDF parsing | pdfplumber |
| Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Vector store | ChromaDB (local, cosine) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Q&A / summaries | OpenAI `gpt-4o` / `gpt-4o-mini` |
| Export | python-docx, fpdf2 |
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | React, Vite, Axios, react-dropzone |

## Windows notes

- Use a **venv with Python 3.12**; system Python 3.9 may hit SQLite / native binding issues with some packages.
- ChromaDB is pinned to **0.4.x** with `pysqlite3` and `numpy<2` for compatibility.
- If port **8000** is busy, stop the old process or use another port and update CORS in `backend/main.py` and `frontend/src/api/client.js`.

## Cost (rough)

Per typical session (one paper, ~10 questions): on the order of **$0.10–0.15** in OpenAI usage (embeddings + summaries + answers + citation previews). Export is free (no API).

## License

MIT — see [LICENSE](LICENSE) if present; add a license file if you publish publicly.

## Author

[RishithaKorrapati](https://github.com/RishithaKorrapati)
