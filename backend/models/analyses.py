from psycopg2.extras import Json


VALID_TRANSITIONS = {
    "queued": {"processing"},
    "processing": {"completed", "failed"},
    "completed": {"deleted"},
    "failed": {"deleted"},
    "deleted": set(),
}


def transition_analysis_status(current: str, next_status: str) -> str:
    if next_status not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid analysis state transition: {current} -> {next_status}")
    return next_status


def create_analysis(
    conn,
    *,
    user_id: str,
    resume_id: str,
    jd_text: str,
    job_title: str | None = None,
    company: str | None = None,
) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO analyses (user_id, resume_id, jd_text, job_title, company, status, progress)
        VALUES (%s, %s, %s, %s, %s, 'queued', 0)
        RETURNING id, user_id, resume_id, jd_text, job_title, company, status, score, progress, current_step, steps_json, result_json, error, created_at, updated_at
        """,
        (user_id, resume_id, jd_text, job_title, company),
    )
    row = cur.fetchone()
    cur.close()
    return _analysis_row_to_dict(row)


def find_active_analysis_for_resume(conn, *, user_id: str, resume_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, resume_id, jd_text, job_title, company, status, score, progress, current_step, steps_json, result_json, error, created_at, updated_at
        FROM analyses
        WHERE user_id = %s
          AND resume_id = %s
          AND status IN ('queued', 'processing')
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, resume_id),
    )
    row = cur.fetchone()
    cur.close()
    return _analysis_row_to_dict(row) if row else None


def get_analysis_task_payload(conn, *, analysis_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT analyses.id, analyses.resume_id, analyses.jd_text, resumes.parsed_text
        FROM analyses
        JOIN resumes ON resumes.id = analyses.resume_id
        WHERE analyses.id = %s
        """,
        (analysis_id,),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return {
        "id": row[0],
        "resume_id": row[1],
        "jd_text": row[2],
        "resume_text": row[3] or "",
    }


def mark_analysis_processing(conn, *, analysis_id: str) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE analyses
        SET status = 'processing',
            progress = 15,
            current_step = 'queued',
            updated_at = now()
        WHERE id = %s
        """,
        (analysis_id,),
    )
    cur.close()


def mark_analysis_completed(conn, *, analysis_id: str, result: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE analyses
        SET status = 'completed',
            score = %s,
            progress = 100,
            current_step = %s,
            steps_json = %s,
            result_json = %s,
            updated_at = now()
        WHERE id = %s
        """,
        (
            result.get("score"),
            result.get("current_step", "completed"),
            Json(result.get("steps", [])),
            Json(result),
            analysis_id,
        ),
    )
    cur.close()


def mark_analysis_failed(conn, *, analysis_id: str, error: str) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE analyses
        SET status = 'failed',
            progress = 100,
            current_step = 'failed',
            error = %s,
            updated_at = now()
        WHERE id = %s
        """,
        (error, analysis_id),
    )
    cur.close()


def list_analyses_for_user(conn, *, user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, resume_id, jd_text, job_title, company, status, score, progress, current_step, steps_json, result_json, error, created_at, updated_at
        FROM analyses
        WHERE user_id = %s AND status != 'deleted'
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, limit, offset),
    )
    rows = cur.fetchall()
    cur.close()
    return [_analysis_row_to_dict(row) for row in rows]


def get_analysis_for_user(conn, *, user_id: str, analysis_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, resume_id, jd_text, job_title, company, status, score, progress, current_step, steps_json, result_json, error, created_at, updated_at
        FROM analyses
        WHERE id = %s AND user_id = %s AND status != 'deleted'
        """,
        (analysis_id, user_id),
    )
    row = cur.fetchone()
    cur.close()
    return _analysis_row_to_dict(row) if row else None


def mark_analysis_deleted(conn, *, user_id: str, analysis_id: str) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE analyses
        SET status = 'deleted', updated_at = now()
        WHERE id = %s AND user_id = %s
        """,
        (analysis_id, user_id),
    )
    cur.close()


def _analysis_row_to_dict(row) -> dict:
    keys = [
        "id",
        "user_id",
        "resume_id",
        "jd_text",
        "job_title",
        "company",
        "status",
        "score",
        "progress",
        "current_step",
        "steps",
        "result",
        "error",
        "created_at",
        "updated_at",
    ]
    return dict(zip(keys, row, strict=True))
