"""Payload -> FHIR JSON conversion for PlanDefinition.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(PlanDefinitionCreateSchema / PlanDefinitionPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.plan_definition.input import (
        PlanDefinitionActionInput,
        PlanDefinitionCodeableConceptInput,
        PlanDefinitionContactInput,
        PlanDefinitionCreateSchema,
        PlanDefinitionGoalInput,
        PlanDefinitionIdentifierInput,
        PlanDefinitionPatchSchema,
        PlanDefinitionRelatedArtifactInput,
        PlanDefinitionUseContextInput,
    )

_SUBJECT_FIELDS = {"subject_codeable_concept", "subject_reference", "subject_display"}
_EFFECTIVE_PERIOD_FIELDS = {"effective_period_start", "effective_period_end"}


def _coding_from_payload(c) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected") or c.get("userSelected"),
            }.items()
            if v is not None
        }
    return {
        k: v
        for k, v in {
            "system": getattr(c, "system", None),
            "version": getattr(c, "version", None),
            "code": getattr(c, "code", None),
            "display": getattr(c, "display", None),
            "userSelected": getattr(c, "user_selected", None),
        }.items()
        if v is not None
    }


def _codeable_concept_from_payload(
    concept: PlanDefinitionCodeableConceptInput | dict | None,
) -> dict | None:
    if not concept:
        return None
    if isinstance(concept, dict):
        d: dict[str, Any] = {}
        if concept.get("coding"):
            cds = [_coding_from_payload(c) for c in concept["coding"]]
            cds = [c for c in cds if c]
            if cds:
                d["coding"] = cds
        if concept.get("text"):
            d["text"] = concept["text"]
        return d or None

    d = {}
    if getattr(concept, "coding", None):
        cds = [_coding_from_payload(c) for c in concept.coding]
        cds = [c for c in cds if c]
        if cds:
            d["coding"] = cds
    if getattr(concept, "text", None):
        d["text"] = concept.text
    return d or None


def _identifier_from_payload(
    i: PlanDefinitionIdentifierInput | dict,
) -> dict:
    if isinstance(i, dict):
        d: dict[str, Any] = {}
        if i.get("use"):
            d["use"] = fhir_enum(i["use"])
        type_text = i.get("type_text")
        type_coding = i.get("type_coding")
        if type_coding or type_text:
            d["type"] = {
                k: v
                for k, v in {
                    "text": type_text,
                    "coding": [_coding_from_payload(c) for c in type_coding]
                    if type_coding
                    else None,
                }.items()
                if v is not None
            }
        if i.get("system"):
            d["system"] = i["system"]
        if i.get("value"):
            d["value"] = i["value"]
        p_start = i.get("period_start")
        p_end = i.get("period_end")
        if p_start or p_end:
            per: dict[str, Any] = {}
            if p_start:
                per["start"] = fhir_instant(p_start)
            if p_end:
                per["end"] = fhir_instant(p_end)
            d["period"] = per
        assigner = i.get("assigner")
        assigner_disp = i.get("assigner_display")
        if assigner or assigner_disp:
            ass: dict[str, Any] = {}
            if assigner:
                ass["reference"] = assigner
            if assigner_disp:
                ass["display"] = assigner_disp
            d["assigner"] = ass
        return d

    d = {}
    if i.use:
        d["use"] = fhir_enum(i.use)
    if i.type_text or i.type_coding:
        tc = None
        if i.type_coding:
            tc = [_coding_from_payload(c) for c in i.type_coding]
            tc = [c for c in tc if c]
        type_dict = {}
        if tc:
            type_dict["coding"] = tc
        if i.type_text:
            type_dict["text"] = i.type_text
        if type_dict:
            d["type"] = type_dict
    if i.system:
        d["system"] = i.system
    if i.value:
        d["value"] = i.value
    if i.period_start or i.period_end:
        per = {}
        if i.period_start:
            per["start"] = fhir_instant(i.period_start)
        if i.period_end:
            per["end"] = fhir_instant(i.period_end)
        d["period"] = per
    if i.assigner or i.assigner_display:
        ass = {}
        if i.assigner:
            ass["reference"] = i.assigner
        if i.assigner_display:
            ass["display"] = i.assigner_display
        d["assigner"] = ass
    return d


def _contact_from_payload(c: PlanDefinitionContactInput | dict) -> dict:
    if isinstance(c, dict):
        d: dict[str, Any] = {}
        if c.get("name"):
            d["name"] = c["name"]
        if c.get("telecom"):
            t_list = []
            for t in c["telecom"]:
                td = {}
                if t.get("system"):
                    td["system"] = fhir_enum(t["system"])
                if t.get("value"):
                    td["value"] = t["value"]
                if t.get("use"):
                    td["use"] = fhir_enum(t["use"])
                if t.get("rank") is not None:
                    td["rank"] = t["rank"]
                t_start = t.get("period_start")
                t_end = t.get("period_end")
                if t_start or t_end:
                    tp = {}
                    if t_start:
                        tp["start"] = fhir_instant(t_start)
                    if t_end:
                        tp["end"] = fhir_instant(t_end)
                    td["period"] = tp
                if td:
                    t_list.append(td)
            if t_list:
                d["telecom"] = t_list
        return d

    d = {}
    if c.name:
        d["name"] = c.name
    if c.telecom:
        t_list = []
        for t in c.telecom:
            td = {}
            if t.system:
                td["system"] = fhir_enum(t.system)
            if t.value:
                td["value"] = t.value
            if t.use:
                td["use"] = fhir_enum(t.use)
            if t.rank is not None:
                td["rank"] = t.rank
            if t.period_start or t.period_end:
                tp = {}
                if t.period_start:
                    tp["start"] = fhir_instant(t.period_start)
                if t.period_end:
                    tp["end"] = fhir_instant(t.period_end)
                td["period"] = tp
            if td:
                t_list.append(td)
        if t_list:
            d["telecom"] = t_list
    return d


def _use_context_from_payload(uc: PlanDefinitionUseContextInput | dict) -> dict:
    if isinstance(uc, dict):
        d: dict[str, Any] = {}
        c_dict = {}
        if uc.get("code_system"):
            c_dict["system"] = uc["code_system"]
        if uc.get("code_version"):
            c_dict["version"] = uc["code_version"]
        if uc.get("code_code"):
            c_dict["code"] = uc["code_code"]
        if uc.get("code_display"):
            c_dict["display"] = uc["code_display"]
        if uc.get("code_user_selected") is not None:
            c_dict["userSelected"] = uc["code_user_selected"]
        if c_dict:
            d["code"] = c_dict

        vcc_coding = uc.get("value_codeable_concept_coding")
        vcc_text = uc.get("value_codeable_concept_text")
        if vcc_coding or vcc_text:
            vcc: dict[str, Any] = {}
            if vcc_coding:
                vcc["coding"] = [_coding_from_payload(c) for c in vcc_coding]
            if vcc_text:
                vcc["text"] = vcc_text
            d["valueCodeableConcept"] = vcc
        elif (
            uc.get("value_quantity_value") is not None
            or uc.get("value_quantity_unit")
            or uc.get("value_quantity_system")
            or uc.get("value_quantity_code")
        ):
            vq: dict[str, Any] = {}
            if uc.get("value_quantity_value") is not None:
                vq["value"] = float(uc["value_quantity_value"])
            if uc.get("value_quantity_comparator"):
                vq["comparator"] = fhir_enum(uc["value_quantity_comparator"])
            if uc.get("value_quantity_unit"):
                vq["unit"] = uc["value_quantity_unit"]
            if uc.get("value_quantity_system"):
                vq["system"] = uc["value_quantity_system"]
            if uc.get("value_quantity_code"):
                vq["code"] = uc["value_quantity_code"]
            d["valueQuantity"] = vq
        elif (
            uc.get("value_range_low_value") is not None
            or uc.get("value_range_high_value") is not None
        ):
            vr: dict[str, Any] = {}
            if uc.get("value_range_low_value") is not None or uc.get("value_range_low_unit"):
                vr["low"] = {
                    "value": float(uc["value_range_low_value"]) if uc.get("value_range_low_value") is not None else None,
                    "unit": uc.get("value_range_low_unit"),
                    "system": uc.get("value_range_low_system"),
                    "code": uc.get("value_range_low_code"),
                }
            if uc.get("value_range_high_value") is not None or uc.get("value_range_high_unit"):
                vr["high"] = {
                    "value": float(uc["value_range_high_value"]) if uc.get("value_range_high_value") is not None else None,
                    "unit": uc.get("value_range_high_unit"),
                    "system": uc.get("value_range_high_system"),
                    "code": uc.get("value_range_high_code"),
                }
            d["valueRange"] = vr
        elif uc.get("value_reference"):
            vref: dict[str, Any] = {"reference": uc["value_reference"]}
            if uc.get("value_reference_display"):
                vref["display"] = uc["value_reference_display"]
            d["valueReference"] = vref
        return d

    d = {}
    c_dict = {}
    if uc.code_system:
        c_dict["system"] = uc.code_system
    if uc.code_version:
        c_dict["version"] = uc.code_version
    if uc.code_code:
        c_dict["code"] = uc.code_code
    if uc.code_display:
        c_dict["display"] = uc.code_display
    if uc.code_user_selected is not None:
        c_dict["userSelected"] = uc.code_user_selected
    if c_dict:
        d["code"] = c_dict

    if uc.value_codeable_concept_coding or uc.value_codeable_concept_text:
        vcc = {}
        if uc.value_codeable_concept_coding:
            vcc["coding"] = [_coding_from_payload(c) for c in uc.value_codeable_concept_coding]
        if uc.value_codeable_concept_text:
            vcc["text"] = uc.value_codeable_concept_text
        d["valueCodeableConcept"] = vcc
    elif (
        uc.value_quantity_value is not None
        or uc.value_quantity_unit
        or uc.value_quantity_system
        or uc.value_quantity_code
    ):
        vq = {}
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
        vr = {}
        if uc.value_range_low_value is not None or uc.value_range_low_unit:
            low_d = {}
            if uc.value_range_low_value is not None:
                low_d["value"] = float(uc.value_range_low_value)
            if uc.value_range_low_unit:
                low_d["unit"] = uc.value_range_low_unit
            if uc.value_range_low_system:
                low_d["system"] = uc.value_range_low_system
            if uc.value_range_low_code:
                low_d["code"] = uc.value_range_low_code
            vr["low"] = low_d
        if uc.value_range_high_value is not None or uc.value_range_high_unit:
            high_d = {}
            if uc.value_range_high_value is not None:
                high_d["value"] = float(uc.value_range_high_value)
            if uc.value_range_high_unit:
                high_d["unit"] = uc.value_range_high_unit
            if uc.value_range_high_system:
                high_d["system"] = uc.value_range_high_system
            if uc.value_range_high_code:
                high_d["code"] = uc.value_range_high_code
            vr["high"] = high_d
        d["valueRange"] = vr
    elif uc.value_reference:
        vref = {"reference": uc.value_reference}
        if uc.value_reference_display:
            vref["display"] = uc.value_reference_display
        d["valueReference"] = vref
    return d


def _related_artifact_from_payload(ra: PlanDefinitionRelatedArtifactInput | dict) -> dict:
    if isinstance(ra, dict):
        d: dict[str, Any] = {"type": fhir_enum(ra.get("type"))}
        if ra.get("label"):
            d["label"] = ra["label"]
        if ra.get("display"):
            d["display"] = ra["display"]
        if ra.get("citation"):
            d["citation"] = ra["citation"]
        if ra.get("url"):
            d["url"] = ra["url"]
        if ra.get("document"):
            d["document"] = ra["document"]
        if ra.get("resource"):
            d["resource"] = ra["resource"]
        return d

    d = {"type": fhir_enum(ra.type)}
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
    return d


def _goal_from_payload(g: PlanDefinitionGoalInput | dict) -> dict:
    if isinstance(g, dict):
        d: dict[str, Any] = {}
        gid = g.get("id") or g.get("goal_id")
        if gid:
            d["id"] = gid
        if g.get("category"):
            c = _codeable_concept_from_payload(g["category"])
            if c:
                d["category"] = c
        if g.get("description"):
            desc = _codeable_concept_from_payload(g["description"])
            if desc:
                d["description"] = desc
        if g.get("priority"):
            p = _codeable_concept_from_payload(g["priority"])
            if p:
                d["priority"] = p
        if g.get("start"):
            s = _codeable_concept_from_payload(g["start"])
            if s:
                d["start"] = s
        if g.get("addresses"):
            d["addresses"] = [
                _codeable_concept_from_payload(a) for a in g["addresses"] if a
            ]
        if g.get("documentation"):
            d["documentation"] = g["documentation"]
        if g.get("target"):
            d["target"] = g["target"]
        return d

    d = {}
    gid = g.id or g.goal_id
    if gid:
        d["id"] = gid
    if g.category:
        c = _codeable_concept_from_payload(g.category)
        if c:
            d["category"] = c
    if g.description:
        desc = _codeable_concept_from_payload(g.description)
        if desc:
            d["description"] = desc
    if g.priority:
        p = _codeable_concept_from_payload(g.priority)
        if p:
            d["priority"] = p
    if g.start:
        s = _codeable_concept_from_payload(g.start)
        if s:
            d["start"] = s
    if g.addresses:
        d["addresses"] = [
            _codeable_concept_from_payload(a) for a in g.addresses if a
        ]
    if g.documentation:
        d["documentation"] = g.documentation
    if g.target:
        d["target"] = g.target
    return d


def _action_from_payload(act: PlanDefinitionActionInput | dict) -> dict:
    if isinstance(act, dict):
        d: dict[str, Any] = {}
        aid = act.get("id") or act.get("action_id_str")
        if aid:
            d["id"] = aid
        if act.get("prefix"):
            d["prefix"] = act["prefix"]
        if act.get("title"):
            d["title"] = act["title"]
        if act.get("description"):
            d["description"] = act["description"]
        if act.get("text_equivalent"):
            d["textEquivalent"] = act["text_equivalent"]
        if act.get("priority"):
            d["priority"] = fhir_enum(act["priority"])
        if act.get("code"):
            d["code"] = act["code"]
        if act.get("reason"):
            d["reason"] = act["reason"]
        if act.get("documentation"):
            d["documentation"] = act["documentation"]
        if act.get("goal_id"):
            d["goalId"] = list(act["goal_id"])
        if act.get("subject_codeable_concept"):
            scc = _codeable_concept_from_payload(act["subject_codeable_concept"])
            if scc:
                d["subjectCodeableConcept"] = scc
        elif act.get("subject_reference"):
            sref = {"reference": act["subject_reference"]}
            if act.get("subject_display"):
                sref["display"] = act["subject_display"]
            d["subjectReference"] = sref
        if act.get("trigger"):
            d["trigger"] = act["trigger"]
        if act.get("condition"):
            d["condition"] = act["condition"]
        if act.get("input"):
            d["input"] = act["input"]
        if act.get("output"):
            d["output"] = act["output"]
        if act.get("related_action"):
            d["relatedAction"] = act["related_action"]
        if act.get("timing_date_time"):
            d["timingDateTime"] = fhir_instant(act["timing_date_time"])
        elif act.get("timing_age"):
            d["timingAge"] = act["timing_age"]
        elif act.get("timing_period_start") or act.get("timing_period_end"):
            per = {}
            if act.get("timing_period_start"):
                per["start"] = fhir_instant(act["timing_period_start"])
            if act.get("timing_period_end"):
                per["end"] = fhir_instant(act["timing_period_end"])
            d["timingPeriod"] = per
        elif act.get("timing_duration"):
            d["timingDuration"] = act["timing_duration"]
        elif act.get("timing_range"):
            d["timingRange"] = act["timing_range"]
        elif act.get("timing_timing"):
            d["timingTiming"] = act["timing_timing"]
        if act.get("participant"):
            d["participant"] = act["participant"]
        if act.get("type"):
            t = _codeable_concept_from_payload(act["type"])
            if t:
                d["type"] = t
        if act.get("grouping_behavior"):
            d["groupingBehavior"] = fhir_enum(act["grouping_behavior"])
        if act.get("selection_behavior"):
            d["selectionBehavior"] = fhir_enum(act["selection_behavior"])
        if act.get("required_behavior"):
            d["requiredBehavior"] = fhir_enum(act["required_behavior"])
        if act.get("precheck_behavior"):
            d["precheckBehavior"] = fhir_enum(act["precheck_behavior"])
        if act.get("cardinality_behavior"):
            d["cardinalityBehavior"] = fhir_enum(act["cardinality_behavior"])
        if act.get("definition_canonical"):
            d["definitionCanonical"] = act["definition_canonical"]
        elif act.get("definition_uri"):
            d["definitionUri"] = act["definition_uri"]
        if act.get("transform"):
            d["transform"] = act["transform"]
        if act.get("dynamic_value"):
            d["dynamicValue"] = act["dynamic_value"]
        if act.get("action"):
            d["action"] = [_action_from_payload(sub) for sub in act["action"]]
        return d

    d = {}
    aid = act.id or act.action_id_str
    if aid:
        d["id"] = aid
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
    if act.subject_codeable_concept:
        scc = _codeable_concept_from_payload(act.subject_codeable_concept)
        if scc:
            d["subjectCodeableConcept"] = scc
    elif act.subject_reference:
        sref = {"reference": act.subject_reference}
        if act.subject_display:
            sref["display"] = act.subject_display
        d["subjectReference"] = sref
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
        per = {}
        if act.timing_period_start:
            per["start"] = fhir_instant(act.timing_period_start)
        if act.timing_period_end:
            per["end"] = fhir_instant(act.timing_period_end)
        d["timingPeriod"] = per
    elif act.timing_duration:
        d["timingDuration"] = act.timing_duration
    elif act.timing_range:
        d["timingRange"] = act.timing_range
    elif act.timing_timing:
        d["timingTiming"] = act.timing_timing
    if act.participant:
        d["participant"] = act.participant
    if act.type:
        t = _codeable_concept_from_payload(act.type)
        if t:
            d["type"] = t
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
    if act.action:
        d["action"] = [_action_from_payload(sub) for sub in act.action]
    return d


def payload_to_fhir_plan_definition(payload: PlanDefinitionCreateSchema) -> dict:
    """Convert a PlanDefinitionCreateSchema to a FHIR R4 JSON dict."""
    d: dict[str, Any] = {
        "resourceType": "PlanDefinition",
        "status": fhir_enum(payload.status),
    }

    if payload.url:
        d["url"] = payload.url
    if payload.identifier:
        d["identifier"] = [_identifier_from_payload(i) for i in payload.identifier]
    if payload.version:
        d["version"] = payload.version
    if payload.name:
        d["name"] = payload.name
    if payload.title:
        d["title"] = payload.title
    if payload.subtitle:
        d["subtitle"] = payload.subtitle
    if payload.type:
        t = _codeable_concept_from_payload(payload.type)
        if t:
            d["type"] = t
    if payload.experimental is not None:
        d["experimental"] = payload.experimental

    if payload.subject_codeable_concept:
        scc = _codeable_concept_from_payload(payload.subject_codeable_concept)
        if scc:
            d["subjectCodeableConcept"] = scc
    elif payload.subject_reference:
        sref = {"reference": payload.subject_reference}
        if payload.subject_display:
            sref["display"] = payload.subject_display
        d["subjectReference"] = sref

    if payload.date:
        d["date"] = fhir_instant(payload.date)
    if payload.publisher:
        d["publisher"] = payload.publisher
    if payload.contact:
        d["contact"] = [_contact_from_payload(c) for c in payload.contact]
    if payload.description:
        d["description"] = payload.description
    if payload.use_context:
        d["useContext"] = [_use_context_from_payload(uc) for uc in payload.use_context]
    if payload.jurisdiction:
        d["jurisdiction"] = [
            _codeable_concept_from_payload(j) for j in payload.jurisdiction if j
        ]
    if payload.purpose:
        d["purpose"] = payload.purpose
    if payload.usage:
        d["usage"] = payload.usage
    if payload.copyright:
        d["copyright"] = payload.copyright
    if payload.approval_date:
        d["approvalDate"] = payload.approval_date.isoformat()
    if payload.last_review_date:
        d["lastReviewDate"] = payload.last_review_date.isoformat()
    if payload.effective_period_start or payload.effective_period_end:
        per = {}
        if payload.effective_period_start:
            per["start"] = fhir_instant(payload.effective_period_start)
        if payload.effective_period_end:
            per["end"] = fhir_instant(payload.effective_period_end)
        d["effectivePeriod"] = per
    if payload.topic:
        d["topic"] = [_codeable_concept_from_payload(t) for t in payload.topic if t]
    if payload.author:
        d["author"] = [_contact_from_payload(c) for c in payload.author]
    if payload.editor:
        d["editor"] = [_contact_from_payload(c) for c in payload.editor]
    if payload.reviewer:
        d["reviewer"] = [_contact_from_payload(c) for c in payload.reviewer]
    if payload.endorser:
        d["endorser"] = [_contact_from_payload(c) for c in payload.endorser]
    if payload.related_artifact:
        d["relatedArtifact"] = [
            _related_artifact_from_payload(ra) for ra in payload.related_artifact
        ]
    if payload.library:
        d["library"] = list(payload.library)
    if payload.goal:
        d["goal"] = [_goal_from_payload(g) for g in payload.goal]
    if payload.action:
        d["action"] = [_action_from_payload(act) for act in payload.action]
    if payload.extension:
        d["extension"] = payload.extension

    return d


def patch_fragment_to_fhir_plan_definition(
    payload: PlanDefinitionPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert a PlanDefinitionPatchSchema to a FHIR R4 partial fragment."""
    fragment: dict[str, Any] = {}
    touched: set[str] = set()
    fields_set = payload.model_fields_set

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "url" in fields_set:
        touched.add("url")
        if payload.url is not None:
            fragment["url"] = payload.url

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                _identifier_from_payload(i) for i in payload.identifier
            ]

    if "version" in fields_set:
        touched.add("version")
        if payload.version is not None:
            fragment["version"] = payload.version

    if "name" in fields_set:
        touched.add("name")
        if payload.name is not None:
            fragment["name"] = payload.name

    if "title" in fields_set:
        touched.add("title")
        if payload.title is not None:
            fragment["title"] = payload.title

    if "subtitle" in fields_set:
        touched.add("subtitle")
        if payload.subtitle is not None:
            fragment["subtitle"] = payload.subtitle

    if "type" in fields_set:
        touched.add("type")
        if payload.type is not None:
            t = _codeable_concept_from_payload(payload.type)
            if t:
                fragment["type"] = t

    if "experimental" in fields_set:
        touched.add("experimental")
        if payload.experimental is not None:
            fragment["experimental"] = payload.experimental

    if fields_set & _SUBJECT_FIELDS:
        touched.update(["subjectCodeableConcept", "subjectReference"])
        if payload.subject_codeable_concept:
            scc = _codeable_concept_from_payload(payload.subject_codeable_concept)
            if scc:
                fragment["subjectCodeableConcept"] = scc
        elif payload.subject_reference:
            sref = {"reference": payload.subject_reference}
            if payload.subject_display:
                sref["display"] = payload.subject_display
            fragment["subjectReference"] = sref

    if "date" in fields_set:
        touched.add("date")
        if payload.date is not None:
            fragment["date"] = fhir_instant(payload.date)

    if "publisher" in fields_set:
        touched.add("publisher")
        if payload.publisher is not None:
            fragment["publisher"] = payload.publisher

    if "contact" in fields_set:
        touched.add("contact")
        if payload.contact is not None:
            fragment["contact"] = [_contact_from_payload(c) for c in payload.contact]

    if "description" in fields_set:
        touched.add("description")
        if payload.description is not None:
            fragment["description"] = payload.description

    if "use_context" in fields_set:
        touched.add("useContext")
        if payload.use_context is not None:
            fragment["useContext"] = [
                _use_context_from_payload(uc) for uc in payload.use_context
            ]

    if "jurisdiction" in fields_set:
        touched.add("jurisdiction")
        if payload.jurisdiction is not None:
            fragment["jurisdiction"] = [
                _codeable_concept_from_payload(j) for j in payload.jurisdiction if j
            ]

    if "purpose" in fields_set:
        touched.add("purpose")
        if payload.purpose is not None:
            fragment["purpose"] = payload.purpose

    if "usage" in fields_set:
        touched.add("usage")
        if payload.usage is not None:
            fragment["usage"] = payload.usage

    if "copyright" in fields_set:
        touched.add("copyright")
        if payload.copyright is not None:
            fragment["copyright"] = payload.copyright

    if "approval_date" in fields_set:
        touched.add("approvalDate")
        if payload.approval_date is not None:
            fragment["approvalDate"] = payload.approval_date.isoformat()

    if "last_review_date" in fields_set:
        touched.add("lastReviewDate")
        if payload.last_review_date is not None:
            fragment["lastReviewDate"] = payload.last_review_date.isoformat()

    if fields_set & _EFFECTIVE_PERIOD_FIELDS:
        touched.add("effectivePeriod")
        per = {}
        if payload.effective_period_start:
            per["start"] = fhir_instant(payload.effective_period_start)
        if payload.effective_period_end:
            per["end"] = fhir_instant(payload.effective_period_end)
        if per:
            fragment["effectivePeriod"] = per

    if "topic" in fields_set:
        touched.add("topic")
        if payload.topic is not None:
            fragment["topic"] = [
                _codeable_concept_from_payload(t) for t in payload.topic if t
            ]

    if "author" in fields_set:
        touched.add("author")
        if payload.author is not None:
            fragment["author"] = [_contact_from_payload(c) for c in payload.author]

    if "editor" in fields_set:
        touched.add("editor")
        if payload.editor is not None:
            fragment["editor"] = [_contact_from_payload(c) for c in payload.editor]

    if "reviewer" in fields_set:
        touched.add("reviewer")
        if payload.reviewer is not None:
            fragment["reviewer"] = [_contact_from_payload(c) for c in payload.reviewer]

    if "endorser" in fields_set:
        touched.add("endorser")
        if payload.endorser is not None:
            fragment["endorser"] = [_contact_from_payload(c) for c in payload.endorser]

    if "related_artifact" in fields_set:
        touched.add("relatedArtifact")
        if payload.related_artifact is not None:
            fragment["relatedArtifact"] = [
                _related_artifact_from_payload(ra) for ra in payload.related_artifact
            ]

    if "library" in fields_set:
        touched.add("library")
        if payload.library is not None:
            fragment["library"] = list(payload.library)

    if "goal" in fields_set:
        touched.add("goal")
        if payload.goal is not None:
            fragment["goal"] = [_goal_from_payload(g) for g in payload.goal]

    if "action" in fields_set:
        touched.add("action")
        if payload.action is not None:
            fragment["action"] = [_action_from_payload(act) for act in payload.action]

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
