"""Multi-Target Renderers for JSON Render: TerminalRenderer & DomRenderer.

Renders flat element specifications into:
1. Terminal console via Rich (panels, tables, columns, metric badges, ASCII bar charts).
2. Web browser via DomRenderer (modern responsive HTML5/CSS3 document with strict CSP and XSS sanitization).
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SELF = Path(__file__).resolve().parent
if str(_SELF) not in sys.path:
    sys.path.insert(0, str(_SELF))

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text
from rich.columns import Columns

try:
    from .catalog import ElementNode, JSONRenderSpec
except (ImportError, ValueError):
    from catalog import ElementNode, JSONRenderSpec



class TerminalRenderer:
    """Renders flat JSON Render element specs into rich ANSI terminal layouts."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def render_element(self, spec: JSONRenderSpec, element_id: str) -> RenderableType:
        """Recursively renders an element and its children into Rich renderables."""
        if element_id not in spec.elements:
            return Text(f"[Missing element: {element_id}]", style="bold red")

        node = spec.elements[element_id]
        node_type = node.type
        props = node.props
        children = node.children

        if node_type == "Container":
            child_renderables = [self.render_element(spec, cid) for cid in children]
            direction = props.get("direction", "column")
            if direction == "row" and child_renderables:
                return Columns(child_renderables, equal=True)
            elif child_renderables:
                # Column: stack vertically inside a panel
                t = RichTable.grid(padding=1)
                for cr in child_renderables:
                    t.add_row(cr)
                return t
            return Text("[Empty Container]", style="dim")

        elif node_type == "Card":
            child_renderables = [self.render_element(spec, cid) for cid in children]
            title = props.get("title", "Card")
            subtitle = props.get("subtitle")
            variant = props.get("variant", "default")
            border_colors = {"default": "blue", "primary": "cyan", "secondary": "magenta", "accent": "yellow", "danger": "red"}
            border_color = border_colors.get(variant, "blue")

            header_text = Text()
            header_text.append(title, style="bold white")
            if subtitle:
                header_text.append(f"\n{subtitle}", style="dim")

            content_table = RichTable.grid(padding=1)
            content_table.add_row(header_text)
            content_table.add_row(Text("─" * 40, style="dim"))
            for cr in child_renderables:
                content_table.add_row(cr)

            return Panel(content_table, border_style=border_color)

        elif node_type == "Metric":
            label = props.get("label", "Metric")
            val = str(props.get("value", "—"))
            delta = props.get("delta")
            trend = props.get("trend")

            txt = Text()
            txt.append(f"{label.upper()}\n", style="dim cyan")
            txt.append(f"{val} ", style="bold white")

            if delta:
                arrow = "▲ " if trend == "up" else ("▼ " if trend == "down" else "")
                color = "green" if trend == "up" else ("red" if trend == "down" else "yellow")
                txt.append(f" {arrow}{delta}", style=f"bold {color}")

            return Panel(txt, border_style="cyan", padding=(0, 2))

        elif node_type == "Table":
            columns = props.get("columns", [])
            rows = props.get("rows", [])
            table = RichTable(border_style="blue", show_header=True, header_style="bold cyan")
            for col in columns:
                table.add_column(str(col))
            for row in rows:
                table.add_row(*[str(c) for c in row])
            return table

        elif node_type == "Button":
            lbl = props.get("label", "Button")
            act = props.get("action", "action")
            var = props.get("variant", "default")
            color = "green" if var == "primary" else ("red" if var == "danger" else "yellow")
            return Panel(Text(f"[ {lbl} ] -> {act}", style=f"bold {color}"), border_style=color, padding=(0, 1))

        elif node_type == "Chart":
            title = props.get("title", "Chart")
            data = props.get("data", {})
            chart_table = RichTable(title=f"📊 {title}", border_style="magenta", show_header=True)
            chart_table.add_column("Category", style="bold cyan")
            chart_table.add_column("Value", style="bold yellow")
            chart_table.add_column("Visual Bar", style="green")

            max_val = max([v for v in data.values() if isinstance(v, (int, float))] or [1])
            for cat, val in data.items():
                if isinstance(val, (int, float)):
                    bar_len = int((val / max_val) * 20) if max_val > 0 else 0
                    bar_str = "█" * bar_len
                else:
                    bar_str = ""
                chart_table.add_row(str(cat), str(val), bar_str)
            return chart_table

        elif node_type == "CustomCodeBlock":
            code = props.get("code", "")
            title = props.get("title", "Dynamic Code")
            return Panel(Text(code, style="green"), title=f"⚡ {title}", border_style="green")

        elif node_type == "Header":
            title = props.get("title", "Header")
            subtitle = props.get("subtitle")
            t = Text(title, style="bold cyan")
            if subtitle:
                t.append(f" — {subtitle}", style="dim")
            return Panel(t, border_style="cyan")

        elif node_type == "Placeholder":
            text_str = props.get("text", "Loading generative content...")
            return Panel(Text(f"[ {text_str} ]", style="dim yellow"), border_style="dim")

        return Text(f"[{node_type}: {props}]", style="white")

    def render(self, spec: JSONRenderSpec) -> None:
        """Renders complete document spec to the console."""
        if not spec.root:
            self.console.print("[dim]Empty document spec (no root element)[/dim]")
            return
        root_renderable = self.render_element(spec, spec.root)
        self.console.print(root_renderable)


class DomRenderer:
    """Renders flat JSON Render element specs into responsive HTML5 documents with strict CSP & XSS escaping."""

    def render_container(self, props: Dict[str, Any], children_html: str) -> str:
        """Renders Container component with escaped CSS properties."""
        direction = props.get("direction", "column")
        flex_dir = "row" if direction == "row" else "column"
        raw_gap = str(props.get("gap", "16px"))
        escaped_gap = html.escape(raw_gap, quote=True)
        return (
            f'<div class="container" style="display:flex; flex-direction:{flex_dir}; gap:{escaped_gap};">'
            f'{children_html}</div>'
        )

    def render_card(self, props: Dict[str, Any], children_html: str) -> str:
        """Renders Card component with escaped title, subtitle, and variant."""
        title = html.escape(str(props.get("title", "Card")), quote=True)
        raw_subtitle = props.get("subtitle")
        subtitle_html = (
            f'<div class="subtitle">{html.escape(str(raw_subtitle), quote=True)}</div>'
            if raw_subtitle
            else ""
        )
        variant = html.escape(str(props.get("variant", "default")), quote=True)
        return f"""<div class="card card-{variant}">
  <div class="card-header">
    <h3>{title}</h3>
    {subtitle_html}
  </div>
  <div class="card-body">{children_html}</div>
</div>"""

    def render_metric(self, props: Dict[str, Any]) -> str:
        """Renders Metric component with escaped label, value, delta, and trend."""
        label = html.escape(str(props.get("label", "Metric")), quote=True)
        val = html.escape(str(props.get("value", "—")), quote=True)
        delta = props.get("delta")
        trend = props.get("trend")
        delta_html = ""
        if delta:
            escaped_delta = html.escape(str(delta), quote=True)
            arrow = "▲ " if trend == "up" else ("▼ " if trend == "down" else "")
            delta_class = f"trend-{html.escape(str(trend), quote=True)}" if trend else "trend-neutral"
            delta_html = f'<span class="metric-delta {delta_class}">{arrow}{escaped_delta}</span>'
        return f"""<div class="metric-box">
  <div class="metric-label">{label}</div>
  <div class="metric-value">{val} {delta_html}</div>
</div>"""

    def render_table(self, props: Dict[str, Any]) -> str:
        """Renders Table component with escaped column headers and cell values."""
        columns = props.get("columns", [])
        rows = props.get("rows", [])
        th_cells = "".join([f"<th>{html.escape(str(col), quote=True)}</th>" for col in columns])
        tr_rows = "".join([
            "<tr>" + "".join([f"<td>{html.escape(str(cell), quote=True)}</td>" for cell in row]) + "</tr>"
            for row in rows
        ])
        return f"""<table class="data-table">
  <thead><tr>{th_cells}</tr></thead>
  <tbody>{tr_rows}</tbody>
</table>"""

    def render_button(self, props: Dict[str, Any]) -> str:
        """Renders Button component with escaped caption, action target, and variant."""
        lbl = html.escape(str(props.get("label", "Button")), quote=True)
        act = html.escape(str(props.get("action", "action")), quote=True)
        var = html.escape(str(props.get("variant", "default")), quote=True)
        return f'<button class="btn btn-{var}" data-action="{act}">{lbl}</button>'

    def render_chart(self, props: Dict[str, Any]) -> str:
        """Renders Chart component with escaped title, categories, and values."""
        title = html.escape(str(props.get("title", "Chart")), quote=True)
        data = props.get("data", {})
        bars = "".join([
            f'<div class="bar-row"><span>{html.escape(str(cat), quote=True)}</span>'
            f'<div class="bar" style="width:{min(100, int(val * 2))}px"></div>'
            f'<span>{html.escape(str(val), quote=True)}</span></div>'
            for cat, val in data.items() if isinstance(val, (int, float))
        ])
        return f"""<div class="chart-card">
  <h4>{title}</h4>
  <div class="chart-body">{bars}</div>
</div>"""

    def render_custom_code_block(self, props: Dict[str, Any]) -> str:
        """Renders CustomCodeBlock with code escaped to prevent markup execution."""
        code = html.escape(str(props.get("code", "")), quote=True)
        return f'<pre class="code-block"><code>{code}</code></pre>'

    def render_header(self, props: Dict[str, Any]) -> str:
        """Renders Header component with escaped title and subtitle."""
        title = html.escape(str(props.get("title", "Header")), quote=True)
        raw_sub = props.get("subtitle")
        subtitle = (
            f'<span class="subtitle"> — {html.escape(str(raw_sub), quote=True)}</span>'
            if raw_sub
            else ""
        )
        return f'<div class="header-banner"><h2>{title}{subtitle}</h2></div>'

    def render_placeholder(self, props: Dict[str, Any]) -> str:
        """Renders Placeholder component with escaped text."""
        text_str = html.escape(str(props.get("text", "Loading generative content...")), quote=True)
        return f'<div class="placeholder-box"><span class="spinner">⏳</span> {text_str}</div>'

    def render_element_html(self, spec: JSONRenderSpec, element_id: str) -> str:
        """Recursively compiles element into HTML markup string."""
        if element_id not in spec.elements:
            escaped_id = html.escape(str(element_id), quote=True)
            return f'<div class="error">Missing element: {escaped_id}</div>'

        node = spec.elements[element_id]
        node_type = node.type
        props = node.props
        children_html = "".join([self.render_element_html(spec, cid) for cid in node.children])

        if node_type == "Container":
            return self.render_container(props, children_html)
        elif node_type == "Card":
            return self.render_card(props, children_html)
        elif node_type == "Metric":
            return self.render_metric(props)
        elif node_type == "Table":
            return self.render_table(props)
        elif node_type == "Button":
            return self.render_button(props)
        elif node_type == "Chart":
            return self.render_chart(props)
        elif node_type == "CustomCodeBlock":
            return self.render_custom_code_block(props)
        elif node_type == "Header":
            return self.render_header(props)
        elif node_type == "Placeholder":
            return self.render_placeholder(props)

        return f'<div class="node">{children_html}</div>'

    def render_html(self, spec: JSONRenderSpec) -> str:
        """Compiles specification into full standalone HTML document with strict CSP."""
        return self.render(spec)

    def render(self, spec: JSONRenderSpec) -> str:
        """Returns complete standalone HTML document with strict Content Security Policy."""
        body_content = self.render_element_html(spec, spec.root) if spec.root else "<div>Empty Spec</div>"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'none';">
<title>JSON Render Multi-Target View</title>
<style>
  :root {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; }}
  body {{ margin: 0; padding: 24px; box-sizing: border-box; }}
  .card {{ background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }}
  .card-primary {{ border-left: 4px solid #38bdf8; }}
  .card-accent {{ border-left: 4px solid #facc15; }}
  .card-header h3 {{ margin: 0 0 4px 0; color: #f8fafc; }}
  .subtitle {{ font-size: 13px; color: #94a3b8; }}
  .metric-box {{ background: #0f172a; border-radius: 8px; padding: 14px 18px; border: 1px solid #334155; min-width: 140px; }}
  .metric-label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.05em; }}
  .metric-value {{ font-size: 24px; font-weight: bold; color: #f8fafc; margin-top: 4px; display: flex; align-items: center; gap: 8px; }}
  .trend-up {{ color: #4ade80; font-size: 14px; }}
  .trend-down {{ color: #f87171; font-size: 14px; }}
  .data-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
  .data-table th, .data-table td {{ text-align: left; padding: 10px 14px; border-bottom: 1px solid #334155; }}
  .data-table th {{ background: #0f172a; color: #38bdf8; }}
  .btn {{ padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; border: none; font-size: 13px; transition: background 0.2s; }}
  .btn-primary {{ background: #38bdf8; color: #0f172a; }}
  .btn-default {{ background: #334155; color: #f8fafc; }}
  .chart-card {{ background: #0f172a; border-radius: 8px; padding: 14px; border: 1px solid #334155; }}
  .bar-row {{ display: flex; align-items: center; gap: 10px; margin: 6px 0; font-size: 12px; }}
  .bar {{ height: 16px; background: #38bdf8; border-radius: 3px; }}
  .code-block {{ background: #020617; padding: 14px; border-radius: 8px; font-family: monospace; color: #4ade80; overflow-x: auto; }}
</style>
</head>
<body>
<div id="root-container">
{body_content}
</div>
</body>
</html>"""
