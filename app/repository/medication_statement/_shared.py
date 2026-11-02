from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType
from app.models.medication_statement import (
    MedicationStatementBasedOn,
    MedicationStatementBasedOnReferenceType,
    MedicationStatementCategoryCoding,
    MedicationStatementContextReferenceType,
    MedicationStatementDerivedFrom,
    MedicationStatementDosage,
    MedicationStatementDosageAdditionalInstruction,
    MedicationStatementDosageAdditionalInstructionCoding,
    MedicationStatementDosageAsNeededCoding,
    MedicationStatementDosageMethodCoding,
    MedicationStatementDosageRouteCoding,
    MedicationStatementDosageSiteCoding,
    MedicationStatementIdentifier,
    MedicationStatementIdentifierTypeCoding,
    MedicationStatementInformationSourceReferenceType,
    MedicationStatementMedicationCoding,
    MedicationStatementMedicationReferenceType,
    MedicationStatementModel,
    MedicationStatementNote,
    MedicationStatementNoteAuthorReferenceType,
    MedicationStatementPartOf,
    MedicationStatementPartOfReferenceType,
    MedicationStatementReasonCode,
    MedicationStatementReasonCodeCoding,
    MedicationStatementReasonReference,
    MedicationStatementReasonReferenceType,
    MedicationStatementStatus,
    MedicationStatementStatusReason,
    MedicationStatementStatusReasonCoding,
    MedicationStatementSubjectReferenceType,
)

_IDENTIFIER_FALLBACK_SUFFIXES = (
    "identifier_use",
    "identifier_type_system",
    "identifier_type_version",
    "identifier_type_code",
    "identifier_type_display",
    "identifier_type_user_selected",
    "identifier_type_text",
    "identifier_system",
    "identifier_value",
    "identifier_period_start",
    "identifier_period_end",
)

_SORTABLE_FIELDS = {
    "medication_statement_id": MedicationStatementModel.medication_statement_id,
    "status": MedicationStatementModel.status,
    "effective_date_time": MedicationStatementModel.effective_date_time,
    "date_asserted": MedicationStatementModel.date_asserted,
    "created_at": MedicationStatementModel.created_at,
    "updated_at": MedicationStatementModel.updated_at,
}


def _parse_org_ref(ref: str | None) -> tuple:
    if not ref:
        return None, None
    res_type, res_id = parse_reference(ref, OrganizationReferenceType)
    return res_type, res_id


def _ref_kwargs(prefix: str, ref_str: str | None, display: str | None, enum_cls) -> dict:
    if not ref_str:
        return {
            f"{prefix}_type": None,
            f"{prefix}_id": None,
            f"{prefix}_display": display,
        }
    if enum_cls is None:
        # Open type (e.g. derived_from)
        parts = ref_str.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            return {
                f"{prefix}_type": parts[0],
                f"{prefix}_id": int(parts[1]),
                f"{prefix}_display": display,
            }
        return {
            f"{prefix}_type": None,
            f"{prefix}_id": None,
            f"{prefix}_display": display,
        }
    res_type, res_id = parse_reference(ref_str, enum_cls)
    return {
        f"{prefix}_type": res_type,
        f"{prefix}_id": res_id,
        f"{prefix}_display": display,
    }


def _single_reference_kwargs(prefix: str, obj, enum_cls) -> dict:
    ref = getattr(obj, "reference", None) if obj else None
    disp = getattr(obj, "reference_display", None) if obj else None
    res = {
        f"{prefix}_reference": ref,
        **_ref_kwargs(prefix, ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"reference_{suffix}", None) if obj else None
        if suffix == "identifier_use" and val is not None:
            res[f"{prefix}_{suffix}"] = (
                IdentifierUseModel[val.name] if hasattr(val, "name") else val
            )
        else:
            res[f"{prefix}_{suffix}"] = val
    return res


def _list_reference_kwargs(obj, enum_cls) -> dict:
    ref = getattr(obj, "reference", None)
    disp = getattr(obj, "reference_display", None)
    res = {
        "reference_reference": ref,
        **_ref_kwargs("reference", ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"reference_{suffix}", None)
        if suffix == "identifier_use" and val is not None:
            res[f"reference_{suffix}"] = (
                IdentifierUseModel[val.name] if hasattr(val, "name") else val
            )
        else:
            res[f"reference_{suffix}"] = val
    return res


async def _validate_ref(
    session, org_id: str, field_name: str, ref_type, ref_id: int | None
) -> None:
    if not ref_type or ref_id is None:
        return
    type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    if type_str in RESOURCE_REGISTRY:
        await ensure_resource_exists(
            session, type_str, ref_id, org_id=org_id, field_name=field_name
        )


def _with_relationships(stmt):
    return stmt.options(
        selectinload(MedicationStatementModel.identifiers).selectinload(
            MedicationStatementIdentifier.type_codings
        ),
        selectinload(MedicationStatementModel.based_on),
        selectinload(MedicationStatementModel.part_of),
        selectinload(MedicationStatementModel.status_reasons).selectinload(
            MedicationStatementStatusReason.codings
        ),
        selectinload(MedicationStatementModel.category_codings),
        selectinload(MedicationStatementModel.medication_codings),
        selectinload(MedicationStatementModel.derived_from),
        selectinload(MedicationStatementModel.reason_codes).selectinload(
            MedicationStatementReasonCode.codings
        ),
        selectinload(MedicationStatementModel.reason_references),
        selectinload(MedicationStatementModel.notes),
        selectinload(MedicationStatementModel.dosages)
        .selectinload(MedicationStatementDosage.additional_instructions)
        .selectinload(MedicationStatementDosageAdditionalInstruction.codings),
        selectinload(MedicationStatementModel.dosages).selectinload(
            MedicationStatementDosage.site_codings
        ),
        selectinload(MedicationStatementModel.dosages).selectinload(
            MedicationStatementDosage.route_codings
        ),
        selectinload(MedicationStatementModel.dosages).selectinload(
            MedicationStatementDosage.method_codings
        ),
        selectinload(MedicationStatementModel.dosages).selectinload(
            MedicationStatementDosage.as_needed_codings
        ),
    )
