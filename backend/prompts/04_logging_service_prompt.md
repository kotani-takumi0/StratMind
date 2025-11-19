# ファイル: backend/app/services/logging_service.py

あなたは Python / FastAPI プロジェクトで堅牢なサービスクラスを書くバックエンドエンジニアです。

前提：
- このプロジェクトの全体設計は `00_context.md` に書かれている。
- 特に「評価指標」「ログ設計」に関するセクション（2-1, 2-2, 3-1, 3-2, 3-3, 4-1, 4-2）は、自己レビューセッションのログスキーマの設計方針を示している。
- `NewIdea`, `Question`, `QuestionFeedback` は既に Pydantic モデルとして定義済みであり、`logging_service.py` からインポートできる前提とする。
  - ここでは例として `from backend.app.schemas.review import NewIdea, Question, QuestionFeedback` と書いてよい（実際の import パスはコメントで「適宜調整」と明記すること）。

## このファイルの目的

`backend/app/services/logging_service.py` に、  
「1回の自己レビューセッションごとに JSON ファイルとしてログを保存するサービス」を実装する。

1セッション分のログは 1 ファイルにまとめて保存し、  
PoC で定義した評価指標と 1:1 で対応づく形の JSON スキーマを持つ。

## ログスキーマ

1 セッションあたり、次のような JSON を保存する。


{
  "session_id": "str (UUID)",
  "created_at": "ISO8601 string (UTC推奨)",
  "new_idea": { /* NewIdea を dict にしたもの */ },
  "questions": [ /* Question を dict にしたものの配列 */ ],

  // 評価指標A: 問いの有用性 (2-1, 2-2)
  "feedbacks": [
    /* QuestionFeedback を dict にしたものの配列 */
  ],

  // 評価指標B: 体験としての価値 (3-1, 3-2, 3-3)
  // ※ QuestionFeedback 側ではなくセッション全体の評価として保持する場合を想定。
  "session_evaluation": {
    // 3-1: 体験の有効性 (5 段階)
    // 「このツールを使った自己レビューは、何も使わない場合と比べて役立ちましたか？」
    "experience_score": "int | null",

    // 3-2: 再利用意向 (0〜10)
    "reuse_intent_score": "int | null",

    // 3-3: 質の向上感 (5 段階)
    "perceived_quality_gain_score": "int | null"
  },

  // ログからとるサブ指標 (4-1, 4-2)
  "interaction_logs": [
    {
      "question_id": "str",
      "clicked_detail": "bool",
      "note_written": "bool",
      "checked_done": "bool"
    }
  ],
  "session_times": {
    "started_at": "ISO8601 string | null",
    "ended_at": "ISO8601 string | null"
  }
}
注意：

NewIdea, Question, QuestionFeedback の中身は 00_context.md / 既存スキーマに従う。
logging_service 側では中身を解釈せず、model_dump()（Pydantic v2）または dict() でシリアライズすることに集中する。

session_evaluation, interaction_logs, session_times は、最初のセッション作成時点では空 or null で構わない。

後から他のサービスで埋める想定でも良い。その場合でも、キー自体は必ず JSON に含める（スキーマを安定させるため）。

## ファイル保存要件

ルート：backend/app/logs/

この配下に logs/ ディレクトリを作成し、そこに保存する。

パス：backend/app/logs/session_{session_id}.json

ディレクトリが存在しなければ自動で作成する（os.makedirs(..., exist_ok=True)）。

ファイル I/O は同期でよい（通常の open / json モジュールを使用）。

エンコーディングは UTF-8。

例外が発生した場合は、そのまま例外を投げて呼び出し側でハンドリングできるようにする（ここでは握りつぶさない）。

### 実装する関数

次の 2 つのトップレベル関数を実装する。

#### 1. create_session_log(new_idea: NewIdea, questions: list[Question]) -> str

新しい session_id（UUID v4）を発行する。

created_at を現在時刻（UTC）で生成し、ISO8601 文字列にする。

上記スキーマに従って、初期 JSON オブジェクトを構築する：

new_idea: new_idea.model_dump() の結果

questions: 各 q.model_dump() の配列

feedbacks: 空配列 []

session_evaluation: 全て null（または None を JSON で表現したもの）

interaction_logs: 空配列 []

session_times: "started_at" に created_at、"ended_at" に null

backend/app/logs/logs/session_{session_id}.json に書き出す。

発行した session_id を返す。

#### 2. append_feedback(session_id: str, feedbacks: list[QuestionFeedback]) -> None

対象ファイル：backend/app/logs/logs/session_{session_id}.json

既存の JSON を読み込む。

ファイルが存在しない場合は FileNotFoundError を投げる。

JSON パースに失敗した場合は ValueError を投げる。

feedbacks フィールドを、引数 feedbacks を model_dump() した配列で 上書き する。

既存の他フィールド（new_idea, questions, session_evaluation など）は変更しない。

上書きした内容で JSON ファイル全体を再保存する。

（必要であれば将来の拡張として、session_evaluation や interaction_logs を更新するメソッドを追加で定義できるよう、クラス設計にしておくのも望ましいが、今回の要件では関数ベースでよい。）

### 実装スタイルの要件

標準ライブラリのみ使用（uuid, datetime, pathlib, json, os など）。

型ヒントをすべての公開関数・戻り値に付ける。

パス操作は pathlib.Path を用いて書く。

再利用性のため、内部で使うパス生成ロジックは _get_log_dir() や _get_log_path(session_id: str) のようなプライベート関数に切り出す。

日本語コメントで、どのフィールドが評価指標（2-1, 2-2, 3-1, 3-2, 3-3, 4-1, 4-2）と対応しているかを簡単に添える。

### 出力形式

logging_service.py の完全なコードのみを出力する。

余計な説明文や Markdown は付けず、1つの Python ファイルとしてそのまま保存できる形にする。
