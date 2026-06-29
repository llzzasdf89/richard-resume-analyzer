def create_report(
    conn,
    *,
    user_id: str,
    analysis_id: str,
    title: str,
    content: str,
    storage_key: str,
    format: str = "pdf",
) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reports (user_id, analysis_id, title, format, content, storage_key)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, analysis_id, title, format, content, storage_key, created_at, updated_at
        """,
        (user_id, analysis_id, title, format, content, storage_key),
    )
    row = cur.fetchone()
    cur.close()
    return _report_row_to_dict(row)


def get_report_for_user(conn, *, user_id: str, report_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, analysis_id, title, format, content, storage_key, created_at, updated_at
        FROM reports
        WHERE id = %s AND user_id = %s
        """,
        (report_id, user_id),
    )
    row = cur.fetchone()
    cur.close()
    return _report_row_to_dict(row) if row else None


def list_reports_for_user(conn, *, user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, analysis_id, title, format, content, storage_key, created_at, updated_at
        FROM reports
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, limit, offset),
    )
    rows = cur.fetchall()
    cur.close()
    return [_report_row_to_dict(row) for row in rows]


def delete_report_for_user(conn, *, user_id: str, report_id: str) -> dict | None:
    report = get_report_for_user(conn, user_id=user_id, report_id=report_id)
    if not report:
        return None
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM reports WHERE id = %s AND user_id = %s",
        (report_id, user_id),
    )
    cur.close()
    return report


def _report_row_to_dict(row) -> dict:
    keys = ["id", "user_id", "analysis_id", "title", "format", "content", "storage_key", "created_at", "updated_at"]
    return dict(zip(keys, row, strict=True))
