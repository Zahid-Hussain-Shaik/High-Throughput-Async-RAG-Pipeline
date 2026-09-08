import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512, examples=["Operations handbook"])
    source: str | None = Field(default=None, max_length=2048)
    content: str = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    source: str | None
    content: str
    metadata: dict = Field(validation_alias="metadata_")
    created_at: datetime
