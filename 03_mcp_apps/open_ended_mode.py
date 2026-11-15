"""Codelab 3: MCP Apps (SEP-1865) — Mode 3: Open-Ended UX Mode.

Demonstrates dynamic, unconstrained UI resource synthesis with rigorous security isolation:
1. FastMCP server delivers interactive HTML application 'ui://dynamic/pricing_sim.html'.
2. Host emulator mounts view in strict sandbox container with Content Security Policy (CSP).
3. Executes adversarial security probes proving protection against:
   - DOM Escape: window.parent.document access blocked.
   - Network Exfiltration: fetch() blocked by connect-src 'none'.
   - Privilege Escalation: unauthorized tool invocations blocked by tool allowlist.
4. Simulates interactive slider manipulation updating host LLM conversational context.
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


def run_open_ended_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes open-ended mode demonstration for MCP Apps."""
    c = console or Console()
    server = LemonadeMCPServer()
    host = MCPHostEmulator(server=server, console=c)

    c.print("[bold yellow]=== Codelab 3 (MCP Apps SEP-1865): Mode 3 — Open-Ended UX Mode ===[/bold yellow]")

    # 1. Generate and mount dynamic pricing simulator
    c.print("[dim]1. Invoking FastMCP tool 'generate_pricing_simulator'...[/dim]")
    sim_result = server.call_tool_sync("generate_pricing_simulator", {"base_price": 3.00, "temp_f": 90.0, "crowd_factor": 1.5})
    mount_info = host.mount_ui(sim_result)
    c.print(f"[green][OK] Mounted dynamic app resource: {mount_info['resourceUri']}[/green]")

    # 2. Simulate user slider manipulation dispatching context update
    c.print("[dim]2. Simulating user slider adjustment ($3.50/cup, 92°F) via postMessage bridge...[/dim]")
    update_msg = {
        "jsonrpc": "2.0",
        "id": "slider-event-201",
        "method": "ui/update-model-context",
        "params": {
            "cup_price": 3.50,
            "projected_cups": 136,
            "projected_revenue": 476.00,
            "weather_temp_f": 92.0,
        },
    }
    host.dispatch_post_message(update_msg)

    # 3. Adversarial Security Verification Suite
    c.print("\n[bold red]3. Running Host Sandbox Adversarial Security Probe Suite...[/bold red]")
    security_probes = [
        host.simulate_security_probe("parent_dom_access"),
        host.simulate_security_probe("external_network_request"),
        host.simulate_security_probe("unauthorized_tool_call"),
    ]

    sec_table = Table(title="Host Sandbox Security Verification Matrix", border_style="red")
    sec_table.add_column("Security Probe Description", style="bold white")
    sec_table.add_column("Result", style="bold green", width=10)
    sec_table.add_column("Policy / Defense Enforced", style="yellow")
    sec_table.add_column("Defense Output / Diagnostic", style="dim")

    for p in security_probes:
        status_str = "BLOCKED" if p["blocked"] else "FAILED"
        sec_table.add_row(
            p["probe"],
            status_str,
            p["policy_enforced"],
            str(p["error"])[:55] + "...",
        )
    c.print(sec_table)

    # 4. Save rendered HTML artifact
    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "open_ended_simulator_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(host.sandboxed_html or "")

    # 5. Display terminal view
    host.render_terminal_view("Open-Ended Mode")

    return {
        "mode": "open_ended",
        "tool": "generate_pricing_simulator",
        "resourceUri": mount_info["resourceUri"],
        "security_probes": security_probes,
        "all_probes_blocked": all(p["blocked"] for p in security_probes),
        "updated_context": host.model_context,
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_open_ended_mode(mock=True)
