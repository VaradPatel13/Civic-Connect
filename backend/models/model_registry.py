"""Model Registry and Versioned Prompt Management for CivicConnect AI Agents.

Table:
- model_registry: Audit registry tracking active system prompts, model configs, and prompt versions

Specs: docs/specs/ai-pipeline.md
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDMixin


class ModelRegistry(Base, UUIDMixin, TimestampMixin):
    """Tracks prompt versions, system prompt hashes, and model parameters for 100% reproducibility."""

    __tablename__ = "model_registry"

    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0.0", index=True)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="nvidia_nim")

    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    system_prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<ModelRegistry agent={self.agent_name} prompt={self.prompt_version} model={self.model_name}>"
