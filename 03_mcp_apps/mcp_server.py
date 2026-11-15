"""FastMCP Server implementation conforming to Model Context Protocol SEP-1865 (MCP Apps).

Exposes tools returning dual output:
1. `content`: Plain text summary for LLM context.
2. `structuredContent`: JSON payload for frontend webviews.
3. `_meta`: UI resource link (`ui://...`) and CSP declarations.

Also registers UI resources with MIME type 'text/html;profile=mcp-app'.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional
from pydantic import AnyUrl

from mcp.server.fastmcp import FastMCP
import mcp.types as types


def create_lemonade_mcp_server() -> FastMCP:
    """Instantiates and configures a FastMCP server supporting SEP-1865 MCP Apps."""
    mcp = FastMCP(
        name="Lemonade-Stand-SEP1865",
        instructions="MCP Apps server demonstrating SEP-1865 interactive UI resources.",
    )

    # In-memory inventory and sales state
    state = {
        "inventory": {"lemons": 48, "sugar_kg": 12.5, "ice_bags": 8, "cups": 120},
        "sales": {"daily_revenue": 342.50, "cups_sold": 137, "avg_rating": 4.8},
        "weather": {"condition": "Sunny", "temp_f": 82.0, "forecast": "Warm and dry"},
    }

    # --------------------------------------------------------------------------
    # 1. Static Mode Tool & Resource
    # --------------------------------------------------------------------------
    @mcp.tool(name="get_lemonade_dashboard", description="Fetch live lemonade stand KPIs, inventory, and sales dashboard.")
    def get_lemonade_dashboard() -> types.CallToolResult:
        """Returns dual-output payload linking to ui://lemonade-stand/dashboard.html."""
        text_summary = (
            f"Lemonade Stand Status: Revenue ${state['sales']['daily_revenue']:.2f}, "
            f"Cups Sold: {state['sales']['cups_sold']}, Temp: {state['weather']['temp_f']}°F. "
            f"Inventory: {state['inventory']['lemons']} lemons, {state['inventory']['sugar_kg']}kg sugar, "
            f"{state['inventory']['ice_bags']} bags of ice."
        )

        structured_data = {
            "title": "Fresh Squeeze Lemonade — Operational Dashboard",
            "metrics": {
                "daily_revenue": state["sales"]["daily_revenue"],
                "cups_sold": state["sales"]["cups_sold"],
                "rating": state["sales"]["avg_rating"],
                "temperature_f": state["weather"]["temp_f"],
                "weather": state["weather"]["condition"],
            },
            "inventory": state["inventory"],
            "timestamp": "2026-11-05T20:00:00Z",
        }

        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text_summary)],
            structuredContent=structured_data,
            meta={
                "ui": {
                    "resourceUri": "ui://lemonade-stand/dashboard.html",
                    "csp": {
                        "connectDomains": [],
                        "resourceDomains": [],
                    },
                }
            },
        )

    @mcp.resource("ui://lemonade-stand/dashboard.html", mime_type="text/html;profile=mcp-app")
    def get_dashboard_html() -> str:
        """Pre-compiled static UI resource for lemonade stand dashboard."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src data:;">
<title>Fresh Squeeze Lemonade Dashboard</title>
<style>
  :root { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; }
  body { margin: 0; padding: 20px; box-sizing: border-box; }
  .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; margin-bottom: 16px; }
  .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 16px; }
  .metric-box { background: #0f172a; border-radius: 8px; padding: 14px; border-left: 4px solid #facc15; }
  .metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
  .metric-val { font-size: 24px; font-weight: bold; color: #f8fafc; margin-top: 4px; }
  .inventory-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  .inventory-table th, .inventory-table td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #334155; font-size: 14px; }
  .badge { display: inline-block; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; background: #22c55e20; color: #4ade80; }
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h2 style="margin:0; color:#facc15;">🍋 Fresh Squeeze Lemonade Stand</h2>
    <span class="badge" id="status-badge">ONLINE • STAND 1</span>
  </div>
  <div class="grid">
    <div class="metric-box">
      <div class="metric-label">Daily Revenue</div>
      <div class="metric-val" id="rev-val">$342.50</div>
    </div>
    <div class="metric-box" style="border-left-color: #38bdf8;">
      <div class="metric-label">Cups Dispensed</div>
      <div class="metric-val" id="cups-val">137</div>
    </div>
    <div class="metric-box" style="border-left-color: #f97316;">
      <div class="metric-label">Ambient Temp</div>
      <div class="metric-val" id="temp-val">82°F</div>
    </div>
    <div class="metric-box" style="border-left-color: #a855f7;">
      <div class="metric-label">Customer Rating</div>
      <div class="metric-val" id="rating-val">4.8 ★</div>
    </div>
  </div>
  <h4 style="margin: 20px 0 8px 0; color:#cbd5e1;">Stock & Supplies</h4>
  <table class="inventory-table">
    <thead>
      <tr><th>Supply Item</th><th>In Stock</th><th>Status</th></tr>
    </thead>
    <tbody>
      <tr><td>Fresh Lemons</td><td id="inv-lemons">48 units</td><td><span class="badge">Healthy</span></td></tr>
      <tr><td>Organic Sugar</td><td id="inv-sugar">12.5 kg</td><td><span class="badge">Healthy</span></td></tr>
      <tr><td>Crushed Ice</td><td id="inv-ice">8 bags</td><td><span class="badge">Healthy</span></td></tr>
      <tr><td>Compostable Cups</td><td id="inv-cups">120 units</td><td><span class="badge">Healthy</span></td></tr>
    </tbody>
  </table>
</div>
<script>
  window.addEventListener('message', (event) => {
    if (!event.data || event.data.type !== 'MCP_DATA_UPDATE') return;
    const d = event.data.payload;
    if (d && d.metrics) {
      if (d.metrics.daily_revenue) document.getElementById('rev-val').textContent = '$' + d.metrics.daily_revenue.toFixed(2);
      if (d.metrics.cups_sold) document.getElementById('cups-val').textContent = d.metrics.cups_sold;
      if (d.metrics.temperature_f) document.getElementById('temp-val').textContent = d.metrics.temperature_f + '°F';
    }
  });
</script>
</body>
</html>"""

    # --------------------------------------------------------------------------
    # 2. Declarative Mode Tool & Schema-Driven Form Resource
    # --------------------------------------------------------------------------
    @mcp.tool(
        name="order_supplies",
        description="Order additional lemonade supplies (lemons, sugar, ice, cups) with optional rush delivery.",
    )
    def order_supplies(
        lemons: int = 24,
        sugar_kg: float = 5.0,
        ice_bags: int = 4,
        cups: int = 50,
        rush_delivery: bool = False,
    ) -> types.CallToolResult:
        """Executes supply re-order, updates state, and returns dual payload."""
        # Update in-memory state
        state["inventory"]["lemons"] += lemons
        state["inventory"]["sugar_kg"] += sugar_kg
        state["inventory"]["ice_bags"] += ice_bags
        state["inventory"]["cups"] += cups

        unit_cost = (lemons * 0.40) + (sugar_kg * 1.50) + (ice_bags * 2.00) + (cups * 0.10)
        shipping = 15.00 if rush_delivery else 5.00
        total_cost = unit_cost + shipping

        summary_text = (
            f"Supply Order Placed: {lemons} lemons, {sugar_kg}kg sugar, {ice_bags} bags of ice, "
            f"{cups} cups. Rush delivery: {rush_delivery}. Total cost: ${total_cost:.2f}. "
            f"New inventory totals: {state['inventory']['lemons']} lemons."
        )

        receipt = {
            "order_id": f"ORD-{state['sales']['cups_sold'] + 100}",
            "items": {
                "lemons": lemons,
                "sugar_kg": sugar_kg,
                "ice_bags": ice_bags,
                "cups": cups,
            },
            "rush_delivery": rush_delivery,
            "cost": {
                "subtotal": round(unit_cost, 2),
                "shipping": shipping,
                "total": round(total_cost, 2),
            },
            "updated_inventory": state["inventory"],
        }

        return types.CallToolResult(
            content=[types.TextContent(type="text", text=summary_text)],
            structuredContent=receipt,
            meta={
                "ui": {
                    "resourceUri": "ui://forms/dynamic_form.html",
                    "csp": {"connectDomains": [], "resourceDomains": []},
                }
            },
        )

    @mcp.resource("ui://forms/dynamic_form.html", mime_type="text/html;profile=mcp-app")
    def get_dynamic_form_html() -> str:
        """Schema-driven declarative form resource. Renders fields matching tool JSON schemas."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src data:;">
<title>Dynamic MCP App Form</title>
<style>
  body { margin: 0; padding: 20px; font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; }
  .form-card { background: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; }
  .field { margin-bottom: 14px; }
  label { display: block; font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 6px; }
  input[type="number"], input[type="text"] { width: 100%; box-sizing: border-box; padding: 8px 12px; background: #0f172a; border: 1px solid #475569; border-radius: 6px; color: #f8fafc; font-size: 14px; }
  .checkbox-field { display: flex; align-items: center; gap: 8px; }
  .checkbox-field label { margin: 0; }
  button { background: #facc15; color: #854d0e; border: none; font-weight: bold; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-size: 14px; width: 100%; }
  button:hover { background: #eab308; }
  #order-result { margin-top: 16px; padding: 12px; border-radius: 6px; background: #0f172a; border-left: 4px solid #22c55e; display: none; font-size: 13px; }
</style>
</head>
<body>
<div class="form-card">
  <h3 style="margin-top:0; color:#facc15;">📦 Dynamic Supply Re-Order Form</h3>
  <p style="font-size:12px; color:#94a3b8;">Generated dynamically from MCP tool schema for <code>order_supplies</code>.</p>
  <form id="order-form">
    <div class="field">
      <label>Lemons (units):</label>
      <input type="number" id="lemons" value="30" min="1" max="500">
    </div>
    <div class="field">
      <label>Organic Sugar (kg):</label>
      <input type="number" id="sugar_kg" value="5.0" step="0.5" min="0.5">
    </div>
    <div class="field">
      <label>Ice (bags):</label>
      <input type="number" id="ice_bags" value="5" min="1">
    </div>
    <div class="field">
      <label>Cups (units):</label>
      <input type="number" id="cups" value="50" min="10">
    </div>
    <div class="field checkbox-field">
      <input type="checkbox" id="rush_delivery">
      <label for="rush_delivery">Rush 2-Hour Delivery (+$10)</label>
    </div>
    <button type="submit" id="submit-btn">Dispatch Order via PostMessage Bridge</button>
  </form>
  <div id="order-result"></div>
</div>
<script>
  const form = document.getElementById('order-form');
  const resultDiv = document.getElementById('order-result');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const args = {
      lemons: parseInt(document.getElementById('lemons').value, 10),
      sugar_kg: parseFloat(document.getElementById('sugar_kg').value),
      ice_bags: parseInt(document.getElementById('ice_bags').value, 10),
      cups: parseInt(document.getElementById('cups').value, 10),
      rush_delivery: document.getElementById('rush_delivery').checked
    };

    // Send JSON-RPC call-tool request to host window
    window.parent.postMessage({
      jsonrpc: "2.0",
      id: "req-" + Date.now(),
      method: "ui/call-tool",
      params: {
        name: "order_supplies",
        arguments: args
      }
    }, "*");
  });

  window.addEventListener('message', (event) => {
    if (!event.data) return;
    if (event.data.method === "ui/tool-result" || (event.data.result && event.data.result.structuredContent)) {
      const res = event.data.result || event.data.params;
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = '<strong>Order Confirmed:</strong> ' + JSON.stringify(res.structuredContent || res);
    }
  });
</script>
</body>
</html>"""

    # --------------------------------------------------------------------------
    # 3. Open-Ended Mode Tool & Resource
    # --------------------------------------------------------------------------
    @mcp.tool(
        name="generate_pricing_simulator",
        description="Generates an open-ended interactive pricing simulator app rendered in a sandboxed host iframe.",
    )
    def generate_pricing_simulator(
        base_price: float = 2.50,
        temp_f: float = 85.0,
        crowd_factor: float = 1.2,
    ) -> types.CallToolResult:
        """Returns dual-output linking to an unconstrained interactive HTML simulator."""
        expected_cups = int(max(10, (temp_f - 60) * 4 * crowd_factor / (base_price / 2.0)))
        expected_revenue = expected_cups * base_price
        summary_text = (
            f"Pricing Simulation: At ${base_price:.2f}/cup, {temp_f}°F, crowd multiplier {crowd_factor}x, "
            f"projected volume is {expected_cups} cups (${expected_revenue:.2f} gross revenue)."
        )

        structured_data = {
            "simulation": {
                "base_price": base_price,
                "temp_f": temp_f,
                "crowd_factor": crowd_factor,
                "projected_cups": expected_cups,
                "projected_revenue": round(expected_revenue, 2),
            }
        }

        return types.CallToolResult(
            content=[types.TextContent(type="text", text=summary_text)],
            structuredContent=structured_data,
            meta={
                "ui": {
                    "resourceUri": "ui://dynamic/pricing_sim.html",
                    "csp": {
                        "connectDomains": [],
                        "resourceDomains": [],
                    },
                }
            },
        )

    @mcp.resource("ui://dynamic/pricing_sim.html", mime_type="text/html;profile=mcp-app")
    def get_pricing_sim_html() -> str:
        """Open-ended interactive simulator with dynamic sliders and real-time computation."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src data:;">
<title>Lemonade Dynamic Pricing Simulator</title>
<style>
  body { margin: 0; padding: 20px; font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; }
  .sim-container { background: #1e293b; padding: 24px; border-radius: 12px; border: 1px solid #334155; }
  .slider-row { margin: 16px 0; }
  .slider-header { display: flex; justify-content: space-between; font-size: 13px; color: #94a3b8; margin-bottom: 4px; }
  input[type="range"] { width: 100%; accent-color: #facc15; }
  .output-panel { background: #0f172a; border-radius: 8px; padding: 16px; margin-top: 20px; border-left: 4px solid #facc15; display: flex; justify-content: space-around; }
  .stat { text-align: center; }
  .stat-val { font-size: 26px; font-weight: bold; color: #facc15; }
  .stat-label { font-size: 12px; color: #94a3b8; }
</style>
</head>
<body>
<div class="sim-container">
  <h3 style="margin-top:0; color:#facc15;">📊 Open-Ended Dynamic Pricing Lab</h3>
  <div class="slider-row">
    <div class="slider-header"><span>Cup Price ($)</span><span id="price-lbl">$2.50</span></div>
    <input type="range" id="price-slider" min="1.0" max="5.0" step="0.25" value="2.50">
  </div>
  <div class="slider-row">
    <div class="slider-header"><span>Weather Temp (°F)</span><span id="temp-lbl">85°F</span></div>
    <input type="range" id="temp-slider" min="65" max="105" step="1" value="85">
  </div>
  <div class="slider-row">
    <div class="slider-header"><span>Foot Traffic Factor</span><span id="traffic-lbl">1.2x</span></div>
    <input type="range" id="traffic-slider" min="0.5" max="2.5" step="0.1" value="1.2">
  </div>
  <div class="output-panel">
    <div class="stat">
      <div class="stat-val" id="cups-proj">120</div>
      <div class="stat-label">Projected Cups</div>
    </div>
    <div class="stat">
      <div class="stat-val" id="rev-proj">$300.00</div>
      <div class="stat-label">Projected Revenue</div>
    </div>
  </div>
</div>
<script>
  const priceS = document.getElementById('price-slider');
  const tempS = document.getElementById('temp-slider');
  const trafficS = document.getElementById('traffic-slider');

  function update() {
    const p = parseFloat(priceS.value);
    const t = parseFloat(tempS.value);
    const tf = parseFloat(trafficS.value);
    document.getElementById('price-lbl').textContent = '$' + p.toFixed(2);
    document.getElementById('temp-lbl').textContent = t + '°F';
    document.getElementById('traffic-lbl').textContent = tf.toFixed(1) + 'x';

    const cups = Math.max(10, Math.round((t - 60) * 4 * tf / (p / 2.0)));
    const rev = cups * p;
    document.getElementById('cups-proj').textContent = cups;
    document.getElementById('rev-proj').textContent = '$' + rev.toFixed(2);

    // Notify host of context update
    window.parent.postMessage({
      jsonrpc: "2.0",
      id: "sim-" + Date.now(),
      method: "ui/update-model-context",
      params: { projected_cups: cups, projected_revenue: rev, cup_price: p }
    }, "*");
  }

  priceS.addEventListener('input', update);
  tempS.addEventListener('input', update);
  trafficS.addEventListener('input', update);
</script>
</body>
</html>"""

    # --------------------------------------------------------------------------
    # 4. Mixed Mode Tool & Nested Hybrid Resource
    # --------------------------------------------------------------------------
    @mcp.tool(
        name="mixed_lemonade_app",
        description="Hybrid MCP app delivering catalog KPI widgets alongside a nested sandboxed generative mini-app.",
    )
    def mixed_lemonade_app(scenario: str = "Campus Festival Rush") -> types.CallToolResult:
        """Returns structured catalog cards + nested generative HTML widget."""
        summary = f"Hybrid App initialized for scenario: {scenario}. Delivering catalog cards and nested interactive widget."

        catalog_components = [
            {"id": "card-header", "type": "Card", "props": {"title": f"Live Operations: {scenario}", "variant": "primary"}},
            {"id": "kpi-daily", "type": "Metric", "props": {"label": "Today's Target", "value": "$500.00"}},
            {"id": "kpi-pace", "type": "Metric", "props": {"label": "Current Pace", "value": "$342.50 (68%)"}},
        ]

        nested_generated_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
<style>
  body { margin:0; padding:12px; font-family:sans-serif; background:#020617; color:#38bdf8; text-align:center; }
  .btn { background:#38bdf8; color:#0f172a; border:none; padding:8px 14px; border-radius:6px; font-weight:bold; cursor:pointer; }
</style>
</head>
<body>
  <div style="font-size:13px; font-weight:bold; margin-bottom:8px;">⚡ Generative Flash Discount Spinner</div>
  <button class="btn" id="spin-btn">Spin 10-25% Flash Sale</button>
  <div id="spin-res" style="margin-top:8px; font-size:14px; color:#facc15;"></div>
  <script>
    document.getElementById('spin-btn').addEventListener('click', () => {
      const disc = Math.floor(Math.random() * 15) + 10;
      document.getElementById('spin-res').textContent = 'Applied: ' + disc + '% OFF NEXT 10 CUPS!';
      window.parent.postMessage({
        jsonrpc: '2.0',
        method: 'ui/update-model-context',
        params: { flash_discount: disc, active: true }
      }, '*');
    });
  </script>
</body>
</html>"""

        structured = {
            "scenario": scenario,
            "components": catalog_components,
            "generated": nested_generated_html,
        }

        return types.CallToolResult(
            content=[types.TextContent(type="text", text=summary)],
            structuredContent=structured,
            meta={
                "ui": {
                    "resourceUri": "ui://hybrid/mixed_app.html",
                    "csp": {"connectDomains": [], "resourceDomains": []},
                }
            },
        )

    @mcp.resource("ui://hybrid/mixed_app.html", mime_type="text/html;profile=mcp-app")
    def get_mixed_app_html() -> str:
        """Primary MCP App container hosting catalog widgets and a nested secondary iframe."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src data:;">
<title>Mixed Mode MCP App Container</title>
<style>
  body { margin:0; padding:20px; font-family:system-ui, sans-serif; background:#0f172a; color:#f8fafc; }
  .container { background:#1e293b; padding:20px; border-radius:12px; border:1px solid #334155; }
  .catalog-shell { display:flex; gap:12px; margin-bottom:16px; }
  .shell-card { background:#0f172a; padding:12px 18px; border-radius:8px; border-left:4px solid #38bdf8; flex:1; }
  .nested-frame-wrapper { border:1px dashed #64748b; border-radius:8px; padding:12px; background:#020617; }
  iframe { width:100%; height:130px; border:none; border-radius:6px; }
</style>
</head>
<body>
<div class="container">
  <h3 style="margin-top:0; color:#facc15;">🔀 Hybrid MCP App (Double Boundary Sandbox)</h3>
  <div class="catalog-shell">
    <div class="shell-card">
      <div style="font-size:11px; color:#94a3b8;">CATALOG KPI</div>
      <div style="font-size:20px; font-weight:bold;">$500.00 Target</div>
    </div>
    <div class="shell-card" style="border-left-color:#22c55e;">
      <div style="font-size:11px; color:#94a3b8;">PROGRESS</div>
      <div style="font-size:20px; font-weight:bold;">68.5% Achieved</div>
    </div>
  </div>
  <div class="nested-frame-wrapper">
    <div style="font-size:12px; color:#94a3b8; margin-bottom:6px;">Nested Secondary Sandbox Frame:</div>
    <iframe id="nested-gen-frame" sandbox="allow-scripts"></iframe>
  </div>
</div>
<script>
  window.addEventListener('message', (event) => {
    // Bubble up nested frame messages to the host window
    if (event.data && event.data.method === 'ui/update-model-context') {
      window.parent.postMessage(event.data, '*');
    }
    if (event.data && event.data.type === 'MOUNT_GENERATED_HTML') {
      const frame = document.getElementById('nested-gen-frame');
      frame.srcdoc = event.data.html;
    }
  });
</script>
</body>
</html>"""

    return mcp


class LemonadeMCPServer:
    """Wrapper class providing synchronous and asynchronous invocation helpers."""

    def __init__(self):
        self.fastmcp = create_lemonade_mcp_server()

    async def list_tools_async(self) -> List[Any]:
        return await self.fastmcp.list_tools()

    async def list_resources_async(self) -> List[Any]:
        return await self.fastmcp.list_resources()

    async def call_tool_async(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> types.CallToolResult:
        res = await self.fastmcp.call_tool(name, arguments or {})
        if isinstance(res, list) and len(res) > 0 and hasattr(res[0], "content"):
            return res[0]  # FastMCP wrapped result
        if isinstance(res, types.CallToolResult):
            return res
        return res

    def call_tool_sync(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> types.CallToolResult:
        return asyncio.run(self.call_tool_async(name, arguments))

    async def read_resource_async(self, uri: str) -> str:
        contents = await self.fastmcp.read_resource(AnyUrl(uri))
        if contents and len(contents) > 0:
            item = contents[0]
            if hasattr(item, "content"):
                return item.content
            if hasattr(item, "text"):
                return item.text
        return ""

    def read_resource_sync(self, uri: str) -> str:
        return asyncio.run(self.read_resource_async(uri))
