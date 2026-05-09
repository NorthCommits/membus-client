"""
Unit tests for the MemBus client.
Uses respx to mock the HTTP calls — no server required.
"""

import pytest
import respx
import httpx
from membus import MemBus, Scope


BASE_URL = "https://membus.test"

BUS = MemBus(
    server_url=BASE_URL,
    api_key="test-key",
    default_scope_ids={"user": "u1", "session": "s1", "agent": "a1", "org": "o1"},
)


@respx.mock
def test_write_success():
    respx.post(f"{BASE_URL}/memory/write").mock(
        return_value=httpx.Response(200, json={"success": True, "key": "name", "scope": "user", "scope_id": "u1"})
    )
    result = BUS.write("name", "Alice", scope=Scope.USER)
    assert result is True


@respx.mock
def test_read_found():
    respx.post(f"{BASE_URL}/memory/read").mock(
        return_value=httpx.Response(200, json={"key": "name", "value": "Alice", "scope": "user", "scope_id": "u1", "found": True})
    )
    value = BUS.read("name", scope=Scope.USER)
    assert value == "Alice"


@respx.mock
def test_read_not_found_returns_default():
    respx.post(f"{BASE_URL}/memory/read").mock(
        return_value=httpx.Response(200, json={"key": "missing", "value": None, "scope": "user", "scope_id": "u1", "found": False})
    )
    value = BUS.read("missing", scope=Scope.USER, default="fallback")
    assert value == "fallback"


@respx.mock
def test_manage_prune():
    respx.post(f"{BASE_URL}/memory/manage").mock(
        return_value=httpx.Response(200, json={
            "operation": "prune", "scope": "session", "scope_id": "s1", "affected": 3, "detail": "Pruned 3 empty/null memories."
        })
    )
    result = BUS.manage(scope=Scope.SESSION, operation="prune")
    assert result["affected"] == 3


@respx.mock
def test_flush():
    respx.post(f"{BASE_URL}/memory/flush").mock(
        return_value=httpx.Response(200, json={"success": True, "deleted": 5})
    )
    deleted = BUS.flush(scope=Scope.SESSION)
    assert deleted == 5


@respx.mock
def test_stats():
    respx.get(f"{BASE_URL}/memory/stats").mock(
        return_value=httpx.Response(200, json={"total_keys": 10, "by_scope": {"user": 4, "session": 6}, "adapter": "memory"})
    )
    data = BUS.stats()
    assert data["total_keys"] == 10
    assert data["adapter"] == "memory"


def test_missing_scope_id_raises():
    bus = MemBus(server_url=BASE_URL)  # no default_scope_ids
    with pytest.raises(ValueError, match="No scope_id provided"):
        bus.write("key", "val", scope=Scope.USER)
