from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./verdict.db"
    gemini_model: str = "gemini-2.0-flash"
    max_retries: int = 3
    rate_limit_rpm: int = 15

    model_config = {"env_file": ".env"}


settings = Settings()
