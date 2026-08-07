import uuid

from fastapi import Request

from app.core.request_context import (
    actor_org_id_ctx_var,
    actor_user_id_ctx_var,
    request_id_ctx_var,
)

# Header carrying an upstream-assigned correlation id. The fhir-gql gateway is
# the only externally-facing surface, so in production this is set there and
# inherited here — the same id then spans both services in the log stream.
REQUEST_ID_HEADER = "X-Request-ID"


async def request_context_middleware(request: Request, call_next):
    """Establishes the per-request logging context and echoes the correlation
    id back to the caller.

    Inherits X-Request-ID when the caller supplies one (the gateway does) and
    only mints a fresh uuid4 when it doesn't — so a trace started upstream
    isn't broken by this server silently generating its own id.
    """
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

    request_id_ctx_var.set(request_id)
    # The actor fields are per-request too, but this middleware runs before
    # auth — reset them here so a recycled worker task can't leak the previous
    # request's actor into an unauthenticated route's logs.
    actor_user_id_ctx_var.set(None)
    actor_org_id_ctx_var.set(None)

    # Also attach to request.state, for handlers that have the Request in hand.
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers[REQUEST_ID_HEADER] = request_id

    return response
