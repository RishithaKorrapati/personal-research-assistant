import os
from typing import Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
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
        for chunk_text in splitter.split_text(page_text):
            all_chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        "page": page_num,
                        "chunk_id": chunk_id,
                        "source": source,
                    },
                }
            )
            chunk_id += 1

    return all_chunks
