"""Синхронные LLM-вызовы для Celery workers."""

import httpx

from app.config import settings


def complete_sync(
    prompt: str,
    system: str = "",
    model_tier: str = "heavy",
    *,
    max_tokens: int | None = None,
    temperature: float = 0.2,
) -> str:
    provider = settings.AI_PROVIDER

    if model_tier == "light":
        if provider in ("local", "hybrid"):
            try:
                return _local_complete(prompt, system, light=True, max_tokens=max_tokens, temperature=temperature)
            except Exception:
                if provider == "local":
                    raise
        return _external_complete(prompt, system, light=True, max_tokens=max_tokens, temperature=temperature)

    if provider == "local":
        return _local_complete(prompt, system, light=False, max_tokens=max_tokens, temperature=temperature)
    if provider == "external":
        return _external_complete(prompt, system, light=False, max_tokens=max_tokens, temperature=temperature)
    # hybrid: heavy → external, fallback local
    try:
        return _external_complete(prompt, system, light=False, max_tokens=max_tokens, temperature=temperature)
    except Exception:
        return _local_complete(prompt, system, light=False, max_tokens=max_tokens, temperature=temperature)


def _external_complete(
    prompt: str,
    system: str,
    light: bool = False,
    *,
    max_tokens: int | None = None,
    temperature: float = 0.2,
) -> str:
    model = settings.AI_LIGHT_MODEL if light else settings.AI_EXTERNAL_MODEL
    if not settings.AI_EXTERNAL_API_KEY:
        raise RuntimeError("AI_EXTERNAL_API_KEY is not configured")

    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    with httpx.Client(timeout=300.0) as client:
        response = client.post(
            f"{settings.AI_EXTERNAL_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.AI_EXTERNAL_API_KEY}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def _local_complete(
    prompt: str,
    system: str,
    light: bool = False,
    *,
    max_tokens: int | None = None,
    temperature: float = 0.2,
) -> str:
    model = settings.AI_LOCAL_LIGHT_MODEL if light else settings.AI_LOCAL_HEAVY_MODEL
    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }
    if max_tokens:
        payload["options"]["num_predict"] = max_tokens
    with httpx.Client(timeout=300.0) as client:
        response = client.post(
            f"{settings.AI_LOCAL_BASE_URL.rstrip('/')}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
