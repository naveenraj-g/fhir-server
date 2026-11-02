from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.models.clinical_impression import (
    ClinicalImpressionAssessorReferenceType,
    ClinicalImpressionFindingItemCodingModel,
    ClinicalImpressionFindingModel,
    ClinicalImpressionFindingReferenceType,
    ClinicalImpressionIdentifierModel,
    ClinicalImpressionIdentifierTypeCodingModel,
    ClinicalImpressionInvestigationCodeCodingModel,
    ClinicalImpressionInvestigationItemModel,
    ClinicalImpressionInvestigationModel,
    ClinicalImpressionModel,
    ClinicalImpressionNoteAuthorReferenceType,
    ClinicalImpressionNoteModel,
    ClinicalImpressionPreviousReferenceType,
    ClinicalImpressionProblemModel,
    ClinicalImpressionProblemReferenceType,
    ClinicalImpressionPrognosisCodeableConceptModel,
    ClinicalImpressionPrognosisCodingModel,
    ClinicalImpressionPrognosisReferenceModel,
    ClinicalImpressionPrognosisReferenceType,
    ClinicalImpressionProtocolModel,
    ClinicalImpressionStatusReasonCodingModel,
    ClinicalImpressionCodeCodingModel,
    ClinicalImpressionSupportingInfoModel,
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
    "clinical_impression_id": ClinicalImpressionModel.clinical_impression_id,
    "status": ClinicalImpressionModel.status,
    "date": ClinicalImpressionModel.date,
    "effective_date_time": ClinicalImpressionModel.effective_date_time,
    "created_at": ClinicalImpressionModel.created_at,
    "updated_at": ClinicalImpressionModel.updated_at,
}


def _ref_kwargs(prefix: str, ref_str: str | None, display: str | None, enum_cls) -> dict:
    disp_key = "display" if prefix == "reference" else f"{prefix}_display"
    if not ref_str:
        return {
            f"{prefix}_type": None,
            f"{prefix}_id": None,
            disp_key: display,
        }
    if enum_cls is None:
        parts = ref_str.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            return {
                f"{prefix}_type": parts[0],
                f"{prefix}_id": int(parts[1]),
                disp_key: display,
            }
        return {
            f"{prefix}_type": None,
            f"{prefix}_id": None,
            disp_key: display,
        }
    res_type, res_id = parse_reference(ref_str, enum_cls)
    return {
        f"{prefix}_type": res_type,
        f"{prefix}_id": res_id,
        disp_key: display,
    }


def _single_reference_kwargs(prefix: str, obj, enum_cls) -> dict:
    ref = getattr(obj, "reference", None) if obj else None
    disp = getattr(obj, "reference_display", None) if obj else None
    if isinstance(obj, str):
        ref = obj
        disp = None

    ref_col = prefix if prefix.endswith("reference") else f"{prefix}_reference"
    res = {
        ref_col: ref,
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


def _list_reference_kwargs(obj, enum_cls, prefix: str = "reference") -> dict:
    ref = getattr(obj, "reference", None) if not isinstance(obj, str) else obj
    disp = getattr(obj, "reference_display", None) if not isinstance(obj, str) else None
    ref_col = prefix if prefix.endswith("reference") else f"{prefix}_reference"
    res = {
        ref_col: ref,
        **_ref_kwargs(prefix, ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"reference_{suffix}", None) if not isinstance(obj, str) else None
        key = suffix if prefix == "reference" else f"{prefix}_{suffix}"
        if suffix == "identifier_use" and val is not None:
            res[key] = (
                IdentifierUseModel[val.name] if hasattr(val, "name") else val
            )
        else:
            res[key] = val
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
        selectinload(ClinicalImpressionModel.identifiers).selectinload(
            ClinicalImpressionIdentifierModel.type_codings
        ),
        selectinload(ClinicalImpressionModel.status_reason_codings),
        selectinload(ClinicalImpressionModel.code_codings),
        selectinload(ClinicalImpressionModel.problems),
        selectinload(ClinicalImpressionModel.investigations).selectinload(
            ClinicalImpressionInvestigationModel.code_codings
        ),
        selectinload(ClinicalImpressionModel.investigations).selectinload(
            ClinicalImpressionInvestigationModel.items
        ),
        selectinload(ClinicalImpressionModel.protocols),
        selectinload(ClinicalImpressionModel.findings).selectinload(
            ClinicalImpressionFindingModel.item_codings
        ),
        selectinload(ClinicalImpressionModel.prognosis_codeable_concepts).selectinload(
            ClinicalImpressionPrognosisCodeableConceptModel.codings
        ),
        selectinload(ClinicalImpressionModel.prognosis_references),
        selectinload(ClinicalImpressionModel.supporting_info),
        selectinload(ClinicalImpressionModel.notes),
    )
