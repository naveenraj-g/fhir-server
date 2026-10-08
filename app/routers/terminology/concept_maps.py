from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.schemas.terminology import AddConceptMapRequest
from app.terminology.client import TerminologyClient

from ._responses import _CONCEPT_MAPS_200

router = APIRouter()


@router.get(
    "/concept-maps",
    operation_id="list_concept_maps",
    summary="List cross-system concept mappings",
    description="Returns all stored concept mappings. Optionally filter by source or target code system URL.",
    responses=_CONCEPT_MAPS_200,
    tags=["Terminology"],
)
async def list_concept_maps(
    source_system: str | None = Query(
        None, description="Filter by source code system canonical URL"
    ),
    target_system: str | None = Query(
        None, description="Filter by target code system canonical URL"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.list_concept_maps(
        source_system, target_system, limit, offset
    )
    return JSONResponse(content=result.model_dump())


@router.post(
    "/concept-maps",
    operation_id="add_concept_map",
    summary="Manually add a concept map entry",
    description="Creates a cross-system mapping between two concepts that are already loaded in the database.",
    responses={
        200: {"content": {"application/json": {"schema": {"type": "object"}}}},
        422: {"description": "Source or target concept not found in DB"},
    },
    tags=["Terminology"],
)
async def add_concept_map(
    body: AddConceptMapRequest,
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.add_concept_map(body)
    return JSONResponse(content=result)
