"""Shared Core Engine for GenUX (Generative User Experience) technologies.

Provides configuration, execution mode selection (live/mock/auto),
unified LLM provider abstractions, and realistic offline mock datasets.
"""

from .config import ExecutionMode, GenUXExecutionConfig
from .llm_provider import (
    BaseModelProvider,
    DeterministicMockProvider,
    GeminiLiveProvider,
    get_llm_provider,
)
from .mock_data import MOCK_DATASETS, get_mock_data

__all__ = [
    "ExecutionMode",
    "GenUXExecutionConfig",
    "BaseModelProvider",
    "GeminiLiveProvider",
    "DeterministicMockProvider",
    "get_llm_provider",
    "MOCK_DATASETS",
    "get_mock_data",
]
