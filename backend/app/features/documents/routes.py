"""Document CRUD API routes (prefix: /api/v1/documents)."""
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from app.features.core.dependencies import DbDep
from app.features.core.security import require_session, require_doc_role, AuthenticatedSession
from app.features.core.settings import get_settings
from app.features.documents.services import DocumentService
from app.features.documents.schemas import (
    CreateDocumentRequest, RenameDocumentRequest,
    DocumentResponse, PaginatedResponse,
)

documents_router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@documents_router.post("", status_code=201)
async def create_document(
    payload: CreateDocumentRequest,
    db = DbDep,
    auth: AuthenticatedSession = Depends(require_session),
) -> DocumentResponse:
    svc = DocumentService(db)
    return await svc.create(auth.user.id, payload)

@documents_router.get("")
async def list_documents(
    scope: Literal["owned", "shared"] = "owned",
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db = DbDep,
    auth: AuthenticatedSession = Depends(require_session),
) -> PaginatedResponse:
    svc = DocumentService(db)
    if scope == "shared":
        return PaginatedResponse(items=[], next_cursor=None)
    return await svc.list_owned(auth.user.id, cursor, limit)

@documents_router.get("/{doc_id}")
async def get_document(
    doc_id: UUID,
    db = DbDep,
    ctx = Depends(require_doc_role("owner")),
) -> DocumentResponse:
    svc = DocumentService(db)
    return await svc.get(ctx.document)

@documents_router.patch("/{doc_id}")
async def rename_document(
    doc_id: UUID,
    payload: RenameDocumentRequest,
    db = DbDep,
    ctx = Depends(require_doc_role("owner")),
) -> DocumentResponse:
    svc = DocumentService(db)
    return await svc.rename(ctx.document, payload)

@documents_router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: UUID,
    db = DbDep,
    ctx = Depends(require_doc_role("owner")),
) -> Response:
    svc = DocumentService(db)
    await svc.soft_delete(ctx.document)
    return Response(status_code=204)


@documents_router.get("/{doc_id}/state", responses={
    200: {"content": {"application/octet-stream": {}}, "description": "Yjs binary state"},
    403: {"description": "Not authorized"},
    404: {"description": "Document not found"},
})
async def get_state(
    doc_id: UUID,
    role_ctx = Depends(require_doc_role("owner")),
    service: DocumentService = Depends(lambda db=DbDep: DocumentService(db)),
) -> Response:
    state = await service.get_state(doc_id)
    return Response(content=state or b"", media_type="application/octet-stream", headers={"Cache-Control": "no-store, private"})


@documents_router.put("/{doc_id}/state", status_code=204, responses={
    204: {"description": "State saved"},
    400: {"description": "Invalid state (sanitization failed)"},
    403: {"description": "Not authorized"},
    404: {"description": "Document not found"},
    413: {"description": "State too large"},
})
async def put_state(
    doc_id: UUID,
    request: Request,
    role_ctx = Depends(require_doc_role("owner")),
    service: DocumentService = Depends(lambda db=DbDep: DocumentService(db)),
) -> Response:
    settings = get_settings()
    content_length = int(request.headers.get("content-length", "0"))
    if content_length > settings.max_yjs_state_bytes:
        from app.features.core.errors import ValidationException
        raise ValidationException(
            code="STATE_TOO_LARGE",
            message=f"Document state exceeds maximum size of {settings.max_yjs_state_bytes} bytes",
            details={"limit": settings.max_yjs_state_bytes, "received": content_length},
        )
    body = await request.body()
    await service.set_state(doc_id, body)
    return Response(status_code=204)
