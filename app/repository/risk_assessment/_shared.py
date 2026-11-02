from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.models.risk_assessment import (
    RiskAssessmentBasisModel,
    RiskAssessmentCodeCodingModel,
    RiskAssessmentConditionReferenceType,
    RiskAssessmentIdentifierModel,
    RiskAssessmentIdentifierTypeCodingModel,
    RiskAssessmentMethodCodingModel,
    RiskAssessmentModel,
    RiskAssessmentNoteAuthorReferenceType,
    RiskAssessmentNoteModel,
    RiskAssessmentPerformerReferenceType,
    RiskAssessmentPredictionModel,
    RiskAssessmentPredOutcomeCodingModel,
    RiskAssessmentPredQualRiskCodingModel,
    RiskAssessmentReasonCodeCodingModel,
    RiskAssessmentReasonCodeModel,
    RiskAssessmentReasonReferenceModel,
    RiskAssessmentReasonReferenceType,
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
    "risk_assessment_id": RiskAssessmentModel.risk_assessment_id,
    "status": RiskAssessmentModel.status,
    "occurrence_date_time": RiskAssessmentModel.occurrence_date_time,
    "created_at": RiskAssessmentModel.created_at,
    "updated_at": RiskAssessmentModel.updated_at,
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
    ref = getattr(obj, "reference", None) if obj else None
    disp = getattr(obj, "reference_display", None) if obj else None
    if isinstance(obj, str):
        ref = obj
        disp = None

    res = {
        f"{prefix}_reference": ref,
        **_ref_kwargs(prefix, ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"reference_{suffix}", None) if not isinstance(obj, str) and obj else None
        if suffix == "identifier_use" and val is not None:
            res[f"{prefix}_{suffix}"] = (
                IdentifierUseModel[val.name] if hasattr(val, "name") else val
            )
        else:
            res[f"{prefix}_{suffix}"] = val
    return res


def _list_reference_kwargs(obj, enum_cls) -> dict:
    ref = getattr(obj, "reference", None) if not isinstance(obj, str) else obj
    disp = getattr(obj, "reference_display", None) if not isinstance(obj, str) else None
    res = {
        "reference_reference": ref,
        **_ref_kwargs("reference", ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"reference_{suffix}", None) if not isinstance(obj, str) else None
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
        selectinload(RiskAssessmentModel.identifiers).selectinload(
            RiskAssessmentIdentifierModel.type_codings
        ),
        selectinload(RiskAssessmentModel.method_codings),
        selectinload(RiskAssessmentModel.code_codings),
        selectinload(RiskAssessmentModel.reason_codes).selectinload(
            RiskAssessmentReasonCodeModel.codings
        ),
        selectinload(RiskAssessmentModel.reason_references),
        selectinload(RiskAssessmentModel.basis),
        selectinload(RiskAssessmentModel.predictions).selectinload(
            RiskAssessmentPredictionModel.outcome_codings
        ),
        selectinload(RiskAssessmentModel.predictions).selectinload(
            RiskAssessmentPredictionModel.qualitative_risk_codings
        ),
        selectinload(RiskAssessmentModel.notes),
    )
