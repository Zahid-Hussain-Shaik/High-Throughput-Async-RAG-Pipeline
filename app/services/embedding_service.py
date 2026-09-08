import asyncio
import hashlib
import math
import httpx
from app.core.config import Settings


class EmbeddingError(RuntimeError):
    pass


class EmbeddingService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self.settings, self.client = settings, client
        self.semaphore = asyncio.Semaphore(settings.embedding_concurrency)

    async def embed_text(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.settings.embedding_api_key:
            return [self._local_embedding(text) for text in texts]
        async with self.semaphore:
            try:
                response = await self.client.post(f"{self.settings.embedding_base_url.rstrip('/')}/embeddings",
                    headers={"Authorization": f"Bearer {self.settings.embedding_api_key}"},
                    json={"model": self.settings.embedding_model, "input": texts,
                          "dimensions": self.settings.embedding_dimension})
                response.raise_for_status()
                vectors = [entry["embedding"] for entry in response.json()["data"]]
                if any(len(vector) != self.settings.embedding_dimension for vector in vectors):
                    raise EmbeddingError("provider returned unexpected embedding dimension")
                return vectors
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                raise EmbeddingError("embedding provider request failed") from exc

    def _local_embedding(self, text: str) -> list[float]:
        """Deterministic offline provider for local development and tests only."""
        values = [0.0] * self.settings.embedding_dimension
        for word in text.lower().split():
            slot = int.from_bytes(hashlib.blake2b(word.encode(), digest_size=8).digest(), "big") % len(values)
            values[slot] += 1
        norm = math.sqrt(sum(v * v for v in values)) or 1
        return [v / norm for v in values]
