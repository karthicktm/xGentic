"""Campaign model for multi-type outbound campaigns."""

import uuid
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CampaignType(str, Enum):
    """Campaign types matching agent modalities."""

    VOICE = "voice"
    CHAT = "chat"
    EMAIL = "email"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Campaign(Base, TimestampMixin):
    """Multi-type campaign for outbound agent interactions."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Campaign info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    campaign_type: Mapped[CampaignType] = mapped_column(
        String(50), nullable=False, index=True
    )
    status: Mapped[CampaignStatus] = mapped_column(
        String(50), nullable=False, default=CampaignStatus.DRAFT
    )

    # Type-specific config (calling hours, email templates, etc.)
    type_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Scheduling
    scheduled_start: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)  # type: ignore[assignment]
    scheduled_end: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)  # type: ignore[assignment]

    # Contacts
    contact_list: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    total_contacts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Statistics
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Settings
    max_concurrent: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    retry_failed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Disposition tracking
    dispositions: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<Campaign {self.id} - {self.name} ({self.campaign_type})>"
