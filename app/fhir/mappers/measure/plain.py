from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.measure import MeasureModel


def _plain_coding_list(codings) -> list[dict] | None:
    result = []
    for c in codings or []:
        result.append(
            {
                "id": c.id,
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
        )
    return result or None


def plain_measure_single_concept(codings, text: str | None) -> dict | None:
    coding_list = _plain_coding_list(codings)
    if not coding_list and text is None:
        return None
    return {
        "text": text,
        "codings": coding_list,
    }


def plain_measure_concept(item) -> dict:
    return {
        "id": item.id,
        "text": item.text,
        "codings": _plain_coding_list(item.codings),
    }


def plain_measure_identifier(i) -> dict:
    assigner_ref = i.assigner_reference
    if not assigner_ref and i.assigner_type and i.assigner_id:
        assigner_ref = f"{fhir_enum(i.assigner_type)}/{i.assigner_id}"
    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type_text": i.type_text,
        "type_codings": _plain_coding_list(i.type_codings),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": assigner_ref,
        "assigner_display": i.assigner_display,
    }


def plain_measure_telecom(t) -> dict:
    return {
        "id": t.id,
        "system": fhir_enum(t.system) if t.system else None,
        "value": t.value,
        "use": fhir_enum(t.use) if t.use else None,
        "rank": t.rank,
        "period_start": t.period_start,
        "period_end": t.period_end,
    }


def plain_measure_contact(c) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "telecoms": [plain_measure_telecom(t) for t in c.telecoms] if c.telecoms else None,
    }


def _contacts_by_role(contacts, role_name: str) -> list[dict] | None:
    res = []
    for c in contacts or []:
        r = c.role.value if hasattr(c.role, "value") else str(c.role)
        if r == role_name:
            res.append(plain_measure_contact(c))
    return res or None


def plain_measure_use_context(uc) -> dict:
    val_ref = uc.value_reference_reference
    if not val_ref and uc.value_reference_type and uc.value_reference_id:
        val_ref = f"{fhir_enum(uc.value_reference_type)}/{uc.value_reference_id}"
    return {
        "id": uc.id,
        "code_system": uc.system,
        "code_version": uc.version,
        "code_code": uc.code,
        "code_display": uc.display,
        "code_user_selected": uc.user_selected,
        "value_codeable_concept_text": uc.value_codeable_concept_text,
        "value_codings": _plain_coding_list(uc.value_codings),
        "value_quantity_value": float(uc.value_quantity_value) if uc.value_quantity_value is not None else None,
        "value_quantity_comparator": fhir_enum(uc.value_quantity_comparator) if uc.value_quantity_comparator else None,
        "value_quantity_unit": uc.value_quantity_unit,
        "value_quantity_system": uc.value_quantity_system,
        "value_quantity_code": uc.value_quantity_code,
        "value_range_low_value": float(uc.value_range_low_value) if uc.value_range_low_value is not None else None,
        "value_range_low_unit": uc.value_range_low_unit,
        "value_range_low_system": uc.value_range_low_system,
        "value_range_low_code": uc.value_range_low_code,
        "value_range_high_value": float(uc.value_range_high_value) if uc.value_range_high_value is not None else None,
        "value_range_high_unit": uc.value_range_high_unit,
        "value_range_high_system": uc.value_range_high_system,
        "value_range_high_code": uc.value_range_high_code,
        "value_reference": val_ref,
        "value_reference_display": uc.value_reference_display,
    }


def plain_measure_related_artifact(ra) -> dict:
    return {
        "id": ra.id,
        "type": fhir_enum(ra.type) if ra.type else None,
        "label": ra.label,
        "display": ra.display,
        "citation": ra.citation,
        "url": ra.url,
        "document": ra.document,
        "resource": ra.resource,
    }


def plain_measure_expression(desc, name, lang, expr, ref) -> dict | None:
    if any(x is not None for x in (desc, name, lang, expr, ref)):
        return {
            "description": desc,
            "name": name,
            "language": lang,
            "expression": expr,
            "reference": ref,
        }
    return None


def plain_measure_group(g) -> dict:
    pops = []
    for p in g.populations or []:
        pops.append(
            {
                "id": p.id,
                "code": plain_measure_single_concept(p.code_codings, p.code_text),
                "description": p.description,
                "criteria": plain_measure_expression(
                    p.criteria_description,
                    p.criteria_name,
                    p.criteria_language,
                    p.criteria_expression,
                    p.criteria_reference,
                ),
            }
        )

    strats = []
    for s in g.stratifiers or []:
        comps = []
        for c in s.components or []:
            comps.append(
                {
                    "id": c.id,
                    "code": plain_measure_single_concept(c.code_codings, c.code_text),
                    "description": c.description,
                    "criteria": plain_measure_expression(
                        c.criteria_description,
                        c.criteria_name,
                        c.criteria_language,
                        c.criteria_expression,
                        c.criteria_reference,
                    ),
                }
            )
        strats.append(
            {
                "id": s.id,
                "code": plain_measure_single_concept(s.code_codings, s.code_text),
                "description": s.description,
                "criteria": plain_measure_expression(
                    s.criteria_description,
                    s.criteria_name,
                    s.criteria_language,
                    s.criteria_expression,
                    s.criteria_reference,
                ),
                "component": comps or None,
            }
        )

    return {
        "id": g.id,
        "code": plain_measure_single_concept(g.code_codings, g.code_text),
        "description": g.description,
        "population": pops or None,
        "stratifier": strats or None,
    }


def plain_measure_supplemental_data(sd) -> dict:
    usages = [plain_measure_concept(u) for u in (sd.usages or [])]
    return {
        "id": sd.id,
        "code": plain_measure_single_concept(sd.code_codings, sd.code_text),
        "usage": usages or None,
        "description": sd.description,
        "criteria": plain_measure_expression(
            sd.criteria_description,
            sd.criteria_name,
            sd.criteria_language,
            sd.criteria_expression,
            sd.criteria_reference,
        ),
    }


def to_plain_measure(model: MeasureModel) -> dict[str, Any]:
    """Convert MeasureModel ORM instance to PlainMeasureResponse dict."""
    subj_ref = model.subject_reference
    if not subj_ref and model.subject_type and model.subject_id:
        subj_ref = f"{fhir_enum(model.subject_type)}/{model.subject_id}"

    return {
        "id": model.measure_id,
        "url": model.url,
        "identifier": [plain_measure_identifier(i) for i in (model.identifiers or [])] or None,
        "version": model.version,
        "name": model.name,
        "title": model.title,
        "subtitle": model.subtitle,
        "status": fhir_enum(model.status),
        "experimental": model.experimental,
        "subject_codeable_concept": plain_measure_single_concept(
            model.subject_codings, model.subject_codeable_concept_text
        ),
        "subject_reference": subj_ref,
        "subject_display": model.subject_display,
        "date": model.date,
        "publisher": model.publisher,
        "contact": _contacts_by_role(model.contacts, "contact"),
        "description": model.description,
        "use_context": [plain_measure_use_context(uc) for uc in (model.use_contexts or [])] or None,
        "jurisdiction": [plain_measure_concept(j) for j in (model.jurisdictions or [])] or None,
        "purpose": model.purpose,
        "usage": model.usage,
        "copyright": model.copyright,
        "approval_date": model.approval_date,
        "last_review_date": model.last_review_date,
        "effective_period_start": model.effective_period_start,
        "effective_period_end": model.effective_period_end,
        "topic": [plain_measure_concept(t) for t in (model.topics or [])] or None,
        "author": _contacts_by_role(model.contacts, "author"),
        "editor": _contacts_by_role(model.contacts, "editor"),
        "reviewer": _contacts_by_role(model.contacts, "reviewer"),
        "endorser": _contacts_by_role(model.contacts, "endorser"),
        "related_artifact": [
            plain_measure_related_artifact(ra) for ra in (model.related_artifacts or [])
        ]
        or None,
        "library": list(model.library) if model.library else None,
        "disclaimer": model.disclaimer,
        "scoring": plain_measure_single_concept(
            model.scoring_codings, model.scoring_text
        ),
        "composite_scoring": plain_measure_single_concept(
            model.composite_scoring_codings, model.composite_scoring_text
        ),
        "type": [plain_measure_concept(t) for t in (model.types or [])] or None,
        "risk_adjustment": model.risk_adjustment,
        "rate_aggregation": model.rate_aggregation,
        "rationale": model.rationale,
        "clinical_recommendation_statement": model.clinical_recommendation_statement,
        "improvement_notation": plain_measure_single_concept(
            model.improvement_notation_codings, model.improvement_notation_text
        ),
        "definition": list(model.definition) if model.definition else None,
        "guidance": model.guidance,
        "group": [plain_measure_group(g) for g in (model.groups or [])] or None,
        "supplemental_data": [
            plain_measure_supplemental_data(sd) for sd in (model.supplemental_data or [])
        ]
        or None,
        "extension": list(model.extension) if model.extension else None,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
