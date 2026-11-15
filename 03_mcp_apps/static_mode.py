"""Codelab 3: MCP Apps (SEP-1865) — Mode 1: Static Mode.

Demonstrates deterministic UI resource serving via FastMCP:
1. FastMCP server registers tool 'get_lemonade_dashboard' and static resource 'ui://lemonade-stand/dashboard.html'.
2. Tool returns CallToolResult with dual output: LLM summary + structuredContent JSON + _meta.ui.resourceUri.
3. Host emulator mounts UI in a sandboxed container, validates Content Security Policy (CSP), and renders.
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


def run_static_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes static mode demonstration for MCP Apps."""
    c = console or Console()
    server = LemonadeMCPServer()
    host = MCPHostEmulator(server=server, console=c)

    c.print("[bold yellow]=== Codelab 3 (MCP Apps SEP-1865): Mode 1 — Static Mode ===[/bold yellow]")

    # 1. Execute tool call on FastMCP server
    c.print("[dim]1. Invoking FastMCP tool 'get_lemonade_dashboard'...[/dim]")
    tool_result = server.call_tool_sync("get_lemonade_dashboard", {})

    llm_text = tool_result.content[0].text if tool_result.content else ""
    meta = host.extract_meta(tool_result)
    ui_meta = meta.get("ui", {}) if isinstance(meta, dict) else {}
    resource_uri = ui_meta.get("resourceUri", "")

    # Display dual-output payload in terminal
    dual_table = Table(title="FastMCP SEP-1865 Dual-Output Return", border_style="cyan")
    dual_table.add_column("Channel", style="bold yellow", width=20)
    dual_table.add_column("Destination", style="bold magenta", width=22)
    dual_table.add_column("Content / Value", style="white")

    dual_table.add_row("content (Text)", "LLM Context Window", llm_text)
    dual_table.add_row("structuredContent", "Frontend App View", str(tool_result.structuredContent))
    dual_table.add_row("_meta.ui.resourceUri", "Host Sandbox Container", resource_uri)
    c.print(dual_table)

    # 2. Host mounts UI resource and enforces sandboxing
    c.print(f"[dim]2. Host fetching resource '{resource_uri}' and injecting CSP...[/dim]")
    mount_info = host.mount_ui(tool_result)

    # 3. Save sandboxed HTML artifact if requested
    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "static_dashboard_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(host.sandboxed_html or "")

    c.print(f"[green][OK] UI successfully mounted. Sandboxed HTML artifact written to: {os.path.basename(target_path)}[/green]")

    # 4. Render host container status to terminal
    host.render_terminal_view("Static Mode")

    return {
        "mode": "static",
        "tool": "get_lemonade_dashboard",
        "resourceUri": resource_uri,
        "csp_status": mount_info["csp_status"],
        "llm_text": llm_text,
        "structuredContent": tool_result.structuredContent,
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_static_mode(mock=True)
