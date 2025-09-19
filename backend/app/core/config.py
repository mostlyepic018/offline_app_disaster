from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Offline Disaster Alert API"
    debug: bool = True
    database_url: str = Field(default="sqlite:///./disaster.db", description="SQLAlchemy database URL")
    gateway_auth_token: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
