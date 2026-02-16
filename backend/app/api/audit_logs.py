"""Audit log API endpoints — compliance and security event viewing."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser
from app.db.session import get_db
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


def _audit_log_to_dict(log: AuditLog) -> dict[str, Any]:
    return {
        "id": str(log.id),
        "user_id": log.user_id,
        "organization_id": str(log.organization_id) if log.organization_id else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at.isoformat(),
    }


@router.get("")
async def list_audit_logs(
    current_user: AdminUser,
    action: str | None = Query(None),
    user_id: int | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List audit logs with optional filters. Requires admin privileges."""
    query = select(AuditLog).where(
        AuditLog.organization_id == current_user.organization_id
    )

    if action:
        query = query.where(AuditLog.action == action)
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)

    query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return [_audit_log_to_dict(log) for log in result.scalars().all()]


@router.get("/{log_id}")
async def get_audit_log(
    log_id: uuid.UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get audit log details. Requires admin privileges."""
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.id == log_id,
            AuditLog.organization_id == current_user.organization_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return _audit_log_to_dict(log)
