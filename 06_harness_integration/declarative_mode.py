"""Codelab 06 — Harness Integration: Declarative Mode.

Demonstrates a multi-turn autonomous tool-calling agent loop with schema enforcement,
deliberate negative test triggering self-correction, and state tracking.
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
from rich.table import Table

try:
    from .harness_loop import AgentLifecycleStage, AutonomousUIAgentLoop
    from .multi_surface import MultiSurfaceBroadcaster
except (ImportError, ValueError):
    from harness_loop import AgentLifecycleStage, AutonomousUIAgentLoop
    from multi_surface import MultiSurfaceBroadcaster

# Turn 1 Spec: Initial Incident Alert Dashboard
TURN_1_INCIDENT_SPEC = {
    "root": "incidentView",
    "elements": {
        "incidentView": {
            "type": "Stack",
            "props": {"direction": "column"},
            "children": ["incidentCard", "kpiRow"],
        },
        "incidentCard": {
            "type": "Card",
            "props": {
                "title": "Incident #892: High Query Latency on db-primary",
                "description": "Triggered by automated health sentinel at 12:04:10Z",
            },
            "children": [],
        },
        "kpiRow": {
            "type": "Stack",
            "props": {"direction": "row"},
            "children": ["latencyKpi", "poolKpi"],
        },
        "latencyKpi": {
            "type": "Metric",
            "props": {"label": "P99 Query Latency", "value": "1,420ms", "change": "+340%"},
            "children": [],
        },
        "poolKpi": {
            "type": "Metric",
            "props": {"label": "Connection Pool Saturation", "value": "98%", "change": "+22%"},
            "children": [],
        },
    },
    "state": {},
}

# Turn 2 Faulty Spec: Deliberately includes unknown component type
TURN_2_FAULTY_SPEC = {
    "root": "invalidRoot",
    "elements": {
        "invalidRoot": {
            "type": "MagicAiFixerWidget",  # Violates catalog schema!
            "props": {"target": "db-primary"},
            "children": [],
        }
    },
    "state": {},
}

# Turn 2 Corrected Spec: Replaces invalid widget with valid Card, Table, and Button
TURN_2_CORRECTED_SPEC = {
    "root": "remediationView",
    "elements": {
        "remediationView": {
            "type": "Stack",
            "props": {"direction": "column"},
            "children": ["remediationCard", "actionStack"],
        },
        "remediationCard": {
            "type": "Card",
            "props": {
                "title": "Remediation Strategy: Scale Read Replicas & Flush Query Cache",
                "description": "Self-corrected specification adhering to catalog schema",
            },
            "children": ["queriesTable"],
        },
        "queriesTable": {
            "type": "Table",
            "props": {
                "columns": ["PID", "User", "Query Snippet", "Duration"],
                "rows": [
                    ["4091", "reporting_svc", "SELECT * FROM large_orders WHERE...", "42.1s"],
                    ["4094", "analytics_job", "SELECT COUNT(DISTINCT uid) FROM...", "18.4s"],
                ],
            },
            "children": [],
        },
        "actionStack": {
            "type": "Stack",
            "props": {"direction": "row"},
            "children": ["killSlowQueriesBtn", "scaleReplicaBtn"],
        },
        "killSlowQueriesBtn": {
            "type": "Button",
            "props": {"label": "Terminate Long-Running Queries", "action": "kill_queries", "variant": "danger"},
            "children": [],
        },
        "scaleReplicaBtn": {
            "type": "Button",
            "props": {"label": "Spawn 2 Read Replicas", "action": "scale_replicas", "variant": "primary"},
            "children": [],
        },
    },
    "state": {},
}


def run_declarative_mode(console: Optional[Console] = None, live: bool = False) -> Dict[str, Any]:
    """Executes Harness Declarative Mode demonstration."""
    c = console or Console()

    c.print(Panel(
        "[bold cyan]Harness Integration — Declarative Mode[/bold cyan]\n"
        "[dim]Multi-turn tool-calling UI agent loop with schema enforcement and self-correction[/dim]",
        border_style="cyan",
    ))

    broadcaster = MultiSurfaceBroadcaster(console=c)
    agent = AutonomousUIAgentLoop(broadcaster=broadcaster, console=c, mode="live" if live else "mock")

    # Turn 1: Agent observes incident and renders initial triage view
    c.print("\n[bold yellow]Turn 1: Initial Reasoning & Projection[/bold yellow]")
    turn1 = agent.run_step(
        thought="Sentinel alerted on P99 database latency. Projecting initial incident status UI to engineer.",
        spec=TURN_1_INCIDENT_SPEC,
    )
    c.print(f"  [cyan]Thought:[/cyan] {turn1.thought}")
    c.print(f"  [cyan]Tool Call:[/cyan] {turn1.tool_call} -> Status: [green]{turn1.tool_result.get('status')}[/green]")
    assert turn1.tool_result.get("status") == "success"

    # Turn 2: Agent attempts to emit faulty component; harness rejects it; agent self-corrects
    c.print("\n[bold yellow]Turn 2a: Schema Violation & Rejection[/bold yellow]")
    turn2a = agent.run_step(
        thought="Attempting to project specialized remediation widget 'MagicAiFixerWidget'.",
        spec=TURN_2_FAULTY_SPEC,
    )
    c.print(f"  [cyan]Tool Call:[/cyan] {turn2a.tool_call} -> Status: [red]{turn2a.tool_result.get('status')}[/red]")
    c.print(f"  [yellow]Harness Validator Feedback:[/yellow] {turn2a.tool_result.get('error')}")
    assert turn2a.tool_result.get("status") == "error"
    assert "Unknown component type 'MagicAiFixerWidget'" in turn2a.tool_result.get("error")

    c.print("\n[bold yellow]Turn 2b: Self-Correction Loop[/bold yellow]")
    turn2b = agent.run_step(
        thought="Harness rejected MagicAiFixerWidget. Self-correcting by compiling plan into standard Card, Table, and Button primitives.",
        spec=TURN_2_CORRECTED_SPEC,
    )
    c.print(f"  [cyan]Thought:[/cyan] {turn2b.thought}")
    c.print(f"  [cyan]Tool Call:[/cyan] {turn2b.tool_call} -> Status: [green]{turn2b.tool_result.get('status')}[/green]")
    assert turn2b.tool_result.get("status") == "success"
    assert agent.self_corrections_count == 1

    # Turn 3: Finalization
    c.print("\n[bold yellow]Turn 3: Lifecycle Completion[/bold yellow]")
    summary = agent.complete()

    c.print(f"[bold green][OK][/bold green] Autonomous agent loop completed in [cyan]{summary['total_turns']}[/cyan] turns with [yellow]{summary['self_corrections']}[/yellow] verified self-correction(s).")
    c.print(f"  - Final Stage: [green]{summary['final_stage']}[/green]")
    c.print(f"  - Rendered surfaces count: [cyan]{summary['rendered_surfaces_count']}[/cyan]")

    return {
        "status": "success",
        "total_turns": summary["total_turns"],
        "self_corrections": summary["self_corrections"],
        "final_stage": summary["final_stage"],
        "turn_records": [
            {
                "turn": t.turn_index,
                "thought": t.thought,
                "status": t.tool_result.get("status") if t.tool_result else None,
            }
            for t in agent.turns
        ],
    }


if __name__ == "__main__":
    run_declarative_mode()
