from abc import ABC, abstractmethod

import httpx

from app.config import settings


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str = "", model_tier: str = "heavy") -> str:
        ...


class ExternalLLMProvider(LLMProvider):
    async def complete(self, prompt: str, system: str = "", model_tier: str = "heavy") -> str:
        model = settings.AI_LIGHT_MODEL if model_tier == "light" else settings.AI_EXTERNAL_MODEL
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.AI_EXTERNAL_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_EXTERNAL_API_KEY}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


class LocalLLMProvider(LLMProvider):
    async def complete(self, prompt: str, system: str = "", model_tier: str = "heavy") -> str:
        model = settings.AI_LOCAL_LIGHT_MODEL if model_tier == "light" else settings.AI_LOCAL_HEAVY_MODEL
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.AI_LOCAL_BASE_URL.rstrip('/')}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]


class HybridLLMProvider(LLMProvider):
    def __init__(self):
        self.external = ExternalLLMProvider()
        self.local = LocalLLMProvider()

    async def complete(self, prompt: str, system: str = "", model_tier: str = "heavy") -> str:
        if model_tier == "light":
            try:
                return await self.local.complete(prompt, system, model_tier)
            except Exception:
                return await self.external.complete(prompt, system, model_tier)
        try:
            return await self.external.complete(prompt, system, model_tier)
        except Exception:
            return await self.local.complete(prompt, system, model_tier)


def get_llm_provider() -> LLMProvider:
    providers = {
        "external": ExternalLLMProvider,
        "local": LocalLLMProvider,
        "hybrid": HybridLLMProvider,
    }
    return providers.get(settings.AI_PROVIDER, HybridLLMProvider)()
