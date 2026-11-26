"""`GET /api/fhir/v1/metadata` — the server's CapabilityStatement
(https://www.hl7.org/fhir/R4/http.html#capabilities). Generated on the fly
from the search registries (app/fhir/capability.py); not a stored resource,
so there is no model, repository or CRUD here. Mounted by main.py's
mount_routers() whatever routes.enabled says, like /health."""

from fastapi import APIRouter, Request

from app.core.content_negotiation import FHIRJSONResponse, fhir_response
from app.core.logging import get_logger
from app.fhir.capability import build_capability_statement

logger = get_logger(__name__)

router = APIRouter(tags=["Capability"])

# Shortened to one resource and one search parameter: the real response lists every
# enabled resource with all of its parameters.
_EXAMPLE = {
    "resourceType": "CapabilityStatement",
    "status": "active",
    "date": "2026-01-15",
    "publisher": "FHIR Server",
    "kind": "instance",
    "software": {"name": "FHIR Server", "version": "1.0.0"},
    "implementation": {
        "description": "FHIR Server",
        "url": "http://localhost:8000/api/fhir/v1",
    },
    "fhirVersion": "4.0.1",
    "format": ["application/fhir+json"],
    "rest": [
        {
            "mode": "server",
            "resource": [
                {
                    "type": "Organization",
                    "profile": "http://hl7.org/fhir/StructureDefinition/Organization",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "patch"},
                        {"code": "delete"},
                        {"code": "search-type"},
                    ],
                    "versioning": "no-version",
                    "conditionalCreate": False,
                    "conditionalUpdate": False,
                    "conditionalDelete": "not-supported",
                    "searchParam": [
                        {
                            "name": "name",
                            "definition": "http://hl7.org/fhir/SearchParameter/Organization-name",
                            "type": "string",
                            "documentation": "A portion of the organization's name or alias.",
                        }
                    ],
                    "searchInclude": ["Organization:partof"],
                    "searchRevInclude": ["Location:organization"],
                }
            ],
        }
    ],
}


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
    response_class=FHIRJSONResponse,
    responses={
        200: {
            "content": {
                "application/fhir+json": {
                    "schema": {"type": "object", "example": _EXAMPLE}
                }
            }
        }
    },
)
async def get_capability_statement(request: Request):
    logger.info(
        "Get CapabilityStatement", extra={"event": "route.get_capability_statement"}
    )
    base = str(request.url_for("get_capability_statement")).rsplit("/metadata", 1)[0]
    return fhir_response(build_capability_statement(base))
