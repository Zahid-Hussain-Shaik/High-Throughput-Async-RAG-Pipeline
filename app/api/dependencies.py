from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request):
    async with request.app.state.session_factory() as session:
        yield session


def get_document_service(request: Request): return request.app.state.document_service
def get_rag_service(request: Request): return request.app.state.rag_service
def get_cache(request: Request): return request.app.state.cache
