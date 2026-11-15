"""Demonstration CLI Runner for Codelab 1: A2UI Protocol v0.9.1.

Supports all 4 operational modes:
1. Static Mode: Deterministic component rendering & data model pointer updates.
2. Declarative Mode: Structured schema-constrained generation & pointer bindings.
3. Open-Ended UX Mode: Dynamic component synthesis with sandboxed Lit/HTML artifacts.
4. Mixed / Hybrid Mode: Shell + generative cards + automated self-correction recovery.

Usage:
    python demo.py --mode static|declarative|open_ended|mixed|all [--mock] [--live] [--format terminal|json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from common.config import GenUXExecutionConfig
from common.llm_provider import BaseModelProvider, get_llm_provider

try:
    from .declarative_mode import run_declarative_mode
    from .mixed_mode import run_mixed_mode
    from .open_ended_mode import run_open_ended_mode
    from .static_mode import run_static_mode
except ImportError:
    from declarative_mode import run_declarative_mode
    from mixed_mode import run_mixed_mode
    from open_ended_mode import run_open_ended_mode
    from static_mode import run_static_mode

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


def format_json_output(data: Dict[str, Any]) -> str:
    """Serializes execution result to formatted JSON string."""
    serializable = {}
    for k, v in data.items():
        if k == "surface":
            continue
        serializable[k] = v
    return json.dumps(serializable, indent=2, default=str)


def run_demo(mode: str, provider: BaseModelProvider, output_format: str) -> bool:
    """Runs the selected mode or all modes and displays results."""
    modes_to_run = ["static", "declarative", "open_ended", "mixed"] if mode == "all" else [mode]
    all_passed = True

    for m in modes_to_run:
        console.rule(f"[bold cyan]Codelab 1 (A2UI) - Mode: {m.upper()}[/bold cyan]")

        try:
            if m == "static":
                result = run_static_mode(provider=provider)
            elif m == "declarative":
                result = run_declarative_mode(provider=provider)
            elif m == "open_ended":
                result = run_open_ended_mode(provider=provider)
            elif m == "mixed":
                result = run_mixed_mode(provider=provider)
            else:
                console.print(f"[bold red]Unknown mode: {m}[/bold red]")
                return False

            if output_format == "json":
                console.print(format_json_output(result))
            else:
                # Terminal Rich Output
                surface = result.get("surface")
                if surface:
                    console.print(surface.render_rich_panel())

                # Summary Table
                table = Table(title=f"Mode Execution Summary: {m.upper()}", border_style="green")
                table.add_column("Property", style="bold white")
                table.add_column("Value", style="cyan")

                table.add_row("Surface ID", str(result.get("surface_id")))
                table.add_row("Schema Valid", "[green]YES (100%)[/green]" if result.get("is_valid", True) else "[red]NO[/red]")
                table.add_row("Component Count", str(result.get("component_count")))

                if m == "static" or m == "declarative":
                    act = result.get("action_event")
                    if act:
                        table.add_row("Action Resolved", f"[yellow]{act.get('name')}[/yellow]")
                        table.add_row("Context Pointers", str(act.get("context")))
                elif m == "open_ended":
                    table.add_row("CSP Security Compliant", "[green]YES (Strict)[/green]" if result.get("is_security_compliant") else "[red]NO[/red]")
                    table.add_row("Artifact Size", f"{result.get('html_artifact_length')} bytes")
                elif m == "mixed":
                    table.add_row("Fault Detected & Handled", "[green]YES[/green]" if result.get("fault_detected") else "[yellow]N/A[/yellow]")
                    table.add_row("Self-Correction Repaired", "[green]YES (Passed)[/green]" if result.get("self_correction_passed") else "[red]FAILED[/red]")
                    table.add_row("Action Dispatch", f"{result.get('action_name')} -> {result.get('action_context')}")

                console.print(table)
                console.print(f"[bold green][PASS] Mode {m} completed successfully.[/bold green]\n")

        except Exception as exc:
            all_passed = False
            console.print(f"[bold red][FAIL] Mode {m} failed with error: {exc}[/bold red]")
            import traceback
            traceback.print_exc()

    return all_passed


def main() -> int:
    parser = argparse.ArgumentParser(description="A2UI Protocol v0.9.1 Demonstration Runner")
    parser.add_argument(
        "--mode",
        choices=["static", "declarative", "open_ended", "mixed", "all"],
        default="all",
        help="Operational mode to demonstrate (default: all)",
    )
    parser.add_argument("--mock", action="store_true", help="Force deterministic offline mock mode")
    parser.add_argument("--live", action="store_true", help="Force live API mode")
    parser.add_argument(
        "--format",
        choices=["terminal", "json"],
        default="terminal",
        help="Output display format (default: terminal)",
    )
    args = parser.parse_args()

    # Determine execution config
    if args.mock and args.live:
        console.print("[bold red]Cannot specify both --mock and --live.[/bold red]")
        return 1

    mode_choice = "mock" if args.mock else ("live" if args.live else "auto")
    config = GenUXExecutionConfig(mode=mode_choice)
    config.print_banner(console)

    provider = get_llm_provider(config)
    success = run_demo(mode=args.mode, provider=provider, output_format=args.format)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
