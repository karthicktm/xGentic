"""Interaction model — unified history for all agent types."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class InteractionType(str, Enum):
    """Type of agent interaction."""

    VOICE_CALL = "voice_call"
    CHAT_SESSION = "chat_session"
    EMAIL_THREAD = "email_thread"
    DOCUMENT_WORKFLOW = "document_workflow"


class InteractionStatus(str, Enum):
    """Interaction lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Interaction(Base, TimestampMixin):
    """Unified interaction history for all agent types.

    Type-specific data is stored in the `type_data` JSON column.
    """

    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    environment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("environments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Type & status
    interaction_type: Mapped[InteractionType] = mapped_column(
        String(50), nullable=False, index=True
    )
    status: Mapped[InteractionStatus] = mapped_column(
        String(50), nullable=False, default=InteractionStatus.ACTIVE
    )

    # Common fields
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Type-specific data
    type_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="Type-specific interaction data",
    )

    # Disposition & outcome
    disposition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)  # type: ignore[assignment]
    ended_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)  # type: ignore[assignment]

    # Relationships
    workspace: Mapped["Workspace | None"] = relationship("Workspace", back_populates="interactions")

    def __repr__(self) -> str:
        return f"<Interaction {self.id} - {self.interaction_type} ({self.status})>"
