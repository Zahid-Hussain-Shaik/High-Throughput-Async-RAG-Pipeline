import pytest
import httpx
from app.core.config import Settings
from app.schemas.response import RAGResponse
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMError, LLMService
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievedChunk

class Retrieval:
    def __init__(self, chunks): self.chunks = chunks
    async def retrieve(self, *args): return self.chunks

@pytest.mark.asyncio
async def test_insufficient_context_returns_ungrounded(settings):
    service = RAGService(Retrieval([RetrievedChunk("c", "d", "x", {}, .1)]), object(), .3)
    result = await service.answer(None, "q", 1)
    assert result.grounded is False and not result.sources

@pytest.mark.asyncio
async def test_local_llm_mode_returns_sources(settings):
    async with httpx.AsyncClient() as client:
        llm = LLMService(settings, client)
        response = await llm.answer("q", [RetrievedChunk("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002", "context", {}, .9)])
    assert response.grounded and len(response.sources) == 1

@pytest.mark.asyncio
async def test_malformed_llm_response_is_rejected(settings):
    settings = settings.model_copy(update={"llm_api_key": "secret", "llm_base_url": "https://example.test"})
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(LLMError):
            await LLMService(settings, client).answer("q", [RetrievedChunk("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002", "context", {}, .9)])
