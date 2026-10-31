from typing import Any

from app.fhir.datatypes import fhir_enum


def _plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
    }


def _plain_codings(codings) -> list[dict]:
    return [_plain_coding(c) for c in codings or []]


def _plain_single_concept(codings, text: str | None) -> dict | None:
    if not codings and not text:
        return None
    return {
        "text": text,
        "codings": _plain_codings(codings),
    }


def _plain_concepts(items) -> list[dict]:
    result = []
    for item in items or []:
        result.append(
            {
                "id": item.id,
                "text": item.text,
                "codings": _plain_codings(item.codings),
            }
        )
    return result


def _plain_identifiers(identifiers) -> list[dict]:
    result = []
    for i in identifiers or []:
        ass_str = i.assigner_reference
        if not ass_str and i.assigner_type and i.assigner_id:
            ass_str = f"{fhir_enum(i.assigner_type)}/{i.assigner_id}"
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
                "assigner": ass_str,
                "assigner_display": i.assigner_display,
            }
        )
    return result


def _plain_contacts_by_role(contacts, role_name: str) -> list[dict]:
    result = []
    for c in contacts or []:
        r = c.role.value if hasattr(c.role, "value") else str(c.role)
        if r != role_name:
            continue
        telecoms = [
            {
                "id": t.id,
                "system": fhir_enum(t.system) if t.system else None,
                "value": t.value,
                "use": fhir_enum(t.use) if t.use else None,
                "rank": t.rank,
                "period_start": t.period_start,
                "period_end": t.period_end,
            }
            for t in (c.telecoms or [])
        ]
        result.append(
            {
                "id": c.id,
                "name": c.name,
                "telecoms": telecoms,
            }
        )
    return result


def _plain_use_contexts(use_contexts) -> list[dict]:
    result = []
    for uc in use_contexts or []:
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
                "value_codeable_concept_codings": _plain_codings(uc.value_codings),
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
    for ra in artifacts or []:
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


def _plain_goals(goals) -> list[dict]:
    result = []
    for g in goals or []:
        result.append(
            {
                "id": g.id,
                "goal_id": g.goal_id,
                "category": _plain_single_concept(g.category_codings, g.category_text),
                "description": _plain_single_concept(g.description_codings, g.description_text),
                "priority": _plain_single_concept(g.priority_codings, g.priority_text),
                "start": _plain_single_concept(g.start_codings, g.start_text),
                "addresses": g.addresses,
                "documentation": g.documentation,
                "target": g.target,
            }
        )
    return result


def _plain_action_single(act) -> dict:
    sub_ref = act.subject_reference
    if not sub_ref and act.subject_type and act.subject_id:
        sub_ref = f"{fhir_enum(act.subject_type)}/{act.subject_id}"

    return {
        "id": act.id,
        "action_id_str": act.action_id_str,
        "prefix": act.prefix,
        "title": act.title,
        "description": act.description,
        "text_equivalent": act.text_equivalent,
        "priority": fhir_enum(act.priority) if act.priority else None,
        "code": act.code,
        "reason": act.reason,
        "documentation": act.documentation,
        "goal_id": list(act.goal_id) if act.goal_id else None,
        "subject_codeable_concept_text": act.subject_codeable_concept_text,
        "subject_reference": sub_ref,
        "subject_display": act.subject_display,
        "trigger": act.trigger,
        "condition": act.condition,
        "input": act.input,
        "output": act.output,
        "related_action": act.related_action,
        "timing_date_time": act.timing_date_time,
        "timing_age": act.timing_age,
        "timing_period_start": act.timing_period_start,
        "timing_period_end": act.timing_period_end,
        "timing_duration": act.timing_duration,
        "timing_range": act.timing_range,
        "timing_timing": act.timing_timing,
        "participant": act.participant,
        "type_text": act.type_text,
        "type_codings": _plain_codings(act.type_codings),
        "grouping_behavior": fhir_enum(act.grouping_behavior) if act.grouping_behavior else None,
        "selection_behavior": fhir_enum(act.selection_behavior) if act.selection_behavior else None,
        "required_behavior": fhir_enum(act.required_behavior) if act.required_behavior else None,
        "precheck_behavior": fhir_enum(act.precheck_behavior) if act.precheck_behavior else None,
        "cardinality_behavior": fhir_enum(act.cardinality_behavior) if act.cardinality_behavior else None,
        "definition_canonical": act.definition_canonical,
        "definition_uri": act.definition_uri,
        "transform": act.transform,
        "dynamic_value": act.dynamic_value,
    }


def _build_plain_actions_tree(actions) -> list[dict]:
    if not actions:
        return []
    by_parent: dict[int | None, list] = {}
    for act in actions:
        by_parent.setdefault(act.parent_action_id, []).append(act)

    def render(parent_id: int | None) -> list[dict]:
        result = []
        for a in by_parent.get(parent_id, []):
            item = _plain_action_single(a)
            children = render(a.id)
            if children:
                item["action"] = children
            result.append(item)
        return result

    return render(None)


def to_plain_plan_definition(model) -> dict:
    """Serialize a PlanDefinitionModel into plain snake_case JSON representation."""
    sub_ref = model.subject_reference
    if not sub_ref and model.subject_type and model.subject_id:
        sub_ref = f"{fhir_enum(model.subject_type)}/{model.subject_id}"

    return {
        "id": model.plan_definition_id,
        "url": model.url,
        "identifier": _plain_identifiers(model.identifiers),
        "version": model.version,
        "name": model.name,
        "title": model.title,
        "subtitle": model.subtitle,
        "type": _plain_single_concept(model.type_codings, model.type_text),
        "status": fhir_enum(model.status),
        "experimental": model.experimental,
        "subject_codeable_concept": _plain_single_concept(
            model.subject_codings, model.subject_codeable_concept_text
        ),
        "subject_reference": sub_ref,
        "subject_display": model.subject_display,
        "date": model.date,
        "publisher": model.publisher,
        "contact": _plain_contacts_by_role(model.contacts, "contact"),
        "description": model.description,
        "use_context": _plain_use_contexts(model.use_contexts),
        "jurisdiction": _plain_concepts(model.jurisdictions),
        "purpose": model.purpose,
        "usage": model.usage,
        "copyright": model.copyright,
        "approval_date": model.approval_date,
        "last_review_date": model.last_review_date,
        "effective_period_start": model.effective_period_start,
        "effective_period_end": model.effective_period_end,
        "topic": _plain_concepts(model.topics),
        "author": _plain_contacts_by_role(model.contacts, "author"),
        "editor": _plain_contacts_by_role(model.contacts, "editor"),
        "reviewer": _plain_contacts_by_role(model.contacts, "reviewer"),
        "endorser": _plain_contacts_by_role(model.contacts, "endorser"),
        "related_artifact": _plain_related_artifacts(model.related_artifacts),
        "library": list(model.library) if model.library else None,
        "goal": _plain_goals(model.goals),
        "action": _build_plain_actions_tree(model.actions),
        "extension": list(model.extension) if model.extension else None,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
