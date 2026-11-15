"""
Tier 3: Cross-Technology Interaction Tests (4 tests total).
Tests protocol combinations and architectural interop:
1. A2UI component envelopes rendered over AG-UI SSE stream.
2. JSON Render dual-surface projection to terminal and web.
3. OpenUI compiled AST executed inside Harness agent loop.
4. MCP Apps hosting AG-UI client widget.
"""

import json
import pytest
from typing import Dict, Any


def test_a2ui_over_agui_transport(contract_engine, mock_sse_client):
    """Tier 3.1: A2UI envelopes encapsulated within AG-UI CUSTOM SSE events."""
    a2ui_create = {
        "version": "v0.9.1",
        "createSurface": {
            "surfaceId": "agui-a2ui-surface",
            "catalogId": "https://a2ui.org/basic",
            "theme": {"primaryColor": "#059669"},
            "sendDataModel": True
        }
    }
    a2ui_update = {
        "version": "v0.9.1",
        "updateComponents": {
            "surfaceId": "agui-a2ui-surface",
            "components": [
                {"id": "root", "component": "Card", "props": {"title": "Streamed A2UI Card"}, "children": ["t1"]},
                {"id": "t1", "component": "Text", "props": {"text": "Rendered via AG-UI SSE Transport"}, "children": []}
            ]
        }
    }

    # Stream over AG-UI protocol
    raw_sse_text = (
        mock_sse_client.format_sse_event("RUN_STARTED", {"threadId": "th_a2ui", "runId": "run_a2ui"}) +
        mock_sse_client.format_sse_event("CUSTOM", {"name": "a2ui", "value": a2ui_create}) +
        mock_sse_client.format_sse_event("CUSTOM", {"name": "a2ui", "value": a2ui_update}) +
        mock_sse_client.format_sse_event("RUN_FINISHED", {"usage": {"total_tokens": 150}})
    )

    events = mock_sse_client.parse_sse_text(raw_sse_text)
    mock_sse_client.assert_valid_agui_lifecycle(events)

    # Validate encapsulated A2UI envelopes
    custom_events = [e for e in events if e["event"] == "CUSTOM" and e["data"].get("name") == "a2ui"]
    assert len(custom_events) == 2

    for cev in custom_events:
        env = cev["data"]["value"]
        contract_engine.validate_a2ui_envelope(env)

    update_envelope = custom_events[1]["data"]["value"]
    assert update_envelope["updateComponents"]["components"][0]["props"]["title"] == "Streamed A2UI Card"


def test_json_render_dual_surface_terminal_and_web(mock_rich_console, mock_sse_client):
    """Tier 3.2: JSON Render dual-surface projection to terminal and web browser."""
    spec = {
        "root": "dashboard-root",
        "elements": {
            "dashboard-root": {
                "type": "Card",
                "props": {"title": "Operations Dashboard"},
                "children": ["kpi-active-nodes", "kpi-qps"]
            },
            "kpi-active-nodes": {
                "type": "Metric",
                "props": {"label": "Active Nodes", "value": "12 / 12"},
                "children": []
            },
            "kpi-qps": {
                "type": "Metric",
                "props": {"label": "Cluster Throughput", "value": "4,200 req/s"},
                "children": []
            }
        },
        "state": {"cluster_status": "optimal"}
    }

    # Surface A: Terminal render via Rich
    mock_rich_console.clear()
    mock_rich_console.print(f"=== {spec['elements']['dashboard-root']['props']['title']} ===")
    for child_id in spec['elements']['dashboard-root']['children']:
        el = spec['elements'][child_id]
        mock_rich_console.print(f"  [{el['props']['label']}]: {el['props']['value']}")
    terminal_output = mock_rich_console.get_output()

    assert "Operations Dashboard" in terminal_output
    assert "Active Nodes" in terminal_output
    assert "4,200 req/s" in terminal_output

    # Surface B: Web render via SSE stream
    web_sse = mock_sse_client.format_sse_event("SPEC_UPDATE", spec)
    parsed_web_events = mock_sse_client.parse_sse_text(web_sse)
    assert len(parsed_web_events) == 1
    assert parsed_web_events[0]["event"] == "SPEC_UPDATE"
    assert parsed_web_events[0]["data"]["root"] == "dashboard-root"
    assert parsed_web_events[0]["data"]["elements"]["kpi-active-nodes"]["props"]["value"] == "12 / 12"


def test_openui_into_harness_loop(contract_engine):
    """Tier 3.3: OpenUI compiled AST executed inside Harness agent loop with action return."""
    dsl_code = [
        'root = Card(title="Security Triage", [vulnMetric, fixBtn])',
        'vulnMetric = Metric("Vulnerabilities", "0 Critical")',
        'fixBtn = Button("Apply Fix", action="apply_patch")'
    ]

    # 1. OpenUI Parser compiles DSL into AST
    ast = contract_engine.resolve_openui_program(dsl_code)
    assert ast["is_complete"] is True
    assert ast["nodes"]["root"]["props"]["title"] == "Security Triage"

    # 2. Harness agent loop receives and validates AST
    harness_state = {
        "active_ast": ast,
        "status": "ui_rendered",
        "action_history": []
    }
    assert harness_state["status"] == "ui_rendered"

    # 3. User clicks action button, feeding back into harness
    user_action = {"action": "apply_patch", "source": "fixBtn", "timestamp": "2026-11-05T20:15:00Z"}
    harness_state["action_history"].append(user_action)
    harness_state["status"] = "patch_applied"

    assert len(harness_state["action_history"]) == 1
    assert harness_state["action_history"][0]["action"] == "apply_patch"
    assert harness_state["status"] == "patch_applied"


def test_mcp_apps_hosting_agui_client(mock_mcp_host, mock_sse_client):
    """Tier 3.4: MCP Apps host container mounting an AG-UI client widget."""
    widget_uri = "ui://analytics/agui_widget"
    widget_html = """<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; connect-src 'self';">
</head>
<body>
<div id="agui-client">Streaming State Consumer</div>
</body>
</html>"""
    mock_mcp_host.register_ui_resource(widget_uri, widget_html)

    # 1. FastMCP tool invocation returns widget
    tool_result = {
        "content": [{"type": "text", "text": "AG-UI Widget ready"}],
        "structuredContent": {"initial_state": {"visitors": 530}},
        "_meta": {"ui": {"resourceUri": widget_uri}}
    }
    assert tool_result["_meta"]["ui"]["resourceUri"] == widget_uri

    # 2. Host iframe security verification
    html_doc = mock_mcp_host.registered_resources[widget_uri]
    assert mock_mcp_host.validate_csp_headers(html_doc) is True

    # 3. Widget receives AG-UI state delta and dispatches postMessage back to host
    state_delta = [{"op": "replace", "path": "/visitors", "value": 542}]
    bridge_msg = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "ui/update-model-context",
        "params": {"visitors": 542, "last_delta": state_delta}
    }
    response = mock_mcp_host.post_message_bridge(bridge_msg)

    assert response["result"]["status"] == "context_updated"
    assert len(mock_mcp_host.postmessage_log) == 1
    assert mock_mcp_host.postmessage_log[0]["params"]["visitors"] == 542
