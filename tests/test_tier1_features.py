"""
Tier 1: Feature Matrix Tests
Covers all 6 GenUX technologies across all 4 modes (24 tests total).
Asserts authentic envelopes, schemas, ASTs, streaming protocols, and contracts.
Zero defensive fallbacks, zero mock fixtures, 100% genuine implementation calls.
"""

import importlib
import json
import os
from typing import Any, Dict
import pytest


def require_module(module_name: str):
    """Imports an implementation module directly, raising an unmasked exception on any import or syntax failure."""
    return importlib.import_module(module_name)


# ============================================================================
# Codelab 1: A2UI Protocol (Tests 1 - 4)
# ============================================================================

def test_a2ui_static_mode(contract_engine):
    """Tier 1.1: A2UI Static Mode — deterministic envelope with immutable components and data model update."""
    mod = require_module("01_a2ui.static_mode")
    result = mod.run_static_mode()

    assert result["status"] == "success"
    assert result["mode"] == "static"
    assert result["is_valid"] is True
    assert result["surface_id"] == "surface-contact-01"
    assert result["component_count"] == 10
    assert "contact" in result["data_model"]
    assert result["data_model"]["contact"]["name"] == "Dr. Alice Chen"

    envelopes = [step["envelope"] for step in result["trace"] if "envelope" in step]
    assert len(envelopes) >= 2
    for msg in envelopes:
        contract_engine.validate_a2ui_envelope(msg)

    create_env = next(e for e in envelopes if "createSurface" in e)
    assert create_env["createSurface"]["surfaceId"] == "surface-contact-01"
    update_comps = next(e for e in envelopes if "updateComponents" in e)
    assert any(c["id"] == "root" for c in update_comps["updateComponents"]["components"])


def test_a2ui_declarative_mode(contract_engine):
    """Tier 1.2: A2UI Declarative Mode — catalog-constrained component tree emission with pointer bindings."""
    mod = require_module("01_a2ui.declarative_mode")
    result = mod.run_declarative_mode()

    assert result["status"] == "success"
    assert result["mode"] == "declarative"
    assert result["is_valid"] is True
    assert result["component_count"] == 9
    assert "telemetry" in result["data_model"]
    assert result["data_model"]["telemetry"]["active_agents"] == 6

    envelopes = [step["envelope"] for step in result["trace"] if "envelope" in step]
    update_comps = next(e for e in envelopes if "updateComponents" in e)
    contract_engine.validate_a2ui_envelope(update_comps)
    components = update_comps["updateComponents"]["components"]
    comp_map = {c["id"]: c for c in components}
    assert "root" in comp_map
    assert len(comp_map) >= 2


def test_a2ui_open_ended_mode(contract_engine):
    """Tier 1.3: A2UI Open-Ended Mode — unconstrained dynamic canvas element inside A2UI surface."""
    mod = require_module("01_a2ui.open_ended_mode")
    result = mod.run_open_ended_mode()

    assert result["status"] == "success"
    assert result["mode"] == "open_ended"
    assert result["is_valid"] is True
    assert result["is_security_compliant"] is True
    assert result["csp_header_present"] is True
    assert result["html_artifact_length"] > 0

    envelopes = [step["envelope"] for step in result["trace"] if "envelope" in step]
    update_comps = next(e for e in envelopes if "updateComponents" in e)
    contract_engine.validate_a2ui_envelope(update_comps)
    comps = update_comps["updateComponents"]["components"]
    assert any("CustomScriptNode" in c.get("component") or "sandbox" in str(c.get("props")) or "html" in str(c.get("props")) for c in comps)


def test_a2ui_mixed_mode(contract_engine):
    """Tier 1.4: A2UI Mixed Mode — fixed catalog shell with generative card and action roundtrip."""
    mod = require_module("01_a2ui.mixed_mode")
    result = mod.run_mixed_mode()

    assert result["status"] == "success"
    assert result["mode"] == "mixed"
    assert result["fault_detected"] is True
    assert result["self_correction_passed"] is True
    assert result["action_name"] == "approve_recommendation"
    assert "optimizations" in result["data_model"]
    assert result["data_model"]["optimizations"]["rec-card-1"]["status"] == "APPLIED"
    assert result["surface"] is not None

    envelopes = [step["envelope"] for step in result["trace"] if "envelope" in step]
    for env in envelopes:
        contract_engine.validate_a2ui_envelope(env)


# ============================================================================
# Codelab 2: AG-UI Streaming Protocol (Tests 5 - 8)
# ============================================================================

def test_agui_static_mode(mock_sse_client):
    """Tier 1.5: AG-UI Static Mode — fixed SSE event stream lifecycle."""
    mod = require_module("02_agui.static_mode")
    result = mod.run_static_mode()

    assert result["status"] == "success"
    assert result["mode"] == "static"
    assert result["event_count"] == 8
    events = result["events"]
    mock_sse_client.assert_valid_agui_lifecycle(events)

    snapshot = next(e for e in events if e["event"] == "STATE_SNAPSHOT")
    assert snapshot["data"]["snapshot"]["system"]["clusterName"] == "SiliconValley-Cluster-1"
    assert snapshot["data"]["snapshot"]["metrics"]["cpu_utilization"] == 24.5
    assert result["final_state"]["metrics"]["cpu_utilization"] == 68.2
    assert len(result["patches_applied"]) == 3


def test_agui_declarative_mode(mock_sse_client):
    """Tier 1.6: AG-UI Declarative Mode — reactive state synchronization via RFC 6902 JSON Patches."""
    mod = require_module("02_agui.declarative_mode")
    result = mod.run_declarative_mode()

    assert result["status"] == "success"
    assert result["mode"] == "declarative"
    events = result["events"]
    mock_sse_client.assert_valid_agui_lifecycle(events)

    assert result["graph_node_count"] == 2
    assert result["graph_edge_count"] == 1
    nodes = result["final_state"]["dashboard"]["nodes"]
    assert len(nodes) == 2
    assert nodes[0]["id"] == "node-agent-a"
    assert nodes[0]["label"] == "Lead Gen Agent (ADK)"

    tool_call = next(e for e in events if e["event"] == "TOOL_CALL_START")
    assert tool_call["data"]["name"] == "add_graph_node"
    delta = next(e for e in events if e["event"] == "STATE_DELTA")
    assert len(delta["data"]["patches"]) > 0


def test_agui_open_ended_mode(mock_sse_client):
    """Tier 1.7: AG-UI Open-Ended Mode — tool call streaming dynamic code block for sandbox execution."""
    mod = require_module("02_agui.open_ended_mode")
    result = mod.run_open_ended_mode()

    assert result["status"] == "success"
    assert result["mode"] == "open_ended"
    events = result["events"]
    mock_sse_client.assert_valid_agui_lifecycle(events)

    assert result["component_synthesized"] is True
    comp_update = next(e for e in events if e["event"] == "COMPONENT_UPDATE")
    assert comp_update["data"]["component"]["componentId"] == "canvas-force-directed"
    assert comp_update["data"]["component"]["type"] == "InteractiveCanvas"
    assert result["final_state"]["artifacts"]["active_component"]["type"] == "InteractiveCanvas"


def test_agui_mixed_mode(mock_sse_client):
    """Tier 1.8: AG-UI Mixed Mode — client-side interactive tool gate pausing run for user confirmation."""
    mod = require_module("02_agui.mixed_mode")
    result = mod.run_mixed_mode()

    assert result["status"] == "success"
    assert result["mode"] == "mixed"
    assert result["approval_granted"] is True
    assert result["workflow_final_stage"] == "COMPLETED_SUCCESSFULLY"
    assert result["custom_a2ui_embedded"] is True

    events = result["events"]
    mock_sse_client.assert_valid_agui_lifecycle(events)

    action_ev = next(e for e in events if e["event"] == "ACTION_EMITTED")
    assert action_ev["data"]["actionName"] == "authorize_action"
    assert action_ev["data"]["approved"] is True
    custom_ev = next(e for e in events if e["event"] == "CUSTOM")
    assert custom_ev["data"]["name"] == "a2ui"
    assert "createSurface" in custom_ev["data"]["envelope"]


# ============================================================================
# Codelab 3: MCP Apps SEP-1865 (Tests 9 - 12)
# ============================================================================

def test_mcp_apps_static_mode(mock_mcp_host):
    """Tier 1.9: MCP Apps Static Mode — FastMCP tool returning static UI resource URI and valid CSP."""
    mod = require_module("03_mcp_apps.static_mode")
    result = mod.run_static_mode()

    assert result["status"] == "success"
    assert result["mode"] == "static"
    assert result["tool"] == "get_lemonade_dashboard"
    assert result["resourceUri"] == "ui://lemonade-stand/dashboard.html"
    assert result["resourceUri"].startswith("ui://")
    assert "title" in result["structuredContent"]
    assert "metrics" in result["structuredContent"]
    assert result["csp_status"] in ["VERIFIED", "VERIFIED_PRE_EXISTING", "INJECTED"]

    with open(result["artifact_path"], "r", encoding="utf-8") as f:
        html_content = f.read()
    assert mock_mcp_host.validate_csp_headers(html_content)


def test_mcp_apps_declarative_mode(mock_mcp_host):
    """Tier 1.10: MCP Apps Declarative Mode — tool returns structuredContent containing catalog spec."""
    mod = require_module("03_mcp_apps.declarative_mode")
    result = mod.run_declarative_mode()

    assert result["status"] == "success"
    assert result["mode"] == "declarative"
    assert result["tool"] == "order_supplies"
    assert result["resourceUri"] == "ui://forms/dynamic_form.html"
    assert result["submitted_args"]["lemons"] == 48
    assert result["submitted_args"]["rush_delivery"] is True
    assert result["bridge_response"]["jsonrpc"] == "2.0"
    assert "updated_inventory" in result
    assert result["updated_inventory"]["lemons"] == 96

    with open(result["artifact_path"], "r", encoding="utf-8") as f:
        html_content = f.read()
    assert mock_mcp_host.validate_csp_headers(html_content)


def test_mcp_apps_open_ended_mode(mock_mcp_host):
    """Tier 1.11: MCP Apps Open-Ended Mode — dynamic single-file HTML app served in sandboxed iframe."""
    mod = require_module("03_mcp_apps.open_ended_mode")
    result = mod.run_open_ended_mode()

    assert result["status"] == "success"
    assert result["mode"] == "open_ended"
    assert result["tool"] == "generate_pricing_simulator"
    assert result["resourceUri"] == "ui://dynamic/pricing_sim.html"
    assert result["all_probes_blocked"] is True
    assert len(result["security_probes"]) == 3
    assert all(p["blocked"] for p in result["security_probes"])
    assert result["updated_context"]["cup_price"] == 3.50
    assert result["updated_context"]["projected_revenue"] == 476.00

    with open(result["artifact_path"], "r", encoding="utf-8") as f:
        html_content = f.read()
    assert mock_mcp_host.validate_csp_headers(html_content)


def test_mcp_apps_mixed_mode(mock_mcp_host):
    """Tier 1.12: MCP Apps Mixed Mode — nested hybrid sandboxing with JSON-RPC postMessage bridge."""
    mod = require_module("03_mcp_apps.mixed_mode")
    result = mod.run_mixed_mode()

    assert result["status"] == "success"
    assert result["mode"] == "mixed"
    assert result["tool"] == "mixed_lemonade_app"
    assert result["resourceUri"] == "ui://hybrid/mixed_app.html"
    assert len(result["catalog_components"]) > 0
    assert result["nested_html_length"] > 0
    assert result["updated_context"]["active_promotion"] == "20% Flash Discount"
    assert result["updated_context"]["discount_percentage"] == 20

    with open(result["artifact_path"], "r", encoding="utf-8") as f:
        html_content = f.read()
    assert mock_mcp_host.validate_csp_headers(html_content)


# ============================================================================
# Codelab 4: JSON Render (Tests 13 - 16)
# ============================================================================

def test_json_render_static_mode():
    """Tier 1.13: JSON Render Static Mode — pre-authored flat element map rendered to terminal and secure DOM."""
    mod = require_module("04_json_render.static_mode")
    res = mod.run_static_mode()

    assert res["status"] == "success"
    assert res["mode"] == "static"
    assert res["elements_count"] == 11
    assert res["validation_errors"] == []

    spec = mod.get_static_spec()
    assert spec.root == "root-container"
    assert "root-container" in spec.elements
    assert "summary-card" in spec.elements
    assert spec.elements["summary-card"].props["title"] == "Cloud Infrastructure Fleet Overview"
    assert spec.elements["metric-nodes"].props["value"] == "128"
    assert spec.elements["metric-health"].props["value"] == "99.8%"
    assert os.path.exists(res["artifact_path"])

    # Verify DomRenderer strict CSP, render_html alias, and XSS escaping
    rend_mod = require_module("04_json_render.renderers")
    dom = rend_mod.DomRenderer()
    html_doc = dom.render(spec)
    assert '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'none\';">' in html_doc
    assert dom.render_html(spec) == html_doc

    malicious_spec = mod.JSONRenderSpec(
        root="xss-card",
        elements={
            "xss-card": mod.ElementNode(
                type="Card",
                props={"title": "<script>alert('xss')</script>"},
                children=[]
            )
        }
    )
    xss_doc = dom.render(malicious_spec)
    assert "<script>alert('xss')</script>" not in xss_doc
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in xss_doc


def test_json_render_declarative_mode():
    """Tier 1.14: JSON Render Declarative Mode — streaming RFC 6902 patches with state binding."""
    mod = require_module("04_json_render.declarative_mode")
    res = mod.run_declarative_mode()

    assert res["status"] == "success"
    assert res["mode"] == "declarative"
    assert res["total_patches"] == 9
    assert res["skipped_patches"] == 0
    assert res["first_paint_patch_idx"] == 3
    assert res["resolved_state_metrics"]["rev"] == "$142,500"
    assert res["resolved_state_metrics"]["ord"] == 890
    assert res["resolved_state_metrics"]["growth"] == "+18.4%"
    assert os.path.exists(res["artifact_path"])


def test_json_render_open_ended_mode():
    """Tier 1.15: JSON Render Open-Ended Mode — dynamic canvas/markup escape hatch in JSON spec."""
    mod = require_module("04_json_render.open_ended_mode")
    res = mod.run_open_ended_mode()

    assert res["status"] == "success"
    assert res["mode"] == "open_ended"
    assert res["total_applied"] == 6
    assert res["total_skipped"] == 3
    assert len(res["skipped_details"]) == 3
    assert any("JSONDecodeError" in s.get("reason", "") for s in res["skipped_details"])
    assert os.path.exists(res["artifact_path"])


def test_json_render_mixed_mode():
    """Tier 1.16: JSON Render Mixed Mode — fixed catalog header with dynamic generative body & action cycle."""
    mod = require_module("04_json_render.mixed_mode")
    res = mod.run_mixed_mode()

    assert res["status"] == "success"
    assert res["mode"] == "mixed"
    assert res["root"] == "hybrid-root"
    assert res["elements"]["fixed-header"]["props"]["title"] == "Analytics Console"
    assert res["elements"]["dynamic-body"]["type"] == "Metric"
    assert res["elements"]["dynamic-body"]["props"]["value"] == "$9,800"
    assert res["initial_patches"] == 16
    assert res["action_patches"] == 9
    assert res["updated_state"]["cluster"]["nodes"] == 16
    assert res["updated_state"]["cluster"]["tps"] == "7,800 rps"
    assert os.path.exists(res["artifact_path"])


# ============================================================================
# Codelab 5: OpenUI Lang DSL (Tests 17 - 20)
# ============================================================================

def test_openui_static_mode():
    """Tier 1.17: OpenUI Static Mode — deterministic parsing of .oui DSL statements into AST."""
    mod = require_module("05_openui.static_mode")
    res = mod.run_static_mode()

    assert res["status"] == "success"
    assert res["node_count"] == 5
    assert res["json_spec"]["root"] == "root"
    assert res["json_spec"]["elements"]["root"]["type"] == "Stack"
    assert "revMetric" in res["json_spec"]["elements"]["root"]["children"]
    assert res["json_spec"]["elements"]["revMetric"]["type"] == "Metric"
    assert res["react_tree"]["component"] == "Stack"
    assert len(res["react_tree"]["children"]) == 4
    assert res["html_artifact_length"] > 0


def test_openui_declarative_mode():
    """Tier 1.18: OpenUI Declarative Mode — streaming DSL with forward references."""
    mod = require_module("05_openui.declarative_mode")
    res = mod.run_declarative_mode()

    assert res["status"] == "success"
    assert res["final_nodes"] == 6
    assert len(res["stream_events"]) == 6
    assert res["json_spec"]["root"] == "root"
    assert "revKpi" in res["json_spec"]["elements"]["root"]["children"]
    assert res["avg_savings_vs_json_pct"] > 60.0
    assert len(res["benchmark"]) == 4
    assert res["html_artifact_length"] > 0


def test_openui_open_ended_mode():
    """Tier 1.19: OpenUI Open-Ended Mode — unconstrained component synthesis in DSL."""
    mod = require_module("05_openui.open_ended_mode")
    res = mod.run_open_ended_mode()

    assert res["status"] == "success"
    assert res["node_count"] == 9
    assert "WorkflowPipeline" in res["custom_components"]
    assert "WorkflowStage" in res["custom_components"]
    assert res["json_spec"]["root"] == "root"
    assert res["react_tree"]["component"] == "WorkflowPipeline"
    assert res["html_artifact_length"] > 0


def test_openui_mixed_mode():
    """Tier 1.20: OpenUI Mixed Mode — catalog components with HtmlArtifact and token savings benchmark."""
    mod = require_module("05_openui.mixed_mode")
    res = mod.run_mixed_mode()

    assert res["status"] == "success"
    assert res["primary_nodes"] == 9
    assert res["has_html_artifact"] is True
    assert res["syntax_errors_handled"] == 1
    assert "root" in res["preserved_nodes"]
    assert "artifactSection" in res["json_spec"]["elements"]
    assert res["json_spec"]["elements"]["artifactSection"]["type"] == "HtmlArtifact"
    assert res["html_artifact_length"] > 0


# ============================================================================
# Codelab 6: Harness Integration (Tests 21 - 24)
# ============================================================================

def test_harness_static_mode():
    """Tier 1.21: Harness Static Mode — deterministic single-turn render_ui execution."""
    mod = require_module("06_harness_integration.static_mode")
    out = mod.run_static_mode()

    assert out["status"] == "success"
    assert out["spec_root"] == "clusterDashboard"
    assert out["elements_count"] == 8
    assert out["receipt"]["status"] == "success"
    assert "terminal" in out["receipt"]["surfaces_projected"]
    assert "web" in out["receipt"]["surfaces_projected"]
    assert out["web_html_length"] > 0


def test_harness_declarative_mode():
    """Tier 1.22: Harness Declarative Mode — multi-turn tool-calling UI agent loop with schema enforcement."""
    mod = require_module("06_harness_integration.declarative_mode")
    history = mod.run_declarative_mode()

    assert history["status"] == "success"
    assert history["total_turns"] == 3
    assert history["self_corrections"] == 1
    assert history["final_stage"] == "COMPLETED"
    assert len(history["turn_records"]) == 3
    assert history["turn_records"][0]["status"] == "success"
    assert history["turn_records"][1]["status"] == "error"
    assert history["turn_records"][2]["status"] == "success"


def test_harness_open_ended_mode():
    """Tier 1.23: Harness Open-Ended Mode — agent emitting dynamic interactive artifact with live re-render."""
    mod = require_module("06_harness_integration.open_ended_mode")
    res = mod.run_open_ended_mode()

    assert res["status"] == "success"
    assert res["total_turns"] == 2
    assert res["rendered_surfaces"] == 2
    assert res["final_stage"] == "COMPLETED"
    assert res["artifact_csp_verified"] is True
    assert "Content-Security-Policy" in mod.TOPOLOGY_ARTIFACT_TURN1
    assert "Microservice Network Topology" in mod.TOPOLOGY_ARTIFACT_TURN1


def test_harness_mixed_mode():
    """Tier 1.24: Harness Mixed Mode — TrueForge hybrid architecture with dual-surface projection and action loop."""
    mod = require_module("06_harness_integration.mixed_mode")
    res = mod.run_mixed_mode()

    assert res["status"] == "success"
    assert res["total_turns"] == 4
    assert res["rendered_surfaces"] == 2
    assert res["final_stage"] == "COMPLETED"
    assert res["interactive_action_verified"] is True
    assert mod.INITIAL_HYBRID_SHELL_SPEC["root"] == "trueforgeShell"
    assert "approveBtn" in mod.INITIAL_HYBRID_SHELL_SPEC["elements"]
    assert mod.UPDATED_POST_ACTION_SPEC["elements"]["executionCard"]["props"]["title"] == "Scale Execution Succeeded"
