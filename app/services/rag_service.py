from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import RAGResponse
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class RAGService:
    def __init__(self, retrieval: RetrievalService, llm: LLMService, threshold: float) -> None:
        self.retrieval, self.llm, self.threshold = retrieval, llm, threshold

    async def answer(self, session: AsyncSession, query: str, top_k: int) -> RAGResponse:
        chunks = await self.retrieval.retrieve(session, query, top_k)
        chunks = [chunk for chunk in chunks if chunk.score >= self.threshold]
        if not chunks:
            return RAGResponse(answer="I cannot determine the answer from the provided context.", sources=[], grounded=False)
        return await self.llm.answer(query, chunks)
