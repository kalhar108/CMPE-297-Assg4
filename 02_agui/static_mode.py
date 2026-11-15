"""AG-UI Codelab 2 - Mode 1: Static Mode.

Static SSE stream emitting pre-defined metrics and dashboard updates.
Demonstrates deterministic event stream sequencing from RUN_STARTED
to STATE_SNAPSHOT, TEXT_MESSAGE_*, STATE_DELTA (RFC 6902), and RUN_FINISHED.
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
    AGUI_STATIC_INITIAL_STATE,
    AGUI_STATIC_RUN_ID,
    AGUI_STATIC_STATE_PATCHES,
    AGUI_THREAD_ID,
)

try:
    from .agui_server import AGUIEvent, AGUIEventType
    from .state_store import JsonPatchOp, ReactiveStateStore
except ImportError:
    from agui_server import AGUIEvent, AGUIEventType
    from state_store import JsonPatchOp, ReactiveStateStore


def stream_static_mode_events(
    state_store: ReactiveStateStore,
    run_id: str = AGUI_STATIC_RUN_ID,
    thread_id: str = AGUI_THREAD_ID,
) -> Generator[AGUIEvent, None, None]:
    """Generates a strictly ordered AG-UI event sequence for static mode."""
    # 1. RUN_STARTED
    yield AGUIEvent(
        event=AGUIEventType.RUN_STARTED,
        data={"threadId": thread_id, "runId": run_id, "timestamp": "2026-11-05T20:00:00Z"},
    )

    # 2. STATE_SNAPSHOT
    snapshot = state_store.get_snapshot()
    yield AGUIEvent(
        event=AGUIEventType.STATE_SNAPSHOT,
        data={"threadId": thread_id, "runId": run_id, "snapshot": snapshot},
    )

    # 3. TEXT_MESSAGE block
    msg_id = "msg-telemetry-01"
    yield AGUIEvent(
        event=AGUIEventType.TEXT_MESSAGE_START,
        data={"messageId": msg_id, "role": "assistant"},
    )
    yield AGUIEvent(
        event=AGUIEventType.TEXT_MESSAGE_CONTENT,
        data={"messageId": msg_id, "delta": "Aggregating telemetry from SiliconValley-Cluster-1..."},
    )
    yield AGUIEvent(
        event=AGUIEventType.TEXT_MESSAGE_CONTENT,
        data={"messageId": msg_id, "delta": " Traffic surge detected; applying state deltas."},
    )
    yield AGUIEvent(
        event=AGUIEventType.TEXT_MESSAGE_END,
        data={"messageId": msg_id},
    )

    # 4. STATE_DELTA: Apply RFC 6902 JSON Patches atomically
    patch_ops = [JsonPatchOp.model_validate(p) for p in AGUI_STATIC_STATE_PATCHES]
    state_store.apply_patch(patch_ops)
    yield AGUIEvent(
        event=AGUIEventType.STATE_DELTA,
        data={
            "threadId": thread_id,
            "runId": run_id,
            "patches": [p.to_wire_dict() for p in patch_ops],
        },
    )

    # 5. RUN_FINISHED
    yield AGUIEvent(
        event=AGUIEventType.RUN_FINISHED,
        data={
            "runId": run_id,
            "status": "COMPLETED",
            "tokenUsage": {"promptTokens": 84, "completionTokens": 32, "totalTokens": 116},
        },
    )


def run_static_mode(
    provider: Optional[BaseModelProvider] = None,
    run_id: str = AGUI_STATIC_RUN_ID,
) -> Dict[str, Any]:
    """Executes AG-UI Static Mode workflow and collects events and state."""
    state_store = ReactiveStateStore(initial_state=AGUI_STATIC_INITIAL_STATE)
    events: List[AGUIEvent] = []
    sse_frames: List[str] = []

    for event in stream_static_mode_events(state_store=state_store, run_id=run_id):
        events.append(event)
        sse_frames.append(event.to_sse())

    final_state = state_store.get_snapshot()

    return {
        "status": "success",
        "mode": "static",
        "run_id": run_id,
        "event_count": len(events),
        "events": [e.model_dump() for e in events],
        "sse_frames": sse_frames,
        "initial_state": AGUI_STATIC_INITIAL_STATE,
        "final_state": final_state,
        "patches_applied": AGUI_STATIC_STATE_PATCHES,
        "state_store": state_store,
    }


if __name__ == "__main__":
    result = run_static_mode()
    print(f"AG-UI Static Mode completed: {result['event_count']} events emitted.")
    print(f"Final CPU Metric in State: {result['final_state']['metrics']['cpu_utilization']}%")
