from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from uuid import uuid4

from app.models import NewIdea, Question, QuestionFeedback


def _get_log_root_dir() -> Path:
    """ログのルートディレクトリ (backend/app/logs) を返す。"""

    return Path(__file__).resolve().parent.parent / "logs"


def _get_log_dir() -> Path:
    """実際にセッションログを保存するディレクトリ (logs/logs) を返す。"""

    return _get_log_root_dir() / "logs"


def _ensure_log_dir() -> Path:
    """ログディレクトリを作成し、その Path を返す。"""

    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _get_log_path(session_id: str) -> Path:
    """セッションIDからログファイルのパスを生成する。"""

    return _get_log_dir() / f"session_{session_id}.json"


def _now_iso_utc() -> str:
    """現在時刻（UTC）の ISO8601 文字列を返す。"""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_session_log(new_idea: NewIdea, questions: List[Question]) -> str:
    """新しい自己レビューセッションのログファイルを作成する。

    ログスキーマは 04_logging_service_prompt.md に準拠し、
    評価指標A/Bおよびサブ指標 (2-1, 2-2, 3-1, 3-2, 3-3, 4-1, 4-2) と 1:1 で対応する。
    """

    _ensure_log_dir()

    session_id = str(uuid4())
    created_at = _now_iso_utc()

    data = {
        "session_id": session_id,
        "created_at": created_at,
        "new_idea": new_idea.dict(),
        "questions": [q.dict() for q in questions],
        # 評価指標A (2-1, 2-2): 問いごとの有用性・行動変化
        "feedbacks": [],
        # 評価指標B (3-1, 3-2, 3-3): 体験の有効性・再利用意向・質の向上感
        "session_evaluation": {
            "experience_score": None,
            "reuse_intent_score": None,
            "perceived_quality_gain_score": None,
        },
        # サブ指標 (4-1, 4-2): クリックやメモなどのインタラクションログ
        "interaction_logs": [],
        "session_times": {
            "started_at": created_at,
            "ended_at": None,
        },
    }

    path = _get_log_path(session_id)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return session_id


def append_feedback(session_id: str, feedbacks: List[QuestionFeedback]) -> None:
    """指定セッションの feedbacks を上書き保存する。

    - ファイルが存在しない場合は FileNotFoundError を送出。
    - JSON パースに失敗した場合は ValueError を送出。
    - feedbacks フィールドのみを更新し、他フィールドは変更しない。
    """

    _ensure_log_dir()
    path = _get_log_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"session log not found: {session_id}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON log for session: {session_id}") from exc

    data["feedbacks"] = [fb.dict() for fb in feedbacks]

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 12/7 ログ管理方法の追加
def add_idea_snapshot(session_id: str, title: str, content: str) -> None: # 引数名を修正
    """
    企画案のスナップショットを履歴に追加保存する。
    """
    _ensure_log_dir()
    path = _get_log_path(session_id)
    
    if not path.exists():
        raise FileNotFoundError(f"session log not found: {session_id}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON log for session: {session_id}") from exc

    # idea_history フィールドがなければ作成
    if "idea_history" not in data:
        data["idea_history"] = []

    # 新しいスナップショットを作成
    snapshot = {
        "step": len(data["idea_history"]) + 1,
        "title": title,
        "summary": content,
        "timestamp": _now_iso_utc()
    }

    data["idea_history"].append(snapshot)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# __all__ を更新
__all__ = ["create_session_log", "append_feedback", "add_idea_snapshot"]
