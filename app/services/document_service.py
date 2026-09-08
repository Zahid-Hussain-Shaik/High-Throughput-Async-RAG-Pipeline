from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentChunk
from app.schemas.document import DocumentCreate
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService


class DocumentService:
    def __init__(self, chunker: ChunkingService, embeddings: EmbeddingService) -> None:
        self.chunker, self.embeddings = chunker, embeddings

    async def create(self, session: AsyncSession, payload: DocumentCreate) -> Document:
        document = Document(title=payload.title, source=payload.source, content=payload.content, metadata_=payload.metadata)
        session.add(document)
        await session.flush()
        drafts = await self.chunker.chunk(payload.content, payload.metadata)
        vectors = await self.embeddings.embed_batch([draft.content for draft in drafts])
        session.add_all([DocumentChunk(document_id=document.id, chunk_index=draft.chunk_index,
            content=draft.content, metadata_=draft.metadata, embedding=vector) for draft, vector in zip(drafts, vectors, strict=True)])
        await session.commit()
        await session.refresh(document)
        return document

    async def get(self, session: AsyncSession, document_id) -> Document | None:
        return await session.scalar(select(Document).where(Document.id == document_id))
