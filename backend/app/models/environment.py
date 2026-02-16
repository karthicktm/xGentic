"""Environment model for isolated deployment stages."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.agent_deployment import AgentDeployment
    from app.models.organization import Organization


class EnvironmentType(str, Enum):
    """Environment types for the deployment pipeline."""

    DEVELOPMENT = "development"
    QA = "qa"
    STAGING = "staging"
    PRODUCTION = "production"
    SANDBOX = "sandbox"


class Environment(Base, TimestampMixin):
    """Deployment environment with provider configuration.

    Environments are organization-level and represent infrastructure
    (Azure AI Foundry endpoints, quotas, etc.).
    """

    __tablename__ = "environments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[EnvironmentType] = mapped_column(
        String(50), nullable=False, default=EnvironmentType.DEVELOPMENT
    )

    # Provider configuration
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="azure_foundry",
        comment="Provider: azure_foundry, aws_bedrock, google_vertex",
    )
    azure_endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    azure_resource_group: Mapped[str | None] = mapped_column(String(200), nullable=True)
    azure_project_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    azure_api_key_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="Additional provider configuration",
    )

    # Quotas
    resource_quotas: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="Resource quotas for this environment",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Lock to prevent modifications (e.g., production freeze)",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="environments")
    deployments: Mapped[list["AgentDeployment"]] = relationship(
        "AgentDeployment", back_populates="environment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Environment {self.id} - {self.name} ({self.type})>"
