"""Environment API endpoints for deployment stages."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.models.environment import Environment, EnvironmentType

router = APIRouter(prefix="/environments", tags=["Environments"])


class EnvironmentCreate(BaseModel):
    name: str
    slug: str
    type: str = "development"
    provider: str = "azure_foundry"
    azure_endpoint: str | None = None
    azure_resource_group: str | None = None
    azure_project_name: str | None = None
    azure_api_key_encrypted: str | None = None
    provider_config: dict[str, Any] | None = None
    resource_quotas: dict[str, Any] | None = None


class EnvironmentUpdate(BaseModel):
    name: str | None = None
    azure_endpoint: str | None = None
    azure_resource_group: str | None = None
    azure_project_name: str | None = None
    azure_api_key_encrypted: str | None = None
    provider_config: dict[str, Any] | None = None
    resource_quotas: dict[str, Any] | None = None
    is_active: bool | None = None
    is_locked: bool | None = None


def _env_to_dict(env: Environment) -> dict[str, Any]:
    return {
        "id": str(env.id),
        "organization_id": str(env.organization_id),
        "name": env.name,
        "slug": env.slug,
        "type": env.type.value if isinstance(env.type, EnvironmentType) else env.type,
        "provider": env.provider,
        "azure_endpoint": env.azure_endpoint,
        "azure_resource_group": env.azure_resource_group,
        "azure_project_name": env.azure_project_name,
        "provider_config": env.provider_config,
        "resource_quotas": env.resource_quotas,
        "is_active": env.is_active,
        "is_locked": env.is_locked,
        "created_at": env.created_at.isoformat(),
        "updated_at": env.updated_at.isoformat(),
    }


@router.get("")
async def list_environments(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List environments for the user's organization."""
    if not current_user.organization_id:
        return []
    result = await db.execute(
        select(Environment).where(Environment.organization_id == current_user.organization_id)
    )
    return [_env_to_dict(e) for e in result.scalars().all()]


@router.get("/{env_id}")
async def get_environment(
    env_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get environment details."""
    result = await db.execute(select(Environment).where(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return _env_to_dict(env)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_environment(
    data: EnvironmentCreate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new environment."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    env = Environment(
        organization_id=current_user.organization_id,
        name=data.name,
        slug=data.slug,
        type=EnvironmentType(data.type),
        provider=data.provider,
        azure_endpoint=data.azure_endpoint,
        azure_resource_group=data.azure_resource_group,
        azure_project_name=data.azure_project_name,
        azure_api_key_encrypted=data.azure_api_key_encrypted,
        provider_config=data.provider_config or {},
        resource_quotas=data.resource_quotas or {},
    )
    db.add(env)
    await db.flush()
    return _env_to_dict(env)


@router.patch("/{env_id}")
async def update_environment(
    env_id: uuid.UUID,
    data: EnvironmentUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update an environment."""
    result = await db.execute(select(Environment).where(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(env, key, value)

    await db.flush()
    return _env_to_dict(env)


@router.post("/{env_id}/test-connection")
async def test_environment_connection(
    env_id: uuid.UUID,
    current_user: AdminUser,  # noqa: ARG001
    db: AsyncSession = Depends(get_db),  # noqa: PT028
) -> dict[str, Any]:
    """Test connection to the environment's AI provider."""
    result = await db.execute(select(Environment).where(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    if env.provider == "azure_foundry":
        from dataclasses import asdict  # noqa: PLC0415

        from app.services.providers.azure_foundry import AzureFoundryProvider  # noqa: PLC0415

        provider = AzureFoundryProvider()
        endpoint = env.azure_endpoint or ""
        api_key = env.azure_api_key_encrypted  # decrypted at usage
        conn_status = await provider.test_connection(endpoint, api_key)
        return asdict(conn_status)

    return {
        "connected": False,
        "provider": env.provider,
        "endpoint": "",
        "error": "Unsupported provider",
    }
