from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "GreenForecast API"
    DATABASE_URL: str = "sqlite:///./data/greenforecast.db"
    LLM_API_KEY: str = ""
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    SECRET_KEY: str = "supersecret"
    DOCUMENT_ENCRYPTION_KEY: str = "UoZ7rK2b5H8J9XcYdF1vA3mN6wQ4tT0sV_xX-LqP7hA="
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    @property
    def supabase_admin_key(self) -> str:
        return self.SUPABASE_SECRET_KEY or self.SUPABASE_SERVICE_ROLE_KEY

    @property
    def supabase_api_key(self) -> str:
        return self.SUPABASE_PUBLISHABLE_KEY or self.SUPABASE_ANON_KEY or self.supabase_admin_key

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
