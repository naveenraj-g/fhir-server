from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.fhir.parameters import get_param, get_params_list
from app.terminology.client import TerminologyClient

router = APIRouter()

_PARAMETERS_200 = {
    200: {"content": {"application/json": {"schema": {"type": "object"}}}}
}
_PARAMETERS_400 = {
    400: {"description": "Missing/unresolvable input, or OperationOutcome-shaped error"}
}


@router.get(
    "/CodeSystem/$lookup",
    operation_id="codesystem_lookup_get",
    summary="$lookup (GET) — code/Coding to display + designations",
    description="FHIR R4 CodeSystem $lookup operation. See docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §2.6.",
    responses={**_PARAMETERS_200, **_PARAMETERS_400},
    tags=["Terminology"],
)
async def codesystem_lookup_get(
    system: str | None = Query(None),
    code: str | None = Query(None),
    property: list[str] | None = Query(None),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.lookup_operation(
        system=system, code=code, coding=None, properties=property
    )
    return JSONResponse(content=result)


@router.post(
    "/CodeSystem/$lookup",
    operation_id="codesystem_lookup_post",
    summary="$lookup (POST Parameters) — code/Coding to display + designations",
    description="FHIR R4 CodeSystem $lookup operation. See docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §2.6.",
    responses={**_PARAMETERS_200, **_PARAMETERS_400},
    tags=["Terminology"],
)
async def codesystem_lookup_post(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    coding = get_param(body, "coding")
    result = await service.lookup_operation(
        system=get_param(body, "system"),
        code=get_param(body, "code"),
        coding=coding,
        properties=[get_param(p, "property") for p in get_params_list(body, "property")]
        or None,
    )
    return JSONResponse(content=result)


@router.get(
    "/CodeSystem/$validate-code",
    operation_id="codesystem_validate_code_get",
    summary="$validate-code (GET) — is this code valid in this CodeSystem",
    description="FHIR R4 CodeSystem $validate-code operation (distinct from the ValueSet variant). See docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §2.6.",
    responses={**_PARAMETERS_200, **_PARAMETERS_400},
    tags=["Terminology"],
)
async def codesystem_validate_code_get(
    url: str | None = Query(None),
    code: str | None = Query(None),
    version: str | None = Query(None),
    display: str | None = Query(None),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.validate_code_on_codesystem_operation(
        url=url,
        code=code,
        version=version,
        display=display,
        coding=None,
        codeable_concept=None,
    )
    return JSONResponse(content=result)


@router.post(
    "/CodeSystem/$validate-code",
    operation_id="codesystem_validate_code_post",
    summary="$validate-code (POST Parameters) — is this code valid in this CodeSystem",
    description="FHIR R4 CodeSystem $validate-code operation (distinct from the ValueSet variant). See docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §2.6.",
    responses={**_PARAMETERS_200, **_PARAMETERS_400},
    tags=["Terminology"],
)
async def codesystem_validate_code_post(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.validate_code_on_codesystem_operation(
        url=get_param(body, "url"),
        code=get_param(body, "code"),
        version=get_param(body, "version"),
        display=get_param(body, "display"),
        coding=get_param(body, "coding"),
        codeable_concept=get_param(body, "codeableConcept"),
    )
    return JSONResponse(content=result)


@router.get(
    "/CodeSystem/$subsumes",
    operation_id="codesystem_subsumes_get",
    summary="$subsumes (GET) — hierarchy relationship between two codes",
    description="FHIR R4 CodeSystem $subsumes operation. See docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §2.6.",
    responses={**_PARAMETERS_200, **_PARAMETERS_400},
    tags=["Terminology"],
)
async def codesystem_subsumes_get(
    codeA: str | None = Query(None),
    codeB: str | None = Query(None),
    system: str | None = Query(None),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.subsumes_operation(
        code_a=codeA, code_b=codeB, system=system, coding_a=None, coding_b=None
    )
    return JSONResponse(content=result)


@router.post(
    "/CodeSystem/$subsumes",
    operation_id="codesystem_subsumes_post",
    summary="$subsumes (POST Parameters) — hierarchy relationship between two codes",
    description="FHIR R4 CodeSystem $subsumes operation. See docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §2.6.",
    responses={**_PARAMETERS_200, **_PARAMETERS_400},
    tags=["Terminology"],
)
async def codesystem_subsumes_post(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.subsumes_operation(
        code_a=get_param(body, "codeA"),
        code_b=get_param(body, "codeB"),
        system=get_param(body, "system"),
        coding_a=get_param(body, "codingA"),
        coding_b=get_param(body, "codingB"),
    )
    return JSONResponse(content=result)


@router.post(
    "/CodeSystem/$find-matches",
    operation_id="codesystem_find_matches_post",
    summary="$find-matches (POST Parameters, Trial Use) — infer a code from property values",
    description=(
        "FHIR R4 CodeSystem $find-matches operation. See docs/terminology-service/"
        "09-fhir-r4-terminology-standard-reference.md §2.6. This repository has no "
        "CodeSystem.property data to match against — always returns an empty match[] "
        "with an explanatory comment, rather than faking a result."
    ),
    responses={**_PARAMETERS_200, **_PARAMETERS_400},
    tags=["Terminology"],
)
async def codesystem_find_matches_post(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    properties = []
    for p in get_params_list(body, "property"):
        parts = {part.get("name"): get_param({"parameter": [part]}, part.get("name")) for part in p.get("part", [])}
        properties.append(parts)
    result = await service.find_matches_operation(
        system=get_param(body, "system"),
        version=get_param(body, "version"),
        properties=properties,
        exact=get_param(body, "exact"),
        compositional=get_param(body, "compositional"),
    )
    return JSONResponse(content=result)
