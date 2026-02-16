"""Compliance API endpoints — GDPR data export, erasure, and privacy settings."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.contact import Contact
from app.models.privacy_settings import PrivacySettings
from app.models.user import User

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class PrivacySettingsUpdate(BaseModel):
    data_collection_consent: bool | None = None
    analytics_consent: bool | None = None
    recording_consent: bool | None = None
    data_retention_days: int | None = None
    preferences: dict[str, Any] | None = None


def _privacy_to_dict(ps: PrivacySettings) -> dict[str, Any]:
    return {
        "id": str(ps.id),
        "user_id": ps.user_id,
        "data_collection_consent": ps.data_collection_consent,
        "analytics_consent": ps.analytics_consent,
        "recording_consent": ps.recording_consent,
        "data_retention_days": ps.data_retention_days,
        "preferences": ps.preferences,
        "created_at": ps.created_at.isoformat(),
        "updated_at": ps.updated_at.isoformat(),
    }


DEFAULT_PRIVACY: dict[str, Any] = {
    "data_collection_consent": True,
    "analytics_consent": True,
    "recording_consent": False,
    "data_retention_days": 365,
    "preferences": {},
}


@router.post("/export")
async def export_user_data(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Export all user data (GDPR data portability)."""
    # Gather user profile data
    user_data: dict[str, Any] = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "department": current_user.department,
        "job_title": current_user.job_title,
        "created_at": current_user.created_at.isoformat(),
    }

    # Gather contacts
    contacts_result = await db.execute(
        select(Contact).where(Contact.user_id == current_user.id)
    )
    contacts = [
        {
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone_number": c.phone_number,
            "company_name": c.company_name,
        }
        for c in contacts_result.scalars().all()
    ]

    # Gather privacy settings
    privacy_result = await db.execute(
        select(PrivacySettings).where(PrivacySettings.user_id == current_user.id)
    )
    privacy = privacy_result.scalar_one_or_none()

    return {
        "user": user_data,
        "contacts": contacts,
        "privacy_settings": _privacy_to_dict(privacy) if privacy else DEFAULT_PRIVACY,
        "export_format": "json",
        "export_version": "1.0",
    }


@router.post("/delete", status_code=status.HTTP_200_OK)
async def delete_user_data(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete user data (GDPR right to erasure)."""
    # Delete contacts
    contacts_result = await db.execute(
        select(Contact).where(Contact.user_id == current_user.id)
    )
    for contact in contacts_result.scalars().all():
        await db.delete(contact)

    # Delete privacy settings
    privacy_result = await db.execute(
        select(PrivacySettings).where(PrivacySettings.user_id == current_user.id)
    )
    privacy = privacy_result.scalar_one_or_none()
    if privacy:
        await db.delete(privacy)

    # Log the erasure request
    audit = AuditLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="data_erasure_request",
        resource_type="user",
        resource_id=str(current_user.id),
        details={"reason": "gdpr_right_to_erasure"},
    )
    db.add(audit)

    # Deactivate user account
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.is_active = False

    await db.flush()

    return {
        "status": "completed",
        "message": "User data has been deleted and account deactivated.",
    }


@router.get("/privacy-settings")
async def get_privacy_settings(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get user privacy settings."""
    result = await db.execute(
        select(PrivacySettings).where(PrivacySettings.user_id == current_user.id)
    )
    privacy = result.scalar_one_or_none()

    if not privacy:
        return {"user_id": current_user.id, **DEFAULT_PRIVACY}

    return _privacy_to_dict(privacy)


@router.patch("/privacy-settings")
async def update_privacy_settings(
    data: PrivacySettingsUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update user privacy settings."""
    result = await db.execute(
        select(PrivacySettings).where(PrivacySettings.user_id == current_user.id)
    )
    privacy = result.scalar_one_or_none()

    if not privacy:
        # Create privacy settings record
        create_data = {
            "user_id": current_user.id,
            **{k: v for k, v in data.model_dump(exclude_unset=True).items()},
        }
        privacy = PrivacySettings(**create_data)
        db.add(privacy)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(privacy, key, value)

    await db.flush()
    return _privacy_to_dict(privacy)
