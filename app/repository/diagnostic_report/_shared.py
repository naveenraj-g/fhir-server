from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import ensure_resource_exists
from app.models.diagnostic_report import (
    DiagnosticReportActorReferenceType,
    DiagnosticReportBasedOnReferenceType,
    DiagnosticReportCategory,
    DiagnosticReportConclusionCode,
    DiagnosticReportIdentifier,
    DiagnosticReportModel,
    DiagnosticReportSubjectReferenceType,
)
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES, _org_ref_kwargs, _parse_org_ref

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_MODELED_ACTOR_TYPES",
    "_MODELED_BASED_ON_TYPES",
    "_MODELED_SUBJECT_TYPES",
    "_SORTABLE_FIELDS",
    "_org_ref_kwargs",
    "_parse_org_ref",
    "_ref_kwargs",
    "_single_reference_kwargs",
    "_validate_ref",
    "_with_relationships",
]

# Of the enumerable-target-type fields on DiagnosticReport, only these
# subsets are modeled resources in this system — the existence check is
# only ever attempted for them. `encounter` (Encounter) and `result`
# (Observation) have no "modeled subset" to speak of — each is a single,
# modeled type, so it's always validated directly (modeled_types=None,
# see full.py). `specimen` (Specimen), `imagingStudy` (ImagingStudy), and
# `media.link` (Media) have NO modeled types at all — never validated
# (modeled_types=set()).
_MODELED_SUBJECT_TYPES = {DiagnosticReportSubjectReferenceType.Location}
_MODELED_BASED_ON_TYPES = {
    DiagnosticReportBasedOnReferenceType.MedicationRequest,
    DiagnosticReportBasedOnReferenceType.ServiceRequest,
}
_MODELED_ACTOR_TYPES = {
    DiagnosticReportActorReferenceType.Practitioner,
    DiagnosticReportActorReferenceType.PractitionerRole,
    DiagnosticReportActorReferenceType.Organization,
}


def _ref_kwargs(prefix: str, ref: str | None, display: str | None, enum_cls) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM
    constructor kwargs from a FHIR reference string."""
    if not ref:
        return {f"{prefix}_type": None, f"{prefix}_id": None, f"{prefix}_display": display}
    ref_type, ref_id = parse_reference(ref, enum_cls)
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
    "diagnostic_report_id": DiagnosticReportModel.diagnostic_report_id,
    "status": DiagnosticReportModel.status,
    "issued": DiagnosticReportModel.issued,
    "created_at": DiagnosticReportModel.created_at,
    "updated_at": DiagnosticReportModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every DiagnosticReport sub-resource to avoid N+1 and
    async lazy-load failures."""
    return stmt.options(
        selectinload(DiagnosticReportModel.code_codings),
        selectinload(DiagnosticReportModel.identifiers).selectinload(DiagnosticReportIdentifier.type_codings),
        selectinload(DiagnosticReportModel.based_ons),
        selectinload(DiagnosticReportModel.categories).selectinload(DiagnosticReportCategory.codings),
        selectinload(DiagnosticReportModel.performers),
        selectinload(DiagnosticReportModel.results_interpreters),
        selectinload(DiagnosticReportModel.specimens),
        selectinload(DiagnosticReportModel.results),
        selectinload(DiagnosticReportModel.imaging_studies),
        selectinload(DiagnosticReportModel.media),
        selectinload(DiagnosticReportModel.conclusion_codes).selectinload(DiagnosticReportConclusionCode.codings),
        selectinload(DiagnosticReportModel.presented_forms),
    )
