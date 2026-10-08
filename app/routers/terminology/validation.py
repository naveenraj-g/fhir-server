from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.schemas.terminology import TranslateRequest, ValidateRequest
from app.terminology.client import TerminologyClient

from ._responses import _TRANSLATE_200, _VALIDATE_200

router = APIRouter()


@router.post(
    "/validate",
    operation_id="validate_terminology_code",
    summary="Validate a code against a FHIR resource field binding",
    description=(
        "Checks whether a given system+code is valid for a specific FHIR resource field. "
        "Respects binding strength: required fields reject codes outside the value set, "
        "extensible/preferred fields allow extensions."
    ),
    responses=_VALIDATE_200,
    tags=["Terminology"],
)
async def validate_code(
    body: ValidateRequest,
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.validate(body)
    return JSONResponse(content=jsonable_encoder(result))


@router.post(
    "/translate",
    operation_id="translate_terminology_concept",
    summary="Translate a concept to another code system",
    description="Looks up existing cross-system mappings for a given code. Returns all stored translations to the target system.",
    responses=_TRANSLATE_200,
    tags=["Terminology"],
)
async def translate_concept(
    body: TranslateRequest,
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.translate(body)
    return JSONResponse(content=jsonable_encoder(result))
