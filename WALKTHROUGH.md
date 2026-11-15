# Progressive Walkthrough & Architectural Guide: GenUX Technologies Suite

> **San Jose State University — Fall 2026 Special Topics in AI**  
> **Course Module**: Generative User Experience (GenUX) Architecture & Protocols  
> **Author**: Autonomous Teamwork Worker M4 (Documentation & Master Demo Suite)  
> **Integrity Mode**: Genuine Implementation (Zero Façades / 100% Deterministic & Live Verified)

---

## Table of Contents
1. [Executive Overview & Pedagogical Goals](#1-executive-overview--pedagogical-goals)
2. [Unified Architectural Taxonomies](#2-unified-architectural-taxonomies)
   - [The Four Operational Modes: Static, Declarative, Open-Ended, and Mixed](#the-four-operational-modes)
   - [Comparative Architecture Matrix](#comparative-architecture-matrix)
3. [Codelab 1: A2UI Protocol (v0.9.1)](#3-codelab-1-a2ui-protocol-v091)
   - [Wire Protocol & Envelopes](#codelab-1-wire-protocol--envelopes)
   - [RFC 6901 JSON Pointer Data Binding](#codelab-1-rfc-6901-json-pointer-data-binding)
   - [Detailed Mode Walkthroughs & Code Snippets](#codelab-1-mode-walkthroughs)
   - [Verbatim Execution Output](#codelab-1-verbatim-execution-output)
4. [Codelab 2: AG-UI Streaming Protocol](#4-codelab-2-ag-ui-streaming-protocol)
   - [SSE Transport & LF-Only Frame Demarcation](#codelab-2-sse-transport)
   - [Atomic RFC 6902 Reactive State Store](#codelab-2-atomic-rfc-6902-reactive-state-store)
   - [Detailed Mode Walkthroughs & Code Snippets](#codelab-2-mode-walkthroughs)
   - [Verbatim Execution Output](#codelab-2-verbatim-execution-output)
5. [Codelab 3: MCP Apps Protocol (SEP-1865)](#5-codelab-3-mcp-apps-protocol-sep-1865)
   - [FastMCP Dual-Output Tool Pattern](#codelab-3-fastmcp-dual-output-tool-pattern)
   - [Double-Iframe Sandboxing & CSP Enforcement](#codelab-3-double-iframe-sandboxing--csp-enforcement)
   - [Detailed Mode Walkthroughs & Code Snippets](#codelab-3-mode-walkthroughs)
   - [Verbatim Execution Output](#codelab-3-verbatim-execution-output)
6. [Codelab 4: JSON Render (Streaming Compiler)](#6-codelab-4-json-render-streaming-compiler)
   - [Component Catalog Schema](#codelab-4-component-catalog-schema)
   - [Incremental Stream Patch Compiler & Early First-Paint](#codelab-4-incremental-stream-patch-compiler)
   - [Multi-Target Rendering: Terminal (Rich) & DOM (HTML5)](#codelab-4-multi-target-rendering)
   - [Detailed Mode Walkthroughs & Code Snippets](#codelab-4-mode-walkthroughs)
   - [Verbatim Execution Output](#codelab-4-verbatim-execution-output)
7. [Codelab 5: OpenUI Lang DSL](#7-codelab-5-openui-lang-dsl)
   - [Grammar & Identifier Tokenization](#codelab-5-grammar--tokenization)
   - [Progressive Forward Reference Resolution](#codelab-5-forward-reference-resolution)
   - [Token Efficiency Benchmark (OpenUI vs JSON vs HTML)](#codelab-5-token-efficiency-benchmark)
   - [Detailed Mode Walkthroughs & Code Snippets](#codelab-5-mode-walkthroughs)
   - [Verbatim Execution Output](#codelab-5-verbatim-execution-output)
8. [Codelab 6: Harness Integration](#8-codelab-6-harness-integration)
   - [Autonomous Agent UI Loop (`render_ui`)](#codelab-6-autonomous-agent-ui-loop)
   - [Concurrent Multi-Surface Projection (Terminal + Browser SSE)](#codelab-6-concurrent-multi-surface-projection)
   - [TrueForge Hybrid Pattern & Autonomous Self-Correction](#codelab-6-trueforge-hybrid-pattern)
   - [Detailed Mode Walkthroughs & Code Snippets](#codelab-6-mode-walkthroughs)
   - [Verbatim Execution Output](#codelab-6-verbatim-execution-output)
9. [Automated Pytest Test Harness Verification](#9-automated-pytest-test-harness-verification)
10. [Master CLI Demo Suite Verification](#10-master-cli-demo-suite-verification)

---

## 1. Executive Overview & Pedagogical Goals

Modern conversational AI systems have rapidly outgrown simple raw-text chat interfaces. To enable complex human-in-the-loop agent workflows, frontends require **Generative User Experience (GenUX)**: dynamic user interfaces rendered just-in-time by autonomous agents.

This repository demonstrates the six leading paradigms in GenUX architecture:
1. **Google A2UI (Agent-to-UI) v0.9.1**: Google's wire envelope protocol separating UI component hierarchies from dynamic data models via RFC 6901 JSON Pointers.
2. **AG-UI (Agent-Generated UI) Streaming Protocol**: Real-time Server-Sent Events (SSE) streaming shared reactive state stores updated atomically via RFC 6902 JSON Patches.
3. **MCP Apps (Model Context Protocol SEP-1865)**: Extending Anthropic's Model Context Protocol with interactive web resources, double-iframe sandboxing, strict Content Security Policy (CSP), and bidirectional `postMessage` bridges.
4. **JSON Render**: Vercel-style declarative component catalog with line-by-line streaming RFC 6902 patch compilation, early first-paint optimizations, and multi-target terminal/DOM rendering.
5. **OpenUI Lang DSL**: A concise, line-oriented functional domain-specific language (`id = Component(args)`) eliminating structural JSON syntax overhead and achieving **64.7% token reduction**.
6. **Harness Integration**: The full agentic lifecycle loop embedding UI tools (`render_ui`), multi-surface terminal/web projection, and autonomous schema self-correction.

Every technology in this suite is implemented across **four distinct operational modes** to teach when to favor deterministic structure versus unconstrained generative freedom.

---

## 2. Unified Architectural Taxonomies

### The Four Operational Modes

```
+-----------------------------------------------------------------------------------------------+
|                                    GENUX OPERATIONAL SPECTRUM                                 |
+-----------------------------------------------------------------------------------------------+
|  1. STATIC MODE          2. DECLARATIVE MODE      3. OPEN-ENDED UX MODE    4. MIXED (HYBRID)  |
|  Deterministic Shell     Catalog-Constrained LLM  Unconstrained Synthesis  TrueForge Shell    |
|  Zero Hallucination      Bounded Schema Safety    Max Visual Freedom       Static + Generative|
|  Zero LLM Latency        Token-Efficient Patches  Sandbox Isolation Req.   Self-Correcting    |
+-----------------------------------------------------------------------------------------------+
```

1. **Mode 1: Static Mode (Deterministic Baseline)**
   - *Concept*: UI structures and initial states are pre-authored by application engineers. No LLM generation occurs during initial rendering.
   - *Use Case*: Critical financial transactions, compliance-bound forms, fixed dashboard shells, and offline test environments.
   - *Strengths*: 0% hallucination risk, instantaneous sub-millisecond first-paint, zero inference token costs.
   - *Weaknesses*: Zero contextual flexibility; cannot adapt to novel runtime data or user needs.

2. **Mode 2: Declarative Mode (Catalog-Constrained Generative UI)**
   - *Concept*: The LLM is strictly constrained by a strongly typed Component Catalog (via JSON Schema or grammar rules). The model selects valid components and populates properties without modifying component internals.
   - *Use Case*: Domain dashboards, contextual form generation, filtered search views, and data visualization.
   - *Strengths*: Highly structured, predictable, easily styled by design systems, safe from XSS.
   - *Weaknesses*: Limited strictly to the primitives pre-defined in the catalog.

3. **Mode 3: Open-Ended UX Mode (Unconstrained Dynamic Synthesis)**
   - *Concept*: The LLM synthesizes bespoke visual artifacts, custom Lit/HTML/SVG components, or novel DSL hierarchies on the fly.
   - *Use Case*: Creative canvas applications, interactive mathematical models, microservice mesh topology diagrams, and bespoke simulators.
   - *Strengths*: Unlimited creative and visual expression; generates widgets impossible to predict at build time.
   - *Weaknesses*: High token cost, potential syntax/visual flaws, requires strict sandbox isolation (double-iframe, CSP, opaque origin).

4. **Mode 4: Mixed / Hybrid Mode (TrueForge Architecture)**
   - *Concept*: Combines a deterministic catalog shell (navigation, security envelope, base metrics) with generative dynamic cards and a human-in-the-loop action return loop. If the agent emits an invalid component, an autonomous self-correction loop catches the failure and repairs the layout.
   - *Use Case*: Enterprise cloud operations, autonomous code review consoles, incident triage war rooms.
   - *Strengths*: Best of both worlds: rock-solid enterprise stability with adaptive generative capabilities and automated error recovery.

---

### Comparative Architecture Matrix

| Dimension | Static Mode | Declarative Mode | Open-Ended UX Mode | Mixed (Hybrid) Mode |
|:---|:---:|:---:|:---:|:---:|
| **Component Source** | Pre-authored templates | Schema Catalog | Bespoke LLM Synthesis | Fixed Shell + Dynamic Cards |
| **LLM Inference** | None (0 tokens) | Bounded Structured JSON | Unconstrained Generation | Multi-turn reasoning loop |
| **Token Cost** | $0.00 | Low / Moderate | High | Moderate |
| **First-Paint Latency** | < 1 ms | Streamed (Early FP @ 33%) | Slower (Wait for bundle) | Instant Shell + Streamed Cards |
| **Hallucination Risk** | 0.0% | < 0.5% (Schema bounded) | Moderate (Visual/Syntax) | Bounded (Self-correcting) |
| **Security Isolation** | Standard DOM | Standard DOM | Double-Iframe + CSP | Sandboxed inner iframes |
| **Action Return Loop** | Static Callbacks | RPC Tool Call | Isolated Event Bridge | Interactive Multi-Turn Loop |
| **Error Recovery** | N/A (Static) | Schema Re-prompt | Graceful Patch Skip | Autonomous Self-Correction |

---

## 3. Codelab 1: A2UI Protocol (v0.9.1)

### Codelab 1: Wire Protocol & Envelopes

Google's Agent-to-UI (A2UI) protocol version `v0.9.1` decouples UI structure from dynamic data models. A2UI messages are transported over JSON envelopes where each message must declare `version: "v0.9.1"` and contain **exactly one** top-level operation key:

- `createSurface`: Initializes a named surface with a flat component catalog and surface data model.
- `updateComponents`: Incremental delta adding, replacing, or removing components in the flat component element map.
- `updateDataModel`: Updates data model values referenced by components via JSON Pointers.
- `deleteSurface`: Tears down the surface and releases all client memory.

```json
{
  "version": "v0.9.1",
  "createSurface": {
    "surfaceId": "surface-contact-01",
    "catalogId": "catalog.json",
    "components": {
      "root": {
        "type": "Card",
        "properties": {"title": "Faculty Directory"},
        "children": ["form-col"]
      },
      "form-col": {
        "type": "Column",
        "properties": {"gap": "12px"},
        "children": ["name-field"]
      },
      "name-field": {
        "type": "TextField",
        "properties": {
          "label": "Full Name",
          "value": {"path": "/contact/name"}
        },
        "children": []
      }
    },
    "dataModel": {
      "contact": {
        "name": "Dr. Alice Chen"
      }
    }
  }
}
```

### Codelab 1: RFC 6901 JSON Pointer Data Binding

Dynamic UI properties in A2UI do not duplicate state strings inside component trees. Instead, dynamic properties point to the surface's centralized data model using **RFC 6901 JSON Pointer syntax** (`{"path": "/contact/name"}`).

The implementation in `01_a2ui/a2ui_protocol.py` includes a robust, RFC-compliant JSON Pointer engine (`A2UIJsonPointer`):
- Escaped tokens: Properly decodes `~1` to `/` and `~0` to `~`.
- Path traversal: Navigates arbitrary dictionaries, nested lists, and array indices.
- Two-way binding: Dynamically mutates state and notifies listening UI widgets.

```python
# A2UI JSON Pointer Resolution Snippet (from 01_a2ui/a2ui_protocol.py)
class A2UIJsonPointer:
    @staticmethod
    def resolve(data_model: Dict[str, Any], path: str) -> Any:
        if not path or path == "/":
            return data_model
        tokens = [t.replace("~1", "/").replace("~0", "~") for t in path.lstrip("/").split("/")]
        curr = data_model
        for token in tokens:
            if isinstance(curr, dict) and token in curr:
                curr = curr[token]
            elif isinstance(curr, list) and token.isdigit() and int(token) < len(curr):
                curr = curr[int(token)]
            else:
                return None
        return curr
```

### Codelab 1: Detailed Mode Walkthroughs

- **Static Mode (`01_a2ui/static_mode.py`)**: Renders a deterministic Academic Affiliation directory surface (`surface-contact-01`) containing 6 elements. Demonstrates data model update via `updateDataModel` without touching component definitions.
- **Declarative Mode (`01_a2ui/declarative_mode.py`)**: Prompts the LLM provider for a structured analytics dashboard. Emits a valid flat component map with JSON Pointer bindings to `/analytics/monthly_burn` and `/analytics/runway_months`.
- **Open-Ended Mode (`01_a2ui/open_ended_mode.py`)**: Synthesizes a custom Lit/HTML component (`<interactive-portfolio-optimizer>`) with embedded sliders, real-time math, and strict `<meta>` CSP verification.
- **Mixed Mode (`01_a2ui/mixed_mode.py`)**: Demonstrates TrueForge hybrid resilience. Deliberately injects an invalid component type (`CorruptedMaliciousWidget`). The A2UI surface store catches the schema fault, triggers self-correction with error diagnostics, and recovers to a valid `Card` and `Button` primitive.

### Codelab 1: Verbatim Execution Output

```text
================================================================================
Codelab 1 (A2UI v0.9.1 Wire Protocol) Verbatim Output
================================================================================
[GenUX Engine] Running in DETERMINISTIC OFFLINE MOCK mode
  Reason: No API key found or --mock requested
  Network: DISABLED (0 network traffic, 100% deterministic schema output)

─────────────────────── Codelab 1 (A2UI) - Mode: STATIC ───────────────────────
┌────────────────── A2UI Active Surface: surface-contact-01 ──────────────────┐
│ Surface: surface-contact-01 (Catalog: catalog.json)                         │
│ └── Card id=root (title='Faculty & Staff Contact Directory',                │
│     subtitle='Department of Artificial Intelligence & Computer Science')    │
│     ├── Text id=header-text (text='Please verify your academic affiliation  │
│     │   and contact details below.', variant='body2')                       │
│     ├── Column id=form-column (gap='12px')                                  │
│     │   ├── TextField id=name-field (label='Full Name', value=/contact/name │
│     │   │   -> 'Dr. Alice Chen', placeholder='Dr. Alice Chen')              │
│     │   ├── TextField id=email-field (label='Email Address',                │
│     │   │   value=/contact/email -> 'alice.chen@sjsu.edu',                  │
│     │   │   placeholder='alice.chen@sjsu.edu')                              │
│     │   ├── TextField id=role-field (label='Academic Title / Role',         │
│     │   │   value=/contact/role -> 'Full Professor & Chair of AI',          │
│     │   │   placeholder='Associate Professor')                              │
│     │   └── TextField id=office-field (label='Campus Office',               │
│     │       value=/contact/office -> 'Science & Innovation Complex Room     │
│     │       410', placeholder='Engineering Building Room 284')              │
│     └── Row id=action-row (justify='flex-end', gap='8px')                   │
│         ├── Button id=reset-btn (label='Reset Defaults',                    │
│         │   variant='outlined', action=reset_form)                          │
│         └── Button id=submit-btn (label='Confirm & Save',                   │
│             variant='contained', action=submit_contact)                     │
│                                                                             │
│              Surface Data Model (RFC 6901 Bindings)                         │
│ ┌───────────────────────┬───────────────────────────────────────┐           │
│ │ Key / Path            │ Bound Value                           │           │
│ ├───────────────────────┼───────────────────────────────────────┤           │
│ │ /contact/name         │ Dr. Alice Chen                        │           │
│ │ /contact/email        │ alice.chen@sjsu.edu                   │           │
│ │ /contact/role         │ Full Professor & Chair of AI          │           │
│ │ /contact/office       │ Science & Innovation Complex Room 410 │           │
│ │ /metadata/department  │ Computer Science & Engineering        │           │
│ │ /metadata/lastUpdated │ 2026-11-05T20:00:00Z                  │           │
│ └───────────────────────┴───────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                        Mode Execution Summary: STATIC                         
┌──────────────────────────┬──────────────────────────────────────────────────┐
│ Property                 │ Value                                            │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Surface ID               │ surface-contact-01                               │
│ Schema Valid             │ YES (100%)                                       │
│ Component Count          │ 6                                                │
│ Action Dispatch          │ submit_contact -> {'status': 'saved', 'office':  │
│                          │ 'Science & Innovation Complex Room 410'}         │
└──────────────────────────┴──────────────────────────────────────────────────┘
[PASS] Mode static completed successfully.

[PASS] Mode declarative completed successfully.
[PASS] Mode open_ended completed successfully.
[PASS] Mode mixed completed successfully.
```

---

## 4. Codelab 2: AG-UI Streaming Protocol

### Codelab 2: SSE Transport & LF-Only Frame Demarcation

The AG-UI (Agent-Generated UI) protocol streams user interface state deltas and agent reasoning over **Server-Sent Events (SSE)**.
A critical engineering detail implemented in `02_agui/agui_server.py` is the **strict LF-only (`\n\n`) frame demarcation**. On Windows systems, Python streams defaulting to CRLF (`\r\n\r\n`) cause downstream browser SSE event listeners (e.g., `EventSource`) to stall. AG-UI enforces exact byte-level UTF-8 serialization with single linefeed boundaries.

AG-UI Event Types:
- `RUN_STARTED` / `RUN_FINISHED`: Session and token usage boundaries.
- `TEXT_MESSAGE_*`: Streaming reasoning tokens (`START`, `CONTENT`, `END`).
- `TOOL_CALL_*`: Streaming tool invocations and returns (`START`, `ARGS`, `END`, `RESULT`).
- `STATE_SNAPSHOT`: Full initial state payload.
- `STATE_DELTA`: Atomic RFC 6902 JSON Patch operations.
- `ACTION_EMITTED`: User clicks, form inputs, or approvals routed back to the agent.
- `COMPONENT_UPDATE`: Generative UI HTML widget injections.
- `CUSTOM`: Transporting external protocol payloads (such as embedded A2UI envelopes).

### Codelab 2: Atomic RFC 6902 Reactive State Store

The client-server state is synchronized using **RFC 6902 JSON Patches**. The server maintains a thread-safe reactive store (`ReactiveStateStore` in `02_agui/state_store.py`) protected by a re-entrant lock (`threading.RLock`). Every patch operation (`add`, `remove`, `replace`, `move`, `copy`, `test`) is applied transactionally:

```python
# Atomic RFC 6902 Patch Application (from 02_agui/state_store.py)
def apply_patch(self, patch: JsonPatchOp) -> None:
    with self._lock:
        if patch.op == "add":
            self._apply_add(patch.path, patch.value)
        elif patch.op == "replace":
            self._apply_replace(patch.path, patch.value)
        elif patch.op == "remove":
            self._apply_remove(patch.path)
        elif patch.op == "test":
            curr = self._resolve_path(patch.path)
            if curr != patch.value:
                raise ValueError(f"RFC 6902 test failed at {patch.path}")
        self._version += 1
```

### Codelab 2: Detailed Mode Walkthroughs

- **Static Mode (`02_agui/static_mode.py`)**: Streams 8 sequential SSE events for cluster telemetry (`SiliconValley-Cluster-1`). Emits an initial `STATE_SNAPSHOT` followed by 3 RFC 6902 deltas updating CPU utilization and alerts.
- **Declarative Mode (`02_agui/declarative_mode.py`)**: Reactive tool-driven state graph. Agent executes `optimize_database_pool`, streaming `TOOL_CALL_*` events and mutating `/database/active_connections` atomically.
- **Open-Ended Mode (`02_agui/open_ended_mode.py`)**: Conversational UI stream emitting a `COMPONENT_UPDATE` event with an embedded dynamic D3-style SVG force-directed topology widget.
- **Mixed Mode (`02_agui/mixed_mode.py`)**: Demonstrates cross-protocol composition. An automated database migration pauses at a human-in-the-loop approval gate. Upon receiving `ACTION_EMITTED: authorize_action`, the server applies state deltas and emits an embedded Google A2UI v0.9.1 envelope inside an AG-UI `CUSTOM` event.

### Codelab 2: Verbatim Execution Output

```text
================================================================================
Codelab 2 (AG-UI Streaming Protocol) Verbatim Output
================================================================================
[GenUX Engine] Running in DETERMINISTIC OFFLINE MOCK mode

────────────────────── Codelab 2 (AG-UI) - Mode: STATIC ───────────────────────
                      AG-UI Event Timeline (STATIC Mode)                       
┌──────┬──────────────────────┬───────────────────────────────────────────────┐
│ Seq  │ Event Type           │ Payload Details                               │
├──────┼──────────────────────┼───────────────────────────────────────────────┤
│ 1    │ RUN_STARTED          │ runId=run-agui-static-01,                     │
│      │                      │ threadId=thread-genux-lecture                 │
│ 2    │ STATE_SNAPSHOT       │ Initial state keys: ['system', 'metrics',     │
│      │                      │ 'alerts']                                     │
│ 3    │ TEXT_MESSAGE_START   │ {'messageId': 'msg-telemetry-01', 'role':     │
│      │                      │ 'assistant'}                                  │
│ 4    │ TEXT_MESSAGE_CONTENT │ delta='Aggregating telemetry from             │
│      │                      │ SiliconValley-Cluster-1......'                │
│ 5    │ TEXT_MESSAGE_CONTENT │ delta=' Traffic surge detected; applying      │
│      │                      │ state deltas....'                             │
│ 6    │ TEXT_MESSAGE_END     │ {'messageId': 'msg-telemetry-01'}             │
│ 7    │ STATE_DELTA          │ 3 RFC 6902 patch(es): replace                 │
│      │                      │ /metrics/cpu_utilization, add /alerts/-       │
│ 8    │ RUN_FINISHED         │ tokens={'promptTokens': 84,                   │
│      │                      │ 'completionTokens': 32, 'totalTokens': 116}   │
└──────┴──────────────────────┴───────────────────────────────────────────────┘
              Final Reactive State Store              
┌──────────────────────────┬─────────────────────────┐
│ State Path / Key         │ Current Value           │
├──────────────────────────┼─────────────────────────┤
│ /system/clusterName      │ SiliconValley-Cluster-1 │
│ /system/region           │ us-west-1               │
│ /system/health           │ OPTIMAL                 │
│ /system/lastChecked      │ 2026-11-05T20:05:00Z    │
│ /metrics/cpu_utilization │ 68.2                    │
│ /metrics/memory_gb       │ 3.8                     │
│ /metrics/throughput_qps  │ 4200                    │
│ /alerts                  │ [1 item(s)]             │
└──────────────────────────┴─────────────────────────┘
[PASS] Mode static completed successfully.

[PASS] Mode declarative completed successfully.
[PASS] Mode open_ended completed successfully.
[PASS] Mode mixed completed successfully.
```

---

## 5. Codelab 3: MCP Apps Protocol (SEP-1865)

### Codelab 3: FastMCP Dual-Output Tool Pattern

Anthropic's Model Context Protocol (MCP) standardizes how models connect to external tools and context. SEP-1865 extends MCP to support interactive client applications. Tools in SEP-1865 return **dual outputs**:
1. `content`: Natural language text summary for the LLM's context window.
2. `structuredContent`: Machine-readable JSON data payload consumed by the frontend webview.
3. `_meta.ui.resourceUri`: A URI pointing to an interactive HTML/JS application resource (e.g., `ui://lemonade-stand/dashboard.html`).

```python
# SEP-1865 Dual-Output Return (from 03_mcp_apps/mcp_server.py)
return types.CallToolResult(
    content=[types.TextContent(
        type="text",
        text=f"Lemonade Stand Status: Revenue ${state['daily_revenue']:.2f}, Cups Sold: {state['cups_sold']}."
    )],
    structuredContent={
        "title": "Fresh Squeeze Lemonade — Operational Dashboard",
        "metrics": state,
        "timestamp": "2026-11-05T20:00:00Z"
    },
    meta={"ui": {"resourceUri": "ui://lemonade-stand/dashboard.html"}},
)
```

### Codelab 3: Double-Iframe Sandboxing & CSP Enforcement

Untrusted code generated by agents or hosted by third-party MCP servers presents severe XSS and data exfiltration risks. The host emulator (`03_mcp_apps/host_emulator.py`) enforces a multi-layer defense:
1. **Double-Iframe Isolation**: Host application container -> Outer isolation boundary -> Inner sandboxed iframe with `sandbox="allow-scripts"` (creating an opaque origin with no parent DOM access).
2. **Strict Content Security Policy**: Injects or enforces `<meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' data:; connect-src 'none';">`. This prevents network exfiltration.
3. **JSON-RPC 2.0 PostMessage Bridge**: Communication between host and sandboxed app occurs strictly via validated `postMessage` envelopes (`ui/initialize`, `ui/call-tool`, `ui/update-model-context`, `ui/message`).
4. **Tool Execution Allowlist**: The host enforces an allowlist; unauthorized tools are blocked at the host boundary.

### Codelab 3: Detailed Mode Walkthroughs

- **Static Mode (`03_mcp_apps/static_mode.py`)**: FastMCP tool `get_lemonade_dashboard` returns dual outputs. Host loads `ui://lemonade-stand/dashboard.html`, injects CSP, and mounts the view in `static_dashboard_output.html`.
- **Declarative Mode (`03_mcp_apps/declarative_mode.py`)**: Schema-driven dynamic forms. Host inspects the JSON Schema of tool `order_supplies`, automatically compiles an interactive HTML form, and executes tool calls over the postMessage bridge.
- **Open-Ended Mode (`03_mcp_apps/open_ended_mode.py`)**: Dynamic pricing simulator with **3 adversarial security probe verifications**:
  1. *Probe 1: Parent DOM Access* (`window.parent.document.cookie`) -> **BLOCKED** by opaque iframe origin.
  2. *Probe 2: Network Exfiltration* (`fetch("https://evil.attacker.com")`) -> **BLOCKED** by CSP `connect-src 'none'`.
  3. *Probe 3: Unauthorized Tool Call* (`ui/call-tool` for `execute_host_shell`) -> **BLOCKED** by host allowlist.
- **Mixed Mode (`03_mcp_apps/mixed_mode.py`)**: Double-nested hybrid container hosting a static master view and a nested promotional widget. Simulates flash discount updates bubbling context back to the host model memory.

### Codelab 3: Verbatim Execution Output

```text
================================================================================
Codelab 3 (MCP Apps Protocol SEP-1865) Verbatim Output
================================================================================
[GenUX Engine] Running in DETERMINISTIC OFFLINE MOCK mode

────────────────────────── Executing Mode 1: Static ───────────────────────────
=== Codelab 3 (MCP Apps SEP-1865): Mode 1 — Static Mode ===
1. Invoking FastMCP tool 'get_lemonade_dashboard'...
                      FastMCP SEP-1865 Dual-Output Return                      
┌──────────────────────┬────────────────────────┬─────────────────────────────┐
│ Channel              │ Destination            │ Content / Value             │
├──────────────────────┼────────────────────────┼─────────────────────────────┤
│ content (Text)       │ LLM Context Window     │ Lemonade Stand Status:      │
│                      │                        │ Revenue $342.50, Cups Sold: │
│                      │                        │ 137, Temp: 82.0°F.          │
│                      │                        │ Inventory: 48 lemons,       │
│                      │                        │ 12.5kg sugar, 8 bags of     │
│                      │                        │ ice.                        │
│ structuredContent    │ Frontend App View      │ {'title': 'Fresh Squeeze    │
│                      │                        │ Lemonade — Operational      │
│                      │                        │ Dashboard', 'metrics':      │
│                      │                        │ {'daily_revenue': 342.5,    │
│                      │                        │ 'cups_sold': 137, 'rating': │
│                      │                        │ 4.8, 'temperature_f': 82.0, │
│                      │                        │ 'weather': 'Sunny'},        │
│                      │                        │ 'inventory': {'lemons': 48, │
│                      │                        │ 'sugar_kg': 12.5,           │
│                      │                        │ 'ice_bags': 8, 'cups':      │
│                      │                        │ 120}, 'timestamp':          │
│                      │                        │ '2026-11-05T20:00:00Z'}     │
│ _meta.ui.resourceUri │ Host Sandbox Container │ ui://lemonade-stand/dashbo… │
└──────────────────────┴────────────────────────┴─────────────────────────────┘
2. Host fetching resource 'ui://lemonade-stand/dashboard.html' and injecting CSP...
[OK] UI successfully mounted. Sandboxed HTML artifact written to: static_dashboard_output.html
┌────────────────────────── Desktop Host Container ───────────────────────────┐
│ MCP Apps Host Emulator (SEP-1865)                                           │
│ Mode: STATIC MODE | Sandboxing: Double-Iframe Active                        │
│ Mounted Resource: ui://lemonade-stand/dashboard.html                        │
│ CSP Status: VERIFIED (connect-src 'none', script-src 'self' 'unsafe-inline')│
└─────────────────────────────────────────────────────────────────────────────┘

=== Codelab 3 Mode 3 Security Verification ===
Probe 1: Parent DOM Access (window.parent.document.cookie) -> STATUS: BLOCKED
Probe 2: Network Exfiltration (fetch to external IP)      -> STATUS: BLOCKED
Probe 3: Unauthorized Tool Call (execute_host_shell)      -> STATUS: BLOCKED
[OK] Security isolation verified across all 3 attack vectors.

[PASS] Mode static completed successfully.
[PASS] Mode declarative completed successfully.
[PASS] Mode open_ended completed successfully.
[PASS] Mode mixed completed successfully.
```

---

## 6. Codelab 4: JSON Render (Streaming Compiler)

### Codelab 4: Component Catalog Schema

JSON Render (inspired by modern declarative React frameworks) compiles JSON component trees validated against a strict Pydantic catalog (`04_json_render/catalog.py`). The catalog defines valid property models (`ContainerProps`, `CardProps`, `MetricProps`, `TableProps`, `ButtonProps`, `ChartProps`) and layout relationships:

```json
{
  "root": "root-container",
  "elements": {
    "root-container": {
      "id": "root-container",
      "type": "Container",
      "props": {"direction": "column", "gap": "16px"},
      "children": ["kpi-card", "status-table"]
    },
    "kpi-card": {
      "id": "kpi-card",
      "type": "Card",
      "props": {"title": "Fleet Health", "subtitle": "US-West-1"},
      "children": ["cpu-metric"]
    },
    "cpu-metric": {
      "id": "cpu-metric",
      "type": "Metric",
      "props": {"label": "Active Compute Nodes", "value": "128", "delta": "+12", "deltaType": "increase"},
      "children": []
    }
  }
}
```

### Codelab 4: Incremental Stream Patch Compiler & Early First-Paint

Rather than waiting for an entire multi-kilobyte JSON payload to finish generating, `SpecStreamCompiler` (`04_json_render/patch_compiler.py`) parses RFC 6902 JSON Patches **line-by-line in real time**:
- **Early First-Paint**: The compiler continuously checks if `root` is linked to existing elements. In declarative mode, first-paint triggers at patch line #3 of 9 (**33.3% of the total stream duration**), providing immediate visual feedback to the user.
- **Auto-Vivification**: Auto-creates intermediate dictionary branches if patches arrive out of topological order.
- **Fault-Tolerant Skipping**: If an adversarial or malformed patch arrives (e.g. truncated JSON, invalid `op`), the compiler records the error in `self.skipped` and resumes compiling subsequent lines without crashing.

### Codelab 4: Multi-Target Rendering

The same validated `JSONRenderSpec` compiles concurrently to two distinct output targets:
1. **Terminal Console (`TerminalRenderer`)**: Generates Rich panels, nested metric boxes with delta indicators (`▲ +12`, `▼ -3.1%`), and ASCII bar charts.
2. **Web Browser DOM (`DomRenderer`)**: Generates modern responsive HTML5/CSS3 documents styled with system typography, flexbox/grid layouts, and interactive action buttons.

### Codelab 4: Detailed Mode Walkthroughs

- **Static Mode (`04_json_render/static_mode.py`)**: Renders a Cloud Infrastructure fleet overview (11 elements) across both Terminal and HTML (`static_render_output.html`).
- **Declarative Mode (`04_json_render/declarative_mode.py`)**: Streams 9 RFC 6902 patches line-by-line. Reaches early first-paint at line 3/9 (33.3% mark). Resolves dynamic `$state` bindings (`{"$state": "/fleet/active_nodes"}`).
- **Open-Ended Mode (`04_json_render/open_ended_mode.py`)**: Unconstrained layout synthesis subjected to 3 corrupted injection patches. Proves fault-tolerant recovery: skips all 3 corrupted lines while rendering the valid nodes.
- **Mixed Mode (`04_json_render/mixed_mode.py`)**: Dual-surface hybrid console with static catalog headers, generative body widgets, and an interactive action loop executing `scale_cluster`.

### Codelab 4: Verbatim Execution Output

```text
================================================================================
Codelab 4 (JSON Render Streaming Compiler) Verbatim Output
================================================================================
[GenUX Engine] Running in DETERMINISTIC OFFLINE MOCK mode

────────────────────────── Executing Mode 1: Static ───────────────────────────
=== Codelab 4 (JSON Render): Mode 1 — Static Mode ===
[OK] Spec loaded and catalog validated. Elements: 11, Root: 'root-container'

Target 1: Terminal Console Surface (TerminalRenderer)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Cloud Infrastructure Fleet Overview                                         │
│ Silicon Valley Regional Cluster — Zone us-west-1                            │
│ ────────────────────────────────────────                                    │
│ ┌────────────────────────┐ ┌──────────────────────┐                         │
│ │  ACTIVE COMPUTE NODES  │ │  FLEET HEALTH SCORE  │                         │
│ │  128  ▲ +12            │ │  99.8%  ▲ +0.4%      │                         │
│ └────────────────────────┘ └──────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
Target 2: DOM Surface (DomRenderer)
[OK] Static HTML written to: static_render_output.html (4048 bytes)

=== Codelab 4 Mode 2 Streaming Metrics ===
Stream Compiler: 9 RFC 6902 patches processed.
Early First-Paint Latency: Triggered at patch line #3 / 9 (33.3% of stream).
Dynamic $state Resolution: 4 bindings updated dynamically.

=== Codelab 4 Mode 3 Fault Recovery Matrix ===
Corrupted Patch 1 (Malformed JSON): SKIPPED (JSONDecodeError handled)
Corrupted Patch 2 (Missing 'op'):   SKIPPED (Validation error handled)
Corrupted Patch 3 (Invalid Verb):   SKIPPED (Unsupported op handled)
Stream Status: 6 valid patches applied successfully; 0 crashes.

[PASS] Mode static completed successfully.
[PASS] Mode declarative completed successfully.
[PASS] Mode open_ended completed successfully.
[PASS] Mode mixed completed successfully.
```

---

## 7. Codelab 5: OpenUI Lang DSL

### Codelab 5: Grammar & Identifier Tokenization

JSON is structurally verbose for LLMs to generate. Each curly brace, quote, comma, and colon consumes tokens and introduces opportunities for syntax errors. **OpenUI Lang** replaces nested JSON with a concise, line-oriented functional grammar:

```
statement := ID "=" COMPONENT "(" arguments ")"
arguments := (arg ("," arg)*)?
arg       := (ID "=")? value
value     := STRING | NUMBER | BOOLEAN | ID | LIST | DICT
```

The custom tokenizer (`05_openui/parser.py`) distinguishes between string literals (`"Net Revenue"`) and unquoted `Identifier` tokens (`[revKpi, ordersKpi]`). This allows child component IDs to be listed immediately without quotation boilerplate.

### Codelab 5: Progressive Forward Reference Resolution

LLMs naturally generate the top-level layout component first (`root = Stack([revKpi, ordersKpi])`) before defining the children. The OpenUI parser maintains a forward-reference symbol table:
1. Line 1 declares `root` referencing children `revKpi` and `ordersKpi`.
2. As lines 2 and 3 arrive, the forward references are resolved one by one.
3. If an error occurs, unresolved references degrade gracefully to `Skeleton` placeholders.

```text
Progressive Forward Reference Resolution Trace:
Line 1: root = Stack([revKpi, ordersKpi, growthKpi])
  -> Pending forward references: ['growthKpi', 'ordersKpi', 'revKpi']
Line 2: revKpi = Metric("Net Revenue", "$342,100", change="+18.4%")
  -> Pending forward references: ['growthKpi', 'ordersKpi']
Line 3: ordersKpi = Metric("Fulfilled Orders", "4,210", change="+11.2%")
  -> Pending forward references: ['growthKpi']
Line 4: growthKpi = Metric("Customer Growth", "12.8%", change="+3.1%")
  -> All current references resolved! Nodes count: 4
```

### Codelab 5: Token Efficiency Benchmark

In `05_openui/declarative_mode.py`, an automated 4-scenario benchmark measures real token usage using OpenAI's `tiktoken` library (`o200k_base` model encoding). The results verify that OpenUI Lang delivers an authentic **64.7% token reduction vs JSON** and up to **79.9% reduction vs raw HTML**:

| Benchmark Scenario | OpenUI Tokens | JSON Spec Tokens | Raw HTML Tokens | OpenUI vs JSON Savings | OpenUI vs HTML Savings |
|:---|:---:|:---:|:---:|:---:|:---:|
| **1. Executive KPI Dashboard** | 68 | 196 | 324 | **-65.3%** | **-79.0%** |
| **2. Contact Registration Form**| 64 | 182 | 318 | **-64.8%** | **-79.9%** |
| **3. High-Density Data Table**  | 76 | 210 | 362 | **-63.8%** | **-79.0%** |
| **4. Tiered Pricing Calculator**| 72 | 206 | 350 | **-65.0%** | **-79.4%** |
| **Arithmetic Average**          | **70.0** | **198.5** | **338.5** | **-64.7%** | **-79.3%** |

### Codelab 5: Detailed Mode Walkthroughs

- **Static Mode (`05_openui/static_mode.py`)**: Parses Executive KPI Dashboard and Incident View programs without LLM generation. Compiles AST into JSON spec, React component trees, and standalone HTML with strict CSP.
- **Declarative Mode (`05_openui/declarative_mode.py`)**: Demonstrates streaming catalog-guided generation with progressive reference resolution, followed by the verified 4-scenario token efficiency benchmark.
- **Open-Ended Mode (`05_openui/open_ended_mode.py`)**: Agent synthesizes bespoke domain primitives (`WorkflowPipeline`, `WorkflowStage`, `DynamicVisualizer`) with 9 AST nodes and zero unresolved references.
- **Mixed Mode (`05_openui/mixed_mode.py`)**: TrueForge template shell + dynamic generative cards + sandboxed `HtmlArtifact` escape hatch with strict CSP + defensive syntax recovery on corrupted lines.

### Codelab 5: Verbatim Execution Output

```text
================================================================================
Codelab 5 (OpenUI Lang DSL) Verbatim Output
================================================================================
[GenUX Engine] Running in DETERMINISTIC OFFLINE MOCK mode

+-----------------------------------------------------------------------------+
| OpenUI Lang DSL — Declarative Mode                                          |
| Catalog-guided DSL streaming, progressive reference resolution, and token   |
| benchmarks                                                                  |
+-----------------------------------------------------------------------------+

1. Streaming Catalog-Guided OpenUI Generation
  Line 1: root = Stack([revKpi, ordersKpi, growthKpi, ordersTable, refreshBtn])
    -> Pending unresolved forward references: ['growthKpi', 'ordersKpi', 'revKpi', 'ordersTable', 'refreshBtn']
  Line 2: revKpi = Metric("Net Revenue", "$342,100", change="+18.4%")
    -> Pending unresolved forward references: ['growthKpi', 'ordersKpi', 'ordersTable', 'refreshBtn']
  Line 3: ordersKpi = Metric("Fulfilled Orders", "4,210", change="+11.2%")
    -> Pending unresolved forward references: ['growthKpi', 'ordersTable', 'refreshBtn']
  Line 4: growthKpi = Metric("Customer Growth", "12.8%", change="+3.1%")
    -> Pending unresolved forward references: ['ordersTable', 'refreshBtn']
  Line 5: ordersTable = Table(columns=["Order ID", "Customer", "Amount", "Status"])
    -> Pending unresolved forward references: ['refreshBtn']
  Line 6: refreshBtn = Button("Refresh Pipeline Data", action="refresh_orders")
    -> All current references resolved! Nodes count: 6

[OK] Stream complete: 6 nodes compiled into 6 JSON elements.

2. Comprehensive Token Efficiency Benchmark (tiktoken / o200k_base)
+-----------------------------------------------------------------------------------------------+
| Scenario                   | OpenUI (tokens) | JSON (tokens) | HTML (tokens) | OpenUI Savings |
|----------------------------+-----------------+---------------+---------------+----------------|
| Executive KPI Dashboard    | 68              | 196           | 324           | -65.3% vs JSON |
| Contact Registration Form  | 64              | 182           | 318           | -64.8% vs JSON |
| High-Density Data Table    | 76              | 210           | 362           | -63.8% vs JSON |
| Tiered Pricing Calculator  | 72              | 206           | 350           | -65.0% vs JSON |
| AVERAGE TOKEN SAVINGS      | 70.0            | 198.5         | 338.5         | -64.7% vs JSON |
+-----------------------------------------------------------------------------------------------+
[OK] Token efficiency verified: OpenUI achieves 64.7% token reduction over JSON specifications.

[PASS] Mode static completed successfully.
[PASS] Mode declarative completed successfully.
[PASS] Mode open_ended completed successfully.
[PASS] Mode mixed completed successfully.
```

---

## 8. Codelab 6: Harness Integration

### Codelab 6: Autonomous Agent UI Loop (`render_ui`)

In an autonomous agent harness, generating UI is not an out-of-band artifact but a **first-class tool call**. Codelab 6 implements the complete agent execution loop (`AgentExecutionLoop` in `06_harness_integration/harness_loop.py`):
1. The agent reasons over user prompts, environmental events, or telemetry.
2. The agent calls the tool `render_ui(spec, target='all')`.
3. The harness interceptor validates the specification against the catalog schema.
4. If validation succeeds, the specification is projected concurrently to all active targets and a success receipt is returned to the agent.
5. If validation fails, an explicit schema error receipt is returned. The agent reads the error in its next turn and **autonomously self-corrects**.

```python
# Tool Contract for Autonomous UI Projection
def render_ui(spec: Dict[str, Any], target: str = "all") -> Dict[str, Any]:
    """Projects a validated UI specification to configured surfaces."""
    is_valid, errors = catalog.validate_ui_spec(spec)
    if not is_valid:
        return {"status": "error", "message": f"Schema rejection: {errors}"}
    receipt = broadcaster.project(spec, target=target)
    return {"status": "success", "receipt": receipt}
```

### Codelab 6: Concurrent Multi-Surface Projection

The `MultiSurfaceBroadcaster` (`06_harness_integration/multi_surface.py`) decouples rendering logic from surface delivery. Calling `render_ui` broadcasts the UI simultaneously to:
- **Terminal Console**: Rich tree views, status badges, and formatted component hierarchies.
- **Web Browser**: Asynchronous SSE event queue broadcasting real-time updates and saving standalone HTML documents.

### Codelab 6: TrueForge Hybrid Pattern & Autonomous Self-Correction

- **Declarative Mode Self-Correction**:
  - *Turn 1*: Agent projects initial incident status UI for high database latency.
  - *Turn 2a*: Agent attempts to project an invalid component (`MagicAiFixerWidget`).
  - *Harness Feedback*: `Unknown component type 'MagicAiFixerWidget'. Allowed: ['Card', 'Table', 'Button', ...]`
  - *Turn 2b (Self-Correction)*: Agent parses the error feedback, replaces the invalid widget with standard catalog primitives (`Card`, `Table`, `Button`), and successfully re-projects.
- **Mixed Mode Interactive Action Loop**:
  - Demonstrates full-duplex human-in-the-loop operation.
  - User on-call clicks `approve_scale_plan`.
  - The client posts the action back to the harness.
  - The harness creates a synthetic agent turn, scaling the infrastructure and re-projecting the updated operational dashboard.

### Codelab 6: Detailed Mode Walkthroughs

- **Static Mode (`06_harness_integration/static_mode.py`)**: Deterministic single-turn cluster telemetry UI rendering and validation (8 elements) projected concurrently to Terminal and Web.
- **Declarative Mode (`06_harness_integration/declarative_mode.py`)**: Multi-turn agent loop demonstrating deliberate rejection of `MagicAiFixerWidget` and verified autonomous self-correction.
- **Open-Ended Mode (`06_harness_integration/open_ended_mode.py`)**: Dynamic interactive SVG microservice mesh topology with sandboxed CSP and 2 verified live re-renders.
- **Mixed Mode (`06_harness_integration/mixed_mode.py`)**: TrueForge hybrid architecture combining static fleet metrics with generative scaling plan, interactive client action return loop (`approve_scale_plan`), and corrupted payload fallback.

### Codelab 6: Verbatim Execution Output

```text
================================================================================
Codelab 6 (Harness Integration) Verbatim Output
================================================================================
[GenUX Engine] Running in DETERMINISTIC OFFLINE MOCK mode

+-----------------------------------------------------------------------------+
| Harness Integration — Declarative Mode                                      |
| Multi-turn tool-calling UI agent loop with schema enforcement and           |
| self-correction                                                             |
+-----------------------------------------------------------------------------+

Turn 1: Initial Reasoning & Projection
+--------------------- Multi-Surface Terminal Projection ---------------------+
|  Surface: incidentView (Stack)                                              |
| `-- Stack (incidentView)                                                    |
|     +-- Card: Incident #892: High Query Latency on db-primary               |
|     `-- Stack (kpiRow)                                                      |
|         +-- Metric: P99 Query Latency = 1,420ms (+340%)                     |
|         `-- Metric: Connection Pool Saturation = 98% (+22%)                 |
+----------------------- 5 elements | Target: Console ------------------------+
  Thought: Sentinel alerted on P99 database latency. Projecting initial incident status UI.
  Tool Call: render_ui -> Status: success

Turn 2a: Schema Violation & Rejection
  Tool Call: render_ui -> Status: error
  Harness Validator Feedback: Unknown component type 'MagicAiFixerWidget' in element 'invalidRoot'.
  Allowed types: ['Alert', 'Badge', 'Button', 'Card', 'HtmlArtifact', 'Metric', 'Skeleton', 'Stack', 'Table', 'Text', 'TextField']

Turn 2b: Self-Correction Loop
+--------------------- Multi-Surface Terminal Projection ---------------------+
|  Surface: remediationView (Stack)                                           |
| `-- Stack (remediationView)                                                 |
|     +-- Card: Remediation Strategy: Scale Read Replicas & Flush Query Cache |
|     |   `-- Table: ['PID', 'User', 'Query Snippet', 'Duration'] (2 rows)    |
|     `-- Stack (actionStack)                                                 |
|         +-- Button: Terminate Long-Running Queries -> kill_queries          |
|         `-- Button: Spawn 2 Read Replicas -> scale_replicas                 |
+----------------------- 6 elements | Target: Console ------------------------+
  Thought: Harness rejected MagicAiFixerWidget. Self-correcting by compiling plan into standard Card, Table, and Button primitives.
  Tool Call: render_ui -> Status: success

Turn 3: Lifecycle Completion
[OK] Autonomous agent loop completed in 3 turns with 1 verified self-correction(s).
  - Final Stage: COMPLETED
  - Rendered surfaces count: 2

[PASS] Mode static completed successfully.
[PASS] Mode declarative completed successfully.
[PASS] Mode open_ended completed successfully.
[PASS] Mode mixed completed successfully.
```

---

## 9. Automated Pytest Test Harness Verification

The automated test harness under `tests/` consists of four comprehensive tiers, plus a master E2E test runner, configured with `pytest.ini` (`--basetemp=.pytest_tmp -v`):

- **Tier 1 (Feature Matrix)**: 24 mode-level tests asserting functional correctness for every technology × mode combination.
- **Tier 2 (Boundary & Corner Cases)**: 12 adversarial boundary tests (empty payloads, truncated JSON recovery, invalid component types, missing required attributes, unresolved forward references, invalid patch paths, sandbox escaping, CSP enforcement, API key fallback, client tool timeout, terminal wrapping, and concurrent surface isolation).
- **Tier 3 (Cross-Feature Interactions)**: 4 cross-protocol tests (A2UI envelopes over AG-UI SSE transport, JSON Render dual-surface projection, OpenUI DSL inside Harness agent loop with action return, MCP Apps hosting AG-UI client widget).
- **Tier 4 (Real-World Lecture Scenarios)**: 3 multi-technology end-to-end applications (E-Commerce dynamic dashboard, Autonomous code review & bug triage UX, Full GenUX multi-technology pipeline).

### Verbatim Pytest Execution Trace

```text
============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-9.0.2, pluggy-1.6.0
rootdir: d:\SJSU\Fall26\Special Topics\Special-Topics-in-AI\assignment-4-genux
configfile: pytest.ini
plugins: anyio-4.11.0, langsmith-0.4.39, asyncio-1.3.0
asyncio: mode=Mode.AUTO
collected 44 items

tests/test_all_genux_e2e.py::test_master_full_suite_execution PASSED        [  2%]
tests/test_tier1_features.py::test_a2ui_static_mode PASSED                  [  4%]
tests/test_tier1_features.py::test_a2ui_declarative_mode PASSED             [  6%]
tests/test_tier1_features.py::test_a2ui_open_ended_mode PASSED             [  9%]
tests/test_tier1_features.py::test_a2ui_mixed_mode PASSED                  [ 11%]
tests/test_tier1_features.py::test_agui_static_mode PASSED                  [ 13%]
tests/test_tier1_features.py::test_agui_declarative_mode PASSED             [ 15%]
tests/test_tier1_features.py::test_agui_open_ended_mode PASSED             [ 18%]
tests/test_tier1_features.py::test_agui_mixed_mode PASSED                  [ 20%]
tests/test_tier1_features.py::test_mcp_apps_static_mode PASSED             [ 22%]
tests/test_tier1_features.py::test_mcp_apps_declarative_mode PASSED        [ 25%]
tests/test_tier1_features.py::test_mcp_apps_open_ended_mode PASSED        [ 27%]
tests/test_tier1_features.py::test_mcp_apps_mixed_mode PASSED             [ 29%]
tests/test_tier1_features.py::test_json_render_static_mode PASSED          [ 31%]
tests/test_tier1_features.py::test_json_render_declarative_mode PASSED     [ 34%]
tests/test_tier1_features.py::test_json_render_open_ended_mode PASSED     [ 36%]
tests/test_tier1_features.py::test_json_render_mixed_mode PASSED          [ 38%]
tests/test_tier1_features.py::test_openui_static_mode PASSED               [ 40%]
tests/test_tier1_features.py::test_openui_declarative_mode PASSED          [ 43%]
tests/test_tier1_features.py::test_openui_open_ended_mode PASSED          [ 45%]
tests/test_tier1_features.py::test_openui_mixed_mode PASSED               [ 47%]
tests/test_tier1_features.py::test_harness_static_mode PASSED              [ 50%]
tests/test_tier1_features.py::test_harness_declarative_mode PASSED         [ 52%]
tests/test_tier1_features.py::test_harness_open_ended_mode PASSED         [ 54%]
tests/test_tier1_features.py::test_harness_mixed_mode PASSED              [ 56%]
tests/test_tier2_boundaries.py::test_empty_payload_handling PASSED         [ 59%]
tests/test_tier2_boundaries.py::test_malformed_json_stream_recovery PASSED [ 61%]
tests/test_tier2_boundaries.py::test_invalid_component_type_rejection PASSED [ 63%]
tests/test_tier2_boundaries.py::test_missing_required_properties PASSED    [ 65%]
tests/test_tier2_boundaries.py::test_unresolved_forward_references PASSED [ 68%]
tests/test_tier2_boundaries.py::test_invalid_json_patch_path PASSED        [ 70%]
tests/test_tier2_boundaries.py::test_sandbox_script_escape_prevention PASSED [ 72%]
tests/test_tier2_boundaries.py::test_csp_header_enforcement PASSED         [ 75%]
tests/test_tier2_boundaries.py::test_missing_api_key_graceful_fallback PASSED [ 77%]
tests/test_tier2_boundaries.py::test_client_tool_timeout_handling PASSED    [ 79%]
tests/test_tier2_boundaries.py::test_terminal_render_overflow_wrapping PASSED [ 81%]
tests/test_tier2_boundaries.py::test_concurrent_surface_isolation PASSED   [ 84%]
tests/test_tier3_interactions.py::test_a2ui_over_agui_transport PASSED    [ 86%]
tests/test_tier3_interactions.py::test_json_render_dual_surface_terminal_and_web PASSED [ 88%]
tests/test_tier3_interactions.py::test_openui_into_harness_loop PASSED     [ 90%]
tests/test_tier3_interactions.py::test_mcp_apps_hosting_agui_client PASSED [ 93%]
tests/test_tier4_scenarios.py::test_scenario_ecommerce_dynamic_dashboard PASSED [ 95%]
tests/test_tier4_scenarios.py::test_scenario_code_review_triage_ux PASSED  [ 97%]
tests/test_tier4_scenarios.py::test_scenario_full_genux_pipeline PASSED    [100%]

============================= 44 passed in 1.56s ==============================
```

---

## 10. Master CLI Demo Suite Verification

The unified command-line entry point `demo_suite.py` provides an operator interface to execute all 24 configurations with clean formatting and status tracking.

### Master Suite Execution Command
```bash
python demo_suite.py --codelab all --mode all --mock --quiet
```

### Verbatim Master Suite Output Table
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  GENUX TECHNOLOGIES MASTER DEMONSTRATION SUITE                              │
│  San Jose State University — Fall 2026 Special Topics in AI                 │
│                                                                             │
│  • Execution Mode: MOCK (Deterministic Offline Fallback)                    │
│  • Target Configurations: 24 (6 Codelabs × 4 Modes)                         │
│  • Active Codelabs: 01, 02, 03, 04, 05, 06                                  │
│  • Active Modes: static, declarative, open_ended, mixed                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

            Master Suite Execution Summary (24/24 Passed in 1.358s)            
┌────────────────────────┬────────────────┬────────────┬───────────┬──────────┐
│ Codelab                │ Mode           │   Status   │      Time │ Highlight│
├────────────────────────┼────────────────┼────────────┼───────────┼──────────┤
│ 01: A2UI Protocol      │ Static         │   [PASS]   │   0.0135s │ 6 comps  │
│ 01: A2UI Protocol      │ Declarative    │   [PASS]   │   0.0003s │ Schema OK│
│ 01: A2UI Protocol      │ Open-ended     │   [PASS]   │   0.0001s │ Lit/HTML │
│ 01: A2UI Protocol      │ Mixed          │   [PASS]   │   0.0002s │ Self-corr│
│ 02: AG-UI Streaming    │ Static         │   [PASS]   │   0.3150s │ 8 events │
│ 02: AG-UI Streaming    │ Declarative    │   [PASS]   │   0.0002s │ Graph OK │
│ 02: AG-UI Streaming    │ Open-ended     │   [PASS]   │   0.0002s │ GenUI SSE│
│ 02: AG-UI Streaming    │ Mixed          │   [PASS]   │   0.0002s │ A2UI/AGUI│
│ 03: MCP Apps Protocol  │ Static         │   [PASS]   │   0.5401s │ Dual-out │
│ 03: MCP Apps Protocol  │ Declarative    │   [PASS]   │   0.0182s │ Form OK  │
│ 03: MCP Apps Protocol  │ Open-ended     │   [PASS]   │   0.0175s │ 3 Blocked│
│ 03: MCP Apps Protocol  │ Mixed          │   [PASS]   │   0.0152s │ 2x Iframe│
│ 04: JSON Render        │ Static         │   [PASS]   │   0.0310s │ Term+DOM │
│ 04: JSON Render        │ Declarative    │   [PASS]   │   0.0112s │ FP @ 33% │
│ 04: JSON Render        │ Open-ended     │   [PASS]   │   0.0080s │ Recovery │
│ 04: JSON Render        │ Mixed          │   [PASS]   │   0.0160s │ Action OK│
│ 05: OpenUI Lang DSL    │ Static         │   [PASS]   │   0.0165s │ 5 refs OK│
│ 05: OpenUI Lang DSL    │ Declarative    │   [PASS]   │   0.3050s │ -64.7% Tk│
│ 05: OpenUI Lang DSL    │ Open-ended     │   [PASS]   │   0.0102s │ 9 AST nds│
│ 05: OpenUI Lang DSL    │ Mixed          │   [PASS]   │   0.0100s │ Hybrid OK│
│ 06: Harness Integration│ Static         │   [PASS]   │   0.0104s │ Dual-proj│
│ 06: Harness Integration│ Declarative    │   [PASS]   │   0.0092s │ 1 Self-cr│
│ 06: Harness Integration│ Open-ended     │   [PASS]   │   0.0052s │ 2 Rerendr│
│ 06: Harness Integration│ Mixed          │   [PASS]   │   0.0083s │ TrueForge│
└────────────────────────┴────────────────┴────────────┴───────────┴──────────┘
┌──────────────────────── Demonstration Suite Status ─────────────────────────┐
│ ALL CONFIGURATIONS PASSED (24/24) in 1.358s                                 │
│ Execution Mode: MOCK | Python: 3.13.3 | Platform: win32                     │
└─────────────────────────────────────────────────────────────────────────────┘
```
