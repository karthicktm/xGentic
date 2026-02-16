"""Usage & quota API endpoints — resource consumption tracking."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.interaction import Interaction
from app.models.quota import UserQuota

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("")
async def get_usage_overview(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get usage overview for the current user."""
    # Total interactions count
    interactions_result = await db.execute(
        select(func.count(Interaction.id)).where(
            Interaction.user_id == current_user.id
        )
    )
    total_interactions = interactions_result.scalar() or 0

    # Total duration across all interactions
    duration_result = await db.execute(
        select(func.coalesce(func.sum(Interaction.duration_seconds), 0)).where(
            Interaction.user_id == current_user.id
        )
    )
    total_duration_seconds = duration_result.scalar() or 0

    # Total cost
    cost_result = await db.execute(
        select(func.coalesce(func.sum(Interaction.cost_usd), 0.0)).where(
            Interaction.user_id == current_user.id
        )
    )
    total_cost_usd = float(cost_result.scalar() or 0.0)

    # Total tokens
    tokens_result = await db.execute(
        select(func.coalesce(func.sum(Interaction.token_count), 0)).where(
            Interaction.user_id == current_user.id
        )
    )
    total_tokens = tokens_result.scalar() or 0

    return {
        "user_id": current_user.id,
        "total_interactions": total_interactions,
        "total_duration_seconds": total_duration_seconds,
        "total_cost_usd": total_cost_usd,
        "total_tokens": total_tokens,
    }


@router.get("/quotas")
async def get_quotas(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get quota allocations and usage for the current user."""
    result = await db.execute(
        select(UserQuota).where(UserQuota.user_id == current_user.id)
    )
    quotas = result.scalars().all()

    return [
        {
            "id": str(q.id),
            "resource_type": q.resource_type,
            "limit_value": q.limit_value,
            "used_value": q.used_value,
            "remaining": max(0.0, q.limit_value - q.used_value),
            "usage_percent": (
                round((q.used_value / q.limit_value) * 100, 1)
                if q.limit_value > 0
                else 0.0
            ),
            "created_at": q.created_at.isoformat(),
            "updated_at": q.updated_at.isoformat(),
        }
        for q in quotas
    ]
