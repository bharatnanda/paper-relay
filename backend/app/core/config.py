from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "PaperRelay"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/paperrelay"
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_BASE_URL: str = ""
    AZURE_OPENAI_MODEL: str = ""
    OPENAI_MAX_TOKENS: int = 4096
    MAGIC_LINK_SECRET: str = "dev-only-change-me"
    MAGIC_LINK_EXPIRY_HOURS: int = 24
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
