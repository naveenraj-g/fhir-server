from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.terminology.client import TerminologyClient

from ._responses import _AUDIT_LOG_200

router = APIRouter()


@router.get(
    "/audit-log",
    operation_id="list_terminology_audit_log",
    summary="List terminology governance audit log",
    description=(
        "Returns a paginated audit trail of all org-concept changes. "
        "Filterable by action (org_concept.created, org_concept.updated, org_concept.deleted), "
        "performer (user sub), or specific concept ID."
    ),
    responses=_AUDIT_LOG_200,
    tags=["Terminology"],
)
async def list_audit_log(
    action: str | None = Query(
        None, description="Filter by action type, e.g. 'org_concept.created'"
    ),
    performed_by: str | None = Query(
        None, description="Filter by user sub who performed the action"
    ),
    concept_id: int | None = Query(None, description="Filter by concept ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.list_audit_log(
        action, performed_by, concept_id, limit, offset
    )
    return JSONResponse(content=jsonable_encoder(result))
