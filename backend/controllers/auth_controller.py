from models.identities import get_identity, upsert_identity
from models.users import get_user_by_id, upsert_user


def normalize_user_claims(claims: dict) -> dict:
    metadata = claims.get("user_metadata") or {}
    app_metadata = claims.get("app_metadata") or {}
    return {
        "provider": "supabase",
        "provider_user_id": claims["sub"],
        "auth_provider": app_metadata.get("provider"),
        "email": claims.get("email"),
        "name": metadata.get("name") or metadata.get("full_name"),
        "avatar_url": metadata.get("avatar_url") or metadata.get("picture"),
    }


def sync_user_from_claims(conn, claims: dict) -> dict:
    normalized = normalize_user_claims(claims)
    identity = get_identity(
        conn,
        provider=normalized["provider"],
        provider_user_id=normalized["provider_user_id"],
    )
    if identity:
        user = get_user_by_id(conn, identity["user_id"])
        if user:
            return user

    user = upsert_user(
        conn,
        email=normalized["email"],
        name=normalized["name"],
        avatar_url=normalized["avatar_url"],
    )
    upsert_identity(
        conn,
        user_id=user["id"],
        provider=normalized["provider"],
        provider_user_id=normalized["provider_user_id"],
        auth_provider=normalized["auth_provider"],
        raw_profile=claims,
    )
    return user
