"""Document repository with cursor-based pagination."""
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.documents.models import Document

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, owner_id: UUID, title: str) -> Document:
        doc = Document(owner_id=owner_id, title=title)
        self.session.add(doc)
        await self.session.flush()
        return doc
    
    async def get_active(self, doc_id: UUID) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()
    
    async def list_owned(self, owner_id: UUID, cursor: tuple[datetime, UUID] | None = None, limit: int = 20) -> list[Document]:
        query = select(Document).where(
            Document.owner_id == owner_id,
            Document.deleted_at == None,
        )
        if cursor:
            updated_at_cursor, id_cursor = cursor
            query = query.where(
                and_(
                    or_(
                        Document.updated_at < updated_at_cursor,
                        and_(Document.updated_at == updated_at_cursor, Document.id < id_cursor)
                    )
                )
            )
        query = query.order_by(
            desc(Document.updated_at),
            desc(Document.id),
        ).limit(limit + 1)  # fetch one extra to determine if there are more
        
        results = list(await self.session.execute(query))
        return [r[0] for r in results]  # extract Document objects
    
    async def rename(self, doc_id: UUID, title: str) -> Document | None:
        doc = await self.get_active(doc_id)
        if doc:
            doc.title = title
            # updated_at is auto-handled by onupdate
        return doc
    
    async def soft_delete(self, doc_id: UUID) -> None:
        doc = await self.get_active(doc_id)
        if doc:
            from datetime import timezone
            doc.deleted_at = datetime.now(timezone.utc)

    async def get_state(self, doc_id: UUID) -> bytes | None:
        """Get the Yjs state bytes for a document. Returns None if never persisted."""
        from sqlalchemy import select
        stmt = select(Document.yjs_state).where(Document.id == doc_id, Document.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        row = result.first()
        return row[0] if row else None

    async def set_state(self, doc_id: UUID, state: bytes) -> None:
        """Persist Yjs state bytes for a document. Uses bulk UPDATE for performance."""
        from sqlalchemy import update, func
        stmt = (
            update(Document)
            .where(Document.id == doc_id, Document.deleted_at.is_(None))
            .values(yjs_state=state, updated_at=func.now())
        )
        await self.session.execute(stmt)
