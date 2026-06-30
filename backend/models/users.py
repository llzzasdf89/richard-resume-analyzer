def upsert_user(conn, *, email: str | None, name: str | None, avatar_url: str | None) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (email, name, avatar_url)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id, email, name, avatar_url, created_at, updated_at
        """,
        (email, name, avatar_url),
    )
    row = cur.fetchone()
    if row is None and email:
        cur.execute(
            """
            SELECT id, email, name, avatar_url, created_at, updated_at
            FROM users
            WHERE email = %s
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (email,),
        )
        row = cur.fetchone()
    cur.close()
    return _user_row_to_dict(row)


def get_user_by_id(conn, user_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, name, avatar_url, created_at, updated_at
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    return _user_row_to_dict(row) if row else None


def _user_row_to_dict(row) -> dict:
    keys = ["id", "email", "name", "avatar_url", "created_at", "updated_at"]
    return dict(zip(keys, row, strict=True))
