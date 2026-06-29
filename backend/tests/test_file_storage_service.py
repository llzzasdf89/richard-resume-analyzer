import pytest

from services.file_storage_service import validate_pdf_upload


def test_accepts_pdf_under_5mb():
    validate_pdf_upload("resume.pdf", "application/pdf", 1024)


def test_rejects_non_pdf_extension():
    with pytest.raises(ValueError, match="Only PDF files up to 5MB are supported"):
        validate_pdf_upload("resume.txt", "text/plain", 1024)


def test_rejects_pdf_over_5mb():
    with pytest.raises(ValueError, match="Only PDF files up to 5MB are supported"):
        validate_pdf_upload("resume.pdf", "application/pdf", 5 * 1024 * 1024 + 1)
