"""AG-UI Codelab 2 - Mode 3: Open-Ended UX Mode.

Conversational graph with generative UI stream and dynamic graph nodes.
Demonstrates live streaming of natural language reasoning tokens coupled with
the emission of unconstrained generative UI components via `COMPONENT_UPDATE`.
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
    AGUI_OPEN_ENDED_COMPONENT,
    AGUI_OPEN_ENDED_REASONING_CHUNKS,
    AGUI_THREAD_ID,
)

try:
    from .agui_server import AGUIEvent, AGUIEventType
    from .state_store import JsonPatchOp, ReactiveStateStore
except ImportError:
    from agui_server import AGUIEvent, AGUIEventType
    from state_store import JsonPatchOp, ReactiveStateStore


def stream_open_ended_mode_events(
    state_store: ReactiveStateStore,
    provider: Optional[BaseModelProvider] = None,
    run_id: str = "run-agui-openended-03",
    thread_id: str = AGUI_THREAD_ID,
) -> Generator[AGUIEvent, None, None]:
    """Generates an AG-UI event sequence featuring streaming reasoning and generative UI."""
    llm = provider or get_llm_provider()

    # 1. RUN_STARTED
    yield AGUIEvent(
        event=AGUIEventType.RUN_STARTED,
        data={"threadId": thread_id, "runId": run_id, "timestamp": "2026-11-05T20:02:00Z"},
    )

    # 2. STATE_SNAPSHOT
    yield AGUIEvent(
        event=AGUIEventType.STATE_SNAPSHOT,
        data={"threadId": thread_id, "runId": run_id, "snapshot": state_store.get_snapshot()},
    )

    # 3. TEXT_MESSAGE stream (Model reasoning tokens)
    msg_id = "msg-reasoning-03"
    yield AGUIEvent(
        event=AGUIEventType.TEXT_MESSAGE_START,
        data={"messageId": msg_id, "role": "assistant"},
    )

    for chunk in llm.stream_text("Synthesize a force-directed interactive topological graph widget"):
        yield AGUIEvent(
            event=AGUIEventType.TEXT_MESSAGE_CONTENT,
            data={"messageId": msg_id, "delta": chunk},
        )

    yield AGUIEvent(
        event=AGUIEventType.TEXT_MESSAGE_END,
        data={"messageId": msg_id},
    )

    # 4. COMPONENT_UPDATE: Emits generative UI widget artifact
    component_payload = AGUI_OPEN_ENDED_COMPONENT
    yield AGUIEvent(
        event=AGUIEventType.COMPONENT_UPDATE,
        data={
            "threadId": thread_id,
            "runId": run_id,
            "component": component_payload,
        },
    )

    # 5. STATE_DELTA: Commit component to state store
    patch_op = JsonPatchOp(
        op="add",
        path="/artifacts/active_component",
        value=component_payload,
    )
    state_store.apply_patch([patch_op])
    yield AGUIEvent(
        event=AGUIEventType.STATE_DELTA,
        data={
            "threadId": thread_id,
            "runId": run_id,
            "patches": [patch_op.to_wire_dict()],
        },
    )

    # 6. RUN_FINISHED
    yield AGUIEvent(
        event=AGUIEventType.RUN_FINISHED,
        data={
            "runId": run_id,
            "status": "COMPLETED",
            "tokenUsage": {"promptTokens": 196, "completionTokens": 112, "totalTokens": 308},
        },
    )


def run_open_ended_mode(
    provider: Optional[BaseModelProvider] = None,
    run_id: str = "run-agui-openended-03",
) -> Dict[str, Any]:
    """Executes AG-UI Open-Ended UX Mode workflow and collects events and artifact state."""
    initial_state = {"session": {"topic": "Dynamic Simulation"}, "artifacts": {}}
    state_store = ReactiveStateStore(initial_state=initial_state)
    events: List[AGUIEvent] = []
    sse_frames: List[str] = []

    for event in stream_open_ended_mode_events(
        state_store=state_store, provider=provider, run_id=run_id
    ):
        events.append(event)
        sse_frames.append(event.to_sse())

    final_state = state_store.get_snapshot()
    has_component = "active_component" in final_state.get("artifacts", {})

    return {
        "status": "success",
        "mode": "open_ended",
        "run_id": run_id,
        "event_count": len(events),
        "events": [e.model_dump() for e in events],
        "sse_frames": sse_frames,
        "component_synthesized": has_component,
        "final_state": final_state,
        "state_store": state_store,
    }


if __name__ == "__main__":
    result = run_open_ended_mode()
    print(f"AG-UI Open-Ended Mode completed: {result['event_count']} events emitted.")
    print(f"Component synthesized in state: {result['component_synthesized']}")
