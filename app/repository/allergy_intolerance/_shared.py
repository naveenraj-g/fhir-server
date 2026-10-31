from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.allergy_intolerance import (
    AllergyIntoleranceAsserterReferenceType,
    AllergyIntoleranceEncounterReferenceType,
    AllergyIntoleranceIdentifier,
    AllergyIntoleranceIdentifierTypeCoding,
    AllergyIntoleranceModel,
    AllergyIntoleranceNote,
    AllergyIntoleranceNoteAuthorReferenceType,
    AllergyIntolerancePatientReferenceType,
    AllergyIntoleranceReaction,
    AllergyIntoleranceReactionManifestation,
    AllergyIntoleranceRecorderReferenceType,
)
from app.models.enums import OrganizationReferenceType

_SORTABLE_FIELDS = {
    "allergy_intolerance_id": AllergyIntoleranceModel.allergy_intolerance_id,
    "clinical_status": AllergyIntoleranceModel.clinical_status_text,
    "verification_status": AllergyIntoleranceModel.verification_status_text,
    "type": AllergyIntoleranceModel.type,
    "criticality": AllergyIntoleranceModel.criticality,
    "onset_date_time": AllergyIntoleranceModel.onset_date_time,
    "recorded_date": AllergyIntoleranceModel.recorded_date,
    "last_occurrence": AllergyIntoleranceModel.last_occurrence,
    "created_at": AllergyIntoleranceModel.created_at,
    "updated_at": AllergyIntoleranceModel.updated_at,
}


def _parse_patient_ref(ref: str) -> tuple:
    return parse_reference(ref, AllergyIntolerancePatientReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, AllergyIntoleranceEncounterReferenceType)


def _parse_recorder_ref(ref: str) -> tuple:
    return parse_reference(ref, AllergyIntoleranceRecorderReferenceType)


def _parse_asserter_ref(ref: str) -> tuple:
    return parse_reference(ref, AllergyIntoleranceAsserterReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_author_ref(ref: str) -> tuple:
    return parse_reference(ref, AllergyIntoleranceNoteAuthorReferenceType)


def _parse_reaction_author_ref(ref: str) -> tuple:
    return parse_reference(ref, AllergyIntoleranceNoteAuthorReferenceType)


async def _validate_ref(
    session, org_id: str, ref_type, ref_id: int | None, field_name: str
) -> None:
    if not ref_type or ref_id is None:
        return
    type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    if type_str in RESOURCE_REGISTRY:
        await ensure_resource_exists(
            session, type_str, ref_id, org_id=org_id, field_name=field_name
        )


def _with_relationships(stmt):
    """Eager-load all AllergyIntolerance sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(AllergyIntoleranceModel.identifiers).selectinload(
            AllergyIntoleranceIdentifier.type_codings
        ),
        selectinload(AllergyIntoleranceModel.clinical_status_codings),
        selectinload(AllergyIntoleranceModel.verification_status_codings),
        selectinload(AllergyIntoleranceModel.code_codings),
        selectinload(AllergyIntoleranceModel.notes),
        selectinload(AllergyIntoleranceModel.reactions).selectinload(
            AllergyIntoleranceReaction.substance_codings
        ),
        selectinload(AllergyIntoleranceModel.reactions)
        .selectinload(AllergyIntoleranceReaction.manifestations)
        .selectinload(AllergyIntoleranceReactionManifestation.codings),
        selectinload(AllergyIntoleranceModel.reactions).selectinload(
            AllergyIntoleranceReaction.exposure_route_codings
        ),
        selectinload(AllergyIntoleranceModel.reactions).selectinload(
            AllergyIntoleranceReaction.notes
        ),
    )
