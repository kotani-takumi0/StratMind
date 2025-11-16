from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

from app.models import (
    DecisionCase,
    FeedbackRequest,
    NewIdea,
    Question,
)


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def create_session_log(
    idea: NewIdea,
    similar_cases: List[DecisionCase],
    questions: List[Question],
) -> str:
    """新しいセッションログを作成し、ファイルに保存する。

    仕様は 00_context.md の「9. ログ設計」に準拠する。
    """

    _ensure_log_dir()

    session_id = str(uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"

    data = {
        "session_id": session_id,
        "created_at": created_at,
        "new_idea": idea.dict(),
        "similar_cases": [
            {"id": c.id, "title": c.title} for c in similar_cases
        ],
        "questions": [q.dict() for q in questions],
        "feedbacks": [],
    }

    path = LOG_DIR / f"session_{session_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return session_id


def append_feedback(session_id: str, feedback_request: FeedbackRequest) -> int:
    """指定セッションのログファイルにフィードバックを追記する。

    セッションが存在しない場合は FileNotFoundError を送出する。
    """

    _ensure_log_dir()
    path = LOG_DIR / f"session_{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"session log not found: {session_id}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    feedbacks = data.get("feedbacks") or []
    feedbacks.extend([fb.dict() for fb in feedback_request.feedbacks])
    data["feedbacks"] = feedbacks

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return len(feedback_request.feedbacks)


__all__ = ["create_session_log", "append_feedback"]
