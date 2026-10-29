from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.enums import EncounterReferenceType
from app.models.questionnaire_response import (
    QuestionnaireResponseAuthorReferenceType,
    QuestionnaireResponseBasedOnReferenceType,
    QuestionnaireResponseModel,
    QuestionnaireResponsePartOfReferenceType,
    QuestionnaireResponseSourceReferenceType,
)
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_MODELED_AUTHOR_TYPES",
    "_MODELED_SOURCE_TYPES",
    "_SORTABLE_FIELDS",
    "_any_ref_kwargs",
    "_author_ref_kwargs",
    "_based_on_ref_kwargs",
    "_encounter_ref_kwargs",
    "_identifier_fallback_kwargs",
    "_org_ref_kwargs",
    "_parse_any_ref",
    "_parse_author_ref",
    "_parse_based_on_ref",
    "_parse_encounter_ref",
    "_parse_org_ref",
    "_parse_part_of_ref",
    "_parse_source_ref",
    "_part_of_ref_kwargs",
    "_reference_kwargs",
    "_source_ref_kwargs",
    "_validate_author_reference",
    "_validate_reference",
    "_validate_source_reference",
    "_with_relationships",
]

# Of QuestionnaireResponse.author's 6 allowed target types, only these
# three are modeled resources in this system (registered in
# RESOURCE_REGISTRY — see app/core/reference_resolver.py). Device/Patient/
# RelatedPerson rows always rely on the reference_identifier_* logical-
# reference fallback instead — calling ensure_resource_exists() for an
# unregistered type fails closed (422 on every valid reference to one), so
# validation is skipped for those three — same reasoning as Appointment's
# own _MODELED_PARTICIPANT_ACTOR_TYPES.
_MODELED_AUTHOR_TYPES = {
    QuestionnaireResponseAuthorReferenceType.Practitioner,
    QuestionnaireResponseAuthorReferenceType.PractitionerRole,
    QuestionnaireResponseAuthorReferenceType.Organization,
}

# Of QuestionnaireResponse.source's 4 allowed target types, only these two
# are modeled resources here.
_MODELED_SOURCE_TYPES = {
    QuestionnaireResponseSourceReferenceType.Practitioner,
    QuestionnaireResponseSourceReferenceType.PractitionerRole,
}


_SORTABLE_FIELDS = {
    "questionnaire_response_id": QuestionnaireResponseModel.questionnaire_response_id,
    "status": QuestionnaireResponseModel.status,
    "authored": QuestionnaireResponseModel.authored,
    "created_at": QuestionnaireResponseModel.created_at,
    "updated_at": QuestionnaireResponseModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every QuestionnaireResponse sub-resource to avoid N+1 and
    async lazy-load failures. `items`/`answers` are the flat, every-depth
    collections (see QuestionnaireResponseModel's own docstring) —
    selectinload here loads every row in one extra query each, regardless
    of nesting depth."""
    return stmt.options(
        selectinload(QuestionnaireResponseModel.identifier_type_codings),
        selectinload(QuestionnaireResponseModel.based_ons),
        selectinload(QuestionnaireResponseModel.part_ofs),
        selectinload(QuestionnaireResponseModel.items),
        selectinload(QuestionnaireResponseModel.answers),
    )


def _identifier_fallback_kwargs(model_prefix: str, obj) -> dict:
    """Build `{model_prefix}_identifier_*` ORM constructor kwargs from one
    of the `_SingleReferenceInput`/`_ReferenceListInput` payload objects
    (app.schemas.questionnaire_response.input.reference) — those objects'
    own attributes are always bare `reference_identifier_*` (the whole
    object IS the reference, so there's no per-field prefix at the schema
    layer), but the target columns on subject/encounter/author/source are
    `{model_prefix}_identifier_*`. based_on/part_of's own child-table
    columns ARE bare `reference_identifier_*` already, so those two reuse
    `_reference_kwargs("reference", obj)` directly instead of this
    adapter — see full.py."""
    return {
        f"{model_prefix}_{suffix}": getattr(obj, f"reference_{suffix}")
        for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
    }


def _parse_any_ref(ref: str) -> tuple[str | None, int | None]:
    """Parse a 'ResourceType/id' string into (type, id) WITHOUT validating
    the type against any enum — used for `subject`, the one genuinely
    Reference(Any) field on this resource. Never raises — mirrors
    app.repository.appointment._shared._parse_any_ref."""
    parts = ref.split("/", 1)
    if len(parts) != 2:
        return None, None
    resource_type, raw_id = parts
    try:
        return resource_type, int(raw_id)
    except ValueError:
        return resource_type, None


def _any_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """`{prefix}_type` is a plain free-text string column, never a
    Postgres Enum — see CLAUDE.md's Reference(Any) invariant."""
    ref_type, ref_id = _parse_any_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_encounter_ref(ref: str) -> tuple:
    """Parse 'Encounter/20001' → (EncounterReferenceType.Encounter, 20001).
    Encounter is the only allowed target type AND is a modeled resource,
    so this one's existence check is always enforced (see full.py)."""
    return parse_reference(ref, EncounterReferenceType)


def _encounter_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_encounter_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_author_ref(ref: str) -> tuple:
    """Parse e.g. 'Practitioner/30001' →
    (QuestionnaireResponseAuthorReferenceType.Practitioner, 30001)."""
    return parse_reference(ref, QuestionnaireResponseAuthorReferenceType)


def _author_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_author_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_author_reference(session, org_id, ref_type, ref_id) -> None:
    """Same as `_validate_reference`, but only actually checks existence
    for the three author target types this system models — see
    `_MODELED_AUTHOR_TYPES`'s docstring above."""
    if ref_type in _MODELED_AUTHOR_TYPES:
        await _validate_reference(session, org_id, ref_type, ref_id, "author")


def _parse_source_ref(ref: str) -> tuple:
    return parse_reference(ref, QuestionnaireResponseSourceReferenceType)


def _source_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_source_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_source_reference(session, org_id, ref_type, ref_id) -> None:
    if ref_type in _MODELED_SOURCE_TYPES:
        await _validate_reference(session, org_id, ref_type, ref_id, "source")


def _parse_based_on_ref(ref: str) -> tuple:
    """Neither CarePlan nor ServiceRequest is a modeled resource here —
    the existence check is never attempted for this field (see
    app.models.questionnaire_response.enums.QuestionnaireResponseBasedOnReferenceType's
    docstring)."""
    return parse_reference(ref, QuestionnaireResponseBasedOnReferenceType)


def _based_on_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_based_on_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_part_of_ref(ref: str) -> tuple:
    """Neither Observation nor Procedure is a modeled resource here."""
    return parse_reference(ref, QuestionnaireResponsePartOfReferenceType)


def _part_of_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_part_of_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }
