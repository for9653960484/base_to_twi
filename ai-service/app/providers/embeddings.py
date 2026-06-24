"""Синхронная генерация эмбеддингов."""

import hashlib

import httpx

from app.config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    provider = settings.AI_EMBEDDING_PROVIDER
    if provider == "local":
        try:
            return _embed_local(texts)
        except Exception:
            if settings.embedding_api_key:
                return _embed_external(texts)
            return _embed_fallback(texts)

    if provider == "external":
        if settings.embedding_api_key:
            return _embed_external(texts)
        return _embed_fallback(texts)

    # hybrid
    try:
        return _embed_local(texts)
    except Exception:
        if settings.embedding_api_key:
            return _embed_external(texts)
        return _embed_fallback(texts)


def embed_single(text: str) -> list[float]:
    return embed_texts([text])[0]


def _embed_external(texts: list[str]) -> list[list[float]]:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{settings.embedding_base_url.rstrip('/')}/embeddings",
            headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
            json={"model": settings.AI_EMBEDDING_MODEL, "input": texts},
        )
        response.raise_for_status()
        data = response.json()["data"]
        sorted_data = sorted(data, key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]


def _embed_local(texts: list[str]) -> list[list[float]]:
    results = []
    with httpx.Client(timeout=120.0) as client:
        for text in texts:
            response = client.post(
                f"{settings.AI_LOCAL_BASE_URL.rstrip('/')}/api/embeddings",
                json={"model": settings.AI_EMBEDDING_LOCAL_MODEL, "prompt": text},
            )
            response.raise_for_status()
            results.append(response.json()["embedding"])
    return results


def _embed_fallback(texts: list[str]) -> list[list[float]]:
    """Детерминированные псевдо-векторы для dev без API-ключей."""
    dim = settings.VECTOR_DIMENSION
    vectors = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(dim):
            chunk = digest[i % len(digest)]
            vec.append((chunk / 255.0) * 2 - 1)
        vectors.append(_normalize(vec))
    return vectors


def _normalize(vec: list[float]) -> list[float]:
    norm = sum(x * x for x in vec) ** 0.5
    if norm == 0:
        return vec
    return [x / norm for x in vec]
