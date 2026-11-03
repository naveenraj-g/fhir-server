from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.measure_report import (
    MeasureReportEvaluatedResource,
    MeasureReportGroup,
    MeasureReportGroupCodeCoding,
    MeasureReportGroupPopulation,
    MeasureReportGroupPopulationCodeCoding,
    MeasureReportGroupStratifier,
    MeasureReportGroupStratifierCode,
    MeasureReportGroupStratifierCodeCoding,
    MeasureReportGroupStratifierStratum,
    MeasureReportGroupStratifierStratumComponent,
    MeasureReportGroupStratifierStratumComponentCodeCoding,
    MeasureReportGroupStratifierStratumComponentValueCoding,
    MeasureReportGroupStratifierStratumPopulation,
    MeasureReportGroupStratifierStratumPopulationCodeCoding,
    MeasureReportGroupStratifierStratumValueCoding,
    MeasureReportIdentifier,
    MeasureReportIdentifierTypeCoding,
    MeasureReportImprovementNotationCoding,
    MeasureReportModel,
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
    "measure_report_id": MeasureReportModel.measure_report_id,
    "status": MeasureReportModel.status,
    "type": MeasureReportModel.type,
    "measure": MeasureReportModel.measure,
    "date": MeasureReportModel.date,
    "created_at": MeasureReportModel.created_at,
    "updated_at": MeasureReportModel.updated_at,
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
    if isinstance(obj, str):
        ref = obj
        disp = None
    elif obj:
        ref = (
            getattr(obj, prefix, None)
            or getattr(obj, f"{prefix}_reference", None)
            or getattr(obj, "reference", None)
        )
        disp = (
            getattr(obj, f"{prefix}_display", None)
            or getattr(obj, "display", None)
            or getattr(obj, "reference_display", None)
        )
    else:
        ref = None
        disp = None

    ref_col = "reference" if prefix == "reference" else f"{prefix}_reference"
    res = {
        ref_col: ref,
        **_ref_kwargs(prefix, ref, disp, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = None
        if obj and not isinstance(obj, str):
            val = (
                getattr(obj, f"{prefix}_{suffix}", None)
                or getattr(obj, f"reference_{suffix}", None)
            )
        if suffix == "identifier_use" and val is not None:
            res[f"{prefix}_{suffix}"] = (
                IdentifierUseModel[val.name] if hasattr(val, "name") else val
            )
        else:
            res[f"{prefix}_{suffix}"] = val
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
        selectinload(MeasureReportModel.identifiers).selectinload(
            MeasureReportIdentifier.type_coding
        ),
        selectinload(MeasureReportModel.improvement_notation_coding),
        selectinload(MeasureReportModel.evaluated_resources),
        selectinload(MeasureReportModel.groups).selectinload(
            MeasureReportGroup.code_coding
        ),
        selectinload(MeasureReportModel.groups)
        .selectinload(MeasureReportGroup.populations)
        .selectinload(MeasureReportGroupPopulation.code_coding),
        selectinload(MeasureReportModel.groups)
        .selectinload(MeasureReportGroup.stratifiers)
        .selectinload(MeasureReportGroupStratifier.codes)
        .selectinload(MeasureReportGroupStratifierCode.coding),
        selectinload(MeasureReportModel.groups)
        .selectinload(MeasureReportGroup.stratifiers)
        .selectinload(MeasureReportGroupStratifier.strata)
        .selectinload(MeasureReportGroupStratifierStratum.value_coding),
        selectinload(MeasureReportModel.groups)
        .selectinload(MeasureReportGroup.stratifiers)
        .selectinload(MeasureReportGroupStratifier.strata)
        .selectinload(MeasureReportGroupStratifierStratum.components)
        .selectinload(MeasureReportGroupStratifierStratumComponent.code_coding),
        selectinload(MeasureReportModel.groups)
        .selectinload(MeasureReportGroup.stratifiers)
        .selectinload(MeasureReportGroupStratifier.strata)
        .selectinload(MeasureReportGroupStratifierStratum.components)
        .selectinload(MeasureReportGroupStratifierStratumComponent.value_coding),
        selectinload(MeasureReportModel.groups)
        .selectinload(MeasureReportGroup.stratifiers)
        .selectinload(MeasureReportGroupStratifier.strata)
        .selectinload(MeasureReportGroupStratifierStratum.populations)
        .selectinload(MeasureReportGroupStratifierStratumPopulation.code_coding),
    )
