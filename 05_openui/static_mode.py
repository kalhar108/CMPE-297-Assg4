"""Codelab 05 — OpenUI Lang: Static Mode.

Demonstrates deterministic .oui program parsing, forward reference resolution,
AST construction, and multi-target compilation with zero LLM generation.
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

# 2. Resolve Module Directory (05_openui/)
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

try:
    from .parser import OpenUIParser, parse_program
    from .compiler import compile_to_html, compile_to_json_spec, compile_to_react_tree
except (ImportError, ValueError):
    from parser import OpenUIParser, parse_program
    from compiler import compile_to_html, compile_to_json_spec, compile_to_react_tree


# Standard deterministic OpenUI programs
STATIC_KPI_DASHBOARD = """
root = Stack([revMetric, orderMetric, conversionMetric, alertsCard], direction="column")
revMetric = Metric("Monthly Recurring Revenue", "$128,450", change="+14.2%")
orderMetric = Metric("Active Subscriptions", "1,842", change="+8.1%")
conversionMetric = Metric("Trial Conversion Rate", "4.8%", change="-0.4%")
alertsCard = Card(title="System Alerts & Status", description="Zero active outages detected")
"""

STATIC_INCIDENT_VIEW = """
root = Card(title="Incident #4092: Database Latency Spike", description="Reported 12 minutes ago by Sentinel")
root_body = Stack([metricsRow, logTable, actionBtn], direction="column")
metricsRow = Stack([p99Latency, errorRate], direction="row")
p99Latency = Metric("P99 Latency", "482ms", change="+180%")
errorRate = Metric("5xx Error Rate", "1.2%", change="+0.9%")
logTable = Table(columns=["Timestamp", "Service", "Severity", "Message"], rows=[["12:04:11", "auth-db", "WARN", "Connection pool near limit"], ["12:05:02", "order-svc", "ERROR", "Query timeout after 5000ms"]])
actionBtn = Button("Trigger Autoscaling & Purge Cache", action="mitigate_latency")
"""


def run_static_mode(console: Optional[Console] = None) -> Dict[str, Any]:
    """Executes OpenUI Static Mode demonstration."""
    c = console or Console()

    c.print(Panel(
        "[bold cyan]OpenUI Lang DSL — Static Mode[/bold cyan]\n"
        "[dim]Deterministic .oui parsing, AST construction, forward references, and multi-target compilation[/dim]",
        border_style="cyan",
    ))

    # Parse Program 1: KPI Dashboard
    c.print("\n[bold yellow]1. Parsing Program: Executive KPI Dashboard[/bold yellow]")
    parser = OpenUIParser()
    program = parser.parse_program(STATIC_KPI_DASHBOARD)

    # Display AST Symbol Table
    table = Table(title="OpenUI Symbol Table (AST Nodes)", border_style="blue")
    table.add_column("Node ID", style="cyan", justify="left")
    table.add_column("Component", style="green")
    table.add_column("Children", style="magenta")
    table.add_column("Props Summary", style="white")

    for node_id, node in program.nodes.items():
        children_str = ", ".join(node.children) if node.children else "[dim]none[/dim]"
        props_str = ", ".join(f"{k}={v}" for k, v in node.props.items() if k != "children")
        table.add_row(node_id, node.component, children_str, props_str)

    c.print(table)

    # Check forward references
    c.print(f"[bold green][OK][/bold green] Forward references successfully resolved: [cyan]{len(program.nodes)}[/cyan] nodes linked.")
    assert len(program.unresolved_references) == 0, "All forward references must be resolved"

    # Multi-target compilation
    json_spec = compile_to_json_spec(program)
    react_tree = compile_to_react_tree(program)
    html_output = compile_to_html(program, title="Executive KPI Dashboard")

    c.print("\n[bold yellow]2. Multi-Target Compilation Results[/bold yellow]")
    c.print(f"  - [bold white]JSON UI Spec:[/bold white] {len(json_spec['elements'])} elements (Root: '{json_spec['root']}')")
    c.print(f"  - [bold white]React Tree Root:[/bold white] <{react_tree['component']} children={len(react_tree['children'])} />")
    c.print(f"  - [bold white]HTML Artifact:[/bold white] {len(html_output)} bytes compiled with strict CSP header.")

    # Tree visualization
    tree = Tree(f"[bold green]{react_tree['component']}[/bold green] (root)")
    for child in react_tree.get("children", []):
        child_branch = tree.add(f"[cyan]{child['component']}[/cyan] ({child['props'].get('label') or child['props'].get('title') or ''})")
        for gchild in child.get("children", []):
            child_branch.add(f"[magenta]{gchild['component']}[/magenta]")

    c.print("\n[bold yellow]3. Hierarchical Component Tree:[/bold yellow]")
    c.print(tree)

    return {
        "status": "success",
        "program": STATIC_KPI_DASHBOARD.strip(),
        "node_count": len(program.nodes),
        "json_spec": json_spec,
        "react_tree": react_tree,
        "html_artifact_length": len(html_output),
    }


if __name__ == "__main__":
    run_static_mode()
