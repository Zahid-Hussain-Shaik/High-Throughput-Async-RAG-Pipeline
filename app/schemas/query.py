from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000, examples=["What is the incident escalation policy?"])
    top_k: int | None = Field(default=None, ge=1, le=20)
