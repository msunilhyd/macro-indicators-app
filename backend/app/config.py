from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Prioritize environment variable over default
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./macro_indicators.db')
    app_name: str = "Macro Indicators API"
    debug: bool = True
    
    class Config:
        # Railway uses environment variables directly, not .env files
        # This allows both local .env files and Railway env vars to work
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
