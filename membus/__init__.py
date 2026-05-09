"""
membus — Scoped memory for LLM agents. Install and go.

Quick start:
    from membus import MemBus, Scope

    bus = MemBus(
        server_url="https://your-membus.onrender.com",
        api_key="your-api-key",
        default_scope_ids={
            "user": "user_123",
            "session": "sess_456",
            "agent": "agent_789",
            "org": "org_001",
        },
    )

    bus.write("name", "Alice", scope=Scope.USER)
    name = bus.read("name", scope=Scope.USER)  # -> "Alice"
    bus.manage(scope=Scope.SESSION, operation="prune")
"""

from membus.client import MemBus, MemBusError
from membus.scopes import Scope

__all__ = ["MemBus", "MemBusError", "Scope"]
__version__ = "0.1.1"
