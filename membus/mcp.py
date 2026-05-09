"""
MemBus MCP Interface.

Exposes read / write / manage / flush as MCP-compatible tools so that
any MCP-aware LLM agent can call them directly.

Usage (standalone MCP server):
    from membus import MemBus
    from membus.mcp import MemBusMCPServer

    bus = MemBus(
        server_url="https://your-membus.onrender.com",
        api_key="...",
        default_scope_ids={"user": "u1", "session": "s1", "agent": "a1", "org": "o1"},
    )

    server = MemBusMCPServer(bus, name="membus")
    server.run()  # starts stdio MCP server

Usage (register tools into an existing FastMCP server):
    from membus.mcp import register_membus_tools
    register_membus_tools(mcp_server, bus)
"""

from typing import Any, Optional
from membus.client import MemBus


def register_membus_tools(mcp, bus: MemBus):
    """
    Register all MemBus memory tools onto an existing MCP server instance.
    `mcp` must be a FastMCP (or compatible) server with a `.tool()` decorator.
    """

    @mcp.tool()
    def memory_write(
        key: str,
        value: Any,
        scope: str = "session",
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> dict:
        """
        Store a memory in MemBus.

        Args:
            key: The memory key to store under.
            value: Any JSON-serialisable value to store.
            scope: One of 'user', 'session', 'agent', 'org'.
            scope_id: ID for the scope (uses default if not provided).
            namespace: Optional sub-namespace within the scope.
            ttl: Time-to-live in seconds. Omit for no expiry.

        Returns:
            {"success": true, "key": "...", "scope": "..."}
        """
        success = bus.write(key=key, value=value, scope=scope, scope_id=scope_id, namespace=namespace, ttl=ttl)
        return {"success": success, "key": key, "scope": scope}

    @mcp.tool()
    def memory_read(
        key: str,
        scope: str = "session",
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> dict:
        """
        Retrieve a memory from MemBus.

        Args:
            key: The memory key to retrieve.
            scope: One of 'user', 'session', 'agent', 'org'.
            scope_id: ID for the scope (uses default if not provided).
            namespace: Optional sub-namespace.

        Returns:
            {"key": "...", "value": <stored value or null>, "found": true/false}
        """
        value = bus.read(key=key, scope=scope, scope_id=scope_id, namespace=namespace)
        return {"key": key, "value": value, "found": value is not None}

    @mcp.tool()
    def memory_manage(
        scope: str,
        operation: str = "prune",
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> dict:
        """
        Run a management operation on a scope's memories.

        Args:
            scope: One of 'user', 'session', 'agent', 'org'.
            operation: One of 'prune', 'deduplicate', 'compress'.
            scope_id: ID for the scope (uses default if not provided).
            namespace: Optional sub-namespace.

        Returns:
            {"operation": "...", "affected": <int>, "detail": "..."}
        """
        return bus.manage(scope=scope, operation=operation, scope_id=scope_id, namespace=namespace)

    @mcp.tool()
    def memory_flush(
        scope: str,
        scope_id: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> dict:
        """
        Delete all memories in a scope.

        Args:
            scope: One of 'user', 'session', 'agent', 'org'.
            scope_id: ID for the scope (uses default if not provided).
            namespace: Optional sub-namespace to restrict the flush.

        Returns:
            {"deleted": <int>}
        """
        deleted = bus.flush(scope=scope, scope_id=scope_id, namespace=namespace)
        return {"deleted": deleted}

    @mcp.tool()
    def memory_stats() -> dict:
        """
        Return memory stats from the MemBus server.

        Returns:
            {"total_keys": <int>, "by_scope": {...}, "adapter": "..."}
        """
        return bus.stats()


class MemBusMCPServer:
    """
    Standalone MCP server that exposes MemBus tools over stdio.

    Requires the `mcp` package (pip install mcp).
    """

    def __init__(self, bus: MemBus, name: str = "membus"):
        self._bus = bus
        self._name = name

    def run(self):
        """Start the MCP server (blocks, communicates over stdio)."""
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError:
            raise ImportError(
                "The 'mcp' package is required to run the MCP server. "
                "Install it with: pip install mcp"
            )

        mcp = FastMCP(self._name)
        register_membus_tools(mcp, self._bus)
        mcp.run()
