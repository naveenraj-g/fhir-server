"""Real FHIR R4 ValueSet operations — `$expand` and `$validate-code` — see
docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §3.2
and the "`$validate-code` on ValueSet" subsection of §2.6.

Deliberately separate from, and does not touch, the existing
`value_sets.py` router (the older `/value-sets`/`/value-sets/{id}/expand`
non-standard endpoints) — both now coexist; the old ones keep their old
bespoke shape, these return real FHIR-shaped output at the real `$`-named
paths."""

from typing import Any

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from app.di.dependencies.terminology import get_terminology_client
from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType
from app.fhir.parameters import get_param, get_param_resource
from app.terminology.client import TerminologyClient

router = APIRouter()

_OPERATION_RESPONSES = {
    200: {"content": {"application/json": {"schema": {"type": "object"}}}},
}


def _reject_unsupported_scoping(
    value_set: Any, context: str | None, context_direction: str | None
) -> None:
    """`valueSet` (inline), `context`, and `contextDirection` would each
    change WHICH ValueSet gets used — silently ignoring them (unlike the
    purely-descriptive expansion params this module does ignore) would
    answer a different question than the one actually asked, so these
    three raise NOT_SUPPORTED instead."""
    if value_set is not None or context is not None or context_direction is not None:
        raise ApplicationError(
            name="UnsupportedOperationParameter",
            message=(
                "This server does not support resolving a ValueSet from an "
                "inline 'valueSet', a binding 'context', or 'contextDirection' "
                "— pass 'url' (optionally with 'valueSetVersion') instead."
            ),
            status_code=400,
            code="OPERATION_PARAMETER_NOT_SUPPORTED",
            issue_type=IssueType.NOT_SUPPORTED,
        )


def _resolve_code_input(
    code: str | None,
    system: str | None,
    coding: dict | None,
    codeable_concept: dict | None,
) -> tuple[str | None, str | None, str | None]:
    """Exactly one of (code+system) / coding / codeableConcept must be
    given, per both $validate-code variants' own invocation rules. Returns
    (system, code, display)."""
    given = [bool(code or system), bool(coding), bool(codeable_concept)]
    if sum(given) != 1:
        raise ApplicationError(
            name="InvalidCodeInput",
            message=(
                "Supply exactly one of: code+system, coding, or codeableConcept."
            ),
            status_code=400,
            code="INVALID_CODE_INPUT",
            issue_type=IssueType.REQUIRED,
        )
    if coding:
        return coding.get("system"), coding.get("code"), coding.get("display")
    if codeable_concept:
        codings = codeable_concept.get("coding") or []
        first = codings[0] if codings else {}
        return first.get("system"), first.get("code"), first.get("display")
    return system, code, None


# ---------------------------------------------------------------------------
# $expand
# ---------------------------------------------------------------------------


@router.get(
    "/ValueSet/$expand",
    operation_id="valueset_expand_operation_type",
    summary="FHIR $expand — materialize a ValueSet's code list, by canonical URL",
    description=(
        "Real FHIR R4 ValueSet/$expand, type-level invocation (canonical URL, "
        "not an internal id). Returns a ValueSet resource with a materialized "
        "`expansion`, not wrapped in Parameters, per the operation's own "
        "spec. Supported query params: url, valueSetVersion, filter, offset, "
        "count. Other legal params (includeDesignations, activeOnly, "
        "excludeNested, exclude-system, etc.) are accepted but not yet "
        "implemented and are silently ignored; `valueSet`/`context`/ "
        "`contextDirection` are rejected (400) since ignoring those would "
        "silently expand the wrong thing."
    ),
    responses=_OPERATION_RESPONSES,
    tags=["Terminology"],
)
async def expand_type_level(
    url: str | None = Query(None, description="Canonical ValueSet URL"),
    valueSetVersion: str | None = Query(None),
    filter: str | None = Query(None, description="Free-text filter"),
    offset: int = Query(0, ge=0),
    count: int = Query(50, ge=0, le=200),
    context: str | None = Query(None),
    contextDirection: str | None = Query(None),
    service: TerminologyClient = Depends(get_terminology_client),
):
    _reject_unsupported_scoping(None, context, contextDirection)
    result = await service.expand_operation(
        value_set_id=None,
        url=url,
        value_set_version=valueSetVersion,
        filter_text=filter,
        offset=offset,
        count=count,
    )
    return JSONResponse(content=result)


@router.post(
    "/ValueSet/$expand",
    operation_id="valueset_expand_operation_type_post",
    summary="FHIR $expand (POST form) — materialize a ValueSet's code list, by canonical URL",
    description="POST/Parameters-body form of the GET $expand above — same semantics, same supported/ignored/rejected params.",
    responses=_OPERATION_RESPONSES,
    tags=["Terminology"],
)
async def expand_type_level_post(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    value_set = get_param_resource(body, "valueSet")
    context = get_param(body, "context")
    context_direction = get_param(body, "contextDirection")
    _reject_unsupported_scoping(value_set, context, context_direction)
    result = await service.expand_operation(
        value_set_id=None,
        url=get_param(body, "url"),
        value_set_version=get_param(body, "valueSetVersion"),
        filter_text=get_param(body, "filter"),
        offset=get_param(body, "offset") or 0,
        count=get_param(body, "count") if get_param(body, "count") is not None else 50,
    )
    return JSONResponse(content=result)


@router.get(
    "/ValueSet/{value_set_id}/$expand",
    operation_id="valueset_expand_operation_instance",
    summary="FHIR $expand — materialize a ValueSet's code list, by internal id",
    description=(
        "Instance-level invocation — same operation as the type-level "
        "GET/POST $expand above, addressed by this server's own internal "
        "ValueSet id instead of a canonical URL. Returns the same "
        "FHIR-shaped ValueSet+expansion body; NOT the same response shape "
        "as the older, separate GET /value-sets/{id}/expand endpoint."
    ),
    responses={**_OPERATION_RESPONSES, 404: {"description": "Value set not found"}},
    tags=["Terminology"],
)
async def expand_instance_level(
    value_set_id: int,
    filter: str | None = Query(None, description="Free-text filter"),
    offset: int = Query(0, ge=0),
    count: int = Query(50, ge=0, le=200),
    service: TerminologyClient = Depends(get_terminology_client),
):
    result = await service.expand_operation(
        value_set_id=value_set_id,
        url=None,
        value_set_version=None,
        filter_text=filter,
        offset=offset,
        count=count,
    )
    return JSONResponse(content=result)


# ---------------------------------------------------------------------------
# $validate-code (ValueSet)
# ---------------------------------------------------------------------------


@router.get(
    "/ValueSet/$validate-code",
    operation_id="valueset_validate_code_operation_type",
    summary="FHIR $validate-code (ValueSet) — is this code a member of this value set, by canonical URL",
    description=(
        "Real FHIR R4 ValueSet/$validate-code, type-level (canonical URL). "
        "Distinct from CodeSystem/$validate-code (is the code valid at all "
        "in the system) and from this app's own non-standard /validate "
        "(resource+field binding) — see docs/terminology-service/09-...md. "
        "GET form only supports the simple code+system input; use POST for "
        "coding/codeableConcept."
    ),
    responses=_OPERATION_RESPONSES,
    tags=["Terminology"],
)
async def validate_code_type_level(
    url: str | None = Query(None, description="Canonical ValueSet URL"),
    valueSetVersion: str | None = Query(None),
    code: str | None = Query(None),
    system: str | None = Query(None),
    display: str | None = Query(None),
    context: str | None = Query(None),
    service: TerminologyClient = Depends(get_terminology_client),
):
    _reject_unsupported_scoping(None, context, None)
    resolved_system, resolved_code, _ = _resolve_code_input(code, system, None, None)
    result = await service.validate_code_on_valueset_operation(
        value_set_id=None,
        url=url,
        value_set_version=valueSetVersion,
        code=resolved_code,
        system=resolved_system,
        display=display,
    )
    return JSONResponse(content=result)


@router.post(
    "/ValueSet/$validate-code",
    operation_id="valueset_validate_code_operation_type_post",
    summary="FHIR $validate-code (ValueSet, POST form) — by canonical URL",
    description="POST/Parameters-body form — accepts code+system, coding, or codeableConcept.",
    responses=_OPERATION_RESPONSES,
    tags=["Terminology"],
)
async def validate_code_type_level_post(
    body: dict = Body(...),
    service: TerminologyClient = Depends(get_terminology_client),
):
    value_set = get_param_resource(body, "valueSet")
    context = get_param(body, "context")
    _reject_unsupported_scoping(value_set, context, None)
    resolved_system, resolved_code, resolved_display = _resolve_code_input(
        get_param(body, "code"),
        get_param(body, "system"),
        get_param(body, "coding"),
        get_param(body, "codeableConcept"),
    )
    result = await service.validate_code_on_valueset_operation(
        value_set_id=None,
        url=get_param(body, "url"),
        value_set_version=get_param(body, "valueSetVersion"),
        code=resolved_code,
        system=resolved_system,
        display=get_param(body, "display") or resolved_display,
    )
    return JSONResponse(content=result)


@router.get(
    "/ValueSet/{value_set_id}/$validate-code",
    operation_id="valueset_validate_code_operation_instance",
    summary="FHIR $validate-code (ValueSet) — is this code a member of this value set, by internal id",
    description="Instance-level invocation — same operation as the type-level form above, addressed by internal id.",
    responses={**_OPERATION_RESPONSES, 400: {"description": "ValueSet could not be resolved"}},
    tags=["Terminology"],
)
async def validate_code_instance_level(
    value_set_id: int,
    code: str | None = Query(None),
    system: str | None = Query(None),
    display: str | None = Query(None),
    service: TerminologyClient = Depends(get_terminology_client),
):
    resolved_system, resolved_code, _ = _resolve_code_input(code, system, None, None)
    result = await service.validate_code_on_valueset_operation(
        value_set_id=value_set_id,
        url=None,
        value_set_version=None,
        code=resolved_code,
        system=resolved_system,
        display=display,
    )
    return JSONResponse(content=result)
