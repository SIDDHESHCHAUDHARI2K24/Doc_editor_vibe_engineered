"""Cursor-based pagination helpers."""
import base64
import json
from datetime import datetime
from uuid import UUID
from typing import Any

def encode_cursor(updated_at: datetime, doc_id: UUID) -> str:
    """Encode (updated_at, doc_id) as a base64-encoded JSON string."""
    payload = json.dumps({
        "t": updated_at.isoformat(),
        "id": str(doc_id),
    })
    return base64.urlsafe_b64encode(payload.encode()).decode()

def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a cursor string back to a dict with 't' and 'id' keys."""
    payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    return {
        "updated_at": datetime.fromisoformat(payload["t"]),
        "id": UUID(payload["id"]),
    }
