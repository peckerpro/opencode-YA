from __future__ import annotations

from openai import AsyncOpenAI


class VolcengineEmbedder:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        model: str = "doubao-embedding-vision-251215",
    ) -> None:
        self._model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [d.embedding for d in response.data]

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
