from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import BaseModel


class Settings(BaseModel):
    """PoC 用のシンプルな設定クラス。

    将来的に LLM のAPIキーやその他設定値もここに集約する想定。
    """

    APP_NAME: str = "Decision Question Helper"
    # 12/3　実際に使用されているポートは8000番だったため、CORSの許可を書き換えた(K.T)
    CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]


@lru_cache()
def get_settings() -> Settings:
    """Settings のシングルトン取得関数。"""

    return Settings()


__all__ = ["Settings", "get_settings"]
