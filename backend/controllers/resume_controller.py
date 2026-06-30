from models.db import get_conn
from models.resumes import delete_resume_for_user, get_resume_for_user, list_resumes_for_user
from services.file_storage_service import delete_storage_file


def list_resumes(*, current_user: dict) -> list[dict]:
    conn = get_conn()
    try:
        return list_resumes_for_user(conn, user_id=str(current_user["id"]))
    finally:
        conn.close()


def get_resume(*, current_user: dict, resume_id: str) -> dict | None:
    conn = get_conn()
    try:
        return get_resume_for_user(conn, user_id=str(current_user["id"]), resume_id=resume_id)
    finally:
        conn.close()


def delete_resume(*, current_user: dict, resume_id: str) -> bool:
    conn = get_conn()
    try:
        resume = get_resume_for_user(conn, user_id=str(current_user["id"]), resume_id=resume_id)
        if not resume:
            return False
        delete_storage_file(resume["storage_key"])
        delete_resume_for_user(conn, user_id=str(current_user["id"]), resume_id=resume_id)
        conn.commit()
        return True
    finally:
        conn.close()
