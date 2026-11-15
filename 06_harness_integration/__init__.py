"""Codelab 06: Harness Integration

Provides autonomous agent execution loop with render_ui tool,
multi-surface projection (rich terminal + web SSE), schema validation,
and interactive action feedback loops.
"""

from .multi_surface import (
    ALLOWED_COMPONENT_TYPES,
    MultiSurfaceBroadcaster,
    validate_ui_spec,
)
from .harness_loop import (
    AgentLifecycleStage,
    AutonomousUIAgentLoop,
    TurnRecord,
)

__all__ = [
    "ALLOWED_COMPONENT_TYPES",
    "MultiSurfaceBroadcaster",
    "validate_ui_spec",
    "AgentLifecycleStage",
    "AutonomousUIAgentLoop",
    "TurnRecord",
]
