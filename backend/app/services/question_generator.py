from __future__ import annotations

from typing import List
from uuid import uuid4

from app.models import DecisionCase, NewIdea, Question


def generate_questions(new_idea: NewIdea, similar_cases: List[DecisionCase]) -> List[Question]:
    """NewIdea と類似 DecisionCase から 3〜7件の問いを生成する簡易実装。

    仮仕様として、LLM 連携や高度なロジックの代わりに、
    固定テンプレートにもとづく問いを返す。
    後続の 03_question_generator.md の仕様に合わせて差し替え可能とする。
    """

    # レイヤー1〜3に対応したシンプルなテンプレート
    templates: List[tuple[str, int]] = [
        ("この企画の一次目的と二次目的は何ですか？", 1),
        ("対象ユーザーとスコープ外の範囲はどこまでですか？", 1),
        ("日常運用の責任者と実行体制はどのように設計していますか？", 2),
        ("既存の施策や事業と比べたとき、この案ならではの違いは何ですか？", 2),
        ("この企画の成否を判断するための具体的な指標は何ですか？", 1),
        ("想定している主要なリスクと、そのリスクに対する対応方針は何ですか？", 3),
        ("どの条件になったら撤退または縮小を検討しますか？", 3),
    ]

    # 最初の 3〜5 件程度を使う（3〜7件の範囲に収める）
    selected = templates[:5]

    # 参考として、類似ケースのIDを紐づけておく（最大3件）
    source_ids = [case.id for case in similar_cases[:3]]

    questions: List[Question] = []
    for text, layer in selected:
        questions.append(
            Question(
                id=str(uuid4()),
                text=text,
                layer=layer,
                source_case_ids=source_ids,
            )
        )

    return questions


__all__ = ["generate_questions"]
