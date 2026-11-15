"""CLI Demonstration Entry Point for Codelab 4: JSON Render (Vercel-style Declarative UI).

Usage:
    python demo.py [--mode static|declarative|open_ended|mixed|all] [--mock] [--live]
"""

from __future__ import annotations

import argparse
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

from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel

from common.config import GenUXExecutionConfig

try:
    from .static_mode import run_static_mode
    from .declarative_mode import run_declarative_mode
    from .open_ended_mode import run_open_ended_mode
    from .mixed_mode import run_mixed_mode
except (ImportError, ValueError):
    from static_mode import run_static_mode
    from declarative_mode import run_declarative_mode
    from open_ended_mode import run_open_ended_mode
    from mixed_mode import run_mixed_mode


def main() -> int:
    parser = argparse.ArgumentParser(description="Demonstrate Codelab 4: JSON Render (Declarative UI & Streaming Patches)")
    parser.add_argument(
        "--mode",
        choices=["static", "declarative", "open_ended", "mixed", "all"],
        default="all",
        help="Which mode to execute (default: all)",
    )
    parser.add_argument("--mock", action="store_true", help="Force deterministic offline mock execution")
    parser.add_argument("--live", action="store_true", help="Force live API execution")

    args = parser.parse_args()
    console = Console()

    mode_choice = "mock" if args.mock else ("live" if args.live else "auto")
    config = GenUXExecutionConfig(mode=mode_choice)
    config.print_banner(console)

    is_mock = config.resolved_mode() == "mock"

    results: Dict[str, Any] = {}

    try:
        if args.mode in ("static", "all"):
            console.rule("[bold cyan]Executing Mode 1: Static[/bold cyan]")
            results["static"] = run_static_mode(mock=is_mock, console=console)

        if args.mode in ("declarative", "all"):
            console.rule("[bold cyan]Executing Mode 2: Declarative[/bold cyan]")
            results["declarative"] = run_declarative_mode(mock=is_mock, console=console)

        if args.mode in ("open_ended", "all"):
            console.rule("[bold cyan]Executing Mode 3: Open-Ended UX[/bold cyan]")
            results["open_ended"] = run_open_ended_mode(mock=is_mock, console=console)

        if args.mode in ("mixed", "all"):
            console.rule("[bold cyan]Executing Mode 4: Mixed / Hybrid[/bold cyan]")
            results["mixed"] = run_mixed_mode(mock=is_mock, console=console)

        console.print(Panel(
            f"[bold green][OK] Codelab 4 (JSON Render) executed successfully across all requested modes: {list(results.keys())}[/bold green]",
            title="[bold white]Demonstration Complete[/bold white]",
            border_style="green",
        ))
        return 0

    except Exception as e:
        console.print(f"[bold red]Execution error in Codelab 4: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
