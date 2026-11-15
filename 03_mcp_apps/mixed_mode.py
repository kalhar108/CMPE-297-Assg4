"""Codelab 3: MCP Apps (SEP-1865) — Mode 4: Mixed / Hybrid Mode.

Demonstrates Nested Hybrid Sandboxing:
1. FastMCP tool 'mixed_lemonade_app' returns structuredContent containing:
   - 'components': Catalog-constrained KPI cards and layout elements.
   - 'generated': LLM-synthesized interactive HTML mini-app (flash discount spinner).
2. The outer MCP App container renders catalog widgets and embeds the generative HTML inside
   a nested secondary iframe (Double Boundary Isolation).
3. Actions inside the nested widget bubble up through the primary app to the host container,
   updating the LLM's conversational state via JSON-RPC 'ui/update-model-context'.
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


def run_mixed_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes mixed/hybrid mode demonstration for MCP Apps."""
    c = console or Console()
    server = LemonadeMCPServer()
    host = MCPHostEmulator(server=server, console=c)

    c.print("[bold yellow]=== Codelab 3 (MCP Apps SEP-1865): Mode 4 — Mixed / Hybrid Mode ===[/bold yellow]")

    # 1. Execute hybrid tool call
    c.print("[dim]1. Invoking FastMCP tool 'mixed_lemonade_app'...[/dim]")
    tool_result = server.call_tool_sync("mixed_lemonade_app", {"scenario": "Midterm Exam Rush"})
    mount_info = host.mount_ui(tool_result)

    structured = tool_result.structuredContent or {}
    catalog_comps = structured.get("components", [])
    generated_html = structured.get("generated", "")

    # Display components breakdown
    comp_table = Table(title="Hybrid Payload Decomposition", border_style="cyan")
    comp_table.add_column("Layer", style="bold yellow", width=18)
    comp_table.add_column("Type / Target", style="magenta", width=22)
    comp_table.add_column("Details", style="white")

    comp_table.add_row("Primary Shell", "Catalog Components", f"{len(catalog_comps)} widgets: {[c['id'] for c in catalog_comps]}")
    comp_table.add_row("Nested Frame", "Generative HTML Sandbox", f"{len(generated_html)} bytes of self-contained HTML/JS")
    comp_table.add_row("Transport", "SEP-1865 Resource", mount_info["resourceUri"])
    c.print(comp_table)

    # 2. Simulate nested iframe message bubbling up to host window
    c.print("[dim]2. Simulating nested widget event bubbling: User spins 20% flash discount...[/dim]")
    bubble_up_msg = {
        "jsonrpc": "2.0",
        "id": "nested-event-301",
        "method": "ui/update-model-context",
        "params": {
            "active_promotion": "20% Flash Discount",
            "discount_percentage": 20,
            "target_duration_mins": 30,
            "expected_volume_boost": "+35%",
        },
    }
    host.dispatch_post_message(bubble_up_msg)
    c.print("[green][OK] Context successfully updated via double-boundary postMessage bridge.[/green]")

    # 3. Save rendered HTML artifact
    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "hybrid_mixed_app_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(host.sandboxed_html or "")

    # 4. Display host container status
    host.render_terminal_view("Mixed Mode")

    return {
        "mode": "mixed",
        "tool": "mixed_lemonade_app",
        "resourceUri": mount_info["resourceUri"],
        "catalog_components": catalog_comps,
        "nested_html_length": len(generated_html),
        "updated_context": host.model_context,
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_mixed_mode(mock=True)
