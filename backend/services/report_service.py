from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from services.file_storage_service import safe_storage_path


def generate_report_pdf(user_id: str, report_id: str, content: str) -> str:
    storage_key = f"reports/{user_id}/{report_id}.pdf"
    path = safe_storage_path(storage_key)
    _write_pdf(path, content)
    return storage_key


def _write_pdf(path: Path, content: str) -> None:
    pdf = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    x = 56
    y = height - 56
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(x, y, "Resume Analysis Report")
    y -= 32
    pdf.setFont("Helvetica", 10)

    for raw_line in content.splitlines() or ["No report content available."]:
        line = raw_line.strip()
        if not line:
            y -= 12
            continue
        for chunk in _wrap_line(line, max_chars=95):
            if y < 56:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 56
            pdf.drawString(x, y, chunk)
            y -= 14

    pdf.save()


def _wrap_line(line: str, max_chars: int) -> list[str]:
    chunks = []
    current = line
    while len(current) > max_chars:
        chunks.append(current[:max_chars])
        current = current[max_chars:]
    chunks.append(current)
    return chunks
