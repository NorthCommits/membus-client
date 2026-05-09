from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.syntax import Syntax
from rich import box

console = Console()

LOGO = """
[bold cyan]
 ███╗   ███╗███████╗███╗   ███╗██████╗ ██╗   ██╗███████╗
 ████╗ ████║██╔════╝████╗ ████║██╔══██╗██║   ██║██╔════╝
 ██╔████╔██║█████╗  ██╔████╔██║██████╔╝██║   ██║███████╗
 ██║╚██╔╝██║██╔══╝  ██║╚██╔╝██║██╔══██╗██║   ██║╚════██║
 ██║ ╚═╝ ██║███████╗██║ ╚═╝ ██║██████╔╝╚██████╔╝███████║
 ╚═╝     ╚═╝╚══════╝╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚══════╝
[/bold cyan]"""


def show_guide():
    console.print(LOGO)
    console.print(
        Panel(
            "[bold white]Scoped memory for LLM agents.[/bold white]  [dim]Install and go.[/dim]",
            border_style="cyan",
            padding=(0, 4),
        )
    )

    # ── Quick start ────────────────────────────────────────────────────────
    console.print("\n[bold yellow]⚡ Quick Start[/bold yellow]")
    code = '''\
from membus import MemBus, Scope

bus = MemBus()                                    # connects to your server

bus.write("user_name", "Alice", scope=Scope.USER, scope_id="u1")
name = bus.read("user_name",  scope=Scope.USER, scope_id="u1")  # → "Alice"
bus.manage(scope=Scope.SESSION, operation="prune", scope_id="s1")'''
    console.print(Syntax(code, "python", theme="monokai", padding=(1, 2)))

    # ── Scopes ─────────────────────────────────────────────────────────────
    console.print("\n[bold yellow]🗂  Memory Scopes[/bold yellow]")
    scopes = Table(box=box.ROUNDED, border_style="cyan", show_header=True, header_style="bold cyan")
    scopes.add_column("Scope",    style="bold white", width=10)
    scopes.add_column("Persists",  width=8)
    scopes.add_column("Who can see it")
    scopes.add_row("user",    "🟢 Long",    "Everything tied to one user across all sessions")
    scopes.add_row("session", "🟡 Short",   "Lives for one conversation, then gone")
    scopes.add_row("agent",   "🟢 Long",    "Private notebook for a specific agent identity")
    scopes.add_row("org",     "🟢 Long",    "Shared across your entire team or product")
    console.print(scopes)

    # ── Adapters ───────────────────────────────────────────────────────────
    console.print("\n[bold yellow]🔌 Adapters — pick your backend[/bold yellow]")
    adapters = Table(box=box.ROUNDED, border_style="magenta", show_header=True, header_style="bold magenta")
    adapters.add_column("Adapter",   style="bold white", width=12)
    adapters.add_column("Best for",  width=28)
    adapters.add_column("Set on server")
    adapters.add_row("memory",   "Dev & testing (zero infra)",    "[dim]MEMBUS_ADAPTER=memory[/dim]")
    adapters.add_row("redis",    "Fast, session-friendly apps",   "[dim]MEMBUS_ADAPTER=redis[/dim]")
    adapters.add_row("supabase", "Persistent, Postgres-backed",   "[dim]MEMBUS_ADAPTER=supabase[/dim]")
    adapters.add_row("chroma",   "Semantic / vector memory",      "[dim]MEMBUS_ADAPTER=chroma[/dim]")
    console.print(adapters)

    console.print(
        "\n  [dim]Set [bold]MEMBUS_ADAPTER[/bold] in your server's .env — no client code changes needed.[/dim]"
    )

    # ── Adapter config in code ─────────────────────────────────────────────
    console.print("\n[bold yellow]🛠  Choosing an adapter in your code[/bold yellow]")
    adapter_code = '''\
from membus import MemBus, Scope

# Default — uses whatever adapter the server is configured with
bus = MemBus()

# Explicitly tell MemBus which adapter the server should use
# (useful for documentation, validation, or multi-server setups)
bus = MemBus(expected_adapter="supabase")

# The client will warn you if the server is running a different adapter
bus.health()  # → {"status": "ok", "adapter": "memory"} ⚠ mismatch warning'''
    console.print(Syntax(adapter_code, "python", theme="monokai", padding=(1, 2)))

    # ── MCP ────────────────────────────────────────────────────────────────
    console.print("\n[bold yellow]🤖 MCP — give your agents memory as a tool[/bold yellow]")
    mcp_code = '''\
from membus import MemBus
from membus.mcp import MemBusMCPServer

bus    = MemBus()
server = MemBusMCPServer(bus)
server.run()   # stdio MCP server — plug into any MCP-compatible agent'''
    console.print(Syntax(mcp_code, "python", theme="monokai", padding=(1, 2)))

    # ── CLI ────────────────────────────────────────────────────────────────
    console.print("\n[bold yellow]💻 CLI Commands[/bold yellow]")
    cli = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    cli.add_column(style="bold cyan",  width=32)
    cli.add_column(style="dim white")
    cli.add_row("membus health --server <url>",  "Check if your server is alive")
    cli.add_row("membus stats  --server <url>",  "Show memory usage by scope")
    cli.add_row("membus flush  --server <url> --scope session --scope-id s1",
                "Wipe a scope clean")
    cli.add_row("membus guide",                  "Show this screen again")
    console.print(cli)

    # ── Footer ─────────────────────────────────────────────────────────────
    console.print(
        Panel(
            "[bold cyan]github.com/NorthCommits/membus[/bold cyan]  ·  "
            "[dim]Deploy your server → render.com  ·  "
            "Publish your agent → pip install membus[/dim]",
            border_style="dim",
            padding=(0, 2),
        )
    )
    console.print()
