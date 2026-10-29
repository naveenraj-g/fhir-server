from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import ensure_resource_exists
from app.models.observation import (
    ObservationBasedOnReferenceType,
    ObservationCategory,
    ObservationComponent,
    ObservationComponentInterpretation,
    ObservationComponentReferenceRange,
    ObservationComponentReferenceRangeAppliesTo,
    ObservationDerivedFromReferenceType,
    ObservationHasMemberReferenceType,
    ObservationIdentifier,
    ObservationInterpretation,
    ObservationModel,
    ObservationNoteAuthorReferenceType,
    ObservationPerformerReferenceType,
    ObservationReferenceRange,
    ObservationReferenceRangeAppliesTo,
    ObservationSubjectReferenceType,
)
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES, _org_ref_kwargs, _parse_org_ref

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_MODELED_BASED_ON_TYPES",
    "_MODELED_DERIVED_FROM_TYPES",
    "_MODELED_HAS_MEMBER_TYPES",
    "_MODELED_NOTE_AUTHOR_TYPES",
    "_MODELED_PERFORMER_TYPES",
    "_MODELED_SUBJECT_TYPES",
    "_SORTABLE_FIELDS",
    "_org_ref_kwargs",
    "_parse_any_ref",
    "_parse_org_ref",
    "_ref_kwargs",
    "_single_reference_kwargs",
    "_validate_ref",
    "_with_relationships",
]

# Of the enumerable-target-type fields on Observation, only these subsets
# are modeled resources in this system — the existence check is only ever
# attempted for them. `encounter` (Encounter) has no "modeled subset" to
# speak of — it's a single, modeled type, so it's always validated
# directly (modeled_types=None, see full.py). `specimen` (Specimen) and
# `device` (Device|DeviceMetric) have NO modeled types at all — never
# validated (modeled_types=set()).
_MODELED_SUBJECT_TYPES = {ObservationSubjectReferenceType.Location}
_MODELED_BASED_ON_TYPES = {
    ObservationBasedOnReferenceType.MedicationRequest,
    ObservationBasedOnReferenceType.ServiceRequest,
}
_MODELED_PERFORMER_TYPES = {
    ObservationPerformerReferenceType.Practitioner,
    ObservationPerformerReferenceType.PractitionerRole,
    ObservationPerformerReferenceType.Organization,
}
_MODELED_HAS_MEMBER_TYPES = {
    ObservationHasMemberReferenceType.Observation,
    ObservationHasMemberReferenceType.QuestionnaireResponse,
}
_MODELED_DERIVED_FROM_TYPES = {
    ObservationDerivedFromReferenceType.Observation,
    ObservationDerivedFromReferenceType.QuestionnaireResponse,
}
_MODELED_NOTE_AUTHOR_TYPES = {
    ObservationNoteAuthorReferenceType.Practitioner,
    ObservationNoteAuthorReferenceType.PractitionerRole,
    ObservationNoteAuthorReferenceType.Organization,
}


def _parse_any_ref(ref: str) -> tuple[str | None, int | None]:
    """Parse a 'ResourceType/id' string WITHOUT validating the type
    against any enum — used for `focus`, the one genuinely
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
    of the `_SingleReferenceInput`/`_ReferenceListInput` payload objects."""
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
    "observation_id": ObservationModel.observation_id,
    "status": ObservationModel.status,
    "issued": ObservationModel.issued,
    "created_at": ObservationModel.created_at,
    "updated_at": ObservationModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every Observation sub-resource to avoid N+1 and async
    lazy-load failures."""
    return stmt.options(
        selectinload(ObservationModel.code_codings),
        selectinload(ObservationModel.value_codeable_concept_codings),
        selectinload(ObservationModel.data_absent_reason_codings),
        selectinload(ObservationModel.body_site_codings),
        selectinload(ObservationModel.method_codings),
        selectinload(ObservationModel.identifiers).selectinload(ObservationIdentifier.type_codings),
        selectinload(ObservationModel.based_ons),
        selectinload(ObservationModel.part_ofs),
        selectinload(ObservationModel.categories).selectinload(ObservationCategory.codings),
        selectinload(ObservationModel.focuses),
        selectinload(ObservationModel.performers),
        selectinload(ObservationModel.interpretations).selectinload(ObservationInterpretation.codings),
        selectinload(ObservationModel.notes),
        selectinload(ObservationModel.reference_ranges).selectinload(ObservationReferenceRange.type_codings),
        selectinload(ObservationModel.reference_ranges)
        .selectinload(ObservationReferenceRange.applies_tos)
        .selectinload(ObservationReferenceRangeAppliesTo.codings),
        selectinload(ObservationModel.has_members),
        selectinload(ObservationModel.derived_froms),
        selectinload(ObservationModel.components).selectinload(ObservationComponent.code_codings),
        selectinload(ObservationModel.components).selectinload(
            ObservationComponent.value_codeable_concept_codings
        ),
        selectinload(ObservationModel.components).selectinload(ObservationComponent.data_absent_reason_codings),
        selectinload(ObservationModel.components)
        .selectinload(ObservationComponent.interpretations)
        .selectinload(ObservationComponentInterpretation.codings),
        selectinload(ObservationModel.components)
        .selectinload(ObservationComponent.reference_ranges)
        .selectinload(ObservationComponentReferenceRange.type_codings),
        selectinload(ObservationModel.components)
        .selectinload(ObservationComponent.reference_ranges)
        .selectinload(ObservationComponentReferenceRange.applies_tos)
        .selectinload(ObservationComponentReferenceRangeAppliesTo.codings),
    )
