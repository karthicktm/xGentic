"""Interaction API — unified interaction history for all agent types."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.interaction import Interaction

router = APIRouter(prefix="/interactions", tags=["Interactions"])


@router.get("")
async def list_interactions(
    current_user: CurrentUser,
    interaction_type: str | None = Query(None),
    agent_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List interactions with optional filters."""
    query = select(Interaction).where(Interaction.user_id == current_user.id)

    if interaction_type:
        query = query.where(Interaction.interaction_type == interaction_type)
    if agent_id:
        query = query.where(Interaction.agent_id == uuid.UUID(agent_id))
    if workspace_id:
        query = query.where(Interaction.workspace_id == uuid.UUID(workspace_id))

    query = query.order_by(Interaction.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)

    return [
        {
            "id": str(i.id),
            "interaction_type": i.interaction_type.value if hasattr(i.interaction_type, "value") else i.interaction_type,
            "status": i.status.value if hasattr(i.status, "value") else i.status,
            "agent_id": str(i.agent_id) if i.agent_id else None,
            "contact_id": i.contact_id,
            "workspace_id": str(i.workspace_id) if i.workspace_id else None,
            "environment_id": str(i.environment_id) if i.environment_id else None,
            "duration_seconds": i.duration_seconds,
            "token_count": i.token_count,
            "disposition": i.disposition,
            "sentiment": i.sentiment,
            "summary": i.summary,
            "type_data": i.type_data,
            "created_at": i.created_at.isoformat(),
        }
        for i in result.scalars().all()
    ]


@router.get("/{interaction_id}")
async def get_interaction(
    interaction_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get interaction details including transcript."""
    result = await db.execute(select(Interaction).where(Interaction.id == interaction_id))
    i = result.scalar_one_or_none()
    if not i:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Interaction not found")

    return {
        "id": str(i.id),
        "interaction_type": i.interaction_type.value if hasattr(i.interaction_type, "value") else i.interaction_type,
        "status": i.status.value if hasattr(i.status, "value") else i.status,
        "agent_id": str(i.agent_id) if i.agent_id else None,
        "contact_id": i.contact_id,
        "workspace_id": str(i.workspace_id) if i.workspace_id else None,
        "environment_id": str(i.environment_id) if i.environment_id else None,
        "transcript": i.transcript,
        "summary": i.summary,
        "duration_seconds": i.duration_seconds,
        "token_count": i.token_count,
        "cost_usd": i.cost_usd,
        "disposition": i.disposition,
        "sentiment": i.sentiment,
        "type_data": i.type_data,
        "started_at": i.started_at,
        "ended_at": i.ended_at,
        "created_at": i.created_at.isoformat(),
    }
