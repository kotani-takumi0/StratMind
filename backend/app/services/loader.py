from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.models import DecisionCase

_CASES: Optional[List[DecisionCase]] = None


def load_decision_cases(path: Path) -> List[DecisionCase]:
    """decision_case.json を読み込み、DecisionCase のリストとして返す。

    起動時に一度だけ呼び出されることを想定している。
    2回目以降の呼び出しでは、キャッシュされた結果をそのまま返す。
    """
    global _CASES

    if _CASES is not None:
        return _CASES

    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # JSON は DecisionCase の配列を前提とする
    _CASES = [DecisionCase(**item) for item in raw_data]
    return _CASES


def get_decision_cases() -> List[DecisionCase]:
    """キャッシュされている DecisionCase 一覧を返す。

    起動時に load_decision_cases() が呼ばれている前提。
    """
    if _CASES is None:
        raise RuntimeError("Decision cases are not loaded. Call load_decision_cases() first.")
    return _CASES


__all__ = ["load_decision_cases", "get_decision_cases"]
