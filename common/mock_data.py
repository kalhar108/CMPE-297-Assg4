"""Deterministic mock datasets and schema-valid GenUX artifacts for offline execution.

Provides pre-seeded, realistic data models, component trees, JSON patches,
and protocol envelopes for A2UI, AG-UI, and shared GenUX demonstrations.
"""

from __future__ import annotations

from typing import Any, Dict, List

# ==============================================================================
# Codelab 1: A2UI Protocol Mock Data
# ==============================================================================

# A2UI Catalog Specification URI
A2UI_BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json"

# Static Mode: Deterministic Contact Form Surface
A2UI_STATIC_CREATE_SURFACE = {
    "surfaceId": "surface-contact-01",
    "catalogId": A2UI_BASIC_CATALOG_ID,
    "theme": {
        "primaryColor": "#2563eb",
        "borderRadius": "8px",
        "fontFamily": "Inter, system-ui, sans-serif",
    },
    "sendDataModel": True,
}

A2UI_STATIC_COMPONENTS: List[Dict[str, Any]] = [
    {
        "id": "root",
        "component": "Card",
        "props": {
            "title": "Faculty & Staff Contact Directory",
            "subtitle": "Department of Artificial Intelligence & Computer Science",
        },
        "children": ["header-text", "form-column", "action-row"],
    },
    {
        "id": "header-text",
        "component": "Text",
        "props": {
            "text": "Please verify your academic affiliation and contact details below.",
            "variant": "body2",
        },
        "children": [],
    },
    {
        "id": "form-column",
        "component": "Column",
        "props": {"gap": "12px"},
        "children": ["name-field", "email-field", "role-field", "office-field"],
    },
    {
        "id": "name-field",
        "component": "TextField",
        "props": {
            "label": "Full Name",
            "value": {"path": "/contact/name"},
            "placeholder": "Dr. Alice Chen",
        },
        "children": [],
    },
    {
        "id": "email-field",
        "component": "TextField",
        "props": {
            "label": "Email Address",
            "value": {"path": "/contact/email"},
            "placeholder": "alice.chen@sjsu.edu",
        },
        "children": [],
    },
    {
        "id": "role-field",
        "component": "TextField",
        "props": {
            "label": "Academic Title / Role",
            "value": {"path": "/contact/role"},
            "placeholder": "Associate Professor",
        },
        "children": [],
    },
    {
        "id": "office-field",
        "component": "TextField",
        "props": {
            "label": "Campus Office",
            "value": {"path": "/contact/office"},
            "placeholder": "Engineering Building Room 284",
        },
        "children": [],
    },
    {
        "id": "action-row",
        "component": "Row",
        "props": {"justify": "flex-end", "gap": "8px"},
        "children": ["reset-btn", "submit-btn"],
    },
    {
        "id": "reset-btn",
        "component": "Button",
        "props": {
            "label": "Reset Defaults",
            "variant": "outlined",
            "action": {
                "name": "reset_form",
                "context": {"surface": "surface-contact-01"},
            },
        },
        "children": [],
    },
    {
        "id": "submit-btn",
        "component": "Button",
        "props": {
            "label": "Confirm & Save",
            "variant": "contained",
            "action": {
                "name": "submit_contact",
                "context": {
                    "name": {"path": "/contact/name"},
                    "email": {"path": "/contact/email"},
                    "role": {"path": "/contact/role"},
                    "office": {"path": "/contact/office"},
                },
            },
        },
        "children": [],
    },
]

A2UI_STATIC_DATA_MODEL: Dict[str, Any] = {
    "contact": {
        "name": "Dr. Alice Chen",
        "email": "alice.chen@sjsu.edu",
        "role": "Associate Professor of AI",
        "office": "ENG 284",
    },
    "metadata": {
        "department": "Computer Science & Engineering",
        "lastUpdated": "2026-11-05T20:00:00Z",
    },
}

# Declarative Mode: Dynamic Analytics Dashboard Surface
A2UI_DECLARATIVE_CREATE_SURFACE = {
    "surfaceId": "surface-analytics-02",
    "catalogId": A2UI_BASIC_CATALOG_ID,
    "theme": {
        "primaryColor": "#10b981",
        "borderRadius": "12px",
    },
    "sendDataModel": True,
}

A2UI_DECLARATIVE_COMPONENTS: List[Dict[str, Any]] = [
    {
        "id": "root",
        "component": "Card",
        "props": {
            "title": "GenUX Intelligent Operations Center",
            "subtitle": "Real-time Multi-Agent Cluster Telemetry",
        },
        "children": ["kpi-row", "metrics-table", "controls-row"],
    },
    {
        "id": "kpi-row",
        "component": "Row",
        "props": {"gap": "16px", "justify": "space-between"},
        "children": ["kpi-active-agents", "kpi-tokens-saved", "kpi-p99-latency"],
    },
    {
        "id": "kpi-active-agents",
        "component": "Metric",
        "props": {
            "label": "Active Agent Workers",
            "value": {"path": "/telemetry/active_agents"},
            "delta": "+4 online",
            "status": "success",
        },
        "children": [],
    },
    {
        "id": "kpi-tokens-saved",
        "component": "Metric",
        "props": {
            "label": "Token Compression Ratio",
            "value": {"path": "/telemetry/token_savings"},
            "delta": "73.2% vs JSON",
            "status": "success",
        },
        "children": [],
    },
    {
        "id": "kpi-p99-latency",
        "component": "Metric",
        "props": {
            "label": "P99 SSE Stream Latency",
            "value": {"path": "/telemetry/p99_latency_ms"},
            "delta": "-14ms",
            "status": "neutral",
        },
        "children": [],
    },
    {
        "id": "metrics-table",
        "component": "List",
        "props": {
            "title": "High Priority Dispatch Queue",
            "items": {"path": "/telemetry/dispatches"},
        },
        "children": [],
    },
    {
        "id": "controls-row",
        "component": "Row",
        "props": {"justify": "flex-end", "gap": "10px"},
        "children": ["refresh-btn", "rebalance-btn"],
    },
    {
        "id": "refresh-btn",
        "component": "Button",
        "props": {
            "label": "Refresh Metrics",
            "variant": "outlined",
            "action": {
                "name": "refresh_telemetry",
                "context": {"cluster": "us-west-1"},
            },
        },
        "children": [],
    },
    {
        "id": "rebalance-btn",
        "component": "Button",
        "props": {
            "label": "Auto-Scale Workers",
            "variant": "contained",
            "action": {
                "name": "auto_scale_workers",
                "context": {
                    "currentCount": {"path": "/telemetry/active_agents"},
                    "targetCount": 8,
                },
            },
        },
        "children": [],
    },
]

A2UI_DECLARATIVE_DATA_MODEL: Dict[str, Any] = {
    "telemetry": {
        "active_agents": 6,
        "token_savings": "73.2%",
        "p99_latency_ms": "38ms",
        "dispatches": [
            {"id": "disp-01", "task": "A2UI Envelope Validation", "status": "COMPLETED"},
            {"id": "disp-02", "task": "AG-UI State Patch Stream", "status": "IN_PROGRESS"},
            {"id": "disp-03", "task": "OpenUI DSL Token Benchmark", "status": "QUEUED"},
        ],
    }
}

# Open-Ended Mode: Sandboxed Lit / HTML Component Artifact
A2UI_OPEN_ENDED_CREATE_SURFACE = {
    "surfaceId": "surface-openended-03",
    "catalogId": A2UI_BASIC_CATALOG_ID,
    "theme": {"primaryColor": "#8b5cf6"},
    "sendDataModel": False,
}

A2UI_OPEN_ENDED_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
  <style>
    :host, body {
      font-family: system-ui, -apple-system, sans-serif;
      margin: 0; padding: 16px;
      background: #0f172a; color: #f8fafc;
    }
    .viz-container {
      border: 1px solid #334155; border-radius: 8px; padding: 16px;
      background: #1e293b;
    }
    .node-grid { display: flex; gap: 12px; margin-top: 12px; }
    .node {
      flex: 1; padding: 12px; border-radius: 6px;
      background: #334155; text-align: center;
      transition: all 0.3s ease;
    }
    .node.active { background: #8b5cf6; color: white; transform: scale(1.03); }
    button {
      margin-top: 16px; background: #8b5cf6; color: white; border: none;
      padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 600;
    }
    button:hover { background: #7c3aed; }
  </style>
</head>
<body>
  <div class="viz-container">
    <h3>Neural Attention Layer Simulation</h3>
    <p style="font-size: 0.9em; color: #94a3b8;">Generative interactive component rendered in sandboxed iframe boundary.</p>
    <div class="node-grid">
      <div class="node active" id="n1">Token: [Query]</div>
      <div class="node" id="n2">Token: [Key]</div>
      <div class="node active" id="n3">Token: [Value]</div>
    </div>
    <button onclick="document.querySelectorAll('.node').forEach(n => n.classList.toggle('active'))">
      Simulate Attention Head Switch
    </button>
  </div>
</body>
</html>"""

A2UI_OPEN_ENDED_COMPONENTS: List[Dict[str, Any]] = [
    {
        "id": "root",
        "component": "Card",
        "props": {
            "title": "Sandboxed Generative Lit Component Canvas",
            "subtitle": "Open-Ended UX Mode with Strict Content Security Policy",
        },
        "children": ["sandbox-frame"],
    },
    {
        "id": "sandbox-frame",
        "component": "CustomScriptNode",
        "props": {
            "title": "Attention Visualization Sandbox",
            "html": A2UI_OPEN_ENDED_HTML,
            "sandboxAttributes": "allow-scripts",
            "csp": "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        },
        "children": [],
    },
]

# Mixed Mode: Catalog Shell + Generative Recommendation Cards + Self-Correction
A2UI_MIXED_CREATE_SURFACE = {
    "surfaceId": "surface-mixed-04",
    "catalogId": A2UI_BASIC_CATALOG_ID,
    "theme": {"primaryColor": "#ec4899"},
    "sendDataModel": True,
}

A2UI_MIXED_COMPONENTS_INITIAL: List[Dict[str, Any]] = [
    {
        "id": "root",
        "component": "Card",
        "props": {
            "title": "Agentic Optimization Studio",
            "subtitle": "Catalog Shell with Generative Cards & Self-Correction",
        },
        "children": ["fixed-header", "dynamic-recommendations-column", "fixed-footer"],
    },
    {
        "id": "fixed-header",
        "component": "Text",
        "props": {
            "text": "Deterministic navigation and security envelope active.",
            "variant": "caption",
        },
        "children": [],
    },
    {
        "id": "dynamic-recommendations-column",
        "component": "Column",
        "props": {"gap": "10px"},
        "children": ["rec-card-1"],
    },
    {
        "id": "rec-card-1",
        "component": "Card",
        "props": {
            "title": "Autonomous Suggestion: Cache Partition Optimization",
            "subtitle": "Generated via frontier reasoning loop",
        },
        "children": ["rec-text", "rec-approve-btn"],
    },
    {
        "id": "rec-text",
        "component": "Text",
        "props": {
            "text": "Allocating 512MB L2 cache to worker pod #3 will reduce tail latency by 24%.",
        },
        "children": [],
    },
    {
        "id": "rec-approve-btn",
        "component": "Button",
        "props": {
            "label": "Approve Optimization",
            "variant": "contained",
            "action": {
                "name": "approve_recommendation",
                "context": {"recommendationId": "rec-card-1", "action": "apply_cache_partition"},
            },
        },
        "children": [],
    },
    {
        "id": "fixed-footer",
        "component": "Text",
        "props": {
            "text": "System status: Ready for user interaction.",
            "variant": "overline",
        },
        "children": [],
    },
]

# Deliberate malformed envelope for self-correction testing (missing root, dangling child)
A2UI_MALFORMED_COMPONENTS: List[Dict[str, Any]] = [
    {
        "id": "orphan-card",
        "component": "Card",
        "props": {"title": "Malformed Element"},
        "children": ["non-existent-child"],
    }
]

# Fixed corrected envelope after self-correction loop
A2UI_SELF_CORRECTED_COMPONENTS: List[Dict[str, Any]] = [
    {
        "id": "root",
        "component": "Card",
        "props": {"title": "Self-Corrected Active Surface"},
        "children": ["corrected-text"],
    },
    {
        "id": "corrected-text",
        "component": "Text",
        "props": {"text": "Schema integrity verified: 'root' restored and child references valid."},
        "children": [],
    },
]

# ==============================================================================
# Codelab 2: AG-UI Streaming Protocol Mock Data
# ==============================================================================

# Static Mode: Pre-defined SSE Stream Sequence
AGUI_STATIC_RUN_ID = "run-agui-static-01"
AGUI_THREAD_ID = "thread-genux-lecture"

AGUI_STATIC_INITIAL_STATE = {
    "system": {
        "clusterName": "SiliconValley-Cluster-1",
        "region": "us-west-1",
        "health": "OPTIMAL",
    },
    "metrics": {
        "cpu_utilization": 24.5,
        "memory_gb": 3.8,
        "throughput_qps": 4200,
    },
    "alerts": [],
}

AGUI_STATIC_STATE_PATCHES = [
    {"op": "replace", "path": "/metrics/cpu_utilization", "value": 68.2},
    {"op": "add", "path": "/alerts/-", "value": {"severity": "warning", "msg": "Traffic surge detected: +45% in 60s"}},
    {"op": "add", "path": "/system/lastChecked", "value": "2026-11-05T20:05:00Z"},
]

# Declarative Mode: Reactive State Graph Patches
AGUI_DECLARATIVE_INITIAL_STATE = {
    "dashboard": {
        "title": "Reactive Multi-Agent Graph",
        "nodes": [],
        "edges": [],
        "summary": "Graph initialization pending...",
    }
}

AGUI_DECLARATIVE_TOOL_CALL = {
    "toolCallId": "call-graph-node-add",
    "name": "add_graph_node",
    "args": {
        "nodeId": "node-agent-a",
        "label": "Lead Gen Agent (ADK)",
        "status": "ACTIVE",
        "load": "42%",
    },
}

AGUI_DECLARATIVE_PATCHES = [
    {
        "op": "add",
        "path": "/dashboard/nodes/-",
        "value": {
            "id": "node-agent-a",
            "label": "Lead Gen Agent (ADK)",
            "status": "ACTIVE",
            "load": "42%",
        },
    },
    {
        "op": "add",
        "path": "/dashboard/nodes/-",
        "value": {
            "id": "node-agent-b",
            "label": "Code Reviewer Agent",
            "status": "PROCESSING",
            "load": "78%",
        },
    },
    {
        "op": "add",
        "path": "/dashboard/edges/-",
        "value": {"from": "node-agent-a", "to": "node-agent-b", "relation": "dispatches_review"},
    },
    {
        "op": "replace",
        "path": "/dashboard/summary",
        "value": "2 active nodes connected via reactive event bridge.",
    },
]

# Open-Ended Mode: Conversational Graph + HTML Component Stream
AGUI_OPEN_ENDED_REASONING_CHUNKS = [
    "Analyzing requested component parameters for live interactive graph...\n",
    "Synthesizing reactive HTML5 canvas visualizer with force-directed physics...\n",
    "Generating sandboxed event listener bindings for drag-and-drop node inspection...\n",
]

AGUI_OPEN_ENDED_COMPONENT = {
    "componentId": "canvas-force-directed",
    "type": "InteractiveCanvas",
    "html": """<div class='interactive-graph-widget'>
  <h4>Live Topological Force Graph</h4>
  <canvas id='top-canvas' width='400' height='220' style='background:#1e293b;border-radius:6px;'></canvas>
  <p style='color:#a855f7; font-size:12px;'>Nodes: 3 | Dynamic Spring Simulation Running</p>
</div>""",
    "statePath": "/artifacts/force_graph",
}

# Mixed Mode: Core Metrics + Client Approval Gate + Embedded A2UI
AGUI_MIXED_INITIAL_STATE = {
    "workflow": {
        "id": "wf-auto-migrate-84",
        "stage": "AWAITING_APPROVAL",
        "targetDb": "Cloud Spanner Multi-Region",
        "estimatedDowntime": "0 seconds",
        "riskScore": 0.12,
    },
    "history": [],
}

AGUI_MIXED_APPROVAL_TOOL_CALL = {
    "toolCallId": "call-approval-gate-99",
    "name": "request_human_approval",
    "args": {
        "workflowId": "wf-auto-migrate-84",
        "prompt": "Authorize live database schema migration to Cloud Spanner?",
        "requiredRole": "DevOps Engineer",
    },
}

AGUI_MIXED_POST_APPROVAL_PATCHES = [
    {"op": "replace", "path": "/workflow/stage", "value": "EXECUTING_MIGRATION"},
    {"op": "add", "path": "/history/-", "value": {"action": "APPROVED", "by": "user-cli", "timestamp": "2026-11-05T20:06:00Z"}},
]

AGUI_MIXED_COMPLETION_PATCHES = [
    {"op": "replace", "path": "/workflow/stage", "value": "COMPLETED_SUCCESSFULLY"},
    {"op": "add", "path": "/workflow/completionTime", "value": "2026-11-05T20:06:02Z"},
]

# Helper function to fetch mock data by key
MOCK_DATASETS: Dict[str, Any] = {
    "a2ui_static_create": A2UI_STATIC_CREATE_SURFACE,
    "a2ui_static_components": A2UI_STATIC_COMPONENTS,
    "a2ui_static_data": A2UI_STATIC_DATA_MODEL,
    "a2ui_declarative_create": A2UI_DECLARATIVE_CREATE_SURFACE,
    "a2ui_declarative_components": A2UI_DECLARATIVE_COMPONENTS,
    "a2ui_declarative_data": A2UI_DECLARATIVE_DATA_MODEL,
    "a2ui_open_ended_create": A2UI_OPEN_ENDED_CREATE_SURFACE,
    "a2ui_open_ended_components": A2UI_OPEN_ENDED_COMPONENTS,
    "a2ui_open_ended_html": A2UI_OPEN_ENDED_HTML,
    "a2ui_mixed_create": A2UI_MIXED_CREATE_SURFACE,
    "a2ui_mixed_components": A2UI_MIXED_COMPONENTS_INITIAL,
    "agui_static_initial": AGUI_STATIC_INITIAL_STATE,
    "agui_static_patches": AGUI_STATIC_STATE_PATCHES,
    "agui_declarative_initial": AGUI_DECLARATIVE_INITIAL_STATE,
    "agui_declarative_tool": AGUI_DECLARATIVE_TOOL_CALL,
    "agui_declarative_patches": AGUI_DECLARATIVE_PATCHES,
    "agui_open_ended_chunks": AGUI_OPEN_ENDED_REASONING_CHUNKS,
    "agui_open_ended_component": AGUI_OPEN_ENDED_COMPONENT,
    "agui_mixed_initial": AGUI_MIXED_INITIAL_STATE,
    "agui_mixed_approval_tool": AGUI_MIXED_APPROVAL_TOOL_CALL,
    "agui_mixed_patches": AGUI_MIXED_POST_APPROVAL_PATCHES,
}


def get_mock_data(key: str) -> Any:
    """Retrieves a pre-seeded mock dataset by key."""
    if key not in MOCK_DATASETS:
        raise KeyError(f"Mock dataset key '{key}' not found. Available: {list(MOCK_DATASETS.keys())}")
    return MOCK_DATASETS[key]
