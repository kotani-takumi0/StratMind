from __future__ import annotations

from typing import List

import numpy as np
from pydantic import BaseModel

from app.models import DecisionCase, NewIdea
from app.services.embeddings import embed_texts
from app.services.loader import get_decision_cases
from app.services.utils import normalize_rows

CASES: list[DecisionCase] | None = None
X_n: np.ndarray | None = None  # shape (N, D), L2 正規化済


class ScoredDecisionCase(BaseModel):
    case: DecisionCase
    similarity: float


def build_case_text(case: DecisionCase) -> str:
    parts = [
        case.title,
        case.summary,
        "Tags: " + ", ".join(case.tags or []),
        "Status: " + case.status,
        "Main reason: " + (case.main_reason or ""),
    ]
    return "\n".join(parts)


def build_query_text(new_idea: NewIdea) -> str:
    parts = [
        new_idea.title,
        new_idea.summary,
        "Tags: " + ", ".join(new_idea.tags or []),
    ]
    return "\n".join(parts)


def initialize_similarity() -> None:
    """DecisionCase の埋め込み行列を作成し、正規化してキャッシュする。"""
    global CASES, X_n

    CASES = get_decision_cases()

    if not CASES:
        X_n = None
        return

    texts = [build_case_text(c) for c in CASES]
    vecs = embed_texts(texts)

    if vecs.size == 0:
        X_n = None
        return

    X_n = normalize_rows(vecs)


def analyze_similarity_cases(
    query_vec: np.ndarray,
    *,
    topk: int = 5,
) -> list[tuple[int, float]]:
    """クエリベクトルと CASES の類似度を計算し、上位 topk 件を返す。"""
    if X_n is None or X_n.size == 0:
        return []

    Q_n = normalize_rows(query_vec)
    scores = (Q_n @ X_n.T)[0]

    n = scores.shape[0]
    if n == 0:
        return []

    k = min(topk, n)
    if k <= 0:
        return []

    # 上位 k 件のインデックスを argpartition で取得し、その部分だけを降順ソート
    idx_part = np.argpartition(scores, -k)[-k:]
    idx_sorted = idx_part[np.argsort(scores[idx_part])[::-1]]

    return [(int(i), float(scores[i])) for i in idx_sorted]


def search_similar_cases(new_idea: NewIdea, top_k: int = 5) -> List[ScoredDecisionCase]:
    """NewIdea を受け取り、類似 DecisionCase をスコア付きで返す。"""
    if CASES is None or X_n is None:
        raise Exception("initialize_similarity() が実行されていません。")

    query_text = build_query_text(new_idea)
    query_vec = embed_texts([query_text])

    idx_scores = analyze_similarity_cases(query_vec, topk=top_k)

    return [
        ScoredDecisionCase(case=CASES[idx], similarity=score) for idx, score in idx_scores
    ]


__all__ = [
    "ScoredDecisionCase",
    "build_case_text",
    "build_query_text",
    "initialize_similarity",
    "analyze_similarity_cases",
    "search_similar_cases",
]
