from __future__ import annotations

import numpy as np

from app.services.ai_services import ai_service

# 11/27 add: services/ai_services.pyに集約
def embed_texts(texts: list[str]) -> np.ndarray:
    return ai_service.embed_texts(texts)

__all__ = ["embed_texts"]

