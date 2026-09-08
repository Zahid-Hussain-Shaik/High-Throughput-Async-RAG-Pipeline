from dataclasses import dataclass
from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import DocumentChunk
from app.services.embedding_service import EmbeddingService


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict
    score: float


class RetrievalService:
    def __init__(self, embeddings: EmbeddingService, vector_weight: float, keyword_weight: float) -> None:
        self.embeddings, self.vector_weight, self.keyword_weight = embeddings, vector_weight, keyword_weight

    async def retrieve(self, session: AsyncSession, query: str, top_k: int) -> list[RetrievedChunk]:
        vector = await self.embeddings.embed_text(query)
        distance = DocumentChunk.embedding.cosine_distance(vector)
        vector_score = 1 - cast(distance, Float)
        fts = func.ts_rank_cd(func.to_tsvector("english", DocumentChunk.content), func.websearch_to_tsquery("english", query))
        score = (self.vector_weight * vector_score + self.keyword_weight * fts).label("score")
        rows = (await session.execute(select(DocumentChunk, score).where(
            func.to_tsvector("english", DocumentChunk.content).op("@@")(func.websearch_to_tsquery("english", query)) | (distance < 1)
        ).order_by(score.desc()).limit(top_k))).all()
        return [RetrievedChunk(str(chunk.id), str(chunk.document_id), chunk.content, chunk.metadata_, max(0., min(1., float(result_score))))
                for chunk, result_score in rows]
