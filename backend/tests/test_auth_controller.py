from controllers.auth_controller import normalize_user_claims


def test_normalize_user_claims_from_supabase_jwt():
    claims = {
        "sub": "user-123",
        "email": "dev@example.com",
        "user_metadata": {
            "name": "Dev User",
            "avatar_url": "https://example.com/a.png",
        },
        "app_metadata": {"provider": "github"},
    }

    assert normalize_user_claims(claims) == {
        "provider": "supabase",
        "provider_user_id": "user-123",
        "auth_provider": "github",
        "email": "dev@example.com",
        "name": "Dev User",
        "avatar_url": "https://example.com/a.png",
    }
