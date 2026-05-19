import os
from collections import defaultdict
from typing import Dict, List

from .embedder import embed_texts, get_collection

TOP_K = int(os.getenv("TOP_K_RESULTS", "8"))


def retrieve_chunks(doc_id: str, question: str) -> List[Dict]:
    """
    Embed the question, search ChromaDB, return top chunks with page diversity.

    Fetches more candidates than TOP_K, then prefers at most 2 chunks per page
    so broad questions are less likely to retrieve only bibliography from one page.

    Confidence: ChromaDB cosine distance is 0 (identical) to 2 (opposite).
    confidence = round((1 - distance / 2) * 100)
    """
    collection = get_collection(doc_id)
    question_embedding = embed_texts([question])[0]

    count = collection.count()
    fetch_n = min(max(TOP_K * 3, TOP_K), max(count, 1), 36)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=fetch_n,
        include=["documents", "metadatas", "distances"],
    )

    candidates: List[Dict] = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        confidence = round((1 - distance / 2) * 100)
        page = metadata["page"]
        if isinstance(page, float):
            page = int(page)
        candidates.append(
            {
                "text": text,
                "page": int(page),
                "confidence": confidence,
            }
        )

    selected: List[Dict] = []
    used_indices = set()
    per_page = defaultdict(int)
    max_per_page = 2

    for i, c in enumerate(candidates):
        if len(selected) >= TOP_K:
            break
        if per_page[c["page"]] >= max_per_page:
            continue
        per_page[c["page"]] += 1
        selected.append(c)
        used_indices.add(i)

    for i, c in enumerate(candidates):
        if len(selected) >= TOP_K:
            break
        if i in used_indices:
            continue
        selected.append(c)
        used_indices.add(i)

    return sorted(selected, key=lambda x: x["confidence"], reverse=True)
