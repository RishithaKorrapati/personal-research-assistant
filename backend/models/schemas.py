from typing import List

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    page: int
    chunk_id: int
    source: str


class CitedChunk(BaseModel):
    page: int
    text: str
    preview: str = ""
    confidence: int


class QueryRequest(BaseModel):
    doc_id: str
    question: str


class QueryResponse(BaseModel):
    answer: str
    citations: List[CitedChunk]


class SummarySection(BaseModel):
    theme: str
    summary: str
    key_terms: List[str] = Field(default_factory=list)
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
    format: str
