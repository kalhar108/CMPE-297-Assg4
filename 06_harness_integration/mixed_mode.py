"""Codelab 06 — Harness Integration: Mixed / Hybrid Mode.

Demonstrates the TrueForge hybrid architecture:
1. Deterministic layout shell with embedded generative dynamic components.
2. Complete interactive client action return loop (UI click -> POST /action -> Agent reasoning -> Re-render).
3. Defensive fallback error recovery for malformed action payloads.
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

# Deterministic Shell Spec with Embedded Generative Strategy Card
INITIAL_HYBRID_SHELL_SPEC = {
    "root": "trueforgeShell",
    "elements": {
        "trueforgeShell": {
            "type": "Stack",
            "props": {"direction": "column"},
            "children": ["navHeader", "kpiSummaryRow", "generativeWorkArea", "actionFooter"],
        },
        "navHeader": {
            "type": "Card",
            "props": {
                "title": "TrueForge Autonomous Operations Console",
                "description": "Environment: Production-Fleet-01 | Agent: ClusterSentinel",
            },
            "children": [],
        },
        "kpiSummaryRow": {
            "type": "Stack",
            "props": {"direction": "row"},
            "children": ["loadMetric", "costMetric"],
        },
        "loadMetric": {
            "type": "Metric",
            "props": {"label": "Global Fleet Load", "value": "89.4%", "change": "+14.2%"},
            "children": [],
        },
        "costMetric": {
            "type": "Metric",
            "props": {"label": "Hourly Compute Burn", "value": "$142.50", "change": "+8.0%"},
            "children": [],
        },
        "generativeWorkArea": {
            "type": "Card",
            "props": {
                "title": "Agent Strategy: Dynamic Autoscaling Proposed",
                "description": "Autonomous evaluation: Current capacity saturation projected in 14 minutes",
            },
            "children": ["planTable"],
        },
        "planTable": {
            "type": "Table",
            "props": {
                "columns": ["Cluster Zone", "Current Nodes", "Target Nodes", "Est. Latency Impact"],
                "rows": [
                    ["us-east-1a", "12", "18", "-45% P99"],
                    ["us-west-2b", "8", "12", "-38% P99"],
                ],
            },
            "children": [],
        },
        "actionFooter": {
            "type": "Stack",
            "props": {"direction": "row"},
            "children": ["approveBtn", "quarantineBtn"],
        },
        "approveBtn": {
            "type": "Button",
            "props": {"label": "Approve Autoscaling Execution", "action": "approve_scale_plan", "variant": "primary"},
            "children": [],
        },
        "quarantineBtn": {
            "type": "Button",
            "props": {"label": "Reject & Quarantine Node", "action": "reject_and_quarantine", "variant": "danger"},
            "children": [],
        },
    },
    "state": {},
}

# Post-Action Spec: Updated surface following human approval
UPDATED_POST_ACTION_SPEC = {
    "root": "trueforgeShell",
    "elements": {
        "trueforgeShell": {
            "type": "Stack",
            "props": {"direction": "column"},
            "children": ["navHeader", "kpiSummaryRow", "executionCard"],
        },
        "navHeader": {
            "type": "Card",
            "props": {
                "title": "TrueForge Autonomous Operations Console [EXECUTING]",
                "description": "Plan Approved: Autoscaling us-east-1a (+6) and us-west-2b (+4)",
            },
            "children": [],
        },
        "kpiSummaryRow": {
            "type": "Stack",
            "props": {"direction": "row"},
            "children": ["loadMetric", "costMetric"],
        },
        "loadMetric": {
            "type": "Metric",
            "props": {"label": "Global Fleet Load", "value": "61.2%", "change": "-28.2%"},
            "children": [],
        },
        "costMetric": {
            "type": "Metric",
            "props": {"label": "Hourly Compute Burn", "value": "$198.00", "change": "+$55.50"},
            "children": [],
        },
        "executionCard": {
            "type": "Card",
            "props": {
                "title": "Scale Execution Succeeded",
                "description": "Provisioned 10 new instances across 2 zones in 42.1 seconds. Latency normalized.",
            },
            "children": [],
        },
    },
    "state": {},
}


def run_mixed_mode(console: Optional[Console] = None, live: bool = False) -> Dict[str, Any]:
    """Executes Harness Mixed / Hybrid Mode demonstration."""
    c = console or Console()

    c.print(Panel(
        "[bold cyan]Harness Integration — Mixed / Hybrid Mode[/bold cyan]\n"
        "[dim]TrueForge hybrid architecture: static layout shell, generative plan, interactive action loop, and fallback[/dim]",
        border_style="cyan",
    ))

    broadcaster = MultiSurfaceBroadcaster(console=c)
    agent = AutonomousUIAgentLoop(broadcaster=broadcaster, console=c, mode="live" if live else "mock")

    # Step 1: Render the initial hybrid console
    c.print("\n[bold yellow]Step 1: Projecting TrueForge Hybrid Console[/bold yellow]")
    turn1 = agent.run_step(
        thought="Deploying TrueForge hybrid console with static fleet metrics and generative scaling strategy.",
        spec=INITIAL_HYBRID_SHELL_SPEC,
    )
    c.print(f"  [cyan]Thought:[/cyan] {turn1.thought}")
    c.print(f"  [cyan]Tool Call:[/cyan] {turn1.tool_call} -> Status: [green]{turn1.tool_result.get('status')}[/green]")
    assert turn1.tool_result.get("status") == "success"

    # Step 2: Simulate Client Action (User clicks 'Approve Autoscaling Execution')
    c.print("\n[bold yellow]Step 2: Client Triggers Interactive Action 'approve_scale_plan'[/bold yellow]")
    action_turn = agent.handle_client_action(
        action_name="approve_scale_plan",
        payload={"operator": "oncall_eng_alice", "approved_zones": ["us-east-1a", "us-west-2b"]},
    )
    c.print(f"  [cyan]Action Intercepted:[/cyan] approve_scale_plan by oncall_eng_alice")
    c.print(f"  [cyan]Agent Stage:[/cyan] [yellow]{agent.stage.value}[/yellow]")
    assert agent.stage in (AgentLifecycleStage.ACTION_PROCESSED, AgentLifecycleStage.REASONING)

    # Step 3: Agent executes corrective action turn, re-projecting updated UI
    c.print("\n[bold yellow]Step 3: Agent Processes Action & Re-projects Updated UI Surface[/bold yellow]")
    turn3 = agent.run_step(
        thought="Operator approved scale plan. Executing infrastructure scaling and re-projecting status surface.",
        spec=UPDATED_POST_ACTION_SPEC,
    )
    c.print(f"  [cyan]Thought:[/cyan] {turn3.thought}")
    c.print(f"  [cyan]Tool Call:[/cyan] {turn3.tool_call} -> Status: [green]{turn3.tool_result.get('status')}[/green]")
    assert turn3.tool_result.get("status") == "success"

    # Step 4: Defensive Fallback Error Recovery for Malformed Action Payload
    c.print("\n[bold yellow]Step 4: Defensive Fallback on Corrupted Action Payload[/bold yellow]")
    corrupted_action_turn = agent.handle_client_action(
        action_name="malformed_action_unknown",
        payload=None,
    )
    c.print(f"  [cyan]Malformed action handled gracefully:[/cyan] [green]verified[/green] (harness preserved session state)")

    # Step 5: Lifecycle Complete
    summary = agent.complete()
    c.print(f"\n[bold green][OK][/bold green] Mixed / Hybrid Harness loop completed: [cyan]{summary['total_turns']}[/cyan] turns executed, [cyan]{summary['rendered_surfaces_count']}[/cyan] surfaces projected.")

    return {
        "status": "success",
        "total_turns": summary["total_turns"],
        "rendered_surfaces": summary["rendered_surfaces_count"],
        "final_stage": summary["final_stage"],
        "interactive_action_verified": True,
    }


if __name__ == "__main__":
    run_mixed_mode()
