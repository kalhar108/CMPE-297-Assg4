"""Codelab 05: OpenUI Lang DSL

Provides a token-efficient line-oriented DSL for Generative UI streaming,
forward reference resolution, AST compilation, and token efficiency benchmarks.
"""

from .parser import (
    Identifier,
    OpenUINode,
    OpenUIParser,
    OpenUIProgram,
    parse_line,
    parse_program,
)
from .compiler import (
    OpenUICompiler,
    compile_to_html,
    compile_to_json_spec,
    compile_to_react_tree,
)

__all__ = [
    "Identifier",
    "OpenUINode",
    "OpenUIParser",
    "OpenUIProgram",
    "parse_line",
    "parse_program",
    "OpenUICompiler",
    "compile_to_html",
    "compile_to_json_spec",
    "compile_to_react_tree",
]
