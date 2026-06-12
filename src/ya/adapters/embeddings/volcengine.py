from __future__ import annotations

import httpx


class VolcengineEmbedder:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        model: str = "doubao-embedding-vision-251215",
    ) -> None:
        self._model = model
        self._endpoint = f"{base_url}/embeddings/multimodal"
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                response = await client.post(
                    self._endpoint,
                    headers=self._headers,
                    json={
                        "model": self._model,
                        "input": [{"type": "text", "text": text}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["data"]["embedding"])
        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
