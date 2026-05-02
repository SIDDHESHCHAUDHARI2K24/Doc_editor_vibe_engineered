"""Pydantic schemas for document requests and responses."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, constr

class CreateDocumentRequest(BaseModel):
    title: constr(min_length=1, max_length=255)

class RenameDocumentRequest(BaseModel):
    title: constr(min_length=1, max_length=255)

class DocumentResponse(BaseModel):
    id: str
    title: str
    owner_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class PaginatedResponse(BaseModel):
    items: List[DocumentResponse]
    next_cursor: Optional[str] = None
