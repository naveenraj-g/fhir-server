from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.medication import (
    MedicationIdentifier,
    MedicationIngredient,
    MedicationModel,
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
    "medication_id": MedicationModel.medication_id,
    "status": MedicationModel.status,
    "created_at": MedicationModel.created_at,
    "updated_at": MedicationModel.updated_at,
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


def _single_reference_kwargs(prefix: str, obj: Any, enum_cls: Any) -> dict:
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


async def _validate_ref(
    session, org_id: str, field_name: str, ref_type: Any, ref_id: int | None
) -> None:
    if not ref_type or ref_id is None:
        return
    res_type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    await ensure_resource_exists(
        session, res_type_str, ref_id, org_id=org_id, field_name=field_name
    )


def _with_relationships(stmt):
    """Eager-load all relationships on MedicationModel."""
    return stmt.options(
        selectinload(MedicationModel.identifiers).selectinload(
            MedicationIdentifier.type_codings
        ),
        selectinload(MedicationModel.code_codings),
        selectinload(MedicationModel.form_codings),
        selectinload(MedicationModel.ingredients).selectinload(
            MedicationIngredient.item_codings
        ),
    )
