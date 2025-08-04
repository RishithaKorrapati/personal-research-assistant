import fitz
import re
def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from a PDF file using PyMuPDF.
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        page_text = page.get_text()
        full_text += page_text + "\n"
    cleaned_text = re.sub(r'\s*\n\s*', ' ',full_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text.strip()
