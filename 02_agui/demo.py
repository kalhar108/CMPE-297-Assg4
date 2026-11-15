"""Demonstration CLI Runner for Codelab 2: AG-UI Streaming Protocol.

Supports all 4 operational modes:
1. Static Mode: Fixed SSE stream with initial STATE_SNAPSHOT and STATE_DELTA patches.
2. Declarative Mode: Reactive state-driven graph responding to tool-driven JSON patch mutations.
3. Open-Ended UX Mode: Conversational graph with generative UI stream (COMPONENT_UPDATE).
4. Mixed / Hybrid Mode: Hybrid state graph with client approval gates and embedded A2UI envelope.

Usage:
    python demo.py --mode static|declarative|open_ended|mixed|all [--mock] [--live] [--format terminal|json|sse]
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
    """Serializes result dictionary to clean JSON."""
    clean = {k: v for k, v in data.items() if k != "state_store"}
    return json.dumps(clean, indent=2, default=str)


def run_demo(mode: str, provider: BaseModelProvider, output_format: str) -> bool:
    """Runs the selected mode or all modes and displays results."""
    modes_to_run = ["static", "declarative", "open_ended", "mixed"] if mode == "all" else [mode]
    all_passed = True

    for m in modes_to_run:
        console.rule(f"[bold cyan]Codelab 2 (AG-UI) - Mode: {m.upper()}[/bold cyan]")

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
            elif output_format == "sse":
                # Print raw SSE frames
                console.print("[dim]=== Raw SSE Event Stream (LF-only delimited) ===[/dim]")
                for frame in result.get("sse_frames", []):
                    console.print(frame, end="")
            else:
                # Terminal Rich Output: Event Timeline Table
                event_table = Table(
                    title=f"AG-UI Event Timeline ({m.upper()} Mode)",
                    border_style="cyan",
                    show_header=True,
                )
                event_table.add_column("Seq", style="dim", width=4)
                event_table.add_column("Event Type", style="bold yellow")
                event_table.add_column("Payload Details", style="white")

                for idx, ev in enumerate(result.get("events", []), start=1):
                    ev_type = ev.get("event", "UNKNOWN")
                    data = ev.get("data", {})
                    if ev_type == "RUN_STARTED":
                        detail = f"runId={data.get('runId')}, threadId={data.get('threadId')}"
                    elif ev_type == "STATE_SNAPSHOT":
                        detail = f"Initial state keys: {list(data.get('snapshot', {}).keys())}"
                    elif ev_type == "TEXT_MESSAGE_CONTENT":
                        detail = f"delta='{data.get('delta', '')[:60]}...'"
                    elif ev_type == "TOOL_CALL_START":
                        detail = f"tool={data.get('name')} (id={data.get('toolCallId')})"
                    elif ev_type == "STATE_DELTA":
                        patches = data.get("patches", [])
                        detail = f"{len(patches)} RFC 6902 patch(es): " + ", ".join(
                            f"{p.get('op')} {p.get('path')}" for p in patches[:2]
                        )
                    elif ev_type == "COMPONENT_UPDATE":
                        comp = data.get("component", {})
                        detail = f"componentId={comp.get('componentId')}, type={comp.get('type')}"
                    elif ev_type == "ACTION_EMITTED":
                        detail = f"action={data.get('actionName')}, approved={data.get('approved')}"
                    elif ev_type == "CUSTOM":
                        detail = f"customName={data.get('name')}, embedded envelope={data.get('envelope', {}).get('version')}"
                    elif ev_type == "RUN_FINISHED":
                        detail = f"tokens={data.get('tokenUsage')}"
                    else:
                        detail = str(data)[:80]

                    event_table.add_row(str(idx), ev_type, detail)

                console.print(event_table)

                # State Snapshot Summary Table
                state_table = Table(title="Final Reactive State Store", border_style="green")
                state_table.add_column("State Path / Key", style="cyan")
                state_table.add_column("Current Value", style="white")

                def flatten(d: dict, prefix: str = "") -> None:
                    for k, v in d.items():
                        path = f"{prefix}/{k}"
                        if isinstance(v, dict):
                            flatten(v, path)
                        elif isinstance(v, list):
                            state_table.add_row(path, f"[{len(v)} item(s)]")
                        else:
                            state_table.add_row(path, str(v)[:60])

                flatten(result.get("final_state", {}))
                console.print(state_table)

                console.print(f"[bold green][PASS] Mode {m} completed successfully.[/bold green]\n")

        except Exception as exc:
            all_passed = False
            console.print(f"[bold red][FAIL] Mode {m} failed with error: {exc}[/bold red]")
            import traceback
            traceback.print_exc()

    return all_passed


def main() -> int:
    parser = argparse.ArgumentParser(description="AG-UI Streaming Protocol Demonstration Runner")
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
        choices=["terminal", "json", "sse"],
        default="terminal",
        help="Output display format (default: terminal)",
    )
    args = parser.parse_args()

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
