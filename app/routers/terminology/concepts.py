from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.schemas.terminology import LookupBatchRequest, LookupRequest
from app.terminology.client import TerminologyClient

from ._responses import _CONCEPTS_FIELD_200, _LOOKUP_200, _LOOKUP_BATCH_200, _SEARCH_200

router = APIRouter()


@router.get(
    "/search",
    operation_id="search_terminology_concepts",
    summary="Full-text search across all concepts",
    description=(
        "Searches concept display names using PostgreSQL trigram similarity. "
        "Results are ranked by relevance. Optionally filter by code system canonical URL."
    ),
    responses=_SEARCH_200,
    tags=["Terminology"],
)
async def search_concepts(
    q: str = Query(..., description="Search query, e.g. 'diabetes' or 'heart attack'"),
    system: str | None = Query(
        None,
        description="Filter by code system canonical URL, e.g. 'http://snomed.info/sct'",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.search_concepts(q, system, limit, offset)
    return JSONResponse(content=jsonable_encoder(result))


@router.post(
    "/lookup",
    operation_id="lookup_terminology_concept",
    summary="Look up a concept by system and code",
    description="Returns full concept details for a given code system URL and code. Returns found=false if the code does not exist.",
    responses=_LOOKUP_200,
    tags=["Terminology"],
)
async def lookup_concept(
    body: LookupRequest,
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.lookup(body)
    return JSONResponse(content=jsonable_encoder(result))


@router.post(
    "/lookup-batch",
    operation_id="lookup_terminology_concepts_batch",
    summary="Bulk concept lookup",
    description="Look up multiple concepts in a single request. Each item returns found=true/false independently.",
    responses=_LOOKUP_BATCH_200,
    tags=["Terminology"],
)
async def lookup_concepts_batch(
    body: LookupBatchRequest,
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.lookup_batch(body)
    return JSONResponse(content=jsonable_encoder(result))


@router.get(
    "/concepts",
    operation_id="get_terminology_concepts_for_field",
    summary="Get allowed concepts for a FHIR resource field",
    description=(
        "Returns the value set concepts bound to a specific FHIR resource field. "
        "Used to populate dropdowns and validate user input. "
        "Example: ?resource=Condition&field=clinicalStatus"
    ),
    responses=_CONCEPTS_FIELD_200,
    tags=["Terminology"],
)
async def get_concepts_for_field(
    resource: str = Query(..., description="FHIR resource type, e.g. 'Condition'"),
    field: str = Query(..., description="Field name, e.g. 'clinicalStatus'"),
    q: str | None = Query(
        None, description="Optional full-text search within the value set"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.get_concepts_for_field(resource, field, q, limit, offset)
    return JSONResponse(content=jsonable_encoder(result))
