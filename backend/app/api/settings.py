"""Settings API endpoints — user application settings."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.user_settings import UserSettings

router = APIRouter(prefix="/settings", tags=["Settings"])

DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "dark",
    "notifications_enabled": True,
    "email_notifications": True,
    "sidebar_collapsed": False,
}


class SettingsUpdate(BaseModel):
    settings: dict[str, Any]


def _settings_to_dict(user_settings: UserSettings) -> dict[str, Any]:
    return {
        "id": str(user_settings.id),
        "user_id": user_settings.user_id,
        "settings": user_settings.settings,
        "created_at": user_settings.created_at.isoformat(),
        "updated_at": user_settings.updated_at.isoformat(),
    }


@router.get("")
async def get_settings(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get user application settings."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()

    if not user_settings:
        # Return defaults if no settings record exists
        return {"user_id": current_user.id, "settings": DEFAULT_SETTINGS}

    return _settings_to_dict(user_settings)


@router.patch("")
async def update_settings(
    data: SettingsUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update user application settings."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()

    if not user_settings:
        # Create settings record if it doesn't exist
        user_settings = UserSettings(
            user_id=current_user.id,
            settings={**DEFAULT_SETTINGS, **data.settings},
        )
        db.add(user_settings)
    else:
        # Merge new settings with existing
        merged = {**user_settings.settings, **data.settings}
        user_settings.settings = merged

    await db.flush()
    return _settings_to_dict(user_settings)
