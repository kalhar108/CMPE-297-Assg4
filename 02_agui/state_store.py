"""Thread-safe Reactive State Store for AG-UI Protocol.

Maintains shared application state synchronized between server and client
via RFC 6902 JSON Patches (add, remove, replace, move, copy, test).
All patch mutations are applied atomically under a re-entrant lock.
"""

from __future__ import annotations

import copy
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class JsonPatchOp(BaseModel):
    """RFC 6902 JSON Patch operation model."""
    op: Literal["add", "remove", "replace", "move", "copy", "test"]
    path: str
    value: Optional[Any] = None
    from_: Optional[str] = Field(default=None, alias="from")

    model_config = {"populate_by_name": True}

    def to_wire_dict(self) -> Dict[str, Any]:
        """Serializes to standard RFC 6902 wire format dictionary."""
        d = {"op": self.op, "path": self.path}
        if self.op in ("add", "replace", "test") or self.value is not None:
            d["value"] = self.value
        if self.op in ("move", "copy") or self.from_ is not None:
            d["from"] = self.from_
        return d


class ReactiveStateStore:
    """Thread-safe reactive in-memory state store with RFC 6902 JSON Patch support."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = copy.deepcopy(initial_state) if initial_state else {}
        self._subscribers: List[Callable[[List[JsonPatchOp], Dict[str, Any]], None]] = []
        self._patch_history: List[JsonPatchOp] = []

    def subscribe(self, callback: Callable[[List[JsonPatchOp], Dict[str, Any]], None]) -> None:
        """Registers a listener callback invoked upon atomic patch application."""
        with self._lock:
            self._subscribers.append(callback)

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns a deep copy of the current state dictionary."""
        with self._lock:
            return copy.deepcopy(self._state)

    def get_value(self, path: str, default: Any = None) -> Any:
        """Resolves a JSON Pointer against the current state."""
        with self._lock:
            if not path or path == "/":
                return copy.deepcopy(self._state)
            tokens = self._parse_tokens(path)
            curr = self._state
            for token in tokens:
                if isinstance(curr, dict) and token in curr:
                    curr = curr[token]
                elif isinstance(curr, list):
                    try:
                        idx = int(token)
                        if 0 <= idx < len(curr):
                            curr = curr[idx]
                        else:
                            return default
                    except ValueError:
                        return default
                else:
                    return default
            return copy.deepcopy(curr)

    def apply_patch(
        self,
        ops: Union[JsonPatchOp, List[JsonPatchOp], Dict[str, Any], List[Dict[str, Any]]],
    ) -> List[JsonPatchOp]:
        """Atomically applies a single operation or batch of RFC 6902 operations."""
        # Normalize to List[JsonPatchOp]
        if isinstance(ops, (JsonPatchOp, dict)):
            raw_list = [ops]
        else:
            raw_list = list(ops)

        patch_ops: List[JsonPatchOp] = []
        for item in raw_list:
            if isinstance(item, JsonPatchOp):
                patch_ops.append(item)
            elif isinstance(item, dict):
                patch_ops.append(JsonPatchOp.model_validate(item))

        with self._lock:
            # First pass: validate all operations against state copy
            trial_state = copy.deepcopy(self._state)
            for op in patch_ops:
                self._apply_single_op(trial_state, op)

            # Second pass: commit mutations to live state
            for op in patch_ops:
                self._apply_single_op(self._state, op)
                self._patch_history.append(op)

            # Notify subscribers
            current_snapshot = copy.deepcopy(self._state)
            for sub in self._subscribers:
                try:
                    sub(patch_ops, current_snapshot)
                except Exception:
                    pass

        return patch_ops

    @staticmethod
    def _parse_tokens(path: str) -> List[str]:
        if not path or path == "/":
            return []
        if not path.startswith("/"):
            raise ValueError(f"Invalid path '{path}': must start with '/'")
        return [t.replace("~1", "/").replace("~0", "~") for t in path[1:].split("/")]

    def _apply_single_op(self, doc: Dict[str, Any], op: JsonPatchOp) -> None:
        tokens = self._parse_tokens(op.path)

        if op.op == "add":
            self._op_add(doc, tokens, op.value)
        elif op.op == "remove":
            self._op_remove(doc, tokens)
        elif op.op == "replace":
            self._op_replace(doc, tokens, op.value)
        elif op.op == "move":
            if not op.from_:
                raise ValueError("RFC 6902 'move' operation requires 'from' path.")
            from_tokens = self._parse_tokens(op.from_)
            val = self._extract_value(doc, from_tokens)
            self._op_remove(doc, from_tokens)
            self._op_add(doc, tokens, val)
        elif op.op == "copy":
            if not op.from_:
                raise ValueError("RFC 6902 'copy' operation requires 'from' path.")
            from_tokens = self._parse_tokens(op.from_)
            val = copy.deepcopy(self._extract_value(doc, from_tokens))
            self._op_add(doc, tokens, val)
        elif op.op == "test":
            actual = self._extract_value(doc, tokens)
            if actual != op.value:
                raise ValueError(
                    f"RFC 6902 test failed at path '{op.path}': expected {op.value}, found {actual}"
                )

    def _extract_value(self, doc: Dict[str, Any], tokens: List[str]) -> Any:
        curr: Any = doc
        for t in tokens:
            if isinstance(curr, dict) and t in curr:
                curr = curr[t]
            elif isinstance(curr, list):
                idx = int(t)
                curr = curr[idx]
            else:
                raise KeyError(f"Path token '{t}' not found in document.")
        return curr

    def _op_add(self, doc: Dict[str, Any], tokens: List[str], value: Any) -> None:
        if not tokens:
            if isinstance(value, dict):
                doc.clear()
                doc.update(value)
            return

        curr: Any = doc
        for i, token in enumerate(tokens[:-1]):
            next_t = tokens[i + 1]
            if isinstance(curr, dict):
                if token not in curr or not isinstance(curr[token], (dict, list)):
                    curr[token] = [] if (next_t.isdigit() or next_t == "-") else {}
                curr = curr[token]
            elif isinstance(curr, list):
                idx = int(token)
                while len(curr) <= idx:
                    curr.append({})
                curr = curr[idx]

        leaf = tokens[-1]
        if isinstance(curr, dict):
            curr[leaf] = copy.deepcopy(value)
        elif isinstance(curr, list):
            if leaf == "-":
                curr.append(copy.deepcopy(value))
            else:
                try:
                    idx = int(leaf)
                    curr.insert(idx, copy.deepcopy(value))
                except ValueError:
                    curr.append(copy.deepcopy(value))

    def _op_remove(self, doc: Dict[str, Any], tokens: List[str]) -> None:
        if not tokens:
            doc.clear()
            return
        curr: Any = doc
        for token in tokens[:-1]:
            if isinstance(curr, dict) and token in curr:
                curr = curr[token]
            elif isinstance(curr, list):
                idx = int(token)
                curr = curr[idx]
            else:
                return

        leaf = tokens[-1]
        if isinstance(curr, dict) and leaf in curr:
            del curr[leaf]
        elif isinstance(curr, list):
            try:
                idx = int(leaf)
                if 0 <= idx < len(curr):
                    curr.pop(idx)
            except ValueError:
                pass

    def _op_replace(self, doc: Dict[str, Any], tokens: List[str], value: Any) -> None:
        if not tokens:
            if isinstance(value, dict):
                doc.clear()
                doc.update(value)
            return
        curr: Any = doc
        for i, token in enumerate(tokens[:-1]):
            next_t = tokens[i + 1]
            if isinstance(curr, dict):
                if token not in curr or not isinstance(curr[token], (dict, list)):
                    curr[token] = [] if (next_t.isdigit() or next_t == "-") else {}
                curr = curr[token]
            elif isinstance(curr, list):
                idx = int(token)
                curr = curr[idx]

        leaf = tokens[-1]
        if isinstance(curr, dict):
            curr[leaf] = copy.deepcopy(value)
        elif isinstance(curr, list):
            idx = int(leaf)
            if 0 <= idx < len(curr):
                curr[idx] = copy.deepcopy(value)
            else:
                curr.append(copy.deepcopy(value))
