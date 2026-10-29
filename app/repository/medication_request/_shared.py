from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import ensure_resource_exists
from app.models.medication_request import (
    MedicationRequestCategory,
    MedicationRequestDosageAdditionalInstruction,
    MedicationRequestDosageInstruction,
    MedicationRequestIdentifier,
    MedicationRequestModel,
    MedicationRequestNoteAuthorReferenceType,
    MedicationRequestPerformerReferenceType,
    MedicationRequestReasonCode,
    MedicationRequestRecorderReferenceType,
    MedicationRequestReportedReferenceType,
    MedicationRequestRequesterReferenceType,
)
from app.models.medication_request.enums import MedicationRequestBasedOnReferenceType
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES, _org_ref_kwargs, _parse_org_ref

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_MODELED_BASED_ON_TYPES",
    "_MODELED_NOTE_AUTHOR_TYPES",
    "_MODELED_PERFORMER_TYPES",
    "_MODELED_REPORTED_REFERENCE_TYPES",
    "_MODELED_REQUESTER_TYPES",
    "_SORTABLE_FIELDS",
    "_identifier_fallback_kwargs",
    "_org_ref_kwargs",
    "_parse_any_ref",
    "_parse_org_ref",
    "_ref_kwargs",
    "_single_reference_kwargs",
    "_validate_ref",
    "_with_relationships",
]

# Of the enumerable-target-type fields on MedicationRequest, only these
# subsets are modeled resources in this system — the existence check is
# only ever attempted for them. `recorder` (Practitioner|PractitionerRole)
# has no "modeled subset" to speak of — both allowed types are modeled,
# so it's always validated directly (modeled_types=None, see full.py).
_MODELED_BASED_ON_TYPES = {
    MedicationRequestBasedOnReferenceType.MedicationRequest,
    MedicationRequestBasedOnReferenceType.ServiceRequest,
}
_MODELED_REQUESTER_TYPES = {
    MedicationRequestRequesterReferenceType.Practitioner,
    MedicationRequestRequesterReferenceType.PractitionerRole,
    MedicationRequestRequesterReferenceType.Organization,
}
_MODELED_PERFORMER_TYPES = {
    MedicationRequestPerformerReferenceType.Practitioner,
    MedicationRequestPerformerReferenceType.PractitionerRole,
    MedicationRequestPerformerReferenceType.Organization,
}
_MODELED_REPORTED_REFERENCE_TYPES = {
    MedicationRequestReportedReferenceType.Practitioner,
    MedicationRequestReportedReferenceType.Organization,
}
_MODELED_NOTE_AUTHOR_TYPES = {
    MedicationRequestNoteAuthorReferenceType.Practitioner,
    MedicationRequestNoteAuthorReferenceType.Organization,
}


def _parse_any_ref(ref: str) -> tuple[str | None, int | None]:
    """Parse a 'ResourceType/id' string WITHOUT validating the type
    against any enum — used for `supportingInformation`, the one
    genuinely Reference(Any) field on this resource."""
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
    means a genuinely free-text Reference(Any) field."""
    if not ref:
        return {f"{prefix}_type": None, f"{prefix}_id": None, f"{prefix}_display": display}
    ref_type, ref_id = _parse_any_ref(ref) if enum_cls is None else parse_reference(ref, enum_cls)
    return {f"{prefix}_type": ref_type, f"{prefix}_id": ref_id, f"{prefix}_display": display}


async def _validate_ref(session, tenant_id, field_name: str, ref_type, ref_id, modeled_types: set | None) -> None:
    """`modeled_types=None` means "always validate"; a set means "only
    validate when ref_type is in this subset"; an empty set means "never
    validate"."""
    if not ref_type or not ref_id:
        return
    if modeled_types is not None and ref_type not in modeled_types:
        return
    await ensure_resource_exists(session, ref_type, ref_id, org_id=tenant_id, field_name=field_name)


def _identifier_fallback_kwargs(model_prefix: str, obj) -> dict:
    """Build `{model_prefix}_identifier_*` ORM constructor kwargs from one
    of the `_SingleReferenceInput` payload objects — mirrors
    app.repository.service_request._shared._identifier_fallback_kwargs."""
    return {f"{model_prefix}_{suffix}": getattr(obj, f"reference_{suffix}") for suffix in _IDENTIFIER_FALLBACK_SUFFIXES}


def _single_reference_kwargs(prefix: str, obj, enum_cls) -> dict:
    """Full `{prefix}_*` column set for one single 0..1 Reference field
    flattened onto the main row — always returns every column, `None`
    where `obj` itself is `None` or a sub-field is absent."""
    ref = obj.reference if obj else None
    display = obj.reference_display if obj else None
    kwargs = {f"{prefix}_reference": ref, **_ref_kwargs(prefix, ref, display, enum_cls)}
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        kwargs[f"{prefix}_{suffix}"] = getattr(obj, f"reference_{suffix}") if obj else None
    return kwargs


_SORTABLE_FIELDS = {
    "medication_request_id": MedicationRequestModel.medication_request_id,
    "status": MedicationRequestModel.status,
    "intent": MedicationRequestModel.intent,
    "authored_on": MedicationRequestModel.authored_on,
    "created_at": MedicationRequestModel.created_at,
    "updated_at": MedicationRequestModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every MedicationRequest sub-resource to avoid N+1 and
    async lazy-load failures."""
    return stmt.options(
        selectinload(MedicationRequestModel.status_reason_codings),
        selectinload(MedicationRequestModel.medication_codings),
        selectinload(MedicationRequestModel.performer_type_codings),
        selectinload(MedicationRequestModel.group_identifier_type_codings),
        selectinload(MedicationRequestModel.course_of_therapy_type_codings),
        selectinload(MedicationRequestModel.substitution_allowed_codings),
        selectinload(MedicationRequestModel.substitution_reason_codings),
        selectinload(MedicationRequestModel.identifiers).selectinload(MedicationRequestIdentifier.type_codings),
        selectinload(MedicationRequestModel.categories).selectinload(MedicationRequestCategory.codings),
        selectinload(MedicationRequestModel.reason_codes).selectinload(MedicationRequestReasonCode.codings),
        selectinload(MedicationRequestModel.reason_references),
        selectinload(MedicationRequestModel.based_ons),
        selectinload(MedicationRequestModel.insurances),
        selectinload(MedicationRequestModel.supporting_informations),
        selectinload(MedicationRequestModel.notes),
        selectinload(MedicationRequestModel.dosage_instructions)
        .selectinload(MedicationRequestDosageInstruction.additional_instructions)
        .selectinload(MedicationRequestDosageAdditionalInstruction.codings),
        selectinload(MedicationRequestModel.dosage_instructions).selectinload(
            MedicationRequestDosageInstruction.site_codings
        ),
        selectinload(MedicationRequestModel.dosage_instructions).selectinload(
            MedicationRequestDosageInstruction.route_codings
        ),
        selectinload(MedicationRequestModel.dosage_instructions).selectinload(
            MedicationRequestDosageInstruction.method_codings
        ),
        selectinload(MedicationRequestModel.dosage_instructions).selectinload(
            MedicationRequestDosageInstruction.as_needed_codings
        ),
        selectinload(MedicationRequestModel.detected_issues),
        selectinload(MedicationRequestModel.event_histories),
    )
