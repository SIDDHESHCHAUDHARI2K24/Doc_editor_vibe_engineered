"""Tests for core/sanitize.py — Delta validation, HTML sanitization, Yjs decode."""
import y_py as Y
import pytest
from app.features.core.sanitize import (
    validate_delta_ops, sanitize_html, UnsafeContentException,
    decode_state, extract_text_content,
    ALLOWED_INLINE_ATTRS, ALLOWED_BLOCK_ATTRS,
)


# --- Delta op validation tests ---

class TestValidateDeltaOps:
    def test_passes_plain_text(self):
        validate_delta_ops([{"insert": "hello world"}])

    def test_passes_bold(self):
        validate_delta_ops([{"insert": "hello", "attributes": {"bold": True}}])

    def test_passes_italic(self):
        validate_delta_ops([{"insert": "hello", "attributes": {"italic": True}}])

    def test_passes_underline(self):
        validate_delta_ops([{"insert": "hello", "attributes": {"underline": True}}])

    def test_passes_strikethrough(self):
        validate_delta_ops([{"insert": "hello", "attributes": {"strike": True}}])

    def test_passes_safe_link(self):
        validate_delta_ops([{"insert": "link", "attributes": {"link": "https://example.com"}}])
        validate_delta_ops([{"insert": "link", "attributes": {"link": "http://example.com"}}])
        validate_delta_ops([{"insert": "link", "attributes": {"link": "mailto:test@example.com"}}])

    def test_passes_header_1_to_3(self):
        for level in (1, 2, 3):
            validate_delta_ops([{"insert": "\n", "attributes": {"header": level}}])

    def test_passes_list_bullet(self):
        validate_delta_ops([{"insert": "\n", "attributes": {"list": "bullet"}}])

    def test_passes_list_ordered(self):
        validate_delta_ops([{"insert": "\n", "attributes": {"list": "ordered"}}])

    def test_rejects_forbidden_inline_attr(self):
        with pytest.raises(UnsafeContentException) as exc:
            validate_delta_ops([{"insert": "x", "attributes": {"color": "red"}}])
        assert exc.value.details["attr"] == "color"

    def test_rejects_forbidden_block_attr(self):
        with pytest.raises(UnsafeContentException) as exc:
            validate_delta_ops([{"insert": "\n", "attributes": {"align": "center"}}])
        assert exc.value.details["attr"] == "align"

    def test_rejects_javascript_url(self):
        with pytest.raises(UnsafeContentException) as exc:
            validate_delta_ops([{"insert": "link", "attributes": {"link": "javascript:alert(1)"}}])
        assert exc.value.details["attr"] == "link"

    def test_rejects_data_url(self):
        with pytest.raises(UnsafeContentException):
            validate_delta_ops([{"insert": "link", "attributes": {"link": "data:text/html,hello"}}])

    def test_rejects_header_4(self):
        with pytest.raises(UnsafeContentException) as exc:
            validate_delta_ops([{"insert": "\n", "attributes": {"header": 4}}])
        assert exc.value.details["attr"] == "header"

    def test_rejects_invalid_list_value(self):
        with pytest.raises(UnsafeContentException) as exc:
            validate_delta_ops([{"insert": "\n", "attributes": {"list": "checklist"}}])
        assert exc.value.details["attr"] == "list"

    def test_bold_with_false_is_ok(self):
        # False means explicitly un-setting the format
        validate_delta_ops([{"insert": "hello", "attributes": {"bold": False}}])


# --- HTML sanitization tests ---

class TestSanitizeHtml:
    def test_passes_safe_html(self):
        result = sanitize_html("<p>Hello <strong>world</strong></p>")
        assert "<p>Hello <strong>world</strong></p>" in result

    def test_strips_script_tag(self):
        result = sanitize_html("<script>alert(1)</script><p>Hi</p>")
        assert "<script>" not in result
        assert "<p>Hi</p>" in result

    def test_strips_unsafe_href(self):
        result = sanitize_html('<a href="javascript:foo">x</a>')
        assert "javascript" not in result

    def test_keeps_allowed_tags(self):
        for tag in ("p", "br", "strong", "b", "em", "i", "u", "h1", "h2", "h3", "ul", "ol", "li"):
            html = f"<{tag}>content</{tag}>"
            result = sanitize_html(html)
            assert f"<{tag}>" in result or f"<{tag} " in result


# --- Yjs decode tests ---

class TestYjsDecode:
    def test_decode_empty_bytes(self):
        doc = decode_state(b"")
        assert doc is not None
        # Empty YDoc should still have the "quill" text type accessible
        ytext = doc.get_text("quill")
        assert str(ytext) == ""

    def test_decode_malformed_bytes(self):
        from app.features.core.errors import ValidationException
        with pytest.raises(ValidationException) as exc:
            decode_state(b"\x00\x01\x02\x03\x04")  # random bytes
        assert exc.value.code == "INVALID_YJS_STATE"

    def test_decode_valid_update(self):
        # Create a valid Yjs update
        doc = Y.YDoc()
        ytext = doc.get_text("quill")
        with doc.begin_transaction() as txn:
            ytext.insert(txn, 0, "test content")
        update = Y.encode_state_as_update(doc)

        decoded = decode_state(update)
        result = str(decoded.get_text("quill"))
        assert result == "test content"

    def test_extract_text_content(self):
        doc = Y.YDoc()
        ytext = doc.get_text("quill")
        with doc.begin_transaction() as txn:
            ytext.insert(txn, 0, "hello")
            ytext.insert(txn, 5, " world", {"bold": True})

        text = extract_text_content(doc)
        assert "hello" in text
        assert "world" in text
