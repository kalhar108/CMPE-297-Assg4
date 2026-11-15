"""Codelab 3: MCP Apps Protocol (SEP-1865).

Demonstrates the Model Context Protocol ext-apps specification (SEP-1865),
exposing interactive HTML webviews via ui:// resource links, dual-output CallToolResult
(LLM plain text + frontend structuredContent), and host container sandboxing.
"""

from .mcp_server import LemonadeMCPServer, create_lemonade_mcp_server
from .host_emulator import MCPHostEmulator, HostSecurityError
from .static_mode import run_static_mode
from .declarative_mode import run_declarative_mode
from .open_ended_mode import run_open_ended_mode
from .mixed_mode import run_mixed_mode

__all__ = [
    "LemonadeMCPServer",
    "create_lemonade_mcp_server",
    "MCPHostEmulator",
    "HostSecurityError",
    "run_static_mode",
    "run_declarative_mode",
    "run_open_ended_mode",
    "run_mixed_mode",
]
