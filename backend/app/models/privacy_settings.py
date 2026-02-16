"""Privacy settings model for GDPR compliance."""

import uuid
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PrivacySettings(Base, TimestampMixin):
    """User privacy preferences for compliance."""

    __tablename__ = "privacy_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Consent flags
    data_collection_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    analytics_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recording_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Retention
    data_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)

    # Additional preferences
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<PrivacySettings user={self.user_id}>"
