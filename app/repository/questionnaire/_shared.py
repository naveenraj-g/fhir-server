from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.questionnaire import (
    QuestionnaireContact,
    QuestionnaireIdentifier,
    QuestionnaireItem,
    QuestionnaireJurisdiction,
    QuestionnaireModel,
    QuestionnaireUseContext,
    QuestionnaireUseContextValueReferenceType,
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
    "_SORTABLE_FIELDS",
    "_any_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_any_ref",
    "_parse_org_ref",
    "_parse_use_context_value_ref",
    "_reference_kwargs",
    "_use_context_value_ref_kwargs",
    "_validate_reference",
    "_with_relationships",
]


def _parse_any_ref(ref: str) -> tuple[str | None, int | None]:
    """Parse a 'ResourceType/id' string into (type, id) WITHOUT validating
    the type against any enum — used for item.enableWhen.answer[x],
    item.answerOption.value[x], and item.initial.value[x], all genuinely
    Reference(Any) fields. Never raises — mirrors
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
    """`{prefix}_type` is a plain free-text string column, never a Postgres
    Enum — see CLAUDE.md's Reference(Any) invariant."""
    ref_type, ref_id = _parse_any_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_use_context_value_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (QuestionnaireUseContextValueReferenceType.Location, 230001).
    Closed 7-type set (PlanDefinition|ResearchStudy|InsurancePlan|
    HealthcareService|Group|Location|Organization) — a real Enum, unlike
    the Reference(Any) fields above."""
    return parse_reference(ref, QuestionnaireUseContextValueReferenceType)


def _use_context_value_ref_kwargs(ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_use_context_value_ref(ref) if ref else (None, None)
    return {
        "value_reference_type": ref_type,
        "value_reference_id": ref_id,
        "value_reference_display": display,
    }


_SORTABLE_FIELDS = {
    "questionnaire_id": QuestionnaireModel.questionnaire_id,
    "name": QuestionnaireModel.name,
    "title": QuestionnaireModel.title,
    "status": QuestionnaireModel.status,
    "date": QuestionnaireModel.date,
    "created_at": QuestionnaireModel.created_at,
    "updated_at": QuestionnaireModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every Questionnaire sub-resource to avoid N+1 and async
    lazy-load failures. `items` is the flat, every-depth collection (see
    QuestionnaireModel's own docstring) — selectinload here loads every
    item row in one extra query regardless of nesting depth, and every
    grandchild type is then one further selectinload hop against that
    same flat set (SQLAlchemy batches each hop's IN(...) across all loaded
    parent ids, not per-row)."""
    return stmt.options(
        selectinload(QuestionnaireModel.identifiers).selectinload(
            QuestionnaireIdentifier.type_codings
        ),
        selectinload(QuestionnaireModel.contacts).selectinload(
            QuestionnaireContact.telecoms
        ),
        selectinload(QuestionnaireModel.use_contexts).selectinload(
            QuestionnaireUseContext.value_codeable_concept_codings
        ),
        selectinload(QuestionnaireModel.jurisdictions).selectinload(
            QuestionnaireJurisdiction.codings
        ),
        selectinload(QuestionnaireModel.codings),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.codings),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.enable_whens),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.answer_options),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.initials),
    )
