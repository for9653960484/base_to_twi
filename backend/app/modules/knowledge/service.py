"""Векторный поиск и Q&A по базе знаний."""

import json
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.knowledge.schemas import KnowledgeSearchResponse, KnowledgeSource


def _vector_to_pg(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


async def _embed_query(query: str) -> list[float]:
    base_url = settings.AI_EMBEDDING_BASE_URL or settings.AI_EXTERNAL_BASE_URL
    api_key = settings.AI_EMBEDDING_API_KEY or settings.AI_EXTERNAL_API_KEY

    if settings.AI_EMBEDDING_PROVIDER == "local" or not api_key:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.AI_LOCAL_BASE_URL.rstrip('/')}/api/embeddings",
                    json={"model": settings.AI_EMBEDDING_LOCAL_MODEL, "prompt": query},
                )
                response.raise_for_status()
                return response.json()["embedding"]
        except Exception:
            pass

    if api_key:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": settings.AI_EMBEDDING_MODEL, "input": query},
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

    # fallback hash embedding (dev)
    import hashlib
    dim = settings.VECTOR_DIMENSION
    digest = hashlib.sha256(query.encode()).digest()
    vec = [((digest[i % len(digest)] / 255.0) * 2 - 1) for i in range(dim)]
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec] if norm else vec


async def _generate_answer(query: str, context: str) -> str:
    if not settings.AI_EXTERNAL_API_KEY and settings.AI_PROVIDER == "external":
        return context[:2000] if context else "Контекст не найден."

    model = settings.qa_model
    system = "Ты — справочная система технической поддержки по обслуживанию аттракционов. Отвечай на русском, кратко и по делу, опираясь только на контекст."
    prompt = f"Контекст:\n{context}\n\nВопрос: {query}"

    if settings.AI_PROVIDER in ("local", "hybrid"):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.AI_LOCAL_BASE_URL.rstrip('/')}/api/chat",
                    json={
                        "model": settings.AI_LOCAL_HEAVY_MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                    },
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception:
            if settings.AI_PROVIDER == "local":
                return context[:2000]

    if settings.AI_EXTERNAL_API_KEY:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.AI_EXTERNAL_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_EXTERNAL_API_KEY}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    return context[:2000] if context else "Недостаточно данных для ответа."


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self, query: str, equipment_id: UUID | None = None, top_k: int = 5
    ) -> KnowledgeSearchResponse:
        embedding = await _embed_query(query)
        vec = _vector_to_pg(embedding)

        sql = """
            SELECT kc.content, kc.source_type::text, kc.source_id, kc.metadata,
                   1 - (kc.embedding <=> CAST(:vec AS vector)) AS score
            FROM knowledge_chunks kc
            WHERE kc.embedding IS NOT NULL
        """
        params: dict = {"vec": vec, "limit": top_k}

        if equipment_id:
            sql += " AND kc.equipment_id = :eq_id"
            params["eq_id"] = str(equipment_id)

        sql += " ORDER BY kc.embedding <=> CAST(:vec AS vector) LIMIT :limit"

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        sources: list[KnowledgeSource] = []
        context_parts: list[str] = []
        for row in rows:
            content, source_type, source_id, metadata, score = row
            meta = metadata if isinstance(metadata, dict) else json.loads(metadata or "{}")
            title = meta.get("title", source_type)
            sources.append(
                KnowledgeSource(
                    source_type=source_type,
                    source_id=source_id,
                    title=title,
                    excerpt=content[:300],
                    relevance_score=float(score),
                )
            )
            context_parts.append(content)

        context = "\n---\n".join(context_parts)
        answer = await _generate_answer(query, context) if context else "По вашему запросу ничего не найдено в базе знаний."

        return KnowledgeSearchResponse(
            answer=answer,
            sources=sources,
            equipment_id=equipment_id,
        )
