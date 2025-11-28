from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """PoC 用のシンプルな設定クラス。

    将来的に LLM のAPIキーやその他設定値もここに集約する想定。
    """

    # 11/28 add: APIキー設定
    # dotenvで取得する
    OPEN_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    APP_NAME: str = "Decision Question Helper"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
    ]

    # 11/28 add: APIキーを.envから取得
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # .envに知らない変数があっても無視    
    )


@lru_cache()
def get_settings() -> Settings:
    """Settings のシングルトン取得関数。"""

    return Settings()


__all__ = ["Settings", "get_settings"]
