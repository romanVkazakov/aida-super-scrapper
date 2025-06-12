from app.log_config import init_logging
init_logging(__name__)
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyUrl

class Settings(BaseSettings):
    # --- scraping ---
    MIN_DELAY: float = 3.0
    GOOD_TTL:  int   = 3600
    TOR_FALLBACK: AnyUrl = "socks5://tor:9050"

    # --- integrations/testing ---
    TEST_NEWS_URL:     AnyUrl | None = None
    HEALTHCHECK_URL:   AnyUrl | None = None

    # --- infra ---
    REDIS_URL: AnyUrl = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
