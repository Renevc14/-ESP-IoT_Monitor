from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "registry"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    allowed_origins: str = "http://localhost"

    class Config:
        env_file = ".env"


settings = Settings()
