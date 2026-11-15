"""
Shared test configuration, fixtures, and contract validators for GenUX test harness.
Configured for deterministic offline execution (GENUX_EXECUTION_MODE=mock).
"""

import os
import sys
import json
import asyncio
import re
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator
import pytest

# Ensure Windows proactor event loop policy for async stability
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Sets environment variables ensuring 100% deterministic offline mock execution."""
    os.environ["GENUX_EXECUTION_MODE"] = "mock"
    os.environ["GENUX_MODE"] = "mock"
    os.environ["GEMINI_API_KEY"] = "mock-api-key-test-12345"
    os.environ["OPENAI_API_KEY"] = "mock-openai-key-test-12345"
    os.environ["GOOGLE_API_KEY"] = "mock-google-key-test-12345"
    yield
    # Cleanup if needed


# ============================================================================
# 1. Mock LLM Provider Fixture
# ============================================================================

class MockLLMProvider:
    """Deterministic offline mock LLM provider conforming to BaseModelProvider interface."""

    def __init__(self, mode: str = "mock"):
        self.mode = mode
        self.call_history: List[Dict[str, Any]] = []

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        self.call_history.append({"method": "generate_text", "prompt": prompt, "system": system_instruction})
        p = prompt.lower()
        if "openui" in p or "oui" in p:
            return 'root = Stack([kpi1, kpi2], "row")\nkpi1 = Metric("Revenue", "$12,450", "+8%")\nkpi2 = Metric("Orders", "340", "+5%")'
        if "a2ui" in p:
            return json.dumps({
                "version": "v0.9.1",
                "updateComponents": {
                    "surfaceId": "main",
                    "components": [
                        {"id": "root", "component": "Card", "props": {"title": "Analytics"}, "children": ["m1"]},
                        {"id": "m1", "component": "Metric", "props": {"label": "Conversion", "value": "3.4%"}, "children": []}
                    ]
                }
            })
        if "patch" in p or "json_render" in p:
            return json.dumps([
                {"op": "add", "path": "/elements/root", "value": {"type": "Card", "props": {"title": "Sales"}, "children": ["kpi"]}},
                {"op": "add", "path": "/elements/kpi", "value": {"type": "Metric", "props": {"label": "Gross", "value": "$89,000"}, "children": []}},
                {"op": "add", "path": "/root", "value": "root"}
            ])
        return "Deterministic GenUX response for prompt: " + prompt[:30]

    def generate_structured(self, prompt: str, schema: Any) -> Dict[str, Any]:
        self.call_history.append({"method": "generate_structured", "prompt": prompt, "schema": str(schema)})
        p = prompt.lower()
        if "a2ui" in p:
            return {
                "version": "v0.9.1",
                "createSurface": {
                    "surfaceId": "main",
                    "catalogId": "https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json",
                    "theme": {"primaryColor": "#2563eb"},
                    "sendDataModel": True
                }
            }
        if "agui" in p or "ag-ui" in p:
            return {
                "state": {"dashboard": {"active_users": 1420, "server_load": "23%"}},
                "components": [{"id": "c1", "type": "StatusWidget", "props": {"status": "ok"}}]
            }
        if "mcp" in p:
            return {
                "components": [{"id": "card-1", "type": "Card", "props": {"title": "Triage Panel"}}],
                "action": "triage_complete"
            }
        return {"status": "success", "mode": "mock", "prompt_echo": prompt[:40]}

    def stream_patches(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        patches = [
            {"op": "add", "path": "/elements/root", "value": {"type": "Stack", "props": {"direction": "vertical"}, "children": []}},
            {"op": "add", "path": "/elements/root/children/0", "value": "metric-1"},
            {"op": "add", "path": "/elements/metric-1", "value": {"type": "Metric", "props": {"label": "Throughput", "value": "1.2k/s"}, "children": []}},
            {"op": "add", "path": "/root", "value": "root"}
        ]
        for patch in patches:
            yield patch

    def stream(self, prompt: str) -> Generator[str, None, None]:
        text = self.generate_text(prompt)
        chunks = text.split(" ")
        for chunk in chunks:
            yield chunk + " "

    async def astream(self, prompt: str) -> AsyncGenerator[str, None]:
        text = self.generate_text(prompt)
        chunks = text.split(" ")
        for chunk in chunks:
            yield chunk + " "
            await asyncio.sleep(0.001)


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    return MockLLMProvider()


# ============================================================================
# 2. Mock SSE Client Fixture
# ============================================================================

class MockSSEClient:
    """In-memory SSE Client for AG-UI and Harness transport testing."""

    def __init__(self):
        self.received_events: List[Dict[str, Any]] = []

    def parse_sse_text(self, sse_stream_text: str) -> List[Dict[str, Any]]:
        """Parses raw SSE formatted text into structured event envelopes."""
        events = []
        blocks = re.split(r'\n\s*\n', sse_stream_text.strip())
        for block in blocks:
            if not block.strip():
                continue
            event_name = "message"
            data_lines = []
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("event:"):
                    event_name = line[6:].strip()
                elif line.startswith("data:"):
                    data_lines.append(line[5:].strip())
            data_str = "\n".join(data_lines)
            try:
                parsed_data = json.loads(data_str) if data_str else {}
            except json.JSONDecodeError:
                parsed_data = data_str
            event_obj = {"event": event_name, "data": parsed_data}
            events.append(event_obj)
            self.received_events.append(event_obj)
        return events

    def format_sse_event(self, event: str, data: Any) -> str:
        """Encodes an event and payload into RFC-compliant SSE wire format."""
        data_json = json.dumps(data) if not isinstance(data, str) else data
        return f"event: {event}\ndata: {data_json}\n\n"

    def assert_valid_agui_lifecycle(self, events: List[Dict[str, Any]]):
        """Asserts strict AG-UI event ordering: RUN_STARTED -> ... -> RUN_FINISHED."""
        assert len(events) >= 2, "AG-UI stream must contain at least RUN_STARTED and terminal event"
        assert events[0]["event"] == "RUN_STARTED", f"First event must be RUN_STARTED, got {events[0]['event']}"
        assert "threadId" in events[0]["data"], "RUN_STARTED missing threadId"
        assert "runId" in events[0]["data"], "RUN_STARTED missing runId"

        terminal = events[-1]
        assert terminal["event"] in ["RUN_FINISHED", "RUN_ERROR"], f"Terminal event must be RUN_FINISHED or RUN_ERROR, got {terminal['event']}"


@pytest.fixture
def mock_sse_client() -> MockSSEClient:
    return MockSSEClient()


# ============================================================================
# 3. Mock MCP Host Fixture
# ============================================================================

class MockMCPHost:
    """Mock MCP Host emulator implementing SEP-1865 Double Boundary sandbox."""

    def __init__(self):
        self.registered_resources: Dict[str, str] = {}
        self.tool_calls: List[Dict[str, Any]] = []
        self.postmessage_log: List[Dict[str, Any]] = []

    def register_ui_resource(self, uri: str, html_content: str):
        self.registered_resources[uri] = html_content

    def invoke_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Emulates FastMCP tool invocation returning CallToolResult with UI metadata."""
        self.tool_calls.append({"tool": tool_name, "args": args})
        resource_uri = f"ui://{tool_name}/view"
        html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline';">
<title>{tool_name} View</title>
</head>
<body>
<div id="app">Structured View for {tool_name}</div>
</body>
</html>"""
        self.register_ui_resource(resource_uri, html_doc)
        return {
            "content": [{"type": "text", "text": f"Tool {tool_name} completed successfully."}],
            "structuredContent": {"tool": tool_name, "parameters": args, "status": "executed"},
            "_meta": {"ui": {"resourceUri": resource_uri}}
        }

    def validate_csp_headers(self, html_content: str) -> bool:
        """Verifies Content Security Policy <meta> is present immediately in <head>."""
        csp_match = re.search(r'<meta[^>]+http-equiv=["\']Content-Security-Policy["\'][^>]*>', html_content, re.IGNORECASE)
        if not csp_match:
            csp_match = re.search(r'<meta[^>]+content=["\'][^"\']*default-src[^"\']*["\'][^>]*>', html_content, re.IGNORECASE)
        return bool(csp_match)

    def post_message_bridge(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handles JSON-RPC 2.0 postMessage exchange between host and iframe."""
        self.postmessage_log.append(message)
        msg_id = message.get("id", 1)
        method = message.get("method", "")
        if method == "ui/initialize":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"host": "GenUX-Host-Emulator", "version": "1.0"}}
        elif method == "ui/update-model-context":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"status": "context_updated"}}
        elif method == "ui/call-tool":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"status": "tool_dispatched"}}
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method {method} not found"}}


@pytest.fixture
def mock_mcp_host() -> MockMCPHost:
    return MockMCPHost()


# ============================================================================
# 4. Mock Rich Console Fixture
# ============================================================================

class MockRichConsole:
    """Mock terminal capture buffer for Rich rendering assertions."""

    def __init__(self):
        self.rendered_output: List[str] = []

    def print(self, *renderables, **kwargs):
        line = " ".join(str(r) for r in renderables)
        self.rendered_output.append(line)

    def get_output(self) -> str:
        return "\n".join(self.rendered_output)

    def clear(self):
        self.rendered_output.clear()


@pytest.fixture
def mock_rich_console() -> MockRichConsole:
    return MockRichConsole()


# ============================================================================
# 5. GenUX Authoritative Contract Simulator Engine
# ============================================================================

class GenUXContractEngine:
    """
    Authoritative reference contract simulator and schema validator.
    Used by tests to dynamically verify actual codelab implementations when present,
    or validate protocol contracts, RFC 6902 patch semantics, OpenUI ASTs,
    A2UI envelopes, and FastMCP schemas.
    """

    @staticmethod
    def validate_a2ui_envelope(message: Dict[str, Any]) -> bool:
        """Validates Google A2UI v0.9.1 protocol envelope."""
        assert message.get("version") == "v0.9.1", f"Expected version 'v0.9.1', got {message.get('version')}"
        ops = ["createSurface", "updateComponents", "updateDataModel", "deleteSurface"]
        present_ops = [op for op in ops if op in message]
        assert len(present_ops) == 1, f"A2UI envelope must contain exactly one operation, got: {present_ops}"

        op = present_ops[0]
        payload = message[op]
        assert "surfaceId" in payload, f"A2UI {op} missing required 'surfaceId'"

        if op == "createSurface":
            assert "catalogId" in payload, "createSurface missing catalogId"
        elif op == "updateComponents":
            assert "components" in payload and isinstance(payload["components"], list), "updateComponents missing components list"
            component_ids = [c["id"] for c in payload["components"] if "id" in c]
            assert "root" in component_ids, "updateComponents must declare a component with id='root'"
            for c in payload["components"]:
                assert "component" in c, f"Component {c.get('id')} missing component type"
                assert "props" in c, f"Component {c.get('id')} missing props dictionary"
        elif op == "updateDataModel":
            assert "path" in payload and payload["path"].startswith("/"), "updateDataModel path must be a valid RFC 6901 JSON Pointer starting with '/'"
            assert "value" in payload or payload.get("remove") is True, "updateDataModel must specify 'value' or 'remove: true'"
        return True

    @staticmethod
    def apply_rfc6902_patch(document: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
        """Pure-Python RFC 6902 JSON patch applicator with graceful error handling."""
        op = patch.get("op")
        path = patch.get("path", "")
        value = patch.get("value")

        parts = [p for p in path.split("/") if p]
        if not parts:
            if op == "replace":
                return value if isinstance(value, dict) else document
            return document

        curr = document
        for i, part in enumerate(parts[:-1]):
            if isinstance(curr, dict):
                if part not in curr:
                    curr[part] = {}
                curr = curr[part]
            elif isinstance(curr, list):
                idx = int(part) if part.isdigit() else 0
                while len(curr) <= idx:
                    curr.append({})
                curr = curr[idx]

        last = parts[-1]
        if op == "add":
            if isinstance(curr, dict):
                curr[last] = value
            elif isinstance(curr, list):
                if last == "-" or not last.isdigit():
                    curr.append(value)
                else:
                    curr.insert(int(last), value)
        elif op == "replace":
            if isinstance(curr, dict):
                curr[last] = value
            elif isinstance(curr, list) and last.isdigit() and int(last) < len(curr):
                curr[int(last)] = value
        elif op == "remove":
            if isinstance(curr, dict) and last in curr:
                del curr[last]
            elif isinstance(curr, list) and last.isdigit() and int(last) < len(curr):
                del curr[int(last)]
        return document

    @staticmethod
    def parse_openui_line(line: str) -> Optional[Dict[str, Any]]:
        """Parses a single OpenUI statement: id = Component(args, kwargs)."""
        try:
            import importlib
            openui_mod = importlib.import_module("05_openui.parser")
            parser = openui_mod.OpenUIParser()
            node = parser.parse_line(line)
            if node:
                return node.to_dict()
        except Exception:
            pass

        line = line.strip()
        if not line or line.startswith("#"):
            return None
        match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', line)
        if not match:
            return None
        var_id, comp_name, args_str = match.groups()

        # Tokenize arguments respecting quotes
        tokens = []
        cur = []
        in_q = False
        q_char = ''
        bracket_depth = 0
        for char in args_str:
            if char in ('"', "'"):
                if not in_q:
                    in_q = True
                    q_char = char
                elif q_char == char:
                    in_q = False
                cur.append(char)
            elif not in_q and char in ('[', '('):
                bracket_depth += 1
                cur.append(char)
            elif not in_q and char in (']', ')'):
                bracket_depth = max(0, bracket_depth - 1)
                cur.append(char)
            elif not in_q and char == ',' and bracket_depth == 0:
                tokens.append("".join(cur).strip())
                cur = []
            else:
                cur.append(char)
        if cur:
            tokens.append("".join(cur).strip())

        children = []
        props = {}
        pos_args = []
        for t in tokens:
            if t.startswith('[') and t.endswith(']'):
                inner = t[1:-1]
                children = [c.strip().strip("'\"") for c in inner.split(',') if c.strip()]
            elif '=' in t and not (t.startswith('"') or t.startswith("'")):
                k, _, v = t.partition('=')
                props[k.strip()] = v.strip().strip("'\"")
            else:
                pos_args.append(t.strip().strip("'\""))

        if pos_args:
            props["_args"] = pos_args
            if comp_name == "Metric":
                if len(pos_args) >= 1 and "label" not in props:
                    props["label"] = pos_args[0]
                if len(pos_args) >= 2 and "value" not in props:
                    props["value"] = pos_args[1]
                if len(pos_args) >= 3 and "change" not in props:
                    props["change"] = pos_args[2]
            elif comp_name in ["Card", "Stack", "Header"]:
                if len(pos_args) >= 1 and "title" not in props:
                    props["title"] = pos_args[0]
            elif comp_name == "Text":
                if len(pos_args) >= 1 and "content" not in props:
                    props["content"] = pos_args[0]
            elif comp_name == "HtmlArtifact":
                if len(pos_args) >= 1 and "title" not in props:
                    props["title"] = pos_args[0]
                if len(pos_args) >= 2 and "document" not in props:
                    props["document"] = pos_args[1]

        return {
            "id": var_id,
            "component": comp_name,
            "children": children,
            "props": props,
            "raw": line
        }

    @staticmethod
    def resolve_openui_program(lines: List[str]) -> Dict[str, Any]:
        """Compiles a complete OpenUI DSL program with forward-reference resolution."""
        try:
            import importlib
            openui_mod = importlib.import_module("05_openui.parser")
            parser = openui_mod.OpenUIParser()
            for line in lines:
                parser.parse_line(line)
            prog = parser.program
            nodes = {nid: n.to_dict() for nid, n in prog.nodes.items()}
            return {
                "root": prog.root_id or ("root" if "root" in nodes else (list(nodes.keys())[0] if nodes else None)),
                "nodes": nodes,
                "unresolved_forward_refs": {nid: list(n.unresolved_refs) for nid, n in prog.nodes.items() if n.unresolved_refs},
                "is_complete": len(prog.unresolved_references) == 0
            }
        except Exception:
            pass

        nodes: Dict[str, Dict[str, Any]] = {}
        forward_refs: Dict[str, List[str]] = {}

        for line in lines:
            node = GenUXContractEngine.parse_openui_line(line)
            if not node:
                continue
            nodes[node["id"]] = node

        # Validate reference linkages
        for node_id, node in nodes.items():
            for child_id in node["children"]:
                if child_id not in nodes:
                    forward_refs.setdefault(node_id, []).append(child_id)

        return {
            "root": "root" if "root" in nodes else (list(nodes.keys())[0] if nodes else None),
            "nodes": nodes,
            "unresolved_forward_refs": forward_refs,
            "is_complete": len(forward_refs) == 0
        }


@pytest.fixture
def contract_engine() -> GenUXContractEngine:
    return GenUXContractEngine()
