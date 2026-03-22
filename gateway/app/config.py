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

    class Config:
        env_file = ".env"


settings = Settings()
