from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.specimen_definition import (
        SpecimenDefinitionContainerAdditive,
        SpecimenDefinitionModel,
        SpecimenDefinitionTypeTested,
        SpecimenDefinitionTypeTestedHandling,
    )

_COMPARATOR_MAP = {
    "lt": "<",
    "le": "<=",
    "ge": ">=",
    "gt": ">",
    "<": "<",
    "<=": "<=",
    ">=": ">=",
    ">": ">",
}


def _plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            "id": c.id,
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        result.append(entry)
    return result


def plain_specimen_definition_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _plain_coding_list(codings)
    if not coding_list and text is None:
        return None
    return {
        "text": text,
        "codings": coding_list if coding_list else None,
    }


def plain_specimen_definition_identifier(model: SpecimenDefinitionModel) -> dict | None:
    has_identifier = any(
        x is not None
        for x in (
            model.identifier_use,
            model.identifier_type_text,
            model.identifier_system,
            model.identifier_value,
            model.identifier_period_start,
            model.identifier_period_end,
            model.identifier_assigner_display,
            model.identifier_type_codings,
        )
    )
    if not has_identifier:
        return None

    entry: dict[str, Any] = {
        "use": fhir_enum(model.identifier_use) if model.identifier_use else None,
        "system": model.identifier_system,
        "value": model.identifier_value,
        "period_start": model.identifier_period_start.isoformat() if model.identifier_period_start else None,
        "period_end": model.identifier_period_end.isoformat() if model.identifier_period_end else None,
        "assigner": model.identifier_assigner_display or model.identifier_assigner_reference,
    }

    type_codings = _plain_coding_list(model.identifier_type_codings)
    if type_codings or model.identifier_type_text:
        entry["type"] = {
            "text": model.identifier_type_text,
            "coding": type_codings if type_codings else None,
        }
    else:
        entry["type"] = None

    return entry


def plain_specimen_definition_container_additive(a: SpecimenDefinitionContainerAdditive) -> dict:
    entry: dict[str, Any] = {
        "id": a.id,
        "additive_codeable_concept": plain_specimen_definition_codeable_concept(
            a.additive_codings, a.additive_codeable_concept_text
        ),
        "additive_reference": a.additive_reference_reference,
        "additive_reference_display": a.additive_reference_display,
        "additive_reference_type": fhir_enum(a.additive_reference_type) if a.additive_reference_type else None,
        "additive_reference_id": a.additive_reference_id,
    }
    return entry


def plain_specimen_definition_handling(h: SpecimenDefinitionTypeTestedHandling) -> dict:
    comparator = fhir_enum(h.max_duration_comparator) if h.max_duration_comparator else None
    return {
        "id": h.id,
        "temperature_qualifier": plain_specimen_definition_codeable_concept(
            h.temperature_qualifier_codings, h.temperature_qualifier_text
        ),
        "temperature_range_low_value": float(h.temperature_range_low_value) if h.temperature_range_low_value is not None else None,
        "temperature_range_low_unit": h.temperature_range_low_unit,
        "temperature_range_low_system": h.temperature_range_low_system,
        "temperature_range_low_code": h.temperature_range_low_code,
        "temperature_range_high_value": float(h.temperature_range_high_value) if h.temperature_range_high_value is not None else None,
        "temperature_range_high_unit": h.temperature_range_high_unit,
        "temperature_range_high_system": h.temperature_range_high_system,
        "temperature_range_high_code": h.temperature_range_high_code,
        "max_duration_value": float(h.max_duration_value) if h.max_duration_value is not None else None,
        "max_duration_comparator": _COMPARATOR_MAP.get(comparator, comparator),
        "max_duration_unit": h.max_duration_unit,
        "max_duration_system": h.max_duration_system,
        "max_duration_code": h.max_duration_code,
        "instruction": h.instruction,
    }


def plain_specimen_definition_type_tested(tt: SpecimenDefinitionTypeTested) -> dict:
    ret_comparator = fhir_enum(tt.retention_time_comparator) if tt.retention_time_comparator else None
    min_vol_comparator = fhir_enum(tt.container_minimum_volume_quantity_comparator) if tt.container_minimum_volume_quantity_comparator else None

    # container
    has_container = any(
        x is not None
        for x in (
            tt.container_material_text,
            tt.container_material_codings,
            tt.container_type_text,
            tt.container_type_codings,
            tt.container_cap_text,
            tt.container_cap_codings,
            tt.container_description,
            tt.container_capacity_value,
            tt.container_minimum_volume_string,
            tt.container_minimum_volume_quantity_value,
            tt.container_additives,
            tt.container_preparation,
        )
    )

    container = None
    if has_container:
        container = {
            "material": plain_specimen_definition_codeable_concept(
                tt.container_material_codings, tt.container_material_text
            ),
            "type": plain_specimen_definition_codeable_concept(
                tt.container_type_codings, tt.container_type_text
            ),
            "cap": plain_specimen_definition_codeable_concept(
                tt.container_cap_codings, tt.container_cap_text
            ),
            "description": tt.container_description,
            "capacity_value": float(tt.container_capacity_value) if tt.container_capacity_value is not None else None,
            "capacity_unit": tt.container_capacity_unit,
            "capacity_system": tt.container_capacity_system,
            "capacity_code": tt.container_capacity_code,
            "minimum_volume_string": tt.container_minimum_volume_string,
            "minimum_volume_quantity_value": float(tt.container_minimum_volume_quantity_value) if tt.container_minimum_volume_quantity_value is not None else None,
            "minimum_volume_quantity_comparator": _COMPARATOR_MAP.get(min_vol_comparator, min_vol_comparator),
            "minimum_volume_quantity_unit": tt.container_minimum_volume_quantity_unit,
            "minimum_volume_quantity_system": tt.container_minimum_volume_quantity_system,
            "minimum_volume_quantity_code": tt.container_minimum_volume_quantity_code,
            "additive": [
                plain_specimen_definition_container_additive(a)
                for a in (tt.container_additives or [])
            ] or None,
            "preparation": tt.container_preparation,
        }

    return {
        "id": tt.id,
        "is_derived": tt.is_derived,
        "type": plain_specimen_definition_codeable_concept(tt.type_codings, tt.type_text),
        "preference": fhir_enum(tt.preference),
        "container": container,
        "requirement": tt.requirement,
        "retention_time_value": float(tt.retention_time_value) if tt.retention_time_value is not None else None,
        "retention_time_comparator": _COMPARATOR_MAP.get(ret_comparator, ret_comparator),
        "retention_time_unit": tt.retention_time_unit,
        "retention_time_system": tt.retention_time_system,
        "retention_time_code": tt.retention_time_code,
        "rejection_criterion": [
            {
                "id": rc.id,
                "text": rc.text,
                "codings": _plain_coding_list(rc.codings) or None,
            }
            for rc in (tt.rejection_criteria or [])
        ] or None,
        "handling": [
            plain_specimen_definition_handling(h)
            for h in (tt.handlings or [])
        ] or None,
    }


def to_plain_specimen_definition(model: SpecimenDefinitionModel) -> dict:
    """Format SpecimenDefinition ORM model as plain snake_case dict."""
    return {
        "id": model.specimen_definition_id,
        "identifier": plain_specimen_definition_identifier(model),
        "type_collected": plain_specimen_definition_codeable_concept(
            model.type_collected_codings, model.type_collected_text
        ),
        "patient_preparation": [
            {
                "id": pp.id,
                "text": pp.text,
                "codings": _plain_coding_list(pp.codings) or None,
            }
            for pp in (model.patient_preparations or [])
        ] or None,
        "time_aspect": model.time_aspect,
        "collection": [
            {
                "id": col.id,
                "text": col.text,
                "codings": _plain_coding_list(col.codings) or None,
            }
            for col in (model.collections or [])
        ] or None,
        "type_tested": [
            plain_specimen_definition_type_tested(tt)
            for tt in (model.types_tested or [])
        ] or None,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
    }
