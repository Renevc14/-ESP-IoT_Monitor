from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "alerts"
    database_url: str
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name: str = "sensor_data_exchange"
    queue_name: str = "alerts_queue"

    class Config:
        env_file = ".env"


settings = Settings()
