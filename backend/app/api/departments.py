"""Department API endpoints — level 3 hierarchy."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.models.department import Department
from app.models.unit import Unit

router = APIRouter(prefix="/units/{unit_id}/departments", tags=["Departments"])

# Simplified router for current user's org
simple_router = APIRouter(prefix="/departments", tags=["Departments"])


class DepartmentCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    settings: dict[str, Any] | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    settings: dict[str, Any] | None = None
    is_active: bool | None = None


def _dept_to_dict(dept: Department) -> dict[str, Any]:
    return {
        "id": str(dept.id),
        "unit_id": str(dept.unit_id),
        "organization_id": str(dept.organization_id),
        "name": dept.name,
        "slug": dept.slug,
        "description": dept.description,
        "settings": dept.settings,
        "is_active": dept.is_active,
        "created_at": dept.created_at.isoformat(),
        "updated_at": dept.updated_at.isoformat(),
    }


@router.get("")
async def list_departments(
    unit_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List departments in a unit."""
    result = await db.execute(
        select(Department).where(Department.unit_id == unit_id, Department.is_active.is_(True))
    )
    return [_dept_to_dict(d) for d in result.scalars().all()]


@router.get("/{dept_id}")
async def get_department(
    unit_id: uuid.UUID,
    dept_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get department details."""
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.unit_id == unit_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return _dept_to_dict(dept)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_department(
    unit_id: uuid.UUID,
    data: DepartmentCreate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new department."""
    # Get unit to denormalize organization_id
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    dept = Department(
        unit_id=unit_id,
        organization_id=unit.organization_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        settings=data.settings or {},
    )
    db.add(dept)
    await db.flush()
    return _dept_to_dict(dept)


@router.patch("/{dept_id}")
async def update_department(
    unit_id: uuid.UUID,
    dept_id: uuid.UUID,
    data: DepartmentUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a department."""
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.unit_id == unit_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)

    await db.flush()
    return _dept_to_dict(dept)


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    unit_id: uuid.UUID,
    dept_id: uuid.UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (deactivate) a department."""
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.unit_id == unit_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    dept.is_active = False
    await db.flush()


# Simplified endpoints for current user's organization
@simple_router.get("")
async def list_my_departments(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List departments in current user's organization."""
    if not current_user.organization_id:
        return []

    result = await db.execute(
        select(Department).where(
            Department.organization_id == current_user.organization_id,
            Department.is_active.is_(True)
        )
    )
    return [_dept_to_dict(d) for d in result.scalars().all()]
