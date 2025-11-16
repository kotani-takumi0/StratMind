from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DecisionCase(BaseModel):
    """意思決定ケースの最小スキーマ (00_context.md / 01_backend_setup.md に準拠)。"""

    id: str
    project_id: Optional[str] = None
    title: str
    summary: str
    status: str  # "adopted" | "rejected" | "pending"
    main_reason: str
    tags: List[str] = Field(default_factory=list)
    decision_date: Optional[str] = None
    decision_level: Optional[str] = None
    source: Optional[str] = None


class NewIdea(BaseModel):
    """ユーザーが入力する新規企画案。"""

    title: str
    summary: str
    tags: List[str] = Field(default_factory=list)


class Question(BaseModel):
    """生成される問い。"""

    id: str
    text: str
    layer: int  # 1, 2, 3 のいずれか
    source_case_ids: List[str] = Field(default_factory=list)


class QuestionFeedback(BaseModel):
    """問いに対するユーザー評価（1問分）。"""

    question_id: str
    helpful_score: int  # 1〜5
    modified_idea: bool
    comment: Optional[str] = None


class SimilarCase(BaseModel):
    """フロントに返す軽量版 DecisionCase。"""

    id: str
    title: str
    status: str
    main_reason: str
    tags: List[str] = Field(default_factory=list)


class SearchCasesResponse(BaseModel):
    similar_cases: List[SimilarCase]


class GenerateQuestionsRequest(BaseModel):
    idea: NewIdea
    similar_case_ids: List[str]


class GenerateQuestionsResponse(BaseModel):
    session_id: str
    questions: List[Question]


class FeedbackRequest(BaseModel):
    feedbacks: List[QuestionFeedback]


class FeedbackResponse(BaseModel):
    session_id: str
    saved_count: int


__all__ = [
    "DecisionCase",
    "NewIdea",
    "Question",
    "QuestionFeedback",
    "SimilarCase",
    "SearchCasesResponse",
    "GenerateQuestionsRequest",
    "GenerateQuestionsResponse",
    "FeedbackRequest",
    "FeedbackResponse",
]
