from __future__ import annotations

from typing import List

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    与えられたテキスト群に対して OpenAI の埋め込みを計算し、
    shape = (len(texts), D) の numpy.ndarray を返す。

    - モデル: text-embedding-3-small
    - .env の OPENAI_API_KEY を利用する
    """
    if not texts:
        return np.zeros((0, 0), dtype="float32")

    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    vectors = [item.embedding for item in res.data]
    arr = np.array(vectors, dtype="float32")
    return arr


__all__ = ["embed_texts"]

