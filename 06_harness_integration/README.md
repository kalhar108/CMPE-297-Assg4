# Codelab 06: Harness Integration

## Overview
Generative UI achieves production utility when wired directly into an autonomous agent harness. In this architecture, the UI is not merely a chat assistant's markdown attachment; it is an active **Agent Execution Tool** and **Runtime Lifecycle Surface**.

## Key Architectural Mechanics

### 1. The `render_ui` Agent Tool
The autonomous agent is equipped with a first-class execution tool:
```python
render_ui(spec: Dict[str, Any], target: str = "all") -> Dict[str, Any]
```
- **Validation**: Every specification is validated against the catalog schema before projection.
- **Self-Correction Feedback**: If an agent emits an unknown component type (e.g. `MagicAiFixerWidget`), the harness rejects the call and returns structured error feedback. The agent observes the rejection and self-corrects into standard catalog primitives.

### 2. Concurrent Multi-Surface Projection
The `MultiSurfaceBroadcaster` projects validated specifications across multiple simultaneous surfaces:
- **Terminal Console**: Renders colored trees, tables, KPI metrics, and panels via `rich`.
- **Web Browser**: Emits real-time Server-Sent Events (SSE) to connected web views.
- **Action Bridge**: Captures client interactions (`POST /action`) and feeds them back into the autonomous agent loop as synthetic execution turns.

### 3. Agent Lifecycle State Machine
```
INITIALIZED ──> REASONING ──> TOOL_INVOCATION ──> SURFACE_RENDERED ──> AWAITING_ACTION
                    ▲                                                          │
                    └────────────────── ACTION_PROCESSED ──────────────────────┘
                    │
                  (Error) ──> Self-Correction ──> SURFACE_RENDERED ──> COMPLETED
```

## Modes Demonstrated

1. **Static Mode (`static_mode.py`)**:
   Deterministic single-turn UI specification rendering and validation. Asserts exact catalog compliance and dual-surface projection.
2. **Declarative Mode (`declarative_mode.py`)**:
   Multi-turn tool-calling UI agent loop with schema enforcement and self-correction. Demonstrates deliberate rejection of an invalid component and successful recovery.
3. **Open-Ended UX Mode (`open_ended_mode.py`)**:
   Agent reasoning loop emitting dynamic interactive HTML/SVG topology artifacts with strict CSP sandbox and live re-rendering.
4. **Mixed / Hybrid Mode (`mixed_mode.py`)**:
   TrueForge hybrid architecture combining deterministic layout shell with generative dynamic cards, an interactive human-in-the-loop action loop, and defensive error recovery for malformed action payloads.

## Running Demonstrations

```bash
# Run all modes in deterministic mock mode
python demo.py --mode all --mock

# Run specific mode
python demo.py --mode static --mock
python demo.py --mode declarative --mock
python demo.py --mode open_ended --mock
python demo.py --mode mixed --mock
```
