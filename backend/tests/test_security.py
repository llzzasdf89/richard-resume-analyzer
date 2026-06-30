from types import SimpleNamespace

from core import security


def test_decode_supabase_token_uses_jwks_for_rs256(monkeypatch):
    captured = {}

    class FakeSigningKey:
        key = "public-key"

    class FakePyJWKClient:
        def __init__(self, jwks_url, ssl_context=None):
            captured["jwks_url"] = jwks_url
            captured["ssl_context"] = ssl_context

        def get_signing_key_from_jwt(self, token):
            captured["token"] = token
            return FakeSigningKey()

    def fake_decode(token, key, algorithms, audience, options):
        captured["decode"] = {
            "token": token,
            "key": key,
            "algorithms": algorithms,
            "audience": audience,
            "options": options,
        }
        return {"sub": "user-123"}

    monkeypatch.setattr(
        security,
        "settings",
        SimpleNamespace(
            supabase_jwt_secret="legacy-secret",
            supabase_url="https://project-ref.supabase.co",
        ),
    )
    monkeypatch.setattr(security.jwt, "get_unverified_header", lambda token: {"alg": "RS256"})
    monkeypatch.setattr(security.jwt, "PyJWKClient", FakePyJWKClient)
    monkeypatch.setattr(security.jwt, "decode", fake_decode)

    claims = security.decode_supabase_token("token")

    assert claims == {"sub": "user-123"}
    assert captured["jwks_url"] == "https://project-ref.supabase.co/auth/v1/.well-known/jwks.json"
    assert captured["ssl_context"] is not None
    assert captured["token"] == "token"
    assert captured["decode"] == {
        "token": "token",
        "key": "public-key",
        "algorithms": ["RS256"],
        "audience": "authenticated",
        "options": {"verify_aud": False},
    }


def test_decode_supabase_token_keeps_hs256_secret_path(monkeypatch):
    captured = {}

    def fake_decode(token, key, algorithms, audience, options):
        captured["decode"] = {
            "token": token,
            "key": key,
            "algorithms": algorithms,
            "audience": audience,
            "options": options,
        }
        return {"sub": "user-123"}

    monkeypatch.setattr(
        security,
        "settings",
        SimpleNamespace(
            supabase_jwt_secret="legacy-secret",
            supabase_url="https://project-ref.supabase.co",
        ),
    )
    monkeypatch.setattr(security.jwt, "get_unverified_header", lambda token: {"alg": "HS256"})
    monkeypatch.setattr(security.jwt, "decode", fake_decode)

    claims = security.decode_supabase_token("token")

    assert claims == {"sub": "user-123"}
    assert captured["decode"] == {
        "token": "token",
        "key": "legacy-secret",
        "algorithms": ["HS256"],
        "audience": "authenticated",
        "options": {"verify_aud": False},
    }
