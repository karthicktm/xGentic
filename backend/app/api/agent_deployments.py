"""Agent deployment API — deploy, promote, rollback agents across environments."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.models.agent import Agent
from app.models.agent_deployment import AgentDeployment, DeploymentStatus
from app.models.agent_version import AgentVersion
from app.models.environment import Environment

router = APIRouter(prefix="/agents/{agent_id}", tags=["Agent Deployments"])


class DeployRequest(BaseModel):
    environment_id: str


class PromoteRequest(BaseModel):
    from_environment_id: str
    to_environment_id: str


@router.post("/deploy", status_code=status.HTTP_201_CREATED)
async def deploy_agent(
    agent_id: uuid.UUID,
    data: DeployRequest,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Deploy an agent to an environment."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    env_result = await db.execute(
        select(Environment).where(Environment.id == uuid.UUID(data.environment_id))
    )
    env = env_result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    if env.is_locked:
        raise HTTPException(status_code=423, detail="Environment is locked")

    # Create version snapshot
    version = AgentVersion(
        agent_id=agent.id,
        version=agent.version,
        config_snapshot={
            "system_prompt": agent.system_prompt,
            "type_config": agent.type_config,
            "provider_config": agent.provider_config,
            "enabled_tools": agent.enabled_tools,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
        },
        change_description=f"Deployed to {env.name}",
        created_by=current_user.id,
    )
    db.add(version)

    # Create deployment
    deployment = AgentDeployment(
        agent_id=agent.id,
        environment_id=env.id,
        version=agent.version,
        status=DeploymentStatus.ACTIVE,
        config_snapshot=version.config_snapshot,
    )
    db.add(deployment)
    await db.flush()

    return {
        "id": str(deployment.id),
        "agent_id": str(deployment.agent_id),
        "environment_id": str(deployment.environment_id),
        "version": deployment.version,
        "status": deployment.status.value,
        "created_at": deployment.created_at.isoformat(),
    }


@router.post("/promote")
async def promote_agent(
    agent_id: uuid.UUID,
    data: PromoteRequest,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Promote an agent from one environment to another."""
    # Get source deployment
    source_result = await db.execute(
        select(AgentDeployment).where(
            AgentDeployment.agent_id == agent_id,
            AgentDeployment.environment_id == uuid.UUID(data.from_environment_id),
            AgentDeployment.status == DeploymentStatus.ACTIVE,
        )
    )
    source = source_result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="No active deployment found in source environment")

    # Check target environment
    target_result = await db.execute(
        select(Environment).where(Environment.id == uuid.UUID(data.to_environment_id))
    )
    target_env = target_result.scalar_one_or_none()
    if not target_env:
        raise HTTPException(status_code=404, detail="Target environment not found")

    if target_env.is_locked:
        raise HTTPException(status_code=423, detail="Target environment is locked")

    # Create promotion deployment
    deployment = AgentDeployment(
        agent_id=agent_id,
        environment_id=target_env.id,
        version=source.version,
        status=DeploymentStatus.ACTIVE,
        config_snapshot=source.config_snapshot,
        promoted_from_environment_id=uuid.UUID(data.from_environment_id),
    )
    db.add(deployment)
    await db.flush()

    return {
        "id": str(deployment.id),
        "agent_id": str(deployment.agent_id),
        "environment_id": str(deployment.environment_id),
        "version": deployment.version,
        "status": deployment.status.value,
        "promoted_from": data.from_environment_id,
    }


@router.get("/versions")
async def list_agent_versions(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List agent version history."""
    result = await db.execute(
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.version.desc())
    )
    versions = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "version": v.version,
            "change_description": v.change_description,
            "created_by": v.created_by,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@router.post("/rollback/{version}")
async def rollback_agent(
    agent_id: uuid.UUID,
    version: int,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Rollback agent to a previous version."""
    # Find the version
    ver_result = await db.execute(
        select(AgentVersion).where(
            AgentVersion.agent_id == agent_id,
            AgentVersion.version == version,
        )
    )
    agent_version = ver_result.scalar_one_or_none()
    if not agent_version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Apply snapshot to agent
    agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    snapshot = agent_version.config_snapshot
    for key, value in snapshot.items():
        if hasattr(agent, key):
            setattr(agent, key, value)

    agent.version += 1
    await db.flush()

    return {"message": f"Agent rolled back to version {version}", "new_version": agent.version}
