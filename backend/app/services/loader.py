from __future__ import annotations

import json
from pathlib import Path

from app.models import DecisionCase, Question

_CASES: list[DecisionCase] | None = None


def load_decision_cases(path: Path | None = None) -> list[DecisionCase]:
    """JSON ファイルから DecisionCase の一覧を読み込んでキャッシュする。

    - path が None の場合は、現在ファイルからの相対パスで
      ../data/decision_case.json をデフォルトとする。
    - すでに読み込まれている場合は再読み込みせず、キャッシュを返す。
    """
    global _CASES

    if _CASES is not None:
        return _CASES

    if path is None:
        services_dir = Path(__file__).resolve().parent
        # backend/app/services/ から 2つ上に上がって backend/ を起点に data/decision_case.json を探す
        path = services_dir.parent.parent / "data" / "decision_case.json"

    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    _CASES = [DecisionCase(**item) for item in raw_data]
    return _CASES

# 11/27 add: デモデータの取り込み
def load_demo_questions(path: Path | None = None) -> list[Question]:
    """
    JSON ファイルから Question のデモデータを読み込む。
    """
    if path is None:
        services_dir = Path(__file__).resolve().parent
        # backend/app/services/ から 2つ上に上がって backend/ を起点に data/decision_case.json を探す
        path = services_dir.parent.parent / "data" / "demo_questions.json"

    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    questions = [Question(**item) for item in raw_data]
    return questions

def get_decision_cases() -> list[DecisionCase]:
    """キャッシュされた DecisionCase の一覧を返す。

    - 未ロードの場合は load_decision_cases() を内部で呼び出す。
    """
    global _CASES

    if _CASES is None:
        load_decision_cases()

    assert _CASES is not None
    return _CASES


__all__ = ["load_decision_cases", "get_decision_cases"]
