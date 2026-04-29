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
    allowed_origins: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        """カンマ区切りの allowed_origins を list に分解する。"""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
