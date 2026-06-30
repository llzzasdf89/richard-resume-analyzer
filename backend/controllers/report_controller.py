from models.db import get_conn
from models.reports import delete_report_for_user, get_report_for_user, list_reports_for_user
from services.file_storage_service import delete_storage_file


def get_report(*, current_user: dict, report_id: str) -> dict | None:
    conn = get_conn()
    try:
        return get_report_for_user(conn, user_id=str(current_user["id"]), report_id=report_id)
    finally:
        conn.close()


def list_reports(*, current_user: dict) -> list[dict]:
    conn = get_conn()
    try:
        return list_reports_for_user(conn, user_id=str(current_user["id"]))
    finally:
        conn.close()


def delete_report(*, current_user: dict, report_id: str) -> bool:
    conn = get_conn()
    try:
        report = delete_report_for_user(conn, user_id=str(current_user["id"]), report_id=report_id)
        if not report:
            return False
        delete_storage_file(report["storage_key"])
        conn.commit()
        return True
    finally:
        conn.close()
