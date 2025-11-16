from __future__ import annotations

from typing import List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import DecisionCase, NewIdea

_vectorizer: Optional[TfidfVectorizer] = None
_case_matrix = None  # scipy.sparse matrix を想定（型は実行時に決まる）
_cases: List[DecisionCase] = []


def initialize_vectorizer(cases: List[DecisionCase]) -> None:
    """DecisionCase 一覧を元に TF-IDF ベクトル化器を初期化する。

    summary フィールドをベースにベクトル化する。
    """
    global _vectorizer, _case_matrix, _cases

    _cases = list(cases)

    if not _cases:
        _vectorizer = None
        _case_matrix = None
        return

    summaries = [c.summary for c in _cases]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(summaries)

    _vectorizer = vectorizer
    _case_matrix = matrix


def search_similar_cases(new_idea: NewIdea, top_k: int = 5) -> List[DecisionCase]:
    """NewIdea.summary をベースに類似 DecisionCase を検索する。

    類似度（コサイン類似度）が高い順に top_k 件返す。
    ベクトル化器が未初期化の場合や、ケースが無い場合は空リストを返す。
    """
    if _vectorizer is None or _case_matrix is None or not _cases:
        return []

    query_vec = _vectorizer.transform([new_idea.summary])

    # ベクトルが全てゼロの場合は有効な類似度が計算できない
    if query_vec.nnz == 0:
        return []

    similarities = cosine_similarity(query_vec, _case_matrix)[0]

    k = max(0, min(top_k, len(_cases)))
    if k == 0:
        return []

    # 類似度の高い順にインデックスをソート
    top_indices = similarities.argsort()[::-1][:k]
    return [_cases[i] for i in top_indices]


__all__ = ["initialize_vectorizer", "search_similar_cases"]
