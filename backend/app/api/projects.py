"""Project API endpoints — level 4 hierarchy."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.models.department import Department
from app.models.project import Project

router = APIRouter(prefix="/departments/{dept_id}/projects", tags=["Projects"])

# Simplified router for current user's org
simple_router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    settings: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    settings: dict[str, Any] | None = None
    is_active: bool | None = None


def _project_to_dict(project: Project) -> dict[str, Any]:
    return {
        "id": str(project.id),
        "department_id": str(project.department_id),
        "organization_id": str(project.organization_id),
        "name": project.name,
        "slug": project.slug,
        "description": project.description,
        "settings": project.settings,
        "is_active": project.is_active,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


@router.get("")
async def list_projects(
    dept_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List projects in a department."""
    result = await db.execute(
        select(Project).where(Project.department_id == dept_id, Project.is_active.is_(True))
    )
    return [_project_to_dict(p) for p in result.scalars().all()]


@router.get("/{project_id}")
async def get_project(
    dept_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get project details."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.department_id == dept_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_dict(project)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    dept_id: uuid.UUID,
    data: ProjectCreate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new project."""
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    project = Project(
        department_id=dept_id,
        organization_id=dept.organization_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        settings=data.settings or {},
    )
    db.add(project)
    await db.flush()
    return _project_to_dict(project)


@router.patch("/{project_id}")
async def update_project(
    dept_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.department_id == dept_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)

    await db.flush()
    return _project_to_dict(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    dept_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (deactivate) a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.department_id == dept_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.is_active = False
    await db.flush()


# Simplified endpoints for current user's organization
@simple_router.get("")
async def list_my_projects(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List projects in current user's organization."""
    if not current_user.organization_id:
        return []

    result = await db.execute(
        select(Project).where(
            Project.organization_id == current_user.organization_id,
            Project.is_active.is_(True)
        )
    )
    return [_project_to_dict(p) for p in result.scalars().all()]
