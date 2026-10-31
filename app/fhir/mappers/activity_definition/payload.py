"""Payload -> FHIR JSON conversion for ActivityDefinition.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ActivityDefinitionCreateSchema / ActivityDefinitionPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.schemas.activity_definition.input import (
        ActivityDefinitionCodeableConceptInput,
        ActivityDefinitionContactInput,
        ActivityDefinitionCreateSchema,
        ActivityDefinitionDosageInput,
        ActivityDefinitionDynamicValueInput,
        ActivityDefinitionIdentifierInput,
        ActivityDefinitionParticipantInput,
        ActivityDefinitionPatchSchema,
        ActivityDefinitionRelatedArtifactInput,
        ActivityDefinitionUseContextInput,
    )


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
    concept: ActivityDefinitionCodeableConceptInput | None,
) -> dict | None:
    if not concept:
        return None
    codings = [_coding_from_payload(c) for c in (concept.coding or [])]
    codings = [c for c in codings if c]
    result: dict[str, Any] = {}
    if codings:
        result["coding"] = codings
    if concept.text:
        result["text"] = concept.text
    return result or None


def _identifier_from_payload(i: ActivityDefinitionIdentifierInput) -> dict:
    ident: dict[str, Any] = {}
    if i.use:
        ident["use"] = fhir_enum(i.use)
    if i.system:
        ident["system"] = i.system
    if i.value:
        ident["value"] = i.value
    if i.type_text or i.type_coding:
        t: dict[str, Any] = {}
        if i.type_text:
            t["text"] = i.type_text
        if i.type_coding:
            cds = [_coding_from_payload(c) for c in i.type_coding]
            cds = [c for c in cds if c]
            if cds:
                t["coding"] = cds
        if t:
            ident["type"] = t
    if i.period_start or i.period_end:
        p: dict[str, Any] = {}
        if i.period_start:
            p["start"] = fhir_instant(i.period_start)
        if i.period_end:
            p["end"] = fhir_instant(i.period_end)
        ident["period"] = p
    if i.assigner:
        ref_obj: dict[str, Any] = {"reference": i.assigner}
        if i.assigner_display:
            ref_obj["display"] = i.assigner_display
        ident["assigner"] = ref_obj
    return ident


def _contact_from_payload(c: ActivityDefinitionContactInput) -> dict:
    entry: dict[str, Any] = {}
    if c.name:
        entry["name"] = c.name
    if c.telecom:
        telecoms = []
        for t in c.telecom:
            tel: dict[str, Any] = {}
            if t.system:
                tel["system"] = fhir_enum(t.system)
            if t.value:
                tel["value"] = t.value
            if t.use:
                tel["use"] = fhir_enum(t.use)
            if t.rank is not None:
                tel["rank"] = t.rank
            if t.period_start or t.period_end:
                p: dict[str, Any] = {}
                if t.period_start:
                    p["start"] = fhir_instant(t.period_start)
                if t.period_end:
                    p["end"] = fhir_instant(t.period_end)
                tel["period"] = p
            if tel:
                telecoms.append(tel)
        if telecoms:
            entry["telecom"] = telecoms
    return entry


def _use_context_from_payload(uc: ActivityDefinitionUseContextInput) -> dict:
    entry: dict[str, Any] = {}
    code_dict: dict[str, Any] = {}
    if uc.code_system:
        code_dict["system"] = uc.code_system
    if uc.code_version:
        code_dict["version"] = uc.code_version
    if uc.code_code:
        code_dict["code"] = uc.code_code
    if uc.code_display:
        code_dict["display"] = uc.code_display
    if uc.code_user_selected is not None:
        code_dict["userSelected"] = uc.code_user_selected
    if code_dict:
        entry["code"] = code_dict

    vcc: dict[str, Any] = {}
    if uc.value_codeable_concept_text:
        vcc["text"] = uc.value_codeable_concept_text
    if uc.value_codeable_concept_coding:
        cds = [_coding_from_payload(c) for c in uc.value_codeable_concept_coding]
        cds = [c for c in cds if c]
        if cds:
            vcc["coding"] = cds
    if vcc:
        entry["valueCodeableConcept"] = vcc

    if uc.value_quantity_value is not None:
        q: dict[str, Any] = {"value": float(uc.value_quantity_value)}
        if uc.value_quantity_comparator:
            q["comparator"] = fhir_enum(uc.value_quantity_comparator)
        if uc.value_quantity_unit:
            q["unit"] = uc.value_quantity_unit
        if uc.value_quantity_system:
            q["system"] = uc.value_quantity_system
        if uc.value_quantity_code:
            q["code"] = uc.value_quantity_code
        entry["valueQuantity"] = q

    if uc.value_range_low_value is not None or uc.value_range_high_value is not None:
        r: dict[str, Any] = {}
        if uc.value_range_low_value is not None:
            low_q: dict[str, Any] = {"value": float(uc.value_range_low_value)}
            if uc.value_range_low_unit:
                low_q["unit"] = uc.value_range_low_unit
            if uc.value_range_low_system:
                low_q["system"] = uc.value_range_low_system
            if uc.value_range_low_code:
                low_q["code"] = uc.value_range_low_code
            r["low"] = low_q
        if uc.value_range_high_value is not None:
            high_q: dict[str, Any] = {"value": float(uc.value_range_high_value)}
            if uc.value_range_high_unit:
                high_q["unit"] = uc.value_range_high_unit
            if uc.value_range_high_system:
                high_q["system"] = uc.value_range_high_system
            if uc.value_range_high_code:
                high_q["code"] = uc.value_range_high_code
            r["high"] = high_q
        entry["valueRange"] = r

    if uc.value_reference:
        ref_obj: dict[str, Any] = {"reference": uc.value_reference}
        if uc.value_reference_display:
            ref_obj["display"] = uc.value_reference_display
        entry["valueReference"] = ref_obj

    return entry


def _related_artifact_from_payload(ra: ActivityDefinitionRelatedArtifactInput) -> dict:
    entry: dict[str, Any] = {}
    if ra.type:
        entry["type"] = fhir_enum(ra.type)
    if ra.label:
        entry["label"] = ra.label
    if ra.display:
        entry["display"] = ra.display
    if ra.citation:
        entry["citation"] = ra.citation
    if ra.url:
        entry["url"] = ra.url
    if ra.document:
        entry["document"] = ra.document
    if ra.resource:
        entry["resource"] = ra.resource
    return entry


def _participant_from_payload(p: ActivityDefinitionParticipantInput) -> dict:
    entry: dict[str, Any] = {}
    if p.type:
        entry["type"] = fhir_enum(p.type)
    role = _codeable_concept_from_payload(p.role)
    if role:
        entry["role"] = role
    return entry


def _dosage_from_payload(d: ActivityDefinitionDosageInput) -> dict:
    entry: dict[str, Any] = {}
    if d.sequence is not None:
        entry["sequence"] = d.sequence
    if d.text:
        entry["text"] = d.text
    if d.patient_instruction:
        entry["patientInstruction"] = d.patient_instruction
    if d.timing:
        entry["timing"] = d.timing
    if d.as_needed_boolean is not None:
        entry["asNeededBoolean"] = d.as_needed_boolean
    an_cc = _codeable_concept_from_payload(d.as_needed_codeable_concept)
    if an_cc:
        entry["asNeededCodeableConcept"] = an_cc
    site = _codeable_concept_from_payload(d.site)
    if site:
        entry["site"] = site
    route = _codeable_concept_from_payload(d.route)
    if route:
        entry["route"] = route
    method = _codeable_concept_from_payload(d.method)
    if method:
        entry["method"] = method
    if d.dose_and_rate:
        entry["doseAndRate"] = d.dose_and_rate
    if d.max_dose_per_period:
        entry["maxDosePerPeriod"] = d.max_dose_per_period
    if d.max_dose_per_administration_value is not None:
        q_admin: dict[str, Any] = {"value": float(d.max_dose_per_administration_value)}
        if d.max_dose_per_administration_unit:
            q_admin["unit"] = d.max_dose_per_administration_unit
        if d.max_dose_per_administration_system:
            q_admin["system"] = d.max_dose_per_administration_system
        if d.max_dose_per_administration_code:
            q_admin["code"] = d.max_dose_per_administration_code
        entry["maxDosePerAdministration"] = q_admin
    if d.max_dose_per_lifetime_value is not None:
        q_life: dict[str, Any] = {"value": float(d.max_dose_per_lifetime_value)}
        if d.max_dose_per_lifetime_unit:
            q_life["unit"] = d.max_dose_per_lifetime_unit
        if d.max_dose_per_lifetime_system:
            q_life["system"] = d.max_dose_per_lifetime_system
        if d.max_dose_per_lifetime_code:
            q_life["code"] = d.max_dose_per_lifetime_code
        entry["maxDosePerLifetime"] = q_life
    return entry


def _dynamic_value_from_payload(dv: ActivityDefinitionDynamicValueInput) -> dict:
    entry: dict[str, Any] = {}
    if dv.path:
        entry["path"] = dv.path
    expr: dict[str, Any] = {}
    if dv.expression_description:
        expr["description"] = dv.expression_description
    if dv.expression_name:
        expr["name"] = dv.expression_name
    if dv.expression_language:
        expr["language"] = dv.expression_language
    if dv.expression_expression:
        expr["expression"] = dv.expression_expression
    if dv.expression_reference:
        expr["reference"] = dv.expression_reference
    if expr:
        entry["expression"] = expr
    return entry


def payload_to_fhir_activity_definition(
    payload: ActivityDefinitionCreateSchema,
) -> dict[str, Any]:
    """Map a CREATE payload into a FHIR R4 ActivityDefinition resource dict for validation."""
    fhir: dict[str, Any] = {
        "resourceType": "ActivityDefinition",
        "status": fhir_enum(payload.status),
    }

    if payload.url:
        fhir["url"] = payload.url

    if payload.identifier:
        fhir["identifier"] = [_identifier_from_payload(i) for i in payload.identifier]

    if payload.version:
        fhir["version"] = payload.version

    if payload.name:
        fhir["name"] = payload.name

    if payload.title:
        fhir["title"] = payload.title

    if payload.subtitle:
        fhir["subtitle"] = payload.subtitle

    if payload.experimental is not None:
        fhir["experimental"] = payload.experimental

    if payload.date:
        fhir["date"] = fhir_instant(payload.date)

    if payload.publisher:
        fhir["publisher"] = payload.publisher

    if payload.contact:
        fhir["contact"] = [_contact_from_payload(c) for c in payload.contact]

    if payload.description:
        fhir["description"] = payload.description

    if payload.use_context:
        fhir["useContext"] = [_use_context_from_payload(uc) for uc in payload.use_context]

    if payload.jurisdiction:
        juris = [_codeable_concept_from_payload(j) for j in payload.jurisdiction]
        fhir["jurisdiction"] = [j for j in juris if j]

    if payload.purpose:
        fhir["purpose"] = payload.purpose

    if payload.usage:
        fhir["usage"] = payload.usage

    if payload.copyright:
        fhir["copyright"] = payload.copyright

    if payload.approval_date:
        fhir["approvalDate"] = payload.approval_date.isoformat()

    if payload.last_review_date:
        fhir["lastReviewDate"] = payload.last_review_date.isoformat()

    if payload.effective_period_start or payload.effective_period_end:
        p: dict[str, Any] = {}
        if payload.effective_period_start:
            p["start"] = fhir_instant(payload.effective_period_start)
        if payload.effective_period_end:
            p["end"] = fhir_instant(payload.effective_period_end)
        fhir["effectivePeriod"] = p

    if payload.topic:
        topics = [_codeable_concept_from_payload(t) for t in payload.topic]
        fhir["topic"] = [t for t in topics if t]

    if payload.author:
        fhir["author"] = [_contact_from_payload(a) for a in payload.author]

    if payload.editor:
        fhir["editor"] = [_contact_from_payload(e) for e in payload.editor]

    if payload.reviewer:
        fhir["reviewer"] = [_contact_from_payload(r) for r in payload.reviewer]

    if payload.endorser:
        fhir["endorser"] = [_contact_from_payload(e) for e in payload.endorser]

    if payload.related_artifact:
        fhir["relatedArtifact"] = [
            _related_artifact_from_payload(ra) for ra in payload.related_artifact
        ]

    if payload.library:
        fhir["library"] = payload.library

    if payload.kind:
        fhir["kind"] = fhir_enum(payload.kind)

    if payload.profile:
        fhir["profile"] = payload.profile

    if payload.code:
        c = _codeable_concept_from_payload(payload.code)
        if c:
            fhir["code"] = c

    if payload.intent:
        fhir["intent"] = fhir_enum(payload.intent)

    if payload.priority:
        fhir["priority"] = fhir_enum(payload.priority)

    if payload.do_not_perform is not None:
        fhir["doNotPerform"] = payload.do_not_perform

    # timing[x]
    if payload.timing_timing:
        fhir["timingTiming"] = payload.timing_timing
    elif payload.timing_date_time:
        fhir["timingDateTime"] = fhir_instant(payload.timing_date_time)
    elif payload.timing_age_value is not None:
        q_age: dict[str, Any] = {"value": float(payload.timing_age_value)}
        if payload.timing_age_unit:
            q_age["unit"] = payload.timing_age_unit
        if payload.timing_age_system:
            q_age["system"] = payload.timing_age_system
        if payload.timing_age_code:
            q_age["code"] = payload.timing_age_code
        fhir["timingAge"] = q_age
    elif payload.timing_period_start or payload.timing_period_end:
        tp: dict[str, Any] = {}
        if payload.timing_period_start:
            tp["start"] = fhir_instant(payload.timing_period_start)
        if payload.timing_period_end:
            tp["end"] = fhir_instant(payload.timing_period_end)
        fhir["timingPeriod"] = tp
    elif (
        payload.timing_range_low_value is not None
        or payload.timing_range_high_value is not None
    ):
        tr: dict[str, Any] = {}
        if payload.timing_range_low_value is not None:
            low_q = {"value": float(payload.timing_range_low_value)}
            if payload.timing_range_low_unit:
                low_q["unit"] = payload.timing_range_low_unit
            tr["low"] = low_q
        if payload.timing_range_high_value is not None:
            high_q = {"value": float(payload.timing_range_high_value)}
            if payload.timing_range_high_unit:
                high_q["unit"] = payload.timing_range_high_unit
            tr["high"] = high_q
        fhir["timingRange"] = tr
    elif payload.timing_duration_value is not None:
        q_dur: dict[str, Any] = {"value": float(payload.timing_duration_value)}
        if payload.timing_duration_unit:
            q_dur["unit"] = payload.timing_duration_unit
        if payload.timing_duration_system:
            q_dur["system"] = payload.timing_duration_system
        if payload.timing_duration_code:
            q_dur["code"] = payload.timing_duration_code
        fhir["timingDuration"] = q_dur

    if payload.location:
        loc_obj: dict[str, Any] = {"reference": payload.location}
        if payload.location_display:
            loc_obj["display"] = payload.location_display
        fhir["location"] = loc_obj

    if payload.participant:
        fhir["participant"] = [_participant_from_payload(p) for p in payload.participant]

    # product[x]
    if payload.product_codeable_concept:
        pcc = _codeable_concept_from_payload(payload.product_codeable_concept)
        if pcc:
            fhir["productCodeableConcept"] = pcc
    elif payload.product_reference:
        pref: dict[str, Any] = {"reference": payload.product_reference}
        if payload.product_display:
            pref["display"] = payload.product_display
        fhir["productReference"] = pref

    if payload.quantity_value is not None:
        qty: dict[str, Any] = {"value": float(payload.quantity_value)}
        if payload.quantity_comparator:
            qty["comparator"] = fhir_enum(payload.quantity_comparator)
        if payload.quantity_unit:
            qty["unit"] = payload.quantity_unit
        if payload.quantity_system:
            qty["system"] = payload.quantity_system
        if payload.quantity_code:
            qty["code"] = payload.quantity_code
        fhir["quantity"] = qty

    if payload.dosage:
        fhir["dosage"] = [_dosage_from_payload(d) for d in payload.dosage]

    if payload.body_site:
        sites = [_codeable_concept_from_payload(b) for b in payload.body_site]
        fhir["bodySite"] = [s for s in sites if s]

    if payload.specimen_requirement:
        fhir["specimenRequirement"] = [
            {"reference": r} for r in payload.specimen_requirement
        ]

    if payload.observation_requirement:
        fhir["observationRequirement"] = [
            {"reference": r} for r in payload.observation_requirement
        ]

    if payload.observation_result_requirement:
        fhir["observationResultRequirement"] = [
            {"reference": r} for r in payload.observation_result_requirement
        ]

    if payload.transform:
        fhir["transform"] = payload.transform

    if payload.dynamic_value:
        fhir["dynamicValue"] = [
            _dynamic_value_from_payload(dv) for dv in payload.dynamic_value
        ]

    # subject[x]
    if payload.subject_codeable_concept:
        scc = _codeable_concept_from_payload(payload.subject_codeable_concept)
        if scc:
            fhir["subjectCodeableConcept"] = scc
    elif payload.subject_reference:
        sref: dict[str, Any] = {"reference": payload.subject_reference}
        if payload.subject_display:
            sref["display"] = payload.subject_display
        fhir["subjectReference"] = sref

    if payload.extension:
        fhir["extension"] = payload.extension

    return {k: v for k, v in fhir.items() if v is not None}


_TIMING_FIELDS = {
    "timing_timing",
    "timing_date_time",
    "timing_age_value",
    "timing_age_unit",
    "timing_age_system",
    "timing_age_code",
    "timing_period_start",
    "timing_period_end",
    "timing_range_low_value",
    "timing_range_low_unit",
    "timing_range_high_value",
    "timing_range_high_unit",
    "timing_duration_value",
    "timing_duration_unit",
    "timing_duration_system",
    "timing_duration_code",
}

_PRODUCT_FIELDS = {
    "product_codeable_concept",
    "product_reference",
    "product_display",
}

_SUBJECT_FIELDS = {
    "subject_codeable_concept",
    "subject_reference",
    "subject_display",
}

_QUANTITY_FIELDS = {
    "quantity_value",
    "quantity_comparator",
    "quantity_unit",
    "quantity_system",
    "quantity_code",
}

_EFFECTIVE_PERIOD_FIELDS = {
    "effective_period_start",
    "effective_period_end",
}


def patch_fragment_to_fhir_activity_definition(
    payload: ActivityDefinitionPatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    """Convert an ActivityDefinition PATCH schema into a partial FHIR fragment and set of touched fields."""
    fields_set = payload.model_dump(exclude_unset=True).keys()
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

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

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "experimental" in fields_set:
        touched.add("experimental")
        if payload.experimental is not None:
            fragment["experimental"] = payload.experimental

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
            juris = [_codeable_concept_from_payload(j) for j in payload.jurisdiction]
            fragment["jurisdiction"] = [j for j in juris if j]

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
        if payload.effective_period_start or payload.effective_period_end:
            p: dict[str, Any] = {}
            if payload.effective_period_start:
                p["start"] = fhir_instant(payload.effective_period_start)
            if payload.effective_period_end:
                p["end"] = fhir_instant(payload.effective_period_end)
            fragment["effectivePeriod"] = p

    if "topic" in fields_set:
        touched.add("topic")
        if payload.topic is not None:
            topics = [_codeable_concept_from_payload(t) for t in payload.topic]
            fragment["topic"] = [t for t in topics if t]

    if "author" in fields_set:
        touched.add("author")
        if payload.author is not None:
            fragment["author"] = [_contact_from_payload(a) for a in payload.author]

    if "editor" in fields_set:
        touched.add("editor")
        if payload.editor is not None:
            fragment["editor"] = [_contact_from_payload(e) for e in payload.editor]

    if "reviewer" in fields_set:
        touched.add("reviewer")
        if payload.reviewer is not None:
            fragment["reviewer"] = [_contact_from_payload(r) for r in payload.reviewer]

    if "endorser" in fields_set:
        touched.add("endorser")
        if payload.endorser is not None:
            fragment["endorser"] = [_contact_from_payload(e) for e in payload.endorser]

    if "related_artifact" in fields_set:
        touched.add("relatedArtifact")
        if payload.related_artifact is not None:
            fragment["relatedArtifact"] = [
                _related_artifact_from_payload(ra) for ra in payload.related_artifact
            ]

    if "library" in fields_set:
        touched.add("library")
        if payload.library is not None:
            fragment["library"] = payload.library

    if "kind" in fields_set:
        touched.add("kind")
        if payload.kind is not None:
            fragment["kind"] = fhir_enum(payload.kind)

    if "profile" in fields_set:
        touched.add("profile")
        if payload.profile is not None:
            fragment["profile"] = payload.profile

    if "code" in fields_set:
        touched.add("code")
        if payload.code is not None:
            c = _codeable_concept_from_payload(payload.code)
            if c:
                fragment["code"] = c

    if "intent" in fields_set:
        touched.add("intent")
        if payload.intent is not None:
            fragment["intent"] = fhir_enum(payload.intent)

    if "priority" in fields_set:
        touched.add("priority")
        if payload.priority is not None:
            fragment["priority"] = fhir_enum(payload.priority)

    if "do_not_perform" in fields_set:
        touched.add("doNotPerform")
        if payload.do_not_perform is not None:
            fragment["doNotPerform"] = payload.do_not_perform

    # timing[x]
    if fields_set & _TIMING_FIELDS:
        touched.update(
            [
                "timingTiming",
                "timingDateTime",
                "timingAge",
                "timingPeriod",
                "timingRange",
                "timingDuration",
            ]
        )
        if payload.timing_timing:
            fragment["timingTiming"] = payload.timing_timing
        elif payload.timing_date_time:
            fragment["timingDateTime"] = fhir_instant(payload.timing_date_time)
        elif payload.timing_age_value is not None:
            q_age = {"value": float(payload.timing_age_value)}
            if payload.timing_age_unit:
                q_age["unit"] = payload.timing_age_unit
            if payload.timing_age_system:
                q_age["system"] = payload.timing_age_system
            if payload.timing_age_code:
                q_age["code"] = payload.timing_age_code
            fragment["timingAge"] = q_age
        elif payload.timing_period_start or payload.timing_period_end:
            tp = {}
            if payload.timing_period_start:
                tp["start"] = fhir_instant(payload.timing_period_start)
            if payload.timing_period_end:
                tp["end"] = fhir_instant(payload.timing_period_end)
            fragment["timingPeriod"] = tp
        elif (
            payload.timing_range_low_value is not None
            or payload.timing_range_high_value is not None
        ):
            tr = {}
            if payload.timing_range_low_value is not None:
                low_q = {"value": float(payload.timing_range_low_value)}
                if payload.timing_range_low_unit:
                    low_q["unit"] = payload.timing_range_low_unit
                tr["low"] = low_q
            if payload.timing_range_high_value is not None:
                high_q = {"value": float(payload.timing_range_high_value)}
                if payload.timing_range_high_unit:
                    high_q["unit"] = payload.timing_range_high_unit
                tr["high"] = high_q
            fragment["timingRange"] = tr
        elif payload.timing_duration_value is not None:
            q_dur = {"value": float(payload.timing_duration_value)}
            if payload.timing_duration_unit:
                q_dur["unit"] = payload.timing_duration_unit
            if payload.timing_duration_system:
                q_dur["system"] = payload.timing_duration_system
            if payload.timing_duration_code:
                q_dur["code"] = payload.timing_duration_code
            fragment["timingDuration"] = q_dur

    if "location" in fields_set or "location_display" in fields_set:
        touched.add("location")
        if payload.location is not None:
            loc_obj = {"reference": payload.location}
            if payload.location_display:
                loc_obj["display"] = payload.location_display
            fragment["location"] = loc_obj

    if "participant" in fields_set:
        touched.add("participant")
        if payload.participant is not None:
            fragment["participant"] = [
                _participant_from_payload(p) for p in payload.participant
            ]

    # product[x]
    if fields_set & _PRODUCT_FIELDS:
        touched.update(["productCodeableConcept", "productReference"])
        if payload.product_codeable_concept:
            pcc = _codeable_concept_from_payload(payload.product_codeable_concept)
            if pcc:
                fragment["productCodeableConcept"] = pcc
        elif payload.product_reference:
            pref = {"reference": payload.product_reference}
            if payload.product_display:
                pref["display"] = payload.product_display
            fragment["productReference"] = pref

    if fields_set & _QUANTITY_FIELDS:
        touched.add("quantity")
        if payload.quantity_value is not None:
            qty = {"value": float(payload.quantity_value)}
            if payload.quantity_comparator:
                qty["comparator"] = fhir_enum(payload.quantity_comparator)
            if payload.quantity_unit:
                qty["unit"] = payload.quantity_unit
            if payload.quantity_system:
                qty["system"] = payload.quantity_system
            if payload.quantity_code:
                qty["code"] = payload.quantity_code
            fragment["quantity"] = qty

    if "dosage" in fields_set:
        touched.add("dosage")
        if payload.dosage is not None:
            fragment["dosage"] = [_dosage_from_payload(d) for d in payload.dosage]

    if "body_site" in fields_set:
        touched.add("bodySite")
        if payload.body_site is not None:
            sites = [_codeable_concept_from_payload(b) for b in payload.body_site]
            fragment["bodySite"] = [s for s in sites if s]

    if "specimen_requirement" in fields_set:
        touched.add("specimenRequirement")
        if payload.specimen_requirement is not None:
            fragment["specimenRequirement"] = [
                {"reference": r} for r in payload.specimen_requirement
            ]

    if "observation_requirement" in fields_set:
        touched.add("observationRequirement")
        if payload.observation_requirement is not None:
            fragment["observationRequirement"] = [
                {"reference": r} for r in payload.observation_requirement
            ]

    if "observation_result_requirement" in fields_set:
        touched.add("observationResultRequirement")
        if payload.observation_result_requirement is not None:
            fragment["observationResultRequirement"] = [
                {"reference": r} for r in payload.observation_result_requirement
            ]

    if "transform" in fields_set:
        touched.add("transform")
        if payload.transform is not None:
            fragment["transform"] = payload.transform

    if "dynamic_value" in fields_set:
        touched.add("dynamicValue")
        if payload.dynamic_value is not None:
            fragment["dynamicValue"] = [
                _dynamic_value_from_payload(dv) for dv in payload.dynamic_value
            ]

    # subject[x]
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

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
