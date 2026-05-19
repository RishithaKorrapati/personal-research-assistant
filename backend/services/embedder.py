import os
from typing import Dict, List, Optional

try:
    __import__("pysqlite3")
    import sys

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

import chromadb
import openai

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./storage/chroma_store")
client = chromadb.PersistentClient(path=PERSIST_DIR)

_openai_client: Optional[openai.OpenAI] = None


def _openai() -> openai.OpenAI:
    global _openai_client
    if _openai_client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy backend/.env.example to backend/.env and add your key."
            )
        _openai_client = openai.OpenAI(api_key=key)
    return _openai_client


def get_collection(doc_id: str):
    return client.get_or_create_collection(
        name=doc_id,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    response = _openai().embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]


def store_chunks(doc_id: str, chunks: List[Dict]) -> None:
    collection = get_collection(doc_id)
    batch_size = 100

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        ids = [f"{doc_id}_chunk_{c['metadata']['chunk_id']}" for c in batch]
        embeddings = embed_texts(texts)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
