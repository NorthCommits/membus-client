<div align="center">

```
 ███╗   ███╗███████╗███╗   ███╗██████╗ ██╗   ██╗███████╗
 ████╗ ████║██╔════╝████╗ ████║██╔══██╗██║   ██║██╔════╝
 ██╔████╔██║█████╗  ██╔████╔██║██████╔╝██║   ██║███████╗
 ██║╚██╔╝██║██╔══╝  ██║╚██╔╝██║██╔══██╗██║   ██║╚════██║
 ██║ ╚═╝ ██║███████╗██║ ╚═╝ ██║██████╔╝╚██████╔╝███████║
 ╚═╝     ╚═╝╚══════╝╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚══════╝
```

**Scoped memory for LLM agents. Install and go.**

[![PyPI version](https://img.shields.io/pypi/v/membus?color=cyan&style=flat-square)](https://pypi.org/project/membus)
[![Python](https://img.shields.io/pypi/pyversions/membus?style=flat-square)](https://pypi.org/project/membus)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![MCP Native](https://img.shields.io/badge/MCP-native-blueviolet?style=flat-square)](#mcp-interface)

</div>

---

Most agent frameworks treat memory as an afterthought — a global dict, a hacked-together file, or nothing at all. **MemBus fixes that.**

It gives your agents a clean, scoped memory layer backed by a real server — so memories survive restarts, agents can share context, and you can swap the storage backend without touching a line of agent code.

---

## Install

```bash
pip install membus
```

After installing, type `membus` in your terminal to open the interactive quick-start guide.

---

## How it works

MemBus has two parts:

| Part | What it does | Where it runs |
|------|-------------|---------------|
| **membus-server** | Stores memories, handles scopes, auth, and adapters | Your server (Render, Railway, self-hosted) |
| **membus** (this package) | Python client — read, write, manage memories | Your agent code |

The client talks to the server over HTTP. Swap the server's adapter in one env var — no client code changes ever.

---

## Quick Start

```python
from membus import MemBus, Scope

bus = MemBus()  # uses your deployed server by default

# Store something
bus.write("user_name", "Alice", scope=Scope.USER, scope_id="user_123")

# Get it back — anywhere, any agent
name = bus.read("user_name", scope=Scope.USER, scope_id="user_123")
# → "Alice"

# Clean up a session when it ends
bus.manage(scope=Scope.SESSION, operation="prune", scope_id="sess_456")
```

---

## Memory Scopes

The four scopes are the heart of MemBus. Each one answers the question: *who should remember this, and for how long?*

| Scope | Lifetime | Use it for |
|-------|----------|-----------|
| `user` | Forever (until deleted) | Preferences, name, history — anything tied to a person |
| `session` | One conversation | Scratchpad state, context window overflow |
| `agent` | Long-lived | An agent's private notes, persona, learned behaviours |
| `org` | Shared across the team | Research findings, shared context, team knowledge |

```python
# Each scope is fully isolated — same key, different scope = different memory
bus.write("status", "active",   scope=Scope.USER,    scope_id="u1")
bus.write("status", "thinking", scope=Scope.SESSION,  scope_id="s1")
bus.write("status", "idle",     scope=Scope.AGENT,    scope_id="researcher")
```

---

## Storage Adapters

Your server decides where memories actually live. The client doesn't care — it just calls the API.

| Adapter | Backed by | Survives restarts | Best for |
|---------|-----------|:-----------------:|----------|
| `memory` | RAM | ❌ | Dev & testing — zero infra |
| `redis` | Redis | ✅ | Fast, session-friendly production |
| `supabase` | Postgres | ✅ | Persistent, Postgres-backed |
| `chroma` | ChromaDB | ✅ | Semantic / vector memory |

Switch adapters in **one line** on your server:

```bash
# In your server's .env
MEMBUS_ADAPTER=supabase
```

No client code changes. Ever.

You can also declare which adapter you expect in your client code — MemBus will warn you if there's a mismatch:

```python
bus = MemBus(expected_adapter="supabase")
bus.health()
# ⚠ UserWarning: expected 'supabase' but server is running 'memory'
```

---

## Operations

### `write` — store a memory

```python
bus.write(
    key="model_preference",
    value="gpt-4o",
    scope=Scope.USER,
    scope_id="user_123",
    ttl=3600,  # optional: expire in 1 hour
)
```

### `read` — retrieve a memory

```python
model = bus.read(
    key="model_preference",
    scope=Scope.USER,
    scope_id="user_123",
    default="gpt-4o-mini",  # fallback if not found
)
```

### `manage` — keep memory clean

```python
# Remove null/empty memories
bus.manage(scope=Scope.SESSION, operation="prune", scope_id="s1")

# Remove exact duplicates
bus.manage(scope=Scope.SESSION, operation="deduplicate", scope_id="s1")

# LLM-powered compression (requires OpenAI key on server)
bus.manage(scope=Scope.SESSION, operation="compress", scope_id="s1")
```

### `flush` — wipe a scope

```python
deleted = bus.flush(scope=Scope.SESSION, scope_id="sess_456")
# → 12
```

### `stats` — see what's stored

```python
bus.stats()
# → {"total_keys": 42, "by_scope": {"user": 10, "session": 5, "agent": 20, "org": 7}, "adapter": "supabase"}
```

---

## MCP Interface

MemBus is MCP-native. Expose all memory operations as tools that any MCP-compatible agent can call directly.

**Standalone MCP server:**

```python
from membus import MemBus
from membus.mcp import MemBusMCPServer

bus = MemBus(
    default_scope_ids={"user": "u1", "session": "s1", "agent": "my_agent", "org": "team"},
)

server = MemBusMCPServer(bus, name="membus")
server.run()  # stdio — plug into Claude, AutoGen, CrewAI, or any MCP host
```

**Register into an existing FastMCP server:**

```python
from membus.mcp import register_membus_tools

register_membus_tools(my_existing_mcp_server, bus)
# Adds: memory_read, memory_write, memory_manage, memory_flush, memory_stats
```

---

## Multi-Agent Example (AutoGen)

```python
from membus import MemBus, Scope
from membus.mcp import register_membus_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool

bus = MemBus()

# Researcher stores findings
bus.write("findings", "LLMs excel at reasoning tasks", scope=Scope.ORG, scope_id="team")

# Analyst reads them — even in a separate process or server
findings = bus.read("findings", scope=Scope.ORG, scope_id="team")
```

Memories flow between agents through MemBus — not through chat history. That means they survive context resets, cross-process boundaries, and outlive any single conversation.

---

## CLI

```bash
# Open the interactive guide
membus

# Check server health
membus health --server https://your-server.onrender.com

# View memory stats
membus stats --server https://your-server.onrender.com

# Flush a scope
membus flush --server https://your-server.onrender.com --scope session --scope-id sess_456

# Show the guide again any time
membus guide
```

Skip the flags by setting env vars:

```bash
export MEMBUS_SERVER_URL=https://your-server.onrender.com
export MEMBUS_API_KEY=your-secret-key

membus stats   # just works
membus health
```

---

## Deploy Your Own Server

MemBus client connects to a **membus-server** instance you control. Deploy one in minutes:

1. Clone [membus-server](https://github.com/NorthCommits/membus-server)
2. Push to GitHub
3. Deploy on [Render](https://render.com) — `render.yaml` is included, everything is pre-configured
4. Set your env vars in the Render dashboard
5. Point the client at your URL

```python
bus = MemBus(server_url="https://your-membus.onrender.com", api_key="your-key")
```

---

## Links

- [GitHub](https://github.com/NorthCommits/membus)
- [membus-server](https://github.com/NorthCommits/membus-server)
- [PyPI](https://pypi.org/project/membus)
