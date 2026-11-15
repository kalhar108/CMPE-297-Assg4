"""A2UI Codelab 1 - Mode 4: Mixed / Hybrid Mode.

Combines a deterministic catalog shell with dynamic generative cards,
interactive human-in-the-loop action loops, and automated self-correction
recovery upon schema validation failure.
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
    A2UI_MALFORMED_COMPONENTS,
    A2UI_MIXED_COMPONENTS_INITIAL,
    A2UI_MIXED_CREATE_SURFACE,
    A2UI_SELF_CORRECTED_COMPONENTS,
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


def run_mixed_mode(
    provider: Optional[BaseModelProvider] = None,
    surface_id: str = "surface-mixed-04",
) -> Dict[str, Any]:
    """Executes A2UI Mixed Mode workflow:

    1. Emits createSurface envelope for hybrid surface.
    2. Mounts deterministic catalog shell combined with generative recommendation cards.
    3. Simulates client validation fault injection (malformed component map).
    4. Triggers autonomous self-correction loop where provider repairs the schema.
    5. Dispatches interactive user action ('approve_recommendation').
    6. Verifies state update and data model synchronization.
    """
    llm = provider or get_llm_provider()
    surface = A2UISurface(surface_id=surface_id)
    trace: List[Dict[str, Any]] = []

    # Step 1: createSurface
    create_payload = CreateSurfacePayload(**A2UI_MIXED_CREATE_SURFACE)
    create_env = A2UIEnvelope(createSurface=create_payload)
    surface.apply_envelope(create_env)
    trace.append({"step": "createSurface", "envelope": create_env.to_wire_dict()})

    # Step 2: Mount initial hybrid components (shell + generative recommendation)
    initial_comps = [A2UIComponent(**c) for c in A2UI_MIXED_COMPONENTS_INITIAL]
    comps_payload = UpdateComponentsPayload(surfaceId=surface_id, components=initial_comps)
    comps_env = A2UIEnvelope(updateComponents=comps_payload)
    surface.apply_envelope(comps_env)
    trace.append({"step": "updateComponents_initial", "envelope": comps_env.to_wire_dict()})

    # Step 3: Fault Injection - Test defensive validation against malformed envelope
    faulty_surface = A2UISurface(surface_id="surface-fault-test")
    faulty_comps = [A2UIComponent(**c) for c in A2UI_MALFORMED_COMPONENTS]
    faulty_payload = UpdateComponentsPayload(surfaceId="surface-fault-test", components=faulty_comps)
    faulty_surface.apply_envelope(A2UIEnvelope(updateComponents=faulty_payload))
    detected_errors = faulty_surface.validate()
    trace.append({
        "step": "fault_injection",
        "injected_errors_count": len(detected_errors),
        "errors": detected_errors,
    })

    # Step 4: Autonomous Self-Correction Loop
    repair_prompt = (
        f"A2UI Envelope Error: {'; '.join(detected_errors)}. "
        "Repair the component dictionary to satisfy A2UI v0.9.1 specifications: "
        "ensure 'root' component is present and all child references exist."
    )
    repaired_payload = llm.generate_structured(
        prompt=repair_prompt,
        schema=UpdateComponentsPayload,
    )
    # Ensure repaired payload has surface_id
    repaired_payload.surfaceId = surface_id
    repaired_env = A2UIEnvelope(updateComponents=repaired_payload)
    surface.apply_envelope(repaired_env)
    trace.append({"step": "self_correction_applied", "envelope": repaired_env.to_wire_dict()})

    post_repair_errors = surface.validate()
    trace.append({
        "step": "post_repair_validation",
        "errors_count": len(post_repair_errors),
        "is_repaired": len(post_repair_errors) == 0,
    })

    # Step 5: Mount interactive recommendation card back for user action
    comps_restored = [A2UIComponent(**c) for c in A2UI_MIXED_COMPONENTS_INITIAL]
    surface.apply_envelope(A2UIEnvelope(updateComponents=UpdateComponentsPayload(
        surfaceId=surface_id,
        components=comps_restored,
    )))

    # Step 6: Dispatch interactive user action ('rec-approve-btn')
    action_event: A2UIActionEvent = surface.dispatch_action("rec-approve-btn")
    trace.append({"step": "action_dispatch", "event": action_event.model_dump()})

    # Step 7: Apply resulting state mutation to data model
    dm_payload = UpdateDataModelPayload(
        surfaceId=surface_id,
        path="/optimizations/rec-card-1",
        value={"status": "APPLIED", "timestamp": "2026-11-05T20:10:00Z"},
    )
    surface.apply_envelope(A2UIEnvelope(updateDataModel=dm_payload))
    trace.append({"step": "updateDataModel_post_action", "path": dm_payload.path, "value": dm_payload.value})

    return {
        "status": "success",
        "surface_id": surface_id,
        "mode": "mixed",
        "fault_detected": len(detected_errors) > 0,
        "self_correction_passed": len(post_repair_errors) == 0,
        "action_name": action_event.name,
        "action_context": action_event.context,
        "component_count": len(surface.components),
        "data_model": surface.data_model,
        "trace": trace,
        "surface": surface,
    }


if __name__ == "__main__":
    result = run_mixed_mode()
    print(f"Mixed Mode Completed: fault_detected={result['fault_detected']}, repaired={result['self_correction_passed']}")
    print(f"Action dispatched: {result['action_name']} with context: {result['action_context']}")
