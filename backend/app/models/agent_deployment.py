"""Agent deployment model for tracking deployments across environments."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.environment import Environment


class DeploymentStatus(str, Enum):
    """Deployment lifecycle status."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    DEACTIVATED = "deactivated"


class AgentDeployment(Base, TimestampMixin):
    """Tracks agent deployments to specific environments."""

    __tablename__ = "agent_deployments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[DeploymentStatus] = mapped_column(
        String(50), nullable=False, default=DeploymentStatus.PENDING
    )
    azure_deployment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="Frozen config at deployment time"
    )
    promoted_from_environment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, comment="Source environment if promoted"
    )

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="deployments")
    environment: Mapped["Environment"] = relationship("Environment", back_populates="deployments")

    def __repr__(self) -> str:
        return f"<AgentDeployment agent={self.agent_id} env={self.environment_id} v{self.version}>"
