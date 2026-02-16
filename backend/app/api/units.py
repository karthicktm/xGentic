"""Unit API endpoints — level 2 hierarchy."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.models.unit import Unit

router = APIRouter(prefix="/organizations/{org_id}/units", tags=["Units"])

# Simplified router for current user's org
simple_router = APIRouter(prefix="/units", tags=["Units"])


class UnitCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    settings: dict[str, Any] | None = None


class UnitUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    settings: dict[str, Any] | None = None
    is_active: bool | None = None


def _unit_to_dict(unit: Unit) -> dict[str, Any]:
    return {
        "id": str(unit.id),
        "organization_id": str(unit.organization_id),
        "name": unit.name,
        "slug": unit.slug,
        "description": unit.description,
        "settings": unit.settings,
        "is_active": unit.is_active,
        "created_at": unit.created_at.isoformat(),
        "updated_at": unit.updated_at.isoformat(),
    }


@router.get("")
async def list_units(
    org_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List units in an organization."""
    result = await db.execute(
        select(Unit).where(Unit.organization_id == org_id, Unit.is_active.is_(True))
    )
    return [_unit_to_dict(u) for u in result.scalars().all()]


@router.get("/{unit_id}")
async def get_unit(
    org_id: uuid.UUID,
    unit_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get unit details."""
    result = await db.execute(
        select(Unit).where(Unit.id == unit_id, Unit.organization_id == org_id)
    )
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return _unit_to_dict(unit)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_unit(
    org_id: uuid.UUID,
    data: UnitCreate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new unit."""
    unit = Unit(
        organization_id=org_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        settings=data.settings or {},
    )
    db.add(unit)
    await db.flush()
    return _unit_to_dict(unit)


@router.patch("/{unit_id}")
async def update_unit(
    org_id: uuid.UUID,
    unit_id: uuid.UUID,
    data: UnitUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a unit."""
    result = await db.execute(
        select(Unit).where(Unit.id == unit_id, Unit.organization_id == org_id)
    )
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(unit, key, value)

    await db.flush()
    return _unit_to_dict(unit)


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    org_id: uuid.UUID,
    unit_id: uuid.UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (deactivate) a unit."""
    result = await db.execute(
        select(Unit).where(Unit.id == unit_id, Unit.organization_id == org_id)
    )
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    unit.is_active = False
    await db.flush()


# Simplified endpoints for current user's organization
@simple_router.get("")
async def list_my_units(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List units in current user's organization."""
    if not current_user.organization_id:
        return []

    result = await db.execute(
        select(Unit).where(
            Unit.organization_id == current_user.organization_id,
            Unit.is_active.is_(True)
        )
    )
    return [_unit_to_dict(u) for u in result.scalars().all()]
