"""Organization model for enterprise multi-tenant architecture."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.environment import Environment
    from app.models.unit import Unit
    from app.models.user import User
    from app.models.workspace import Workspace


class Organization(Base, TimestampMixin):
    """Organization model — top level of the 5-level hierarchy.

    Represents an enterprise tenant with SSO configuration,
    Azure integration, and resource limits.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="Organization name")
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="URL-friendly identifier"
    )

    # Owner
    owner_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Organization owner user ID",
    )

    # SSO Configuration
    sso_provider: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="SSO provider: azure_ad, okta, saml"
    )
    sso_tenant_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="SSO tenant/realm ID"
    )
    sso_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="SSO provider configuration metadata"
    )

    # Azure Configuration
    azure_tenant_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Azure AD tenant ID for this org"
    )
    azure_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Azure subscription ID"
    )

    # Limits
    max_users: Mapped[int] = mapped_column(
        Integer, nullable=False, default=50, comment="Maximum users allowed"
    )
    max_agents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=20, comment="Maximum agents allowed"
    )

    # Feature Flags
    features_enabled: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, comment="Enabled feature flags"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether organization is active"
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", foreign_keys="Organization.owner_id", back_populates="owned_organization"
    )
    users: Mapped[list["User"]] = relationship(
        "User", foreign_keys="User.organization_id", back_populates="organization"
    )
    units: Mapped[list["Unit"]] = relationship(
        "Unit", back_populates="organization", cascade="all, delete-orphan"
    )
    environments: Mapped[list["Environment"]] = relationship(
        "Environment", back_populates="organization", cascade="all, delete-orphan"
    )
    workspaces: Mapped[list["Workspace"]] = relationship(
        "Workspace",
        back_populates="organization",
        cascade="all, delete-orphan",
        foreign_keys="Workspace.organization_id",
    )

    def __repr__(self) -> str:
        return f"<Organization {self.id} - {self.name}>"
