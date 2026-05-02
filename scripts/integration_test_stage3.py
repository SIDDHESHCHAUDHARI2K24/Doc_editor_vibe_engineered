"""Integration test for Stage 3 state endpoints using httpx."""
import httpx
import y_py as Y

BASE = "http://localhost:8002"


def encode_test_state(text: str = "hello world") -> bytes:
    """Create a valid Yjs binary state update."""
    doc = Y.YDoc()
    ytext = doc.get_text("quill")
    with doc.begin_transaction() as txn:
        ytext.insert(txn, 0, text)
    return bytes(Y.encode_state_as_update(doc))


def test_health():
    with httpx.Client() as c:
        r = c.get(f"{BASE}/health")
        assert r.status_code == 200
        print(f"  [PASS] Health: {r.json()['status']}")


def test_full_flow():
    c = httpx.Client()

    # Login
    r = c.post(f"{BASE}/api/v1/auth/login", json={
        "identifier": "alice@example.com",
        "password": "Password123!"
    })
    assert r.status_code == 200, f"Login: {r.status_code}"
    data = r.json()
    print(f"  [PASS] Login: {data['user']['email']}")

    # Get CSRF token from /me
    r = c.get(f"{BASE}/api/v1/auth/me")
    assert r.status_code == 200, f"Me: {r.status_code}"
    me_data = r.json()
    csrf_token = me_data.get("csrf_token", "")
    print(f"  [INFO] CSRF token: '{csrf_token[:8]}...'")

    # Create document
    r = c.post(f"{BASE}/api/v1/documents", json={"title": "Stage 3 Integration Test"},
               headers={"X-CSRF-Token": csrf_token})
    assert r.status_code == 201, f"Create: {r.status_code} {r.text}"
    doc = r.json()
    doc_id = doc["id"]
    print(f"  [PASS] Create doc: {doc_id[:8]}... - {doc['title']}")

    # PUT valid Yjs state
    valid_state = encode_test_state("hello world")
    r = c.put(
        f"{BASE}/api/v1/documents/{doc_id}/state",
        content=valid_state,
        headers={"Content-Type": "application/octet-stream", "X-CSRF-Token": csrf_token}
    )
    assert r.status_code == 204, f"PUT state: {r.status_code} {r.text}"
    print(f"  [PASS] PUT valid Yjs state: 204")

    # GET state — verify roundtrip
    r = c.get(f"{BASE}/api/v1/documents/{doc_id}/state")
    assert r.status_code == 200
    assert len(r.content) > 0, "State should not be empty"
    # Verify roundtrip: decode what we got back
    decoded_doc = Y.YDoc()
    Y.apply_update(decoded_doc, r.content)
    decoded_text = str(decoded_doc.get_text("quill"))
    assert decoded_text == "hello world", f"Roundtrip mismatch: '{decoded_text}'"
    print(f"  [PASS] GET state roundtrip: '{decoded_text}'")

    # PUT unsafe state (invalid binary)
    r = c.put(
        f"{BASE}/api/v1/documents/{doc_id}/state",
        content=b"\x00\x01\x02",
        headers={"Content-Type": "application/octet-stream", "X-CSRF-Token": csrf_token}
    )
    assert r.status_code in (400, 422), f"Unsafe: expected 400/422, got {r.status_code}"
    print(f"  [PASS] PUT invalid bytes rejected: {r.status_code}")

    # Unedited doc GET state
    r = c.post(f"{BASE}/api/v1/documents", json={"title": "Fresh Doc"},
               headers={"X-CSRF-Token": csrf_token})
    assert r.status_code == 201
    fresh_id = r.json()["id"]
    r = c.get(f"{BASE}/api/v1/documents/{fresh_id}/state")
    assert r.status_code == 200 and len(r.content) == 0
    print(f"  [PASS] GET unedited state: empty OK")
    c.delete(f"{BASE}/api/v1/documents/{fresh_id}",
             headers={"X-CSRF-Token": csrf_token})

    # Non-owner access
    bob = httpx.Client()
    r = bob.post(f"{BASE}/api/v1/auth/login", json={
        "identifier": "bob@example.com",
        "password": "Password123!"
    })
    assert r.status_code == 200
    r = bob.get(f"{BASE}/api/v1/documents/{doc_id}/state")
    assert r.status_code == 403
    print(f"  [PASS] Non-owner GET state: 403")

    # Soft-deleted doc
    r = c.post(f"{BASE}/api/v1/documents", json={"title": "To Delete"},
               headers={"X-CSRF-Token": csrf_token})
    del_id = r.json()["id"]
    c.delete(f"{BASE}/api/v1/documents/{del_id}",
             headers={"X-CSRF-Token": csrf_token})
    r = c.get(f"{BASE}/api/v1/documents/{del_id}/state")
    assert r.status_code == 404
    print(f"  [PASS] Soft-deleted GET state: 404")

    # CSRF enforcement
    carol = httpx.Client()
    r = carol.post(f"{BASE}/api/v1/auth/login", json={
        "identifier": "carol@example.com",
        "password": "Password123!"
    })
    assert r.status_code == 200
    r = carol.get(f"{BASE}/api/v1/auth/me")
    carol_csrf = r.json().get("csrf_token", "")
    r = carol.put(
        f"{BASE}/api/v1/documents/{doc_id}/state",
        content=valid_state,
        headers={"Content-Type": "application/octet-stream", "X-CSRF-Token": carol_csrf}
    )
    assert r.status_code == 403, f"Carol write: expected 403, got {r.status_code}"
    print(f"  [PASS] Non-owner PUT state: 403")

    # Cleanup
    c.delete(f"{BASE}/api/v1/documents/{doc_id}",
             headers={"X-CSRF-Token": csrf_token})

    c.close()
    bob.close()
    carol.close()
    print(f"\nAll integration tests passed!")


if __name__ == "__main__":
    print("Stage 3 Integration Tests")
    print("=========================")
    test_health()
    test_full_flow()
