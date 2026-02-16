"""Hierarchy tree API — flat endpoint for full org navigation."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.department import Department
from app.models.organization import Organization
from app.models.project import Project
from app.models.unit import Unit
from app.models.workspace import Workspace

router = APIRouter(prefix="/hierarchy", tags=["Hierarchy"])


@router.get("/tree")
async def get_hierarchy_tree(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get full organization hierarchy tree for navigation.

    Returns nested structure: Org > Units > Departments > Projects > Workspaces
    """
    # Get organizations the user has access to
    if current_user.role.value == "super_admin":
        org_query = select(Organization).where(Organization.is_active.is_(True))
    elif current_user.organization_id:
        org_query = select(Organization).where(
            Organization.id == current_user.organization_id,
            Organization.is_active.is_(True),
        )
    else:
        return []

    org_result = await db.execute(org_query)
    orgs = org_result.scalars().all()
    tree = []

    for org in orgs:
        # Load units
        units_result = await db.execute(
            select(Unit).where(Unit.organization_id == org.id, Unit.is_active.is_(True))
        )
        units = units_result.scalars().all()

        unit_nodes = []
        for unit in units:
            # Load departments
            depts_result = await db.execute(
                select(Department).where(
                    Department.unit_id == unit.id, Department.is_active.is_(True)
                )
            )
            depts = depts_result.scalars().all()

            dept_nodes = []
            for dept in depts:
                # Load projects
                projects_result = await db.execute(
                    select(Project).where(
                        Project.department_id == dept.id, Project.is_active.is_(True)
                    )
                )
                projects = projects_result.scalars().all()

                project_nodes = []
                for project in projects:
                    # Load workspaces
                    ws_result = await db.execute(
                        select(Workspace).where(
                            Workspace.project_id == project.id, Workspace.is_active.is_(True)
                        )
                    )
                    workspaces = ws_result.scalars().all()

                    project_nodes.append({
                        "id": str(project.id),
                        "name": project.name,
                        "slug": project.slug,
                        "type": "project",
                        "workspaces": [
                            {
                                "id": str(ws.id),
                                "name": ws.name,
                                "is_default": ws.is_default,
                                "type": "workspace",
                            }
                            for ws in workspaces
                        ],
                    })

                dept_nodes.append({
                    "id": str(dept.id),
                    "name": dept.name,
                    "slug": dept.slug,
                    "type": "department",
                    "projects": project_nodes,
                })

            unit_nodes.append({
                "id": str(unit.id),
                "name": unit.name,
                "slug": unit.slug,
                "type": "unit",
                "departments": dept_nodes,
            })

        tree.append({
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "type": "organization",
            "units": unit_nodes,
        })

    return tree
