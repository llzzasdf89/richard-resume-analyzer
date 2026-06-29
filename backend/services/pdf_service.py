from tools import parse_pdf


def parse_resume_pdf(file_bytes: bytes) -> str:
    return parse_pdf(file_bytes)
