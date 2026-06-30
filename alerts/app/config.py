from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "alerts"
    database_url: str
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name: str = "sensor_data_exchange"
    queue_name: str = "alerts_queue"
    jwt_secret_key: str  # obligatorio: el servicio no arranca sin secreto (fail-closed)
    allowed_origins: str = "http://localhost"

    # SMTP / email notifications
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_from: str = "alerts@iot.local"
    alert_emails: str = ""  # default recipients (comma-separated) when a rule has none

    @property
    def alert_emails_list(self) -> list[str]:
        return [e.strip() for e in self.alert_emails.split(",") if e.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
