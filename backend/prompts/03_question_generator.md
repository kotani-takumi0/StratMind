# 問い生成サービス（question_generator）の設計

## 1. このモジュールの目的

- 新しい事業案（NewIdea）と、過去の意思決定ケース（DecisionCase）の一覧を入力として受け取り、
  「企画担当者の自己レビューを深くするための問い」を 3〜7 個生成するサービスを設計・実装したい。
- ここでいう「問い」は、Yes/No ではなく、企画者が自分で文章を書いて答えざるを得ないような
  思考を引き出す問いとする。
- 判定やスコアリングは行わない。あくまで「よい問いを出す」のが責務。

このプロンプトでは、`question_generator` モジュールの設計方針・インターフェース・振る舞いを一緒に詰めたい。

---

## 2. question_generator の責務

- 責務：
  - `NewIdea` + `DecisionCase` のリスト → `Question` のリスト + メタ情報
  - LLMを使うのは「問いのテキスト生成」の部分だけに限定する。
- 非責務：
  - 類似度計算（similarity search）は別モジュール（similarity.py）の責務。
  - ログ保存やセッション管理は logging_service 側の責務。
  - フロントエンドとのHTTP通信（FastAPIエンドポイント）は main.py 側の責務。

---

## 3. インターフェース仕様（Pythonレベル）

設計したい関数は最低限以下：

def generate_questions(
    new_idea: NewIdea,
    cases: list[DecisionCase],
    *,
    num_questions_min: int = 3,
    num_questions_max: int = 7,
) -> tuple[list[Question], QuestionGenerationMeta]:
    """
    new_idea と類似 DecisionCase のリストをもとに、自己レビュー用の問いを生成する。

    - LLMに渡す system / user プロンプトの構築
    - LLM呼び出し
    - JSONパース
    - Question モデルへの変換
    - メタ情報（レイヤーごとの件数など）の返却
    までを一つの関数で完結させる。
    """
    ```
    
NewIdea, DecisionCase, Question, QuestionGenerationMeta は models.py の Pydantic モデルを想定。

generate_questions は副作用を持たない（ログ保存などは別の層で行う）。

## 4. 入力データ仕様の前提

NewIdea（新しい企画案）には少なくとも以下のフィールドがある前提で設計する：

title: str

summary: str

1〜3段落程度のテキスト（目的・ターゲット・提供価値・ビジネスモデルなどが混ざっている）

tags: list[str]

例: ["B2B", "SaaS", "製造業", "API"]

DecisionCase は decision_case.json のスキーマに準拠：

id: str

project_id: str

title: str

summary: str

status: Literal["adopted", "rejected", "pending"]

main_reason: str

tags: list[str]

decision_date: str (YYYY-MM-DD)

decision_level: str

source: str

question_generator は すでに類似度計算済みの DecisionCase 上位N件 を受け取る想定で設計する。

## 5. 出力データ仕様（Question / Meta）

Question は少なくとも以下のフィールドを持つ：

id: str

セッション内で一意なID（"q1", "q2" などでよい）

layer: int

1 / 2 / 3 のレイヤー種別（後述のレイヤーモデルに対応）

theme: str

問いの主領域（例： "purpose_kpi", "target_scope", "execution", "finance", "risk", "differentiation" など）

question: str

実際にユーザーに表示する問いの本文（日本語）

based_on_case_ids: list[str]

この問いのヒントになった DecisionCase の id のリスト（Layer2/3 で主に利用）

risk_type: str

想定しているリスクの種類（例："market_size", "cannibalization", "execution_capacity", "regulation", "generic_check" など）

priority: int

1〜3 の整数（3が最優先）

note_for_admin: str

「なぜこの問いを出したのか」のメモ（ユーザー非表示）

QuestionGenerationMeta には：

num_questions: int

layer1_count: int

layer2_count: int

layer3_count: int

comment: str（全体方針の短い説明）

## 6. 3レイヤーモデル（問いの種類）
Layer 1：企画の基礎チェック

ドメインに依存しない、どの組織でもほぼ共通の「基本チェック項目」に基づく問い。

代表的な領域：

目的・KPI（purpose_kpi）

ターゲット・スコープ（target_scope）

提供価値・差別化（differentiation）

実行体制・オペレーション（execution）

コスト・収支構造・撤退条件（finance / unit_economics）

実装方針：

コード側に Layer1 用の問いテンプレ候補を定義しておく（BASE_QUESTIONS_LAYER1）。

LLMには「このテンプレ一覧を見たうえで、今回の案が特に弱そうな観点を2つ程度選び、言い換えて返す」という指示を与える。

Layer1 の問いは基本 1〜2 個に抑える。

Layer 2：組織の「よく出る論点」パターン

過去の DecisionCase の main_reason からよく出る懸念・NG理由を抽象化し、問いにする。

例：

「市場規模が小さすぎる」「スケールしない」→ market_size

「既存プロダクトを食うだけ」「差別化が弱い」→ cannibalization / differentiation

「現場のリソースが足りない」「運用が回らない」→ execution_capacity

実装方針：

LLMに対し、similar_cases の main_reason と tags を渡し、

「どんな懸念が共通しているか」

「今回の案にも同じ罠があり得るか」
を考えさせて問いを作らせる。

based_on_case_ids には、その問いと特に関連がある DecisionCase の id を 1〜3 件入れる。

Layer2 の問いは 1〜3 個を目安。

Layer 3：今回の案の特徴から動的に

current_proposal 特有の特徴や、過去ケースとの「ズレ」に着目した問い。

例：

過去の類似案件より明らかに予算規模が大きい／小さい。

ターゲットセグメントがニッチで、タグから見ても対象企業数が少なそう。

過去に status="rejected" が多いタグ構成と酷似している。

実装方針：

LLMに「今回の案と過去ケースを比較して、どこが極端・特徴的か」を説明させ、
そこに対する問いを 1〜2 個作らせる。

based_on_case_ids に対応するケースを入れ、risk_type もセットする。

## 7. 問いの品質条件

Yes/No で終わる問いは避ける。

例×：「この企画の市場規模は十分ですか？」

例○：「この企画のターゲット市場規模は、3年後の売上目標を支えられる水準かどうか、根拠とともに説明できますか？」

答えをそのまま提案者に教えるのではなく、「考える切り口」を与えることにフォーカスする。

1つの問いは、全角80〜140文字程度に収める（長すぎる説教にしない）。

「抽象フレームワーク語だけ」の質問は避ける。

例×：「この企画のシナジーは何ですか？」

例○：「既存サービスとの組み合わせで、顧客に追加で生まれる具体的な価値は何ですか？」

トーンはフラットでよいが、「攻撃的」「人格否定」にならないようにする。

## 8. LLMの使い方（このモジュール内での前提）

テキスト生成系のLLM を使うのは question_generator だけにする

責務：

systemプロンプト：このドキュメントで定義した役割・出力フォーマット・レイヤー説明を含める。

userプロンプト：具体的な NewIdea と similar_decision_cases を埋め込む。

出力：

response_format={"type": "json_object"} を指定し、必ず有効なJSONを返してもらう前提で設計。

エラー時：

パースに失敗した場合は、最低限 Layer1 のテンプレートから静的な問いを返すフォールバックを用意する。

## 9. このプロンプトに対してあなたにやってほしいこと

上記の要件を読み、question_generator.py の設計を具体化してほしい。

必要であれば、Question, QuestionGenerationMeta の Pydantic モデル定義案を出してほしい。

build_system_prompt(), build_user_message(), call_llm(), generate_questions() のように、
責務分離された関数構成を提案し、そのコード例を出してほしい。

実装上の注意点（例：プロンプト長・タイムアウト・例外処理・将来的な拡張余地）も指摘してほしい。

この前提を踏まえて、問い生成サービスの設計と、最初の実装案を一緒に作ってください。