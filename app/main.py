from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy import text

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.database import Database
from app.core.logging import get_logger, setup_logging
from app.core.openapi_tags import OPENAPI_TAGS
from app.core.redis import redis_client
from app.di.container import container
from app.errors.base import ApplicationError
from app.errors.handlers import (
    application_error_handler,
    http_exception_handler,
    request_validation_exception_handler,
    response_validation_exception_handler,
    unhandled_exception_handler,
)
from app.middleware import (
    AccessLogMiddleware,
    RateLimitMiddleware,
    request_context_middleware,
)
from app.routers import discover_routers
from app.routers.fhir_profile import router as fhir_profile_router
from app.routers.fhir_validate import router as fhir_validate_router
from app.routers.terminology import router as terminology_router

setup_logging()
logger = get_logger(__name__)

db: Database = container.core.database()


async def log_route_entry(request: Request) -> None:
    """DEBUG-level route-handler entry line — the top of the per-request flow
    trace, above the service/repository lines that app.core.logging's
    trace_methods emits. Applied once as a router-level dependency below, so
    it covers every route of every mounted resource with no per-handler code.
    Silent at INFO."""
    if not logger.isEnabledFor(10):  # logging.DEBUG
        return
    route = request.scope.get("route")
    logger.debug(
        "Route entered",
        extra={
            "event": "route.entered",
            "operation_id": getattr(route, "operation_id", None)
            or getattr(route, "name", None),
            "path_params": dict(request.path_params),
            "query_params": dict(request.query_params),
        },
    )


# Tags that exist regardless of routes.enabled — Health is defined
# directly on `app`, not gated by any router mount at all. Terminology/
# FHIR Profiles/FHIR Validation are NOT here (unlike before) — they're
# now gated by routes.enabled same as everything else in
# _OWN_PREFIX_ROUTERS, so their tags only show up in the docs when
# actually mounted, via the same active_tags.update(router.tags) call
# every other mounted router gets.
_ALWAYS_ON_TAGS = {"Health"}


# Mounted via mount_routers() under their OWN distinct prefix, not merged
# into the shared /api/fhir/v1 api_router below — they aren't FHIR
# resources with public sequence IDs, so folding them into that generic
# mechanism would also move their URLs under /api/fhir/v1. Still driven by
# the exact same routes.enabled set as everything else, computed once in
# mount_routers() — see that function's own docstring for why this used to
# be a second, separate module-level check instead, and why that was
# actually a real bug (duplicate-mounted routes, confirmed via duplicate-
# operation-id warnings at startup).
_OWN_PREFIX_ROUTERS: tuple[tuple[str, APIRouter, dict], ...] = (
    (
        "terminology",
        terminology_router,
        {"prefix": "/api/v1/terminology", "tags": ["Terminology"]},
    ),
    ("fhir_profile", fhir_profile_router, {"prefix": "/api/v1"}),
    ("fhir_validate", fhir_validate_router, {"prefix": "/api/v1"}),
)


def mount_routers(app: FastAPI) -> None:
    """Discovers + conditionally mounts every FHIR resource router, plus
    the handful of own-prefix routers in _OWN_PREFIX_ROUTERS above, based
    on configs/config.yaml's routes.enabled list (see
    app.routers.discover_routers()). Called from lifespan() below at
    actual ASGI startup — mirrors txtai's api/application.py::lifespan()
    pattern of mounting at startup rather than at module-import time.
    Kept as a standalone sync function (not inlined into lifespan) so
    tests/conftest.py can call it directly once, since httpx's
    ASGITransport doesn't run the ASGI lifespan protocol on its own.
    get_current_user runs once for every route mounted here — decodes the
    JWT and sets request.state.user. Individual routes add
    require_permission(...) on top for fine-grained access control
    (currently wired for Patient/Practitioner/Organization only).

    One `enabled_routes` set, computed once here, is the only thing either
    group checks — deliberately not two separate checks living in two
    separate places, which is exactly what caused the duplicate-mount bug
    this replaced.

    Also filters app.openapi_tags down to the tags actually in play, so a
    resource left out of routes.enabled doesn't show an empty tag group in
    Swagger UI — the same config that decides what's mounted now decides
    what's documented."""
    enabled_routes = set(settings.routes.enabled)
    api_router = APIRouter()
    active_tags = set(_ALWAYS_ON_TAGS)
    for name, router in discover_routers().items():
        if name in enabled_routes:
            api_router.include_router(router)
            active_tags.update(router.tags)
    logger.info(
        "Mounted resource routers",
        extra={
            "event": "startup.routes_mounted",
            "count": len(enabled_routes),
            "routes": sorted(enabled_routes),
        },
    )
    app.include_router(
        api_router,
        prefix="/api/fhir/v1",
        dependencies=[Depends(get_current_user), Depends(log_route_entry)],
    )

    for name, router, kwargs in _OWN_PREFIX_ROUTERS:
        if name in enabled_routes:
            app.include_router(
                router, dependencies=[Depends(get_current_user)], **kwargs
            )
            active_tags.update(router.tags)

    app.openapi_tags = [tag for tag in OPENAPI_TAGS if tag["name"] in active_tags]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One config summary at startup — answers most "why is this environment
    # behaving differently" questions straight from the log stream, without
    # needing shell access to the running container.
    logger.info(
        "🟢 Starting up the application",
        extra={
            "event": "startup.begin",
            "environment": settings.ENVIRONMENT,
            "log_level": settings.logging.level,
            "log_format": settings.logging.format,
            "debug_payloads": settings.logging.debug_payloads,
            "slow_query_ms": settings.logging.slow_query_ms,
            "redis_enabled": settings.redis.enabled,
            "rate_limit_backend": settings.rate_limit.backend,
        },
    )

    if settings.logging.debug_payloads:
        logger.warning(
            "debug_payloads is ENABLED — full request payloads (including PHI) "
            "are being written to the log stream. Local development only.",
            extra={"event": "startup.phi_logging_enabled"},
        )

    await db.create_extensions()

    mount_routers(app)

    if settings.redis.enabled:
        try:
            await cast(Any, redis_client.ping())
            app.state.redis = redis_client
            logger.info(
                "Connected to Redis successfully.",
                extra={"event": "startup.redis_connected"},
            )
        except Exception as e:
            logger.error(
                "Failed to connect to Redis.",
                extra={"event": "startup.redis_failed"},
                exc_info=e,
            )
            app.state.redis = None
    else:
        # Deliberately disabled, not an outage — INFO, not ERROR. Every
        # Redis-backed dependent already has its backend forced to the
        # non-Redis fallback by Settings._apply_redis_switch().
        logger.info(
            "Redis disabled by config — dependent features run in their "
            "non-Redis fallback (e.g. rate limiting is process-local only).",
            extra={"event": "startup.redis_disabled"},
        )
        app.state.redis = None
    yield

    logger.info("🔴 Shutting down application...", extra={"event": "shutdown.begin"})
    await db.disconnect()

    logger.info("Database engine disposed.", extra={"event": "shutdown.db_disposed"})


app: FastAPI = FastAPI(
    title=settings.app.title,
    version=settings.app.version,
    description=(
        "FHIR R4-compliant REST API server for managing healthcare resources. "
        "Supports 34 FHIR R4 resources with dual-format responses (application/json and "
        "application/fhir+json). Pure CRUD data layer — no auth, no business rules. "
        "Designed for integration with AI agents via FastMCP dynamic tool generation."
    ),
    # docs_enabled gates only the interactive Swagger/Redoc UIs — openapi_url
    # is never gated (left at its default), since /openapi.json is the
    # FastMCP contract (see CLAUDE.md's "OpenAPI Spec = MCP Contract") and
    # must stay reachable regardless.
    docs_url="/docs" if settings.app.docs_enabled else None,
    redoc_url="/redoc" if settings.app.docs_enabled else None,
    lifespan=lifespan,
)

app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(
    ResponseValidationError, response_validation_exception_handler
)
app.add_exception_handler(HTTPException, http_exception_handler)

app.container = container

# Middleware order matters — Starlette runs the LAST-added one outermost:
#   cors (outermost, only if enabled — must see preflight OPTIONS before
#         anything else can reject them)
#     -> request_context (establishes request_id before anything logs)
#       -> access_log      (records every response, including 429s below it)
#         -> rate_limit    (innermost)
app.add_middleware(
    RateLimitMiddleware,
    backend=settings.rate_limit.backend,
    read_limit=settings.rate_limit.read_limit,
    write_limit=settings.rate_limit.write_limit,
    window_seconds=settings.rate_limit.window_seconds,
)
app.add_middleware(AccessLogMiddleware)
app.middleware("http")(request_context_middleware)

if settings.cors.enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

# Scalar renders the same /openapi.json as /docs and /redoc — no spec
# changes, just a nicer UI with a built-in light/dark toggle neither of
# those ship with. Gated by docs_enabled the same way /docs and /redoc are
# (the route isn't registered at all when disabled, same "doesn't exist"
# behavior FastAPI's own docs_url=None gives those two).
if settings.app.docs_enabled:
    @app.get("/docs/scalar", include_in_schema=False)
    async def scalar_docs():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url, title=app.title
        )


# ── OpenAPI schema override ────────────────────────────────────────────────────
# FastAPI has no constructor param for top-level `security`/`securitySchemes` —
# override app.openapi() to inject them so Swagger UI shows the Authorize
# button. Cached on app.openapi_schema after the first call.
def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT access token (without the 'Bearer ' prefix).",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _custom_openapi  # type: ignore[method-assign]


@app.get(
    "/health",
    operation_id="health_check",
    summary="Liveness probe",
    description=(
        "Returns 200 if the process is running. "
        "Use for liveness probes — does not check DB or Redis. "
        "No authentication required."
    ),
    response_description="Process is alive",
    tags=["Health"],
)
async def health_check(request: Request):
    return JSONResponse(content={"status": "ok", "req_id": request.state.request_id})


@app.get(
    "/health/ready",
    operation_id="readiness_check",
    summary="Readiness probe",
    description=(
        "Returns 200 only when the database and Redis are reachable. "
        "Use for readiness probes — orchestrators should stop routing traffic "
        "to this instance when it returns 503. No authentication required."
    ),
    response_description="All dependencies are reachable",
    tags=["Health"],
    responses={503: {"description": "One or more dependencies are unavailable"}},
)
async def readiness_check(request: Request):
    checks: dict[str, str] = {}
    healthy = True

    # Database check
    try:
        async with db.session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.error("Readiness: database check failed", exc_info=exc)
        checks["database"] = "unavailable"
        healthy = False

    # Redis check — disabled by config is a healthy state, not a degradation.
    if not settings.redis.enabled:
        checks["redis"] = "disabled"
    else:
        redis = getattr(request.app.state, "redis", None)
        if redis is not None:
            try:
                await redis.ping()
                checks["redis"] = "ok"
            except Exception as exc:
                logger.error("Readiness: Redis check failed", exc_info=exc)
                checks["redis"] = "unavailable"
                healthy = False
        else:
            checks["redis"] = "unavailable"
            healthy = False

    payload = {
        "status": "ok" if healthy else "degraded",
        "req_id": request.state.request_id,
        "checks": checks,
    }
    return JSONResponse(content=payload, status_code=200 if healthy else 503)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


"""
Common Mertics:
 - CPU Usage
 - Memory Usage
 - Response Time
 - Server Load
 - Network Traffic
 - Database Queries

Observability:
 - Logs
 - Metrics
 _ Traces
"""
# python.analysis.typeCheckingMode

# observability
# deterministic execution
# auditability
# retries
# tracing
# idempotency
# failure recovery
