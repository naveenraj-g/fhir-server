from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType
from app.models.medication_dispense import (
    MedicationDispenseAuthorizingPrescription,
    MedicationDispenseAuthorizingPrescriptionReferenceType,
    MedicationDispenseCategoryCoding,
    MedicationDispenseContextReferenceType,
    MedicationDispenseDestinationReferenceType,
    MedicationDispenseDetectedIssue,
    MedicationDispenseDetectedIssueReferenceType,
    MedicationDispenseDosageAdditionalInstruction,
    MedicationDispenseDosageAdditionalInstructionCoding,
    MedicationDispenseDosageAsNeededCoding,
    MedicationDispenseDosageInstruction,
    MedicationDispenseDosageMethodCoding,
    MedicationDispenseDosageRouteCoding,
    MedicationDispenseDosageSiteCoding,
    MedicationDispenseEventHistory,
    MedicationDispenseEventHistoryReferenceType,
    MedicationDispenseIdentifier,
    MedicationDispenseIdentifierTypeCoding,
    MedicationDispenseLocationReferenceType,
    MedicationDispenseMedicationCoding,
    MedicationDispenseMedicationReferenceType,
    MedicationDispenseModel,
    MedicationDispenseNote,
    MedicationDispenseNoteAuthorReferenceType,
    MedicationDispensePartOf,
    MedicationDispensePartOfReferenceType,
    MedicationDispensePerformer,
    MedicationDispensePerformerActorReferenceType,
    MedicationDispensePerformerFunctionCoding,
    MedicationDispenseReceiver,
    MedicationDispenseReceiverReferenceType,
    MedicationDispenseStatus,
    MedicationDispenseStatusReasonCoding,
    MedicationDispenseStatusReasonReferenceType,
    MedicationDispenseSubjectReferenceType,
    MedicationDispenseSubstitutionReason,
    MedicationDispenseSubstitutionReasonCoding,
    MedicationDispenseSubstitutionResponsibleParty,
    MedicationDispenseSubstitutionResponsiblePartyReferenceType,
    MedicationDispenseSubstitutionTypeCoding,
    MedicationDispenseSupportingInfo,
    MedicationDispenseTypeCoding,
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
    "medication_dispense_id": MedicationDispenseModel.medication_dispense_id,
    "status": MedicationDispenseModel.status,
    "when_prepared": MedicationDispenseModel.when_prepared,
    "when_handed_over": MedicationDispenseModel.when_handed_over,
    "created_at": MedicationDispenseModel.created_at,
    "updated_at": MedicationDispenseModel.updated_at,
}


def _ref_kwargs(prefix: str, ref_str: str | None, display: str | None, enum_cls) -> dict:
    if not ref_str:
        return {
            f"{prefix}_type": None,
            f"{prefix}_id": None,
            f"{prefix}_display": display,
        }
    if enum_cls is None:
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
    ref = (
        getattr(obj, prefix, None)
        or getattr(obj, f"{prefix}_reference", None)
        or getattr(obj, "reference", None)
        if obj
        else None
    )
    disp = (
        getattr(obj, f"{prefix}_display", None)
        or getattr(obj, "reference_display", None)
        or getattr(obj, "display", None)
        if obj
        else None
    )
    ref_col = prefix if prefix.endswith("_reference") else f"{prefix}_reference"
    res = {
        ref_col: ref,
        **_ref_kwargs(prefix, ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = (
            getattr(obj, f"{prefix}_{suffix}", None)
            or getattr(obj, f"reference_{suffix}", None)
            if obj
            else None
        )
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
        selectinload(MedicationDispenseModel.identifiers).selectinload(
            MedicationDispenseIdentifier.type_codings
        ),
        selectinload(MedicationDispenseModel.part_of),
        selectinload(MedicationDispenseModel.status_reason_codings),
        selectinload(MedicationDispenseModel.category_codings),
        selectinload(MedicationDispenseModel.medication_codings),
        selectinload(MedicationDispenseModel.supporting_informations),
        selectinload(MedicationDispenseModel.performers).selectinload(
            MedicationDispensePerformer.function_codings
        ),
        selectinload(MedicationDispenseModel.authorizing_prescriptions),
        selectinload(MedicationDispenseModel.type_codings),
        selectinload(MedicationDispenseModel.receivers),
        selectinload(MedicationDispenseModel.notes),
        selectinload(MedicationDispenseModel.dosage_instructions).selectinload(
            MedicationDispenseDosageInstruction.additional_instructions
        ).selectinload(
            MedicationDispenseDosageAdditionalInstruction.codings
        ),
        selectinload(MedicationDispenseModel.dosage_instructions).selectinload(
            MedicationDispenseDosageInstruction.site_codings
        ),
        selectinload(MedicationDispenseModel.dosage_instructions).selectinload(
            MedicationDispenseDosageInstruction.route_codings
        ),
        selectinload(MedicationDispenseModel.dosage_instructions).selectinload(
            MedicationDispenseDosageInstruction.method_codings
        ),
        selectinload(MedicationDispenseModel.dosage_instructions).selectinload(
            MedicationDispenseDosageInstruction.as_needed_codings
        ),
        selectinload(MedicationDispenseModel.substitution_type_codings),
        selectinload(MedicationDispenseModel.substitution_reasons).selectinload(
            MedicationDispenseSubstitutionReason.codings
        ),
        selectinload(MedicationDispenseModel.substitution_responsible_parties),
        selectinload(MedicationDispenseModel.detected_issues),
        selectinload(MedicationDispenseModel.event_history),
    )
