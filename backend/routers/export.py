import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from models.schemas import ExportRequest
from services.exporter import export_docx, export_pdf

router = APIRouter()
EXPORT_DIR = "./storage/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


@router.post("/export")
async def export_report(request: ExportRequest):
    fmt = request.format.lower()
    output_path = os.path.join(EXPORT_DIR, f"{request.doc_id}_report.{fmt}")
    qa_pairs = [qa.model_dump() for qa in request.qa_pairs]

    if fmt == "docx":
        export_docx(request.doc_title, qa_pairs, output_path)
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    elif fmt == "pdf":
        export_pdf(request.doc_title, qa_pairs, output_path)
        media_type = "application/pdf"
    else:
        raise HTTPException(
            status_code=400,
            detail="Format must be 'docx' or 'pdf'.",
        )

    return FileResponse(
        path=output_path,
        media_type=media_type,
        filename=f"report.{fmt}",
    )
