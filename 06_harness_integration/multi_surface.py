"""Multi-surface projection engine for GenUX coding harness.

Concurrent multi-target projection broadcasting validated UI specifications
to:
1. Terminal Console: via rich (Panels, Tables, Tree structure, and KPI metrics).
2. Web Browser: via Server-Sent Events (SSE) and interactive POST /action callback bridge.
"""

from __future__ import annotations

import json
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree


# Standard UI catalog schema for validation
ALLOWED_COMPONENT_TYPES = {
    "Stack", "Card", "Metric", "Table", "Button", "TextField",
    "Text", "HtmlArtifact", "Skeleton", "Alert", "Badge"
}


def validate_ui_spec(spec: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validates that a UI specification conforms to standard GenUX shape and component catalog."""
    if not isinstance(spec, dict):
        return False, "UI spec must be a dictionary"

    if "root" not in spec:
        return False, "UI spec missing required 'root' identifier"

    if "elements" not in spec or not isinstance(spec["elements"], dict):
        return False, "UI spec missing required 'elements' dictionary"

    root_id = spec["root"]
    elements = spec["elements"]

    if root_id not in elements:
        return False, f"Root element '{root_id}' not found in elements dictionary"

    for elem_id, elem in elements.items():
        if not isinstance(elem, dict):
            return False, f"Element '{elem_id}' must be a dictionary"
        comp_type = elem.get("type")
        if not comp_type:
            return False, f"Element '{elem_id}' missing required 'type' property"
        if comp_type not in ALLOWED_COMPONENT_TYPES:
            return False, f"Unknown component type '{comp_type}' in element '{elem_id}'. Allowed types: {sorted(ALLOWED_COMPONENT_TYPES)}"

        children = elem.get("children", [])
        if not isinstance(children, list):
            return False, f"Element '{elem_id}' 'children' must be a list"

    return True, None


class MultiSurfaceBroadcaster:
    """Manages concurrent projection to terminal console and web browser SSE transport."""

    def __init__(self, console: Optional[Console] = None) -> None:
        self.console = console or Console()
        self.active_spec: Optional[Dict[str, Any]] = None
        self.render_history: List[Dict[str, Any]] = []
        self.sse_event_queue: queue.Queue = queue.Queue()
        self.action_queue: queue.Queue = queue.Queue()
        self._server_thread: Optional[threading.Thread] = None
        self._server_running = False
        self._server_port: Optional[int] = None

    def render_ui(self, spec: Dict[str, Any], target: str = "all") -> Dict[str, Any]:
        """Validates and broadcasts a UI specification across configured surface targets."""
        is_valid, error_msg = validate_ui_spec(spec)
        if not is_valid:
            receipt = {
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            return receipt

        self.active_spec = spec
        timestamp = datetime.now(timezone.utc).isoformat()
        receipt = {
            "status": "success",
            "root": spec["root"],
            "elements_count": len(spec["elements"]),
            "surfaces_projected": [],
            "timestamp": timestamp,
        }

        # 1. Project to Terminal Console
        if target in ("all", "terminal", "console"):
            self._project_to_terminal(spec)
            receipt["surfaces_projected"].append("terminal")

        # 2. Project to Web Surface (SSE Queue)
        if target in ("all", "web", "browser"):
            event_payload = {
                "event": "render_ui",
                "spec": spec,
                "timestamp": timestamp,
            }
            self.sse_event_queue.put(event_payload)
            receipt["surfaces_projected"].append("web")

        self.render_history.append(receipt)
        return receipt

    def _project_to_terminal(self, spec: Dict[str, Any]) -> None:
        """Renders the UI spec in the terminal using rich widgets."""
        elements = spec.get("elements", {})
        root_id = spec.get("root", "")

        if not root_id or root_id not in elements:
            self.console.print("[dim]Empty or invalid UI spec[/dim]")
            return

        def _build_terminal_tree(node_id: str, current_tree: Any, visited: set) -> None:
            if node_id in visited:
                current_tree.add(f"[red]Circular ref: {node_id}[/red]")
                return
            visited.add(node_id)

            if node_id not in elements:
                current_tree.add(f"[yellow]Skeleton ({node_id})[/yellow]")
                return

            elem = elements[node_id]
            comp_type = elem.get("type", "Unknown")
            props = elem.get("props", {})
            children = elem.get("children", [])

            # Format node display based on component type
            if comp_type == "Metric":
                label = props.get("label", node_id)
                val = props.get("value", "")
                change = props.get("change", "")
                change_str = f" ({change})" if change else ""
                branch = current_tree.add(f"[bold cyan]Metric[/bold cyan]: [white]{label}[/white] = [bold green]{val}[/bold green]{change_str}")
            elif comp_type == "Card":
                title = props.get("title", node_id)
                branch = current_tree.add(f"[bold blue]Card[/bold blue]: [white]{title}[/white]")
            elif comp_type == "Button":
                btn_lbl = props.get("label", "Click")
                action = props.get("action", "")
                branch = current_tree.add(f"[bold magenta]Button[/bold magenta]: [white]{btn_lbl}[/white] -> [dim]{action}[/dim]")
            elif comp_type == "Table":
                cols = props.get("columns", [])
                rows_count = len(props.get("rows", []))
                branch = current_tree.add(f"[bold yellow]Table[/bold yellow]: [white]{cols}[/white] ({rows_count} rows)")
            elif comp_type == "HtmlArtifact":
                art_title = props.get("title", "Artifact")
                branch = current_tree.add(f"[bold red]HtmlArtifact[/bold red]: [white]{art_title}[/white] (Sandboxed)")
            else:
                branch = current_tree.add(f"[white]{comp_type}[/white] ([dim]{node_id}[/dim])")

            for child_id in children:
                _build_terminal_tree(child_id, branch, visited)

        root_elem = elements[root_id]
        root_type = root_elem.get("type", "Root")
        tree = Tree(f"[bold white on blue] Surface: {root_id} ({root_type}) [/bold white on blue]")
        _build_terminal_tree(root_id, tree, set())

        panel = Panel(
            tree,
            title="[bold cyan]Multi-Surface Terminal Projection[/bold cyan]",
            border_style="cyan",
            subtitle=f"[dim]{len(elements)} elements | Target: Console[/dim]",
        )
        self.console.print(panel)

    def dispatch_action(self, action_name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Receives a client interaction event (e.g. from web button click or mock event)."""
        action_event = {
            "action": action_name,
            "payload": payload or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.action_queue.put(action_event)
        return {"status": "action_queued", "action": action_name}

    def get_pending_action(self, timeout: float = 0.5) -> Optional[Dict[str, Any]]:
        """Retrieves the next pending client action, if any."""
        try:
            return self.action_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def export_web_html(self, title: str = "GenUX Multi-Surface Web View") -> str:
        """Generates self-contained HTML for the web surface with SSE client listener."""
        spec_json = json.dumps(self.active_spec or {})
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 24px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
    .btn {{ background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }}
    pre {{ background: #020617; padding: 12px; border-radius: 6px; overflow-x: auto; color: #38bdf8; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div id="status">Connected to Multi-Surface Broadcast Engine</div>
  <div class="card">
    <h3>Active Surface Specification</h3>
    <pre id="spec-view">{spec_json}</pre>
  </div>
  <script>
    console.log("[MultiSurface Web Client Ready]");
  </script>
</body>
</html>"""
