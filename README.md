# StratMind

StratMindは、過去の意思決定事例に基づき、AIが新規企画への「問い」を自動生成することで、アイデアのレビューを加速させる意思決定支援ツールです。

---
## 環境
- Python3.10以降
- OpenAI APIキー（もしくはGemini APIに対応(予定)）

## 環境設定と実行
1. ライブラリのインストール
   ```[bash]
   pip install -r requirements.txt
   ```
   
2. **環境変数の設定**  
   環境変数`OPENAI_API_KEY`にAPIキーをセット 
   （Geminiの場合は`GEMINI_API_KEY`）
   
4. 実行・サーバー起動
   ```[bash]
   uvicorn app.main:app --reload
   ```


### 主な使用技術
**バックエンド :**
- [FastAPI](https://fastapi.tiangolo.com/) - Webフレームワーク
- [Uvicorn](https://www.uvicorn.org/) - ASGIサーバー
- [Pydantic](https://docs.pydantic.dev/) - データ検証
- [OpenAI API](https://platform.openai.com/)




# StratMind

新規事業の企画ドラフトを「問い」によってブラッシュアップする、自己レビュー用ツールの技術 PoC です。  
過去の意思決定ケース（採用案・没案を含む）から学びを抽出し、企画担当者にとって有用な問いを提示することを目的としています。

---

## コンセプト

- 過去の「採用された案」「惜しい没案」を DecisionCase として構造化して蓄積
- 新しい企画案（NewIdea）を入力すると、過去の類似ケースを検索
- 類似ケースの評価理由をもとに 3〜7 個の問い（Question）を生成
- ユーザーは問いを読みながら企画書を自己レビューし、必要に応じて修正
- 各問いの有用性・行動変化をログとして保存し、問いの質を検証

---

## 技術スタック

- 言語: Python 3.10+
- Web フレームワーク: FastAPI
- テンプレート: Jinja2
- フロントエンド: HTML + バニラ JavaScript + CSS
- 外部 API:
  - OpenAI Embeddings API（`text-embedding-3-small`）
  - OpenAI Responses API（`gpt-4.1-mini`）
- 依存パッケージ: `requirements.txt` を参照

---

## ディレクトリ構成（主要）

```text
StratMind/
  README.md                 # このファイル
  requirements.txt          # Python 依存パッケージ
  .env                      # OpenAI API キー（Git 管理対象外）

  backend/
    app/
      main.py               # FastAPI エントリポイント
      models.py             # Pydantic モデル定義
      config.py             # 設定クラス（CORS など）
      services/
        loader.py           # decision_case.json ロード＆キャッシュ
        embeddings.py       # OpenAI 埋め込みラッパ
        similarity.py       # 類似ケース検索（埋め込み＋コサイン類似度）
        question_generator.py  # LLM を用いた問い生成ロジック
        logging_service.py     # セッションログ・フィードバック保存
        utils.py              # ベクトル正規化などユーティリティ
      templates/
        index.html          # メイン画面（エディタ＋レビュー UI）
      statics/
        css/style.css       # 画面レイアウト・スタイル
        js/app.js           # フロントエンドロジック（現状はダミーデータ表示）
      logs/
        logs/               # セッションログ JSON（自動生成）

    data/
      decision_case.json    # 過去の意思決定ケースデータ
```

---

## セットアップ

### 1. Python 環境の準備

```bash
# プロジェクトルートで
python -m venv .venv
source .venv/bin/activate  # Windows の場合は .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. OpenAI API キーの設定

ルートディレクトリに `.env` を配置し、環境変数を設定します。

```env
OPENAI_API_KEY=あなたのAPIキー
# 必要に応じて
# OPENAI_BASE_URL=https://api.openai.com/v1
```

※ `.env` は `.gitignore` に含まれているため、キーはリポジトリにコミットされません。  
※ `backend/app/services/embeddings.py` と `backend/app/services/question_generator.py` がこのキーを利用します。

### 3. データファイルの確認

`backend/data/decision_case.json` に DecisionCase の配列が保存されています。  
スキーマは `backend/app/models.py` の `DecisionCase` モデルに準拠します。

---

## 起動方法

FastAPI アプリケーションは `backend` ディレクトリから起動します。

```bash
cd backend

# 開発サーバ起動
uvicorn app.main:app --reload
```

- デフォルト URL: `http://127.0.0.1:8000/`
- ヘルスチェック: `GET /health`  
  → `{"status": "ok"}` が返れば起動成功

---

## 画面の使い方（現状）

1. ブラウザで `http://127.0.0.1:8000/` を開く
2. 左ペイン「企画エディタ」
   - `企画タイトル`
   - `企画書本文`
   を自由に記入
3. 右上の「AIレビューを更新する」ボタンを押す
   - 現状のフロントエンド (`backend/statics/js/app.js`) では **ダミーデータ** を使って
     - Review Questions（問いカード）
     - Reference Cases（参考ケース）
     を描画します（バックエンド API への実通信はまだ行っていません）
4. 問いカードの「企画書に反映する」ボタンを押すと、左ペインのテキストエリア末尾にメモ用テンプレートが追記されます
5. チェックボックスで「検討済み」の状態にしながら、企画書を育てていく想定です

> バックエンド側には実際の類似検索＋問い生成ロジック（OpenAI 利用）が実装済みで、  
> 将来的にはフロントエンドから下記 API を叩いてリアルなレビューを実行する形に拡張できます。

---

## 主な API エンドポイント

### フロントエンド統合用（/api/...）

- `POST /api/review_sessions`
  - 入力: `ReviewSessionCreateRequest`
    - `new_idea`: フロントエンドフォームの構造（タイトル＋複数フィールド）
    - `tags`: 文字列配列
  - 処理:
    - フォーム入力を 1 本の `NewIdea.summary` に統合
    - 類似 DecisionCase を検索（OpenAI 埋め込み）
    - 類似ケース群を元に問いを LLM で生成
    - セッションログ作成
  - 出力: `ReviewSessionCreateResponse`
    - `session_id`
    - `new_idea`
    - `questions`（生成された問いの配列）
    - `similar_cases`（参考ケース一覧）

- `POST /api/review_sessions/{session_id}/feedback`
  - 入力: `ReviewSessionFeedbackRequest`
    - `feedbacks`: 各問いに対する
      - `question_id`
      - `usefulness_score`（1〜5 / null）
      - `applied`（問いをきっかけに修正したか）
      - `note`（任意メモ）
  - 処理:
    - 既存の `QuestionFeedback` モデルに変換し、該当セッションログに保存
  - 出力:
    - `{ "ok": true }`（成功時）

- `GET /api/decision_cases/{case_id}`
  - 入力: パスパラメータ `case_id`
  - 出力: 該当 `DecisionCase` の詳細（見つからない場合は 404）

### 内部向け API（類似検索＋問い生成）

- `POST /cases/search`
  - 入力: `NewIdea`
  - 出力: `SearchCasesResponse`（`SimilarCase` の配列）

- `POST /questions/generate`
  - 入力: `GenerateQuestionsRequest`
    - `idea`: `NewIdea`
    - `similar_case_ids`: 類似ケース ID の配列
  - 出力: `GenerateQuestionsResponse`
    - `session_id`
    - `questions`

- `POST /sessions/{session_id}/feedback`
  - 入力: `FeedbackRequest`（`QuestionFeedback` 配列）
  - 出力: `FeedbackResponse`（保存件数など）

---

## ログと評価データ

- ログディレクトリ: `backend/app/logs/logs/`
- ファイル名: `session_{session_id}.json`
- 内容:
  - `session_id`, `created_at`
  - `new_idea`（当時の企画案）
  - `questions`（提示した問い）
  - `feedbacks`（各問いへの有用性スコア・修正有無・コメント）
  - `session_evaluation`（体験全体に対する主観評価用フィールド）
  - `interaction_logs`（将来のクリックログなど用フィールド）
  - `session_times`（開始/終了時刻）

これらは、問いの質や体験価値を振り返るための評価指標設計（`backend/prompts/00_context.md` の 8 章）に対応しています。

---

## トラブルシューティング

過去に発生した代表的なエラーと対応内容は `ERROR_LOG.md` にまとめています。  
FastAPI 起動時のエラーなどに遭遇した場合は、まずそちらを参照してください。

---

## 今後の拡張の方向性（メモ）

- フロントエンドから `POST /api/review_sessions` / `POST /api/review_sessions/{session_id}/feedback` に接続し、ダミーデータではなく実際の LLM ベースレビューを実行する
- DecisionCase スキーマの拡張（オプションレベルの構造化、評価軸のラベリングなど）
- 組織別の「よくある NG パターン」から問いテンプレートを学習し、Layer2 の精度を向上
- セッション評価 (`session_evaluation`) を UI 上で入力できるフォームの追加

---

この README の内容を `README.md` に保存しました。プロジェクトの概要・セットアップ・起動方法・API を把握するためのベースとして利用できます。
