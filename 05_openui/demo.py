"""CLI Demonstration Entry Point for Codelab 05: OpenUI Lang DSL.

Usage:
  python demo.py [--mode {all,static,declarative,open_ended,mixed}] [--mock | --live] [--format {terminal,json,html}]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 1. Resolve Project Root (assignment-4-genux/)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 2. Resolve Module Directory (05_openui/)
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
        description="Codelab 05: OpenUI Lang DSL Demonstration Runner",
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
        "--format",
        choices=["terminal", "json", "html"],
        default="terminal",
        help="Output presentation format (default: terminal)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Optional path to write HTML or JSON artifact",
    )

    args = parser.parse_args()
    console = Console()

    # Determine execution mode
    if args.mock:
        config_mode = "mock"
    elif args.live:
        config_mode = "live"
    else:
        config_mode = "mock"  # Safe default for reliable verification

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

        # Handle file export if requested
        if args.output_file and "static" in results:
            if args.format == "html":
                from compiler import compile_to_html, parse_program
                p = parse_program(results["static"]["program"])
                with open(args.output_file, "w", encoding="utf-8") as f:
                    f.write(compile_to_html(p))
                console.print(f"[bold green]Artifact written to {args.output_file}[/bold green]")

        console.print(Panel(
            f"[bold green]All requested modes ({args.mode}) completed successfully.[/bold green]",
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
