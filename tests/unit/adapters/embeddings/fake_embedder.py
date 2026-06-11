from __future__ import annotations


class FakeEmbedder:
    def __init__(self, dimension: int = 128) -> None:
        self._dim = dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import hashlib
        results: list[list[float]] = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            vec = [float(b) / 255.0 for b in h[:self._dim]]
            results.append(vec)
        return results

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
