"""Codelab 05 — OpenUI Lang: Mixed / Hybrid Mode.

Demonstrates the TrueForge-style hybrid architecture:
1. Static DSL template shell (Navigation header, KPI metrics, fixed action bar).
2. Embedded agent-generated dynamic components.
3. Isolated HtmlArtifact escape hatch with strict CSP sandbox.
4. Defensive error recovery: graceful isolation of malformed lines with fallback cards.
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

try:
    from .parser import OpenUIParser, parse_program
    from .compiler import compile_to_html, compile_to_json_spec, compile_to_react_tree
except (ImportError, ValueError):
    from parser import OpenUIParser, parse_program
    from compiler import compile_to_html, compile_to_json_spec, compile_to_react_tree

# Hybrid DSL Program: Static application shell + embedded generative widget + HtmlArtifact escape hatch
HYBRID_TEMPLATE_PROGRAM = """
root = Stack([appHeader, mainGrid, artifactSection], direction="column")
appHeader = Card(title="TrueForge Analytics Command Center", description="Production Cluster: us-east-1a")
mainGrid = Stack([kpiRow, dynamicSection], direction="column")
kpiRow = Stack([kpi1, kpi2, kpi3], direction="row")
kpi1 = Metric("Total Portfolio Value", "$1,420,850", change="+7.4%")
kpi2 = Metric("Active Hedging Ratio", "68.2%", change="+2.1%")
kpi3 = Metric("VaR (99% Confidence)", "$42,100", change="-1.2%")
dynamicSection = Card(title="Agent Recommendations", description="Synthesized dynamic strategy cards")
artifactSection = HtmlArtifact("Monte Carlo Portfolio Risk Simulator", "<!DOCTYPE html><html><head><style>body{font-family:sans-serif;color:#333;padding:12px;text-align:center;}button{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;}</style></head><body><h4>Interactive Risk Simulator</h4><p>Simulated 10,000 iterations for scenario: Tech Downturn</p><button onclick=\\"alert('Simulation re-run complete: VaR remains within tolerance.')\\">Run Simulation</button></body></html>")
"""

# Program demonstrating defensive error recovery when a line contains syntax errors
FAULTY_HYBRID_PROGRAM = """
root = Stack([metricCard, corruptedWidget, actionBtn], direction="column")
metricCard = Card(title="Cluster Telemetry", description="Telemetry streaming")
123_corrupted_id = InvalidSyntaxStatement(missing_quotes)
actionBtn = Button("Recover Surface", action="retry_surface")
"""


def run_mixed_mode(console: Optional[Console] = None, live: bool = False) -> Dict[str, Any]:
    """Executes OpenUI Mixed / Hybrid Mode demonstration."""
    c = console or Console()

    c.print(Panel(
        "[bold cyan]OpenUI Lang DSL — Mixed / Hybrid Mode[/bold cyan]\n"
        "[dim]Deterministic template shell + generative dynamic cards + sandboxed HtmlArtifact + error recovery[/dim]",
        border_style="cyan",
    ))

    # Phase 1: Parse and compile the hybrid template
    c.print("\n[bold yellow]1. Parsing Hybrid Template with Sandboxed HtmlArtifact[/bold yellow]")
    parser = OpenUIParser()
    program = parser.parse_program(HYBRID_TEMPLATE_PROGRAM)

    # Check components
    table = Table(title="Hybrid Architecture Components", border_style="cyan")
    table.add_column("Node ID", style="cyan")
    table.add_column("Component", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Isolation / Properties", style="white")

    for node_id, node in program.nodes.items():
        if node.component == "HtmlArtifact":
            category = "[bold red]Sandboxed Escape Hatch[/bold red]"
            details = f"Title: {node.props.get('title')} (Strict CSP meta tag)"
        elif node_id in ("root", "appHeader", "mainGrid", "kpiRow"):
            category = "[bold blue]Static Template Shell[/bold blue]"
            details = f"Children: {', '.join(node.children)}"
        else:
            category = "[bold green]Generative Component[/bold green]"
            details = ", ".join(f"{k}={v}" for k, v in node.props.items() if k != "children")
        table.add_row(node_id, node.component, category, details)

    c.print(table)

    json_spec = compile_to_json_spec(program)
    html_output = compile_to_html(program, title="TrueForge Hybrid Analytics")
    c.print(f"[bold green][OK][/bold green] Hybrid program parsed successfully: [cyan]{len(program.nodes)}[/cyan] nodes compiled.")
    c.print(f"  - [bold white]HtmlArtifact presence:[/bold white] [green]verified[/green] (rendered inside iframe with allow-scripts and strict CSP).")
    assert "artifactSection" in json_spec["elements"]
    assert "Content-Security-Policy" in html_output

    # Phase 2: Defensive Syntax Error Recovery
    c.print("\n[bold yellow]2. Defensive Error Recovery Demonstration[/bold yellow]")
    c.print("[dim]Injecting faulty DSL program with unbalanced quotation and malformed syntax...[/dim]")

    fault_parser = OpenUIParser()
    fault_program = fault_parser.parse_program(FAULTY_HYBRID_PROGRAM)

    c.print(f"  - Syntax errors caught without crashing: [bold yellow]{len(fault_program.syntax_errors)}[/bold yellow]")
    for err in fault_program.syntax_errors:
        c.print(f"    [red]Line {err['line']}:[/red] {err['error']} -> Statement: [dim]'{err['statement']}'[/dim]")

    # Check that healthy nodes survived
    healthy_ids = list(fault_program.nodes.keys())
    c.print(f"  - Healthy nodes preserved intact: [green]{healthy_ids}[/green]")
    assert "root" in fault_program.nodes
    assert "metricCard" in fault_program.nodes
    assert "actionBtn" in fault_program.nodes

    # Compilation of error-recovering program
    recovering_json = compile_to_json_spec(fault_program)
    # Check that unresolved/corrupted widget gets a skeleton placeholder
    c.print(f"  - Corrupted node handling: Auto-synthesized skeleton placeholder in JSON spec: [cyan]{recovering_json['elements'].get('corruptedWidget', {}).get('type')}[/cyan]")

    c.print(f"\n[bold green][OK][/bold green] Mixed / Hybrid Mode demonstrated complete feature integrity.")

    return {
        "status": "success",
        "primary_nodes": len(program.nodes),
        "has_html_artifact": "artifactSection" in program.nodes,
        "syntax_errors_handled": len(fault_program.syntax_errors),
        "preserved_nodes": healthy_ids,
        "json_spec": json_spec,
        "html_artifact_length": len(html_output),
    }


if __name__ == "__main__":
    run_mixed_mode()
