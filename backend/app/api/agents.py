"""Agent API endpoints — multi-type agent CRUD and management."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.public_id import generate_public_id
from app.db.session import get_db
from app.models.agent import Agent, AgentStatus, AgentType

router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    agent_type: str
    system_prompt: str
    language: str = "en-US"
    temperature: float = 0.7
    max_tokens: int = 2000
    provider_type: str = "azure_foundry"
    provider_config: dict[str, Any] | None = None
    type_config: dict[str, Any] | None = None
    enabled_tools: list[str] | None = None
    enabled_tool_ids: dict[str, list[str]] | None = None
    tool_configs: dict[str, dict[str, Any]] | None = None
    embed_enabled: bool = True
    allowed_domains: list[str] | None = None
    embed_settings: dict[str, Any] | None = None
    agent_source: str = "local"
    azure_foundry_agent_id: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    language: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    provider_config: dict[str, Any] | None = None
    type_config: dict[str, Any] | None = None
    enabled_tools: list[str] | None = None
    enabled_tool_ids: dict[str, list[str]] | None = None
    tool_configs: dict[str, dict[str, Any]] | None = None
    status: str | None = None
    embed_enabled: bool | None = None
    allowed_domains: list[str] | None = None
    embed_settings: dict[str, Any] | None = None
    is_active: bool | None = None


def _agent_to_dict(agent: Agent) -> dict[str, Any]:
    return {
        "id": str(agent.id),
        "user_id": agent.user_id,
        "organization_id": str(agent.organization_id),
        "name": agent.name,
        "description": agent.description,
        "agent_type": agent.agent_type.value
        if isinstance(agent.agent_type, AgentType)
        else agent.agent_type,
        "status": agent.status.value if isinstance(agent.status, AgentStatus) else agent.status,
        "system_prompt": agent.system_prompt,
        "language": agent.language,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "provider_type": agent.provider_type,
        "provider_config": agent.provider_config,
        "type_config": agent.type_config,
        "version": agent.version,
        "enabled_tools": agent.enabled_tools,
        "enabled_tool_ids": agent.enabled_tool_ids,
        "tool_configs": agent.tool_configs,
        "public_id": agent.public_id,
        "embed_enabled": agent.embed_enabled,
        "allowed_domains": agent.allowed_domains,
        "embed_settings": agent.embed_settings,
        "is_active": agent.is_active,
        "total_interactions": agent.total_interactions,
        "agent_source": agent.agent_source,
        "azure_foundry_agent_id": agent.azure_foundry_agent_id,
        "created_at": agent.created_at.isoformat(),
        "updated_at": agent.updated_at.isoformat(),
    }


@router.get("")
async def list_agents(
    current_user: CurrentUser,
    agent_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List agents, optionally filtered by type."""
    query = select(Agent).where(Agent.user_id == current_user.id, Agent.is_active.is_(True))
    if agent_type:
        query = query.where(Agent.agent_type == agent_type)
    result = await db.execute(query)
    return [_agent_to_dict(a) for a in result.scalars().all()]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get agent details."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new agent."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    agent = Agent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        name=data.name,
        description=data.description,
        agent_type=AgentType(data.agent_type),
        system_prompt=data.system_prompt,
        language=data.language,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        provider_type=data.provider_type,
        provider_config=data.provider_config or {},
        type_config=data.type_config or {},
        enabled_tools=data.enabled_tools or [],
        enabled_tool_ids=data.enabled_tool_ids or {},
        tool_configs=data.tool_configs or {},
        agent_source=data.agent_source,
        azure_foundry_agent_id=data.azure_foundry_agent_id,
        embed_enabled=data.embed_enabled,
        allowed_domains=data.allowed_domains or [],
        embed_settings=data.embed_settings
        or {
            "theme": "auto",
            "position": "bottom-right",
            "primary_color": "#818cf8",
            "greeting_message": "Hi! How can I help you today?",
            "button_text": "Talk to us",
        },
        public_id=generate_public_id("ag"),
    )
    db.add(agent)
    await db.flush()
    return _agent_to_dict(agent)


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update an agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = AgentStatus(update_data["status"])

    for key, value in update_data.items():
        setattr(agent, key, value)

    agent.version += 1
    await db.flush()
    return _agent_to_dict(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (deactivate) an agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.is_active = False
    await db.flush()
