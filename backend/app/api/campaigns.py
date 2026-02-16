"""Campaign API endpoints — CRUD for multi-type outbound campaigns."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.campaign import Campaign, CampaignStatus, CampaignType

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class CampaignCreate(BaseModel):
    name: str
    campaign_type: str
    agent_id: str
    workspace_id: str | None = None
    description: str | None = None
    type_config: dict[str, Any] | None = None
    max_concurrent: int = 1
    retry_failed: bool = False


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type_config: dict[str, Any] | None = None
    status: str | None = None
    max_concurrent: int | None = None


def _campaign_to_dict(campaign: Campaign) -> dict[str, Any]:
    return {
        "id": str(campaign.id),
        "user_id": campaign.user_id,
        "agent_id": str(campaign.agent_id),
        "workspace_id": str(campaign.workspace_id) if campaign.workspace_id else None,
        "name": campaign.name,
        "description": campaign.description,
        "campaign_type": (
            campaign.campaign_type.value
            if isinstance(campaign.campaign_type, CampaignType)
            else campaign.campaign_type
        ),
        "status": (
            campaign.status.value
            if isinstance(campaign.status, CampaignStatus)
            else campaign.status
        ),
        "type_config": campaign.type_config,
        "scheduled_start": campaign.scheduled_start,
        "scheduled_end": campaign.scheduled_end,
        "total_contacts": campaign.total_contacts,
        "completed_count": campaign.completed_count,
        "failed_count": campaign.failed_count,
        "pending_count": campaign.pending_count,
        "max_concurrent": campaign.max_concurrent,
        "retry_failed": campaign.retry_failed,
        "max_retries": campaign.max_retries,
        "dispositions": campaign.dispositions,
        "created_at": campaign.created_at.isoformat(),
        "updated_at": campaign.updated_at.isoformat(),
    }


@router.get("")
async def list_campaigns(
    current_user: CurrentUser,
    campaign_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List campaigns, optionally filtered by type."""
    query = select(Campaign).where(Campaign.user_id == current_user.id)
    if campaign_type:
        query = query.where(Campaign.campaign_type == campaign_type)
    query = query.order_by(Campaign.created_at.desc())
    result = await db.execute(query)
    return [_campaign_to_dict(c) for c in result.scalars().all()]


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get campaign details."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _campaign_to_dict(campaign)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new campaign."""
    campaign = Campaign(
        user_id=current_user.id,
        agent_id=uuid.UUID(data.agent_id),
        workspace_id=uuid.UUID(data.workspace_id) if data.workspace_id else None,
        name=data.name,
        description=data.description,
        campaign_type=CampaignType(data.campaign_type),
        type_config=data.type_config or {},
        max_concurrent=data.max_concurrent,
        retry_failed=data.retry_failed,
    )
    db.add(campaign)
    await db.flush()
    return _campaign_to_dict(campaign)


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: uuid.UUID,
    data: CampaignUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a campaign."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = CampaignStatus(update_data["status"])

    for key, value in update_data.items():
        setattr(campaign, key, value)

    await db.flush()
    return _campaign_to_dict(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a campaign."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)
    await db.flush()
