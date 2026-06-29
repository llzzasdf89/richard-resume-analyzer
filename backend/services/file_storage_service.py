from pathlib import Path

from core.config import settings

PDF_ERROR_MESSAGE = "Only PDF files up to 5MB are supported"


def validate_pdf_upload(filename: str, content_type: str, size: int) -> None:
    is_pdf_name = filename.lower().endswith(".pdf")
    is_pdf_type = content_type in {"application/pdf", "application/octet-stream"}
    if not is_pdf_name or not is_pdf_type or size > settings.max_upload_bytes:
        raise ValueError(PDF_ERROR_MESSAGE)


def storage_root() -> Path:
    root = Path(settings.upload_storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_storage_path(storage_key: str) -> Path:
    root = storage_root().resolve()
    target = (root / storage_key).resolve()
    if root != target and root not in target.parents:
        raise ValueError("Invalid storage path")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def store_resume_pdf(user_id: str, resume_id: str, file_bytes: bytes) -> str:
    storage_key = f"resumes/{user_id}/{resume_id}.pdf"
    safe_storage_path(storage_key).write_bytes(file_bytes)
    return storage_key


def read_storage_file(storage_key: str) -> bytes:
    return safe_storage_path(storage_key).read_bytes()


def delete_storage_file(storage_key: str | None) -> None:
    if not storage_key:
        return
    path = safe_storage_path(storage_key)
    if path.exists():
        path.unlink()
