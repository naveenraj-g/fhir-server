from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType
from app.models.medication_administration import (
    MedicationAdministrationCategoryCoding,
    MedicationAdministrationContextReferenceType,
    MedicationAdministrationDevice,
    MedicationAdministrationDeviceReferenceType,
    MedicationAdministrationDosageMethodCoding,
    MedicationAdministrationDosageRouteCoding,
    MedicationAdministrationDosageSiteCoding,
    MedicationAdministrationEventHistory,
    MedicationAdministrationEventHistoryReferenceType,
    MedicationAdministrationIdentifier,
    MedicationAdministrationIdentifierTypeCoding,
    MedicationAdministrationMedicationCoding,
    MedicationAdministrationMedicationReferenceType,
    MedicationAdministrationModel,
    MedicationAdministrationNote,
    MedicationAdministrationNoteAuthorReferenceType,
    MedicationAdministrationPartOf,
    MedicationAdministrationPartOfReferenceType,
    MedicationAdministrationPerformer,
    MedicationAdministrationPerformerActorReferenceType,
    MedicationAdministrationPerformerFunctionCoding,
    MedicationAdministrationReasonCode,
    MedicationAdministrationReasonCodeCoding,
    MedicationAdministrationReasonReference,
    MedicationAdministrationReasonReferenceType,
    MedicationAdministrationRequestReferenceType,
    MedicationAdministrationStatus,
    MedicationAdministrationStatusReason,
    MedicationAdministrationStatusReasonCoding,
    MedicationAdministrationSubjectReferenceType,
    MedicationAdministrationSupportingInformation,
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
    "medication_administration_id": MedicationAdministrationModel.medication_administration_id,
    "status": MedicationAdministrationModel.status,
    "effective_date_time": MedicationAdministrationModel.effective_date_time,
    "created_at": MedicationAdministrationModel.created_at,
    "updated_at": MedicationAdministrationModel.updated_at,
}


def _ref_kwargs(prefix: str, ref_str: str | None, display: str | None, enum_cls) -> dict:
    if not ref_str:
        return {
            f"{prefix}_type": None,
            f"{prefix}_id": None,
            f"{prefix}_display": display,
        }
    if enum_cls is None:
        # Open type (e.g. supporting_information)
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
    ref = getattr(obj, prefix, None) or getattr(obj, f"{prefix}_reference", None) or getattr(obj, "reference", None) if obj else None
    disp = getattr(obj, f"{prefix}_display", None) or getattr(obj, "reference_display", None) or getattr(obj, "display", None) if obj else None
    res = {
        f"{prefix}_reference": ref,
        **_ref_kwargs(prefix, ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"{prefix}_{suffix}", None) or getattr(obj, f"reference_{suffix}", None) if obj else None
        if suffix == "identifier_use" and val is not None:
            res[f"{prefix}_{suffix}"] = (
                IdentifierUseModel[val.name] if hasattr(val, "name") else val
            )
        else:
            res[f"{prefix}_{suffix}"] = val
    return res


def _list_reference_kwargs(obj, enum_cls) -> dict:
    ref = getattr(obj, "reference", None)
    disp = getattr(obj, "reference_display", None) or getattr(obj, "display", None)
    res = {
        "reference_reference": ref,
        **_ref_kwargs("reference", ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"reference_{suffix}", None) or getattr(obj, f"identifier_{suffix}", None)
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
        selectinload(MedicationAdministrationModel.identifiers).selectinload(
            MedicationAdministrationIdentifier.type_codings
        ),
        selectinload(MedicationAdministrationModel.part_of),
        selectinload(MedicationAdministrationModel.status_reasons).selectinload(
            MedicationAdministrationStatusReason.codings
        ),
        selectinload(MedicationAdministrationModel.category_codings),
        selectinload(MedicationAdministrationModel.medication_codings),
        selectinload(MedicationAdministrationModel.supporting_informations),
        selectinload(MedicationAdministrationModel.performers).selectinload(
            MedicationAdministrationPerformer.function_codings
        ),
        selectinload(MedicationAdministrationModel.reason_codes).selectinload(
            MedicationAdministrationReasonCode.codings
        ),
        selectinload(MedicationAdministrationModel.reason_references),
        selectinload(MedicationAdministrationModel.devices),
        selectinload(MedicationAdministrationModel.notes),
        selectinload(MedicationAdministrationModel.dosage_site_codings),
        selectinload(MedicationAdministrationModel.dosage_route_codings),
        selectinload(MedicationAdministrationModel.dosage_method_codings),
        selectinload(MedicationAdministrationModel.event_history),
    )
