"""Shared security dependencies: session validation and document RBAC."""
from typing import Literal
from uuid import UUID

from fastapi import Depends, Request

from app.features.core.errors import AuthenticationException, NotFoundException, PermissionDeniedException
from app.features.core.settings import get_settings
from app.features.core.dependencies import DbDep
from app.features.auth.session_store import session_store, SessionData
from app.features.auth.models import User
from app.features.auth.repositories import UserRepository

settings = get_settings()


class AuthenticatedSession:
    def __init__(self, user: User, session: SessionData):
        self.user = user
        self.session = session


async def require_session(request: Request, db=DbDep) -> AuthenticatedSession:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise AuthenticationException(message="Missing session cookie")
    data = await session_store.get(token)
    if not data:
        raise AuthenticationException(message="Invalid or expired session")
    repo = UserRepository(db)
    user = await repo.get_by_id(data.user_id)
    if not user:
        raise AuthenticationException(message="User not found")
    return AuthenticatedSession(user=user, session=data)


ROLE_HIERARCHY = {"viewer": 0, "editor": 1, "owner": 2}


def require_doc_role(min_role: Literal["viewer", "editor", "owner"]):
    async def dep(
        doc_id: UUID,
        session: AuthenticatedSession = Depends(require_session),
        db=DbDep,
    ):
        from app.features.documents.repositories import DocumentRepository

        repo = DocumentRepository(db)
        doc = await repo.get_active(doc_id)
        if not doc:
            raise NotFoundException(message="Document not found", details={"document_id": str(doc_id)})
        user_role: str | None = None
        if str(doc.owner_id) == str(session.user.id):
            user_role = "owner"
        if user_role is None or ROLE_HIERARCHY[user_role] < ROLE_HIERARCHY[min_role]:
            raise PermissionDeniedException(message="Insufficient role for this operation")

        class DocumentRoleContext:
            def __init__(self, document, user_role, session):
                self.document = document
                self.user_role = user_role
                self.session = session

        return DocumentRoleContext(document=doc, user_role=user_role, session=session)

    return dep
