from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_cache, get_rag_service, get_session
from app.core.security import cache_key
from app.schemas.query import QueryRequest
from app.schemas.response import RAGResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/query", tags=["query"])

@router.post("", response_model=RAGResponse)
async def query_rag(payload: QueryRequest, session: AsyncSession = Depends(get_session), service: RAGService = Depends(get_rag_service), cache=Depends(get_cache)):
    settings = service.retrieval.embeddings.settings
    top_k = payload.top_k or settings.top_k
    key = cache_key(payload.query, top_k, settings.vector_weight, settings.keyword_weight)
    cached = await cache.get(key)
    if cached: return RAGResponse.model_validate(cached)
    try: response = await service.answer(session, payload.query, top_k)
    except Exception as exc:
        from app.services.llm_service import LLMError
        if isinstance(exc, LLMError): raise HTTPException(502, "Answer generation failed") from exc
        raise
    await cache.set(key, response.model_dump(mode="json"))
    return response
