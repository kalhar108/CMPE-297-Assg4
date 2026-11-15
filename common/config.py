"""Configuration and execution mode management for GenUX technologies.

Supports automatic sensing of live API keys (Google Gemini / OpenAI) with seamless,
deterministic offline mock fallback when keys are absent or when --mock is requested.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class ExecutionMode(str, Enum):
    """Execution modes for GenUX components."""
    LIVE = "live"
    MOCK = "mock"
    AUTO = "auto"


class GenUXExecutionConfig(BaseModel):
    """Configuration model for GenUX execution engine."""
    mode: Literal["mock", "live", "auto"] = Field(
        default="auto",
        description="Execution mode: 'auto' (senses API keys), 'mock' (offline), 'live' (frontier LLM)",
    )
    model_name: str = Field(
        default="gemini-3.8-flash",
        description="Model name to use in live mode (defaults to gemini-3.8-flash or env HARNESS_MODEL)",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Optional explicit API key; if None, detects GOOGLE_API_KEY / GEMINI_API_KEY from environment",
    )
    temperature: float = Field(
        default=0.2,
        description="Sampling temperature for live model calls",
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        # Check for model name in environment if default
        if self.model_name == "gemini-3.8-flash" and os.environ.get("HARNESS_MODEL"):
            self.model_name = os.environ["HARNESS_MODEL"]

    def get_api_key(self) -> Optional[str]:
        """Resolves the active API key from instance or environment."""
        if self.api_key:
            return self.api_key
        return (
            os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("API_KEY")
        )

    def resolved_mode(self) -> Literal["live", "mock"]:
        """Resolves the operational mode to either 'live' or 'mock'."""
        if self.mode == "mock":
            return "mock"
        if self.mode == "live":
            return "live"

        # Check environment flag override
        env_mode = os.environ.get("GENUX_MODE", "").lower().strip()
        if env_mode in ("mock", "offline"):
            return "mock"
        if env_mode == "live":
            return "live"

        # Auto-sense available API keys
        key = self.get_api_key()
        if key and len(key.strip()) > 10:
            return "live"
        return "mock"

    def print_banner(self, console: Optional[Console] = None) -> None:
        """Prints a rich banner communicating active execution mode and provider status."""
        c = console or Console()
        active_mode = self.resolved_mode()

        if active_mode == "mock":
            text = Text()
            text.append("[GenUX Engine] Running in ", style="bold cyan")
            text.append("DETERMINISTIC OFFLINE MOCK", style="bold yellow")
            text.append(" mode\n", style="bold cyan")
            text.append("  Reason: ", style="bold white")
            text.append("No API key found or --mock requested\n", style="dim")
            text.append("  Network: ", style="bold white")
            text.append("DISABLED (0 network traffic, 100% deterministic schema output)", style="green")
            panel = Panel(
                text,
                title="[bold yellow]Offline Execution Engine[/bold yellow]",
                border_style="yellow",
            )
            c.print(panel)
        else:
            text = Text()
            text.append("[GenUX Engine] Running in ", style="bold cyan")
            text.append("LIVE API", style="bold green")
            text.append(" mode\n", style="bold cyan")
            text.append("  Provider: ", style="bold white")
            text.append(f"Google Gemini ({self.model_name})\n", style="green")
            text.append("  Endpoint: ", style="bold white")
            text.append("Authenticated via GOOGLE_API_KEY / GEMINI_API_KEY", style="dim")
            panel = Panel(
                text,
                title="[bold green]Live LLM Execution Engine[/bold green]",
                border_style="green",
            )
            c.print(panel)
