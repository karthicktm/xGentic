"""Unit model — level 2 in the organization hierarchy."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization


class Unit(Base, TimestampMixin):
    """Business unit within an organization.

    Hierarchy: Organization > Unit > Department > Project > Workspace
    """

    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_unit_org_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="units")
    departments: Mapped[list["Department"]] = relationship(
        "Department", back_populates="unit", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Unit {self.id} - {self.name}>"
