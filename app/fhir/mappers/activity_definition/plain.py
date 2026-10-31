from typing import Any

from app.fhir.datatypes import fhir_enum


def _plain_coding(c) -> dict:
    return {
        "system": getattr(c, "system", None),
        "version": getattr(c, "version", None),
        "code": getattr(c, "code", None),
        "display": getattr(c, "display", None),
        "user_selected": getattr(c, "user_selected", None),
    }


def _plain_codings(codings) -> list[dict]:
    if not codings:
        return []
    return [_plain_coding(c) for c in codings]


def _plain_single_concept(codings, text: str | None) -> dict | None:
    if not codings and not text:
        return None
    return {
        "text": text,
        "codings": _plain_codings(codings),
    }


def _plain_concept(entry) -> dict:
    return {
        "id": entry.id,
        "text": entry.text,
        "codings": _plain_codings(entry.codings),
    }


def _plain_identifiers(identifiers) -> list[dict]:
    result = []
    for i in identifiers:
        ref_str = i.assigner_reference
        if not ref_str and i.assigner_type and i.assigner_id:
            ref_str = f"{fhir_enum(i.assigner_type)}/{i.assigner_id}"
        result.append(
            {
                "id": i.id,
                "use": fhir_enum(i.use) if i.use else None,
                "system": i.system,
                "value": i.value,
                "type_text": i.type_text,
                "type_codings": _plain_codings(i.type_codings),
                "period_start": i.period_start,
                "period_end": i.period_end,
                "assigner": ref_str,
                "assigner_display": i.assigner_display,
            }
        )
    return result


def _plain_contacts(contacts, role: str) -> list[dict]:
    result = []
    for c in contacts:
        if c.role and fhir_enum(c.role) == role:
            telecoms = []
            if c.telecoms:
                for t in c.telecoms:
                    telecoms.append(
                        {
                            "id": t.id,
                            "system": fhir_enum(t.system) if t.system else None,
                            "value": t.value,
                            "use": fhir_enum(t.use) if t.use else None,
                            "rank": t.rank,
                            "period_start": t.period_start,
                            "period_end": t.period_end,
                        }
                    )
            result.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "telecom": telecoms,
                }
            )
    return result


def _plain_use_contexts(use_contexts) -> list[dict]:
    result = []
    for uc in use_contexts:
        val_ref = uc.value_reference_reference
        if not val_ref and uc.value_reference_type and uc.value_reference_id:
            val_ref = f"{fhir_enum(uc.value_reference_type)}/{uc.value_reference_id}"
        result.append(
            {
                "id": uc.id,
                "code_system": uc.system,
                "code_version": uc.version,
                "code_code": uc.code,
                "code_display": uc.display,
                "code_user_selected": uc.user_selected,
                "value_codeable_concept_text": uc.value_codeable_concept_text,
                "value_codings": _plain_codings(uc.value_codings),
                "value_quantity_value": (
                    float(uc.value_quantity_value)
                    if uc.value_quantity_value is not None
                    else None
                ),
                "value_quantity_comparator": (
                    fhir_enum(uc.value_quantity_comparator)
                    if uc.value_quantity_comparator
                    else None
                ),
                "value_quantity_unit": uc.value_quantity_unit,
                "value_quantity_system": uc.value_quantity_system,
                "value_quantity_code": uc.value_quantity_code,
                "value_range_low_value": (
                    float(uc.value_range_low_value)
                    if uc.value_range_low_value is not None
                    else None
                ),
                "value_range_low_unit": uc.value_range_low_unit,
                "value_range_low_system": uc.value_range_low_system,
                "value_range_low_code": uc.value_range_low_code,
                "value_range_high_value": (
                    float(uc.value_range_high_value)
                    if uc.value_range_high_value is not None
                    else None
                ),
                "value_range_high_unit": uc.value_range_high_unit,
                "value_range_high_system": uc.value_range_high_system,
                "value_range_high_code": uc.value_range_high_code,
                "value_reference": val_ref,
                "value_reference_display": uc.value_reference_display,
            }
        )
    return result


def _plain_related_artifacts(artifacts) -> list[dict]:
    result = []
    for ra in artifacts:
        result.append(
            {
                "id": ra.id,
                "type": fhir_enum(ra.type) if ra.type else None,
                "label": ra.label,
                "display": ra.display,
                "citation": ra.citation,
                "url": ra.url,
                "document": ra.document,
                "resource": ra.resource,
            }
        )
    return result


def _plain_participants(participants) -> list[dict]:
    result = []
    for p in participants:
        result.append(
            {
                "id": p.id,
                "type": fhir_enum(p.type) if p.type else None,
                "role_text": p.role_text,
                "role_codings": _plain_codings(p.role_codings),
            }
        )
    return result


def _plain_dosages(dosages) -> list[dict]:
    result = []
    for d in dosages:
        result.append(
            {
                "id": d.id,
                "sequence": d.sequence,
                "text": d.text,
                "patient_instruction": d.patient_instruction,
                "timing": d.timing,
                "as_needed_boolean": d.as_needed_boolean,
                "as_needed_text": d.as_needed_codeable_concept_text,
                "as_needed_codings": _plain_codings(d.as_needed_codings),
                "site_text": d.site_text,
                "site_codings": _plain_codings(d.site_codings),
                "route_text": d.route_text,
                "route_codings": _plain_codings(d.route_codings),
                "method_text": d.method_text,
                "method_codings": _plain_codings(d.method_codings),
                "dose_and_rate": d.dose_and_rate,
                "max_dose_per_period": d.max_dose_per_period,
                "max_dose_per_administration_value": (
                    float(d.max_dose_per_administration_value)
                    if d.max_dose_per_administration_value is not None
                    else None
                ),
                "max_dose_per_administration_unit": d.max_dose_per_administration_unit,
                "max_dose_per_administration_system": d.max_dose_per_administration_system,
                "max_dose_per_administration_code": d.max_dose_per_administration_code,
                "max_dose_per_lifetime_value": (
                    float(d.max_dose_per_lifetime_value)
                    if d.max_dose_per_lifetime_value is not None
                    else None
                ),
                "max_dose_per_lifetime_unit": d.max_dose_per_lifetime_unit,
                "max_dose_per_lifetime_system": d.max_dose_per_lifetime_system,
                "max_dose_per_lifetime_code": d.max_dose_per_lifetime_code,
            }
        )
    return result


def _plain_dynamic_values(dynamic_values) -> list[dict]:
    result = []
    for dv in dynamic_values:
        result.append(
            {
                "id": dv.id,
                "path": dv.path,
                "expression_description": dv.expression_description,
                "expression_name": dv.expression_name,
                "expression_language": dv.expression_language,
                "expression_expression": dv.expression_expression,
                "expression_reference": dv.expression_reference,
            }
        )
    return result


def _plain_requirements(requirements) -> list[dict]:
    result = []
    for r in requirements:
        ref_str = r.reference_reference
        if not ref_str and r.reference_type and r.reference_id:
            ref_str = f"{fhir_enum(r.reference_type)}/{r.reference_id}"
        result.append(
            {
                "id": r.id,
                "reference": ref_str,
                "display": r.reference_display,
            }
        )
    return result


def to_plain_activity_definition(model) -> dict[str, Any]:
    """Transform an ActivityDefinitionModel into a plain snake_case dict."""
    loc_ref = model.location_reference
    if not loc_ref and model.location_type and model.location_id:
        loc_ref = f"{fhir_enum(model.location_type)}/{model.location_id}"

    prod_ref = model.product_reference
    if not prod_ref and model.product_type and model.product_id:
        prod_ref = f"{fhir_enum(model.product_type)}/{model.product_id}"

    subj_ref = model.subject_reference
    if not subj_ref and model.subject_type and model.subject_id:
        subj_ref = f"{fhir_enum(model.subject_type)}/{model.subject_id}"

    return {
        "id": model.activity_definition_id,
        "tenant_id": model.tenant_id,
        "url": model.url,
        "identifier": _plain_identifiers(model.identifiers) if model.identifiers else [],
        "version": model.version,
        "name": model.name,
        "title": model.title,
        "subtitle": model.subtitle,
        "status": fhir_enum(model.status) if model.status else None,
        "experimental": model.experimental,
        "date": model.date,
        "publisher": model.publisher,
        "contact": _plain_contacts(model.contacts, "contact") if model.contacts else [],
        "description": model.description,
        "use_context": _plain_use_contexts(model.use_contexts) if model.use_contexts else [],
        "jurisdiction": [_plain_concept(j) for j in model.jurisdictions] if model.jurisdictions else [],
        "purpose": model.purpose,
        "usage": model.usage,
        "copyright": model.copyright,
        "approval_date": model.approval_date,
        "last_review_date": model.last_review_date,
        "effective_period_start": model.effective_period_start,
        "effective_period_end": model.effective_period_end,
        "topic": [_plain_concept(t) for t in model.topics] if model.topics else [],
        "author": _plain_contacts(model.contacts, "author") if model.contacts else [],
        "editor": _plain_contacts(model.contacts, "editor") if model.contacts else [],
        "reviewer": _plain_contacts(model.contacts, "reviewer") if model.contacts else [],
        "endorser": _plain_contacts(model.contacts, "endorser") if model.contacts else [],
        "related_artifact": (
            _plain_related_artifacts(model.related_artifacts)
            if model.related_artifacts
            else []
        ),
        "library": model.library or [],
        "kind": fhir_enum(model.kind) if model.kind else None,
        "profile": model.profile,
        "code": _plain_single_concept(model.code_codings, model.code_text),
        "intent": fhir_enum(model.intent) if model.intent else None,
        "priority": fhir_enum(model.priority) if model.priority else None,
        "do_not_perform": model.do_not_perform,
        "timing_timing": model.timing_timing,
        "timing_date_time": model.timing_date_time,
        "timing_age_value": (
            float(model.timing_age_value) if model.timing_age_value is not None else None
        ),
        "timing_age_unit": model.timing_age_unit,
        "timing_age_system": model.timing_age_system,
        "timing_age_code": model.timing_age_code,
        "timing_period_start": model.timing_period_start,
        "timing_period_end": model.timing_period_end,
        "timing_range_low_value": (
            float(model.timing_range_low_value)
            if model.timing_range_low_value is not None
            else None
        ),
        "timing_range_low_unit": model.timing_range_low_unit,
        "timing_range_high_value": (
            float(model.timing_range_high_value)
            if model.timing_range_high_value is not None
            else None
        ),
        "timing_range_high_unit": model.timing_range_high_unit,
        "timing_duration_value": (
            float(model.timing_duration_value)
            if model.timing_duration_value is not None
            else None
        ),
        "timing_duration_unit": model.timing_duration_unit,
        "timing_duration_system": model.timing_duration_system,
        "timing_duration_code": model.timing_duration_code,
        "location": loc_ref,
        "location_display": model.location_display,
        "participant": _plain_participants(model.participants) if model.participants else [],
        "product_codeable_concept": _plain_single_concept(
            model.product_codings, model.product_codeable_concept_text
        ),
        "product_reference": prod_ref,
        "product_display": model.product_display,
        "quantity_value": (
            float(model.quantity_value) if model.quantity_value is not None else None
        ),
        "quantity_comparator": (
            fhir_enum(model.quantity_comparator) if model.quantity_comparator else None
        ),
        "quantity_unit": model.quantity_unit,
        "quantity_system": model.quantity_system,
        "quantity_code": model.quantity_code,
        "dosage": _plain_dosages(model.dosages) if model.dosages else [],
        "body_site": [_plain_concept(b) for b in model.body_sites] if model.body_sites else [],
        "specimen_requirement": (
            _plain_requirements(model.specimen_requirements)
            if model.specimen_requirements
            else []
        ),
        "observation_requirement": (
            _plain_requirements(model.observation_requirements)
            if model.observation_requirements
            else []
        ),
        "observation_result_requirement": (
            _plain_requirements(model.observation_result_requirements)
            if model.observation_result_requirements
            else []
        ),
        "transform": model.transform,
        "dynamic_value": (
            _plain_dynamic_values(model.dynamic_values)
            if model.dynamic_values
            else []
        ),
        "subject_codeable_concept": _plain_single_concept(
            model.subject_codings, model.subject_codeable_concept_text
        ),
        "subject_reference": subj_ref,
        "subject_display": model.subject_display,
        "extension": model.extension or [],
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
