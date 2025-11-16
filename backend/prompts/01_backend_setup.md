[コンテキストは省略、00_context.md を前提としている]

FastAPI で次の構成のコードを作ってください。

backend/app/main.py

FastAPIアプリ本体

DecisionCase / NewIdea / Question などのPydanticモデルは models.py に定義して import する

起動時に services/loader.py の関数で data/decision_case.json を読み込む

エンドポイント：

GET /health : { "status": "ok" } を返す

POST /cases/search : NewIdea を受け取り、類似ケーストップ5件を返す（中身は services/similarity.py に委譲）

POST /questions/generate : NewIdea と関連するDecisionCase配列を受け取り、3〜7件の Question を返す（中身は services/question_generator.py に委譲）

CORS設定： http://localhost:5500 などフロントのオリジンからのアクセスを許可する

backend/app/models.py

次のPydanticモデルを定義する：

DecisionCase

NewIdea（少なくとも title: str, summary: str, tags: list[str] = []）

Question（id: str, text: str, layer: int（1〜3）, source_case_ids: list[str]）

QuestionFeedback（question_id: str, helpful_score: int (1-5), modified_idea: bool）

backend/app/services/__init__.py は空でよい。

それぞれのファイルの完全なコードを出力してください。
実行例：uvicorn app.main:app --reload で起動できる構成にしてください。