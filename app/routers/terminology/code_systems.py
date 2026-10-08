from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.terminology.client import TerminologyClient

from ._responses import _CS_LIST_200

router = APIRouter()


@router.get(
    "/code-systems",
    operation_id="list_terminology_code_systems",
    summary="List all loaded code systems",
    description="Returns all active terminology code systems loaded in the platform (FHIR R4, ICD-10-CM, LOINC, RxNorm, SNOMED CT).",
    responses=_CS_LIST_200,
    tags=["Terminology"],
)
async def list_code_systems(
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.list_code_systems()
    return JSONResponse(content=jsonable_encoder(result))
