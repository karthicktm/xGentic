"""User management API endpoints — org member listing and admin operations."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.models.user import User, UserRole

router = APIRouter(prefix="/users", tags=["Users"])


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    department: str | None = None
    job_title: str | None = None
    is_active: bool | None = None


def _user_to_dict(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        "department": user.department,
        "job_title": user.job_title,
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@router.get("")
async def list_users(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List organization members."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    query = (
        select(User)
        .where(
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
        )
        .order_by(User.created_at.asc())
    )
    result = await db.execute(query)
    return [_user_to_dict(u) for u in result.scalars().all()]


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get user details."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure user belongs to the same organization
    if user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return _user_to_dict(user)


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a user. Requires admin privileges."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = data.model_dump(exclude_unset=True)
    if "role" in update_data:
        update_data["role"] = UserRole(update_data["role"])

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.flush()
    return _user_to_dict(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deactivate a user. Requires admin privileges."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user.is_active = False
    await db.flush()
