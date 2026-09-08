from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from app.api.routes import documents, health, query
from app.cache.redis import RedisCache
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import build_engine, build_session_factory
from app.middleware.rate_limit import RateLimitMiddleware, RedisTokenBucket
from app.middleware.request_id import RequestIDMiddleware
from app.services.chunking_service import ChunkingService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings(); configure_logging(); app.state.settings = settings
    app.state.engine = build_engine(settings); app.state.session_factory = build_session_factory(app.state.engine)
    app.state.http = httpx.AsyncClient(timeout=settings.embedding_timeout_seconds)
    try:
        app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True); await app.state.redis.ping()
    except Exception: app.state.redis = None
    embeddings = EmbeddingService(settings, app.state.http)
    app.state.document_service = DocumentService(ChunkingService(settings.chunk_size, settings.chunk_overlap), embeddings)
    app.state.rag_service = RAGService(RetrievalService(embeddings, settings.vector_weight, settings.keyword_weight), LLMService(settings, app.state.http), settings.min_retrieval_score)
    app.state.cache = RedisCache(app.state.redis, settings.redis_cache_ttl)
    yield
    if app.state.redis: await app.state.redis.aclose()
    await app.state.http.aclose(); await app.state.engine.dispose()

app = FastAPI(title="Async RAG API", version="1.0.0", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, limiter=RedisTokenBucket(None, get_settings().rate_limit_capacity, get_settings().rate_limit_refill_rate))
app.include_router(health.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")

@app.get("/", tags=["health"], summary="API landing endpoint")
async def root() -> dict[str, str]:
    return {
        "service": "Async RAG API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "openapi": "/openapi.json",
    }

@app.exception_handler(Exception)
async def unhandled_error(_, __): return JSONResponse({"detail": "Internal server error"}, status_code=500)
