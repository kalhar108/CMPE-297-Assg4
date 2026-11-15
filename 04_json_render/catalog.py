"""Component Catalog and Specification Contract for JSON Render.

Defines:
1. Pydantic component property models: Container, Card, Metric, Table, Button, Chart, CustomCodeBlock.
2. ElementNode and Spec document data models.
3. Catalog schema validator (check_spec).
4. System prompt generator (catalog.prompt()) generating instructions for LLMs.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# 1. Component Property Schemas
# ==============================================================================

class ContainerProps(BaseModel):
    direction: Literal["row", "column", "grid"] = Field(default="column", description="Layout direction")
    gap: str = Field(default="16px", description="CSS gap between children")
    padding: str = Field(default="16px", description="Internal padding")
    align: Literal["start", "center", "end", "stretch"] = "stretch"
    justify: Literal["start", "center", "end", "space-between"] = "start"


class CardProps(BaseModel):
    title: str = Field(..., description="Card heading")
    subtitle: Optional[str] = Field(default=None, description="Optional secondary text")
    variant: Literal["default", "primary", "secondary", "accent", "danger"] = "default"
    elevation: int = Field(default=1, ge=0, le=4)


class MetricProps(BaseModel):
    label: str = Field(..., description="Metric label")
    value: Any = Field(..., description="Literal value or dynamic state reference {'$state': '/path'}")
    delta: Optional[str] = Field(default=None, description="Percentage or absolute change")
    trend: Optional[Literal["up", "down", "neutral"]] = None


class TableProps(BaseModel):
    columns: List[str] = Field(..., description="Column headers")
    rows: List[List[Any]] = Field(..., description="2D matrix of cell values")
    sortable: bool = Field(default=False)
    striped: bool = Field(default=True)


class ButtonProps(BaseModel):
    label: str = Field(..., description="Button caption")
    action: str = Field(..., description="Action identifier triggered on click")
    variant: Literal["default", "primary", "secondary", "danger"] = "default"
    disabled: bool = Field(default=False)
    icon: Optional[str] = None


class ChartProps(BaseModel):
    chart_type: Literal["bar", "line", "pie", "donut"] = Field(default="bar")
    title: str = Field(..., description="Chart title")
    data: Dict[str, Any] = Field(..., description="Dataset mapping categories to values")
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None


class CustomCodeBlockProps(BaseModel):
    language: str = Field(default="javascript")
    code: str = Field(..., description="Raw executable code or markup")
    title: Optional[str] = None


class HeaderProps(BaseModel):
    title: str = Field(..., description="Header text")
    subtitle: Optional[str] = None


class PlaceholderProps(BaseModel):
    loading: bool = Field(default=True)
    text: Optional[str] = None


COMPONENT_PROP_MODELS: Dict[str, type[BaseModel]] = {
    "Container": ContainerProps,
    "Card": CardProps,
    "Metric": MetricProps,
    "Table": TableProps,
    "Button": ButtonProps,
    "Chart": ChartProps,
    "CustomCodeBlock": CustomCodeBlockProps,
    "Header": HeaderProps,
    "Placeholder": PlaceholderProps,
}


# ==============================================================================
# 2. Document & Element Models
# ==============================================================================

class ElementNode(BaseModel):
    """A single component node in the flat element map."""
    type: str = Field(..., description="Component type from catalog")
    props: Dict[str, Any] = Field(default_factory=dict, description="Component properties")
    children: List[str] = Field(default_factory=list, description="IDs of child elements")


class JSONRenderSpec(BaseModel):
    """The complete declarative document model."""
    root: Optional[str] = Field(default=None, description="ID of root element")
    elements: Dict[str, ElementNode] = Field(default_factory=dict, description="Flat element dictionary")
    state: Dict[str, Any] = Field(default_factory=dict, description="Dynamic application state store")


# ==============================================================================
# 3. Catalog Validator & Contract Engine
# ==============================================================================

class ComponentCatalog:
    """Contract definition, prompt generator, and validator for JSON Render specs."""

    def __init__(self):
        self.components = COMPONENT_PROP_MODELS

    def validate_element(self, element_id: str, node: ElementNode) -> List[str]:
        """Validates a single element against its catalog schema."""
        errors: List[str] = []
        if node.type not in self.components:
            errors.append(f"Element '{element_id}': Unknown component type '{node.type}'.")
            return errors

        model = self.components[node.type]
        # Check required fields
        for field_name, field_info in model.model_fields.items():
            if field_info.is_required() and field_name not in node.props:
                errors.append(f"Element '{element_id}' ({node.type}): Missing required prop '{field_name}'.")

        return errors

    def validate_spec(self, spec: JSONRenderSpec) -> List[str]:
        """Validates entire document specification including circular reference checks."""
        errors: List[str] = []
        if spec.root is None:
            errors.append("Spec error: Missing 'root' element identifier.")
        elif spec.root not in spec.elements:
            errors.append(f"Spec error: 'root' element '{spec.root}' not found in elements dictionary.")

        # Validate elements
        for elem_id, node in spec.elements.items():
            errors.extend(self.validate_element(elem_id, node))
            # Validate children exist or are declared
            for child_id in node.children:
                if child_id not in spec.elements:
                    errors.append(f"Element '{elem_id}': Referenced child '{child_id}' does not exist in elements.")

        # Detect circular references
        if spec.root and spec.root in spec.elements:
            visited = set()
            path = set()

            def has_cycle(curr_id: str) -> bool:
                if curr_id in path:
                    return True
                if curr_id in visited or curr_id not in spec.elements:
                    return False
                visited.add(curr_id)
                path.add(curr_id)
                for c_id in spec.elements[curr_id].children:
                    if has_cycle(c_id):
                        return True
                path.remove(curr_id)
                return False

            if has_cycle(spec.root):
                errors.append("Spec error: Circular child hierarchy detected.")

        return errors

    def prompt(self) -> str:
        """Generates system prompt explaining catalog primitives and streaming patch protocol."""
        return """You are a Generative UI agent. Emit interfaces as flat element maps using RFC 6902 JSON Patches.

Available Catalog Components:
1. Container: props { direction: 'row'|'column'|'grid', gap: str, padding: str }
2. Card: props { title: str, subtitle: Optional[str], variant: 'default'|'primary'|'accent' }
3. Metric: props { label: str, value: Any, delta: Optional[str], trend: 'up'|'down'|'neutral' }
   * Note: value can reference dynamic state using {"$state": "/path/to/key"}
4. Table: props { columns: List[str], rows: List[List[Any]], striped: bool }
5. Button: props { label: str, action: str, variant: 'default'|'primary'|'danger' }
6. Chart: props { chart_type: 'bar'|'line'|'pie', title: str, data: Dict[str, Any] }

Format each update as an RFC 6902 JSON Patch line:
{"op": "add", "path": "/elements/root", "value": {"type": "Card", "props": {"title": "Sales"}, "children": ["kpi"]}}
{"op": "add", "path": "/elements/kpi", "value": {"type": "Metric", "props": {"label": "Revenue", "value": "$12,400"}}}
{"op": "add", "path": "/root", "value": "root"}
"""


# Global catalog singleton
DEFAULT_CATALOG = ComponentCatalog()
