from typing import Any

from app.fhir.datatypes import (
    fhir_enum,
    fhir_instant,
)


def _fhir_meta(model) -> dict:
    meta: dict[str, Any] = {}
    if getattr(model, "updated_at", None):
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif getattr(model, "created_at", None):
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta


def _fhir_coding(c) -> dict | None:
    d: dict[str, Any] = {}
    if getattr(c, "system", None):
        d["system"] = c.system
    if getattr(c, "version", None):
        d["version"] = c.version
    if getattr(c, "code", None):
        d["code"] = c.code
    if getattr(c, "display", None):
        d["display"] = c.display
    if getattr(c, "user_selected", None) is not None:
        d["userSelected"] = c.user_selected
    return d or None


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    cc: dict[str, Any] = {}
    if codings:
        cds = [_fhir_coding(c) for c in codings]
        cds = [c for c in cds if c]
        if cds:
            cc["coding"] = cds
    if text:
        cc["text"] = text
    return cc or None


def _fhir_ref(reference, ref_type, ref_id, display) -> dict | None:
    entry: dict[str, Any] = {}
    if reference:
        entry["reference"] = reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry or None


def _fhir_period(start, end) -> dict | None:
    p: dict[str, Any] = {}
    if start:
        p["start"] = fhir_instant(start)
    if end:
        p["end"] = fhir_instant(end)
    return p or None


def _fhir_identifiers(identifiers) -> list[dict] | None:
    res = []
    for i in identifiers or []:
        d: dict[str, Any] = {}
        if i.use:
            d["use"] = fhir_enum(i.use)
        if i.type_codings or i.type_text:
            d["type"] = _fhir_codeable_concept(i.type_codings, i.type_text)
        if i.system:
            d["system"] = i.system
        if i.value:
            d["value"] = i.value
        per = _fhir_period(i.period_start, i.period_end)
        if per:
            d["period"] = per
        ass = _fhir_ref(i.assigner_reference, i.assigner_type, i.assigner_id, i.assigner_display)
        if ass:
            d["assigner"] = ass
        if d:
            res.append(d)
    return res or None


def _fhir_telecoms(telecoms) -> list[dict] | None:
    res = []
    for t in telecoms or []:
        d: dict[str, Any] = {}
        if t.system:
            d["system"] = fhir_enum(t.system)
        if t.value:
            d["value"] = t.value
        if t.use:
            d["use"] = fhir_enum(t.use)
        if t.rank is not None:
            d["rank"] = t.rank
        per = _fhir_period(t.period_start, t.period_end)
        if per:
            d["period"] = per
        if d:
            res.append(d)
    return res or None


def _fhir_contacts_by_role(contacts, role_name: str) -> list[dict] | None:
    res = []
    for c in contacts or []:
        r = c.role.value if hasattr(c.role, "value") else str(c.role)
        if r != role_name:
            continue
        d: dict[str, Any] = {}
        if c.name:
            d["name"] = c.name
        t = _fhir_telecoms(c.telecoms)
        if t:
            d["telecom"] = t
        if d:
            res.append(d)
    return res or None


def _fhir_use_contexts(use_contexts) -> list[dict] | None:
    res = []
    for uc in use_contexts or []:
        d: dict[str, Any] = {}
        code_d = _fhir_coding(uc)
        if code_d:
            d["code"] = code_d

        if uc.value_codings or uc.value_codeable_concept_text:
            d["valueCodeableConcept"] = _fhir_codeable_concept(
                uc.value_codings, uc.value_codeable_concept_text
            )
        elif uc.value_quantity_value is not None or uc.value_quantity_unit or uc.value_quantity_system or uc.value_quantity_code:
            vq: dict[str, Any] = {}
            if uc.value_quantity_value is not None:
                vq["value"] = float(uc.value_quantity_value)
            if uc.value_quantity_comparator:
                vq["comparator"] = fhir_enum(uc.value_quantity_comparator)
            if uc.value_quantity_unit:
                vq["unit"] = uc.value_quantity_unit
            if uc.value_quantity_system:
                vq["system"] = uc.value_quantity_system
            if uc.value_quantity_code:
                vq["code"] = uc.value_quantity_code
            d["valueQuantity"] = vq
        elif (
            uc.value_range_low_value is not None
            or uc.value_range_high_value is not None
        ):
            vr: dict[str, Any] = {}
            if uc.value_range_low_value is not None or uc.value_range_low_unit or uc.value_range_low_system or uc.value_range_low_code:
                low_q: dict[str, Any] = {}
                if uc.value_range_low_value is not None:
                    low_q["value"] = float(uc.value_range_low_value)
                if uc.value_range_low_unit:
                    low_q["unit"] = uc.value_range_low_unit
                if uc.value_range_low_system:
                    low_q["system"] = uc.value_range_low_system
                if uc.value_range_low_code:
                    low_q["code"] = uc.value_range_low_code
                vr["low"] = low_q
            if uc.value_range_high_value is not None or uc.value_range_high_unit or uc.value_range_high_system or uc.value_range_high_code:
                high_q: dict[str, Any] = {}
                if uc.value_range_high_value is not None:
                    high_q["value"] = float(uc.value_range_high_value)
                if uc.value_range_high_unit:
                    high_q["unit"] = uc.value_range_high_unit
                if uc.value_range_high_system:
                    high_q["system"] = uc.value_range_high_system
                if uc.value_range_high_code:
                    high_q["code"] = uc.value_range_high_code
                vr["high"] = high_q
            d["valueRange"] = vr
        elif uc.value_reference_reference or (uc.value_reference_type and uc.value_reference_id):
            ref = _fhir_ref(
                uc.value_reference_reference,
                uc.value_reference_type,
                uc.value_reference_id,
                uc.value_reference_display,
            )
            if ref:
                d["valueReference"] = ref

        if d:
            res.append(d)
    return res or None


def _fhir_concepts(items) -> list[dict] | None:
    res = []
    for item in items or []:
        cc = _fhir_codeable_concept(item.codings, item.text)
        if cc:
            res.append(cc)
    return res or None


def _fhir_related_artifacts(artifacts) -> list[dict] | None:
    res = []
    for ra in artifacts or []:
        d: dict[str, Any] = {}
        if ra.type:
            d["type"] = fhir_enum(ra.type)
        if ra.label:
            d["label"] = ra.label
        if ra.display:
            d["display"] = ra.display
        if ra.citation:
            d["citation"] = ra.citation
        if ra.url:
            d["url"] = ra.url
        if ra.document:
            d["document"] = ra.document
        if ra.resource:
            d["resource"] = ra.resource
        if d:
            res.append(d)
    return res or None


def _fhir_goals(goals) -> list[dict] | None:
    res = []
    for g in goals or []:
        d: dict[str, Any] = {}
        if g.goal_id:
            d["id"] = g.goal_id
        if g.category_codings or g.category_text:
            d["category"] = _fhir_codeable_concept(g.category_codings, g.category_text)
        if g.description_codings or g.description_text:
            d["description"] = _fhir_codeable_concept(g.description_codings, g.description_text)
        if g.priority_codings or g.priority_text:
            d["priority"] = _fhir_codeable_concept(g.priority_codings, g.priority_text)
        if g.start_codings or g.start_text:
            d["start"] = _fhir_codeable_concept(g.start_codings, g.start_text)
        if g.addresses:
            d["addresses"] = g.addresses
        if g.documentation:
            d["documentation"] = g.documentation
        if g.target:
            d["target"] = g.target
        if d:
            res.append(d)
    return res or None


def _fhir_action_single(act) -> dict:
    d: dict[str, Any] = {}
    if act.action_id_str:
        d["id"] = act.action_id_str
    if act.prefix:
        d["prefix"] = act.prefix
    if act.title:
        d["title"] = act.title
    if act.description:
        d["description"] = act.description
    if act.text_equivalent:
        d["textEquivalent"] = act.text_equivalent
    if act.priority:
        d["priority"] = fhir_enum(act.priority)
    if act.code:
        d["code"] = act.code
    if act.reason:
        d["reason"] = act.reason
    if act.documentation:
        d["documentation"] = act.documentation
    if act.goal_id:
        d["goalId"] = list(act.goal_id)

    if act.subject_codeable_concept_text:
        d["subjectCodeableConcept"] = {"text": act.subject_codeable_concept_text}
    elif act.subject_reference or (act.subject_type and act.subject_id):
        ref = _fhir_ref(
            act.subject_reference,
            act.subject_type,
            act.subject_id,
            act.subject_display,
        )
        if ref:
            d["subjectReference"] = ref

    if act.trigger:
        d["trigger"] = act.trigger
    if act.condition:
        d["condition"] = act.condition
    if act.input:
        d["input"] = act.input
    if act.output:
        d["output"] = act.output
    if act.related_action:
        d["relatedAction"] = act.related_action

    if act.timing_date_time:
        d["timingDateTime"] = fhir_instant(act.timing_date_time)
    elif act.timing_age:
        d["timingAge"] = act.timing_age
    elif act.timing_period_start or act.timing_period_end:
        per = _fhir_period(act.timing_period_start, act.timing_period_end)
        if per:
            d["timingPeriod"] = per
    elif act.timing_duration:
        d["timingDuration"] = act.timing_duration
    elif act.timing_range:
        d["timingRange"] = act.timing_range
    elif act.timing_timing:
        d["timingTiming"] = act.timing_timing

    if act.participant:
        d["participant"] = act.participant

    if act.type_codings or act.type_text:
        d["type"] = _fhir_codeable_concept(act.type_codings, act.type_text)

    if act.grouping_behavior:
        d["groupingBehavior"] = fhir_enum(act.grouping_behavior)
    if act.selection_behavior:
        d["selectionBehavior"] = fhir_enum(act.selection_behavior)
    if act.required_behavior:
        d["requiredBehavior"] = fhir_enum(act.required_behavior)
    if act.precheck_behavior:
        d["precheckBehavior"] = fhir_enum(act.precheck_behavior)
    if act.cardinality_behavior:
        d["cardinalityBehavior"] = fhir_enum(act.cardinality_behavior)

    if act.definition_canonical:
        d["definitionCanonical"] = act.definition_canonical
    elif act.definition_uri:
        d["definitionUri"] = act.definition_uri

    if act.transform:
        d["transform"] = act.transform
    if act.dynamic_value:
        d["dynamicValue"] = act.dynamic_value

    return d


def _build_fhir_actions_tree(actions) -> list[dict] | None:
    if not actions:
        return None
    by_parent: dict[int | None, list] = {}
    for act in actions:
        by_parent.setdefault(act.parent_action_id, []).append(act)

    def render(parent_id: int | None) -> list[dict]:
        result = []
        for a in by_parent.get(parent_id, []):
            item = _fhir_action_single(a)
            children = render(a.id)
            if children:
                item["action"] = children
            result.append(item)
        return result

    tree = render(None)
    return tree or None


def to_fhir_plan_definition(model) -> dict:
    """Serialize a PlanDefinitionModel into FHIR R4 JSON representation."""
    d: dict[str, Any] = {
        "resourceType": "PlanDefinition",
        "id": str(model.plan_definition_id),
    }

    meta = _fhir_meta(model)
    if meta:
        d["meta"] = meta

    if model.url:
        d["url"] = model.url

    idents = _fhir_identifiers(model.identifiers)
    if idents:
        d["identifier"] = idents

    if model.version:
        d["version"] = model.version
    if model.name:
        d["name"] = model.name
    if model.title:
        d["title"] = model.title
    if model.subtitle:
        d["subtitle"] = model.subtitle

    if model.type_codings or model.type_text:
        d["type"] = _fhir_codeable_concept(model.type_codings, model.type_text)

    d["status"] = fhir_enum(model.status)

    if model.experimental is not None:
        d["experimental"] = model.experimental

    if model.subject_codeable_concept_text or model.subject_codings:
        d["subjectCodeableConcept"] = _fhir_codeable_concept(
            model.subject_codings, model.subject_codeable_concept_text
        )
    elif model.subject_reference or (model.subject_type and model.subject_id):
        sub_ref = _fhir_ref(
            model.subject_reference,
            model.subject_type,
            model.subject_id,
            model.subject_display,
        )
        if sub_ref:
            d["subjectReference"] = sub_ref

    if model.date:
        d["date"] = fhir_instant(model.date)
    if model.publisher:
        d["publisher"] = model.publisher

    contacts = _fhir_contacts_by_role(model.contacts, "contact")
    if contacts:
        d["contact"] = contacts

    if model.description:
        d["description"] = model.description

    use_contexts = _fhir_use_contexts(model.use_contexts)
    if use_contexts:
        d["useContext"] = use_contexts

    jurisdictions = _fhir_concepts(model.jurisdictions)
    if jurisdictions:
        d["jurisdiction"] = jurisdictions

    if model.purpose:
        d["purpose"] = model.purpose
    if model.usage:
        d["usage"] = model.usage
    if model.copyright:
        d["copyright"] = model.copyright
    if model.approval_date:
        d["approvalDate"] = model.approval_date.isoformat()
    if model.last_review_date:
        d["lastReviewDate"] = model.last_review_date.isoformat()

    eff_period = _fhir_period(model.effective_period_start, model.effective_period_end)
    if eff_period:
        d["effectivePeriod"] = eff_period

    topics = _fhir_concepts(model.topics)
    if topics:
        d["topic"] = topics

    authors = _fhir_contacts_by_role(model.contacts, "author")
    if authors:
        d["author"] = authors
    editors = _fhir_contacts_by_role(model.contacts, "editor")
    if editors:
        d["editor"] = editors
    reviewers = _fhir_contacts_by_role(model.contacts, "reviewer")
    if reviewers:
        d["reviewer"] = reviewers
    endorsers = _fhir_contacts_by_role(model.contacts, "endorser")
    if endorsers:
        d["endorser"] = endorsers

    related_artifacts = _fhir_related_artifacts(model.related_artifacts)
    if related_artifacts:
        d["relatedArtifact"] = related_artifacts

    if model.library:
        d["library"] = list(model.library)

    goals = _fhir_goals(model.goals)
    if goals:
        d["goal"] = goals

    actions = _build_fhir_actions_tree(model.actions)
    if actions:
        d["action"] = actions

    if model.extension:
        d["extension"] = list(model.extension)

    return {k: v for k, v in d.items() if v is not None}
