from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "processing"
    database_url: str
    redis_url: str = "redis://redis:6379"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name: str = "sensor_data_exchange"
    queue_name: str = "processing_queue"
    redis_cache_ttl: int = 300  # 5 minutes

    class Config:
        env_file = ".env"


settings = Settings()
