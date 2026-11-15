"""Codelab 4: JSON Render (Vercel-style Declarative UI).

Implements component catalog contracts, streaming RFC 6902 patch compilation
(createSpecStreamCompiler), dynamic $state expression binding, fault-tolerant error recovery,
and multi-target rendering (TerminalRenderer via Rich & DomRenderer via responsive HTML).
"""

from .catalog import (
    ComponentCatalog,
    DEFAULT_CATALOG,
    ElementNode,
    JSONRenderSpec,
    ContainerProps,
    CardProps,
    MetricProps,
    TableProps,
    ButtonProps,
    ChartProps,
    CustomCodeBlockProps,
)
from .patch_compiler import SpecStreamCompiler, createSpecStreamCompiler
from .renderers import TerminalRenderer, DomRenderer
from .static_mode import run_static_mode
from .declarative_mode import run_declarative_mode
from .open_ended_mode import run_open_ended_mode
from .mixed_mode import run_mixed_mode

__all__ = [
    "ComponentCatalog",
    "DEFAULT_CATALOG",
    "ElementNode",
    "JSONRenderSpec",
    "ContainerProps",
    "CardProps",
    "MetricProps",
    "TableProps",
    "ButtonProps",
    "ChartProps",
    "CustomCodeBlockProps",
    "SpecStreamCompiler",
    "createSpecStreamCompiler",
    "TerminalRenderer",
    "DomRenderer",
    "run_static_mode",
    "run_declarative_mode",
    "run_open_ended_mode",
    "run_mixed_mode",
]
