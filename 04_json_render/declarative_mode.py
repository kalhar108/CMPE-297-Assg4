"""Codelab 4: JSON Render — Mode 2: Declarative Mode.

Demonstrates streaming RFC 6902 patch compilation with dynamic state bindings:
1. Emits incremental patch stream line-by-line via createSpecStreamCompiler.
2. Tracks early first-paint latency metrics (first-paint achieved upon root element linkage).
3. Resolves dynamic {"$state": "/path"} pointer expressions against document state.
4. Validates final assembled specification against catalog schemas.
5. Dual-target renders to Terminal and DOM web outputs.
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


STREAMED_PATCH_LINES: List[str] = [
    # Patch 1: Initialize reactive state
    '{"op": "add", "path": "/state", "value": {"sales": {"q3_gross": "$142,500", "orders_count": 890, "growth": "+18.4%"}, "region": "North America"}}',
    # Patch 2: Add top-level container
    '{"op": "add", "path": "/elements/root-dash", "value": {"type": "Container", "props": {"direction": "column", "gap": "16px"}, "children": ["kpi-card", "sales-chart"]}}',
    # Patch 3: Link root identifier -> Triggers Early First-Paint!
    '{"op": "add", "path": "/root", "value": "root-dash"}',
    # Patch 4: Add KPI card container
    '{"op": "add", "path": "/elements/kpi-card", "value": {"type": "Card", "props": {"title": "Enterprise Sales Performance", "subtitle": "Streaming Patches with Dynamic State Binding", "variant": "accent"}, "children": ["kpi-row"]}}',
    # Patch 5: Add nested horizontal row container
    '{"op": "add", "path": "/elements/kpi-row", "value": {"type": "Container", "props": {"direction": "row", "gap": "12px"}, "children": ["metric-rev", "metric-ord", "metric-growth"]}}',
    # Patch 6: Metric with dynamic $state binding to /sales/q3_gross
    '{"op": "add", "path": "/elements/metric-rev", "value": {"type": "Metric", "props": {"label": "Gross Revenue", "value": {"$state": "/sales/q3_gross"}, "delta": "+$22k", "trend": "up"}, "children": []}}',
    # Patch 7: Metric with dynamic $state binding to /sales/orders_count
    '{"op": "add", "path": "/elements/metric-ord", "value": {"type": "Metric", "props": {"label": "Total Orders", "value": {"$state": "/sales/orders_count"}, "delta": "+112", "trend": "up"}, "children": []}}',
    # Patch 8: Metric with dynamic $state binding to /sales/growth
    '{"op": "add", "path": "/elements/metric-growth", "value": {"type": "Metric", "props": {"label": "YoY Growth", "value": {"$state": "/sales/growth"}, "delta": "+4.2%", "trend": "up"}, "children": []}}',
    # Patch 9: Add Chart element
    '{"op": "add", "path": "/elements/sales-chart", "value": {"type": "Chart", "props": {"chart_type": "bar", "title": "Revenue Distribution by Tier ($k)", "data": {"Enterprise Cloud": 85, "SMB Solutions": 42, "Direct Web": 15.5}}, "children": []}}',
]


def run_declarative_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes declarative mode streaming patch compilation demonstration."""
    c = console or Console()
    c.print("[bold yellow]=== Codelab 4 (JSON Render): Mode 2 — Declarative Mode ===[/bold yellow]")

    compiler = createSpecStreamCompiler(catalog=DEFAULT_CATALOG)
    c.print(f"[dim]Streaming {len(STREAMED_PATCH_LINES)} RFC 6902 patch lines to compiler...[/dim]")

    # Compile stream line-by-line and monitor progressive compilation
    stream_progress_table = Table(title="Progressive Patch Compilation Stream", border_style="cyan")
    stream_progress_table.add_column("Line #", style="dim", width=6)
    stream_progress_table.add_column("Op & Target Path", style="bold yellow")
    stream_progress_table.add_column("Doc Status", style="green")
    stream_progress_table.add_column("Paint Milestone", style="bold magenta")

    for idx, line in enumerate(STREAMED_PATCH_LINES, 1):
        compiler.compile_line(line)
        patch_info = compiler.patch_history[-1] if compiler.patch_history else {}
        op_path = f"{patch_info.get('op', '')} {patch_info.get('path', '')}"

        milestone = ""
        if compiler.first_paint_patch_idx == idx:
            milestone = "[FIRST PAINT TRIGGERED]"

        elements_count = len(compiler.document.get("elements", {}))
        stream_progress_table.add_row(
            str(idx),
            op_path,
            f"{elements_count} elements, root={'yes' if compiler.document.get('root') else 'no'}",
            milestone,
        )

    c.print(stream_progress_table)

    # Validate assembled specification
    spec = compiler.get_spec()
    errors = DEFAULT_CATALOG.validate_spec(spec)
    if errors:
        raise ValueError(f"Assembled spec catalog validation failed: {errors}")

    c.print(f"\n[green][OK] Stream compiled cleanly! Total patches: {len(compiler.patch_history)}, Skipped: {len(compiler.skipped)}[/green]")
    c.print(f"[bold cyan]First-Paint achieved at patch #{compiler.first_paint_patch_idx} of {len(STREAMED_PATCH_LINES)} "
            f"({(compiler.first_paint_patch_idx / len(STREAMED_PATCH_LINES) * 100):.1f}% of total stream)[/bold cyan]")

    # Dual-target rendering
    c.print("\n[bold cyan]Target 1: Terminal Console Surface (TerminalRenderer)[/bold cyan]")
    term_renderer = TerminalRenderer(console=c)
    term_renderer.render(spec)

    c.print("\n[bold cyan]Target 2: DOM Web Surface (DomRenderer)[/bold cyan]")
    dom_renderer = DomRenderer()
    html_output = dom_renderer.render(spec)

    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "declarative_patch_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    c.print(f"[green][OK] HTML rendered and written to: {os.path.basename(target_path)} ({len(html_output)} bytes)[/green]")

    return {
        "mode": "declarative",
        "total_patches": len(compiler.patch_history),
        "skipped_patches": len(compiler.skipped),
        "first_paint_patch_idx": compiler.first_paint_patch_idx,
        "resolved_state_metrics": {
            "rev": spec.elements["metric-rev"].props.get("value"),
            "ord": spec.elements["metric-ord"].props.get("value"),
            "growth": spec.elements["metric-growth"].props.get("value"),
        },
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_declarative_mode(mock=True)
