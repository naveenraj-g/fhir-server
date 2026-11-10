"""ConceptMap's `$translate` and `$closure` — see
docs/terminology-service/09-fhir-r4-terminology-standard-reference.md
§4.3-4.4. Separate from the existing, non-standard `/translate` route
(`app/routers/terminology/validation.py`) and `/concept-maps` CRUD
(`app/routers/terminology/concept_maps.py`) — both of those stay exactly
as they were; these are new, additional, `$`-prefixed endpoints."""

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType
from app.fhir.parameters import get_param, get_param_resource, get_params_list
from app.terminology.client import TerminologyClient

router = APIRouter()


def _reject_unsupported_translate_params(
    url: str | None, concept_map: dict | str | None, concept_map_version: str | None
) -> None:
    """`url`/`conceptMap`/`conceptMapVersion` would resolve `$translate` by a
    ConceptMap canonical URL — not supported, since `TerminologyConceptMap`
    has no canonical-URL-addressable ConceptMap resource of its own (see its
    docstring, app/models/terminology/terminology.py)."""
    if url or concept_map or concept_map_version:
        raise ApplicationError(
            name="UnsupportedTranslateInput",
            message=(
                "Resolving $translate by a ConceptMap canonical URL "
                "(url/conceptMap/conceptMapVersion) is not supported — this "
                "server has no canonical-URL-addressable ConceptMap resource "
                "yet. Resolve by system+code and targetsystem instead."
            ),
            status_code=400,
            code="TERMINOLOGY_OPERATION_NOT_SUPPORTED",
            issue_type=IssueType.NOT_SUPPORTED,
        )


def _resolve_translate_code(
    system: str | None,
    code: str | None,
    coding: dict | None,
    codeable_concept: dict | None,
) -> tuple[str, str]:
    """Exactly one of code/coding/codeableConcept is required, per §4.3."""
    given = [v for v in (code, coding, codeable_concept) if v is not None]
    if len(given) != 1:
        raise ApplicationError(
            name="InvalidTranslateInput",
            message="Exactly one of code, coding, or codeableConcept is required.",
            status_code=400,
            code="TERMINOLOGY_OPERATION_INPUT_INVALID",
            issue_type=IssueType.REQUIRED,
        )
    if code is not None:
        if not system:
            raise ApplicationError(
                name="InvalidTranslateInput",
                message="`system` is required when `code` is given.",
                status_code=400,
                code="TERMINOLOGY_OPERATION_INPUT_INVALID",
                issue_type=IssueType.REQUIRED,
            )
        return system, code
    if coding is not None:
        return coding.get("system"), coding.get("code")
    codings = (codeable_concept or {}).get("coding") or []
    if not codings:
        raise ApplicationError(
            name="InvalidTranslateInput",
            message="codeableConcept has no coding entries.",
            status_code=400,
            code="TERMINOLOGY_OPERATION_INPUT_INVALID",
            issue_type=IssueType.REQUIRED,
        )
    first = codings[0]
    return first.get("system"), first.get("code")


@router.get(
    "/ConceptMap/$translate",
    operation_id="conceptmap_translate_get",
    summary="$translate — translate a code to another code system (GET)",
    description=(
        "FHIR R4 ConceptMap $translate operation. Resolves by source "
        "system+code and a target system (`targetsystem`) — NOT by "
        "ConceptMap canonical URL (`url`/`conceptMap`/`conceptMapVersion` "
        "are rejected with a 400 not-supported OperationOutcome), since "
        "this server has no canonical-URL-addressable ConceptMap resource "
        "yet. `source`/`target` (ValueSet-scoped narrowing) and "
        "`dependency` are accepted but ignored. See "
        "docs/terminology-service/09-fhir-r4-terminology-standard-"
        "reference.md §4.3."
    ),
    responses={200: {"content": {"application/json": {"schema": {"type": "object"}}}}},
    tags=["Terminology"],
)
async def conceptmap_translate_get(
    system: str | None = Query(None),
    code: str | None = Query(None),
    targetsystem: str | None = Query(None),
    reverse: bool = Query(False),
    source: str | None = Query(
        None, description="Accepted, ignored — ValueSet-scoped narrowing not supported"
    ),
    target: str | None = Query(
        None, description="Accepted, ignored — ValueSet-scoped narrowing not supported"
    ),
    url: str | None = Query(None, description="Not supported — see description"),
    concept_map: str | None = Query(
        None, alias="conceptMap", description="Not supported — see description"
    ),
    concept_map_version: str | None = Query(
        None, alias="conceptMapVersion", description="Not supported — see description"
    ),
    service: TerminologyClient = Depends(get_terminology_client),
):
    _reject_unsupported_translate_params(url, concept_map, concept_map_version)
    resolved_system, resolved_code = _resolve_translate_code(system, code, None, None)
    result = await service.translate_operation(
        resolved_system, resolved_code, targetsystem, reverse
    )
    return JSONResponse(content=result)


@router.post(
    "/ConceptMap/$translate",
    operation_id="conceptmap_translate_post",
    summary="$translate — translate a code to another code system (POST)",
    description=(
        "POST Parameters-body form of the same operation — see the GET "
        "route's description for the full behavior."
    ),
    responses={200: {"content": {"application/json": {"schema": {"type": "object"}}}}},
    tags=["Terminology"],
)
async def conceptmap_translate_post(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    _reject_unsupported_translate_params(
        get_param(body, "url"),
        get_param_resource(body, "conceptMap"),
        get_param(body, "conceptMapVersion"),
    )
    system = get_param(body, "system")
    code = get_param(body, "code")
    coding = get_param(body, "coding")
    codeable_concept = get_param(body, "codeableConcept")
    resolved_system, resolved_code = _resolve_translate_code(
        system, code, coding, codeable_concept
    )
    targetsystem = get_param(body, "targetsystem")
    reverse = bool(get_param(body, "reverse") or False)
    result = await service.translate_operation(
        resolved_system, resolved_code, targetsystem, reverse
    )
    return JSONResponse(content=result)


@router.post(
    "/$closure",
    operation_id="closure_operation",
    summary="$closure — maintain a client-side transitive-closure table",
    description=(
        "FHIR R4 $closure operation — mounted at the terminology base "
        "(NOT under /ConceptMap/, per spec), and the one operation in this "
        "module that is NOT idempotent: a named closure table accumulates "
        "members across calls. Returns a ConceptMap resource directly, not "
        "wrapped in Parameters. See docs/terminology-service/"
        "09-fhir-r4-terminology-standard-reference.md §4.4."
    ),
    responses={200: {"content": {"application/json": {"schema": {"type": "object"}}}}},
    tags=["Terminology"],
)
async def closure_operation(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    name = get_param(body, "name")
    if not name:
        raise ApplicationError(
            name="InvalidClosureInput",
            message="`name` is required.",
            status_code=400,
            code="TERMINOLOGY_OPERATION_INPUT_INVALID",
            issue_type=IssueType.REQUIRED,
        )
    version = get_param(body, "version")
    concept_params = get_params_list(body, "concept")
    concepts = [
        {"system": p["valueCoding"]["system"], "code": p["valueCoding"]["code"]}
        for p in concept_params
        if "valueCoding" in p
    ]
    if concepts and version is not None:
        raise ApplicationError(
            name="InvalidClosureInput",
            message="`concept` and `version` cannot be combined.",
            status_code=400,
            code="TERMINOLOGY_OPERATION_INPUT_INVALID",
            issue_type=IssueType.INVALID,
        )
    result = await service.closure_operation(name, concepts, version)
    return JSONResponse(content=result)
