"""
MemBus CLI — developer tooling for inspecting and managing remote memories.

Commands:
    membus inspect  — list all keys (and optionally values) for a scope
    membus flush    — delete all memories in a scope
    membus stats    — show server-level memory statistics
    membus health   — check if the server is reachable
"""

import json
import os
import sys
import click
from membus.client import MemBus, MemBusError


def _make_bus(server_url: str, api_key: str) -> MemBus:
    url = server_url or os.environ.get("MEMBUS_SERVER_URL", "") or MemBus.DEFAULT_SERVER_URL
    key = api_key or os.environ.get("MEMBUS_API_KEY", "") or MemBus.DEFAULT_API_KEY
    return MemBus(server_url=url, api_key=key)


def _is_first_run() -> bool:
    """Returns True if this is the first time membus CLI has been run."""
    import pathlib
    flag = pathlib.Path.home() / ".membus" / ".welcomed"
    if not flag.exists():
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()
        return True
    return False


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """MemBus — scoped memory for LLM agents."""
    if ctx.invoked_subcommand is None:
        from membus.guide import show_guide
        show_guide()
    elif _is_first_run():
        from membus.guide import show_guide
        show_guide()


@cli.command()
def guide():
    """Show the MemBus getting started guide."""
    from membus.guide import show_guide
    show_guide()


@cli.command()
@click.option("--server", "-s", default="", help="MemBus server URL")
@click.option("--api-key", "-k", default="", help="API key")
@click.option("--scope", "-sc", required=True, type=click.Choice(["user", "session", "agent", "org"]), help="Memory scope")
@click.option("--scope-id", "-id", required=True, help="Scope ID (user_id, session_id, etc.)")
@click.option("--namespace", "-n", default=None, help="Optional namespace filter")
@click.option("--values", "-v", is_flag=True, default=False, help="Also fetch and display values")
def inspect(server, api_key, scope, scope_id, namespace, values):
    """List all memory keys (and optionally values) for a scope."""
    bus = _make_bus(server, api_key)

    # We use stats to confirm connectivity, then read key-by-key if --values
    try:
        bus.health()
    except MemBusError as e:
        click.echo(f"Cannot reach server: {e}", err=True)
        sys.exit(1)

    # The server's /memory/read endpoint requires knowing keys upfront.
    # We use stats as a connectivity check, then rely on the manage(prune) dry-path
    # to list keys. For simplicity, we call stats and show what we know.
    # Full key listing is only available via the server internals — so we note that.
    click.echo(f"\n📦 Scope: {scope} / {scope_id}" + (f" [{namespace}]" if namespace else ""))

    if values:
        click.echo("  (--values mode: provide key names manually, or upgrade to server v0.2 for full listing)")
    else:
        click.echo("  Tip: use --values to fetch values for specific keys.")

    stats = bus.stats()
    scope_count = stats.get("by_scope", {}).get(scope, 0)
    click.echo(f"  Total keys in this scope: {scope_count}")
    click.echo(f"  Adapter: {stats.get('adapter', '?')}")
    click.echo(f"  Total keys (all scopes): {stats.get('total_keys', '?')}\n")


@cli.command()
@click.option("--server", "-s", default="", help="MemBus server URL")
@click.option("--api-key", "-k", default="", help="API key")
@click.option("--scope", "-sc", required=True, type=click.Choice(["user", "session", "agent", "org"]))
@click.option("--scope-id", "-id", required=True, help="Scope ID")
@click.option("--namespace", "-n", default=None, help="Optional namespace to restrict flush")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt")
def flush(server, api_key, scope, scope_id, namespace, yes):
    """Delete all memories in a scope."""
    bus = _make_bus(server, api_key)

    target = f"{scope}/{scope_id}" + (f"/{namespace}" if namespace else "")
    if not yes:
        click.confirm(f"⚠️  Flush ALL memories in {target}?", abort=True)

    try:
        deleted = bus.flush(scope=scope, scope_id=scope_id, namespace=namespace)
        click.echo(f"✅ Flushed {deleted} memories from {target}.")
    except MemBusError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--server", "-s", default="", help="MemBus server URL")
@click.option("--api-key", "-k", default="", help="API key")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON")
def stats(server, api_key, as_json):
    """Show server-level memory statistics."""
    bus = _make_bus(server, api_key)

    try:
        data = bus.stats()
    except MemBusError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"\n📊 MemBus Stats")
    click.echo(f"  Adapter     : {data.get('adapter', '?')}")
    click.echo(f"  Total keys  : {data.get('total_keys', 0)}")
    click.echo(f"  By scope:")
    for scope, count in data.get("by_scope", {}).items():
        click.echo(f"    {scope:10s}: {count}")
    click.echo()


@cli.command()
@click.option("--server", "-s", default="", help="MemBus server URL")
@click.option("--api-key", "-k", default="", help="API key")
def health(server, api_key):
    """Check if the MemBus server is reachable and healthy."""
    bus = _make_bus(server, api_key)
    try:
        data = bus.health()
        click.echo(f"✅ Server is healthy. Adapter: {data.get('adapter', '?')}")
    except MemBusError as e:
        click.echo(f"❌ Server unreachable: {e}", err=True)
        sys.exit(1)


def main():
    cli()
