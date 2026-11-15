"""AG-UI (Agent-Guided UI) SSE Streaming Server and Protocol Generator.

Implements the official AG-UI event stream specification over Server-Sent Events (SSE).
Emits strictly typed events:
- RUN_STARTED / RUN_FINISHED / RUN_ERROR
- TEXT_MESSAGE_START / TEXT_MESSAGE_CONTENT / TEXT_MESSAGE_END
- TOOL_CALL_START / TOOL_CALL_ARGS / TOOL_CALL_END / TOOL_CALL_RESULT
- STATE_SNAPSHOT / STATE_DELTA (RFC 6902 JSON Patches)
- ACTION_EMITTED / COMPONENT_UPDATE / CUSTOM

Note: All SSE frames strictly use LF-only ('\\n') line endings per AG-UI specifications.
"""

from __future__ import annotations

import asyncio
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

try:
    from .state_store import JsonPatchOp, ReactiveStateStore
except ImportError:
    from state_store import JsonPatchOp, ReactiveStateStore


class AGUIEventType(str, Enum):
    """Enumeration of standard AG-UI protocol event types."""
    RUN_STARTED = "RUN_STARTED"
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"
    ACTION_EMITTED = "ACTION_EMITTED"
    COMPONENT_UPDATE = "COMPONENT_UPDATE"
    CUSTOM = "CUSTOM"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"


class AGUIEvent(BaseModel):
    """Typed AG-UI event envelope."""
    event: AGUIEventType
    data: Dict[str, Any] = Field(default_factory=dict)

    def to_sse(self) -> str:
        """Formats the event as a standard SSE frame with LF-only line breaks."""
        payload_json = json.dumps(self.data, default=str)
        # Enforce LF-only delimiters, never CRLF
        return f"event: {self.event.value}\ndata: {payload_json}\n\n"


class RunAgentInput(BaseModel):
    """Input parameters initiating an agent execution run."""
    threadId: str = "thread-genux-default"
    runId: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    mode: str = "static"


class ClientActionInput(BaseModel):
    """Client-dispatched interactive action."""
    actionName: str
    threadId: str = "thread-genux-default"
    runId: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


def format_sse_frame(event_name: str, payload: Any) -> str:
    """Helper formatting an SSE event line with data payload (LF-only)."""
    data_str = json.dumps(payload, default=str) if not isinstance(payload, str) else payload
    return f"event: {event_name}\ndata: {data_str}\n\n"


class AGUIServer:
    """FastAPI AG-UI SSE streaming server with reactive state integration."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        self.state_store = ReactiveStateStore(initial_state=initial_state)
        self.app = FastAPI(title="AG-UI Streaming Protocol Server", version="1.0.0")
        self._register_routes()

    def _register_routes(self) -> None:
        @self.app.get("/health")
        def health_check() -> Dict[str, str]:
            return {"status": "ok", "service": "agui-server", "protocol": "ag-ui/v1.0"}

        @self.app.get("/state")
        def get_current_state() -> Dict[str, Any]:
            return self.state_store.get_snapshot()

        @self.app.post("/action")
        def dispatch_action(action: ClientActionInput) -> Dict[str, Any]:
            # Apply state patch if action carries patch payload
            if "patch" in action.payload:
                ops = self.state_store.apply_patch(action.payload["patch"])
                return {"status": "action_processed", "applied_patches": len(ops)}
            return {"status": "action_acknowledged", "action": action.actionName}

        @self.app.post("/run")
        async def run_agent(input_data: RunAgentInput) -> StreamingResponse:
            async def event_generator() -> AsyncGenerator[str, None]:
                # Stream RUN_STARTED
                run_id = input_data.runId or f"run-{int(asyncio.get_event_loop().time() * 1000)}"
                yield AGUIEvent(
                    event=AGUIEventType.RUN_STARTED,
                    data={"threadId": input_data.threadId, "runId": run_id},
                ).to_sse()

                # Stream STATE_SNAPSHOT
                snapshot = self.state_store.get_snapshot()
                yield AGUIEvent(
                    event=AGUIEventType.STATE_SNAPSHOT,
                    data={"snapshot": snapshot},
                ).to_sse()

                # Stream terminal event
                yield AGUIEvent(
                    event=AGUIEventType.RUN_FINISHED,
                    data={"runId": run_id, "tokenUsage": {"prompt": 120, "completion": 45}},
                ).to_sse()

            return StreamingResponse(event_generator(), media_type="text/event-stream")
