from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "gateway"
    database_url: str
    redis_url: str = "redis://redis:6379"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    allowed_origins: str = "http://localhost"
    analytics_service_url: str = "http://analytics:8004"
    alerts_url: str = "http://alerts:8003"
    ingestion_url: str = "http://ingestion:8001"
    processing_url: str = "http://processing:8002"

    # Cookies (refresh token) — Secure requires HTTPS, off by default for local
    cookie_secure: bool = False
    frontend_url: str = "http://localhost"

    # SMTP (password recovery emails)
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_from: str = "no-reply@iot.local"

    class Config:
        env_file = ".env"


settings = Settings()
