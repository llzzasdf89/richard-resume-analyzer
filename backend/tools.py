# tools.py
import fitz  # PyMuPDF

def parse_pdf(file_bytes: bytes) -> str:
    """解析 PDF 文件，返回文本内容"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()