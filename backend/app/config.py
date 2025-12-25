from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Explicitly prioritize environment variable with fallback
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./macro_indicators.db')
    app_name: str = "Macro Indicators API"
    debug: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Log which database is being used for debugging
        if self.database_url.startswith('postgresql'):
            print(f"🐘 Using PostgreSQL: {self.database_url.split('@')[1] if '@' in self.database_url else 'connection confirmed'}")
        else:
            print(f"💾 Using SQLite: {self.database_url}")
    
    class Config:
        # Railway uses environment variables directly, not .env files
        # This allows both local .env files and Railway env vars to work
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
