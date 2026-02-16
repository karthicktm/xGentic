"""User model for authentication and authorization."""

import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.membership import HierarchyMembership
    from app.models.organization import Organization
    from app.models.quota import UserQuota
    from app.models.user_profile import UserProfile
    from app.models.workspace_member import WorkspaceMember


class AuthProvider(str, Enum):
    """Authentication provider types."""

    EMAIL = "email"
    AZURE_AD = "azure_ad"
    OKTA = "okta"
    SAML = "saml"


class UserRole(str, Enum):
    """User roles for system-level permissions.

    Hierarchy: SUPER_ADMIN > ORG_ADMIN > MANAGER > USER
    """

    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    MANAGER = "manager"
    USER = "user"


class User(Base, TimestampMixin):
    """User model with enterprise SSO support."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Null for SSO-only users"
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # SSO support
    provider: Mapped[AuthProvider] = mapped_column(
        String(50),
        nullable=False,
        default=AuthProvider.EMAIL,
        comment="Authentication provider",
    )
    provider_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True, comment="Unique ID from SSO provider"
    )
    sso_subject_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True, comment="SSO subject identifier"
    )

    # Enterprise fields
    department: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="User's department (informational)"
    )
    job_title: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="User's job title"
    )

    # Organization & Role
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="User's organization (null for super admin)",
    )
    role: Mapped[UserRole] = mapped_column(
        String(50), nullable=False, default=UserRole.USER, comment="System-level role"
    )

    # Email Verification
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Whether email is verified"
    )
    email_verification_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    email_verification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # OTP
    otp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_otp_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Security
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization", foreign_keys=[organization_id], back_populates="users"
    )
    owned_organization: Mapped["Organization | None"] = relationship(
        "Organization", foreign_keys="Organization.owner_id", back_populates="owner"
    )
    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        foreign_keys="WorkspaceMember.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    hierarchy_memberships: Mapped[list["HierarchyMembership"]] = relationship(
        "HierarchyMembership", back_populates="user", cascade="all, delete-orphan"
    )
    quotas: Mapped[list["UserQuota"]] = relationship(
        "UserQuota", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.id} - {self.email} ({self.role})>"

    def is_account_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until

    def can_request_otp(self) -> bool:
        """Check if user can request a new OTP (rate limiting)."""
        if self.last_otp_sent_at is None:
            return True
        return datetime.now(UTC) > self.last_otp_sent_at.replace(tzinfo=UTC) + timedelta(minutes=1)

    def is_otp_valid(self) -> bool:
        """Check if current OTP is still valid."""
        if self.otp_expires_at is None or self.otp_secret is None:
            return False
        return datetime.now(UTC) < self.otp_expires_at.replace(tzinfo=UTC)
