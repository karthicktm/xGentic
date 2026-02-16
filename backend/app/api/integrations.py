"""Integration API endpoints — enterprise tool connection management."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.integration import IntegrationType, UserIntegration

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class IntegrationCreate(BaseModel):
    integration_type: str
    credentials: dict[str, Any] = {}
    settings: dict[str, Any] = {}


def _integration_to_dict(integration: UserIntegration) -> dict[str, Any]:
    return {
        "id": str(integration.id),
        "user_id": integration.user_id,
        "organization_id": (
            str(integration.organization_id) if integration.organization_id else None
        ),
        "integration_type": (
            integration.integration_type.value
            if isinstance(integration.integration_type, IntegrationType)
            else integration.integration_type
        ),
        "settings": integration.settings,
        "is_active": integration.is_active,
        "created_at": integration.created_at.isoformat(),
        "updated_at": integration.updated_at.isoformat(),
    }


@router.get("")
async def list_integrations(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List connected integrations for the current user."""
    query = select(UserIntegration).where(
        UserIntegration.user_id == current_user.id,
        UserIntegration.is_active.is_(True),
    )
    result = await db.execute(query)
    return [_integration_to_dict(i) for i in result.scalars().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def connect_integration(
    data: IntegrationCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Connect a new integration."""
    # Check for existing active integration of the same type
    existing_result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.user_id == current_user.id,
            UserIntegration.integration_type == data.integration_type,
            UserIntegration.is_active.is_(True),
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Integration of type '{data.integration_type}' is already connected",
        )

    integration = UserIntegration(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        integration_type=IntegrationType(data.integration_type),
        credentials=data.credentials,
        settings=data.settings,
    )
    db.add(integration)
    await db.flush()
    return _integration_to_dict(integration)


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_integration(
    integration_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Disconnect (deactivate) an integration."""
    result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.id == integration_id,
            UserIntegration.user_id == current_user.id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration.is_active = False
    await db.flush()
