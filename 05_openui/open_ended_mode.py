"""Codelab 05 — OpenUI Lang: Open-Ended UX Mode.

Demonstrates agent-synthesized DSL programs creating bespoke, custom component
hierarchies beyond basic catalog primitives (e.g. complex workflow stages,
graph nodes, and specialized interactive visualizations).
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

# Agent-synthesized bespoke DSL program with non-standard domain primitives
OPEN_ENDED_SYNTHESIS_PROGRAM = """
root = WorkflowPipeline(name="Agentic ETL & Auto-Remediation", status="Active", children=[stageIngest, stageValidate, stageTransform, stageDeploy])
stageIngest = WorkflowStage(title="1. Event Ingestion", worker="stream-ingest-v2", throughput="14,200 msg/sec", health="Optimal")
stageValidate = WorkflowStage(title="2. Schema & PII Filtering", worker="guardrail-filter", rejected="12 records", health="Optimal")
stageTransform = WorkflowStage(title="3. Embedding Generation", worker="gemini-embedding-001", batchSize=128, health="Degraded")
stageDeploy = WorkflowStage(title="4. Vector Index Sync", worker="bigquery-vector-sink", latency="48ms", health="Optimal")
detailsPanel = Card(title="Stage 3 Diagnostics", description="Embedding latency elevated due to API rate throttling")
detailsStack = Stack([throttleMetric, retryBtn], direction="row")
throttleMetric = Metric("Rate Limit Backoff", "2.4s", change="+400%")
retryBtn = Button("Trigger Instant Worker Scale-Out", action="scale_workers", variant="danger")
"""


def run_open_ended_mode(console: Optional[Console] = None, live: bool = False) -> Dict[str, Any]:
    """Executes OpenUI Open-Ended UX Mode demonstration."""
    c = console or Console()

    c.print(Panel(
        "[bold cyan]OpenUI Lang DSL — Open-Ended UX Mode[/bold cyan]\n"
        "[dim]Agent synthesis of custom, unconstrained component hierarchies and domain-specific primitives[/dim]",
        border_style="cyan",
    ))

    # Parse synthesized OpenUI program
    c.print("\n[bold yellow]1. Parsing Agent-Synthesized OpenUI DSL[/bold yellow]")
    parser = OpenUIParser()
    program = parser.parse_program(OPEN_ENDED_SYNTHESIS_PROGRAM)

    # Inspect synthesized components
    table = Table(title="Synthesized Custom Components", border_style="magenta")
    table.add_column("Node ID", style="cyan")
    table.add_column("Custom Component", style="bold magenta")
    table.add_column("Type Classification", style="yellow")
    table.add_column("Extracted Attributes", style="white")

    standard_types = {"Stack", "Card", "Metric", "Table", "Button", "TextField", "Text"}

    for node_id, node in program.nodes.items():
        is_custom = node.component not in standard_types
        type_class = "[bold magenta]Bespoke Synthesized[/bold magenta]" if is_custom else "[dim]Standard Primitive[/dim]"
        attr_summary = ", ".join(f"{k}={v}" for k, v in node.props.items() if k != "children")
        table.add_row(node_id, node.component, type_class, attr_summary)

    c.print(table)

    # Check forward references and AST
    c.print(f"[bold green][OK][/bold green] Synthesized program parsed: [cyan]{len(program.nodes)}[/cyan] nodes, [cyan]{len(program.unresolved_references)}[/cyan] unresolved references.")
    assert len(program.unresolved_references) == 0

    # Multi-target compilation
    json_spec = compile_to_json_spec(program)
    react_tree = compile_to_react_tree(program)
    html_output = compile_to_html(program, title="Agentic ETL Pipeline")

    c.print("\n[bold yellow]2. Multi-Target Compilation for Custom Hierarchy[/bold yellow]")
    c.print(f"  - [bold white]JSON UI Spec:[/bold white] {len(json_spec['elements'])} elements (Root: '{json_spec['root']}')")
    c.print(f"  - [bold white]React Tree Root:[/bold white] <{react_tree['component']} children={len(react_tree['children'])} />")
    c.print(f"  - [bold white]HTML Artifact:[/bold white] {len(html_output)} bytes with embedded custom visualizers.")

    # Tree visualization
    tree = Tree(f"[bold magenta]{react_tree['component']}[/bold magenta] (root)")
    for child in react_tree.get("children", []):
        child_props = child["props"]
        label = child_props.get("title") or child_props.get("name") or child["component"]
        tree.add(f"[cyan]{child['component']}[/cyan]: {label}")

    c.print("\n[bold yellow]3. Hierarchical Component Tree:[/bold yellow]")
    c.print(tree)

    return {
        "status": "success",
        "program": OPEN_ENDED_SYNTHESIS_PROGRAM.strip(),
        "node_count": len(program.nodes),
        "custom_components": [n.component for n in program.nodes.values() if n.component not in standard_types],
        "json_spec": json_spec,
        "react_tree": react_tree,
        "html_artifact_length": len(html_output),
    }


if __name__ == "__main__":
    run_open_ended_mode()
