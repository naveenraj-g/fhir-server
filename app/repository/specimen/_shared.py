from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType, ServiceRequestReferenceType
from app.models.specimen import (
    SpecimenAdditiveReferenceType,
    SpecimenCollectorReferenceType,
    SpecimenCondition,
    SpecimenContainer,
    SpecimenContainerIdentifier,
    SpecimenIdentifier,
    SpecimenModel,
    SpecimenNoteAuthorReferenceType,
    SpecimenParentReferenceType,
    SpecimenProcessing,
    SpecimenQuantityComparator as SpecimenQuantityComparatorModel,
    SpecimenStatus as SpecimenStatusModel,
    SpecimenSubjectReferenceType,
)
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _prefixed_identifier_kwargs,
)


def _child_reference_kwargs(r, prefix: str = "reference") -> dict:
    if isinstance(r, str):
        return {
            f"{prefix}_reference": r,
            f"{prefix}_display": None,
            **{f"{prefix}_{s}": None for s in _IDENTIFIER_FALLBACK_SUFFIXES},
        }
    display = (
        getattr(r, "display", None)
        or getattr(r, f"{prefix}_display", None)
        or getattr(r, "reference_display", None)
    )
    ref = (
        getattr(r, "reference", None)
        or getattr(r, f"{prefix}_reference", None)
    )
    kwargs = {
        f"{prefix}_reference": ref,
        f"{prefix}_display": display,
    }
    for s in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = (
            getattr(r, s, None)
            or getattr(r, f"{prefix}_{s}", None)
            or getattr(r, f"reference_{s}", None)
        )
        if s == "identifier_use" and val and hasattr(val, "name"):
            val = IdentifierUseModel[val.name]
        kwargs[f"{prefix}_{s}"] = val
    return kwargs


_SORTABLE_FIELDS = {
    "specimen_id": SpecimenModel.specimen_id,
    "status": SpecimenModel.status,
    "received_time": SpecimenModel.received_time,
    "created_at": SpecimenModel.created_at,
    "updated_at": SpecimenModel.updated_at,
}


def _reference_kwargs(prefix: str, payload) -> dict:
    """Build {prefix}_identifier_* ORM constructor kwargs from payload."""
    if payload is None:
        return {f"{prefix}_{suffix}": None for suffix in _IDENTIFIER_FALLBACK_SUFFIXES}
    res = {}
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = (
            getattr(payload, f"reference_{suffix}", None)
            or getattr(payload, suffix, None)
            or getattr(payload, f"{prefix}_{suffix}", None)
        )
        if suffix == "identifier_use" and val and hasattr(val, "name"):
            val = IdentifierUseModel[val.name]
        res[f"{prefix}_{suffix}"] = val
    return res


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, SpecimenSubjectReferenceType)


def _parse_parent_ref(ref: str) -> tuple:
    return parse_reference(ref, SpecimenParentReferenceType)


def _parse_request_ref(ref: str) -> tuple:
    return parse_reference(ref, ServiceRequestReferenceType)


def _parse_collector_ref(ref: str) -> tuple:
    return parse_reference(ref, SpecimenCollectorReferenceType)


def _parse_additive_ref(ref: str) -> tuple:
    return parse_reference(ref, SpecimenAdditiveReferenceType)


def _parse_org_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_note_author_ref(ref: str) -> tuple:
    return parse_reference(ref, SpecimenNoteAuthorReferenceType)


async def _validate_ref(session, org_id: str, ref_type, ref_id: int | None, field_name: str) -> None:
    if not ref_type or ref_id is None:
        return
    type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    if type_str in RESOURCE_REGISTRY:
        await ensure_resource_exists(
            session, type_str, ref_id, org_id=org_id, field_name=field_name
        )


def _with_relationships(stmt):
    """Eager-load all Specimen sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(SpecimenModel.identifiers).selectinload(
            SpecimenIdentifier.type_codings
        ),
        selectinload(SpecimenModel.accession_identifier_type_codings),
        selectinload(SpecimenModel.type_codings),
        selectinload(SpecimenModel.parents),
        selectinload(SpecimenModel.requests),
        selectinload(SpecimenModel.collection_method_codings),
        selectinload(SpecimenModel.collection_body_site_codings),
        selectinload(SpecimenModel.collection_fasting_status_codings),
        selectinload(SpecimenModel.processings).selectinload(
            SpecimenProcessing.procedure_codings
        ),
        selectinload(SpecimenModel.processings).selectinload(
            SpecimenProcessing.additives
        ),
        selectinload(SpecimenModel.containers)
        .selectinload(SpecimenContainer.identifiers)
        .selectinload(SpecimenContainerIdentifier.type_codings),
        selectinload(SpecimenModel.containers).selectinload(
            SpecimenContainer.type_codings
        ),
        selectinload(SpecimenModel.containers).selectinload(
            SpecimenContainer.additive_codings
        ),
        selectinload(SpecimenModel.conditions).selectinload(
            SpecimenCondition.codings
        ),
        selectinload(SpecimenModel.notes),
    )
