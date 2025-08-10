from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="Water Watch API")
    api_prefix: str = Field(default="/api/v1")
    debug: bool = Field(default=True)

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./waterwatch.db")

    # Redis
    redis_url: str = Field(default="redis://redis:6379/0")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

