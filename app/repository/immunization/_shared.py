from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType
from app.models.immunization import (
    ImmunizationEducationModel,
    ImmunizationEncounterReferenceType,
    ImmunizationFundingSourceCodingModel,
    ImmunizationIdentifierModel,
    ImmunizationIdentifierTypeCodingModel,
    ImmunizationLocationReferenceType,
    ImmunizationManufacturerReferenceType,
    ImmunizationModel,
    ImmunizationNoteAuthorReferenceType,
    ImmunizationNoteModel,
    ImmunizationPatientReferenceType,
    ImmunizationPerformerActorReferenceType,
    ImmunizationPerformerFunctionCodingModel,
    ImmunizationPerformerModel,
    ImmunizationProgramEligibilityModel,
    ImmunizationProtocolAppliedAuthorityReferenceType,
    ImmunizationProtocolAppliedModel,
    ImmunizationProtocolAppliedTargetDiseaseCodingModel,
    ImmunizationProtocolAppliedTargetDiseaseModel,
    ImmunizationReactionDetailReferenceType,
    ImmunizationReactionModel,
    ImmunizationReasonCodeCodingModel,
    ImmunizationReasonCodeModel,
    ImmunizationReasonReferenceModel,
    ImmunizationReasonReferenceType,
    ImmunizationReportOriginCodingModel,
    ImmunizationRouteCodingModel,
    ImmunizationSiteCodingModel,
    ImmunizationStatus,
    ImmunizationStatusReasonCodingModel,
    ImmunizationSubpotentReasonCodingModel,
    ImmunizationSubpotentReasonModel,
    ImmunizationVaccineCodingModel,
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
    "immunization_id": ImmunizationModel.immunization_id,
    "status": ImmunizationModel.status,
    "date": ImmunizationModel.occurrence_date_time,
    "occurrence_date_time": ImmunizationModel.occurrence_date_time,
    "recorded": ImmunizationModel.recorded,
    "created_at": ImmunizationModel.created_at,
    "updated_at": ImmunizationModel.updated_at,
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


async def _validate_ref(session, ref_type, ref_id, org_id: str | None, field_name: str) -> None:
    if not ref_type or not ref_id:
        return
    type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    if type_str in RESOURCE_REGISTRY:
        await ensure_resource_exists(
            session, type_str, ref_id, org_id=org_id, field_name=field_name
        )


def _with_relationships(stmt):
    return stmt.options(
        selectinload(ImmunizationModel.identifiers).selectinload(
            ImmunizationIdentifierModel.type_codings
        ),
        selectinload(ImmunizationModel.status_reason_codings),
        selectinload(ImmunizationModel.vaccine_codings),
        selectinload(ImmunizationModel.report_origin_codings),
        selectinload(ImmunizationModel.site_codings),
        selectinload(ImmunizationModel.route_codings),
        selectinload(ImmunizationModel.funding_source_codings),
        selectinload(ImmunizationModel.performers).selectinload(
            ImmunizationPerformerModel.function_codings
        ),
        selectinload(ImmunizationModel.notes),
        selectinload(ImmunizationModel.reason_codes).selectinload(
            ImmunizationReasonCodeModel.codings
        ),
        selectinload(ImmunizationModel.reason_references),
        selectinload(ImmunizationModel.subpotent_reasons).selectinload(
            ImmunizationSubpotentReasonModel.codings
        ),
        selectinload(ImmunizationModel.education_items),
        selectinload(ImmunizationModel.program_eligibilities).selectinload(
            ImmunizationProgramEligibilityModel.codings
        ),
        selectinload(ImmunizationModel.reactions),
        selectinload(ImmunizationModel.protocol_applied_items)
        .selectinload(ImmunizationProtocolAppliedModel.target_diseases)
        .selectinload(ImmunizationProtocolAppliedTargetDiseaseModel.codings),
    )
