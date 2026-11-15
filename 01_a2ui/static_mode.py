"""A2UI Codelab 1 - Mode 1: Static Mode.

Deterministic surface rendering using pre-authored component definitions
and incremental data model updates via RFC 6901 JSON Pointers.
The component hierarchy remains fixed; dynamic state changes flow exclusively
through `updateDataModel`.
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
    A2UI_STATIC_COMPONENTS,
    A2UI_STATIC_CREATE_SURFACE,
    A2UI_STATIC_DATA_MODEL,
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


def run_static_mode(
    provider: Optional[BaseModelProvider] = None,
    surface_id: str = "surface-contact-01",
) -> Dict[str, Any]:
    """Executes A2UI Static Mode workflow:

    1. Emits createSurface envelope with theme and catalog URI.
    2. Emits updateComponents with static Card, TextFields, and Action Buttons.
    3. Emits updateDataModel initializing contact data via RFC 6901 pointers.
    4. Simulates runtime data mutation (/contact/role and /contact/office).
    5. Dispatches client action event ('submit_contact'), testing pointer resolution.
    """
    surface = A2UISurface(surface_id=surface_id)
    trace: List[Dict[str, Any]] = []

    # Step 1: createSurface
    create_payload = CreateSurfacePayload(**A2UI_STATIC_CREATE_SURFACE)
    create_env = A2UIEnvelope(createSurface=create_payload)
    surface.apply_envelope(create_env)
    trace.append({"step": "createSurface", "envelope": create_env.to_wire_dict()})

    # Step 2: updateComponents
    components = [A2UIComponent(**comp) for comp in A2UI_STATIC_COMPONENTS]
    update_comps_payload = UpdateComponentsPayload(surfaceId=surface_id, components=components)
    comps_env = A2UIEnvelope(updateComponents=update_comps_payload)
    surface.apply_envelope(comps_env)
    trace.append({"step": "updateComponents", "envelope": comps_env.to_wire_dict()})

    # Step 3: updateDataModel initial values
    for section_key, section_data in A2UI_STATIC_DATA_MODEL.items():
        for field_key, field_val in section_data.items():
            path = f"/{section_key}/{field_key}"
            dm_payload = UpdateDataModelPayload(surfaceId=surface_id, path=path, value=field_val)
            dm_env = A2UIEnvelope(updateDataModel=dm_payload)
            surface.apply_envelope(dm_env)
            trace.append({"step": "updateDataModel_init", "path": path, "value": field_val})

    # Step 4: Runtime state mutation via updateDataModel
    mutations = [
        ("/contact/role", "Full Professor & Chair of AI"),
        ("/contact/office", "Science & Innovation Complex Room 410"),
    ]
    for path, new_val in mutations:
        dm_mut_payload = UpdateDataModelPayload(surfaceId=surface_id, path=path, value=new_val)
        dm_mut_env = A2UIEnvelope(updateDataModel=dm_mut_payload)
        surface.apply_envelope(dm_mut_env)
        trace.append({"step": "updateDataModel_mutation", "path": path, "value": new_val})

    # Step 5: Simulate user clicking 'submit-btn'
    action_event: A2UIActionEvent = surface.dispatch_action("submit-btn")
    trace.append({"step": "action_dispatch", "event": action_event.model_dump()})

    validation_errors = surface.validate()

    return {
        "status": "success",
        "surface_id": surface_id,
        "mode": "static",
        "validation_errors": validation_errors,
        "is_valid": len(validation_errors) == 0,
        "component_count": len(surface.components),
        "data_model": surface.data_model,
        "action_event": action_event.model_dump(),
        "trace": trace,
        "surface": surface,
    }


if __name__ == "__main__":
    result = run_static_mode()
    print(f"Static Mode Completed: valid={result['is_valid']}, components={result['component_count']}")
    print(f"Action context resolved: {result['action_event']['context']}")
