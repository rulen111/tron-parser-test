import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tronparser"
    TRONPY_API_KEY: Optional[str] = None
    TRONPY_TIMEOUT: float = 10.
    TRONPY_NETWORK: str = "nile"


class TestSettings(Settings):
    DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_tronparser"
    APP_BASE_URL: str = "http://test"


class LocalSettings(Settings):
    ...


class ProductionSettings(Settings):
    ...


def get_settings() -> Settings:
    env = os.getenv("ENV", "local")
    settings_type = {
        "test": TestSettings(),
        "local": LocalSettings(),
        "prod": ProductionSettings(),
    }
    return settings_type[env]


settings = get_settings()
