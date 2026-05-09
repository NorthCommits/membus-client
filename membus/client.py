"""
MemBus Python client.

Usage:
    from membus import MemBus, Scope

    bus = MemBus(
        adapter="memory",           # "memory" | "redis" | "supabase" | "chroma"
        default_scope_ids={
            "user": "user_123",
            "session": "sess_456",
            "agent": "agent_789",
            "org": "org_001",
        }
    )

    bus.write("username", "Alice", scope=Scope.USER)
    name = bus.read("username", scope=Scope.USER)
    bus.manage(scope=Scope.SESSION, operation="prune")
"""

from typing import Any, Optional, Union
import httpx

from membus.scopes import Scope

ScopeType = Union[Scope, str]
ManageOperation = Union["prune", "compress", "deduplicate"]  # type: ignore


class MemBusError(Exception):
    """Raised when the MemBus server returns an error."""


class MemBus:
    """
    Client for the MemBus memory server.

    Parameters
    ----------
    adapter : str
        Which storage backend to use for all operations.
        Options: "memory" (default), "redis", "supabase", "chroma".
        The adapter must be configured on the server side.
    server_url : str
        Base URL of the deployed MemBus server.
    api_key : str, optional
        API key for the server (must match MEMBUS_API_KEY on the server).
    default_scope_ids : dict, optional
        Default scope_id values so you don't have to pass them on every call.
        Keys: "user", "session", "agent", "org"
    timeout : float
        HTTP request timeout in seconds (default: 10).
    """

    DEFAULT_SERVER_URL = "https://membus-server.onrender.com"
    DEFAULT_API_KEY = "55792fcfad8ea963634f1044bf125d5bcd11c63c7009de0a2a8efc78b0343d5b549024ff46fc2f52cbd9667667d7eeae919f910db669405b4e05e4bcc9669c16"

    def __init__(
        self,
        adapter: str = "memory",
        server_url: str = DEFAULT_SERVER_URL,
        api_key: str = DEFAULT_API_KEY,
        default_scope_ids: Optional[dict[str, str]] = None,
        timeout: float = 10.0,
    ):
        self._adapter = adapter
        self._base = server_url.rstrip("/")
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["x-api-key"] = api_key
        self._scope_ids: dict[str, str] = default_scope_ids or {}
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_scope_id(self, scope: ScopeType, scope_id: Optional[str]) -> str:
        scope_str = scope.value if isinstance(scope, Scope) else scope
        if scope_id:
            return scope_id
        if scope_str in self._scope_ids:
            return self._scope_ids[scope_str]
        raise ValueError(
            f"No scope_id provided for scope={scope_str!r} and no default set. "
            "Pass scope_id= or set default_scope_ids in MemBus()."
        )

    def _http_client(self) -> httpx.Client:
        # trust_env=False prevents httpx from picking up SOCKS/HTTP proxy env vars
        return httpx.Client(timeout=self._timeout, trust_env=False)

    def _post(self, path: str, payload: dict) -> dict:
        with self._http_client() as client:
            resp = client.post(f"{self._base}{path}", json=payload, headers=self._headers)
        self._raise_for_status(resp)
        return resp.json()

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        with self._http_client() as client:
            resp = client.get(f"{self._base}{path}", params=params, headers=self._headers)
        self._raise_for_status(resp)
        return resp.json()

    def _raise_for_status(self, resp: httpx.Response):
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise MemBusError(f"[{resp.status_code}] {detail}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(
        self,
        key: str,
        value: Any,
        scope: ScopeType = Scope.SESSION,
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store a memory.

        Parameters
        ----------
        key       : Memory key (string)
        value     : Any JSON-serialisable value
        scope     : Scope enum or string ("user", "session", "agent", "org")
        scope_id  : ID for the scope. Uses default if set via default_scope_ids.
        namespace : Optional sub-namespace within the scope
        ttl       : Time-to-live in seconds. None means no expiry.

        Returns True on success.
        """
        scope_str = scope.value if isinstance(scope, Scope) else scope
        sid = self._resolve_scope_id(scope, scope_id)
        payload = {
            "key": key,
            "value": value,
            "scope": scope_str,
            "scope_id": sid,
            "namespace": namespace,
            "ttl": ttl,
            "adapter": self._adapter,
        }
        result = self._post("/memory/write", payload)
        return result.get("success", False)

    def read(
        self,
        key: str,
        scope: ScopeType = Scope.SESSION,
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a memory.

        Returns the stored value, or `default` if the key does not exist.
        """
        scope_str = scope.value if isinstance(scope, Scope) else scope
        sid = self._resolve_scope_id(scope, scope_id)
        payload = {
            "key": key,
            "scope": scope_str,
            "scope_id": sid,
            "namespace": namespace,
            "adapter": self._adapter,
        }
        result = self._post("/memory/read", payload)
        if not result.get("found"):
            return default
        return result.get("value")

    def manage(
        self,
        scope: ScopeType,
        operation: str = "prune",
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> dict:
        """
        Run a management operation on a scope's memories.

        Operations:
          - "prune"       : Remove empty/null memories
          - "deduplicate" : Remove memories with identical values
          - "compress"    : LLM-powered compression (requires OpenAI key on server)

        Returns a dict with `operation`, `affected`, and `detail`.
        """
        scope_str = scope.value if isinstance(scope, Scope) else scope
        sid = self._resolve_scope_id(scope, scope_id)
        payload = {
            "scope": scope_str,
            "scope_id": sid,
            "operation": operation,
            "namespace": namespace,
            "adapter": self._adapter,
        }
        return self._post("/memory/manage", payload)

    def flush(
        self,
        scope: ScopeType,
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> int:
        """
        Delete all memories in a scope. Returns count of deleted entries.
        """
        scope_str = scope.value if isinstance(scope, Scope) else scope
        sid = self._resolve_scope_id(scope, scope_id)
        payload = {
            "scope": scope_str,
            "scope_id": sid,
            "namespace": namespace,
            "adapter": self._adapter,
        }
        result = self._post("/memory/flush", payload)
        return result.get("deleted", 0)

    def stats(self) -> dict:
        """
        Return memory stats for the current adapter (total keys, breakdown by scope).
        """
        return self._get("/memory/stats", params={"adapter": self._adapter})

    def health(self) -> dict:
        """
        Check server health. Returns status and list of available adapters.
        """
        return self._get("/health")
