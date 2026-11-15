"""Codelab 4: JSON Render — Mode 3: Open-Ended UX Mode.

Demonstrates unconstrained layout synthesis with graceful schema parser error recovery:
1. Injects malformed, incomplete, and adversarial JSON patch lines into the stream:
   - Malformed JSON syntax (syntax error).
   - Missing required RFC 6902 fields ('op' or 'path').
   - Unsupported operation verb ('unsupported_op').
2. Compiler intercepts all errors, populates 'compiler.skipped' with detailed diagnostics,
   and continues compiling subsequent valid lines without terminating the stream.
3. Renders open-ended generative elements (CustomCodeBlock interactive JavaScript visualizer).
4. Dual-target renders surviving valid components to Terminal and DOM.
"""

from __future__ import annotations

import json
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


ADVERSARIAL_STREAM_LINES: List[str] = [
    # Valid Patch 1: Root container
    '{"op": "add", "path": "/elements/open-root", "value": {"type": "Container", "props": {"direction": "column", "gap": "16px"}, "children": ["header-card", "canvas-block"]}}',
    '{"op": "add", "path": "/root", "value": "open-root"}',
    # Valid Patch 2: Header card
    '{"op": "add", "path": "/elements/header-card", "value": {"type": "Card", "props": {"title": "Open-Ended Generative Canvas", "subtitle": "Fault-Tolerant Patch Stream with Self-Healing Recovery", "variant": "accent"}, "children": []}}',
    # --- MALFORMED INJECTION 1: Syntax error (truncated JSON) ---
    '{"op": "add", "path": /corrupted-syntax-unbalanced-quotes',
    # --- MALFORMED INJECTION 2: Missing required 'op' field ---
    '{"path": "/elements/orphan-node", "value": {"type": "Card"}}',
    # --- MALFORMED INJECTION 3: Unsupported RFC 6902 op verb ---
    '{"op": "unsupported_verb_action", "path": "/elements/test", "value": 123}',
    # Valid Patch 3: Auto-creates missing parents on the fly
    '{"op": "add", "path": "/elements/open-root/children/-", "value": "resilient-metric"}',
    '{"op": "add", "path": "/elements/resilient-metric", "value": {"type": "Metric", "props": {"label": "Error Recovery Rate", "value": "100%", "delta": "3 skipped", "trend": "up"}, "children": []}}',
    # Valid Patch 4: Open-ended CustomCodeBlock element
    '{"op": "add", "path": "/elements/canvas-block", "value": {"type": "CustomCodeBlock", "props": {"title": "Generative Particle Mesh (WebGL/Canvas)", "language": "javascript", "code": "const canvas = document.getElementById(\'particle-mesh\');\\nconst ctx = canvas.getContext(\'2d\');\\n// Render 100 autonomous orbiting particle nodes with spring physics\\nfor(let i=0; i<100; i++) {\\n  ctx.fillStyle = \'hsl(\' + (i*3.6) + \', 80%, 60%)\';\\n  ctx.fillRect(Math.sin(i)*100+150, Math.cos(i)*100+150, 4, 4);\\n}"}, "children": []}}',
]


def run_open_ended_mode(
    mock: bool = True,
    console: Optional[Console] = None,
    output_html_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes open-ended mode fault-tolerance and error recovery demonstration."""
    c = console or Console()
    c.print("[bold yellow]=== Codelab 4 (JSON Render): Mode 3 — Open-Ended UX Mode ===[/bold yellow]")

    compiler = createSpecStreamCompiler(catalog=DEFAULT_CATALOG)
    c.print(f"[dim]Streaming {len(ADVERSARIAL_STREAM_LINES)} lines including 3 intentional malformed injections...[/dim]\n")

    for idx, line in enumerate(ADVERSARIAL_STREAM_LINES, 1):
        compiler.compile_line(line)

    # Display fault-tolerance diagnostic table
    recovery_table = Table(title="Fault-Tolerant Compiler Error Recovery Matrix", border_style="red")
    recovery_table.add_column("#", style="dim", width=4)
    recovery_table.add_column("Intercepted Malformed Line / Reason", style="bold red")
    recovery_table.add_column("Compiler Action", style="bold green", width=22)

    for idx, skip in enumerate(compiler.skipped, 1):
        raw = skip.get("raw_line") or json.dumps(skip.get("patch", {}))
        reason = skip.get("reason", "Unknown error")
        recovery_table.add_row(
            str(idx),
            f"Input: {raw[:45]}...\nReason: {reason}",
            "RECORDED & SKIPPED",
        )
    c.print(recovery_table)

    c.print(f"\n[green][OK] Stream compilation completed with resilient self-healing![/green]")
    c.print(f"  Total patches successfully applied: [bold green]{len(compiler.patch_history)}[/bold green]")
    c.print(f"  Total malformed patches safely skipped: [bold yellow]{len(compiler.skipped)}[/bold yellow]")

    # Validate surviving spec
    spec = compiler.get_spec()
    errors = DEFAULT_CATALOG.validate_spec(spec)
    if errors:
        c.print(f"[yellow]Catalog validation warnings on surviving spec: {errors}[/yellow]")
    else:
        c.print("[green][OK] Surviving spec passed 100% of catalog validation checks.[/green]")

    # Dual-target rendering
    c.print("\n[bold cyan]Target 1: Terminal Console Surface (TerminalRenderer)[/bold cyan]")
    term_renderer = TerminalRenderer(console=c)
    term_renderer.render(spec)

    c.print("\n[bold cyan]Target 2: DOM Web Surface (DomRenderer)[/bold cyan]")
    dom_renderer = DomRenderer()
    html_output = dom_renderer.render(spec)

    target_path = output_html_path or os.path.join(os.path.dirname(__file__), "open_ended_canvas_output.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    c.print(f"[green][OK] HTML rendered and written to: {os.path.basename(target_path)} ({len(html_output)} bytes)[/green]")

    return {
        "mode": "open_ended",
        "total_applied": len(compiler.patch_history),
        "total_skipped": len(compiler.skipped),
        "skipped_details": compiler.skipped,
        "artifact_path": target_path,
        "status": "success",
    }


if __name__ == "__main__":
    run_open_ended_mode(mock=True)
