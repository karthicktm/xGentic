"""Hierarchy membership model for role-based access at each level."""

import uuid
from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class HierarchyLevel(str, Enum):
    """Levels in the organization hierarchy."""

    ORGANIZATION = "organization"
    UNIT = "unit"
    DEPARTMENT = "department"
    PROJECT = "project"


class HierarchyRole(str, Enum):
    """Roles within a hierarchy level."""

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class HierarchyMembership(Base, TimestampMixin):
    """Polymorphic membership model for hierarchy-level access control.

    Associates a user with a specific level in the hierarchy with a role.
    Uses nullable FKs for the polymorphic level reference.
    """

    __tablename__ = "hierarchy_memberships"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "level", "organization_id", "unit_id", "department_id", "project_id",
            name="uq_hierarchy_membership",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[HierarchyLevel] = mapped_column(
        String(50), nullable=False, comment="Which hierarchy level this membership is for"
    )
    role: Mapped[HierarchyRole] = mapped_column(
        String(50), nullable=False, default=HierarchyRole.MEMBER
    )

    # Polymorphic level references (only one should be set based on `level`)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="hierarchy_memberships")

    def __repr__(self) -> str:
        return f"<HierarchyMembership user={self.user_id} level={self.level} role={self.role}>"
