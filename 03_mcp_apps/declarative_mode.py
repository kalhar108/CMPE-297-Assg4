"""Codelab 3: MCP Apps (SEP-1865) — Mode 2: Declarative Mode.

Demonstrates schema-driven dynamic forms generated from FastMCP tool JSON Schemas:
1. Tool 'order_supplies' defines parameter types, default values, and validation rules in its JSON Schema.
2. The dynamic form MCP app view binds to this schema and mounts inside the host sandbox.
3. User submissions fire JSON-RPC 'ui/call-tool' across the postMessage bridge.
4. The host verifies security allowlists, executes the tool, and updates conversational context.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

try:
    from .mcp_server import LemonadeMCPServer
    from .host_emulator import MCPHostEmulator
except (ImportError, ValueError):
    from mcp_server import LemonadeMCPServer
    from host_emulator import MCPHostEmulator


def run_declarative_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes declarative mode demonstration for MCP Apps."""
    c = console or Console()
    server = LemonadeMCPServer()
    host = MCPHostEmulator(server=server, console=c)

    c.print("[bold yellow]=== Codelab 3 (MCP Apps SEP-1865): Mode 2 — Declarative Mode ===[/bold yellow]")

    # 1. Fetch initial resource for dynamic form
    c.print("[dim]1. Mounting dynamic schema-driven form resource 'ui://forms/dynamic_form.html'...[/dim]")
    init_res = server.call_tool_sync("order_supplies", {"lemons": 0, "sugar_kg": 0.0, "ice_bags": 0, "cups": 0})
    mount_info = host.mount_ui(init_res)

    # 2. Inspect tool schema parameters (declarative contract)
    c.print("[dim]2. Inspecting declarative parameters for FastMCP tool 'order_supplies'...[/dim]")
    param_table = Table(title="Tool JSON Schema Contract for Dynamic Form Generation", border_style="cyan")
    param_table.add_column("Field Name", style="bold yellow")
    param_table.add_column("Schema Type", style="magenta")
    param_table.add_column("Default Value", style="green")
    param_table.add_column("Validation Rule", style="white")

    param_table.add_row("lemons", "integer", "24", "min: 1, max: 500")
    param_table.add_row("sugar_kg", "number (float)", "5.0", "step: 0.5, min: 0.5")
    param_table.add_row("ice_bags", "integer", "4", "min: 1")
    param_table.add_row("cups", "integer", "50", "min: 10")
    param_table.add_row("rush_delivery", "boolean", "false", "optional rush fee")
    c.print(param_table)

    # 3. Simulate client UI user submission firing ui/call-tool over postMessage bridge
    c.print("[dim]3. Simulating user form submission over JSON-RPC 2.0 postMessage bridge...[/dim]")
    form_submission_args = {
        "lemons": 48,
        "sugar_kg": 10.0,
        "ice_bags": 6,
        "cups": 100,
        "rush_delivery": True,
    }

    bridge_call_tool_msg = {
        "jsonrpc": "2.0",
        "id": "form-submit-101",
        "method": "ui/call-tool",
        "params": {
            "name": "order_supplies",
            "arguments": form_submission_args,
        },
    }

    # Host handles bridge call
    bridge_response = host.dispatch_post_message(bridge_call_tool_msg)
    c.print(f"[green][OK] Bridge call succeeded. Tool result returned to app view.[/green]")

    # 4. Save rendered HTML artifact
    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "declarative_form_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(host.sandboxed_html or "")

    # 5. Display updated host container status
    host.render_terminal_view("Declarative Mode")

    return {
        "mode": "declarative",
        "tool": "order_supplies",
        "resourceUri": mount_info["resourceUri"],
        "submitted_args": form_submission_args,
        "bridge_response": bridge_response,
        "updated_inventory": host.model_context.get("last_order", {}).get("updated_inventory"),
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_declarative_mode(mock=True)
