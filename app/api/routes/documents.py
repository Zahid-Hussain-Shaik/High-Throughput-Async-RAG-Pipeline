import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_document_service, get_session
from app.schemas.document import DocumentCreate, DocumentRead
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(payload: DocumentCreate, request: Request, session: AsyncSession = Depends(get_session), service: DocumentService = Depends(get_document_service)):
    if len(payload.content) > request.app.state.settings.max_document_chars: raise HTTPException(422, "Document exceeds maximum size")
    return await service.create(session, payload)

@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: uuid.UUID, session: AsyncSession = Depends(get_session), service: DocumentService = Depends(get_document_service)):
    document = await service.get(session, document_id)
    if not document: raise HTTPException(404, "Document not found")
    return document
