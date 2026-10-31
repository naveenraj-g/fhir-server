from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.condition import (
    ConditionAsserterReferenceType,
    ConditionBodySite,
    ConditionCategory,
    ConditionEvidence,
    ConditionEvidenceCode,
    ConditionIdentifier,
    ConditionModel,
    ConditionNoteAuthorReferenceType,
    ConditionQuantityComparator as ConditionQuantityComparatorModel,
    ConditionRecorderReferenceType,
    ConditionStage,
    ConditionStageAssessmentReferenceType,
)
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
    SubjectReferenceType,
)

_IDENTIFIER_FALLBACK_SUFFIXES = (
    "identifier_use",
    "identifier_system",
    "identifier_value",
    "identifier_type_text",
)

_SORTABLE_FIELDS = {
    "condition_id": ConditionModel.condition_id,
    "recorded_date": ConditionModel.recorded_date,
    "created_at": ConditionModel.created_at,
    "updated_at": ConditionModel.updated_at,
}


def _reference_kwargs(prefix: str, payload) -> dict:
    """Build {prefix}_identifier_* ORM constructor kwargs from payload."""
    if payload is None:
        return {}
    res = {}
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(payload, f"reference_{suffix}", None)
        if val is not None:
            res[f"{prefix}_{suffix}"] = val
    return res


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, SubjectReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, EncounterReferenceType)


def _parse_recorder_ref(ref: str) -> tuple:
    return parse_reference(ref, ConditionRecorderReferenceType)


def _parse_asserter_ref(ref: str) -> tuple:
    return parse_reference(ref, ConditionAsserterReferenceType)


def _parse_assessment_ref(ref: str) -> tuple:
    return parse_reference(ref, ConditionStageAssessmentReferenceType)


def _parse_org_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_note_author_ref(ref: str) -> tuple:
    return parse_reference(ref, ConditionNoteAuthorReferenceType)


async def _validate_ref(session, org_id: str, ref_type, ref_id: int | None, field_name: str) -> None:
    if not ref_type or ref_id is None:
        return
    type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    if type_str in RESOURCE_REGISTRY:
        await ensure_resource_exists(
            session, type_str, ref_id, org_id=org_id, field_name=field_name
        )


def _with_relationships(stmt):
    """Eager-load all Condition sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(ConditionModel.identifiers).selectinload(
            ConditionIdentifier.type_codings
        ),
        selectinload(ConditionModel.clinical_status_codings),
        selectinload(ConditionModel.verification_status_codings),
        selectinload(ConditionModel.categories).selectinload(
            ConditionCategory.codings
        ),
        selectinload(ConditionModel.severity_codings),
        selectinload(ConditionModel.code_codings),
        selectinload(ConditionModel.body_sites).selectinload(
            ConditionBodySite.codings
        ),
        selectinload(ConditionModel.stages).selectinload(
            ConditionStage.summary_codings
        ),
        selectinload(ConditionModel.stages).selectinload(
            ConditionStage.type_codings
        ),
        selectinload(ConditionModel.stages).selectinload(
            ConditionStage.assessments
        ),
        selectinload(ConditionModel.evidence)
        .selectinload(ConditionEvidence.codes)
        .selectinload(ConditionEvidenceCode.codings),
        selectinload(ConditionModel.evidence).selectinload(
            ConditionEvidence.details
        ),
        selectinload(ConditionModel.notes),
    )
