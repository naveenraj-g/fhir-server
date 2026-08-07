"""Per-request context, carried in ContextVars rather than threaded through
function signatures.

Why ContextVars: a repository method has no access to the `Request` object and
never will — passing `request_id` down through ~35 repositories x ~15 methods
each is not viable. `app.core.logging.JsonFormatter` reads these directly, so
any log line emitted anywhere below the router — service, repository, mapper —
automatically carries the request's correlation fields with zero plumbing at
the call site.

Each asyncio task gets its own copy, so concurrent requests never bleed into
each other.

Set by:
  - request_id  -> app.middleware.request_context.request_context_middleware
  - user_id     -> app.auth.rbac.require_permission (once the JWT is verified)
  - org_id      -> app.auth.rbac.require_permission (activeOrganizationId claim)

This module holds the ContextVars only. The middleware that populates
request_id lives in app/middleware/request_context.py.
"""

from contextvars import ContextVar

request_id_ctx_var: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

# Acting user's `sub` claim — only populated on auth-gated routes.
#
# Deliberately named `actor_*`, not `user_id`/`org_id`: rows and request
# payloads carry their OWN user_id/org_id columns (see CLAUDE.md's Standard
# Columns), so an unqualified `user_id` in a log line would be ambiguous —
# is it the caller, or the record being operated on? `actor_` always means
# "who made this request", read from the verified JWT.
actor_user_id_ctx_var: ContextVar[str | None] = ContextVar(
    "actor_user_id",
    default=None,
)

# Acting user's `activeOrganizationId` claim — the tenant every query is
# scoped to. The first thing anyone filters logs by on a multi-tenant server.
actor_org_id_ctx_var: ContextVar[str | None] = ContextVar(
    "actor_org_id",
    default=None,
)


def bind_actor(request, user_id: str | None, org_id: str | None) -> None:
    """Attach the verified actor to the request's logging context. Called from
    app.auth.rbac.require_permission once check_permission() has returned a
    typed AuthUser — a single place that covers every auth-gated route.

    Writes to BOTH the ContextVars and request.state, because they propagate
    in opposite directions:

    - ContextVars flow **downward** only. Starlette's BaseHTTPMiddleware runs
      the downstream app in a child anyio task, which copies the context at
      creation — so a value set here (inside the route's dependency, i.e. in
      that child task) is visible to the service, repository and mappers
      below it, but is INVISIBLE to any middleware above, which is still
      sitting in the parent context. That's why request_id (set in the
      outermost middleware) reaches everything, while the actor set here
      cannot reach back up.
    - request.state is backed by the shared `scope` dict, which is the same
      object all the way up and down the stack — so the access-log
      middleware can read it after call_next() returns.
    """
    actor_user_id_ctx_var.set(user_id)
    actor_org_id_ctx_var.set(org_id)
    request.state.actor_user_id = user_id
    request.state.actor_org_id = org_id


def get_request_actor(request) -> dict[str, str]:
    """Actor fields off request.state — for middleware, which runs outside the
    task where the ContextVars were set. See bind_actor()."""
    actor = {
        "actor_user_id": getattr(request.state, "actor_user_id", None),
        "actor_org_id": getattr(request.state, "actor_org_id", None),
    }
    return {k: v for k, v in actor.items() if v is not None}


def get_log_context() -> dict[str, str]:
    """Snapshot of the non-None context fields, for injection into a log
    record. Used by both the JSON and console formatters.

    Keys are `actor_user_id`/`actor_org_id`, never bare `user_id`/`org_id` —
    resource rows and request payloads have their own columns by those names,
    and the log line must make clear which is which.
    """
    ctx = {
        "request_id": request_id_ctx_var.get(),
        "actor_user_id": actor_user_id_ctx_var.get(),
        "actor_org_id": actor_org_id_ctx_var.get(),
    }
    return {k: v for k, v in ctx.items() if v is not None}
