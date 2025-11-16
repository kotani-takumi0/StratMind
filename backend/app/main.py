from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


@app.on_event("startup")
def on_startup() -> None:
    """アプリ起動時に DecisionCase や類似度計算の初期化を行う。"""

    data_path = BASE_DIR / "data" / "decision_case.json"
    cases = loader.load_decision_cases(data_path)
    similarity.initialize_vectorizer(cases)


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

    cases = similarity.search_similar_cases(idea, top_k=5)

    similar_cases: List[SimilarCase] = [
        SimilarCase(
            id=c.id,
            title=c.title,
            status=c.status,
            main_reason=c.main_reason,
            tags=c.tags,
        )
        for c in cases
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

    questions: List[Question] = question_generator.generate_questions(
        request_body.idea,
        selected_cases,
    )

    session_id = logging_service.create_session_log(
        request_body.idea,
        selected_cases,
        questions,
    )

    return GenerateQuestionsResponse(session_id=session_id, questions=questions)


@app.post("/sessions/{session_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(session_id: str, body: FeedbackRequest) -> FeedbackResponse:
    """指定セッションに対するフィードバックを保存する。"""

    try:
        saved_count = logging_service.append_feedback(session_id, body)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    return FeedbackResponse(session_id=session_id, saved_count=saved_count)


# 実行例:
#   (backend ディレクトリで)
#   uvicorn app.main:app --reload
