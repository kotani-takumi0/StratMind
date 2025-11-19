from __future__ import annotations

import json
from typing import Any, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.models import (
    DecisionCase,
    NewIdea,
    Question,
    QuestionGenerationMeta,
)

load_dotenv()
_client = OpenAI()


# Layer1 用のベース質問テンプレート
BASE_QUESTIONS_LAYER1: list[dict[str, str]] = [
    {
        "id": "L1-1",
        "theme": "purpose_kpi",
        "risk_type": "generic_check",
        "template": (
            "この企画の最終的な目的と成功指標（KPI）を、誰にどんな変化を起こすのかという観点で一文で説明してください。"
        ),
    },
    {
        "id": "L1-2",
        "theme": "target_scope",
        "risk_type": "generic_check",
        "template": (
            "この企画の主な対象ユーザーと、あえて対象外とするユーザーを、具体的な属性や利用シーンとセットで書き分けてください。"
        ),
    },
    {
        "id": "L1-3",
        "theme": "execution",
        "risk_type": "execution_capacity",
        "template": (
            "日常運用の責任者と必要なロール（部署・役割）を挙げ、現状の体制でどこが特に弱いかを説明してください。"
        ),
    },
]


class LLMQuestionItem(BaseModel):
    id: str
    layer: int
    theme: str
    question: str
    based_on_case_ids: list[str]
    risk_type: str
    priority: int
    note_for_admin: str


class LLMQuestionsPayload(BaseModel):
    questions: list[LLMQuestionItem]
    meta: QuestionGenerationMeta


def build_system_prompt() -> str:
    """役割・フォーマット・3レイヤーモデルを説明する system プロンプトを構築する。"""

    return """
あなたは「新規事業の自己レビューを支援する問いジェネレーター」です。

目的:
- NewIdea（新しい企画案）と、類似 DecisionCase の一覧を読み、
  企画担当者が自己レビューに使える3〜7個の問いを日本語で生成します。
- AIが回答を決めるのではなく、「どの観点から考えればよいか」を示す問いを出してください。

出力フォーマット:
- 必ず JSON オブジェクトで返してください。
- スキーマ:

{
  "questions": [
    {
      "id": "q1",
      "layer": 1,
      "theme": "purpose_kpi",
      "question": "ここに問い本文",
      "based_on_case_ids": ["DC-001"],
      "risk_type": "market_size",
      "priority": 2,
      "note_for_admin": "ここに運営向けメモ"
    }
  ],
  "meta": {
    "num_questions": 5,
    "layer1_count": 2,
    "layer2_count": 2,
    "layer3_count": 1,
    "comment": "全体方針の短い説明"
  }
}

制約:
- questions 配列は3〜7個。
- Yes/No で終わらず、記述式で答えざるを得ない問いにすること。
- 1つの問いは全角80〜140文字程度を目安に、長すぎる説教は避けること。
- Layer1/2/3 をすべて含め、どれか1レイヤーに極端に偏らないこと。
- theme, risk_type は一貫した英単語を用いること。

3レイヤーモデル:
- Layer1: 企画の基礎チェック（purpose_kpi, target_scope, differentiation, execution, finance など）
- Layer2: 過去 DecisionCase の main_reason や tags から見える「よくあるNG/懸念パターン」由来の問い。
- Layer3: current_proposal と類似 DecisionCase を比較したときの「極端・特徴的な点」にフォーカスした問い。

品質:
- 「不安を煽るだけ」の問いではなく、「どう考えれば前に進めるか」が分かる問いにしてください。
- 抽象的なフレームワーク用語だけで終わらず、現場の言葉で具体的に書いてください。
- 攻撃的・人格否定的な表現は禁止です。
""".strip()


def build_user_message(
    new_idea: NewIdea,
    cases: list[DecisionCase],
    num_questions_min: int,
    num_questions_max: int,
) -> str:
    """具体的な NewIdea / DecisionCase / テンプレを埋め込んだ user メッセージを構築する。"""

    simplified_cases: list[dict[str, Any]] = []
    for c in cases[:10]:
        simplified_cases.append(
            {
                "id": c.id,
                "title": c.title,
                "summary": c.summary,
                "status": c.status,
                "main_reason": c.main_reason,
                "tags": c.tags,
            }
        )

    payload = {
        "current_proposal": new_idea.dict(),
        "similar_decision_cases": simplified_cases,
        "layer1_base_questions": BASE_QUESTIONS_LAYER1,
        "constraints": {
            "num_questions_min": num_questions_min,
            "num_questions_max": num_questions_max,
        },
        "instructions": {
            "layer1": "BASE_QUESTIONS_LAYER1 を参考に、今回の案で特に弱そうな観点を1〜2つ選び、必要に応じて言い換えてください。",
            "layer2": "similar_decision_cases の main_reason / tags から共通する懸念パターンを整理し、それを避けるための問いを1〜3個作ってください。",
            "layer3": "current_proposal が過去ケースと比べて極端・特徴的な点を挙げ、その点を検証する問いを1〜2個作ってください。",
        },
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)


def call_llm(system_prompt: str, user_message: str) -> LLMQuestionsPayload:
    """OpenAI Responses API を呼び出し、JSON をパースして内部モデルに変換する。"""

    res = _client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )

    # output_text プロパティから JSON 文字列を取得する前提
    content = res.output_text
    raw = json.loads(content)
    return LLMQuestionsPayload.model_validate(raw)


def _fallback_questions(
    new_idea: NewIdea,
    cases: list[DecisionCase],
    num_questions_min: int,
    num_questions_max: int,
) -> Tuple[list[Question], QuestionGenerationMeta]:
    """LLM失敗時用の静的問い生成（Layer1のみ）。"""

    k = max(3, min(num_questions_max, len(BASE_QUESTIONS_LAYER1)))
    selected = BASE_QUESTIONS_LAYER1[:k]

    based_on_ids = [c.id for c in cases[:3]]

    questions: list[Question] = []
    for i, tpl in enumerate(selected, start=1):
        questions.append(
            Question(
                id=f"q{i}",
                layer=1,
                theme=tpl["theme"],
                question=tpl["template"],
                based_on_case_ids=based_on_ids,
                risk_type=tpl["risk_type"],
                priority=2,
                note_for_admin="LLM出力のパースに失敗したため、Layer1テンプレートから生成されたフォールバック質問です。",
            )
        )

    meta = QuestionGenerationMeta(
        num_questions=len(questions),
        layer1_count=len(questions),
        layer2_count=0,
        layer3_count=0,
        comment="LLM出力のパースに失敗したため、Layer1テンプレートのみで問いを生成しました。",
    )
    return questions, meta


def generate_questions(
    new_idea: NewIdea,
    cases: list[DecisionCase],
    *,
    num_questions_min: int = 3,
    num_questions_max: int = 7,
) -> Tuple[list[Question], QuestionGenerationMeta]:
    """
    new_idea と類似 DecisionCase のリストをもとに、自己レビュー用の問いを生成する。

    - LLMに渡す system / user プロンプトの構築
    - LLM呼び出し
    - JSONパース
    - Question モデルへの変換
    - メタ情報（レイヤーごとの件数など）の返却
    """

    system_prompt = build_system_prompt()
    user_message = build_user_message(new_idea, cases, num_questions_min, num_questions_max)

    try:
        payload = call_llm(system_prompt, user_message)
    except (json.JSONDecodeError, ValidationError, Exception):
        return _fallback_questions(new_idea, cases, num_questions_min, num_questions_max)

    questions: list[Question] = []
    for i, q in enumerate(payload.questions, start=1):
        questions.append(
            Question(
                id=q.id or f"q{i}",
                layer=q.layer,
                theme=q.theme,
                question=q.question,
                based_on_case_ids=q.based_on_case_ids,
                risk_type=q.risk_type,
                priority=q.priority,
                note_for_admin=q.note_for_admin,
            )
        )

    meta = QuestionGenerationMeta(
        num_questions=len(questions),
        layer1_count=sum(1 for q in questions if q.layer == 1),
        layer2_count=sum(1 for q in questions if q.layer == 2),
        layer3_count=sum(1 for q in questions if q.layer == 3),
        comment=payload.meta.comment,
    )

    return questions, meta


__all__ = [
    "generate_questions",
    "build_system_prompt",
    "build_user_message",
    "call_llm",
]
