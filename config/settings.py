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

    #langfuse
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"
    LANGFUSE_PROJECT_NAME: str = "sql-analyst-agent"

    # Demo
    DEMO_ACCESS_CODE: str = ""
    MAX_QUESTIONS_PER_SESSION: int = 5


settings = Settings()

settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)