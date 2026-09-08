import json
import httpx
from app.core.config import Settings
from app.schemas.response import RAGResponse
from app.services.retrieval_service import RetrievedChunk

SYSTEM_PROMPT = """You are a retrieval-grounded question answering system. Answer ONLY using supplied context. Do not use outside knowledge or infer unsupported facts. If context is insufficient, state that the answer cannot be determined from the provided context. Every factual claim must be supported by context. Return ONLY valid JSON matching answer, sources, grounded. No Markdown."""


class LLMError(RuntimeError):
    pass


class LLMService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self.settings, self.client = settings, client

    async def answer(self, query: str, chunks: list[RetrievedChunk]) -> RAGResponse:
        sources = [{"document_id": c.document_id, "chunk_id": c.chunk_id, "score": c.score} for c in chunks]
        if not self.settings.llm_api_key:
            return RAGResponse(answer="LLM is not configured; retrieved context is available.", sources=sources, grounded=True)
        context = "\n\n".join(f"[{i}] {c.content}" for i, c in enumerate(chunks, 1))
        try:
            response = await self.client.post(f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={"model": self.settings.llm_model, "response_format": {"type": "json_object"},
                      "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}]})
            response.raise_for_status()
            parsed = json.loads(response.json()["choices"][0]["message"]["content"])
            parsed["sources"] = sources
            return RAGResponse.model_validate(parsed)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LLMError("LLM returned an invalid response") from exc
