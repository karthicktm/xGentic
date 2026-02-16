"""Permission system for role-based access control.

Supports both system-level roles (UserRole) and hierarchy-level memberships.
"""

from enum import Enum

from app.models.user import User, UserRole


class Permission(str, Enum):
    """Enumeration of all available permissions."""

    # System-level permissions (SUPER_ADMIN only)
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    MANAGE_ALL_ORGANIZATIONS = "manage_all_organizations"
    VIEW_SYSTEM_AUDIT_LOGS = "view_system_audit_logs"
    MANAGE_PLATFORM_USERS = "manage_platform_users"

    # Organization-level permissions (ORG_ADMIN+)
    MANAGE_ORGANIZATION = "manage_organization"
    MANAGE_ORGANIZATION_USERS = "manage_organization_users"
    VIEW_ORGANIZATION_AUDIT_LOGS = "view_organization_audit_logs"

    # Hierarchy management (ORG_ADMIN+)
    MANAGE_UNITS = "manage_units"
    MANAGE_DEPARTMENTS = "manage_departments"
    MANAGE_PROJECTS = "manage_projects"

    # Workspace management (MANAGER+)
    CREATE_WORKSPACES = "create_workspaces"
    DELETE_WORKSPACES = "delete_workspaces"
    MANAGE_WORKSPACE = "manage_workspace"
    MANAGE_WORKSPACE_MEMBERS = "manage_workspace_members"

    # User management (ORG_ADMIN+)
    INVITE_USERS = "invite_users"
    REMOVE_USERS = "remove_users"
    CHANGE_USER_ROLES = "change_user_roles"

    # Agent management (MANAGER+)
    CREATE_AGENTS = "create_agents"
    DELETE_AGENTS = "delete_agents"
    MANAGE_AGENTS = "manage_agents"
    DEPLOY_AGENTS = "deploy_agents"
    PROMOTE_AGENTS = "promote_agents"

    # Environment management (ORG_ADMIN+)
    MANAGE_ENVIRONMENTS = "manage_environments"

    # Resource access (USER+)
    VIEW_WORKSPACE = "view_workspace"
    USE_AGENTS = "use_agents"
    VIEW_INTERACTIONS = "view_interactions"
    MANAGE_CONTACTS = "manage_contacts"
    MANAGE_CAMPAIGNS = "manage_campaigns"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_INTEGRATIONS = "manage_integrations"


# Permission matrix: maps roles to their allowed permissions
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.SUPER_ADMIN: set(Permission),  # All permissions
    UserRole.ORG_ADMIN: {
        Permission.MANAGE_ORGANIZATION,
        Permission.MANAGE_ORGANIZATION_USERS,
        Permission.VIEW_ORGANIZATION_AUDIT_LOGS,
        Permission.MANAGE_UNITS,
        Permission.MANAGE_DEPARTMENTS,
        Permission.MANAGE_PROJECTS,
        Permission.CREATE_WORKSPACES,
        Permission.DELETE_WORKSPACES,
        Permission.MANAGE_WORKSPACE,
        Permission.MANAGE_WORKSPACE_MEMBERS,
        Permission.INVITE_USERS,
        Permission.REMOVE_USERS,
        Permission.CHANGE_USER_ROLES,
        Permission.CREATE_AGENTS,
        Permission.DELETE_AGENTS,
        Permission.MANAGE_AGENTS,
        Permission.DEPLOY_AGENTS,
        Permission.PROMOTE_AGENTS,
        Permission.MANAGE_ENVIRONMENTS,
        Permission.VIEW_WORKSPACE,
        Permission.USE_AGENTS,
        Permission.VIEW_INTERACTIONS,
        Permission.MANAGE_CONTACTS,
        Permission.MANAGE_CAMPAIGNS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_INTEGRATIONS,
    },
    UserRole.MANAGER: {
        Permission.MANAGE_PROJECTS,
        Permission.CREATE_WORKSPACES,
        Permission.MANAGE_WORKSPACE,
        Permission.MANAGE_WORKSPACE_MEMBERS,
        Permission.CREATE_AGENTS,
        Permission.MANAGE_AGENTS,
        Permission.DEPLOY_AGENTS,
        Permission.PROMOTE_AGENTS,
        Permission.VIEW_WORKSPACE,
        Permission.USE_AGENTS,
        Permission.VIEW_INTERACTIONS,
        Permission.MANAGE_CONTACTS,
        Permission.MANAGE_CAMPAIGNS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_INTEGRATIONS,
    },
    UserRole.USER: {
        Permission.VIEW_WORKSPACE,
        Permission.USE_AGENTS,
        Permission.VIEW_INTERACTIONS,
        Permission.MANAGE_CONTACTS,
        Permission.MANAGE_CAMPAIGNS,
        Permission.VIEW_ANALYTICS,
    },
}


def has_permission(user: User, permission: Permission) -> bool:
    """Check if a user has a specific permission."""
    role_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return permission in role_permissions


def has_any_permission(user: User, permissions: list[Permission]) -> bool:
    """Check if a user has any of the specified permissions."""
    role_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return bool(role_permissions & set(permissions))


def has_all_permissions(user: User, permissions: list[Permission]) -> bool:
    """Check if a user has all of the specified permissions."""
    role_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return set(permissions) <= role_permissions


def get_user_permissions(user: User) -> set[Permission]:
    """Get all permissions for a user based on their role."""
    return ROLE_PERMISSIONS.get(user.role, set())


def can_manage_role(manager: User, target_role: UserRole) -> bool:
    """Check if a user can manage users with a specific role."""
    if manager.role == UserRole.SUPER_ADMIN:
        return True
    if manager.role == UserRole.ORG_ADMIN:
        return target_role in [UserRole.ORG_ADMIN, UserRole.MANAGER, UserRole.USER]
    if manager.role == UserRole.MANAGER:
        return target_role == UserRole.USER
    return False


def can_delete_user(deleter: User, target: User) -> bool:
    """Check if a user can delete another user."""
    if deleter.id == target.id:
        return False
    if deleter.role == UserRole.SUPER_ADMIN:
        return True
    if deleter.role == UserRole.ORG_ADMIN:
        return target.role != UserRole.SUPER_ADMIN
    return False
