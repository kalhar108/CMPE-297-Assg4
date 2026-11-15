"""Automated Output Recording Pipeline for GenUX Walkthrough Documentation.

Executes all 6 codelab demonstration scripts and the automated test suite in
deterministic offline mock mode, captures raw verbatim stdout and stderr,
and compiles structured output records for WALKTHROUGH.md and DEMOS.md.

Usage:
    python scripts/record_walkthrough_outputs.py [--output-dir DIR]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = sys.executable


def run_command_capture(cmd: List[str], env: Dict[str, str], cwd: Path) -> Dict[str, Any]:
    """Runs a command, timing execution and capturing stdout and stderr."""
    start_time = time.time()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(cwd),
            timeout=120,
        )
        duration_sec = round(time.time() - start_time, 3)
        return {
            "cmd": " ".join(cmd),
            "exit_code": proc.returncode,
            "duration_sec": duration_sec,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "success": proc.returncode == 0,
        }
    except Exception as exc:
        duration_sec = round(time.time() - start_time, 3)
        return {
            "cmd": " ".join(cmd),
            "exit_code": -1,
            "duration_sec": duration_sec,
            "stdout": "",
            "stderr": str(exc),
            "success": False,
        }


def main() -> int:
    env = os.environ.copy()
    python_path = str(PROJECT_ROOT)
    for sub in ["01_a2ui", "02_agui", "03_mcp_apps", "04_json_render", "05_openui", "06_harness_integration", "common"]:
        python_path += os.pathsep + str(PROJECT_ROOT / sub)
    env["PYTHONPATH"] = python_path
    env["PYTHONIOENCODING"] = "utf-8"
    env["GENUX_EXECUTION_MODE"] = "mock"

    recordings: Dict[str, Any] = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": str(PROJECT_ROOT),
        },
        "codelabs": {},
        "test_suite": None,
    }

    runs = [
        ("01_a2ui", [PYTHON_EXE, str(PROJECT_ROOT / "01_a2ui" / "demo.py"), "--mode", "all", "--mock"]),
        ("02_agui", [PYTHON_EXE, str(PROJECT_ROOT / "02_agui" / "demo.py"), "--mode", "all", "--mock"]),
        ("03_mcp_apps", [PYTHON_EXE, "-m", "03_mcp_apps.demo", "--mode", "all", "--mock"]),
        ("04_json_render", [PYTHON_EXE, "-m", "04_json_render.demo", "--mode", "all", "--mock"]),
        ("05_openui", [PYTHON_EXE, str(PROJECT_ROOT / "05_openui" / "demo.py"), "--mode", "all", "--mock"]),
        ("06_harness_integration", [PYTHON_EXE, str(PROJECT_ROOT / "06_harness_integration" / "demo.py"), "--mode", "all", "--mock"]),
    ]

    print("=" * 80)
    print("GENUX AUTOMATED OUTPUT RECORDER")
    print("Recording executions across all 6 codelabs and 4-tier test harness...")
    print("=" * 80)

    all_passed = True

    for name, cmd in runs:
        print(f"\n[RECORDING] {name}...")
        res = run_command_capture(cmd, env, PROJECT_ROOT)
        status_label = "PASS" if res["success"] else "FAIL"
        print(f"  -> Exit: {res['exit_code']} [{status_label}] ({res['duration_sec']}s)")
        recordings["codelabs"][name] = res
        if not res["success"]:
            all_passed = False
            print(f"  Error details: {res['stderr'][:300]}")

    # Also record pytest suite
    print("\n[RECORDING] Automated Pytest Test Harness (4 Tiers)...")
    pytest_cmd = [PYTHON_EXE, "-m", "pytest", "tests/", "--basetemp=.pytest_tmp", "-v"]
    test_res = run_command_capture(pytest_cmd, env, PROJECT_ROOT)
    status_label = "PASS" if test_res["success"] else "FAIL"
    print(f"  -> Exit: {test_res['exit_code']} [{status_label}] ({test_res['duration_sec']}s)")
    recordings["test_suite"] = test_res
    if not test_res["success"]:
        all_passed = False

    output_dir = PROJECT_ROOT / "scripts"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "recorded_outputs.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(recordings, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Recorded JSON outputs saved to: {json_path}")

    # Write human-readable markdown transcript
    md_path = output_dir / "recorded_transcript.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# GenUX Master Execution Transcript\n\n")
        f.write(f"- **Timestamp**: {recordings['metadata']['timestamp']}\n")
        f.write(f"- **Python Version**: {recordings['metadata']['python_version']}\n")
        f.write(f"- **Platform**: {recordings['metadata']['platform']}\n\n")

        f.write("## Test Suite Verification\n\n")
        f.write(f"Command: `{test_res['cmd']}`\n")
        f.write(f"Exit Code: `{test_res['exit_code']}` | Duration: `{test_res['duration_sec']}s`\n\n")
        f.write("```text\n")
        f.write(test_res["stdout"].strip())
        f.write("\n```\n\n")

        for name, data in recordings["codelabs"].items():
            f.write(f"## Codelab: {name}\n\n")
            f.write(f"- **Command**: `{data['cmd']}`\n")
            f.write(f"- **Exit Code**: `{data['exit_code']}` | **Duration**: `{data['duration_sec']}s`\n\n")
            f.write("```text\n")
            f.write(data["stdout"].strip())
            f.write("\n```\n\n")

    print(f"[OK] Recorded Markdown transcript saved to: {md_path}")
    print(f"\nOverall Result: {'ALL PASSED' if all_passed else 'SOME RUNS FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
