def create_resume(
    conn,
    *,
    resume_id: str,
    user_id: str,
    original_filename: str,
    storage_key: str,
    file_size: int,
    mime_type: str,
    parsed_text: str,
) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO resumes (id, user_id, original_filename, storage_key, file_size, mime_type, parsed_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, original_filename, storage_key, file_size, mime_type, parsed_text, created_at
        """,
        (resume_id, user_id, original_filename, storage_key, file_size, mime_type, parsed_text),
    )
    row = cur.fetchone()
    cur.close()
    return _resume_row_to_dict(row)


def get_resume_for_user(conn, *, user_id: str, resume_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, original_filename, storage_key, file_size, mime_type, parsed_text, created_at
        FROM resumes
        WHERE id = %s AND user_id = %s
        """,
        (resume_id, user_id),
    )
    row = cur.fetchone()
    cur.close()
    return _resume_row_to_dict(row) if row else None


def list_resumes_for_user(conn, *, user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, original_filename, storage_key, file_size, mime_type, parsed_text, created_at
        FROM resumes
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, limit, offset),
    )
    rows = cur.fetchall()
    cur.close()
    return [_resume_row_to_dict(row) for row in rows]


def delete_resume_for_user(conn, *, user_id: str, resume_id: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM resumes WHERE id = %s AND user_id = %s",
        (resume_id, user_id),
    )
    cur.close()


def _resume_row_to_dict(row) -> dict:
    keys = ["id", "user_id", "original_filename", "storage_key", "file_size", "mime_type", "parsed_text", "created_at"]
    return dict(zip(keys, row, strict=True))
