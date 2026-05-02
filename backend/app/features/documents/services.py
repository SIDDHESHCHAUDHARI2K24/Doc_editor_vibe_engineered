"""Document service layer — business logic."""
import asyncio
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.documents.repositories import DocumentRepository
from app.features.documents.schemas import (
    CreateDocumentRequest, RenameDocumentRequest,
    DocumentResponse, PaginatedResponse,
)
from app.features.core.errors import ValidationException
from app.features.core.pagination import encode_cursor, decode_cursor

class DocumentService:
    def __init__(self, db: AsyncSession):
        self.repo = DocumentRepository(db)
    
    def _to_response(self, doc) -> DocumentResponse:
        return DocumentResponse(
            id=str(doc.id),
            title=doc.title,
            owner_id=str(doc.owner_id),
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            deleted_at=doc.deleted_at,
        )
    
    def _validate_title(self, title: str) -> str:
        title = title.strip()
        if not title:
            raise ValidationException(message="Title cannot be empty")
        if len(title) > 255:
            raise ValidationException(message="Title cannot exceed 255 characters")
        return title
    
    async def create(self, owner_id: UUID, request: CreateDocumentRequest) -> DocumentResponse:
        title = self._validate_title(request.title)
        doc = await self.repo.create(owner_id, title)
        # Audit log placeholder (full implementation in Stage 4)
        return self._to_response(doc)
    
    async def list_owned(self, owner_id: UUID, cursor_str: str | None, limit: int) -> PaginatedResponse:
        cursor = None
        if cursor_str:
            decoded = decode_cursor(cursor_str)
            cursor = (decoded["updated_at"], decoded["id"])
        
        results = await self.repo.list_owned(owner_id, cursor=cursor, limit=limit)
        
        has_more = len(results) > limit
        items = results[:limit]
        
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_cursor(last.updated_at, last.id)
        
        return PaginatedResponse(
            items=[self._to_response(d) for d in items],
            next_cursor=next_cursor,
        )
    
    async def get(self, doc) -> DocumentResponse:
        return self._to_response(doc)
    
    async def rename(self, doc, request: RenameDocumentRequest) -> DocumentResponse:
        title = self._validate_title(request.title)
        updated = await self.repo.rename(doc.id, title)
        # Audit log
        from app.features.core.audit import log
        await log(
            # Note: actor_user_id will be set by the route handler
            actor_user_id=doc.owner_id,
            action="document.renamed",
            target_type="document",
            target_id=doc.id,
            metadata={"old_title": doc.title, "new_title": title},
        )
        return self._to_response(updated)
    
    async def soft_delete(self, doc) -> None:
        await self.repo.soft_delete(doc.id)
        from app.features.core.audit import log
        await log(
            actor_user_id=doc.owner_id,
            action="document.deleted",
            target_type="document",
            target_id=doc.id,
            metadata={"title": doc.title},
        )

    async def get_state(self, doc_id: UUID) -> bytes | None:
        """Get Yjs state bytes for a document."""
        return await self.repo.get_state(doc_id)

    async def set_state(self, doc_id: UUID, state_bytes: bytes) -> None:
        """Persist Yjs state bytes for a document, with sanitization."""
        if state_bytes:
            from app.features.core.sanitize import decode_state, extract_text_content

            def _decode_and_extract(data: bytes) -> str:
                doc = decode_state(data)
                return extract_text_content(doc)

            text = await asyncio.to_thread(_decode_and_extract, state_bytes)
            for scheme in ('javascript:', 'data:', 'vbscript:', 'file:'):
                if scheme in text.lower():
                    raise ValidationException(
                        code="UNSAFE_CONTENT",
                        message="Document contains unsafe content",
                        details={"scheme": scheme},
                    )
        await self.repo.set_state(doc_id, state_bytes)
