from fastapi import Request

from app.auth.models import AuthUser
from app.core.logging import get_logger
from app.core.request_context import bind_actor
from app.errors.auth import PermissionDeniedError

logger = get_logger(__name__)


def check_permission(user: dict, resource: str, action: str) -> AuthUser:
    """Core RBAC rule — single source of truth for `resource:action` checks.

    The permission set lives entirely inside the JWT's `permissions` claim
    (flat scope strings, e.g. "patient:read") — no roles/permissions table.

    Raises PermissionDeniedError (403) if `resource:action` is absent.
    Returns a typed AuthUser built from the JWT's sub/activeOrganizationId.
    """
    permissions: list[str] = user.get("permissions", [])

    if f"{resource}:{action}" not in permissions:
        logger.warning(
            "Permission denied",
            extra={
                "event": "auth.permission_denied",
                "required": f"{resource}:{action}",
                # Denial happens before bind_actor(), so the formatter has
                # nothing to inject yet — pass the actor explicitly, under the
                # same names it would have used.
                "actor_user_id": user.get("sub"),
                "actor_org_id": user.get("activeOrganizationId"),
            },
        )
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
        actor = check_permission(request.state.user, resource, action)
        # The single place that attaches the verified actor to the logging
        # context — from here on, every log line emitted for this request at
        # any layer carries user_id/org_id automatically. Also writes it to
        # request.state so middleware ABOVE this task can see it; see
        # bind_actor()'s docstring for why both are needed.
        bind_actor(request, actor.sub, actor.org_id)
        return actor

    return _check
