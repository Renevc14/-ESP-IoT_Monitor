from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "ingestion"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name: str = "sensor_data_exchange"
    jwt_secret_key: str  # obligatorio: el servicio no arranca sin secreto (fail-closed)
    allowed_origins: str = "http://localhost"
    # True = garantía de entrega (espera ack del broker). False = máximo throughput.
    publisher_confirms: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
