"""User/Organization integration model for enterprise tool connections."""

import uuid
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IntegrationType(str, Enum):
    """Supported enterprise integration types."""

    SERVICENOW = "servicenow"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    SALESFORCE = "salesforce"
    DYNAMICS365 = "dynamics365"
    SHAREPOINT = "sharepoint"
    TEAMS = "teams"
    OUTLOOK = "outlook"
    POWER_AUTOMATE = "power_automate"
    PAGERDUTY = "pagerduty"
    SAP = "sap"


class UserIntegration(Base, TimestampMixin):
    """Integration credentials and config for enterprise tools."""

    __tablename__ = "user_integrations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Org-level integrations shared across users",
    )

    integration_type: Mapped[IntegrationType] = mapped_column(
        String(50), nullable=False, index=True
    )

    # Encrypted credentials
    credentials: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="Encrypted integration credentials"
    )
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="Integration-specific settings"
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<UserIntegration {self.id} - {self.integration_type}>"
