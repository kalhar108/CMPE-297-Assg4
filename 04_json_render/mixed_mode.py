"""Codelab 4: JSON Render — Mode 4: Mixed / Hybrid Mode.

Demonstrates dual-surface rendering combining catalog shells with dynamic interactive actions:
1. Fixed catalog shell displays header, system health KPIs, and action buttons.
2. User triggers an action button ('action: "scale_cluster"').
3. Server emits incremental RFC 6902 JSON Patches mutating specific state keys and element props.
4. Compiler updates the live document without requiring a full re-render.
5. Verifies dual-surface consistency across Terminal and DOM.
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

try:
    from .catalog import DEFAULT_CATALOG
    from .patch_compiler import createSpecStreamCompiler
    from .renderers import DomRenderer, TerminalRenderer
except (ImportError, ValueError):
    from catalog import DEFAULT_CATALOG
    from patch_compiler import createSpecStreamCompiler
    from renderers import DomRenderer, TerminalRenderer


INITIAL_HYBRID_PATCHES: List[str] = [
    '{"op": "add", "path": "/state", "value": {"cluster": {"nodes": 12, "tps": "4,200 rps", "status": "STABLE"}, "audit": []}}',
    '{"op": "add", "path": "/elements/hybrid-root", "value": {"type": "Container", "props": {"direction": "column", "gap": "16px"}, "children": ["fixed-header", "dynamic-body", "shell-card", "actions-card", "log-card"]}}',
    '{"op": "add", "path": "/root", "value": "hybrid-root"}',
    '{"op": "add", "path": "/elements/fixed-header", "value": {"type": "Header", "props": {"title": "Analytics Console"}, "children": []}}',
    '{"op": "add", "path": "/elements/dynamic-body", "value": {"type": "Placeholder", "props": {"loading": true, "text": "Awaiting server turn..."}, "children": []}}',
    '{"op": "add", "path": "/elements/shell-card", "value": {"type": "Card", "props": {"title": "Autonomous Cluster Controller", "subtitle": "Hybrid Architecture: Fixed Catalog Shell + Interactive Action Loop", "variant": "primary"}, "children": ["kpi-row"]}}',
    '{"op": "add", "path": "/elements/kpi-row", "value": {"type": "Container", "props": {"direction": "row", "gap": "12px"}, "children": ["metric-nodes", "metric-tps", "metric-status"]}}',
    '{"op": "add", "path": "/elements/metric-nodes", "value": {"type": "Metric", "props": {"label": "Cluster Nodes", "value": {"$state": "/cluster/nodes"}, "delta": "+0", "trend": "neutral"}, "children": []}}',
    '{"op": "add", "path": "/elements/metric-tps", "value": {"type": "Metric", "props": {"label": "Throughput", "value": {"$state": "/cluster/tps"}, "delta": "steady", "trend": "neutral"}, "children": []}}',
    '{"op": "add", "path": "/elements/metric-status", "value": {"type": "Metric", "props": {"label": "Cluster State", "value": {"$state": "/cluster/status"}, "trend": "up"}, "children": []}}',
    '{"op": "add", "path": "/elements/actions-card", "value": {"type": "Card", "props": {"title": "Interactive Operations Panel", "variant": "default"}, "children": ["btn-row"]}}',
    '{"op": "add", "path": "/elements/btn-row", "value": {"type": "Container", "props": {"direction": "row", "gap": "12px"}, "children": ["btn-scale", "btn-refresh"]}}',
    '{"op": "add", "path": "/elements/btn-scale", "value": {"type": "Button", "props": {"label": "Scale Cluster (+4 Pods)", "action": "scale_cluster", "variant": "primary"}, "children": []}}',
    '{"op": "add", "path": "/elements/btn-refresh", "value": {"type": "Button", "props": {"label": "Refresh Telemetry", "action": "refresh_telemetry", "variant": "default"}, "children": []}}',
    '{"op": "add", "path": "/elements/log-card", "value": {"type": "Card", "props": {"title": "Action Execution Audit Trail", "variant": "default"}, "children": ["audit-table"]}}',
    '{"op": "add", "path": "/elements/audit-table", "value": {"type": "Table", "props": {"columns": ["Timestamp", "Action", "Detail", "Result"], "rows": [["2026-11-05T20:00:00Z", "init", "Controller online", "READY"]], "striped": true}, "children": []}}',
]


def run_mixed_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes mixed/hybrid mode interactive action loop demonstration."""
    c = console or Console()
    c.print("[bold yellow]=== Codelab 4 (JSON Render): Mode 4 — Mixed / Hybrid Mode ===[/bold yellow]")

    # 1. Compile initial shell
    compiler = createSpecStreamCompiler(catalog=DEFAULT_CATALOG)
    for p in INITIAL_HYBRID_PATCHES:
        compiler.compile_line(p)

    c.print("[dim]1. Fixed catalog shell compiled. Rendering initial state...[/dim]")
    term_renderer = TerminalRenderer(console=c)
    term_renderer.render(compiler.get_spec())

    # 2. Simulate User Interaction: clicking 'scale_cluster'
    c.print("\n[bold cyan]2. Simulating User Action: Click '[ Scale Cluster (+4 Pods) ]'[/bold cyan]")
    incremental_action_patches = [
        # Dynamic body replacement with generative Refreshed Sales Metric
        '{"op": "replace", "path": "/elements/dynamic-body", "value": {"type": "Metric", "props": {"label": "Refreshed Sales", "value": "$9,800"}, "children": []}}',
        # Update state values
        '{"op": "replace", "path": "/state/cluster/nodes", "value": 16}',
        '{"op": "replace", "path": "/state/cluster/tps", "value": "7,800 rps"}',
        '{"op": "replace", "path": "/state/cluster/status", "value": "SCALING_COMPLETE"}',
        # Update metric delta tags
        '{"op": "replace", "path": "/elements/metric-nodes/props/delta", "value": "+4 pods"}',
        '{"op": "replace", "path": "/elements/metric-nodes/props/trend", "value": "up"}',
        '{"op": "replace", "path": "/elements/metric-tps/props/delta", "value": "+85.7%"}',
        '{"op": "replace", "path": "/elements/metric-tps/props/trend", "value": "up"}',
        # Append to audit table rows
        '{"op": "add", "path": "/elements/audit-table/props/rows/-", "value": ["2026-11-05T20:10:00Z", "scale_cluster", "Added 4 worker nodes to pool", "SUCCESS"]}',
    ]

    for p in incremental_action_patches:
        compiler.compile_line(p)

    c.print(f"[green][OK] Applied {len(incremental_action_patches)} incremental patches. Re-rendering updated surface...[/green]")

    # 3. Re-render updated state
    updated_spec = compiler.get_spec()
    c.print("\n[bold cyan]Updated Terminal Surface:[/bold cyan]")
    term_renderer.render(updated_spec)

    # 4. Render to DOM
    dom_renderer = DomRenderer()
    html_output = dom_renderer.render(updated_spec)

    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "hybrid_mixed_render_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    c.print(f"[green][OK] Updated HTML written to: {os.path.basename(target_path)} ({len(html_output)} bytes)[/green]")

    # Serialize elements dictionary for test contract compatibility
    elements_dict = {
        k: ({"type": v.type, "props": v.props, "children": v.children} if hasattr(v, "type") else v)
        for k, v in updated_spec.elements.items()
    }

    return {
        "mode": "mixed",
        "root": updated_spec.root,
        "elements": elements_dict,
        "state": updated_spec.state,
        "initial_patches": len(INITIAL_HYBRID_PATCHES),
        "action_patches": len(incremental_action_patches),
        "updated_state": updated_spec.state,
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_mixed_mode(mock=True)
