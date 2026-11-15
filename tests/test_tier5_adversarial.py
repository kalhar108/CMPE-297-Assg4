"""
Tier 5: Adversarial Boundary, Fault Injection, and Stress Testing Suite.
Empirically stress-tests protocol boundaries, malformed streams, corrupted chunks,
dangling/circular references in OpenUI DSL, out-of-spec A2UI envelopes,
and JSON Pointer exception surfacing across the GenUX codebase.
"""

import sys
import copy
import threading
import pytest
import pydantic
from pathlib import Path
from typing import Dict, Any, List

# Ensure assignment-4-genux is in sys.path
_ASSIGNMENT_ROOT = Path(__file__).resolve().parent.parent
if str(_ASSIGNMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_ASSIGNMENT_ROOT))

import importlib
patch_compiler_mod = importlib.import_module("04_json_render.patch_compiler")
SpecStreamCompiler = patch_compiler_mod.SpecStreamCompiler
createSpecStreamCompiler = patch_compiler_mod.createSpecStreamCompiler

agui_server_mod = importlib.import_module("02_agui.agui_server")
AGUIServer = agui_server_mod.AGUIServer
AGUIEvent = agui_server_mod.AGUIEvent
AGUIEventType = agui_server_mod.AGUIEventType
ClientActionInput = agui_server_mod.ClientActionInput

state_store_mod = importlib.import_module("02_agui.state_store")
ReactiveStateStore = state_store_mod.ReactiveStateStore
JsonPatchOp = state_store_mod.JsonPatchOp

openui_parser_mod = importlib.import_module("05_openui.parser")
OpenUIParser = openui_parser_mod.OpenUIParser
parse_program = openui_parser_mod.parse_program

openui_compiler_mod = importlib.import_module("05_openui.compiler")
OpenUICompiler = openui_compiler_mod.OpenUICompiler
compile_to_json_spec = openui_compiler_mod.compile_to_json_spec
compile_to_react_tree = openui_compiler_mod.compile_to_react_tree
compile_to_html = openui_compiler_mod.compile_to_html

a2ui_protocol_mod = importlib.import_module("01_a2ui.a2ui_protocol")
A2UIEnvelope = a2ui_protocol_mod.A2UIEnvelope
A2UISurface = a2ui_protocol_mod.A2UISurface
A2UIComponent = a2ui_protocol_mod.A2UIComponent
A2UIJsonPointer = a2ui_protocol_mod.A2UIJsonPointer
CreateSurfacePayload = a2ui_protocol_mod.CreateSurfacePayload
UpdateComponentsPayload = a2ui_protocol_mod.UpdateComponentsPayload
UpdateDataModelPayload = a2ui_protocol_mod.UpdateDataModelPayload
DeleteSurfacePayload = a2ui_protocol_mod.DeleteSurfacePayload


# ============================================================================
# Section 1: Malformed Stream Injections (04_json_render & 02_agui)
# ============================================================================

def test_patch_compiler_truncated_json_chunks():
    """Adversarial 1.1: Inject truncated JSON chunks line-by-line; verify graceful recovery and skipping."""
    compiler = createSpecStreamCompiler()
    
    truncated_chunks = [
        '{"op": "add", "path": "/elements/header", "value": {"title": ',  # Unclosed JSON object
        '{"op": "replace", "path": "/root"',                             # Premature EOF
        '[{"op": "add", "path": "/elements/broken"',                      # Unclosed list
        '{"op": "add", "path": "/elements/bad_esc", "value": "\\u00',     # Incomplete unicode escape
        '{"op": "add", "path": "/state/counter", "value": 12e',           # Incomplete exponent
    ]
    
    for chunk in truncated_chunks:
        success = compiler.compile_line(chunk)
        assert success is False, f"Expected compile_line to return False for truncated chunk: {chunk}"
    
    # Verify skipped count and error messages
    assert len(compiler.skipped) == len(truncated_chunks)
    for record in compiler.skipped:
        assert "raw_line" in record
        assert "JSONDecodeError" in record["reason"]
    
    # Verify compiler state remains clean and can process subsequent valid patches
    valid_patches = [
        '{"op": "add", "path": "/elements/header", "value": {"type": "Header", "props": {"title": "Recovered"}}}',
        '{"op": "add", "path": "/root", "value": "header"}'
    ]
    for patch in valid_patches:
        ok = compiler.compile_line(patch)
        assert ok is True
        
    assert compiler.document["root"] == "header"
    assert "header" in compiler.document["elements"]
    assert compiler.document["elements"]["header"]["props"]["title"] == "Recovered"
    
    # Verify spec compilation succeeds without crashing
    spec = compiler.get_spec()
    assert spec.root == "header"
    assert "header" in spec.elements


def test_patch_compiler_invalid_rfc6902_verbs_and_payloads():
    """Adversarial 1.2: Inject unsupported verbs, missing op/path, and malformed move/copy."""
    compiler = createSpecStreamCompiler()
    
    adversarial_patches = [
        {"op": "upsert", "path": "/elements/foo", "value": {}},           # Invalid verb
        {"op": "delete", "path": "/elements/foo"},                        # Invalid verb (RFC uses 'remove')
        {"op": "patch", "path": "/elements/foo", "value": {}},            # Invalid verb
        {"op": 12345, "path": "/elements/foo"},                          # Non-string op
        {"path": "/elements/foo", "value": {}},                           # Missing op
        {"op": "add", "value": {}},                                       # Missing path
        {},                                                               # Empty patch
        {"op": "move", "path": "/elements/foo"},                          # Move missing 'from'
        {"op": "copy", "from": "/elements/nonexistent", "path": "/bar"},  # Copy from non-existent key
        {"op": "replace", "path": "/", "value": "string_not_dict"},       # Root replace with non-dict
    ]
    
    for patch in adversarial_patches:
        ok = compiler.apply_patch(patch)
        assert ok is False, f"Expected apply_patch to fail for: {patch}"
        
    assert len(compiler.skipped) == len(adversarial_patches)
    # Ensure document remains unaffected
    assert compiler.document == {"root": None, "elements": {}, "state": {}}


def test_patch_compiler_corrupted_chunk_stream():
    """Adversarial 1.3: Inject noisy stream with blank lines, comments, and deep paths."""
    compiler = createSpecStreamCompiler()
    
    stream_data = [
        "",                                      # Blank line
        "   ",                                   # Whitespace line
        "# This is a comment",                   # Comment line
        {"op": "add", "path": "/elements/c1", "value": {"type": "Container", "props": {}}},
        42,                                      # Primitive number (invalid in compile_stream)
        "not a json line",                       # Syntax error
        {"op": "add", "path": "/state/metrics/deep/nested/rate", "value": 99.4}, # Auto-creates nested path
        {"op": "add", "path": "/root", "value": "c1"},
    ]
    
    # Process stream
    compiler.compile_stream(stream_data)
    
    # Verify root was set and deep nested state was created
    assert compiler.document["root"] == "c1"
    assert compiler.document["elements"]["c1"]["type"] == "Container"
    assert compiler.document["state"]["metrics"]["deep"]["nested"]["rate"] == 99.4
    
    # Check early first-paint threshold was captured
    assert compiler.first_paint_patch_idx is not None
    assert compiler.first_paint_timestamp is not None


def test_agui_server_action_malformed_stream_injections():
    """Adversarial 1.4: Inject malformed patches into AGUIServer dispatch_action and ReactiveStateStore."""
    from fastapi.testclient import TestClient
    server = AGUIServer(initial_state={"user": "alice", "balance": 100, "active": True})
    client = TestClient(server.app)
    
    # 1. Invalid patch op in dispatch_action raises ValidationError from pydantic
    with pytest.raises(pydantic.ValidationError) as exc_info:
        client.post("/action", json={
            "actionName": "corrupt_attempt",
            "payload": {"patch": [{"op": "invalid_verb", "path": "/balance", "value": 999}]}
        })
    assert "op" in str(exc_info.value)
    
    # 2. Verify state store balance was NOT corrupted
    assert server.state_store.get_snapshot()["balance"] == 100
    
    # 3. Test atomic rollback on failed batch in ReactiveStateStore
    # Patch 1 replaces balance with 500, but Patch 2 fails 'test' assertion
    failing_batch = [
        {"op": "replace", "path": "/balance", "value": 500},
        {"op": "test", "path": "/user", "value": "bob"}  # Actual is alice -> fails!
    ]
    with pytest.raises(ValueError) as exc_info:
        server.state_store.apply_patch(failing_batch)
    assert "RFC 6902 test failed" in str(exc_info.value)
    
    # CRITICAL: Verify balance was NOT mutated to 500 (atomicity check)
    snapshot = server.state_store.get_snapshot()
    assert snapshot["balance"] == 100, "ReactiveStateStore must roll back trial mutations upon batch failure"
    
    # 4. Action without patch returns acknowledged
    res = client.post("/action", json={"actionName": "ping", "payload": {}})
    assert res.status_code == 200
    assert res.json()["status"] == "action_acknowledged"


def test_agui_state_store_concurrency_stress():
    """Adversarial 1.5: Concurrent multi-threaded patch execution on ReactiveStateStore."""
    store = ReactiveStateStore(initial_state={"counter": 0, "logs": []})
    num_threads = 8
    increments_per_thread = 25
    
    def worker(worker_id: int):
        for _ in range(increments_per_thread):
            # Atomic batch: increment counter and append to logs
            current_c = store.get_value("/counter")
            store.apply_patch([
                {"op": "replace", "path": "/counter", "value": current_c + 1},
                {"op": "add", "path": "/logs/-", "value": f"w{worker_id}"}
            ])
            
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    final_state = store.get_snapshot()
    assert len(final_state["logs"]) == num_threads * increments_per_thread


# ============================================================================
# Section 2: Dangling Forward References in OpenUI (05_openui)
# ============================================================================

def test_openui_dangling_forward_references():
    """Adversarial 2.1: OpenUI DSL containing dangling unresolved forward references."""
    source = """
    root = Stack(direction="column", children=[header, missing_kpi1, missing_kpi2])
    header = Card(title="System Overview")
    """
    program = parse_program(source)
    
    # Verify parser marks dangling IDs in unresolved_references
    assert "missing_kpi1" in program.unresolved_references
    assert "missing_kpi2" in program.unresolved_references
    assert "header" not in program.unresolved_references
    
    # Root node unresolved_refs set
    assert program.nodes["root"].unresolved_refs == {"missing_kpi1", "missing_kpi2"}
    assert program.nodes["header"].unresolved_refs == set()
    
    # Compiler to JSON spec: generates Skeleton placeholders with is_skeleton=True
    json_spec = compile_to_json_spec(program)
    assert "missing_kpi1" in json_spec["elements"]
    assert json_spec["elements"]["missing_kpi1"]["is_skeleton"] is True
    assert json_spec["elements"]["missing_kpi1"]["type"] == "Skeleton"
    assert "missing_kpi1" in json_spec["unresolved_references"]
    assert "missing_kpi2" in json_spec["unresolved_references"]
    
    # Compiler to React tree: replaces dangling references with Skeleton component
    react_tree = compile_to_react_tree(program)
    assert react_tree["component"] == "Stack"
    child_components = [c["component"] for c in react_tree["children"]]
    assert child_components.count("Skeleton") == 2
    assert "Card" in child_components
    
    # Compiler to HTML: emits .skeleton-shimmer placeholders without crashing
    html_out = compile_to_html(program)
    assert "skeleton-shimmer" in html_out
    assert "missing_kpi1" in html_out


def test_openui_circular_references_termination():
    """Adversarial 2.2: Circular references in OpenUI DSL must terminate cleanly without RecursionError."""
    # Direct self-reference
    self_ref_source = "a = Card(title='Self', children=[a])"
    prog_self = parse_program(self_ref_source)
    assert "a" in prog_self.nodes
    
    react_tree_self = compile_to_react_tree(prog_self)
    assert react_tree_self["component"] == "Card"
    assert react_tree_self["children"][0]["component"] == "CircularRefWarning"
    
    html_self = compile_to_html(prog_self)
    assert "Circular reference: a" in html_self
    
    # 2-node mutual circular reference
    mutual_source = """
    node_a = Stack(children=[node_b])
    node_b = Stack(children=[node_a])
    """
    prog_mutual = parse_program(mutual_source)
    assert "node_a" in prog_mutual.nodes
    assert "node_b" in prog_mutual.nodes
    
    react_tree_mutual = compile_to_react_tree(prog_mutual)
    assert react_tree_mutual["component"] == "Stack"
    # Traversing node_a -> node_b -> node_a catches cycle
    child_b = react_tree_mutual["children"][0]
    assert child_b["children"][0]["component"] == "CircularRefWarning"
    
    html_mutual = compile_to_html(prog_mutual)
    assert "Circular reference" in html_mutual
    
    # 3-node cycle
    cycle_source = """
    c1 = Stack(children=[c2])
    c2 = Stack(children=[c3])
    c3 = Stack(children=[c1])
    """
    prog_cycle = parse_program(cycle_source)
    react_tree_cycle = compile_to_react_tree(prog_cycle)
    assert react_tree_cycle["children"][0]["children"][0]["children"][0]["component"] == "CircularRefWarning"


def test_openui_malformed_syntax_graceful_recovery():
    """Adversarial 2.3: Interleaved syntax errors in OpenUI DSL must not abort parser."""
    source = """
    valid_header = Card(title="Valid Header")
    bad_syntax_no_equal Button(label="No Equal")
    valid_metric = Metric(label="Active Sessions", value=1420)
    garbage_line %^&*@!
    valid_button = Button(label="Submit", action="save")
    """
    program = parse_program(source)
    
    # Verify syntax errors logged
    assert len(program.syntax_errors) == 2
    assert program.syntax_errors[0]["line"] == 2
    assert program.syntax_errors[1]["line"] == 4
    
    # Verify valid nodes were still parsed
    assert "valid_header" in program.nodes
    assert "valid_metric" in program.nodes
    assert "valid_button" in program.nodes
    assert program.nodes["valid_metric"].props["value"] == 1420


# ============================================================================
# Section 3: Envelope Boundary Violations (01_a2ui)
# ============================================================================

def test_a2ui_json_pointer_boundary_stress():
    """Adversarial 3.1: JSON Pointer syntax errors, escapes, list bounds, and deletion."""
    # 1. Missing leading slash raises ValueError
    with pytest.raises(ValueError) as exc_info:
        A2UIJsonPointer.parse_tokens("invalid_pointer_without_slash")
    assert "must start with '/'" in str(exc_info.value)
    
    # 2. Empty string or single slash returns whole doc
    doc = {"users": [{"name": "Ada"}, {"name": "Grace"}]}
    assert A2UIJsonPointer.resolve(doc, "") == doc
    assert A2UIJsonPointer.resolve(doc, "/") == doc
    
    # 3. RFC 6901 Escaping: ~1 -> / and ~0 -> ~
    doc_escaped = {"path/with/slash": {"field~with~tilde": "escaped_success"}}
    pointer = "/path~1with~1slash/field~0with~0tilde"
    assert A2UIJsonPointer.resolve(doc_escaped, pointer) == "escaped_success"
    
    # 4. Out of bounds list indexing in resolve returns default
    assert A2UIJsonPointer.resolve(doc, "/users/99/name", default="NOT_FOUND") == "NOT_FOUND"
    assert A2UIJsonPointer.resolve(doc, "/users/invalid_idx/name", default="NOT_FOUND") == "NOT_FOUND"
    
    # 5. List indexing in set_value: "-" appends, non-numeric raises KeyError
    A2UIJsonPointer.set_value(doc, "/users/-", {"name": "Linus"})
    assert len(doc["users"]) == 3
    assert doc["users"][2]["name"] == "Linus"
    
    with pytest.raises(KeyError) as exc_info:
        A2UIJsonPointer.set_value(doc, "/users/bad_token/name", "value")
    assert "Cannot index list" in str(exc_info.value)
    
    # 6. Delete value gracefully deletes target and ignores nonexistent paths
    A2UIJsonPointer.delete_value(doc, "/users/2")
    assert len(doc["users"]) == 2
    # Deleting non-existent path doesn't raise exception
    A2UIJsonPointer.delete_value(doc, "/users/99/nonexistent")


def test_a2ui_envelope_validation_and_boundary_rejection():
    """Adversarial 3.2: Rejection of out-of-spec envelopes and Pydantic schema validation."""
    # 1. Envelope with no operations set
    empty_env = A2UIEnvelope()
    assert empty_env.operation_type() == "unknown"
    assert empty_env.to_wire_dict() == {"version": "v0.9.1"}
    
    # 2. Pydantic validation rejects missing required fields
    with pytest.raises(pydantic.ValidationError) as exc_info:
        CreateSurfacePayload.model_validate({})  # Missing surfaceId
    assert "surfaceId" in str(exc_info.value)
    
    with pytest.raises(pydantic.ValidationError) as exc_info:
        UpdateComponentsPayload.model_validate({"surfaceId": "s1"})  # Missing components
    assert "components" in str(exc_info.value)
    
    with pytest.raises(pydantic.ValidationError) as exc_info:
        UpdateDataModelPayload.model_validate({"surfaceId": "s1"})  # Missing path
    assert "path" in str(exc_info.value)
    
    with pytest.raises(pydantic.ValidationError) as exc_info:
        A2UIComponent.model_validate({"id": "btn1"})  # Missing component type
    assert "component" in str(exc_info.value)


def test_a2ui_surface_lifecycle_and_error_diagnostics():
    """Adversarial 3.3: Surface validation errors, missing action component, and pointer failure."""
    surface = A2UISurface("test-surface-alpha")
    
    # 1. Validation on empty surface
    errors = surface.validate()
    assert "Surface has no components registered." in errors
    
    # 2. Validation with components missing 'root'
    surface.components["comp1"] = A2UIComponent(id="comp1", component="Card", props={}, children=["btn1"])
    errors = surface.validate()
    assert any("root" in err for err in errors)
    assert any("references missing child ID 'btn1'" in err for err in errors)
    
    # 3. Dispatch action on nonexistent component raises KeyError
    with pytest.raises(KeyError) as exc_info:
        surface.dispatch_action("ghost_button")
    assert "ghost_button" in str(exc_info.value)
    
    # 4. Out-of-spec pointer in updateDataModel raises ValueError
    bad_dm_envelope = A2UIEnvelope(
        updateDataModel=UpdateDataModelPayload(
            surfaceId="test-surface-alpha",
            path="missing_slash_pointer",
            value="fail"
        )
    )
    with pytest.raises(ValueError) as exc_info:
        surface.apply_envelope(bad_dm_envelope)
    assert "must start with '/'" in str(exc_info.value)
    
    # 5. Full lifecycle cleanup via deleteSurface
    del_envelope = A2UIEnvelope(deleteSurface=DeleteSurfacePayload(surfaceId="test-surface-alpha"))
    surface.apply_envelope(del_envelope)
    assert surface.active is False
    assert len(surface.components) == 0
    assert len(surface.data_model) == 0
