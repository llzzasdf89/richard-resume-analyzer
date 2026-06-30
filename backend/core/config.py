from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_prefix: str = "/api/v1"
    upload_storage_dir: str = os.getenv("UPLOAD_STORAGE_DIR", "uploads")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")


settings = Settings()
