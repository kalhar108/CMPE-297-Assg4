"""AG-UI Codelab 2 - Mode 4: Mixed / Hybrid Mode.

Hybrid state graph with deterministic core metrics and dynamic agent-suggested action widgets.
Demonstrates human-in-the-loop client approval gates, bidirectional action dispatch,
and multi-protocol composability by embedding A2UI protocol envelopes inside
AG-UI `CUSTOM` events.
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
    A2UI_MIXED_CREATE_SURFACE,
    AGUI_MIXED_APPROVAL_TOOL_CALL,
    AGUI_MIXED_COMPLETION_PATCHES,
    AGUI_MIXED_INITIAL_STATE,
    AGUI_MIXED_POST_APPROVAL_PATCHES,
    AGUI_THREAD_ID,
)

try:
    from .agui_server import AGUIEvent, AGUIEventType
    from .state_store import JsonPatchOp, ReactiveStateStore
except ImportError:
    from agui_server import AGUIEvent, AGUIEventType
    from state_store import JsonPatchOp, ReactiveStateStore


def stream_mixed_mode_events(
    state_store: ReactiveStateStore,
    provider: Optional[BaseModelProvider] = None,
    run_id: str = "run-agui-mixed-04",
    thread_id: str = AGUI_THREAD_ID,
    auto_approve: bool = True,
) -> Generator[AGUIEvent, None, None]:
    """Generates an AG-UI event sequence with approval gate and embedded A2UI envelope."""
    # 1. RUN_STARTED
    yield AGUIEvent(
        event=AGUIEventType.RUN_STARTED,
        data={"threadId": thread_id, "runId": run_id, "timestamp": "2026-11-05T20:03:00Z"},
    )

    # 2. STATE_SNAPSHOT
    yield AGUIEvent(
        event=AGUIEventType.STATE_SNAPSHOT,
        data={"threadId": thread_id, "runId": run_id, "snapshot": state_store.get_snapshot()},
    )

    # 3. TOOL_CALL for Human-in-the-loop authorization gate
    tool_call = AGUI_MIXED_APPROVAL_TOOL_CALL
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_START,
        data={
            "toolCallId": tool_call["toolCallId"],
            "name": tool_call["name"],
        },
    )
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_ARGS,
        data={
            "toolCallId": tool_call["toolCallId"],
            "delta": '{"workflowId": "wf-auto-migrate-84", "prompt": "Authorize Spanner migration?"}',
        },
    )
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_END,
        data={"toolCallId": tool_call["toolCallId"]},
    )

    # 4. ACTION_EMITTED: Simulate client interactive approval feedback
    action_data = {
        "actionName": "authorize_action",
        "toolCallId": tool_call["toolCallId"],
        "approved": auto_approve,
        "operator": "devops_engineer",
    }
    yield AGUIEvent(
        event=AGUIEventType.ACTION_EMITTED,
        data=action_data,
    )

    # 5. STATE_DELTA: Post-approval transition
    post_approval_ops = [JsonPatchOp.model_validate(p) for p in AGUI_MIXED_POST_APPROVAL_PATCHES]
    state_store.apply_patch(post_approval_ops)
    yield AGUIEvent(
        event=AGUIEventType.STATE_DELTA,
        data={
            "threadId": thread_id,
            "runId": run_id,
            "patches": [p.to_wire_dict() for p in post_approval_ops],
        },
    )

    # 6. TOOL_CALL_RESULT: Tool completes execution
    yield AGUIEvent(
        event=AGUIEventType.TOOL_CALL_RESULT,
        data={
            "toolCallId": tool_call["toolCallId"],
            "content": {"status": "authorized", "executionInitiated": True},
        },
    )

    # 7. STATE_DELTA: Workflow completion
    completion_ops = [JsonPatchOp.model_validate(p) for p in AGUI_MIXED_COMPLETION_PATCHES]
    state_store.apply_patch(completion_ops)
    yield AGUIEvent(
        event=AGUIEventType.STATE_DELTA,
        data={
            "threadId": thread_id,
            "runId": run_id,
            "patches": [p.to_wire_dict() for p in completion_ops],
        },
    )

    # 8. CUSTOM: Protocol Composability - Embed A2UI envelope inside AG-UI CUSTOM event
    yield AGUIEvent(
        event=AGUIEventType.CUSTOM,
        data={
            "name": "a2ui",
            "format": "application/vnd.a2ui.v0.9.1+json",
            "envelope": {
                "version": "v0.9.1",
                "createSurface": A2UI_MIXED_CREATE_SURFACE,
            },
        },
    )

    # 9. RUN_FINISHED
    yield AGUIEvent(
        event=AGUIEventType.RUN_FINISHED,
        data={
            "runId": run_id,
            "status": "COMPLETED",
            "tokenUsage": {"promptTokens": 180, "completionTokens": 95, "totalTokens": 275},
        },
    )


def run_mixed_mode(
    provider: Optional[BaseModelProvider] = None,
    run_id: str = "run-agui-mixed-04",
) -> Dict[str, Any]:
    """Executes AG-UI Mixed Mode workflow and collects events, approval status, and state."""
    state_store = ReactiveStateStore(initial_state=AGUI_MIXED_INITIAL_STATE)
    events: List[AGUIEvent] = []
    sse_frames: List[str] = []

    for event in stream_mixed_mode_events(
        state_store=state_store, provider=provider, run_id=run_id
    ):
        events.append(event)
        sse_frames.append(event.to_sse())

    final_state = state_store.get_snapshot()
    workflow_stage = final_state.get("workflow", {}).get("stage", "UNKNOWN")
    has_custom_a2ui = any(e.event == AGUIEventType.CUSTOM for e in events)

    return {
        "status": "success",
        "mode": "mixed",
        "run_id": run_id,
        "event_count": len(events),
        "events": [e.model_dump() for e in events],
        "sse_frames": sse_frames,
        "approval_granted": True,
        "workflow_final_stage": workflow_stage,
        "custom_a2ui_embedded": has_custom_a2ui,
        "final_state": final_state,
        "state_store": state_store,
    }


if __name__ == "__main__":
    result = run_mixed_mode()
    print(f"AG-UI Mixed Mode completed: {result['event_count']} events emitted.")
    print(f"Workflow Final Stage: {result['workflow_final_stage']}, A2UI embedded: {result['custom_a2ui_embedded']}")
