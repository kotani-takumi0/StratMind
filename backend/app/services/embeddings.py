from __future__ import annotations

from typing import List

import numpy as np
from dotenv import load_dotenv

from .aimodel import OpenAI, genai, get_ai_client
from google.genai import types

load_dotenv()

client = get_ai_client()

def embed_texts(texts: list[str]) -> np.ndarray:
    """
    与えられたテキスト群に対して OpenAI の埋め込みを計算し、
    shape = (len(texts), D) の numpy.ndarray を返す。

    - モデル: text-embedding-3-small
    - .env の OPENAI_API_KEY を利用する
    """
    if not texts:
        return np.zeros((0, 0), dtype="float32")
    
    vectors = []
    
    # OpenAIクライアントの場合
    if isinstance(client, OpenAI):
        # モデル名: text-embedding-3-small (OpenAI)
        res = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        vectors = [item.embedding for item in res.data]

    # Geminiクライアントの場合
    elif isinstance(client, genai.Client):
        # モデル名: gemini-embedding-001 (Google)
        res = client.models.embed_content(
            model="gemini-embedding-001", 
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY" # 例: 意味的類似性のタスク
            )
        )
        # Geminiのレスポンスは .embeddings プロパティを持ち、要素ごとに値が格納されている
        vectors = [list(e.values) for e in res.embeddings]

    arr = np.array(vectors, dtype="float32")
    return arr


__all__ = ["embed_texts"]

