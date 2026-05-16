from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./supply_chain_ai.db"
    SECRET_KEY: str = "my_super_secret_key_123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    OPENAI_API_KEY: str = "your_openai_api_key_here"

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        case_sensitive=True,
    )


settings = Settings()