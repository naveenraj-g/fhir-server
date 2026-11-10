"""`TerminologyCapabilities` — see
docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §6.

Spec's own retrieval convention is `GET [base]/metadata?mode=terminology`,
where `[base]` is the whole FHIR server's root. This app doesn't have an
app-wide `/metadata`/`CapabilityStatement` endpoint yet (a separate,
broader, still-deferred gap — see 08 §7), so this is mounted at this
router's own base instead: `GET /api/v1/terminology/metadata`. `mode` is
accepted (so a client sending the spec's own query string doesn't 422)
but not actually branching on anything — this path only ever returns
`TerminologyCapabilities`, never a general `CapabilityStatement`."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.terminology.client import TerminologyClient

router = APIRouter()


@router.get(
    "/metadata",
    operation_id="get_terminology_capabilities",
    summary="TerminologyCapabilities — what this deployment actually supports",
    description=(
        "Real FHIR R4 TerminologyCapabilities resource: which code systems "
        "(and versions) are loaded, which have subsumption/hierarchy data, "
        "and which operations/parameters this server implements. See "
        "docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §6."
    ),
    responses={200: {"content": {"application/json": {"schema": {"type": "object"}}}}},
    tags=["Terminology"],
)
async def get_terminology_capabilities(
    mode: str | None = Query(
        None, description="Accepted for spec compatibility (?mode=terminology); not branched on."
    ),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.get_terminology_capabilities()
    return JSONResponse(content=result)
