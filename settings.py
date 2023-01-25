from functools import lru_cache
from pydantic.env_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = '/app/.env'
    AUTH_TOKEN: str
    TWITTER_ENDPOINT: str
    REDIS_URL: str
    SQLALCHEMY_DATABASE_URL: str
    TWITTER_LIMIT_PER_BATCH_REQUEST: int = 100


@lru_cache
def get_settings():
    return Settings()
