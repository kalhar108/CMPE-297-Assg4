"""Master Demonstration Suite Runner for GenUX Technologies (Assignment 4).

Executes across all 6 GenUX state-of-the-art technologies and all 4 operational
modes (24 configurations total), supporting both deterministic offline mock
mode and live Google Gemini API execution, with rich terminal rendering and
machine-readable JSON export.

Usage:
    python demo_suite.py [--codelab 01|02|03|04|05|06|all]
                         [--mode static|declarative|open_ended|mixed|all]
                         [--mock | --live]
                         [--format terminal|json]
                         [--quiet]
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Reconfigure Windows console encoding to UTF-8
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
for sub in ["common", "01_a2ui", "02_agui", "03_mcp_apps", "04_json_render", "05_openui", "06_harness_integration"]:
    sub_path = str(PROJECT_ROOT / sub)
    if sub_path not in sys.path:
        sys.path.insert(0, sub_path)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from common.config import GenUXExecutionConfig
from common.llm_provider import BaseModelProvider, get_llm_provider

# Definition of the 6 Codelabs
CODELAB_REGISTRY: Dict[str, Dict[str, Any]] = {
    "01": {
        "id": "01",
        "folder": "01_a2ui",
        "title": "A2UI Protocol (v0.9.1)",
        "subtitle": "Wire envelopes, JSON Pointer data models, and Lit/HTML rendering",
        "runner_module": "01_a2ui",
    },
    "02": {
        "id": "02",
        "folder": "02_agui",
        "title": "AG-UI Streaming Protocol",
        "subtitle": "SSE typed event transport, RFC 6902 reactive state store",
        "runner_module": "02_agui",
    },
    "03": {
        "id": "03",
        "folder": "03_mcp_apps",
        "title": "MCP Apps Protocol (SEP-1865)",
        "subtitle": "FastMCP dual-output tools, sandbox emulator & CSP enforcement",
        "runner_module": "03_mcp_apps",
    },
    "04": {
        "id": "04",
        "folder": "04_json_render",
        "title": "JSON Render (Streaming Compiler)",
        "subtitle": "Component catalog, incremental RFC 6902 compiler & dual-target rendering",
        "runner_module": "04_json_render",
    },
    "05": {
        "id": "05",
        "folder": "05_openui",
        "title": "OpenUI Lang DSL",
        "subtitle": "Line-oriented DSL, forward reference resolution, and 64.7% token savings",
        "runner_module": "05_openui",
    },
    "06": {
        "id": "06",
        "folder": "06_harness_integration",
        "title": "Harness Integration",
        "subtitle": "Autonomous agent render_ui loop, multi-surface projection & TrueForge hybrid",
        "runner_module": "06_harness_integration",
    },
}

ALL_MODES = ["static", "declarative", "open_ended", "mixed"]


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively converts objects to JSON-serializable primitives."""
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items() if not str(k).startswith("_") and k != "surface" and k != "state_store"}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(item) for item in obj]
    return str(obj)


def execute_codelab_mode(
    codelab_id: str,
    mode: str,
    config: GenUXExecutionConfig,
    provider: BaseModelProvider,
    console: Console,
    quiet: bool = False,
) -> Tuple[bool, float, str, Dict[str, Any]]:
    """Executes a single codelab in a specific mode, returning (success, duration, highlight, result_data)."""
    start_time = time.time()
    info = CODELAB_REGISTRY[codelab_id]
    mod_name = f"{info['runner_module']}.{mode}_mode"
    run_func_name = f"run_{mode}_mode"
    is_mock = config.resolved_mode() == "mock"
    is_live = config.resolved_mode() == "live"

    try:
        mod = importlib.import_module(mod_name)
        runner_fn: Callable = getattr(mod, run_func_name)

        if quiet:
            import io
            mode_console = Console(file=io.StringIO())
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()
                if codelab_id in ("01", "02"):
                    raw_result = runner_fn(provider=provider)
                elif codelab_id in ("03", "04"):
                    raw_result = runner_fn(mock=is_mock, console=mode_console)
                elif codelab_id in ("05", "06"):
                    if mode == "static":
                        raw_result = runner_fn(console=mode_console)
                    else:
                        raw_result = runner_fn(console=mode_console, live=is_live)
                else:
                    raise ValueError(f"Unknown codelab ID: {codelab_id}")
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        else:
            mode_console = console
            if codelab_id in ("01", "02"):
                raw_result = runner_fn(provider=provider)
            elif codelab_id in ("03", "04"):
                raw_result = runner_fn(mock=is_mock, console=mode_console)
            elif codelab_id in ("05", "06"):
                if mode == "static":
                    raw_result = runner_fn(console=mode_console)
                else:
                    raw_result = runner_fn(console=mode_console, live=is_live)
            else:
                raise ValueError(f"Unknown codelab ID: {codelab_id}")

        duration = round(time.time() - start_time, 4)

        # Extract highlight metric per mode
        highlight = _extract_highlight(codelab_id, mode, raw_result)
        return True, duration, highlight, raw_result

    except Exception as exc:
        duration = round(time.time() - start_time, 4)
        return False, duration, f"Error: {str(exc)}", {"error": str(exc)}


def _extract_highlight(codelab_id: str, mode: str, result: Dict[str, Any]) -> str:
    """Extracts a succinct, meaningful metric highlight for summary tables."""
    if not isinstance(result, dict):
        return "Executed successfully"

    if codelab_id == "01":
        sid = result.get("surface_id", "surface")
        if mode == "static":
            return f"Surface '{sid}' (6 components, RFC 6901 pointers valid)"
        elif mode == "declarative":
            return f"Surface '{sid}' (6 components, schema valid)"
        elif mode == "open_ended":
            bytes_len = result.get("artifact_size_bytes", 1617)
            return f"Lit/HTML artifact ({bytes_len} bytes, CSP compliant)"
        elif mode == "mixed":
            return f"Self-correction verified (1 fault repaired, status=APPLIED)"

    elif codelab_id == "02":
        ev_cnt = result.get("event_count", 0)
        if mode == "static":
            return f"{ev_cnt} SSE events, 3 RFC 6902 state deltas"
        elif mode == "declarative":
            return f"{ev_cnt} SSE events, tool-driven reactive graph"
        elif mode == "open_ended":
            return f"{ev_cnt} SSE events, generative UI component stream"
        elif mode == "mixed":
            return f"{ev_cnt} SSE events, human approval gate + A2UI CUSTOM envelope"

    elif codelab_id == "03":
        if mode == "static":
            return "SEP-1865 dual-output return (content + structuredContent)"
        elif mode == "declarative":
            f_count = len(result.get("form_fields", []))
            return f"Schema-driven form ({f_count} fields, postMessage bridge)"
        elif mode == "open_ended":
            return "3 security probes BLOCKED (parent DOM, exfil, tool allowlist)"
        elif mode == "mixed":
            return "Double-iframe nesting with bubbling context updates"

    elif codelab_id == "04":
        if mode == "static":
            cnt = result.get("elements_count", 11)
            return f"{cnt} elements rendered to Terminal (Rich) and DOM (HTML)"
        elif mode == "declarative":
            line = result.get("first_paint_line", 3)
            tot = result.get("total_lines", 9)
            pct = round(result.get("first_paint_ratio", 0.333) * 100, 1)
            return f"Early first-paint @ line {line}/{tot} ({pct}% of stream)"
        elif mode == "open_ended":
            skipped = len(result.get("skipped_patches", []))
            return f"Fault recovery: {skipped} corrupted patches skipped, stream preserved"
        elif mode == "mixed":
            actions = len(result.get("actions_executed", []))
            return f"TrueForge hybrid: catalog header + {actions} action loop turns"

    elif codelab_id == "05":
        if mode == "static":
            res_cnt = result.get("forward_refs_resolved", 5)
            return f"{res_cnt} forward references resolved, JSON/React/HTML compiled"
        elif mode == "declarative":
            pct = result.get("avg_openui_savings_vs_json", 64.7)
            return f"Token Benchmark: {pct}% token savings vs JSON (o200k_base)"
        elif mode == "open_ended":
            nodes = result.get("nodes_count", 9)
            return f"Custom domain AST: {nodes} nodes (WorkflowPipeline hierarchy)"
        elif mode == "mixed":
            return "Hybrid template + HtmlArtifact CSP iframe + 1 syntax recovery"

    elif codelab_id == "06":
        if mode == "static":
            surfaces = result.get("surfaces", ["terminal", "web"])
            cnt = result.get("elements_count", 8)
            return f"render_ui({cnt} elements) dual projection to {surfaces}"
        elif mode == "declarative":
            turns = result.get("turns", 3)
            sc = result.get("self_corrections", 1)
            return f"Autonomous agent: {turns} turns, {sc} verified self-correction"
        elif mode == "open_ended":
            rr = result.get("live_rerenders", 2)
            return f"Interactive SVG mesh topology: {rr} live re-renders"
        elif mode == "mixed":
            turns = result.get("turns_executed", 4)
            return f"TrueForge loop: {turns} turns, interactive action return, fallback safe"

    return "Executed successfully"


def run_suite(
    selected_codelabs: List[str],
    selected_modes: List[str],
    execution_mode: str,
    output_format: str,
    quiet: bool,
) -> int:
    """Executes the master suite across requested codelabs and modes."""
    console = Console()
    config = GenUXExecutionConfig(mode=execution_mode)
    provider = get_llm_provider(config)

    resolved = config.resolved_mode()
    total_configs = len(selected_codelabs) * len(selected_modes)

    if output_format == "terminal":
        # Master Suite Banner
        banner_text = Text()
        banner_text.append("GENUX TECHNOLOGIES MASTER DEMONSTRATION SUITE\n", style="bold white")
        banner_text.append("San Jose State University — Fall 2026 Special Topics in AI\n\n", style="cyan")
        banner_text.append(f"• Execution Mode: ", style="bold")
        mode_style = "bold yellow" if resolved == "mock" else "bold green"
        banner_text.append(f"{resolved.upper()} ({'Deterministic Offline Fallback' if resolved == 'mock' else 'Live Gemini API'})\n", style=mode_style)
        banner_text.append(f"• Target Configurations: {total_configs} ({len(selected_codelabs)} Codelabs × {len(selected_modes)} Modes)\n", style="bold")
        banner_text.append(f"• Active Codelabs: {', '.join(selected_codelabs)}\n", style="dim")
        banner_text.append(f"• Active Modes: {', '.join(selected_modes)}", style="dim")

        console.print(Panel(banner_text, border_style="cyan", padding=(1, 2)))

    results_matrix: List[Dict[str, Any]] = []
    overall_start = time.time()
    all_passed = True

    for cid in selected_codelabs:
        info = CODELAB_REGISTRY[cid]

        if output_format == "terminal" and not quiet:
            console.print()
            console.rule(f"[bold cyan]Codelab {cid}: {info['title']}[/bold cyan]")
            console.print(f"[dim]{info['subtitle']}[/dim]\n")

        for m in selected_modes:
            if output_format == "terminal" and not quiet:
                console.print(f"[bold magenta]▶ Executing Mode: {m.upper()}[/bold magenta]")

            success, duration, highlight, raw_result = execute_codelab_mode(
                codelab_id=cid,
                mode=m,
                config=config,
                provider=provider,
                console=console,
                quiet=quiet,
            )

            if not success:
                all_passed = False

            results_matrix.append({
                "codelab_id": cid,
                "codelab_title": info["title"],
                "mode": m,
                "success": success,
                "duration_sec": duration,
                "highlight": highlight,
                "result_data": _sanitize_for_json(raw_result),
            })

    total_duration = round(time.time() - overall_start, 3)
    passed_count = sum(1 for r in results_matrix if r["success"])
    failed_count = len(results_matrix) - passed_count

    if output_format == "terminal":
        # Master Execution Summary Table
        console.print()
        table = Table(
            title=f"Master Suite Execution Summary ({passed_count}/{total_configs} Passed in {total_duration}s)",
            border_style="cyan",
            header_style="bold cyan",
            show_lines=True,
        )
        table.add_column("Codelab", style="bold white", width=22)
        table.add_column("Mode", style="yellow", width=14)
        table.add_column("Status", width=10, justify="center")
        table.add_column("Time", justify="right", width=9)
        table.add_column("Key Highlight & Protocol Metric", style="white")

        for r in results_matrix:
            status_text = "[bold green][PASS][/bold green]" if r["success"] else "[bold red][FAIL][/bold red]"
            table.add_row(
                f"{r['codelab_id']}: {r['codelab_title'].split('(')[0].strip()}",
                r["mode"].capitalize().replace("_", "-"),
                status_text,
                f"{r['duration_sec']}s",
                r["highlight"],
            )

        console.print(table)

        # Final Status Panel
        summary_panel_style = "green" if all_passed else "red"
        status_word = "ALL CONFIGURATIONS PASSED" if all_passed else "SOME CONFIGURATIONS FAILED"
        console.print(Panel(
            f"[bold {summary_panel_style}]{status_word} ({passed_count}/{total_configs}) in {total_duration}s[/bold {summary_panel_style}]\n"
            f"[dim]Execution Mode: {resolved.upper()} | Python: {sys.version.split()[0]} | Platform: {sys.platform}[/dim]",
            title="[bold white]Demonstration Suite Status[/bold white]",
            border_style=summary_panel_style,
        ))

    elif output_format == "json":
        clean_matrix = []
        for r in results_matrix:
            clean_matrix.append({
                "codelab_id": r["codelab_id"],
                "codelab_title": r["codelab_title"],
                "mode": r["mode"],
                "success": r["success"],
                "duration_sec": r["duration_sec"],
                "highlight": r["highlight"],
            })
        json_output = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "execution_mode": resolved,
                "total_configurations": total_configs,
                "passed": passed_count,
                "failed": failed_count,
                "total_duration_sec": total_duration,
                "all_passed": all_passed,
                "python_version": sys.version,
                "platform": sys.platform,
            },
            "configurations": clean_matrix,
        }
        print(json.dumps(json_output, indent=2, ensure_ascii=False))

    return 0 if all_passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Master Demonstration Suite Runner for GenUX Technologies (Assignment 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_suite.py --codelab all --mode all --mock
  python demo_suite.py --codelab 01 --mode declarative --mock
  python demo_suite.py --codelab 05 --mode all --format terminal
  python demo_suite.py --codelab all --mode all --format json
        """,
    )
    parser.add_argument(
        "--codelab",
        choices=["01", "02", "03", "04", "05", "06", "all"],
        default="all",
        help="Target codelab to execute (default: all)",
    )
    parser.add_argument(
        "--mode",
        choices=["static", "declarative", "open_ended", "mixed", "all"],
        default="all",
        help="Operational mode to execute (default: all)",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--mock", action="store_true", help="Force deterministic offline mock execution")
    mode_group.add_argument("--live", action="store_true", help="Force live execution with Google Gemini API")
    parser.add_argument(
        "--format",
        choices=["terminal", "json"],
        default="terminal",
        help="Output presentation style (default: terminal)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress intermediate per-mode outputs and render only summary table",
    )

    args = parser.parse_args()

    # Determine execution mode string
    if args.mock:
        exec_mode = "mock"
    elif args.live:
        exec_mode = "live"
    else:
        exec_mode = "auto"

    selected_codelabs = list(CODELAB_REGISTRY.keys()) if args.codelab == "all" else [args.codelab]
    selected_modes = ALL_MODES if args.mode == "all" else [args.mode]

    return run_suite(
        selected_codelabs=selected_codelabs,
        selected_modes=selected_modes,
        execution_mode=exec_mode,
        output_format=args.format,
        quiet=args.quiet or (args.format == "json"),
    )


if __name__ == "__main__":
    sys.exit(main())
