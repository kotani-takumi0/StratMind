[00_context.md 前提]

backend/app/services/loader.py と backend/app/services/similarity.py のコードを書いてください。

前提：

データファイル backend/app/data/decision_case.json には、DecisionCaseの配列がJSONとして保存されている。

スキーマは 00_context.md で説明したものと同じ。

要件：

loader.py

関数 load_decision_cases(path: Path) -> list[DecisionCase] を実装する。

起動時に一度だけJSONを読み込み、DecisionCase モデルのリストとして返す。

将来キャッシュしやすいように、内部的にはモジュールレベルの変数 _CASES に保存しておき、
get_decision_cases() -> list[DecisionCase] で参照できるようにする。

similarity.py

scikit-learn の TfidfVectorizer を使って、summary フィールドをベースに類似度検索を行う。

initialize_vectorizer(cases: list[DecisionCase]) でベクトル化器とコーパスを初期化。

search_similar_cases(new_idea: NewIdea, top_k: int = 5) -> list[DecisionCase] を実装。

new_idea.summary をTF-IDFベクトルに変換し、既存ケースとのコサイン類似度を計算。

類似度が高い順に top_k 件の DecisionCase を返す。

実装上の注意：

ベクトル化器や行列はモジュール内のグローバル変数にキャッシュし、毎回fitしない。

日本語テキストだが、まずは単純にスペース区切り・n-gram無しでよい（高度な形態素解析は不要）。

これら2ファイルの完全なコードを出力してください。