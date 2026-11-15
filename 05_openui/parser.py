"""Pure-Python line-oriented DSL parser for OpenUI Lang (.oui).

Provides token-efficient AST construction, forward reference resolution,
defensive line-by-line streaming, and error recovery.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


class Identifier(str):
    """Represents an unquoted variable or component identifier."""
    pass


@dataclass
class OpenUINode:
    """Represents a single parsed OpenUI DSL component node."""
    id: str
    component: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    props: Dict[str, Any] = field(default_factory=dict)
    raw_statement: str = ""
    line_number: int = 0
    is_skeleton: bool = False
    unresolved_refs: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Converts AST node to dictionary representation."""
        return {
            "id": self.id,
            "component": self.component,
            "props": self.props,
            "children": self.children,
            "is_skeleton": self.is_skeleton,
            "line_number": self.line_number,
        }


@dataclass
class OpenUIProgram:
    """Represents the complete parsed OpenUI program and its symbol table."""
    root_id: Optional[str] = None
    nodes: Dict[str, OpenUINode] = field(default_factory=dict)
    unresolved_references: Set[str] = field(default_factory=set)
    syntax_errors: List[Dict[str, Any]] = field(default_factory=list)
    source_lines: List[str] = field(default_factory=list)

    def get_root(self) -> Optional[OpenUINode]:
        """Returns the root AST node if defined, or the first defined node."""
        if self.root_id and self.root_id in self.nodes:
            return self.nodes[self.root_id]
        if "root" in self.nodes:
            return self.nodes["root"]
        if self.nodes:
            first_key = next(iter(self.nodes))
            return self.nodes[first_key]
        return None


def _tokenize_arguments(arg_str: str) -> List[str]:
    """Splits an argument string by top-level commas, respecting quotes and brackets.
    
    Gracefully handles unbalanced trailing quotes by terminating the string at line end.
    """
    tokens: List[str] = []
    current: List[str] = []
    in_single_quote = False
    in_double_quote = False
    bracket_depth = 0
    brace_depth = 0
    escaped = False

    for char in arg_str:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\":
            escaped = True
            current.append(char)
            continue

        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
            continue

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
            continue

        if not in_single_quote and not in_double_quote:
            if char in ("[", "("):
                bracket_depth += 1
            elif char in ("]", ")"):
                bracket_depth = max(0, bracket_depth - 1)
            elif char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth = max(0, brace_depth - 1)
            elif char == "," and bracket_depth == 0 and brace_depth == 0:
                token = "".join(current).strip()
                if token:
                    tokens.append(token)
                current = []
                continue

        current.append(char)

    token = "".join(current).strip()
    if token:
        tokens.append(token)

    return tokens


def _parse_value(val_str: str) -> Any:
    """Parses a primitive literal, identifier reference, or nested collection."""
    val_str = val_str.strip()
    if not val_str:
        return ""

    # Quoted string (single or double) -> returns regular str
    if (val_str.startswith('"') and val_str.endswith('"')) or (val_str.startswith("'") and val_str.endswith("'")):
        if len(val_str) >= 2:
            return val_str[1:-1].encode("utf-8").decode("unicode_escape", errors="replace")
        return ""

    # Unbalanced quote fallback: treat as regular string
    if (val_str.startswith('"') and not val_str.endswith('"')) or (val_str.startswith("'") and not val_str.endswith("'")):
        return val_str[1:]

    # Booleans and Null
    lower = val_str.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "none"):
        return None

    # Numbers
    if re.fullmatch(r"-?\d+", val_str):
        return int(val_str)
    if re.fullmatch(r"-?\d+\.\d+", val_str):
        return float(val_str)

    # List literal: [a, b, c]
    if val_str.startswith("[") and val_str.endswith("]"):
        inner = val_str[1:-1].strip()
        if not inner:
            return []
        items = _tokenize_arguments(inner)
        return [_parse_value(item) for item in items]

    # Unquoted token matching identifier pattern -> returns Identifier
    if re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_-]*", val_str):
        return Identifier(val_str)

    # Fallback to string
    return val_str


class OpenUIParser:
    """Streaming and batch parser for OpenUI Lang DSL."""

    STATEMENT_PATTERN = re.compile(
        r"^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*$",
        re.DOTALL,
    )
    ASSIGNMENT_PATTERN = re.compile(
        r"^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*(.+)$",
        re.DOTALL,
    )

    def __init__(self) -> None:
        self.program = OpenUIProgram()

    def parse_line(self, line: str, line_no: int = 1) -> Optional[OpenUINode]:
        """Parses a single line of OpenUI code."""
        self.program.source_lines.append(line)
        cleaned = line.strip()

        # Ignore empty lines and comments
        if not cleaned or cleaned.startswith("#") or cleaned.startswith("//"):
            return None

        # Check for Component invocation: id = Component(...)
        match = self.STATEMENT_PATTERN.match(cleaned)
        if match:
            var_id, comp_name, raw_args = match.groups()
            return self._create_component_node(var_id, comp_name, raw_args, cleaned, line_no)

        # Check for direct assignment: id = [...] or id = "..."
        assign_match = self.ASSIGNMENT_PATTERN.match(cleaned)
        if assign_match:
            var_id, raw_val = assign_match.groups()
            parsed_val = _parse_value(raw_val)
            children: List[str] = []
            unresolved: Set[str] = set()
            self._trace_references(parsed_val, children, unresolved)

            node = OpenUINode(
                id=var_id,
                component="Literal",
                props={"value": parsed_val},
                children=children,
                raw_statement=cleaned,
                line_number=line_no,
                unresolved_refs=unresolved,
            )
            self._register_node(node)
            return node

        # Syntax Error: malformed statement
        error_info = {
            "line": line_no,
            "statement": cleaned,
            "error": "SyntaxError: Expected 'identifier = Component(...)' format",
        }
        self.program.syntax_errors.append(error_info)
        return None

    def _create_component_node(
        self,
        var_id: str,
        comp_name: str,
        raw_args: str,
        raw_statement: str,
        line_no: int,
    ) -> OpenUINode:
        """Constructs an OpenUINode, separates positional/kwargs, and traces children."""
        raw_tokens = _tokenize_arguments(raw_args)
        args: List[Any] = []
        kwargs: Dict[str, Any] = {}
        children: List[str] = []
        unresolved: Set[str] = set()

        for token in raw_tokens:
            token = token.strip()
            # Check for key=value
            if "=" in token and not (token.startswith('"') or token.startswith("'") or token.startswith("[")):
                key, _, val_str = token.partition("=")
                key = key.strip()
                val = _parse_value(val_str)
                kwargs[key] = val
                self._trace_references(val, children, unresolved)
            else:
                val = _parse_value(token)
                args.append(val)
                self._trace_references(val, children, unresolved)

        # Build unified props dictionary
        props: Dict[str, Any] = dict(kwargs)
        # Component-specific positional arg mapping
        if comp_name == "Metric":
            if len(args) >= 1 and "label" not in props:
                props["label"] = str(args[0])
            if len(args) >= 2 and "value" not in props:
                props["value"] = str(args[1])
            if len(args) >= 3 and "change" not in props:
                props["change"] = str(args[2])
        elif comp_name == "Card":
            if len(args) >= 1 and "title" not in props:
                props["title"] = str(args[0])
            if len(args) >= 2 and "description" not in props:
                props["description"] = str(args[1])
        elif comp_name == "Button":
            if len(args) >= 1 and "label" not in props:
                props["label"] = str(args[0])
            if len(args) >= 2 and "action" not in props:
                props["action"] = str(args[1])
        elif comp_name == "Text":
            if len(args) >= 1 and "content" not in props:
                props["content"] = str(args[0])
        elif comp_name == "TextField":
            if len(args) >= 1 and "label" not in props:
                props["label"] = str(args[0])
            if len(args) >= 2 and "value" not in props:
                props["value"] = str(args[1])
        elif comp_name == "Table":
            if len(args) >= 1 and "columns" not in props:
                props["columns"] = args[0]
            if len(args) >= 2 and "rows" not in props:
                props["rows"] = args[1]
        elif comp_name == "HtmlArtifact":
            if len(args) >= 1 and "title" not in props:
                props["title"] = str(args[0])
            if len(args) >= 2 and "document" not in props:
                props["document"] = str(args[1])
        elif comp_name == "Stack":
            if len(args) >= 1 and "direction" not in props and isinstance(args[0], str) and not isinstance(args[0], Identifier):
                props["direction"] = args[0]
            elif len(args) >= 2 and "direction" not in props and isinstance(args[1], str) and not isinstance(args[1], Identifier):
                props["direction"] = args[1]

        # Explicit children keyword prop
        if "children" in props and isinstance(props["children"], list):
            for ch in props["children"]:
                ch_id = str(ch)
                if ch_id not in children:
                    children.append(ch_id)

        node = OpenUINode(
            id=var_id,
            component=comp_name,
            args=args,
            kwargs=kwargs,
            children=children,
            props=props,
            raw_statement=raw_statement,
            line_number=line_no,
            unresolved_refs=unresolved,
        )

        self._register_node(node)
        return node

    def _trace_references(self, val: Any, children: List[str], unresolved: Set[str]) -> None:
        """Checks parsed values for Identifier instances to track child IDs and forward refs."""
        if isinstance(val, Identifier):
            ref_id = str(val)
            if ref_id not in self.program.nodes:
                unresolved.add(ref_id)
                self.program.unresolved_references.add(ref_id)
            if ref_id not in children:
                children.append(ref_id)
        elif isinstance(val, list):
            for item in val:
                self._trace_references(item, children, unresolved)
        elif isinstance(val, dict):
            for item in val.values():
                self._trace_references(item, children, unresolved)

    def _register_node(self, node: OpenUINode) -> None:
        """Registers a node into program symbol table and resolves pending forward references."""
        self.program.nodes[node.id] = node
        if self.program.root_id is None:
            self.program.root_id = node.id
        elif node.id == "root":
            self.program.root_id = "root"

        # Resolve forward references to this newly defined node
        if node.id in self.program.unresolved_references:
            self.program.unresolved_references.remove(node.id)

        # Clear unresolved status from existing nodes that reference node.id
        for existing in self.program.nodes.values():
            if node.id in existing.unresolved_refs:
                existing.unresolved_refs.remove(node.id)

    def parse_program(self, source: str) -> OpenUIProgram:
        """Parses a multi-line OpenUI DSL source string into a complete AST program."""
        lines = source.strip().splitlines()
        for idx, line in enumerate(lines, start=1):
            self.parse_line(line, line_no=idx)
        return self.program


def parse_program(source: str) -> OpenUIProgram:
    """Convenience helper to parse an OpenUI program."""
    parser = OpenUIParser()
    return parser.parse_program(source)


def parse_line(line: str, line_no: int = 1) -> Tuple[Optional[OpenUINode], OpenUIProgram]:
    """Convenience helper to parse a single line."""
    parser = OpenUIParser()
    node = parser.parse_line(line, line_no)
    return node, parser.program
