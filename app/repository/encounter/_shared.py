from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.encounter import (
    EncounterDiagnosis,
    EncounterHospitalization,
    EncounterHospitalizationDietPreference,
    EncounterHospitalizationSpecialArrangement,
    EncounterHospitalizationSpecialCourtesy,
    EncounterIdentifier,
    EncounterLocationRow,
    EncounterModel,
    EncounterParticipant,
    EncounterParticipantType,
    EncounterReasonCode,
    EncounterType,
)
from app.models.encounter.enums import EncounterParticipantIndividualReferenceType
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_SORTABLE_FIELDS",
    "_org_ref_kwargs",
    "_parse_org_ref",
    "_parse_ref",
    "_reference_kwargs",
    "_ref_kwargs",
    "_validate_individual_reference",
    "_validate_reference",
    "_with_relationships",
]

# Of FHIR R4's three allowed Encounter.participant.individual target
# types, only these two are modeled resources in this system (registered
# in RESOURCE_REGISTRY) — RelatedPerson rows always rely on the
# reference_identifier_* logical-reference fallback instead. Same
# reasoning as app.repository.appointment._shared's own
# _MODELED_PARTICIPANT_ACTOR_TYPES.
_MODELED_INDIVIDUAL_TYPES = {
    EncounterParticipantIndividualReferenceType.Practitioner,
    EncounterParticipantIndividualReferenceType.PractitionerRole,
}


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort).
_SORTABLE_FIELDS = {
    "encounter_id": EncounterModel.encounter_id,
    "period_start": EncounterModel.period_start,
    "created_at": EncounterModel.created_at,
    "updated_at": EncounterModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every Encounter sub-resource to avoid N+1 and async
    lazy-load failures. Every CodeableConcept-list field nests 2 levels
    (child+grandchild coding) and participant.type/hospitalization's own
    CC-list sub-fields each nest 3 levels (parent->child->grandchild) —
    every level must be eager-loaded explicitly or a DetachedInstanceError
    follows at render time (see CLAUDE.md's "nests 3 levels deep"
    invariant, discovered building Appointment/AppointmentResponse)."""
    return stmt.options(
        selectinload(EncounterModel.identifiers).selectinload(
            EncounterIdentifier.type_codings
        ),
        selectinload(EncounterModel.status_history),
        selectinload(EncounterModel.class_history),
        selectinload(EncounterModel.types).selectinload(EncounterType.codings),
        selectinload(EncounterModel.service_type_codings),
        selectinload(EncounterModel.priority_codings),
        selectinload(EncounterModel.episode_of_cares),
        selectinload(EncounterModel.based_ons),
        selectinload(EncounterModel.appointments),
        selectinload(EncounterModel.reason_codes).selectinload(
            EncounterReasonCode.codings
        ),
        selectinload(EncounterModel.reason_references),
        selectinload(EncounterModel.accounts),
        selectinload(EncounterModel.participants)
        .selectinload(EncounterParticipant.types)
        .selectinload(EncounterParticipantType.codings),
        selectinload(EncounterModel.diagnoses).selectinload(
            EncounterDiagnosis.use_codings
        ),
        selectinload(EncounterModel.hospitalization).selectinload(
            EncounterHospitalization.pre_admission_identifier_type_codings
        ),
        selectinload(EncounterModel.hospitalization).selectinload(
            EncounterHospitalization.admit_source_codings
        ),
        selectinload(EncounterModel.hospitalization).selectinload(
            EncounterHospitalization.re_admission_codings
        ),
        selectinload(EncounterModel.hospitalization)
        .selectinload(EncounterHospitalization.diet_preferences)
        .selectinload(EncounterHospitalizationDietPreference.codings),
        selectinload(EncounterModel.hospitalization)
        .selectinload(EncounterHospitalization.special_courtesies)
        .selectinload(EncounterHospitalizationSpecialCourtesy.codings),
        selectinload(EncounterModel.hospitalization)
        .selectinload(EncounterHospitalization.special_arrangements)
        .selectinload(EncounterHospitalizationSpecialArrangement.codings),
        selectinload(EncounterModel.hospitalization).selectinload(
            EncounterHospitalization.discharge_disposition_codings
        ),
        selectinload(EncounterModel.locations).selectinload(
            EncounterLocationRow.physical_type_codings
        ),
    )


def _parse_ref(ref: str, enum_cls) -> tuple:
    """Parse 'Type/id' against any of this resource's reference-type
    enums — generalizes the usual per-field `_parse_X_ref` duplicate seen
    on every other resource, since Encounter alone has 11 distinct
    polymorphic/single-target reference fields and hand-duplicating the
    same 2-line function 11 times would buy nothing."""
    return parse_reference(ref, enum_cls)


def _ref_kwargs(prefix: str, ref: str | None, display: str | None, enum_cls) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM
    constructor kwargs from a FHIR reference string, against any of this
    resource's reference-type enums."""
    ref_type, ref_id = _parse_ref(ref, enum_cls) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_individual_reference(session, org_id, ref_type, ref_id) -> None:
    """Same as `_validate_reference`, but only actually checks existence
    for the two participant.individual target types this system models —
    see `_MODELED_INDIVIDUAL_TYPES`'s docstring above."""
    if ref_type in _MODELED_INDIVIDUAL_TYPES:
        await _validate_reference(session, org_id, ref_type, ref_id, "individual")
