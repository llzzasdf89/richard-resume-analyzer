import ssl

import certifi
from fastapi import Request
import jwt

from controllers.auth_controller import sync_user_from_claims
from core.config import settings
from core.exceptions import AppError
from models.db import get_conn


ASYMMETRIC_ALGORITHMS = {"RS256", "ES256"}


def get_supabase_jwks_url() -> str:
    if not settings.supabase_url:
        raise AppError("Supabase URL is not configured")
    return f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


def create_jwks_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def decode_supabase_token(token: str) -> dict:
    algorithm = jwt.get_unverified_header(token).get("alg")

    if algorithm in ASYMMETRIC_ALGORITHMS:
        signing_key = jwt.PyJWKClient(
            get_supabase_jwks_url(),
            ssl_context=create_jwks_ssl_context(),
        ).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience="authenticated",
            options={"verify_aud": False},
        )

    if algorithm != "HS256":
        raise AppError(f"Unsupported Supabase JWT algorithm: {algorithm}")

    if not settings.supabase_jwt_secret:
        raise AppError("Supabase JWT secret is not configured")

    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=[algorithm],
        audience="authenticated",
        options={"verify_aud": False},
    )


def extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise AppError("Unauthorized")
    return authorization[len(prefix):]


async def get_current_user(request: Request) -> dict:
    token = extract_bearer_token(request)
    claims = decode_supabase_token(token)
    conn = get_conn()
    try:
        user = sync_user_from_claims(conn, claims)
        conn.commit()
    finally:
        conn.close()
    request.state.user = user
    return user
