from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .config import get_settings
from .models import (
    DecisionCase,
    FeedbackRequest,
    FeedbackResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    NewIdea,
    Question,
    SearchCasesResponse,
    SimilarCase,
)
from .services import loader, logging_service, question_generator, similarity


app = FastAPI(title=get_settings().APP_NAME)

settings = get_settings()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# テンプレートと静的ファイル
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "templates"))
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR.parent / "statics")),
    name="static",
)


class NewIdeaForm(BaseModel):
    """フロントエンドのフォーム構造に対応する NewIdea 入力用モデル。"""

    title: str
    purpose: str
    target: str
    value: str
    model: str
    memo: str
    content: str


class ReviewSessionCreateRequest(BaseModel):
    """POST /api/review_sessions のリクエストボディ。"""

    new_idea: NewIdeaForm
    is_demo: bool
    tags: List[str] = []


class ReviewSessionCreateResponse(BaseModel):
    """POST /api/review_sessions のレスポンスボディ。"""

    session_id: str
    new_idea: NewIdea
    questions: List[Question]
    similar_cases: List[DecisionCase]


class QuestionFeedbackV2(BaseModel):
    """フロントエンドのフィードバック形式に対応したモデル。"""

    question_id: str
    usefulness_score: Optional[int] = None  # 1〜5（未選択は null）
    applied: bool
    note: str = ""


class ReviewSessionFeedbackRequest(BaseModel):
    """POST /api/review_sessions/{session_id}/feedback のリクエストボディ。"""

    feedbacks: List[QuestionFeedbackV2]


@app.on_event("startup")
def on_startup() -> None:
    """アプリ起動時に DecisionCase や類似度計算の初期化を行う。"""

    # デフォルトパス (services/loader.py からの相対パス ../data/decision_case.json) を利用してロード
    loader.load_decision_cases()
    similarity.initialize_similarity()


@app.get("/health")
def health_check() -> dict:
    """疎通確認用エンドポイント。"""

    return {"status": "ok"}


@app.get("/")
def index(request: Request) -> object:
    """トップページとしてテンプレートを返す。"""

    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/cases/search", response_model=SearchCasesResponse)
def search_cases(idea: NewIdea) -> SearchCasesResponse:
    """NewIdea を受け取り、類似する DecisionCase を上位5件返す。"""

    scored_cases = similarity.search_similar_cases(idea, top_k=5)

    similar_cases: List[SimilarCase] = [
        SimilarCase(
            id=sc.case.id,
            title=sc.case.title,
            status=sc.case.status,
            main_reason=sc.case.main_reason,
            tags=sc.case.tags,
        )
        for sc in scored_cases
    ]

    return SearchCasesResponse(similar_cases=similar_cases)


@app.post("/questions/generate", response_model=GenerateQuestionsResponse)
def generate_questions(request_body: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    """NewIdea と選択された類似ケースから問いを生成し、セッションログを作成する。"""

    all_cases = loader.get_decision_cases()
    # similar_case_ids に存在しないIDが含まれていても、該当分をスキップ
    selected_cases: List[DecisionCase] = [
        c for c in all_cases if c.id in set(request_body.similar_case_ids)
    ]

    questions, meta = question_generator.generate_questions(
        request_body.idea, selected_cases
    )

    session_id = logging_service.create_session_log(request_body.idea, questions)

    return GenerateQuestionsResponse(session_id=session_id, questions=questions)


@app.post("/sessions/{session_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(session_id: str, body: FeedbackRequest) -> FeedbackResponse:
    """指定セッションに対するフィードバックを保存する。"""

    try:
        logging_service.append_feedback(session_id, body.feedbacks)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    return FeedbackResponse(session_id=session_id, saved_count=len(body.feedbacks))


@app.post("/api/review_sessions", response_model=ReviewSessionCreateResponse)
def create_review_session(payload: ReviewSessionCreateRequest) -> ReviewSessionCreateResponse:
    """フロントエンド用の自己レビューセッション作成エンドポイント。

    - NewIdeaForm を内部の NewIdea に変換
    - 類似ケース検索
    - 問い生成
    - セッションログ作成
    をまとめて実行し、1つのレスポンスとして返す。
    """

    form = payload.new_idea

    # NewIdea.summary を複数フィールドから組み立てる
    summary_parts = [
        f"【目的・課題】\n{form.purpose}",
        f"【対象ユーザー】\n{form.target}",
        f"【提供価値・ユースケース】\n{form.value}",
        f"【収益モデル・ビジネスモデル】\n{form.model}",
        f"【その他メモ・前提】\n{form.memo}",
    ]
    summary = "\n\n".join(summary_parts)

    new_idea = NewIdea(
        title=form.title,
        summary=summary,
        tags=payload.tags or [],
    )

    # 類似ケース検索
    scored_cases = similarity.search_similar_cases(new_idea, top_k=5)
    similar_cases: List[DecisionCase] = [sc.case for sc in scored_cases]

    # デモ実行時
    if payload.is_demo:
        questions, _ = question_generator.generate_demo_questions()
    else:
        # 問い生成（上位類似ケースを渡す）
        questions, meta = question_generator.generate_questions(new_idea, similar_cases)

    # セッションログ作成
    session_id = logging_service.create_session_log(new_idea, questions)

    print(ReviewSessionCreateResponse(
        session_id=session_id,
        new_idea=new_idea,
        questions=questions,
        similar_cases=similar_cases,
    ))

    return ReviewSessionCreateResponse(
        session_id=session_id,
        new_idea=new_idea,
        questions=questions,
        similar_cases=similar_cases,
    )


@app.post("/api/review_sessions/{session_id}/feedback")
def create_review_session_feedback(
    session_id: str,
    body: ReviewSessionFeedbackRequest,
) -> dict:
    """フロントエンド用のフィードバック保存エンドポイント。

    QuestionFeedbackV2 を内部の QuestionFeedback モデルに変換して保存する。
    """

    from .models import QuestionFeedback  # 循環 import を避けるためローカル import

    # V2 形式 → 既存の QuestionFeedback 形式に変換
    converted: List[QuestionFeedback] = []
    for fb in body.feedbacks:
        converted.append(
            QuestionFeedback(
                question_id=fb.question_id,
                helpful_score=fb.usefulness_score or 0,
                modified_idea=fb.applied,
                comment=fb.note or None,
            )
        )

    try:
        logging_service.append_feedback(session_id, converted)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"ok": True}


@app.get("/api/decision_cases/{case_id}")
def get_decision_case(case_id: str) -> DecisionCase:
    """ID で指定された DecisionCase の詳細を返すエンドポイント。"""

    cases = loader.get_decision_cases()
    for c in cases:
        if c.id == case_id:
            return c

    raise HTTPException(status_code=404, detail="DecisionCase not found")

# @app.post("api/reveiew_sessions")
# def 


# 実行例:
#   (backend ディレクトリで)
#   uvicorn app.main:app --reload
