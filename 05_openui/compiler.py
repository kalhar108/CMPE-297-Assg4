"""Compiler for OpenUI Lang (.oui) AST.

Compiles OpenUI AST programs into:
1. JSON UI specification dictionary (compatible with json-render flat element maps).
2. React-style hierarchical component tree.
3. Self-contained, executable HTML artifact with injected CSP.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# 1. Resolve Project Root (assignment-4-genux/)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 2. Resolve Module Directory (05_openui/)
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

try:
    from .parser import OpenUINode, OpenUIProgram
except (ImportError, ValueError):
    from parser import OpenUINode, OpenUIProgram


class OpenUICompiler:
    """Compiles OpenUIProgram AST into multiple target formats."""

    def __init__(self, program: OpenUIProgram) -> None:
        self.program = program

    def to_json_spec(self) -> Dict[str, Any]:
        """Compiles AST into a flat element map JSON UI specification."""
        elements: Dict[str, Any] = {}

        # First add all parsed nodes
        for node_id, node in self.program.nodes.items():
            clean_props = {k: v for k, v in node.props.items() if k not in ("children",)}
            elements[node_id] = {
                "type": node.component,
                "props": clean_props,
                "children": list(node.children),
                "is_skeleton": node.is_skeleton,
            }

        # For any unresolved forward references, create a skeleton placeholder element
        for unres_id in self.program.unresolved_references:
            if unres_id not in elements:
                elements[unres_id] = {
                    "type": "Skeleton",
                    "props": {
                        "placeholderId": unres_id,
                        "label": f"Loading {unres_id}...",
                    },
                    "children": [],
                    "is_skeleton": True,
                }

        root_id = self.program.root_id or (next(iter(elements)) if elements else "root")
        return {
            "root": root_id,
            "elements": elements,
            "unresolved_references": list(self.program.unresolved_references),
            "state": {},
        }

    def to_react_tree(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        """Compiles AST into a nested React-style component tree."""
        target_root = root_id or self.program.root_id
        if not target_root and self.program.nodes:
            target_root = next(iter(self.program.nodes))

        if not target_root or target_root not in self.program.nodes:
            return {"component": "Empty", "props": {}, "children": []}

        visited: Set[str] = set()

        def _build_node(node_id: str) -> Dict[str, Any]:
            if node_id in visited:
                return {
                    "component": "CircularRefWarning",
                    "props": {"refId": node_id},
                    "children": [],
                }
            visited.add(node_id)

            if node_id in self.program.nodes:
                node = self.program.nodes[node_id]
                clean_props = {k: v for k, v in node.props.items() if k != "children"}
                child_trees: List[Dict[str, Any]] = []
                for child_id in node.children:
                    child_trees.append(_build_node(child_id))
                return {
                    "component": node.component,
                    "props": clean_props,
                    "children": child_trees,
                }
            else:
                # Unresolved reference placeholder
                return {
                    "component": "Skeleton",
                    "props": {
                        "placeholderId": node_id,
                        "status": "pending_stream",
                    },
                    "children": [],
                }

        return _build_node(target_root)

    def to_html(self, title: str = "OpenUI Interface") -> str:
        """Compiles AST into a standalone, beautiful HTML document with injected CSP."""
        json_spec = self.to_json_spec()
        elements = json_spec["elements"]
        root_id = json_spec["root"]

        # Render component DOM recursively
        visited: Set[str] = set()

        def _render_element(node_id: str) -> str:
            if node_id in visited:
                return f'<div class="error-node">Circular reference: {html.escape(node_id)}</div>'
            visited.add(node_id)

            if node_id not in elements:
                return (
                    f'<div class="skeleton-shimmer" data-id="{html.escape(node_id)}">'
                    f'<span>⏳ Loading {html.escape(node_id)}...</span></div>'
                )

            elem = elements[node_id]
            comp_type = elem["type"]
            props = elem.get("props", {})
            children_ids = elem.get("children", [])

            rendered_children = "".join(_render_element(ch_id) for ch_id in children_ids)

            if comp_type == "Stack":
                direction = props.get("direction", "column")
                dir_class = "stack-row" if direction == "row" else "stack-col"
                return f'<div class="oui-stack {dir_class}" id="{html.escape(node_id)}">{rendered_children}</div>'

            elif comp_type == "Card":
                card_title = html.escape(str(props.get("title", "")))
                desc = html.escape(str(props.get("description", "")))
                header_html = f'<div class="card-header"><h3 class="card-title">{card_title}</h3>'
                if desc:
                    header_html += f'<p class="card-desc">{desc}</p>'
                header_html += '</div>'
                return (
                    f'<div class="oui-card" id="{html.escape(node_id)}">'
                    f'{header_html}'
                    f'<div class="card-body">{rendered_children}</div>'
                    f'</div>'
                )

            elif comp_type == "Metric":
                label = html.escape(str(props.get("label", "")))
                val = html.escape(str(props.get("value", "")))
                change = str(props.get("change", ""))
                badge_html = ""
                if change:
                    is_pos = change.startswith("+")
                    badge_class = "badge-positive" if is_pos else "badge-negative"
                    badge_html = f'<span class="metric-badge {badge_class}">{html.escape(change)}</span>'
                return (
                    f'<div class="oui-metric" id="{html.escape(node_id)}">'
                    f'<div class="metric-label">{label}</div>'
                    f'<div class="metric-row">'
                    f'<div class="metric-value">{val}</div>'
                    f'{badge_html}'
                    f'</div>'
                    f'</div>'
                )

            elif comp_type == "Table":
                columns = props.get("columns", [])
                rows = props.get("rows", [])
                th_html = "".join(f'<th>{html.escape(str(c))}</th>' for c in columns)
                tr_html = ""
                for row in rows:
                    td_html = "".join(f'<td>{html.escape(str(cell))}</td>' for cell in row)
                    tr_html += f'<tr>{td_html}</tr>'
                return (
                    f'<div class="table-container" id="{html.escape(node_id)}">'
                    f'<table class="oui-table">'
                    f'<thead><tr>{th_html}</tr></thead>'
                    f'<tbody>{tr_html}</tbody>'
                    f'</table>'
                    f'</div>'
                )

            elif comp_type == "Button":
                btn_label = html.escape(str(props.get("label", "Click")))
                action_name = html.escape(str(props.get("action", "")))
                variant = props.get("variant", "primary")
                return (
                    f'<button class="oui-button btn-{html.escape(variant)}" data-action="{action_name}" '
                    f'onclick="handleAction(\'{action_name}\')">{btn_label}</button>'
                )

            elif comp_type == "TextField":
                tf_label = html.escape(str(props.get("label", "")))
                tf_val = html.escape(str(props.get("value", "")))
                placeholder = html.escape(str(props.get("placeholder", "")))
                return (
                    f'<div class="oui-field">'
                    f'<label class="field-label">{tf_label}</label>'
                    f'<input type="text" class="field-input" value="{tf_val}" placeholder="{placeholder}" />'
                    f'</div>'
                )

            elif comp_type == "Text":
                content = html.escape(str(props.get("content", "")))
                return f'<p class="oui-text" id="{html.escape(node_id)}">{content}</p>'

            elif comp_type == "HtmlArtifact":
                doc_title = html.escape(str(props.get("title", "Artifact Sandbox")))
                doc_content = str(props.get("document", ""))
                # In sandboxed iframe
                escaped_srcdoc = html.escape(doc_content, quote=True)
                return (
                    f'<div class="oui-artifact-container" id="{html.escape(node_id)}">'
                    f'<div class="artifact-header">🛡️ <span>{doc_title}</span> <span class="badge-tag">Sandboxed</span></div>'
                    f'<iframe sandbox="allow-scripts" class="artifact-frame" srcdoc="{escaped_srcdoc}"></iframe>'
                    f'</div>'
                )

            elif comp_type == "Skeleton":
                placeholder_id = html.escape(str(props.get("placeholderId", node_id)))
                return (
                    f'<div class="skeleton-shimmer" id="{html.escape(node_id)}">'
                    f'<span>⏳ Loading <strong>{placeholder_id}</strong>...</span>'
                    f'</div>'
                )

            else:
                # Custom or unknown component
                props_summary = ", ".join(f"{k}={v}" for k, v in props.items())
                return (
                    f'<div class="oui-custom-node" id="{html.escape(node_id)}">'
                    f'<div class="custom-badge">&lt;{html.escape(comp_type)} /&gt;</div>'
                    f'<div class="custom-props">{html.escape(props_summary)}</div>'
                    f'<div class="custom-children">{rendered_children}</div>'
                    f'</div>'
                )

        body_content = _render_element(root_id) if root_id in elements else '<div class="empty">No content</div>'

        # Full HTML document with strict CSP
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' data:;">
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --success: #10b981;
      --danger: #ef4444;
      --radius: 8px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 24px;
      line-height: 1.5;
    }}
    .oui-stack {{ display: flex; gap: 16px; }}
    .stack-col {{ flex-direction: column; }}
    .stack-row {{ flex-direction: row; flex-wrap: wrap; }}
    .oui-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }}
    .card-header {{ margin-bottom: 14px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
    .card-title {{ font-size: 1.15rem; font-weight: 600; color: #e2e8f0; }}
    .card-desc {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 4px; }}
    .card-body {{ display: flex; flex-direction: column; gap: 12px; }}
    .oui-metric {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px;
      min-width: 180px;
      flex: 1;
    }}
    .metric-label {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }}
    .metric-row {{ display: flex; align-items: baseline; gap: 10px; margin-top: 6px; }}
    .metric-value {{ font-size: 1.75rem; font-weight: 700; color: #fff; }}
    .metric-badge {{
      font-size: 0.75rem;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
    }}
    .badge-positive {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}
    .badge-negative {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
    .table-container {{ overflow-x: auto; }}
    .oui-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      text-align: left;
    }}
    .oui-table th {{
      background: rgba(255, 255, 255, 0.05);
      padding: 10px 14px;
      border-bottom: 2px solid var(--border);
      color: var(--text-muted);
    }}
    .oui-table td {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
    }}
    .oui-button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 6px;
      padding: 8px 16px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s ease;
    }}
    .oui-button:hover {{ background: var(--primary-hover); }}
    .oui-field {{ display: flex; flex-direction: column; gap: 6px; }}
    .field-label {{ font-size: 0.85rem; color: var(--text-muted); }}
    .field-input {{
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 12px;
      color: white;
      font-size: 0.9rem;
    }}
    .oui-artifact-container {{
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      margin-top: 10px;
    }}
    .artifact-header {{
      background: rgba(255, 255, 255, 0.05);
      padding: 8px 12px;
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .badge-tag {{
      background: #475569;
      color: #cbd5e1;
      font-size: 0.7rem;
      padding: 2px 6px;
      border-radius: 3px;
    }}
    .artifact-frame {{
      width: 100%;
      height: 280px;
      border: none;
      background: white;
    }}
    .skeleton-shimmer {{
      background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      padding: 16px;
      border-radius: var(--radius);
      color: #cbd5e1;
      font-size: 0.85rem;
    }}
    @keyframes shimmer {{
      0% {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}
    .oui-custom-node {{
      border: 1px dashed var(--border);
      border-radius: var(--radius);
      padding: 12px;
    }}
    .custom-badge {{ font-size: 0.75rem; color: #a855f7; font-weight: 600; }}
  </style>
</head>
<body>
  {body_content}
  <script>
    function handleAction(actionName) {{
      console.log("[OpenUI Action]", actionName);
      if (window.parent && window.parent !== window) {{
        window.parent.postMessage({{ type: "action", action: actionName }}, "*");
      }}
    }}
  </script>
</body>
</html>
"""


def compile_to_json_spec(program: OpenUIProgram) -> Dict[str, Any]:
    """Convenience helper to compile AST to JSON spec."""
    return OpenUICompiler(program).to_json_spec()


def compile_to_react_tree(program: OpenUIProgram) -> Dict[str, Any]:
    """Convenience helper to compile AST to React component tree."""
    return OpenUICompiler(program).to_react_tree()


def compile_to_html(program: OpenUIProgram, title: str = "OpenUI Interface") -> str:
    """Convenience helper to compile AST to HTML."""
    return OpenUICompiler(program).to_html(title=title)
