"""CLI Demonstration Entry Point for Codelab 06: Harness Integration.

Usage:
  python demo.py [--mode {all,static,declarative,open_ended,mixed}] [--mock | --live] [--port PORT]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 1. Resolve Project Root (assignment-4-genux/)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 2. Resolve Module Directory (06_harness_integration/)
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from typing import Any, Dict
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
    parser = argparse.ArgumentParser(
        description="Codelab 06: Harness Integration Demonstration Runner",
    )
    parser.add_argument(
        "--mode",
        choices=["all", "static", "declarative", "open_ended", "mixed"],
        default="all",
        help="Demonstration mode to execute (default: all)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mock", action="store_true", help="Force deterministic offline mock execution")
    group.add_argument("--live", action="store_true", help="Force live LLM execution with Google Gemini")
    parser.add_argument(
        "--port",
        type=int,
        default=8086,
        help="Optional port for web surface (default: 8086)",
    )

    args = parser.parse_args()
    console = Console()

    # Determine execution mode
    if args.mock:
        config_mode = "mock"
    elif args.live:
        config_mode = "live"
    else:
        config_mode = "mock"

    config = GenUXExecutionConfig(mode=config_mode)
    config.print_banner(console)

    results: Dict[str, Any] = {}

    try:
        if args.mode in ("all", "static"):
            results["static"] = run_static_mode(console=console)

        if args.mode in ("all", "declarative"):
            results["declarative"] = run_declarative_mode(console=console, live=args.live)

        if args.mode in ("all", "open_ended"):
            results["open_ended"] = run_open_ended_mode(console=console, live=args.live)

        if args.mode in ("all", "mixed"):
            results["mixed"] = run_mixed_mode(console=console, live=args.live)

        console.print(Panel(
            f"[bold green]All requested Harness modes ({args.mode}) completed successfully.[/bold green]",
            border_style="green",
        ))
        return 0

    except Exception as e:
        console.print(f"[bold red]Execution error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
