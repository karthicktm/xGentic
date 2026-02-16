"""Multi-type agent model."""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.agent_deployment import AgentDeployment
    from app.models.agent_version import AgentVersion
    from app.models.document import Document
    from app.models.quota import AgentQuota


class AgentType(str, Enum):
    """Agent type determines the interaction modality."""

    VOICE = "voice"
    CHAT = "chat"
    EMAIL = "email"
    DOCUMENT_WORKFLOW = "document_workflow"


class AgentStatus(str, Enum):
    """Agent lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Agent(Base):
    """Multi-type agent configuration.

    Supports voice, chat, email, and document workflow agents.
    Type-specific configuration is stored in the `type_config` JSON column.
    """

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Agent type and status
    agent_type: Mapped[AgentType] = mapped_column(
        String(50), nullable=False, index=True, comment="Agent modality type"
    )
    status: Mapped[AgentStatus] = mapped_column(
        String(50), nullable=False, default=AgentStatus.DRAFT
    )

    # LLM configuration
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en-US")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)

    # Provider
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, default="azure_foundry")
    provider_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Source tracking (local vs imported from Azure Foundry)
    agent_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="local",
        comment="Origin: local or azure_foundry",
    )
    azure_foundry_agent_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="External Azure Foundry agent ID for imported agents",
    )

    # Type-specific config (voice settings, chat settings, etc.)
    type_config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Type-specific configuration (voice, chat, email, workflow)",
    )

    # Versioning
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Tools & integrations
    enabled_tools: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    enabled_tool_ids: Mapped[dict[str, list[str]]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    tool_configs: Mapped[dict[str, dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Embed settings
    public_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, unique=True, index=True
    )
    embed_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_domains: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    embed_settings: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "theme": "auto",
            "position": "bottom-right",
            "primary_color": "#818cf8",
            "greeting_message": "Hi! How can I help you today?",
            "button_text": "Talk to us",
        },
    )

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Statistics
    total_interactions: Mapped[int] = mapped_column(default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="agent", cascade="all, delete-orphan"
    )
    deployments: Mapped[list["AgentDeployment"]] = relationship(
        "AgentDeployment", back_populates="agent", cascade="all, delete-orphan"
    )
    versions: Mapped[list["AgentVersion"]] = relationship(
        "AgentVersion", back_populates="agent", cascade="all, delete-orphan"
    )
    quota: Mapped["AgentQuota | None"] = relationship(
        "AgentQuota", back_populates="agent", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Agent {self.id} - {self.name} ({self.agent_type})>"
