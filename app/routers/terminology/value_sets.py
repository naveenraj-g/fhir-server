from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.terminology.client import TerminologyClient

from ._responses import _VS_EXPAND_200, _VS_LIST_200

router = APIRouter()


@router.get(
    "/value-sets",
    operation_id="list_terminology_value_sets",
    summary="List value sets",
    description="Returns paginated value sets. Supports keyword search by name, title, or canonical URL.",
    responses=_VS_LIST_200,
    tags=["Terminology"],
)
async def list_value_sets(
    q: str | None = Query(
        None, description="Keyword filter on name, title, or canonical URL"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.list_value_sets(q, limit, offset)
    return JSONResponse(content=jsonable_encoder(result))


@router.get(
    "/value-sets/{value_set_id}/expand",
    operation_id="expand_terminology_value_set",
    summary="Expand a value set",
    description="Returns the paginated list of concepts belonging to a value set. Supports optional full-text search within the set.",
    responses={**_VS_EXPAND_200, 404: {"description": "Value set not found"}},
    tags=["Terminology"],
)
async def expand_value_set(
    value_set_id: int,
    q: str | None = Query(None, description="Full-text search within the value set"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.expand_value_set(value_set_id, q, limit, offset)
    if result is None:
        raise HTTPException(status_code=404, detail="Value set not found")
    return JSONResponse(content=jsonable_encoder(result))
