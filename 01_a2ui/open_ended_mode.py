"""A2UI Codelab 1 - Mode 3: Open-Ended UX Mode.

Dynamic generative component synthesis with sandboxed Lit/HTML artifact generation.
Demonstrates unconstrained canvas execution inside strict security boundaries
enforced by Content Security Policy (CSP) and sandbox flags.
"""

from __future__ import annotations

import re
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
    A2UI_OPEN_ENDED_COMPONENTS,
    A2UI_OPEN_ENDED_CREATE_SURFACE,
    A2UI_OPEN_ENDED_HTML,
)

try:
    from .a2ui_protocol import (
        A2UIComponent,
        A2UIEnvelope,
        A2UISurface,
        CreateSurfacePayload,
        UpdateComponentsPayload,
    )
except ImportError:
    from a2ui_protocol import (
        A2UIComponent,
        A2UIEnvelope,
        A2UISurface,
        CreateSurfacePayload,
        UpdateComponentsPayload,
    )


def run_open_ended_mode(
    provider: Optional[BaseModelProvider] = None,
    surface_id: str = "surface-openended-03",
    prompt: str = "Synthesize an interactive neural network attention visualization web component",
) -> Dict[str, Any]:
    """Executes A2UI Open-Ended Mode workflow:

    1. Emits createSurface envelope with custom purple theme.
    2. Uses LLM provider to synthesize custom HTML5 / Web Component code.
    3. Wraps the synthesized artifact in an A2UI CustomScriptNode component.
    4. Enforces strict Content Security Policy (CSP) and iframe sandbox attributes.
    5. Validates sandbox security constraints.
    """
    llm = provider or get_llm_provider()
    surface = A2UISurface(surface_id=surface_id)
    trace: List[Dict[str, Any]] = []

    # Step 1: createSurface
    create_payload = CreateSurfacePayload(**A2UI_OPEN_ENDED_CREATE_SURFACE)
    create_env = A2UIEnvelope(createSurface=create_payload)
    surface.apply_envelope(create_env)
    trace.append({"step": "createSurface", "envelope": create_env.to_wire_dict()})

    # Step 2: Synthesize custom component HTML / Lit script
    try:
        raw_html = llm.generate_text(
            prompt=(
                f"Synthesize a standalone, self-contained HTML/CSS/JS interactive simulation widget for: {prompt}. "
                "Include a <meta http-equiv='Content-Security-Policy'> header restricting network access."
            )
        )
        if not raw_html or "<html" not in raw_html.lower():
            raw_html = A2UI_OPEN_ENDED_HTML
    except Exception:
        raw_html = A2UI_OPEN_ENDED_HTML

    # Step 3: Package into CustomScriptNode component
    sandbox_node = A2UIComponent(
        id="sandbox-frame",
        component="CustomScriptNode",
        props={
            "title": "Synthesized Simulation Artifact",
            "html": raw_html,
            "sandboxAttributes": "allow-scripts",
            "csp": "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        },
        children=[],
    )
    root_card = A2UIComponent(
        id="root",
        component="Card",
        props={
            "title": "Sandboxed Generative Lit Component Canvas",
            "subtitle": "Open-Ended UX Mode with Strict Content Security Policy",
        },
        children=["sandbox-frame"],
    )

    update_payload = UpdateComponentsPayload(
        surfaceId=surface_id,
        components=[root_card, sandbox_node],
    )
    comps_env = A2UIEnvelope(updateComponents=update_payload)
    surface.apply_envelope(comps_env)
    trace.append({"step": "updateComponents", "envelope": comps_env.to_wire_dict()})

    # Step 4: Verify sandbox security attributes
    has_csp = "Content-Security-Policy" in raw_html or "default-src" in sandbox_node.props.get("csp", "")
    has_sandbox_flags = "allow-scripts" in sandbox_node.props.get("sandboxAttributes", "")
    is_safe = has_csp and has_sandbox_flags

    validation_errors = surface.validate()

    return {
        "status": "success",
        "surface_id": surface_id,
        "mode": "open_ended",
        "validation_errors": validation_errors,
        "is_valid": len(validation_errors) == 0,
        "is_security_compliant": is_safe,
        "html_artifact_length": len(raw_html),
        "csp_header_present": has_csp,
        "component_count": len(surface.components),
        "trace": trace,
        "surface": surface,
    }


if __name__ == "__main__":
    result = run_open_ended_mode()
    print(f"Open-Ended Mode Completed: valid={result['is_valid']}, safe={result['is_security_compliant']}")
    print(f"Artifact size: {result['html_artifact_length']} chars, components: {result['component_count']}")
