"""Workspace API endpoints — level 5 (leaf) hierarchy."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.models.project import Project
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole

router = APIRouter(prefix="/projects/{project_id}/workspaces", tags=["Workspaces"])

# Simplified router for current user's org
simple_router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class WorkspaceCreate(BaseModel):
    name: str
    description: str | None = None
    settings: dict[str, Any] | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    settings: dict[str, Any] | None = None
    is_active: bool | None = None


class WorkspaceMemberAdd(BaseModel):
    user_id: int
    role: str = "member"


def _workspace_to_dict(ws: Workspace) -> dict[str, Any]:
    return {
        "id": str(ws.id),
        "project_id": str(ws.project_id),
        "organization_id": str(ws.organization_id),
        "name": ws.name,
        "description": ws.description,
        "settings": ws.settings,
        "is_default": ws.is_default,
        "is_active": ws.is_active,
        "created_at": ws.created_at.isoformat(),
        "updated_at": ws.updated_at.isoformat(),
    }


@router.get("")
async def list_workspaces(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List workspaces in a project."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.project_id == project_id, Workspace.is_active.is_(True)
        )
    )
    return [_workspace_to_dict(ws) for ws in result.scalars().all()]


@router.get("/{workspace_id}")
async def get_workspace(
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get workspace details."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.project_id == project_id
        )
    )
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return _workspace_to_dict(ws)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    project_id: uuid.UUID,
    data: WorkspaceCreate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new workspace."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ws = Workspace(
        project_id=project_id,
        organization_id=project.organization_id,
        name=data.name,
        description=data.description,
        settings=data.settings or {},
    )
    db.add(ws)
    await db.flush()

    # Add creator as workspace admin
    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=current_user.id,
        role=WorkspaceRole.ADMIN,
    )
    db.add(member)
    await db.flush()

    return _workspace_to_dict(ws)


@router.patch("/{workspace_id}")
async def update_workspace(
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a workspace."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.project_id == project_id
        )
    )
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ws, key, value)

    await db.flush()
    return _workspace_to_dict(ws)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (deactivate) a workspace."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.project_id == project_id
        )
    )
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ws.is_active = False
    await db.flush()


@router.get("/{workspace_id}/members")
async def list_workspace_members(
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List workspace members."""
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    )
    members = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "user_id": m.user_id,
            "role": m.role.value,
            "created_at": m.created_at.isoformat(),
        }
        for m in members
    ]


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: WorkspaceMemberAdd,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Add a member to a workspace."""
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=data.user_id,
        role=WorkspaceRole(data.role),
    )
    db.add(member)
    await db.flush()
    return {
        "id": str(member.id),
        "user_id": member.user_id,
        "role": member.role.value,
    }


# Simplified endpoints for current user's organization
@simple_router.get("")
async def list_my_workspaces(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List workspaces in current user's organization."""
    if not current_user.organization_id:
        return []

    result = await db.execute(
        select(Workspace).where(
            Workspace.organization_id == current_user.organization_id,
            Workspace.is_active.is_(True)
        )
    )
    return [_workspace_to_dict(ws) for ws in result.scalars().all()]
