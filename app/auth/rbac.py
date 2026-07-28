from fastapi import Request

from app.auth.models import AuthUser
from app.errors.auth import PermissionDeniedError


def check_permission(user: dict, resource: str, action: str) -> AuthUser:
    """Core RBAC rule — single source of truth for `resource:action` checks.

    The permission set lives entirely inside the JWT's `permissions` claim
    (flat scope strings, e.g. "patient:read") — no roles/permissions table.

    Raises PermissionDeniedError (403) if `resource:action` is absent.
    Returns a typed AuthUser built from the JWT's sub/activeOrganizationId.
    """
    permissions: list[str] = user.get("permissions", [])

    if f"{resource}:{action}" not in permissions:
        raise PermissionDeniedError(f"Permission denied: {resource}:{action}")

    return AuthUser(
        sub=user.get("sub", ""),
        org_id=user.get("activeOrganizationId"),
    )


def require_permission(resource: str, action: str):
    """FastAPI dependency factory — checks the caller has `resource:action`
    and returns a typed AuthUser. Requires get_current_user to have already
    populated request.state.user (applied at router level in app.main)."""

    async def _check(request: Request) -> AuthUser:
        return check_permission(request.state.user, resource, action)

    return _check
