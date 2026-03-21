from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "ingestion"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name: str = "sensor_data_exchange"
    jwt_secret_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
