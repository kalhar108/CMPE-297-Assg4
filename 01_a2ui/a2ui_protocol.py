"""A2UI (Agent-to-UI) Protocol v0.9.1 Implementation.

Implements the official Google A2UI v0.9.1 wire protocol envelopes:
- createSurface
- updateComponents
- updateDataModel (RFC 6901 JSON Pointer binding)
- deleteSurface
- client action event resolution and data model synchronization
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class A2UIJsonPointer:
    """RFC 6901 compliant JSON Pointer resolver, setter, and deleter."""

    @staticmethod
    def _unescape(token: str) -> str:
        return token.replace("~1", "/").replace("~0", "~")

    @staticmethod
    def _escape(token: str) -> str:
        return token.replace("~", "~0").replace("/", "~1")

    @classmethod
    def parse_tokens(cls, pointer: str) -> List[str]:
        """Parses a JSON Pointer string into reference tokens."""
        if not pointer or pointer == "/":
            return []
        if not pointer.startswith("/"):
            raise ValueError(f"Invalid JSON Pointer '{pointer}': must start with '/'")
        return [cls._unescape(token) for token in pointer[1:].split("/")]

    @classmethod
    def resolve(cls, doc: Any, pointer: str, default: Any = None) -> Any:
        """Resolves a JSON Pointer against a document."""
        if not pointer or pointer == "/":
            return doc
        tokens = cls.parse_tokens(pointer)
        curr = doc
        for token in tokens:
            if isinstance(curr, dict):
                if token in curr:
                    curr = curr[token]
                else:
                    return default
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
        return curr

    @classmethod
    def set_value(cls, doc: Dict[str, Any], pointer: str, value: Any) -> Dict[str, Any]:
        """Sets a value at the specified JSON pointer path, creating parents if missing."""
        tokens = cls.parse_tokens(pointer)
        if not tokens:
            if isinstance(value, dict):
                doc.clear()
                doc.update(value)
            return doc

        curr: Any = doc
        for i, token in enumerate(tokens[:-1]):
            next_token = tokens[i + 1]
            if isinstance(curr, dict):
                if token not in curr or not isinstance(curr[token], (dict, list)):
                    # Check if next token is numeric
                    curr[token] = [] if (next_token.isdigit() or next_token == "-") else {}
                curr = curr[token]
            elif isinstance(curr, list):
                try:
                    idx = int(token)
                    while len(curr) <= idx:
                        curr.append({})
                    curr = curr[idx]
                except ValueError:
                    raise KeyError(f"Cannot index list with non-integer token '{token}'")

        leaf = tokens[-1]
        if isinstance(curr, dict):
            curr[leaf] = value
        elif isinstance(curr, list):
            if leaf == "-":
                curr.append(value)
            else:
                try:
                    idx = int(leaf)
                    while len(curr) <= idx:
                        curr.append(None)
                    curr[idx] = value
                except ValueError:
                    curr.append(value)
        return doc

    @classmethod
    def delete_value(cls, doc: Dict[str, Any], pointer: str) -> Dict[str, Any]:
        """Deletes a node at the specified JSON pointer path."""
        tokens = cls.parse_tokens(pointer)
        if not tokens:
            doc.clear()
            return doc

        curr: Any = doc
        for token in tokens[:-1]:
            if isinstance(curr, dict) and token in curr:
                curr = curr[token]
            elif isinstance(curr, list):
                try:
                    idx = int(token)
                    curr = curr[idx]
                except (ValueError, IndexError):
                    return doc
            else:
                return doc

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
        return doc


class A2UIComponent(BaseModel):
    """Component definition within an A2UI flat element map."""
    id: str = Field(description="Unique string identifier for the component")
    component: str = Field(description="Catalog component type, e.g. Card, Row, Column, Text, TextField, Button")
    props: Dict[str, Any] = Field(default_factory=dict, description="Component properties and dynamic pointer bindings")
    children: List[str] = Field(default_factory=list, description="IDs of direct child components")


class CreateSurfacePayload(BaseModel):
    """Payload for creating a new isolated A2UI surface."""
    surfaceId: str
    catalogId: str = "https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json"
    theme: Dict[str, Any] = Field(default_factory=dict)
    sendDataModel: bool = True


class UpdateComponentsPayload(BaseModel):
    """Payload for updating or replacing the flat component dictionary."""
    surfaceId: str
    components: List[A2UIComponent]


class UpdateDataModelPayload(BaseModel):
    """Payload for mutating surface data model via JSON Pointer."""
    surfaceId: str
    path: str
    value: Optional[Any] = None
    remove: Optional[bool] = False


class DeleteSurfacePayload(BaseModel):
    """Payload for releasing a surface instance."""
    surfaceId: str


class A2UIEnvelope(BaseModel):
    """The standard A2UI v0.9.1 wire protocol envelope."""
    version: str = "v0.9.1"
    createSurface: Optional[CreateSurfacePayload] = None
    updateComponents: Optional[UpdateComponentsPayload] = None
    updateDataModel: Optional[UpdateDataModelPayload] = None
    deleteSurface: Optional[DeleteSurfacePayload] = None

    def operation_type(self) -> str:
        """Returns the active operation name within this envelope."""
        for op in ("createSurface", "updateComponents", "updateDataModel", "deleteSurface"):
            if getattr(self, op) is not None:
                return op
        return "unknown"

    def to_wire_dict(self) -> Dict[str, Any]:
        """Serializes to standard A2UI JSON wire format, omitting None keys."""
        return self.model_dump(exclude_none=True)


class A2UIActionEvent(BaseModel):
    """Client-to-server action event triggered by interactive elements."""
    name: str = Field(description="Action name identifier")
    surfaceId: str = Field(description="Surface where action originated")
    sourceComponentId: str = Field(description="ID of component triggering the action")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context: Dict[str, Any] = Field(default_factory=dict, description="Resolved action context values")
    dataModel: Dict[str, Any] = Field(default_factory=dict, description="Echoed client data model state")


class A2UISurface:
    """Reactive in-memory A2UI surface representing live component and data states."""

    def __init__(self, surface_id: str) -> None:
        self.surface_id = surface_id
        self.catalog_id: str = ""
        self.theme: Dict[str, Any] = {}
        self.send_data_model: bool = True
        self.components: Dict[str, A2UIComponent] = {}
        self.data_model: Dict[str, Any] = {}
        self.envelope_history: List[A2UIEnvelope] = []
        self.active: bool = False

    def apply_envelope(self, envelope: A2UIEnvelope) -> None:
        """Applies an incoming A2UI envelope message to the surface state."""
        self.envelope_history.append(envelope)

        if envelope.createSurface:
            payload = envelope.createSurface
            self.surface_id = payload.surfaceId
            self.catalog_id = payload.catalogId
            self.theme = payload.theme
            self.send_data_model = payload.sendDataModel
            self.components.clear()
            self.data_model.clear()
            self.active = True

        elif envelope.updateComponents:
            for comp in envelope.updateComponents.components:
                self.components[comp.id] = comp

        elif envelope.updateDataModel:
            payload = envelope.updateDataModel
            if payload.remove:
                A2UIJsonPointer.delete_value(self.data_model, payload.path)
            else:
                A2UIJsonPointer.set_value(self.data_model, payload.path, payload.value)

        elif envelope.deleteSurface:
            self.active = False
            self.components.clear()
            self.data_model.clear()

    def resolve_pointer(self, pointer: str, default: Any = None) -> Any:
        """Resolves an RFC 6901 pointer against this surface's data model."""
        return A2UIJsonPointer.resolve(self.data_model, pointer, default=default)

    def resolve_prop_value(self, prop_val: Any) -> Any:
        """Resolves dynamic pointer bindings within component properties."""
        if isinstance(prop_val, dict) and "path" in prop_val and len(prop_val) == 1:
            return self.resolve_pointer(prop_val["path"])
        return prop_val

    def dispatch_action(self, component_id: str) -> A2UIActionEvent:
        """Simulates client action dispatch, resolving context pointers against data model."""
        if component_id not in self.components:
            raise KeyError(f"Component '{component_id}' not found in surface '{self.surface_id}'")

        comp = self.components[component_id]
        action_spec = comp.props.get("action", {})
        action_name = action_spec.get("name", "generic_action")
        raw_context = action_spec.get("context", {})

        # Resolve context pointer bindings
        resolved_context: Dict[str, Any] = {}
        for k, v in raw_context.items():
            resolved_context[k] = self.resolve_prop_value(v)

        return A2UIActionEvent(
            name=action_name,
            surfaceId=self.surface_id,
            sourceComponentId=component_id,
            context=resolved_context,
            dataModel=copy.deepcopy(self.data_model) if self.send_data_model else {},
        )

    def validate(self) -> List[str]:
        """Validates surface integrity against A2UI catalog rules."""
        errors: List[str] = []
        if not self.components:
            errors.append("Surface has no components registered.")
            return errors

        if "root" not in self.components:
            errors.append("Missing required 'root' component in component map.")

        for comp_id, comp in self.components.items():
            for child_id in comp.children:
                if child_id not in self.components:
                    errors.append(f"Component '{comp_id}' references missing child ID '{child_id}'.")

        return errors

    def render_rich_tree(self) -> Tree:
        """Generates a rich tree visualization of the active component hierarchy."""
        tree = Tree(f"[bold cyan]Surface: {self.surface_id}[/bold cyan] (Catalog: [dim]{self.catalog_id.split('/')[-1]}[/dim])")

        def add_node(parent_tree: Tree, comp_id: str) -> None:
            if comp_id not in self.components:
                parent_tree.add(f"[bold red]MISSING: {comp_id}[/bold red]")
                return
            comp = self.components[comp_id]

            # Format props with resolved values
            props_summary = []
            for k, v in comp.props.items():
                if k == "action":
                    props_summary.append(f"[yellow]action={v.get('name')}[/yellow]")
                elif isinstance(v, dict) and "path" in v:
                    resolved = self.resolve_pointer(v["path"], default="<unset>")
                    props_summary.append(f"{k}=[magenta]{v['path']} -> '{resolved}'[/magenta]")
                else:
                    props_summary.append(f"{k}='{v}'")

            props_str = f" ({', '.join(props_summary)})" if props_summary else ""
            node = parent_tree.add(f"[bold green]{comp.component}[/bold green] [dim]id={comp.id}[/dim]{props_str}")
            for child_id in comp.children:
                add_node(node, child_id)

        if "root" in self.components:
            add_node(tree, "root")
        else:
            for cid in self.components:
                add_node(tree, cid)
        return tree

    def render_rich_panel(self) -> Panel:
        """Renders the component tree and data model in a unified Rich Panel."""
        from rich.console import Group

        tree = self.render_rich_tree()

        # Data model table
        table = Table(title="Surface Data Model (RFC 6901 Bindings)", border_style="blue", show_header=True)
        table.add_column("Key / Path", style="cyan")
        table.add_column("Bound Value", style="white")

        def flatten_dict(d: dict, prefix: str = "") -> None:
            for k, v in d.items():
                path = f"{prefix}/{k}"
                if isinstance(v, dict):
                    flatten_dict(v, path)
                else:
                    table.add_row(path, str(v))

        flatten_dict(self.data_model)

        group = Group(tree, Text(""), table)
        return Panel(group, title=f"[bold]A2UI Active Surface: {self.surface_id}[/bold]", border_style="cyan")
