from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "identity"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    allowed_origins: str = "http://localhost"

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
