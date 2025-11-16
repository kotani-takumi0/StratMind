# Prompt 01: backend skeleton（FastAPI）

以下の `00_context.md` をすでに読み込んでいる前提で、  
FastAPI バックエンドの骨格コードを実装してください。

---

## 共通前提（要約）

- プロジェクトは「没案を含む意思決定ケースから“問い”を生成する自己レビュー用ツール」の技術PoC。
- データは `DecisionCase` の配列で `backend/app/data/decision_case.json` に保存。
- ユーザーは新しい企画案 `NewIdea` を入力し、
  - 類似ケース検索
  - 三層の「問い」生成
  - 問いの有用性フィードバックの保存
  を行う。

詳細仕様・概念は 00_context.md に従ってください。

---

## 今回あなたにやってほしいこと

次の3ファイルを実装してください：

1. `backend/app/models.py`
2. `backend/app/config.py`（簡易版）
3. `backend/app/main.py`

最低限「サーバを起動して叩ける状態」まで持っていく骨格が目的です。  
実際の類似検索や問い生成の中身は `services/` 側の責務とし、ここでは呼び出しだけにします。

### 1. `backend/app/models.py`

Pydantic v1 系を前提として、以下のモデルを定義してください。

- `DecisionCase`
  - 00_context.md の「6.1 第一層：PoCで必須のカラム」をベースにする
  - フィールド（型とOptional）は例：
    - `id: str`
    - `project_id: Optional[str] = None`
    - `title: str`
    - `summary: str`
    - `status: str`  # "adopted" | "rejected" | "pending"
    - `main_reason: str`
    - `tags: List[str] = []`
    - `decision_date: Optional[str] = None`
    - `decision_level: Optional[str] = None`
    - `source: Optional[str] = None`

- `NewIdea`
  - ユーザーが入力する新規企画案
  - フィールド：
    - `title: str`
    - `summary: str`
    - `tags: List[str] = []`

- `Question`
  - 生成される問い
  - フィールド：
    - `id: str`
    - `text: str`
    - `layer: int`  # 1, 2, 3 のいずれか
    - `source_case_ids: List[str] = []`

- `QuestionFeedback`
  - 問いに対するユーザー評価（1問分）
  - フィールド：
    - `question_id: str`
    - `helpful_score: int`  # 1〜5
    - `modified_idea: bool`
    - `comment: Optional[str] = None`

- `SimilarCase`
  - フロントに返すときの軽量版 DecisionCase
  - フィールド：
    - `id: str`
    - `title: str`
    - `status: str`
    - `main_reason: str`
    - `tags: List[str] = []`

- APIレスポンス用モデル

  - `SearchCasesResponse`
    - `similar_cases: List[SimilarCase]`

  - `GenerateQuestionsRequest`
    - `idea: NewIdea`
    - `similar_case_ids: List[str]`

  - `GenerateQuestionsResponse`
    - `session_id: str`
    - `questions: List[Question]`

  - `FeedbackRequest`
    - `feedbacks: List[QuestionFeedback]`

  - `FeedbackResponse`
    - `session_id: str`
    - `saved_count: int`

`from __future__ import annotations` と `typing` モジュールを適切に使い、  
全モデルに型ヒントを付けてください。

### 2. `backend/app/config.py`

シンプルで構いません。PoC 用の設定クラスを作ってください。

- 目的：
  - 将来、LLM APIキーや設定値をここに寄せるための「箱」を作る
- 実装例：

  - `Settings` クラス（`pydantic.BaseSettings` を継承）
    - フィールド：
      - `APP_NAME: str = "Decision Question Helper"`
      - `CORS_ORIGINS: List[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]` など
  - `get_settings()` 関数でシングルトン的に返す

`.env` はまだ使わなくてよいが、`BaseSettings` ベースで作っておいてください。

### 3. `backend/app/main.py`

FastAPI アプリ本体を実装してください。

#### 3-1. 基本セットアップ

- やること：
  - `FastAPI` インスタンスの生成
  - CORS ミドルウェア設定
  - テンプレート（Jinja2Templates）の設定
  - 静的ファイル（`/static`）のマウント
  - アプリ起動時に `services/loader.py` を呼び出して DecisionCase をロード
  - `similarity` や `question_generator` の初期化関数がある前提で呼び出す

- インポート想定：

  ```python
  from fastapi import FastAPI, Depends, HTTPException
  from fastapi.middleware.cors import CORSMiddleware
  from fastapi.staticfiles import StaticFiles
  from fastapi.templating import Jinja2Templates
  from fastapi import Request

  from .config import get_settings
  from .models import (
      NewIdea, SearchCasesResponse,
      GenerateQuestionsRequest, GenerateQuestionsResponse,
      FeedbackRequest, FeedbackResponse,
      SimilarCase, Question
  )
  from .services import loader, similarity, question_generator, logging_service

#### 3-2. ルーティング

次のエンドポイントを実装してください。

GET /health

返り値例：

{ "status": "ok" }


GET /

templates/index.html を返す

引数に request: Request を取り、templates.TemplateResponse を返す

POST /cases/search

入力: NewIdea

処理フロー：

loader.get_decision_cases() から全ケースを取得

similarity.search_similar_cases(idea: NewIdea, cases: list[DecisionCase], top_k: int = 5) を呼び出す想定

戻り値の DecisionCase のリストを SimilarCase にマッピング

出力: SearchCasesResponse

エラー処理:

ケースが0件の場合は空配列を返す（500にしない）

POST /questions/generate

入力: GenerateQuestionsRequest

idea: NewIdea

similar_case_ids: List[str]

処理フロー：

loader.get_decision_cases() から全ケースを取得し、similar_case_ids に対応するケースだけ抽出

question_generator.generate_questions(idea, similar_cases) を呼ぶ

logging_service.create_session_log(idea, similar_cases, questions) を呼び出し、session_id を取得

出力: GenerateQuestionsResponse

session_id

questions

エラー処理：

similar_case_ids に存在しないIDが含まれていても、該当分をスキップして続行する（PoCなので）

POST /sessions/{session_id}/feedback

パスパラメータ: session_id: str

入力: FeedbackRequest

処理フロー：

logging_service.append_feedback(session_id, feedbacks) を呼び出し

保存した件数（len(feedbacks)）を返す

出力: FeedbackResponse

session_id

saved_count

エラー処理：

対象のセッションファイルが存在しない場合 404 を返す

#### 3-3. CORS とアプリ起動

CORS：

config.get_settings().CORS_ORIGINS を使って設定

allow_credentials=True, allow_methods=["*"], allow_headers=["*"]

アプリ起動方法をコメントで記載してください：

# 実行例:
# uvicorn app.main:app --reload

実装上の注意

責務分離

類似度計算の中身は services/similarity.py に隠蔽し、main.py では呼び出すだけにする

問い生成ロジックも services/question_generator.py に隠蔽し、ここではI/Oとルーティングのみ

ログ保存は services/logging_service.py に任せる

型ヒント

全関数・モデルに型ヒントを付与すること

from __future__ import annotations を冒頭に置くと依存関係が書きやすい

PoC前提

エラー時のメッセージはシンプルで構わない

ロギングは print ベースでもよいが、logging モジュールを使う場合は最低限の設定で良い

上記仕様に従い、

backend/app/models.py

backend/app/config.py

backend/app/main.py

の 完全な実装コード を出力してください。