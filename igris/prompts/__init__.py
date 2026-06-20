"""Igris Routing Prompt templates for the 8B router model."""

from .router_prompts import (
    ROUTER_SYSTEM_PROMPT,
    ROUTER_DECISION_SCHEMA,
    assemble_router_prompt,
    build_observation,
)

__all__ = [
    "ROUTER_SYSTEM_PROMPT",
    "ROUTER_DECISION_SCHEMA",
    "assemble_router_prompt",
    "build_observation",
]
