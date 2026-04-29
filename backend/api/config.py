from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリ全体の設定。優先度は os.environ > .env > デフォルト値。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/docs_checker"
    jwt_secret: str = "change-me"
    jwt_expire_hours: int = 24
    initial_admin_username: str = "admin"
    initial_admin_password: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"


settings = Settings()
