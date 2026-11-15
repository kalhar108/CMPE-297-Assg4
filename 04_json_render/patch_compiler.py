"""Streaming RFC 6902 Patch Compiler for JSON Render (createSpecStreamCompiler).

Compiles streaming JSON patches line-by-line into a live document specification.
Implements:
1. Incremental compilation enabling early first-paint.
2. Auto-creation of missing parent objects/arrays for 'add' operations.
3. Graceful recovery: malformed or unparseable lines recorded in 'skipped' list.
4. Dynamic expression resolution: binds {"$state": "/path"} to document state.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

try:
    from .catalog import ElementNode, JSONRenderSpec, DEFAULT_CATALOG, ComponentCatalog
except (ImportError, ValueError):
    from catalog import ElementNode, JSONRenderSpec, DEFAULT_CATALOG, ComponentCatalog


class SpecStreamCompiler:
    """Live streaming patch compiler implementing RFC 6902 compilation with fault-tolerance."""

    def __init__(self, catalog: Optional[ComponentCatalog] = None):
        self.catalog = catalog or DEFAULT_CATALOG
        self.document: Dict[str, Any] = {
            "root": None,
            "elements": {},
            "state": {},
        }
        self.patch_history: List[Dict[str, Any]] = []
        self.skipped: List[Dict[str, Any]] = []
        self.first_paint_patch_idx: Optional[int] = None
        self.first_paint_timestamp: Optional[float] = None
        self._start_time: float = time.time()

    def _get_nested_target(self, path_parts: List[str], create_missing: bool = True) -> Tuple[Any, str]:
        """Traverses document down to parent container, auto-creating missing structures."""
        curr = self.document
        for part in path_parts[:-1]:
            if isinstance(curr, dict):
                if part not in curr:
                    if not create_missing:
                        raise KeyError(f"Missing key '{part}'")
                    curr[part] = {}
                curr = curr[part]
            elif isinstance(curr, list):
                idx = int(part) if part.isdigit() else 0
                while len(curr) <= idx:
                    curr.append({})
                curr = curr[idx]
        return curr, path_parts[-1]

    def apply_patch(self, patch: Dict[str, Any]) -> bool:
        """Applies a single RFC 6902 patch dictionary to the live document."""
        op = patch.get("op")
        path = patch.get("path", "")
        value = patch.get("value")

        if not op or not path:
            self.skipped.append({"patch": patch, "reason": "Missing required 'op' or 'path' field"})
            return False

        path_parts = [p for p in path.split("/") if p]
        if not path_parts:
            if op == "replace" and isinstance(value, dict):
                self.document = value
                self.patch_history.append(patch)
                return True
            self.skipped.append({"patch": patch, "reason": "Root replacement requires dict value"})
            return False

        try:
            parent, key = self._get_nested_target(path_parts, create_missing=(op in ("add", "replace")))

            if op == "add":
                if isinstance(parent, dict):
                    parent[key] = value
                elif isinstance(parent, list):
                    if key == "-" or not key.isdigit():
                        parent.append(value)
                    else:
                        idx = int(key)
                        if idx >= len(parent):
                            parent.append(value)
                        else:
                            parent.insert(idx, value)

            elif op == "replace":
                if isinstance(parent, dict):
                    parent[key] = value
                elif isinstance(parent, list) and key.isdigit():
                    idx = int(key)
                    if idx < len(parent):
                        parent[idx] = value
                    else:
                        parent.append(value)

            elif op == "remove":
                if isinstance(parent, dict) and key in parent:
                    del parent[key]
                elif isinstance(parent, list) and key.isdigit():
                    idx = int(key)
                    if idx < len(parent):
                        del parent[idx]

            elif op == "copy":
                from_path = patch.get("from", "")
                from_parts = [p for p in from_path.split("/") if p]
                from_parent, from_key = self._get_nested_target(from_parts, create_missing=False)
                val_to_copy = from_parent[from_key] if isinstance(from_parent, dict) else from_parent[int(from_key)]
                if isinstance(parent, dict):
                    parent[key] = val_to_copy
                elif isinstance(parent, list):
                    parent.append(val_to_copy)

            elif op == "move":
                from_path = patch.get("from", "")
                from_parts = [p for p in from_path.split("/") if p]
                from_parent, from_key = self._get_nested_target(from_parts, create_missing=False)
                val_to_move = from_parent[from_key] if isinstance(from_parent, dict) else from_parent[int(from_key)]
                if isinstance(from_parent, dict):
                    del from_parent[from_key]
                elif isinstance(from_parent, list) and from_key.isdigit():
                    del from_parent[int(from_key)]
                if isinstance(parent, dict):
                    parent[key] = val_to_move
                elif isinstance(parent, list):
                    parent.append(val_to_move)

            else:
                self.skipped.append({"patch": patch, "reason": f"Unsupported or unknown op '{op}'"})
                return False

            self.patch_history.append(patch)

            # Check early first-paint threshold: root exists and has at least one valid element
            if self.first_paint_patch_idx is None:
                if self.document.get("root") and self.document.get("elements"):
                    root_id = self.document["root"]
                    if root_id in self.document["elements"]:
                        self.first_paint_patch_idx = len(self.patch_history)
                        self.first_paint_timestamp = time.time() - self._start_time

            return True

        except Exception as e:
            self.skipped.append({"patch": patch, "reason": f"Execution error: {str(e)}"})
            return False

    def compile_line(self, line: str) -> bool:
        """Parses and compiles a single patch line string (JSONL format)."""
        line = line.strip()
        if not line or line.startswith("#"):
            return True

        try:
            patch_data = json.loads(line)
        except json.JSONDecodeError as e:
            self.skipped.append({"raw_line": line, "reason": f"JSONDecodeError: {str(e)}"})
            return False

        if isinstance(patch_data, list):
            all_ok = True
            for item in patch_data:
                if isinstance(item, dict):
                    ok = self.apply_patch(item)
                    all_ok = all_ok and ok
            return all_ok

        if isinstance(patch_data, dict):
            return self.apply_patch(patch_data)

        self.skipped.append({"raw_line": line, "reason": "Line must be JSON object or list of patch objects"})
        return False

    def compile_stream(self, stream: Iterable[Union[str, Dict[str, Any]]]) -> None:
        """Processes an iterable stream of lines or patch dictionaries."""
        for item in stream:
            if isinstance(item, str):
                self.compile_line(item)
            elif isinstance(item, dict):
                self.apply_patch(item)

    def resolve_state_expression(self, expr_val: Any) -> Any:
        """Resolves dynamic state pointer {'$state': '/path'} against document state."""
        if isinstance(expr_val, dict) and "$state" in expr_val:
            state_path = expr_val["$state"]
            parts = [p for p in state_path.split("/") if p]
            curr = self.document.get("state", {})
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                elif isinstance(curr, list) and p.isdigit() and int(p) < len(curr):
                    curr = curr[int(p)]
                else:
                    return None
            return curr
        return expr_val

    def get_resolved_elements(self) -> Dict[str, ElementNode]:
        """Returns element dictionary with all $state dynamic references resolved."""
        resolved: Dict[str, ElementNode] = {}
        raw_elements = self.document.get("elements", {})
        for elem_id, raw_node in raw_elements.items():
            if isinstance(raw_node, dict):
                node_type = raw_node.get("type", "Container")
                props = dict(raw_node.get("props", {}))
                children = list(raw_node.get("children", []))
                # Resolve props expressions
                resolved_props = {}
                for k, v in props.items():
                    resolved_props[k] = self.resolve_state_expression(v)
                resolved[elem_id] = ElementNode(type=node_type, props=resolved_props, children=children)
            elif isinstance(raw_node, ElementNode):
                resolved[elem_id] = raw_node
        return resolved

    def get_spec(self) -> JSONRenderSpec:
        """Returns validated Pydantic JSONRenderSpec with resolved element tree."""
        return JSONRenderSpec(
            root=self.document.get("root"),
            elements=self.get_resolved_elements(),
            state=self.document.get("state", {}),
        )


def createSpecStreamCompiler(catalog: Optional[ComponentCatalog] = None) -> SpecStreamCompiler:
    """Factory function conforming to json-render API conventions."""
    return SpecStreamCompiler(catalog=catalog)
