from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import ensure_resource_exists
from app.models.service_request import (
    ServiceRequestBasedOnReferenceType,
    ServiceRequestBodySite,
    ServiceRequestCategory,
    ServiceRequestIdentifier,
    ServiceRequestInsuranceReferenceType,
    ServiceRequestLocationCode,
    ServiceRequestModel,
    ServiceRequestNoteAuthorReferenceType,
    ServiceRequestOrderDetail,
    ServiceRequestPerformerReferenceType,
    ServiceRequestReasonCode,
    ServiceRequestReasonReferenceType,
    ServiceRequestRelevantHistoryReferenceType,
    ServiceRequestRequesterReferenceType,
    ServiceRequestSpecimenReferenceType,
    ServiceRequestSubjectReferenceType,
)
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES, _org_ref_kwargs, _parse_org_ref

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_MODELED_BASED_ON_TYPES",
    "_MODELED_PERFORMER_TYPES",
    "_MODELED_REQUESTER_TYPES",
    "_MODELED_SUBJECT_TYPES",
    "_MODELED_NOTE_AUTHOR_TYPES",
    "_identifier_fallback_kwargs",
    "_org_ref_kwargs",
    "_parse_any_ref",
    "_parse_org_ref",
    "_ref_kwargs",
    "_single_reference_kwargs",
    "_validate_ref",
    "_with_relationships",
]

# Of the enumerable-target-type fields on ServiceRequest, only these
# subsets are modeled resources in this system (registered in
# RESOURCE_REGISTRY) — the existence check is only ever attempted for
# them; every other allowed type relies on the identifier fallback
# instead. `replaces`/`encounter`/`locationReference` have no "modeled
# subset" to speak of — their one allowed type IS the modeled resource,
# so they're always validated directly (see full.py).
_MODELED_BASED_ON_TYPES = {ServiceRequestBasedOnReferenceType.ServiceRequest}
_MODELED_SUBJECT_TYPES = {ServiceRequestSubjectReferenceType.Location}
_MODELED_REQUESTER_TYPES = {
    ServiceRequestRequesterReferenceType.Practitioner,
    ServiceRequestRequesterReferenceType.PractitionerRole,
    ServiceRequestRequesterReferenceType.Organization,
}
_MODELED_PERFORMER_TYPES = {
    ServiceRequestPerformerReferenceType.Practitioner,
    ServiceRequestPerformerReferenceType.PractitionerRole,
    ServiceRequestPerformerReferenceType.Organization,
    ServiceRequestPerformerReferenceType.HealthcareService,
}
_MODELED_NOTE_AUTHOR_TYPES = {
    ServiceRequestNoteAuthorReferenceType.Practitioner,
    ServiceRequestNoteAuthorReferenceType.Organization,
}
# reasonReference/insurance/specimen/relevantHistory: none of their
# allowed types are modeled resources here — never validated (no set
# needed, see full.py).


def _parse_any_ref(ref: str) -> tuple[str | None, int | None]:
    """Parse a 'ResourceType/id' string WITHOUT validating the type
    against any enum — used for `supportingInfo`, the one genuinely
    Reference(Any) field on this resource."""
    parts = ref.split("/", 1)
    if len(parts) != 2:
        return None, None
    resource_type, raw_id = parts
    try:
        return resource_type, int(raw_id)
    except ValueError:
        return resource_type, None


def _ref_kwargs(prefix: str, ref: str | None, display: str | None, enum_cls) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM
    constructor kwargs from a FHIR reference string. `enum_cls=None`
    means a genuinely free-text Reference(Any) field (plain String
    column, never a Postgres Enum) — otherwise `enum_cls` is whichever
    resource-scoped (or shared) reference-type enum this field uses."""
    if not ref:
        return {f"{prefix}_type": None, f"{prefix}_id": None, f"{prefix}_display": display}
    ref_type, ref_id = _parse_any_ref(ref) if enum_cls is None else parse_reference(ref, enum_cls)
    return {f"{prefix}_type": ref_type, f"{prefix}_id": ref_id, f"{prefix}_display": display}


async def _validate_ref(session, tenant_id, field_name: str, ref_type, ref_id, modeled_types: set | None) -> None:
    """`modeled_types=None` means "always validate" (the field's only
    allowed type IS the modeled resource); a set means "only validate
    when ref_type is in this subset"; an empty set means "never
    validate" (none of the allowed types are modeled here)."""
    if not ref_type or not ref_id:
        return
    if modeled_types is not None and ref_type not in modeled_types:
        return
    await ensure_resource_exists(session, ref_type, ref_id, org_id=tenant_id, field_name=field_name)


def _identifier_fallback_kwargs(model_prefix: str, obj) -> dict:
    """Build `{model_prefix}_identifier_*` ORM constructor kwargs from one
    of the `_SingleReferenceInput`/`_ReferenceListInput` payload objects
    (app.schemas.service_request.input.reference) — those objects' own
    attributes are always bare `reference_identifier_*`, but the target
    columns on subject/encounter/requester are `{model_prefix}_
    identifier_*`. The list-reference child tables' own columns ARE bare
    `reference_identifier_*` already, so those reuse `_reference_kwargs`-
    style direct attribute access instead — see full.py."""
    return {f"{model_prefix}_{suffix}": getattr(obj, f"reference_{suffix}") for suffix in _IDENTIFIER_FALLBACK_SUFFIXES}


def _single_reference_kwargs(prefix: str, obj, enum_cls) -> dict:
    """Full `{prefix}_*` column set for one of subject/encounter/requester
    (each 0..1 or 1..1, flattened onto the main row) — always returns
    every column, `None` where `obj` itself is `None` or a sub-field is
    absent."""
    ref = obj.reference if obj else None
    display = obj.reference_display if obj else None
    kwargs = {f"{prefix}_reference": ref, **_ref_kwargs(prefix, ref, display, enum_cls)}
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        kwargs[f"{prefix}_{suffix}"] = getattr(obj, f"reference_{suffix}") if obj else None
    return kwargs


_SORTABLE_FIELDS = {
    "service_request_id": ServiceRequestModel.service_request_id,
    "status": ServiceRequestModel.status,
    "intent": ServiceRequestModel.intent,
    "authored_on": ServiceRequestModel.authored_on,
    "created_at": ServiceRequestModel.created_at,
    "updated_at": ServiceRequestModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every ServiceRequest sub-resource to avoid N+1 and
    async lazy-load failures."""
    return stmt.options(
        selectinload(ServiceRequestModel.requisition_type_codings),
        selectinload(ServiceRequestModel.code_codings),
        selectinload(ServiceRequestModel.as_needed_codings),
        selectinload(ServiceRequestModel.performer_type_codings),
        selectinload(ServiceRequestModel.identifiers).selectinload(ServiceRequestIdentifier.type_codings),
        selectinload(ServiceRequestModel.based_ons),
        selectinload(ServiceRequestModel.replaces),
        selectinload(ServiceRequestModel.categories).selectinload(ServiceRequestCategory.codings),
        selectinload(ServiceRequestModel.order_details).selectinload(ServiceRequestOrderDetail.codings),
        selectinload(ServiceRequestModel.location_codes).selectinload(ServiceRequestLocationCode.codings),
        selectinload(ServiceRequestModel.location_references),
        selectinload(ServiceRequestModel.reason_codes).selectinload(ServiceRequestReasonCode.codings),
        selectinload(ServiceRequestModel.reason_references),
        selectinload(ServiceRequestModel.insurances),
        selectinload(ServiceRequestModel.supporting_infos),
        selectinload(ServiceRequestModel.specimens),
        selectinload(ServiceRequestModel.relevant_histories),
        selectinload(ServiceRequestModel.notes),
        selectinload(ServiceRequestModel.performers),
        selectinload(ServiceRequestModel.body_sites).selectinload(ServiceRequestBodySite.codings),
    )
