from fastapi import APIRouter, HTTPException

from models.schemas import CitedChunk, QueryRequest, QueryResponse
from services.citation_preview import attach_citation_previews
from services.llm import answer_question
from services.retriever import retrieve_chunks

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    chunks = retrieve_chunks(request.doc_id, request.question)

    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant content found.")

    attach_citation_previews(chunks)

    answer = answer_question(request.question, chunks)

    cited_chunks = [
        CitedChunk(
            page=c["page"],
            text=c["text"],
            preview=c.get("preview") or "",
            confidence=c["confidence"],
        )
        for c in chunks
    ]

    return QueryResponse(answer=answer, citations=cited_chunks)
