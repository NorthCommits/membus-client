from rich.console import Console
from rich.panel import Panel
from rich.table import Table
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

    # -- Quick start -----------------------------------------------------------
    console.print("\n[bold yellow]Quick Start[/bold yellow]")
    code = '''\
from membus import MemBus, Scope

bus = MemBus(adapter="memory")                    # "memory" | "redis" | "supabase" | "chroma"

bus.write("user_name", "Alice", scope=Scope.USER, scope_id="u1")
name = bus.read("user_name",  scope=Scope.USER, scope_id="u1")  # -> "Alice"
bus.manage(scope=Scope.SESSION, operation="prune", scope_id="s1")'''
    console.print(Syntax(code, "python", theme="monokai", padding=(1, 2)))

    # -- Scopes ----------------------------------------------------------------
    console.print("\n[bold yellow]Memory Scopes[/bold yellow]")
    scopes = Table(box=box.ROUNDED, border_style="cyan", show_header=True, header_style="bold cyan")
    scopes.add_column("Scope",    style="bold white", width=10)
    scopes.add_column("Persists",  width=8)
    scopes.add_column("Who can see it")
    scopes.add_row("user",    "Long",    "Everything tied to one user across all sessions")
    scopes.add_row("session", "Short",   "Lives for one conversation, then gone")
    scopes.add_row("agent",   "Long",    "Private notebook for a specific agent identity")
    scopes.add_row("org",     "Long",    "Shared across your entire team or product")
    console.print(scopes)

    # -- Adapters --------------------------------------------------------------
    console.print("\n[bold yellow]Adapters — pick your backend[/bold yellow]")
    adapters = Table(box=box.ROUNDED, border_style="magenta", show_header=True, header_style="bold magenta")
    adapters.add_column("Adapter",   style="bold white", width=12)
    adapters.add_column("Best for",  width=28)
    adapters.add_column("How to use")
    adapters.add_row("memory",   "Dev & testing (zero infra)",    '[dim]MemBus(adapter="memory")[/dim]')
    adapters.add_row("redis",    "Fast, session-friendly apps",   '[dim]MemBus(adapter="redis")[/dim]')
    adapters.add_row("supabase", "Persistent, Postgres-backed",   '[dim]MemBus(adapter="supabase")[/dim]')
    adapters.add_row("chroma",   "Semantic / vector memory",      '[dim]MemBus(adapter="chroma")[/dim]')
    console.print(adapters)

    console.print(
        "\n  [dim]The MemBus server supports all adapters simultaneously — "
        "you choose per client instance.[/dim]"
    )

    # -- Adapter config in code ------------------------------------------------
    console.print("\n[bold yellow]Choosing an adapter in your code[/bold yellow]")
    adapter_code = '''\
from membus import MemBus, Scope

# Default — uses fast in-memory storage (great for dev)
bus = MemBus()

# Switch to a persistent adapter — no server changes needed
redis_bus    = MemBus(adapter="redis")
supabase_bus = MemBus(adapter="supabase")
chroma_bus   = MemBus(adapter="chroma")

# Each instance routes to its own backend independently
redis_bus.write("session_data", {...}, scope=Scope.SESSION, scope_id="s1")
chroma_bus.write("doc_embedding", [...], scope=Scope.USER, scope_id="u1")'''
    console.print(Syntax(adapter_code, "python", theme="monokai", padding=(1, 2)))

    # -- MCP -------------------------------------------------------------------
    console.print("\n[bold yellow]MCP — give your agents memory as a tool[/bold yellow]")
    mcp_code = '''\
from membus import MemBus
from membus.mcp import MemBusMCPServer

bus    = MemBus()
server = MemBusMCPServer(bus)
server.run()   # stdio MCP server — plug into any MCP-compatible agent'''
    console.print(Syntax(mcp_code, "python", theme="monokai", padding=(1, 2)))

    # -- CLI -------------------------------------------------------------------
    console.print("\n[bold yellow]CLI Commands[/bold yellow]")
    cli = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    cli.add_column(style="bold cyan",  width=40)
    cli.add_column(style="dim white")
    cli.add_row("membus health --server <url>",  "Check if your server is alive")
    cli.add_row("membus stats  --server <url>",  "Show memory usage by scope")
    cli.add_row("membus flush  --server <url> --scope session --scope-id s1", "Wipe a scope clean")
    cli.add_row("membus guide",                  "Show this screen again")
    console.print(cli)

    # -- Footer ----------------------------------------------------------------
    console.print(
        Panel(
            "[bold cyan]github.com/NorthCommits/membus[/bold cyan]  ·  "
            "[dim]Deploy your server → render.com  ·  "
            "pip install membus[/dim]",
            border_style="dim",
            padding=(0, 2),
        )
    )
    console.print()
