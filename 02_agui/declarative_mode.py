"""AG-UI Codelab 2 - Mode 2: Declarative Mode.

Reactive state-driven graph responding to tool-driven JSON patch mutations.
The agent interacts with the user interface entirely through tool calls
that emit atomic RFC 6902 JSON Patches against the shared reactive state graph.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from common.llm_provider import BaseModelProvider, get_llm_provider
from common.mock_data import (
    AGUI_DECLARATIVE_INITIAL_STATE,
    AGUI_DECLARATIVE_PATCHES,
    AGUI_DECLARATIVE_TOOL_CALL,
    AGUI_THREAD_ID,
)

try:
    from .agui_server import AGUIEvent, AGUIEventType
    from .state_store import JsonPatchOp, ReactiveStateStore
except ImportError:
    from agui_server import AGUIEvent, AGUIEventType
    from state_store import JsonPatchOp, ReactiveStateStore


def stream_declarative_mode_events(
    state_store: ReactiveStateStore,
    provider: Optional[BaseModelProvider] = None,
    run_id: str = "run-agui-declarative-02",
    thread_id: str = AGUI_THREAD_ID,
) -> Generator[AGUIEvent, None, None]:
    """Generates an AG-UI event sequence for tool-driven declarative state mutations."""
    # 1. RUN_STARTED
    yield AGUIEvent(
        event=AGUIEventType.RUN_STARTED,
        data={"threadId": thread_id, "runId": run_id, "timestamp": "2026-11-05T20:01:00Z"},
    )

    # 2. STATE_SNAPSHOT (Initial empty dashboard graph)
    yield AGUIEvent(
        event=AGUIEventType.STATE_SNAPSHOT,
        data={"threadId": thread_id, "runId": run_id, "snapshot": state_store.get_snapshot()},
    )

    # 3. TOOL_CALL_START: Agent invokes `add_graph_node`
    tool_call = AGUI_DECLARATIVE_TOOL_CALL
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_START,
        data={
            "toolCallId": tool_call["toolCallId"],
            "name": tool_call["name"],
        },
    )

    # 4. TOOL_CALL_ARGS (Streaming tool arguments)
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_ARGS,
        data={
            "toolCallId": tool_call["toolCallId"],
            "delta": '{"nodeId": "node-agent-a", "label": "Lead Gen Agent (ADK)"}',
        },
    )
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_END,
        data={"toolCallId": tool_call["toolCallId"]},
    )

    # 5. STATE_DELTA: Apply RFC 6902 JSON Patches for graph topology
    patch_ops = [JsonPatchOp.model_validate(p) for p in AGUI_DECLARATIVE_PATCHES]
    state_store.apply_patch(patch_ops)

    yield AGUIEvent(
        event=AGUIEventType.STATE_DELTA,
        data={
            "threadId": thread_id,
            "runId": run_id,
            "patches": [p.to_wire_dict() for p in patch_ops],
        },
    )

    # 6. TOOL_CALL_RESULT: Tool responds with execution confirmation
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_RESULT,
        data={
            "toolCallId": tool_call["toolCallId"],
            "content": {"status": "success", "nodesAdded": 2, "edgesAdded": 1},
        },
    )

    # 7. RUN_FINISHED
    yield AGUIEvent(
        event=AGUIEventType.RUN_FINISHED,
        data={
            "runId": run_id,
            "status": "COMPLETED",
            "tokenUsage": {"promptTokens": 142, "completionTokens": 68, "totalTokens": 210},
        },
    )


def run_declarative_mode(
    provider: Optional[BaseModelProvider] = None,
    run_id: str = "run-agui-declarative-02",
) -> Dict[str, Any]:
    """Executes AG-UI Declarative Mode workflow and collects events and graph state."""
    state_store = ReactiveStateStore(initial_state=AGUI_DECLARATIVE_INITIAL_STATE)
    events: List[AGUIEvent] = []
    sse_frames: List[str] = []

    for event in stream_declarative_mode_events(
        state_store=state_store, provider=provider, run_id=run_id
    ):
        events.append(event)
        sse_frames.append(event.to_sse())

    final_state = state_store.get_snapshot()
    node_count = len(final_state.get("dashboard", {}).get("nodes", []))
    edge_count = len(final_state.get("dashboard", {}).get("edges", []))

    return {
        "status": "success",
        "mode": "declarative",
        "run_id": run_id,
        "event_count": len(events),
        "events": [e.model_dump() for e in events],
        "sse_frames": sse_frames,
        "graph_node_count": node_count,
        "graph_edge_count": edge_count,
        "final_state": final_state,
        "state_store": state_store,
    }


if __name__ == "__main__":
    result = run_declarative_mode()
    print(f"AG-UI Declarative Mode completed: {result['event_count']} events emitted.")
    print(f"Reactive Graph State: {result['graph_node_count']} nodes, {result['graph_edge_count']} edges.")
