"""Organization API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import AdminUser, CurrentUser, SuperAdminUser
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    sso_provider: str | None = None
    sso_tenant_id: str | None = None
    azure_tenant_id: str | None = None
    azure_subscription_id: str | None = None
    max_users: int = 50
    max_agents: int = 20


class OrganizationUpdate(BaseModel):
    name: str | None = None
    sso_provider: str | None = None
    sso_tenant_id: str | None = None
    sso_metadata: dict[str, Any] | None = None
    azure_tenant_id: str | None = None
    azure_subscription_id: str | None = None
    max_users: int | None = None
    max_agents: int | None = None
    features_enabled: list[str] | None = None
    is_active: bool | None = None


def _org_to_dict(org: Organization) -> dict[str, Any]:
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "owner_id": org.owner_id,
        "sso_provider": org.sso_provider,
        "sso_tenant_id": org.sso_tenant_id,
        "azure_tenant_id": org.azure_tenant_id,
        "azure_subscription_id": org.azure_subscription_id,
        "max_users": org.max_users,
        "max_agents": org.max_agents,
        "features_enabled": org.features_enabled,
        "is_active": org.is_active,
        "created_at": org.created_at.isoformat(),
        "updated_at": org.updated_at.isoformat(),
    }


@router.get("")
async def list_organizations(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List organizations the user has access to."""
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value == "super_admin":
        result = await db.execute(select(Organization))
    else:
        result = await db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
    orgs = result.scalars().all()
    return [_org_to_dict(org) for org in orgs]


@router.get("/{org_id}")
async def get_organization(
    org_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get organization details."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _org_to_dict(org)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: SuperAdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new organization (super admin only)."""
    org = Organization(
        name=data.name,
        slug=data.slug,
        owner_id=current_user.id,
        sso_provider=data.sso_provider,
        sso_tenant_id=data.sso_tenant_id,
        azure_tenant_id=data.azure_tenant_id,
        azure_subscription_id=data.azure_subscription_id,
        max_users=data.max_users,
        max_agents=data.max_agents,
    )
    db.add(org)
    await db.flush()
    return _org_to_dict(org)


@router.patch("/{org_id}")
async def update_organization(
    org_id: uuid.UUID,
    data: OrganizationUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update organization settings."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)

    await db.flush()
    return _org_to_dict(org)


@router.get("/{org_id}/members")
async def list_organization_members(
    org_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List members of an organization."""
    result = await db.execute(
        select(User).where(User.organization_id == org_id, User.is_active.is_(True))
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "department": u.department,
            "job_title": u.job_title,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]
