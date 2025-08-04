from src.chunker import extract_text_from_pdf
pdf_path = "data/sample.pdf"
text = extract_text_from_pdf(pdf_path)
print("Extracted test from PDF:")
print(text[:500])