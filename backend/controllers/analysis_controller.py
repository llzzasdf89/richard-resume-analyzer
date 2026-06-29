import uuid

from fastapi import UploadFile

from core.responses import api_error, api_success
from models.analyses import (
    create_analysis,
    find_active_analysis_for_resume,
    get_analysis_for_user,
    list_analyses_for_user,
    mark_analysis_deleted,
)
from models.db import get_conn
from models.idempotency import create_idempotency_record, get_idempotency_record
from models.resumes import create_resume
from services.analysis_task_service import active_resume_tasks, start_analysis_task
from services.file_storage_service import store_resume_pdf, validate_pdf_upload
from services.pdf_service import parse_resume_pdf


async def create_analysis_from_upload(
    *,
    current_user: dict,
    request_id: str,
    resume: UploadFile,
    jd_text: str,
    job_title: str | None,
    company: str | None,
) -> dict:
    user_id = str(current_user["id"])
    file_bytes = await resume.read()
    validate_pdf_upload(
        resume.filename or "resume.pdf",
        resume.content_type or "application/octet-stream",
        len(file_bytes),
    )

    conn = get_conn()
    try:
        existing = get_idempotency_record(conn, user_id=user_id, request_id=request_id)
        if existing and existing.get("response_json"):
            return existing["response_json"]

        resume_id = str(uuid.uuid4())
        active_analysis_id = active_resume_tasks.get_active_analysis(user_id, resume_id)
        if active_analysis_id:
            return api_error(
                "This resume is already being analyzed. Please wait for the current task to finish.",
                {"analysis_id": active_analysis_id, "status": "processing"},
            )

        storage_key = store_resume_pdf(user_id, resume_id, file_bytes)
        parsed_text = parse_resume_pdf(file_bytes)
        resume_record = create_resume(
            conn,
            resume_id=resume_id,
            user_id=user_id,
            original_filename=resume.filename or "resume.pdf",
            storage_key=storage_key,
            file_size=len(file_bytes),
            mime_type=resume.content_type or "application/pdf",
            parsed_text=parsed_text,
        )
        active = find_active_analysis_for_resume(conn, user_id=user_id, resume_id=resume_record["id"])
        if active:
            return api_error(
                "This resume is already being analyzed. Please wait for the current task to finish.",
                {"analysis_id": active["id"], "status": active["status"]},
            )

        analysis = create_analysis(
            conn,
            user_id=user_id,
            resume_id=resume_record["id"],
            jd_text=jd_text,
            job_title=job_title,
            company=company,
        )
        response = api_success(
            {
                "analysis_id": str(analysis["id"]),
                "resume_id": str(resume_record["id"]),
                "status": analysis["status"],
            }
        )
        create_idempotency_record(
            conn,
            user_id=user_id,
            request_id=request_id,
            resource_type="analysis",
            resource_id=str(analysis["id"]),
            response_json=response,
        )
        conn.commit()

        if active_resume_tasks.try_start(user_id, str(resume_record["id"]), str(analysis["id"])):
            start_analysis_task(
                user_id=user_id,
                resume_id=str(resume_record["id"]),
                analysis_id=str(analysis["id"]),
            )
        return response
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_analyses(*, current_user: dict) -> list[dict]:
    conn = get_conn()
    try:
        return list_analyses_for_user(conn, user_id=str(current_user["id"]))
    finally:
        conn.close()


def get_analysis(*, current_user: dict, analysis_id: str) -> dict | None:
    conn = get_conn()
    try:
        return get_analysis_for_user(conn, user_id=str(current_user["id"]), analysis_id=analysis_id)
    finally:
        conn.close()


def delete_analysis(*, current_user: dict, analysis_id: str) -> None:
    conn = get_conn()
    try:
        mark_analysis_deleted(conn, user_id=str(current_user["id"]), analysis_id=analysis_id)
        conn.commit()
    finally:
        conn.close()
