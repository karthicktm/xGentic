"""Quota models for usage tracking and limits."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.user import User


class UserQuota(Base, TimestampMixin):
    """User-level quota tracking."""

    __tablename__ = "user_quotas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="e.g., voice_minutes, chat_messages, tokens"
    )
    limit_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    used_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quotas")

    def __repr__(self) -> str:
        return f"<UserQuota user={self.user_id} {self.resource_type}: {self.used_value}/{self.limit_value}>"


class AgentQuota(Base, TimestampMixin):
    """Agent-level quota tracking."""

    __tablename__ = "agent_quotas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    limit_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    used_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="quota")

    def __repr__(self) -> str:
        return f"<AgentQuota agent={self.agent_id} {self.resource_type}>"
