"""Dual-Mode LLM Provider abstraction for GenUX technologies.

Supports live Google Gemini generation via the modern `google-genai` SDK
and 100% deterministic, offline mock execution returning authentic,
schema-valid GenUX data structures without network dependencies.
"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional, Type, TypeVar

from pydantic import BaseModel

from .config import GenUXExecutionConfig
from .mock_data import (
    A2UI_DECLARATIVE_COMPONENTS,
    A2UI_MIXED_COMPONENTS_INITIAL,
    A2UI_OPEN_ENDED_COMPONENTS,
    A2UI_SELF_CORRECTED_COMPONENTS,
    A2UI_STATIC_COMPONENTS,
    AGUI_DECLARATIVE_PATCHES,
    AGUI_OPEN_ENDED_REASONING_CHUNKS,
    AGUI_STATIC_STATE_PATCHES,
)

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class BaseModelProvider(ABC):
    """Abstract base class for all GenUX LLM providers."""

    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generates plain text response synchronously."""
        pass

    @abstractmethod
    def generate_structured(
        self, prompt: str, schema: Type[T], system_instruction: Optional[str] = None
    ) -> T:
        """Generates a structured object validated against a Pydantic schema."""
        pass

    @abstractmethod
    def stream_patches(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        """Streams RFC 6902 JSON patch operations line by line."""
        pass

    @abstractmethod
    def stream_text(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Streams plain text chunks."""
        pass


class GeminiLiveProvider(BaseModelProvider):
    """Live LLM provider backed by Google Gemini via the `google-genai` SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.8-flash",
        temperature: float = 0.2,
    ) -> None:
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GeminiLiveProvider requires GOOGLE_API_KEY or GEMINI_API_KEY.")
        self.model_name = model_name
        self.temperature = temperature

        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text or ""

    def generate_structured(
        self, prompt: str, schema: Type[T], system_instruction: Optional[str] = None
    ) -> T:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        raw_text = response.text or "{}"
        return schema.model_validate_json(raw_text)

    def stream_patches(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        from google.genai import types

        system_instruction = (
            "You are an RFC 6902 JSON Patch streaming engine. "
            "Emit only individual JSON Patch operations, one per line (JSONL), "
            "with keys 'op', 'path', and 'value'."
        )
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
        )
        response_stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        buffer = ""
        for chunk in response_stream:
            text = chunk.text or ""
            buffer += text
            lines = buffer.split("\n")
            buffer = lines.pop()  # Keep incomplete last fragment in buffer
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        clean_line = re.sub(r"^```[a-z]*", "", line).replace("```", "").strip()
                        if clean_line:
                            yield json.loads(clean_line)
                    except json.JSONDecodeError:
                        continue

        if buffer.strip():
            try:
                clean = re.sub(r"^```[a-z]*", "", buffer.strip()).replace("```", "").strip()
                if clean:
                    yield json.loads(clean)
            except json.JSONDecodeError:
                pass

    def stream_text(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> Generator[str, None, None]:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
        )
        response_stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        for chunk in response_stream:
            text = chunk.text or ""
            if text:
                yield text


class DeterministicMockProvider(BaseModelProvider):
    """100% offline, deterministic mock provider returning schema-valid GenUX structures."""

    def __init__(self, model_name: str = "mock-deterministic-frontier") -> None:
        self.model_name = model_name

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        prompt_lower = prompt.lower()
        if "correct" in prompt_lower or "repair" in prompt_lower:
            return json.dumps(
                {"status": "repaired", "components": A2UI_SELF_CORRECTED_COMPONENTS}, indent=2
            )
        if "a2ui" in prompt_lower:
            return json.dumps(
                {"surfaceId": "surface-mock", "components": A2UI_DECLARATIVE_COMPONENTS}, indent=2
            )
        return (
            f"[DeterministicMockProvider] Synthesized offline response for prompt: "
            f"{prompt[:60]}... Generated 0 external network requests."
        )

    def generate_structured(
        self, prompt: str, schema: Type[T], system_instruction: Optional[str] = None
    ) -> T:
        """Returns authentic, schema-validated mock data conforming to the requested Pydantic schema."""
        prompt_lower = prompt.lower()

        # Check schema fields to tailor mock synthesis
        schema_fields = getattr(schema, "model_fields", {})

        # Scenario 1: A2UI UpdateComponentsPayload
        if "components" in schema_fields and "surfaceId" in schema_fields:
            if "correct" in prompt_lower or "repair" in prompt_lower or "malformed" in prompt_lower:
                data = {
                    "surfaceId": "surface-mixed-04",
                    "components": A2UI_SELF_CORRECTED_COMPONENTS,
                }
            elif "open_ended" in prompt_lower or "canvas" in prompt_lower or "neural" in prompt_lower:
                data = {
                    "surfaceId": "surface-openended-03",
                    "components": A2UI_OPEN_ENDED_COMPONENTS,
                }
            elif "mixed" in prompt_lower or "hybrid" in prompt_lower:
                data = {
                    "surfaceId": "surface-mixed-04",
                    "components": A2UI_MIXED_COMPONENTS_INITIAL,
                }
            elif "static" in prompt_lower:
                data = {
                    "surfaceId": "surface-contact-01",
                    "components": A2UI_STATIC_COMPONENTS,
                }
            else:
                data = {
                    "surfaceId": "surface-analytics-02",
                    "components": A2UI_DECLARATIVE_COMPONENTS,
                }
            return schema.model_validate(data)

        # Scenario 2: Generic dictionary or component list
        if "components" in schema_fields:
            data = {"components": A2UI_DECLARATIVE_COMPONENTS}
            return schema.model_validate(data)

        # Scenario 3: Fallback generic model instantiation with defaults
        # Attempt to instantiate with default fields or empty dict
        try:
            return schema.model_validate({})
        except Exception:
            # Construct dictionary with mock values for each field
            mock_dict: Dict[str, Any] = {}
            for field_name, field_info in schema_fields.items():
                if field_info.default is not None:
                    continue
                mock_dict[field_name] = f"mock_{field_name}"
            return schema.model_validate(mock_dict)

    def stream_patches(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        """Yields authentic RFC 6902 JSON patch operations offline."""
        prompt_lower = prompt.lower()
        if "declarative" in prompt_lower or "graph" in prompt_lower:
            patches = AGUI_DECLARATIVE_PATCHES
        else:
            patches = AGUI_STATIC_STATE_PATCHES

        for patch in patches:
            yield patch

    def stream_text(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Yields realistic streaming text tokens offline."""
        for chunk in AGUI_OPEN_ENDED_REASONING_CHUNKS:
            yield chunk


def get_llm_provider(config: Optional[GenUXExecutionConfig] = None) -> BaseModelProvider:
    """Factory creating the appropriate LLM provider based on config and environment."""
    cfg = config or GenUXExecutionConfig()
    mode = cfg.resolved_mode()

    if mode == "live":
        api_key = cfg.get_api_key()
        try:
            return GeminiLiveProvider(
                api_key=api_key,
                model_name=cfg.model_name,
                temperature=cfg.temperature,
            )
        except Exception as exc:
            logger.warning(
                f"Failed to initialize live Gemini provider ({exc}). Falling back to DeterministicMockProvider."
            )
            return DeterministicMockProvider()
    return DeterministicMockProvider()
