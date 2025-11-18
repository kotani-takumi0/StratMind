結論から言うと、今まで話してたのはほぼ `similarity.py` だけです。
ちゃんと動かすには少なくともこの3つが要ります：

* `loader.py`：JSONからDecisionCaseを読むやつ
* `embeddings.py`：OpenAIの埋め込みAPIを叩くやつ
* `similarity.py`：埋め込みベクトルを使って類似ケースを返すやつ

＋それを支える `.env` と `config`。

ここで全部まとめて「**あなたがやること**」と「**LLMに投げるプロンプト**」を整理します。

---

## 0. まず、あなたが手動でやること

### 0-1. 必要パッケージのインストール

```bash
pip install fastapi uvicorn "openai>=1.0.0" python-dotenv numpy
```

> 新しい OpenAI SDK は `from openai import OpenAI` + `client = OpenAI()` で使います。([OpenAI Platform][1])

### 0-2. `.env` を作る

プロジェクトルート（`backend/` と同じ階層）に `.env` ファイルを作成：

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
```

※ `OPENAI_BASE_URL` はデフォルトなら省略可。
※ `.gitignore` に `.env` を必ず入れておくこと（GitHubに上がったら終わり）。

### 0-3. ディレクトリ前提

ここではこう置いている前提でプロンプトを書きます：

```bash
backend/
  app/
    models.py
    services/
      loader.py
      embeddings.py
      similarity.py
    data/
      decision_case.json
```

---

## 1. loader.py 用プロンプト（4-1）

`decision_case.json` を読み込んで `list[DecisionCase]` に変換するやつです。

### Prompt 4-1: `backend/app/services/loader.py` 生成用

> あなたは Python/FastAPI アプリの一部として、JSON ファイルから `DecisionCase` の一覧を読み込む `loader.py` を実装するエンジニアです。
>
> 前提：
>
> * `app.models` に Pydantic モデル `DecisionCase` が定義されている。
> * JSON ファイルは `backend/app/data/decision_case.json` にあり、内容は `DecisionCase` の配列。
>
> 目的：
>
> * アプリ起動時に一度だけ JSON を読み込み、`DecisionCase` のリストとして保持する。
> * 他のモジュールからは `get_decision_cases()` で読み取り専用でアクセスできるようにする。
>
> 実装要件：
>
> ```python
> # loader.py に実装したいインターフェース
> from pathlib import Path
> from typing import List
> from app.models import DecisionCase
>
> _CASES: list[DecisionCase] | None = None
>
> def load_decision_cases(path: Path | None = None) -> list[DecisionCase]:
>     """
>     JSON ファイルから DecisionCase の一覧を読み込んでキャッシュする。
>     - path が None の場合は、現在ファイルからの相対パスで
>       ../data/decision_case.json をデフォルトとする。
>     - すでに読み込まれている場合は再読み込みせず、キャッシュを返す。
>     """
>
> def get_decision_cases() -> list[DecisionCase]:
>     """
>     キャッシュされた DecisionCase の一覧を返す。
>     - 未ロードの場合は load_decision_cases() を内部で呼び出す。
>     """
> ```
>
> 実装詳細：
>
> * `Path(__file__).resolve()` から辿って `data/decision_case.json` へのパスを組み立てる。
> * JSON は標準ライブラリ `json` で読み込んでから、`DecisionCase` の list に変換する。
> * 例外処理は最低限で構わないが、ファイルが見つからない場合は `FileNotFoundError` をそのまま投げてよい。
>
> 上記要件を満たす `loader.py` の完全なコードを書いてください。

---

## 2. embeddings.py 用プロンプト（4-2）

OpenAI APIキーを使って埋め込みを取る部分。
ここで `.env` を読む / `OpenAI` クライアントを作る。

### Prompt 4-2: `backend/app/services/embeddings.py` 生成用

> あなたは Python アプリの一部として、OpenAI の埋め込み API を叩く `embeddings.py` を実装するエンジニアです。
>
> 前提：
>
> * ライブラリ `openai>=1.0.0` と `python-dotenv` はインストール済み。
> * `.env` ファイルに `OPENAI_API_KEY` が定義されている。
>
> 目的：
>
> * テキストのリストを受け取り、`text-embedding-3-small` で埋め込みを取得し、`np.ndarray` として返すユーティリティ関数 `embed_texts` を実装する。
>
> 実装要件：
>
> ```python
> # embeddings.py に実装したいインターフェース
> from typing import List
> import numpy as np
>
> def embed_texts(texts: list[str]) -> np.ndarray:
>     """
>     与えられたテキスト群に対して OpenAI の埋め込みを計算し、
>     shape = (len(texts), D) の numpy.ndarray を返す。
>     - モデル: text-embedding-3-small
>     - .env の OPENAI_API_KEY を利用する
>     """
> ```
>
> 実装詳細：
>
> * モジュールロード時に `.env` を読み込む：
>
>   ```python
>   from dotenv import load_dotenv
>   load_dotenv()
>   ```
>
> * OpenAI クライアントは新しい SDK を使う：
>
>   ```python
>   from openai import OpenAI
>   client = OpenAI()
>   ```
>
> * 埋め込み呼び出しは次のように行う：
>
>   ```python
>   res = client.embeddings.create(
>       model="text-embedding-3-small",
>       input=texts,
>   )
>   vectors = [item.embedding for item in res.data]
>   arr = np.array(vectors, dtype="float32")
>   ```
>
> * `texts` が空リストの場合は、長さ0の `(0, 0)` ndarray を返すようにする。
>
> * エラー処理は PoC のため最小限でよく、OpenAI の例外はそのまま上位に投げて構わない。
>
> 上記要件を満たす `embeddings.py` の完全なコードを書いてください。

---

## 3. similarity.py 用プロンプト（4-3・改訂）

さっき話した「1ベクトル版 `analyze_similarity`」を前提にしたやつを、`loader.py` と `embeddings.py` 前提で書き直します。

### Prompt 4-3: `backend/app/services/similarity.py` 生成用

> あなたは Python/FastAPI アプリの一部として、OpenAI 埋め込みを用いた類似度検索サービス `similarity.py` を実装するエンジニアです。
>
> 前提：
>
> * `app.models` に Pydantic モデル `DecisionCase`, `NewIdea` が定義されている。
> * `app.services.loader` に `get_decision_cases()` がある。
> * `app.services.embeddings` に `embed_texts(texts: list[str]) -> np.ndarray` がある。
> * ユーティリティ関数 `normalize_rows(vecs: np.ndarray) -> np.ndarray` がどこかにあり import できる（既存プロジェクトと同じ仕様）。
>
> 目的：
>
> * アプリ起動時に DecisionCase をすべて読み込み、埋め込みベクトル行列を作って正規化してキャッシュする。
> * 新しい `NewIdea` から埋め込みを1本計算し、コサイン類似度で TopK 件の類似ケースを返す。
> * 類似度計算部分は、既存の `analyze_similarity` の設計（正規化＋内積＋`argpartition`）を踏襲する。
>
> 実装要件：
>
> ```python
> from typing import List
> import numpy as np
> from pydantic import BaseModel
> from app.models import DecisionCase, NewIdea
> from app.services.loader import get_decision_cases
> from app.services.embeddings import embed_texts
> from app.services.utils import normalize_rows  # ※ 実際の場所に合わせて修正してよい
>
> CASES: list[DecisionCase] | None = None
> X_n: np.ndarray | None = None  # shape (N, D), L2 正規化済
>
> class ScoredDecisionCase(BaseModel):
>     case: DecisionCase
>     similarity: float
>
> def build_case_text(case: DecisionCase) -> str:
>     ...
>
> def build_query_text(new_idea: NewIdea) -> str:
>     ...
>
> def initialize_similarity() -> None:
>     ...
>
> def analyze_similarity_cases(
>     query_vec: np.ndarray,
>     *,
>     topk: int = 5,
> ) -> list[tuple[int, float]]:
>     ...
>
> def search_similar_cases(new_idea: NewIdea, top_k: int = 5) -> List[ScoredDecisionCase]:
>     ...
> ```
>
> 詳細仕様：
>
> 1. `build_case_text(case)`
>
>    * 以下を単純に改行区切りで連結した文字列でよい：
>
>      * `case.title`
>      * `case.summary`
>      * `"Tags: " + ", ".join(case.tags or [])`
>      * `"Status: " + case.status`
>      * `"Main reason: " + (case.main_reason or "")`
> 2. `build_query_text(new_idea)`
>
>    * 以下を改行区切りで連結：
>
>      * `new_idea.title`
>      * `new_idea.summary`
>      * `"Tags: " + ", ".join(new_idea.tags or [])`
> 3. `initialize_similarity()`
>
>    * `CASES = get_decision_cases()` でケース一覧を取得
>    * `texts = [build_case_text(c) for c in CASES]`
>    * `vecs = embed_texts(texts)` で埋め込み行列を取得
>    * `X_n = normalize_rows(vecs)` で正規化し、グローバル変数に代入
> 4. `analyze_similarity_cases(query_vec, topk)`
>
>    * `query_vec` は shape `(1, D)` を想定
>    * 関数内で `Q_n = normalize_rows(query_vec)` する
>    * `scores = (Q_n @ X_n.T)[0]` で類似度ベクトルを取る
>    * `topk` が `scores` の長さより大きい場合は自動的に短くする
>    * `np.argpartition` → `np.argsort` で上位 K 件のインデックスを取り出し、
>      `[(index, float(scores[index])), ...]` をスコア降順で返す
> 5. `search_similar_cases(new_idea, top_k)`
>
>    * `CASES` / `X_n` が `None` の場合は `Exception("initialize_similarity() が実行されていません。")` を投げる
>    * `query_text = build_query_text(new_idea)`
>    * `query_vec = embed_texts([query_text])`
>    * `idx_scores = analyze_similarity_cases(query_vec, topk=top_k)`
>    * 各 `(idx, score)` から `ScoredDecisionCase(case=CASES[idx], similarity=score)` を作り、リストで返す
> 6. 型ヒント：
>
>    * Python 3.10 以降の新記法（`list[int]` など）で統一すること。
>
> 上記要件をすべて満たす `similarity.py` の完全なコードを書いてください。

---

## 4. 「APIキーまわり」であなたがやることのまとめ

* `.env` に `OPENAI_API_KEY=...` を書く（絶対にGitに上げない）
* `embeddings.py` で `load_dotenv()` + `OpenAI()` クライアントを作る
* ローカルで動かすときは `.env` が参照されるように、`backend/` 直下で `uvicorn app.main:app --reload` する or カレントディレクトリを整える


[1]: https://platform.openai.com/docs/models/text-embedding-3-small?utm_source=chatgpt.com "Model - OpenAI API"
