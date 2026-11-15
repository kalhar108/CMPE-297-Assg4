"""A2UI Codelab 1 - Mode 2: Declarative Mode.

Structured, schema-constrained generation producing a flat element map
and dynamic RFC 6901 pointer bindings. The agent generates the component
structure dynamically according to catalog schema rules while data values
are bound via JSON Pointers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from common.llm_provider import BaseModelProvider, get_llm_provider
from common.mock_data import (
    A2UI_DECLARATIVE_COMPONENTS,
    A2UI_DECLARATIVE_CREATE_SURFACE,
    A2UI_DECLARATIVE_DATA_MODEL,
)

try:
    from .a2ui_protocol import (
        A2UIActionEvent,
        A2UIComponent,
        A2UIEnvelope,
        A2UISurface,
        CreateSurfacePayload,
        UpdateComponentsPayload,
        UpdateDataModelPayload,
    )
except ImportError:
    from a2ui_protocol import (
        A2UIActionEvent,
        A2UIComponent,
        A2UIEnvelope,
        A2UISurface,
        CreateSurfacePayload,
        UpdateComponentsPayload,
        UpdateDataModelPayload,
    )


def run_declarative_mode(
    provider: Optional[BaseModelProvider] = None,
    surface_id: str = "surface-analytics-02",
    prompt: str = "Generate an A2UI analytics dashboard with active agent metrics, token compression, and action controls",
) -> Dict[str, Any]:
    """Executes A2UI Declarative Mode workflow:

    1. Emits createSurface envelope with emerald theme.
    2. Requests LLM provider to synthesize a schema-valid UpdateComponentsPayload.
    3. Emits updateComponents with the generated flat component map.
    4. Binds telemetry data model via updateDataModel.
    5. Validates catalog rules (root exists, all child references resolve).
    6. Dispatches client action event ('rebalance-btn').
    """
    llm = provider or get_llm_provider()
    surface = A2UISurface(surface_id=surface_id)
    trace: List[Dict[str, Any]] = []

    # Step 1: createSurface
    create_payload = CreateSurfacePayload(**A2UI_DECLARATIVE_CREATE_SURFACE)
    create_env = A2UIEnvelope(createSurface=create_payload)
    surface.apply_envelope(create_env)
    trace.append({"step": "createSurface", "envelope": create_env.to_wire_dict()})

    # Step 2: Request structured component synthesis
    try:
        generated_payload = llm.generate_structured(
            prompt=f"A2UI Declarative Mode: {prompt}. Emit flat element map with root Card, Metric rows, and action Buttons.",
            schema=UpdateComponentsPayload,
        )
    except Exception:
        # Fallback to schema-valid mock
        components = [A2UIComponent(**comp) for comp in A2UI_DECLARATIVE_COMPONENTS]
        generated_payload = UpdateComponentsPayload(surfaceId=surface_id, components=components)

    # Step 3: Apply updateComponents
    comps_env = A2UIEnvelope(updateComponents=generated_payload)
    surface.apply_envelope(comps_env)
    trace.append({"step": "updateComponents", "envelope": comps_env.to_wire_dict()})

    # Step 4: Populate Data Model via updateDataModel
    for section_k, section_v in A2UI_DECLARATIVE_DATA_MODEL.items():
        if isinstance(section_v, dict):
            for field_k, field_v in section_v.items():
                path = f"/{section_k}/{field_k}"
                dm_payload = UpdateDataModelPayload(surfaceId=surface_id, path=path, value=field_v)
                surface.apply_envelope(A2UIEnvelope(updateDataModel=dm_payload))
                trace.append({"step": "updateDataModel", "path": path, "value": field_v})
        else:
            path = f"/{section_k}"
            dm_payload = UpdateDataModelPayload(surfaceId=surface_id, path=path, value=section_v)
            surface.apply_envelope(A2UIEnvelope(updateDataModel=dm_payload))
            trace.append({"step": "updateDataModel", "path": path, "value": section_v})

    # Step 5: Validate surface hierarchy
    validation_errors = surface.validate()

    # Step 6: Dispatch action on interactive button
    action_event = None
    if "rebalance-btn" in surface.components:
        action_event = surface.dispatch_action("rebalance-btn")
        trace.append({"step": "action_dispatch", "event": action_event.model_dump()})

    return {
        "status": "success",
        "surface_id": surface_id,
        "mode": "declarative",
        "validation_errors": validation_errors,
        "is_valid": len(validation_errors) == 0,
        "component_count": len(surface.components),
        "data_model": surface.data_model,
        "action_event": action_event.model_dump() if action_event else None,
        "trace": trace,
        "surface": surface,
    }


if __name__ == "__main__":
    result = run_declarative_mode()
    print(f"Declarative Mode Completed: valid={result['is_valid']}, components={result['component_count']}")
    if result["action_event"]:
        print(f"Dispatched action context: {result['action_event']['context']}")
