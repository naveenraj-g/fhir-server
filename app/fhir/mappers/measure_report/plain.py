from typing import Any

from app.fhir.datatypes import fhir_enum
from app.models.measure_report import MeasureReportModel


def _plain_coding(c) -> dict[str, Any]:
    return {
        "system": getattr(c, "system", None),
        "version": getattr(c, "version", None),
        "code": getattr(c, "code", None),
        "display": getattr(c, "display", None),
        "user_selected": getattr(c, "user_selected", None),
    }


def _to_plain_identifier(ident) -> dict[str, Any]:
    assigner = ident.assigner_reference
    if not assigner and ident.assigner_type and ident.assigner_id:
        assigner = f"{fhir_enum(ident.assigner_type)}/{ident.assigner_id}"
    return {
        "id": ident.id,
        "use": fhir_enum(ident.use) if ident.use else None,
        "type_text": ident.type_text,
        "type_codings": (
            [_plain_coding(c) for c in ident.type_coding]
            if getattr(ident, "type_coding", None)
            else None
        ),
        "system": ident.system,
        "value": ident.value,
        "period_start": ident.period_start,
        "period_end": ident.period_end,
        "assigner": assigner,
        "assigner_display": ident.assigner_display,
    }


def _to_plain_population(pop) -> dict[str, Any]:
    sub_res = pop.subject_results_reference
    if not sub_res and pop.subject_results_type and pop.subject_results_id:
        sub_res = f"{fhir_enum(pop.subject_results_type)}/{pop.subject_results_id}"
    return {
        "id": pop.id,
        "code_text": pop.code_text,
        "code_codings": (
            [_plain_coding(c) for c in pop.code_coding]
            if getattr(pop, "code_coding", None)
            else None
        ),
        "count": pop.count,
        "subject_results": sub_res,
        "subject_results_display": pop.subject_results_display,
    }


def _to_plain_component(comp) -> dict[str, Any]:
    return {
        "id": comp.id,
        "code_text": comp.code_text,
        "code_codings": (
            [_plain_coding(c) for c in comp.code_coding]
            if getattr(comp, "code_coding", None)
            else None
        ),
        "value_text": comp.value_text,
        "value_codings": (
            [_plain_coding(c) for c in comp.value_coding]
            if getattr(comp, "value_coding", None)
            else None
        ),
    }


def _to_plain_stratum(stratum) -> dict[str, Any]:
    return {
        "id": stratum.id,
        "value_text": stratum.value_text,
        "value_codings": (
            [_plain_coding(c) for c in stratum.value_coding]
            if getattr(stratum, "value_coding", None)
            else None
        ),
        "component": (
            [_to_plain_component(c) for c in stratum.components]
            if getattr(stratum, "components", None)
            else None
        ),
        "population": (
            [_to_plain_population(p) for p in stratum.populations]
            if getattr(stratum, "populations", None)
            else None
        ),
        "measure_score_value": (
            float(stratum.measure_score_value)
            if stratum.measure_score_value is not None
            else None
        ),
        "measure_score_comparator": (
            fhir_enum(stratum.measure_score_comparator)
            if stratum.measure_score_comparator
            else None
        ),
        "measure_score_unit": stratum.measure_score_unit,
        "measure_score_system": stratum.measure_score_system,
        "measure_score_code": stratum.measure_score_code,
    }


def _to_plain_stratifier_code(code_model) -> dict[str, Any]:
    return {
        "id": code_model.id,
        "text": code_model.code_text,
        "codings": (
            [_plain_coding(c) for c in code_model.coding]
            if getattr(code_model, "coding", None)
            else None
        ),
    }


def _to_plain_stratifier(strat) -> dict[str, Any]:
    return {
        "id": strat.id,
        "code": (
            [_to_plain_stratifier_code(c) for c in strat.codes]
            if getattr(strat, "codes", None)
            else None
        ),
        "stratum": (
            [_to_plain_stratum(s) for s in strat.strata]
            if getattr(strat, "strata", None)
            else None
        ),
    }


def _to_plain_group(grp) -> dict[str, Any]:
    return {
        "id": grp.id,
        "code_text": grp.code_text,
        "code_codings": (
            [_plain_coding(c) for c in grp.code_coding]
            if getattr(grp, "code_coding", None)
            else None
        ),
        "population": (
            [_to_plain_population(p) for p in grp.populations]
            if getattr(grp, "populations", None)
            else None
        ),
        "measure_score_value": (
            float(grp.measure_score_value)
            if grp.measure_score_value is not None
            else None
        ),
        "measure_score_comparator": (
            fhir_enum(grp.measure_score_comparator)
            if grp.measure_score_comparator
            else None
        ),
        "measure_score_unit": grp.measure_score_unit,
        "measure_score_system": grp.measure_score_system,
        "measure_score_code": grp.measure_score_code,
        "stratifier": (
            [_to_plain_stratifier(s) for s in grp.stratifiers]
            if getattr(grp, "stratifiers", None)
            else None
        ),
    }


def _to_plain_evaluated_resource(er) -> dict[str, Any]:
    ref = er.evaluated_resource_reference
    if not ref and er.evaluated_resource_type and er.evaluated_resource_id:
        ref = f"{er.evaluated_resource_type}/{er.evaluated_resource_id}"
    return {
        "id": er.id,
        "reference": ref,
        "display": er.evaluated_resource_display,
    }


def to_plain_measure_report(model: MeasureReportModel) -> dict[str, Any]:
    """Convert MeasureReportModel ORM instance to a plain JSON dict."""
    subj = model.subject_reference
    if not subj and model.subject_type and model.subject_id:
        subj = f"{fhir_enum(model.subject_type)}/{model.subject_id}"

    rep = model.reporter_reference
    if not rep and model.reporter_type and model.reporter_id:
        rep = f"{fhir_enum(model.reporter_type)}/{model.reporter_id}"

    return {
        "id": model.measure_report_id,
        "status": fhir_enum(model.status),
        "type": fhir_enum(model.type),
        "measure": model.measure,
        "subject": subj,
        "subject_display": model.subject_display,
        "date": model.date,
        "reporter": rep,
        "reporter_display": model.reporter_display,
        "period_start": model.period_start,
        "period_end": model.period_end,
        "improvement_notation_text": model.improvement_notation_text,
        "improvement_notation_coding": (
            [_plain_coding(c) for c in model.improvement_notation_coding]
            if model.improvement_notation_coding
            else None
        ),
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "identifier": (
            [_to_plain_identifier(i) for i in model.identifiers]
            if model.identifiers
            else None
        ),
        "evaluated_resource": (
            [_to_plain_evaluated_resource(er) for er in model.evaluated_resources]
            if model.evaluated_resources
            else None
        ),
        "group": (
            [_to_plain_group(g) for g in model.groups]
            if model.groups
            else None
        ),
    }
