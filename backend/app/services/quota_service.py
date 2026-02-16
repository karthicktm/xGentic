"""Quota service for checking and enforcing resource limits.

This module provides the core quota checking logic for the organization-level
quota system. It checks quotas at applicable levels (organization -> user -> agent)
and enforces the STRICTER limit at any level.
"""

import uuid
from typing import NamedTuple

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quota import AgentQuota, UserQuota

logger = structlog.get_logger()


class QuotaCheckResult(NamedTuple):
    """Result of a quota check."""

    allowed: bool
    reason: str
    current_usage: float
    limit: float | None
    remaining: float | None


async def check_user_quota(
    db: AsyncSession,
    user_id: int,
    resource_type: str,
    amount: float,
) -> QuotaCheckResult:
    """Check if a user has quota available for a resource.

    Args:
        db: Database session
        user_id: User to check
        resource_type: Type of resource (e.g., voice_minutes, chat_messages, tokens)
        amount: Amount to check against quota

    Returns:
        QuotaCheckResult indicating if request is allowed
    """
    log = logger.bind(user_id=user_id, resource_type=resource_type)

    # Get user quota for the specific resource type
    quota = await db.scalar(
        select(UserQuota).where(
            UserQuota.user_id == user_id,
            UserQuota.resource_type == resource_type,
        )
    )

    if not quota:
        # No quota defined means unlimited
        log.debug("no_user_quota_defined")
        return QuotaCheckResult(
            allowed=True,
            reason="No user-specific limits defined",
            current_usage=0,
            limit=None,
            remaining=None,
        )

    remaining = quota.limit_value - quota.used_value
    if quota.used_value + amount > quota.limit_value:
        log.warning(
            "user_quota_exceeded",
            current=quota.used_value,
            limit=quota.limit_value,
            requested=amount,
        )
        return QuotaCheckResult(
            allowed=False,
            reason=f"User quota exceeded for {resource_type}: {quota.used_value}/{quota.limit_value} used",
            current_usage=quota.used_value,
            limit=quota.limit_value,
            remaining=remaining,
        )

    return QuotaCheckResult(
        allowed=True,
        reason="Within quota",
        current_usage=quota.used_value,
        limit=quota.limit_value,
        remaining=remaining,
    )


async def check_agent_quota(
    db: AsyncSession,
    agent_id: uuid.UUID,
    resource_type: str,
    amount: float,
) -> QuotaCheckResult:
    """Check if an agent has quota available.

    Args:
        db: Database session
        agent_id: Agent to check
        resource_type: Type of resource
        amount: Amount to check

    Returns:
        QuotaCheckResult indicating if request is allowed
    """
    log = logger.bind(agent_id=str(agent_id), resource_type=resource_type)

    quota = await db.scalar(
        select(AgentQuota).where(
            AgentQuota.agent_id == agent_id,
            AgentQuota.resource_type == resource_type,
        )
    )

    if not quota:
        log.debug("no_agent_quota_defined")
        return QuotaCheckResult(
            allowed=True,
            reason="No agent-specific limits defined",
            current_usage=0,
            limit=None,
            remaining=None,
        )

    remaining = quota.limit_value - quota.used_value
    if quota.used_value + amount > quota.limit_value:
        log.warning(
            "agent_quota_exceeded",
            current=quota.used_value,
            limit=quota.limit_value,
            requested=amount,
        )
        return QuotaCheckResult(
            allowed=False,
            reason=f"Agent quota exceeded for {resource_type}: {quota.used_value}/{quota.limit_value}",
            current_usage=quota.used_value,
            limit=quota.limit_value,
            remaining=remaining,
        )

    return QuotaCheckResult(
        allowed=True,
        reason="Within quota",
        current_usage=quota.used_value,
        limit=quota.limit_value,
        remaining=remaining,
    )


async def check_quota(
    db: AsyncSession,
    resource_type: str,
    amount: float,
    user_id: int | None = None,
    agent_id: uuid.UUID | None = None,
) -> QuotaCheckResult:
    """Check all applicable quotas for a resource request.

    Enforces the STRICTER limit at any level of the hierarchy.
    Checks are performed in order: user -> agent

    Args:
        db: Database session
        resource_type: Type of resource
        amount: Amount being requested
        user_id: Optional user context
        agent_id: Optional agent context

    Returns:
        QuotaCheckResult from the strictest applicable limit
    """
    log = logger.bind(
        resource_type=resource_type,
        amount=amount,
        user_id=user_id,
        agent_id=str(agent_id) if agent_id else None,
    )

    # Check user quota if user_id provided
    if user_id is not None:
        result = await check_user_quota(db, user_id, resource_type, amount)
        if not result.allowed:
            log.info("quota_denied_user", reason=result.reason)
            return result

    # Check agent quota if agent_id provided
    if agent_id is not None:
        result = await check_agent_quota(db, agent_id, resource_type, amount)
        if not result.allowed:
            log.info("quota_denied_agent", reason=result.reason)
            return result

    log.debug("quota_check_passed")
    return QuotaCheckResult(
        allowed=True,
        reason="All quota checks passed",
        current_usage=0,
        limit=None,
        remaining=None,
    )


async def record_usage(
    db: AsyncSession,
    resource_type: str,
    amount: float,
    user_id: int | None = None,
    agent_id: uuid.UUID | None = None,
) -> None:
    """Record resource usage by incrementing the used_value on matching quotas.

    Args:
        db: Database session
        resource_type: Type of resource used
        amount: Amount consumed
        user_id: Optional user context
        agent_id: Optional agent context
    """
    # Increment user quota usage
    if user_id is not None:
        quota = await db.scalar(
            select(UserQuota).where(
                UserQuota.user_id == user_id,
                UserQuota.resource_type == resource_type,
            )
        )
        if quota:
            quota.used_value += amount

    # Increment agent quota usage
    if agent_id is not None:
        quota = await db.scalar(
            select(AgentQuota).where(
                AgentQuota.agent_id == agent_id,
                AgentQuota.resource_type == resource_type,
            )
        )
        if quota:
            quota.used_value += amount

    await db.flush()

    logger.info(
        "usage_recorded",
        resource_type=resource_type,
        amount=amount,
        user_id=user_id,
        agent_id=str(agent_id) if agent_id else None,
    )
