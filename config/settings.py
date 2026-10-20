from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MODEL_NAME: str = "openai/gpt-4o-mini"

    # Database
    DATABASE_PATH: Path = PROJECT_ROOT / "data" / "northwind.db"
    CURRENCY: str = "USD"


settings = Settings()

settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)