import uuid
from pydantic import BaseModel, Field


class Source(BaseModel):
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    score: float = Field(ge=0, le=1)


class RAGResponse(BaseModel):
    answer: str
    sources: list[Source]
    grounded: bool
