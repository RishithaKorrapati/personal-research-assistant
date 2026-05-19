import os
import shutil
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import SummaryMapResponse
from services.chunker import chunk_pages
from services.embedder import store_chunks
from services.llm import generate_summary_map
from services.pdf_parser import extract_pages

router = APIRouter()
UPLOAD_DIR = "./storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=SummaryMapResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    doc_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    pages = extract_pages(save_path)
    if not pages:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in PDF.",
        )

    chunks = chunk_pages(pages, source=file.filename)
    store_chunks(doc_id, chunks)

    summary_sections = generate_summary_map(pages)

    title = file.filename.rsplit(".pdf", 1)[0] if file.filename.lower().endswith(".pdf") else file.filename

    return SummaryMapResponse(
        doc_id=doc_id,
        title=title,
        sections=summary_sections,
    )
