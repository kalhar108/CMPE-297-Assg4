"""Codelab 06 — Harness Integration: Static Mode.

Demonstrates deterministic single-turn UI specification rendering and validation
invoking render_ui tool with simultaneous projection to terminal and web surfaces.
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
    from .multi_surface import MultiSurfaceBroadcaster, validate_ui_spec
except (ImportError, ValueError):
    from multi_surface import MultiSurfaceBroadcaster, validate_ui_spec

# Deterministic golden UI specification for static infrastructure monitoring
STATIC_CLUSTER_SPEC = {
    "root": "clusterDashboard",
    "elements": {
        "clusterDashboard": {
            "type": "Stack",
            "props": {"direction": "column"},
            "children": ["headerCard", "metricsStack", "nodeTable", "refreshButton"],
        },
        "headerCard": {
            "type": "Card",
            "props": {
                "title": "Production Kubernetes Cluster: k8s-prod-us-east",
                "description": "Region: us-east-1 | 24 Active Pods | Zero Pending Incidents",
            },
            "children": [],
        },
        "metricsStack": {
            "type": "Stack",
            "props": {"direction": "row"},
            "children": ["cpuMetric", "memMetric", "ingressMetric"],
        },
        "cpuMetric": {
            "type": "Metric",
            "props": {"label": "Cluster CPU Load", "value": "42.8%", "change": "-2.1%"},
            "children": [],
        },
        "memMetric": {
            "type": "Metric",
            "props": {"label": "Allocated Memory", "value": "78.4 GB", "change": "+4.6%"},
            "children": [],
        },
        "ingressMetric": {
            "type": "Metric",
            "props": {"label": "Ingress Throughput", "value": "18.4k req/s", "change": "+12.0%"},
            "children": [],
        },
        "nodeTable": {
            "type": "Table",
            "props": {
                "columns": ["Node ID", "Instance Type", "Pods", "Status"],
                "rows": [
                    ["ip-10-0-1-12", "c6i.2xlarge", "8", "Ready"],
                    ["ip-10-0-2-45", "c6i.2xlarge", "9", "Ready"],
                    ["ip-10-0-3-88", "c6i.2xlarge", "7", "Ready"],
                ],
            },
            "children": [],
        },
        "refreshButton": {
            "type": "Button",
            "props": {"label": "Refresh Cluster Telemetry", "action": "poll_telemetry", "variant": "primary"},
            "children": [],
        },
    },
    "state": {},
}


def run_static_mode(console: Optional[Console] = None) -> Dict[str, Any]:
    """Executes Harness Static Mode demonstration."""
    c = console or Console()

    c.print(Panel(
        "[bold cyan]Harness Integration — Static Mode[/bold cyan]\n"
        "[dim]Deterministic single-turn UI specification rendering, schema validation, and dual-surface projection[/dim]",
        border_style="cyan",
    ))

    # Phase 1: Schema Validation
    c.print("\n[bold yellow]1. Catalog Schema Validation[/bold yellow]")
    is_valid, error = validate_ui_spec(STATIC_CLUSTER_SPEC)
    assert is_valid, f"Validation failed: {error}"
    c.print(f"[bold green][OK][/bold green] Static UI specification validated against component catalog (0 errors).")

    # Phase 2: Multi-Surface Projection
    c.print("\n[bold yellow]2. Invoking render_ui(spec, target='all')[/bold yellow]")
    broadcaster = MultiSurfaceBroadcaster(console=c)
    receipt = broadcaster.render_ui(STATIC_CLUSTER_SPEC, target="all")

    c.print(f"[bold green][OK][/bold green] Render receipt received: Status=[green]{receipt['status']}[/green]")
    c.print(f"  - Surfaces projected: [cyan]{receipt['surfaces_projected']}[/cyan]")
    c.print(f"  - Elements count: [cyan]{receipt['elements_count']}[/cyan] (Root: '{receipt['root']}')")
    c.print(f"  - Web SSE event queued: [cyan]{broadcaster.sse_event_queue.qsize()}[/cyan] event(s)")

    # Assert dual-surface projection
    assert "terminal" in receipt["surfaces_projected"]
    assert "web" in receipt["surfaces_projected"]
    assert receipt["elements_count"] == 8

    # Phase 3: Export Web HTML Artifact
    web_html = broadcaster.export_web_html(title="Production Kubernetes Cluster Telemetry")
    c.print(f"  - Web HTML artifact length: [cyan]{len(web_html)}[/cyan] bytes")

    return {
        "status": "success",
        "receipt": receipt,
        "spec_root": STATIC_CLUSTER_SPEC["root"],
        "elements_count": len(STATIC_CLUSTER_SPEC["elements"]),
        "web_html_length": len(web_html),
    }


if __name__ == "__main__":
    run_static_mode()
