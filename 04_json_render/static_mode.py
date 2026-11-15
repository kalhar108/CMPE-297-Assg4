"""Codelab 4: JSON Render — Mode 1: Static Mode.

Demonstrates deterministic JSON UI specification rendering to dual targets:
1. Terminal console via Rich (TerminalRenderer).
2. Web browser via responsive HTML5 (DomRenderer).
Zero LLM runtime modification; validates catalog compliance and dual-surface consistency.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 1. Resolve Project Root (assignment-4-genux/)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 2. Resolve Module Directory (04_json_render/)
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from typing import Any, Dict, Optional
from rich.console import Console
from rich.panel import Panel

try:
    from .catalog import DEFAULT_CATALOG, ElementNode, JSONRenderSpec
    from .renderers import DomRenderer, TerminalRenderer
except (ImportError, ValueError):
    from catalog import DEFAULT_CATALOG, ElementNode, JSONRenderSpec
    from renderers import DomRenderer, TerminalRenderer


def get_static_spec() -> JSONRenderSpec:
    """Returns a deterministic, schema-valid JSON Render specification."""
    elements = {
        "root-container": ElementNode(
            type="Container",
            props={"direction": "column", "gap": "16px"},
            children=["summary-card", "kpi-row", "table-card"],
        ),
        "summary-card": ElementNode(
            type="Card",
            props={
                "title": "Cloud Infrastructure Fleet Overview",
                "subtitle": "Silicon Valley Regional Cluster — Zone us-west-1",
                "variant": "primary",
            },
            children=["summary-container"],
        ),
        "summary-container": ElementNode(
            type="Container",
            props={"direction": "row", "gap": "12px"},
            children=["metric-nodes", "metric-health"],
        ),
        "metric-nodes": ElementNode(
            type="Metric",
            props={"label": "Active Compute Nodes", "value": "128", "delta": "+12", "trend": "up"},
            children=[],
        ),
        "metric-health": ElementNode(
            type="Metric",
            props={"label": "Fleet Health Score", "value": "99.8%", "delta": "+0.4%", "trend": "up"},
            children=[],
        ),
        "kpi-row": ElementNode(
            type="Container",
            props={"direction": "row", "gap": "12px"},
            children=["metric-cpu", "metric-mem", "metric-lat"],
        ),
        "metric-cpu": ElementNode(
            type="Metric",
            props={"label": "CPU Utilization", "value": "42.5%", "delta": "-3.1%", "trend": "down"},
            children=[],
        ),
        "metric-mem": ElementNode(
            type="Metric",
            props={"label": "Memory Allocated", "value": "384 GB", "delta": "+8 GB", "trend": "up"},
            children=[],
        ),
        "metric-lat": ElementNode(
            type="Metric",
            props={"label": "P99 Gateway Latency", "value": "14 ms", "delta": "steady", "trend": "neutral"},
            children=[],
        ),
        "table-card": ElementNode(
            type="Card",
            props={"title": "Primary Service Topologies", "variant": "default"},
            children=["services-table"],
        ),
        "services-table": ElementNode(
            type="Table",
            props={
                "columns": ["Service Name", "Pods", "Version", "Status"],
                "rows": [
                    ["gateway-proxy", 8, "v2.4.1", "RUNNING"],
                    ["auth-authenticator", 4, "v1.9.0", "RUNNING"],
                    ["billing-engine", 3, "v3.1.2", "RUNNING"],
                    ["event-bus-kafka", 6, "v3.7.0", "HEALTHY"],
                ],
                "striped": True,
            },
            children=[],
        ),
    }

    return JSONRenderSpec(
        root="root-container",
        elements=elements,
        state={"region": "us-west-1", "fleet": "production"},
    )


def run_static_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes static mode demonstration for JSON Render."""
    c = console or Console()
    c.print("[bold yellow]=== Codelab 4 (JSON Render): Mode 1 — Static Mode ===[/bold yellow]")

    # 1. Load static spec and validate against catalog
    spec = get_static_spec()
    errors = DEFAULT_CATALOG.validate_spec(spec)
    if errors:
        raise ValueError(f"Static spec validation failed: {errors}")

    c.print(f"[green][OK] Spec loaded and catalog validated. Elements: {len(spec.elements)}, Root: '{spec.root}'[/green]")

    # 2. Render to Target 1: Terminal via Rich
    c.print("\n[bold cyan]Target 1: Terminal Console Surface (TerminalRenderer)[/bold cyan]")
    term_renderer = TerminalRenderer(console=c)
    term_renderer.render(spec)

    # 3. Render to Target 2: Web DOM via HTML
    c.print("\n[bold cyan]Target 2: DOM Web Surface (DomRenderer)[/bold cyan]")
    dom_renderer = DomRenderer()
    html_output = dom_renderer.render(spec)

    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "static_render_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    c.print(f"[green][OK] HTML rendered and written to: {os.path.basename(target_path)} ({len(html_output)} bytes)[/green]")

    return {
        "mode": "static",
        "elements_count": len(spec.elements),
        "validation_errors": errors,
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_static_mode(mock=True)
