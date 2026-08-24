from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url_prod: str
    database_url_test: str
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 90
    cors_origins: list[str] = ["http://localhost:5173"]
    environment: str = "development"

    # Cloudflare R2 (S3-compatible) — empty defaults so dev runs without uploads configured.
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_prod: str = ""
    r2_bucket_test: str = ""
    r2_signed_url_ttl_seconds: int = 86400

    # SOCKS5 proxy for MDOC OTIS. Cloudflare 403s this server's IP on every
    # mdocweb.state.mi.us path, so the lookup route needs an egress elsewhere
    # (infra/otis-tunnel.sh opens one over reverse SSH). Empty is a supported
    # state, not a misconfiguration: /mdoc/lookup then fails with a 502 that
    # says so, and /mdoc/parse still works on HTML the caller supplies.
    mdoc_proxy: str = ""


settings = Settings()
