"""`GET /api/fhir/v1/metadata` — the server's CapabilityStatement
(https://www.hl7.org/fhir/R4/http.html#capabilities). Generated on the fly
from the search registries (app/fhir/capability.py); not a stored resource,
so there is no model, repository or CRUD here. Mounted by main.py's
mount_routers() whatever routes.enabled says, like /health."""

from fastapi import APIRouter, Request

from app.core.content_negotiation import fhir_response
from app.core.logging import get_logger
from app.fhir.capability import build_capability_statement

logger = get_logger(__name__)

router = APIRouter(tags=["Capability"])


@router.get(
    "/metadata",
    operation_id="get_capability_statement",
    summary="CapabilityStatement — what this server supports (FHIR R4 /metadata)",
    description=(
        "Real FHIR R4 CapabilityStatement, built from each resource's search registry: "
        "per resource the interactions, every search parameter (type, modifiers, chaining, "
        "sortable), and the supported `_include` / `_revinclude` targets. Only resources "
        "that run on the FHIR R4 search engine are listed."
    ),
    responses={200: {"content": {"application/fhir+json": {"schema": {"type": "object"}}}}},
)
async def get_capability_statement(request: Request):
    logger.info("Get CapabilityStatement", extra={"event": "route.get_capability_statement"})
    base = str(request.url_for("get_capability_statement")).rsplit("/metadata", 1)[0]
    return fhir_response(build_capability_statement(base))
