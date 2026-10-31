"""Payload -> FHIR JSON conversion for Condition.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ConditionCreateSchema / ConditionPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.condition.input import (
        ConditionCreateSchema,
        ConditionEvidenceInput,
        ConditionIdentifierInput,
        ConditionNoteInput,
        ConditionPatchSchema,
        ConditionStageInput,
    )
    from app.schemas.condition.input.codeable_concept import ConditionCodeableConceptInput

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}

_ONSET_FIELDS = {
    "onset_date_time",
    "onset_age_value",
    "onset_age_comparator",
    "onset_age_unit",
    "onset_age_system",
    "onset_age_code",
    "onset_period_start",
    "onset_period_end",
    "onset_range_low_value",
    "onset_range_low_unit",
    "onset_range_low_system",
    "onset_range_low_code",
    "onset_range_high_value",
    "onset_range_high_unit",
    "onset_range_high_system",
    "onset_range_high_code",
    "onset_string",
}
_ONSET_FHIR_KEYS = {"onsetDateTime", "onsetAge", "onsetPeriod", "onsetRange", "onsetString"}

_ABATEMENT_FIELDS = {
    "abatement_date_time",
    "abatement_age_value",
    "abatement_age_comparator",
    "abatement_age_unit",
    "abatement_age_system",
    "abatement_age_code",
    "abatement_period_start",
    "abatement_period_end",
    "abatement_range_low_value",
    "abatement_range_low_unit",
    "abatement_range_low_system",
    "abatement_range_low_code",
    "abatement_range_high_value",
    "abatement_range_high_unit",
    "abatement_range_high_system",
    "abatement_range_high_code",
    "abatement_string",
}
_ABATEMENT_FHIR_KEYS = {
    "abatementDateTime",
    "abatementAge",
    "abatementPeriod",
    "abatementRange",
    "abatementString",
}


def _coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "userSelected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def payload_condition_codeable_concept(
    cc: ConditionCodeableConceptInput | None,
) -> dict | None:
    if cc is None:
        return None
    coding_list = _coding_list(cc.coding)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if cc.text:
        result["text"] = cc.text
    return result or None


def _reference_from_payload(obj) -> dict:
    if obj is None:
        return {}
    entry: dict = {}
    if getattr(obj, "reference", None):
        entry["reference"] = obj.reference
    if getattr(obj, "reference_display", None):
        entry["display"] = obj.reference_display

    id_use = getattr(obj, "reference_identifier_use", None)
    id_system = getattr(obj, "reference_identifier_system", None)
    id_value = getattr(obj, "reference_identifier_value", None)
    id_type_text = getattr(obj, "reference_identifier_type_text", None)

    if id_use or id_system or id_value or id_type_text:
        identifier: dict = {}
        if id_use:
            identifier["use"] = id_use.value if hasattr(id_use, "value") else str(id_use)
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_type_text:
            identifier["type"] = {"text": id_type_text}
        entry["identifier"] = identifier

    return entry


def payload_condition_identifier(i: ConditionIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use.value if hasattr(i.use, "value") else str(i.use)
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value

    type_codings = _coding_list(i.type_coding)
    if type_codings or i.type_text:
        type_cc: dict = {}
        if type_codings:
            type_cc["coding"] = type_codings
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc

    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": i.period_start.isoformat() if i.period_start else None,
                "end": i.period_end.isoformat() if i.period_end else None,
            }.items()
            if v
        }

    if i.assigner or i.assigner_display or i.assigner_identifier_system or i.assigner_identifier_value:
        assigner: dict = {}
        if i.assigner:
            assigner["reference"] = i.assigner
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        if i.assigner_identifier_use or i.assigner_identifier_system or i.assigner_identifier_value or i.assigner_identifier_type_text:
            assigner_id: dict = {}
            if i.assigner_identifier_use:
                assigner_id["use"] = (
                    i.assigner_identifier_use.value
                    if hasattr(i.assigner_identifier_use, "value")
                    else str(i.assigner_identifier_use)
                )
            if i.assigner_identifier_system:
                assigner_id["system"] = i.assigner_identifier_system
            if i.assigner_identifier_value:
                assigner_id["value"] = i.assigner_identifier_value
            if i.assigner_identifier_type_text:
                assigner_id["type"] = {"text": i.assigner_identifier_type_text}
            assigner["identifier"] = assigner_id
        entry["assigner"] = assigner

    return entry


def payload_condition_stage(s: ConditionStageInput) -> dict:
    stage_dict: dict = {}
    summary = payload_condition_codeable_concept(s.summary)
    if summary:
        stage_dict["summary"] = summary

    assessments = [
        _reference_from_payload(a) for a in (s.assessment or [])
    ]
    assessments = [a for a in assessments if a]
    if assessments:
        stage_dict["assessment"] = assessments

    stage_type = payload_condition_codeable_concept(s.type)
    if stage_type:
        stage_dict["type"] = stage_type

    return stage_dict


def payload_condition_evidence(e: ConditionEvidenceInput) -> dict:
    evidence_dict: dict = {}
    codes = [
        payload_condition_codeable_concept(c) for c in (e.code or [])
    ]
    codes = [c for c in codes if c]
    if codes:
        evidence_dict["code"] = codes

    details = [
        _reference_from_payload(d) for d in (e.detail or [])
    ]
    details = [d for d in details if d]
    if details:
        evidence_dict["detail"] = details

    return evidence_dict


def payload_condition_note(n: ConditionNoteInput) -> dict:
    note_dict: dict = {}
    if n.author_reference:
        ref: dict = {"reference": n.author_reference}
        if n.author_reference_display:
            ref["display"] = n.author_reference_display
        note_dict["authorReference"] = ref
    elif n.author_string:
        note_dict["authorString"] = n.author_string

    if n.time:
        note_dict["time"] = n.time.isoformat()
    if n.text:
        note_dict["text"] = n.text
    return note_dict


def _onset_choice_from_payload(p) -> tuple[str, any] | None:
    if p.onset_date_time:
        return "onsetDateTime", p.onset_date_time.isoformat()
    if p.onset_age_value is not None:
        comp = p.onset_age_comparator
        comp_val = _COMPARATOR_SYMBOLS.get(
            comp.value if hasattr(comp, "value") else str(comp)
        ) if comp else None
        q = {
            k: v
            for k, v in {
                "value": float(p.onset_age_value),
                "comparator": comp_val,
                "unit": p.onset_age_unit,
                "system": p.onset_age_system,
                "code": p.onset_age_code,
            }.items()
            if v is not None
        }
        return "onsetAge", q
    if p.onset_period_start or p.onset_period_end:
        period = {
            k: v
            for k, v in {
                "start": p.onset_period_start.isoformat() if p.onset_period_start else None,
                "end": p.onset_period_end.isoformat() if p.onset_period_end else None,
            }.items()
            if v
        }
        return "onsetPeriod", period
    if p.onset_range_low_value is not None or p.onset_range_high_value is not None:
        rng: dict = {}
        if p.onset_range_low_value is not None:
            rng["low"] = {
                k: v
                for k, v in {
                    "value": float(p.onset_range_low_value),
                    "unit": p.onset_range_low_unit,
                    "system": p.onset_range_low_system,
                    "code": p.onset_range_low_code,
                }.items()
                if v is not None
            }
        if p.onset_range_high_value is not None:
            rng["high"] = {
                k: v
                for k, v in {
                    "value": float(p.onset_range_high_value),
                    "unit": p.onset_range_high_unit,
                    "system": p.onset_range_high_system,
                    "code": p.onset_range_high_code,
                }.items()
                if v is not None
            }
        return "onsetRange", rng
    if p.onset_string:
        return "onsetString", p.onset_string
    return None


def _abatement_choice_from_payload(p) -> tuple[str, any] | None:
    if p.abatement_date_time:
        return "abatementDateTime", p.abatement_date_time.isoformat()
    if p.abatement_age_value is not None:
        comp = p.abatement_age_comparator
        comp_val = _COMPARATOR_SYMBOLS.get(
            comp.value if hasattr(comp, "value") else str(comp)
        ) if comp else None
        q = {
            k: v
            for k, v in {
                "value": float(p.abatement_age_value),
                "comparator": comp_val,
                "unit": p.abatement_age_unit,
                "system": p.abatement_age_system,
                "code": p.abatement_age_code,
            }.items()
            if v is not None
        }
        return "abatementAge", q
    if p.abatement_period_start or p.abatement_period_end:
        period = {
            k: v
            for k, v in {
                "start": p.abatement_period_start.isoformat() if p.abatement_period_start else None,
                "end": p.abatement_period_end.isoformat() if p.abatement_period_end else None,
            }.items()
            if v
        }
        return "abatementPeriod", period
    if p.abatement_range_low_value is not None or p.abatement_range_high_value is not None:
        rng: dict = {}
        if p.abatement_range_low_value is not None:
            rng["low"] = {
                k: v
                for k, v in {
                    "value": float(p.abatement_range_low_value),
                    "unit": p.abatement_range_low_unit,
                    "system": p.abatement_range_low_system,
                    "code": p.abatement_range_low_code,
                }.items()
                if v is not None
            }
        if p.abatement_range_high_value is not None:
            rng["high"] = {
                k: v
                for k, v in {
                    "value": float(p.abatement_range_high_value),
                    "unit": p.abatement_range_high_unit,
                    "system": p.abatement_range_high_system,
                    "code": p.abatement_range_high_code,
                }.items()
                if v is not None
            }
        return "abatementRange", rng
    if p.abatement_string:
        return "abatementString", p.abatement_string
    return None


def payload_to_fhir_condition(payload: ConditionCreateSchema) -> dict:
    result: dict = {"resourceType": "Condition"}

    if payload.extension:
        result["extension"] = payload.extension

    if payload.identifier:
        result["identifier"] = [
            payload_condition_identifier(i) for i in payload.identifier
        ]

    clinical_status = payload_condition_codeable_concept(payload.clinical_status)
    if clinical_status:
        result["clinicalStatus"] = clinical_status

    verification_status = payload_condition_codeable_concept(payload.verification_status)
    if verification_status:
        result["verificationStatus"] = verification_status

    if payload.category:
        cats = [payload_condition_codeable_concept(c) for c in payload.category]
        cats = [c for c in cats if c]
        if cats:
            result["category"] = cats

    severity = payload_condition_codeable_concept(payload.severity)
    if severity:
        result["severity"] = severity

    code = payload_condition_codeable_concept(payload.code)
    if code:
        result["code"] = code

    if payload.body_site:
        sites = [payload_condition_codeable_concept(b) for b in payload.body_site]
        sites = [b for b in sites if b]
        if sites:
            result["bodySite"] = sites

    subject = _reference_from_payload(payload.subject)
    if subject:
        result["subject"] = subject

    if payload.encounter:
        encounter = _reference_from_payload(payload.encounter)
        if encounter:
            result["encounter"] = encounter

    onset = _onset_choice_from_payload(payload)
    if onset:
        result[onset[0]] = onset[1]

    abatement = _abatement_choice_from_payload(payload)
    if abatement:
        result[abatement[0]] = abatement[1]

    if payload.recorded_date:
        result["recordedDate"] = payload.recorded_date.isoformat()

    if payload.recorder:
        recorder = _reference_from_payload(payload.recorder)
        if recorder:
            result["recorder"] = recorder

    if payload.asserter:
        asserter = _reference_from_payload(payload.asserter)
        if asserter:
            result["asserter"] = asserter

    if payload.stage:
        stages = [payload_condition_stage(s) for s in payload.stage]
        stages = [s for s in stages if s]
        if stages:
            result["stage"] = stages

    if payload.evidence:
        evidence = [payload_condition_evidence(e) for e in payload.evidence]
        evidence = [e for e in evidence if e]
        if evidence:
            result["evidence"] = evidence

    if payload.note:
        notes = [payload_condition_note(n) for n in payload.note]
        notes = [n for n in notes if n]
        if notes:
            result["note"] = notes

    return result


def patch_fragment_to_fhir_condition(
    payload: ConditionPatchSchema,
) -> tuple[dict, set[str]]:
    provided = payload.model_dump(exclude_unset=True)
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = payload.extension

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                payload_condition_identifier(i) for i in payload.identifier
            ]

    if "clinical_status" in provided:
        touched.add("clinicalStatus")
        if payload.clinical_status is not None:
            cc = payload_condition_codeable_concept(payload.clinical_status)
            if cc:
                fragment["clinicalStatus"] = cc

    if "verification_status" in provided:
        touched.add("verificationStatus")
        if payload.verification_status is not None:
            cc = payload_condition_codeable_concept(payload.verification_status)
            if cc:
                fragment["verificationStatus"] = cc

    if "category" in provided:
        touched.add("category")
        if payload.category is not None:
            cats = [payload_condition_codeable_concept(c) for c in payload.category]
            cats = [c for c in cats if c]
            if cats:
                fragment["category"] = cats

    if "severity" in provided:
        touched.add("severity")
        if payload.severity is not None:
            cc = payload_condition_codeable_concept(payload.severity)
            if cc:
                fragment["severity"] = cc

    if "code" in provided:
        touched.add("code")
        if payload.code is not None:
            cc = payload_condition_codeable_concept(payload.code)
            if cc:
                fragment["code"] = cc

    if "body_site" in provided:
        touched.add("bodySite")
        if payload.body_site is not None:
            sites = [payload_condition_codeable_concept(b) for b in payload.body_site]
            sites = [b for b in sites if b]
            if sites:
                fragment["bodySite"] = sites

    if "subject" in provided:
        touched.add("subject")
        if payload.subject is not None:
            subj = _reference_from_payload(payload.subject)
            if subj:
                fragment["subject"] = subj

    if "encounter" in provided:
        touched.add("encounter")
        if payload.encounter is not None:
            enc = _reference_from_payload(payload.encounter)
            if enc:
                fragment["encounter"] = enc

    if set(provided.keys()) & _ONSET_FIELDS:
        touched.update(_ONSET_FHIR_KEYS)
        onset = _onset_choice_from_payload(payload)
        if onset:
            fragment[onset[0]] = onset[1]

    if set(provided.keys()) & _ABATEMENT_FIELDS:
        touched.update(_ABATEMENT_FHIR_KEYS)
        abatement = _abatement_choice_from_payload(payload)
        if abatement:
            fragment[abatement[0]] = abatement[1]

    if "recorded_date" in provided:
        touched.add("recordedDate")
        if payload.recorded_date:
            fragment["recordedDate"] = payload.recorded_date.isoformat()

    if "recorder" in provided:
        touched.add("recorder")
        if payload.recorder is not None:
            recorder = _reference_from_payload(payload.recorder)
            if recorder:
                fragment["recorder"] = recorder

    if "asserter" in provided:
        touched.add("asserter")
        if payload.asserter is not None:
            asserter = _reference_from_payload(payload.asserter)
            if asserter:
                fragment["asserter"] = asserter

    if "stage" in provided:
        touched.add("stage")
        if payload.stage is not None:
            stages = [payload_condition_stage(s) for s in payload.stage]
            stages = [s for s in stages if s]
            if stages:
                fragment["stage"] = stages

    if "evidence" in provided:
        touched.add("evidence")
        if payload.evidence is not None:
            evidence = [payload_condition_evidence(e) for e in payload.evidence]
            evidence = [e for e in evidence if e]
            if evidence:
                fragment["evidence"] = evidence

    if "note" in provided:
        touched.add("note")
        if payload.note is not None:
            notes = [payload_condition_note(n) for n in payload.note]
            notes = [n for n in notes if n]
            if notes:
                fragment["note"] = notes

    return fragment, touched
