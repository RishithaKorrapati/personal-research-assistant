from typing import Dict, List

import pdfplumber


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
                pages.append({"page_num": page_num, "text": text.strip()})
    return pages
