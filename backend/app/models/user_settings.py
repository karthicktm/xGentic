"""User settings model."""

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    """User application settings (notifications, theme, etc.)."""

    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=lambda: {
            "theme": "dark",
            "notifications_enabled": True,
            "email_notifications": True,
            "sidebar_collapsed": False,
        }
    )

    def __repr__(self) -> str:
        return f"<UserSettings user={self.user_id}>"
