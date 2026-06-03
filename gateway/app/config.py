from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "gateway"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    redis_url: str = "redis://redis:6379"
    allowed_origins: str = "http://localhost"
    # Upstreams para el proxy
    identity_url: str = "http://identity:8005"
    registry_url: str = "http://registry:8006"
    alerts_url: str = "http://alerts:8003"
    analytics_url: str = "http://analytics:8004"
    ingestion_url: str = "http://ingestion:8001"
    processing_url: str = "http://processing:8002"

    class Config:
        env_file = ".env"


settings = Settings()
