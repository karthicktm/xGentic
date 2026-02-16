"""Audit logging for sensitive operations."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Sensitive fields to sanitize in audit logs
SENSITIVE_FIELDS = {"password", "api_key", "token", "secret", "credentials", "private_key"}


class AuditAction:
    """Audit action constants."""

    # Auth
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    SSO_LOGIN = "auth.sso_login"
    REGISTER = "auth.register"
    PASSWORD_CHANGE = "auth.password_change"

    # Organization hierarchy
    ORG_CREATE = "organization.create"
    ORG_UPDATE = "organization.update"
    ORG_DELETE = "organization.delete"
    UNIT_CREATE = "unit.create"
    UNIT_UPDATE = "unit.update"
    UNIT_DELETE = "unit.delete"
    DEPT_CREATE = "department.create"
    DEPT_UPDATE = "department.update"
    DEPT_DELETE = "department.delete"
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"
    WORKSPACE_CREATE = "workspace.create"
    WORKSPACE_UPDATE = "workspace.update"
    WORKSPACE_DELETE = "workspace.delete"

    # Agents
    AGENT_CREATE = "agent.create"
    AGENT_UPDATE = "agent.update"
    AGENT_DELETE = "agent.delete"
    AGENT_DEPLOY = "agent.deploy"
    AGENT_PROMOTE = "agent.promote"
    AGENT_ROLLBACK = "agent.rollback"

    # Environments
    ENV_CREATE = "environment.create"
    ENV_UPDATE = "environment.update"
    ENV_DELETE = "environment.delete"

    # Users
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"

    # Integrations
    INTEGRATION_CONNECT = "integration.connect"
    INTEGRATION_DISCONNECT = "integration.disconnect"

    # Compliance
    DATA_EXPORT = "compliance.data_export"
    DATA_DELETE = "compliance.data_delete"

    # Contacts
    CONTACT_CREATE = "contact.create"
    CONTACT_UPDATE = "contact.update"
    CONTACT_DELETE = "contact.delete"
    CONTACT_IMPORT = "contact.import"


def _sanitize_details(details: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive values from audit log details."""
    sanitized = {}
    for key, value in details.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_details(value)
        else:
            sanitized[key] = value
    return sanitized


def audit_log(
    action: str,
    user_id: int | None = None,
    organization_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """Log an audit event."""
    sanitized_details = _sanitize_details(details) if details else {}

    logger.info(
        "Audit: %s",
        action,
        extra={
            "audit_action": action,
            "user_id": user_id,
            "organization_id": organization_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": sanitized_details,
            "ip_address": ip_address,
        },
    )
