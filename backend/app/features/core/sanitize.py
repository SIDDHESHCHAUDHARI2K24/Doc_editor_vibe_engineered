"""Server-side content sanitization for Yjs Delta operations and HTML.

Mirrors the Stage 3 formatting scope. Reusable by Stage 5 import flow.
"""

import logging
from urllib.parse import urlparse

import bleach
import y_py as Y

from app.features.core.errors import ValidationException

logger = logging.getLogger(__name__)

YTEXT_KEY = "quill"

# --- Delta attribute allowlist (matches Stage 3 formatting scope) ---

ALLOWED_INLINE_ATTRS = {"bold", "italic", "underline", "strike", "link"}
ALLOWED_BLOCK_ATTRS = {"header", "list"}
ALLOWED_HEADER_VALUES = {1, 2, 3}
ALLOWED_LIST_VALUES = {"ordered", "bullet"}

ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


class UnsafeContentException(ValidationException):
    """Raised when document content contains forbidden attributes or unsafe URLs."""

    def __init__(self, code: str = "UNSAFE_CONTENT", message: str = "Document contains unsafe content", details: dict | None = None):
        super().__init__(code=code, message=message, details=details or {})


# --- Yjs decode helpers ---

def decode_state(state: bytes) -> Y.YDoc:
    """Decode a Yjs state update into a YDoc. Returns a fresh empty YDoc for empty input."""
    doc = Y.YDoc()
    if not state:
        return doc
    try:
        Y.apply_update(doc, state)
    except Exception as e:
        raise ValidationException(
            code="INVALID_YJS_STATE",
            message="Document state could not be decoded",
            details={"underlying": str(e)},
        ) from e
    return doc


def extract_text_content(doc: Y.YDoc, ytext_key: str = YTEXT_KEY) -> str:
    """Extract plain text content from a YDoc's shared text for validation.

    y-py 0.7.0a1 does not expose to_delta(), so we work with text content
    for URL safety checks. Full Delta-op validation is still available via
    validate_delta_ops() for paths that produce Delta ops directly (e.g., S5 import).
    """
    ytext: Y.YText = doc.get_text(ytext_key)
    return str(ytext)


# --- Delta op validation ---

def _is_safe_url(url: str) -> bool:
    """Check that a URL uses an allowed scheme."""
    parsed = urlparse(url)
    return parsed.scheme in ALLOWED_URL_SCHEMES


def validate_delta_ops(ops: list[dict]) -> None:
    """Validate Delta operations against the allowed attribute set.
    
    Raises UnsafeContentException if any op contains a forbidden attribute
    or an unsafe URL.
    """
    for i, op in enumerate(ops):
        attrs = op.get("attributes")
        if not attrs:
            continue
        for k, v in attrs.items():
            if k in ALLOWED_INLINE_ATTRS:
                if k == "link":
                    if not isinstance(v, str) or not _is_safe_url(v):
                        raise UnsafeContentException(
                            details={"attr": k, "value": v, "op_index": i}
                        )
                elif k in {"bold", "italic", "underline", "strike"}:
                    if v not in (True, None, False):
                        raise UnsafeContentException(
                            details={"attr": k, "value": v, "op_index": i}
                        )
            elif k in ALLOWED_BLOCK_ATTRS:
                if k == "header" and v not in ALLOWED_HEADER_VALUES:
                    raise UnsafeContentException(
                        details={"attr": k, "value": v, "op_index": i}
                    )
                if k == "list" and v not in ALLOWED_LIST_VALUES:
                    raise UnsafeContentException(
                        details={"attr": k, "value": v, "op_index": i}
                    )
            else:
                raise UnsafeContentException(
                    details={"attr": k, "value": v, "op_index": i}
                )


# --- HTML sanitization (reusable for Stage 5 import) ---

ALLOWED_HTML_TAGS = {"p", "br", "strong", "b", "em", "i", "u", "s", "strike", "h1", "h2", "h3", "ul", "ol", "li", "a"}
ALLOWED_HTML_ATTRS = {"a": ["href", "title"]}


def sanitize_html(html: str) -> str:
    """Clean HTML to allowed tags/attributes matching our Quill formatting scope."""
    return bleach.clean(
        html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRS,
        protocols=list(ALLOWED_URL_SCHEMES),
        strip=True,
    )
