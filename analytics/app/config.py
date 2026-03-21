from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "analytics"
    database_url: str

    class Config:
        env_file = ".env"


settings = Settings()
