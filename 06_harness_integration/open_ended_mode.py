"""Codelab 06 — Harness Integration: Open-Ended UX Mode.

Demonstrates an autonomous agent reasoning loop emitting dynamic interactive
HTML/SVG UI artifacts with sandboxed execution, CSP enforcement, and live re-rendering.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 1. Resolve Project Root (assignment-4-genux/)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 2. Resolve Module Directory (06_harness_integration/)
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from rich.console import Console
from rich.panel import Panel

try:
    from .harness_loop import AgentLifecycleStage, AutonomousUIAgentLoop
    from .multi_surface import MultiSurfaceBroadcaster
except (ImportError, ValueError):
    from harness_loop import AgentLifecycleStage, AutonomousUIAgentLoop
    from multi_surface import MultiSurfaceBroadcaster

# Turn 1 Artifact: Interactive Network Topology Graph (HTML/SVG)
TOPOLOGY_ARTIFACT_TURN1 = """<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' data:;">
  <style>
    body { font-family: monospace; background: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }
    svg { width: 100%; height: 260px; background: #1e293b; border-radius: 8px; border: 1px solid #334155; }
    .node { fill: #3b82f6; stroke: #60a5fa; stroke-width: 2px; cursor: pointer; }
    .node-text { fill: #fff; font-size: 11px; text-anchor: middle; }
    .link { stroke: #10b981; stroke-width: 2px; stroke-dasharray: 4; animation: flow 1s linear infinite; }
  </style>
</head>
<body>
  <h3>Microservice Network Topology (Live Mesh)</h3>
  <svg>
    <line x1="80" y1="120" x2="220" y2="80" class="link" />
    <line x1="220" y1="80" x2="380" y2="120" class="link" />
    <line x1="220" y1="80" x2="220" y2="200" class="link" />
    <circle cx="80" cy="120" r="28" class="node" />
    <text x="80" y="124" class="node-text">Ingress</text>
    <circle cx="220" cy="80" r="28" class="node" />
    <text x="220" y="84" class="node-text">API-GW</text>
    <circle cx="380" cy="120" r="28" class="node" />
    <text x="380" y="124" class="node-text">Payments</text>
    <circle cx="220" cy="200" r="28" class="node" />
    <text x="220" y="204" class="node-text">Auth-DB</text>
  </svg>
</body>
</html>"""

# Turn 2 Artifact: Live Re-Render with Highlighted Degraded Node & Incident Link
TOPOLOGY_ARTIFACT_TURN2 = """<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' data:;">
  <style>
    body { font-family: monospace; background: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }
    svg { width: 100%; height: 260px; background: #1e293b; border-radius: 8px; border: 1px solid #334155; }
    .node-healthy { fill: #3b82f6; stroke: #60a5fa; stroke-width: 2px; }
    .node-degraded { fill: #ef4444; stroke: #f87171; stroke-width: 3px; animation: pulse 1s infinite alternate; }
    .node-text { fill: #fff; font-size: 11px; text-anchor: middle; }
    .link-healthy { stroke: #10b981; stroke-width: 2px; }
    .link-degraded { stroke: #ef4444; stroke-width: 3px; stroke-dasharray: 6; }
    .alert-banner { background: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; padding: 8px; margin-bottom: 10px; font-size: 12px; }
  </style>
</head>
<body>
  <div class="alert-banner">CRITICAL: 18.2% Packet Drop detected between API-GW and Payments</div>
  <svg>
    <line x1="80" y1="120" x2="220" y2="80" class="link-healthy" />
    <line x1="220" y1="80" x2="380" y2="120" class="link-degraded" />
    <line x1="220" y1="80" x2="220" y2="200" class="link-healthy" />
    <circle cx="80" cy="120" r="28" class="node-healthy" />
    <text x="80" y="124" class="node-text">Ingress</text>
    <circle cx="220" cy="80" r="28" class="node-healthy" />
    <text x="220" y="84" class="node-text">API-GW</text>
    <circle cx="380" cy="120" r="28" class="node-degraded" />
    <text x="380" y="124" class="node-text">Payments</text>
    <circle cx="220" cy="200" r="28" class="node-healthy" />
    <text x="220" y="204" class="node-text">Auth-DB</text>
  </svg>
</body>
</html>"""


def run_open_ended_mode(console: Optional[Console] = None, live: bool = False) -> Dict[str, Any]:
    """Executes Harness Open-Ended UX Mode demonstration."""
    c = console or Console()

    c.print(Panel(
        "[bold cyan]Harness Integration — Open-Ended UX Mode[/bold cyan]\n"
        "[dim]Agent reasoning loop emitting dynamic interactive UI artifacts with live re-rendering[/dim]",
        border_style="cyan",
    ))

    broadcaster = MultiSurfaceBroadcaster(console=c)
    agent = AutonomousUIAgentLoop(broadcaster=broadcaster, console=c, mode="live" if live else "mock")

    # Turn 1: Synthesize initial interactive topology graph
    c.print("\n[bold yellow]Turn 1: Agent Synthesizes Interactive Network Topology Artifact[/bold yellow]")
    spec_t1 = {
        "root": "topologySurface",
        "elements": {
            "topologySurface": {
                "type": "Stack",
                "props": {"direction": "column"},
                "children": ["headerCard", "topologyArtifact"],
            },
            "headerCard": {
                "type": "Card",
                "props": {
                    "title": "Mesh Topology Visualizer",
                    "description": "Synthesized interactive SVG artifact with sandboxed CSP",
                },
                "children": [],
            },
            "topologyArtifact": {
                "type": "HtmlArtifact",
                "props": {
                    "title": "Real-time Microservice Mesh",
                    "document": TOPOLOGY_ARTIFACT_TURN1,
                },
                "children": [],
            },
        },
        "state": {},
    }

    turn1 = agent.run_step(
        thought="User requested real-time network topology visualizer. Emitting bespoke SVG artifact inside sandboxed HtmlArtifact.",
        spec=spec_t1,
    )
    c.print(f"  [cyan]Thought:[/cyan] {turn1.thought}")
    c.print(f"  [cyan]Tool Call:[/cyan] {turn1.tool_call} -> Status: [green]{turn1.tool_result.get('status')}[/green]")
    assert turn1.tool_result.get("status") == "success"
    assert "Content-Security-Policy" in TOPOLOGY_ARTIFACT_TURN1

    # Turn 2: Live Re-render with Updated Degraded State
    c.print("\n[bold yellow]Turn 2: Agent Reasons Over Health Delta & Live Re-renders Artifact[/bold yellow]")
    spec_t2 = {
        "root": "topologySurface",
        "elements": {
            "topologySurface": {
                "type": "Stack",
                "props": {"direction": "column"},
                "children": ["headerCard", "topologyArtifactUpdated", "mitigateBtn"],
            },
            "headerCard": {
                "type": "Card",
                "props": {
                    "title": "Mesh Topology Visualizer [DEGRADED DETECTED]",
                    "description": "Live re-render reflecting 18.2% packet drop between API-GW and Payments",
                },
                "children": [],
            },
            "topologyArtifactUpdated": {
                "type": "HtmlArtifact",
                "props": {
                    "title": "Real-time Microservice Mesh (Updated)",
                    "document": TOPOLOGY_ARTIFACT_TURN2,
                },
                "children": [],
            },
            "mitigateBtn": {
                "type": "Button",
                "props": {
                    "label": "Reroute Traffic via Fallback Mesh",
                    "action": "reroute_mesh",
                    "variant": "danger",
                },
                "children": [],
            },
        },
        "state": {},
    }

    turn2 = agent.run_step(
        thought="Detected packet loss anomaly on Payments node. Live re-rendering SVG mesh with alert highlights and mitigation button.",
        spec=spec_t2,
    )
    c.print(f"  [cyan]Thought:[/cyan] {turn2.thought}")
    c.print(f"  [cyan]Tool Call:[/cyan] {turn2.tool_call} -> Status: [green]{turn2.tool_result.get('status')}[/green]")
    assert turn2.tool_result.get("status") == "success"

    # Turn 3: Complete
    summary = agent.complete()
    c.print(f"\n[bold green][OK][/bold green] Open-Ended UX agent loop completed with [cyan]{summary['rendered_surfaces_count']}[/cyan] verified live re-renders.")

    return {
        "status": "success",
        "total_turns": summary["total_turns"],
        "rendered_surfaces": summary["rendered_surfaces_count"],
        "final_stage": summary["final_stage"],
        "artifact_csp_verified": True,
    }


if __name__ == "__main__":
    run_open_ended_mode()
