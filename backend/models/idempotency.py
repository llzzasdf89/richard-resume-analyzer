from psycopg2.extras import Json


def get_idempotency_record(conn, *, user_id: str, request_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, request_id, resource_type, resource_id, response_json, created_at
        FROM idempotency_keys
        WHERE user_id = %s AND request_id = %s
        """,
        (user_id, request_id),
    )
    row = cur.fetchone()
    cur.close()
    return _idempotency_row_to_dict(row) if row else None


def create_idempotency_record(
    conn,
    *,
    user_id: str,
    request_id: str,
    resource_type: str,
    resource_id: str | None,
    response_json: dict | None,
) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO idempotency_keys (user_id, request_id, resource_type, resource_id, response_json)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, user_id, request_id, resource_type, resource_id, response_json, created_at
        """,
        (user_id, request_id, resource_type, resource_id, Json(response_json or {})),
    )
    row = cur.fetchone()
    cur.close()
    return _idempotency_row_to_dict(row)


def _idempotency_row_to_dict(row) -> dict:
    keys = ["id", "user_id", "request_id", "resource_type", "resource_id", "response_json", "created_at"]
    return dict(zip(keys, row, strict=True))
