"""앱 설정 모듈"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 앱 기본 설정
    app_name: str = "MoneyLog"
    app_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"

    # 데이터베이스
    database_url: str = "sqlite+aiosqlite:///./moneylog.db"

    # AI 설정 (선택사항)
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
