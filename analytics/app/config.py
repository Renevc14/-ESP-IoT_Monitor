from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "analytics"
    database_url: str
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name: str = "sensor_data_exchange"
    queue_name: str = "analytics_queue"
    jwt_secret_key: str  # obligatorio: el servicio no arranca sin secreto (fail-closed)
    allowed_origins: str = "http://localhost"
    # Composición de API (los dispositivos y alertas viven en otros servicios)
    registry_url: str = "http://registry:8006"
    alerts_url: str = "http://alerts:8003"

    class Config:
        env_file = ".env"


settings = Settings()
