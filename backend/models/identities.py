from psycopg2.extras import Json


def upsert_identity(
    conn,
    *,
    user_id: str,
    provider: str,
    provider_user_id: str,
    auth_provider: str | None,
    raw_profile: dict | None,
) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_identities (user_id, provider, provider_user_id, auth_provider, raw_profile)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (provider, provider_user_id)
        DO UPDATE SET auth_provider = EXCLUDED.auth_provider, raw_profile = EXCLUDED.raw_profile
        RETURNING id, user_id, provider, provider_user_id, auth_provider, raw_profile, created_at
        """,
        (user_id, provider, provider_user_id, auth_provider, Json(raw_profile or {})),
    )
    row = cur.fetchone()
    cur.close()
    return _identity_row_to_dict(row)


def get_identity(conn, *, provider: str, provider_user_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, provider, provider_user_id, auth_provider, raw_profile, created_at
        FROM user_identities
        WHERE provider = %s AND provider_user_id = %s
        """,
        (provider, provider_user_id),
    )
    row = cur.fetchone()
    cur.close()
    return _identity_row_to_dict(row) if row else None


def _identity_row_to_dict(row) -> dict:
    keys = ["id", "user_id", "provider", "provider_user_id", "auth_provider", "raw_profile", "created_at"]
    return dict(zip(keys, row, strict=True))
