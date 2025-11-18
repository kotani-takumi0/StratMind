from __future__ import annotations

import numpy as np


def normalize_rows(vecs: np.ndarray) -> np.ndarray:
    """行ごとに L2 正規化した行列を返す。

    ゼロベクトルの行はそのままゼロベクトルとして返す。
    """
    if vecs.size == 0:
        return vecs

    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return vecs / norms


__all__ = ["normalize_rows"]

