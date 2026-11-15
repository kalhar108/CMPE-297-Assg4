"""Autonomous Agent UI Execution Loop and Lifecycle Manager.

Coordinates multi-turn agent reasoning, invoking the render_ui tool,
enforcing schema constraints with self-correction feedback, and managing
interactive human-in-the-loop action loops.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 1. Resolve Project Root (assignment-4-genux/)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 2. Resolve Module Directory (06_harness_integration/)
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from rich.console import Console
from rich.panel import Panel

try:
    from .multi_surface import MultiSurfaceBroadcaster, validate_ui_spec
except (ImportError, ValueError):
    from multi_surface import MultiSurfaceBroadcaster, validate_ui_spec


class AgentLifecycleStage(str, Enum):
    """Lifecycle stages of an autonomous UI agent execution loop."""
    INITIALIZED = "INITIALIZED"
    REASONING = "REASONING"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    SURFACE_RENDERED = "SURFACE_RENDERED"
    AWAITING_ACTION = "AWAITING_ACTION"
    ACTION_PROCESSED = "ACTION_PROCESSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass
class TurnRecord:
    """Represents a single execution turn in the harness loop."""
    turn_index: int
    stage: AgentLifecycleStage
    thought: str
    tool_call: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    ui_spec: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AutonomousUIAgentLoop:
    """Autonomous agent execution loop with render_ui tool and lifecycle state management."""

    def __init__(
        self,
        broadcaster: Optional[MultiSurfaceBroadcaster] = None,
        console: Optional[Console] = None,
        mode: str = "mock",
    ) -> None:
        self.console = console or Console()
        self.broadcaster = broadcaster or MultiSurfaceBroadcaster(console=self.console)
        self.mode = mode
        self.stage = AgentLifecycleStage.INITIALIZED
        self.turns: List[TurnRecord] = []
        self.context: Dict[str, Any] = {}
        self.self_corrections_count = 0

    def execute_tool_render_ui(self, spec: Dict[str, Any], target: str = "all") -> Dict[str, Any]:
        """Tool implementation invoked by the agent to project UI surfaces."""
        self.stage = AgentLifecycleStage.TOOL_INVOCATION
        receipt = self.broadcaster.render_ui(spec, target=target)

        if receipt.get("status") == "success":
            self.stage = AgentLifecycleStage.SURFACE_RENDERED
        else:
            # Schema error triggers self-correction loop
            self.stage = AgentLifecycleStage.ERROR
            self.self_corrections_count += 1

        return receipt

    def run_step(
        self,
        thought: str,
        spec: Optional[Dict[str, Any]] = None,
        target: str = "all",
    ) -> TurnRecord:
        """Executes a single reasoning step and optional render_ui tool invocation."""
        turn_idx = len(self.turns) + 1
        self.stage = AgentLifecycleStage.REASONING

        tool_result = None
        if spec is not None:
            tool_result = self.execute_tool_render_ui(spec, target=target)

        record = TurnRecord(
            turn_index=turn_idx,
            stage=self.stage,
            thought=thought,
            tool_call="render_ui" if spec is not None else None,
            tool_args={"spec": spec, "target": target} if spec is not None else None,
            tool_result=tool_result,
            ui_spec=spec,
        )
        self.turns.append(record)
        return record

    def handle_client_action(self, action_name: str, payload: Optional[Dict[str, Any]] = None) -> TurnRecord:
        """Processes an incoming client action from web/terminal and resumes agent loop."""
        self.stage = AgentLifecycleStage.ACTION_PROCESSED
        self.broadcaster.dispatch_action(action_name, payload)

        action_turn = self.run_step(
            thought=f"Received client action '{action_name}'. Adjusting UI state and re-projecting.",
            spec=None,
        )
        return action_turn

    def complete(self) -> Dict[str, Any]:
        """Terminates the execution loop and computes evaluation metrics."""
        self.stage = AgentLifecycleStage.COMPLETED
        return {
            "status": "completed",
            "total_turns": len(self.turns),
            "self_corrections": self.self_corrections_count,
            "final_stage": self.stage.value,
            "rendered_surfaces_count": len(self.broadcaster.render_history),
        }
