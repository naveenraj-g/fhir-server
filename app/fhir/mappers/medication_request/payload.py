"""Payload -> FHIR JSON conversion, the mirror image of fhir.py — see that
module's docstring pattern (e.g. app.fhir.mappers.organization.payload) for
the full reasoning. Reads the validated Pydantic input schema
(MedicationRequestCreateSchema / MedicationRequestPatchSchema and their
nested sub-schemas) rather than the persisted ORM model, before anything is
written to the DB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.medication_request.input import (
        MedicationRequestCreateSchema,
        MedicationRequestIdentifierInput,
        MedicationRequestNoteInput,
        MedicationRequestPatchSchema,
    )
    from app.schemas.medication_request.input.codeable_concept import MedicationRequestCodeableConceptInput
    from app.schemas.medication_request.input.dosage_instruction import MedicationRequestDosageInstructionInput


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


def _period(start, end) -> dict | None:
    period = {
        k: v
        for k, v in {"start": start.isoformat() if start else None, "end": end.isoformat() if end else None}.items()
        if v
    }
    return period or None


def _reference_from_payload(obj) -> dict:
    entry: dict = {}
    if getattr(obj, "reference", None):
        entry["reference"] = obj.reference
    if getattr(obj, "reference_display", None):
        entry["display"] = obj.reference_display
    return entry


def _reference_with_identifier_fallback_from_payload(obj) -> dict:
    entry = _reference_from_payload(obj)
    id_use = getattr(obj, "reference_identifier_use", None)
    id_type_system = getattr(obj, "reference_identifier_type_system", None)
    id_type_code = getattr(obj, "reference_identifier_type_code", None)
    id_type_text = getattr(obj, "reference_identifier_type_text", None)
    id_system = getattr(obj, "reference_identifier_system", None)
    id_value = getattr(obj, "reference_identifier_value", None)
    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = id_use.value if hasattr(id_use, "value") else id_use
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": getattr(obj, "reference_identifier_type_version", None),
                            "code": id_type_code,
                            "display": getattr(obj, "reference_identifier_type_display", None),
                            "userSelected": getattr(obj, "reference_identifier_type_user_selected", None),
                        }.items()
                        if v is not None
                    }
                ]
            if id_type_text:
                type_cc["text"] = id_type_text
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        period = _period(
            getattr(obj, "reference_identifier_period_start", None),
            getattr(obj, "reference_identifier_period_end", None),
        )
        if period:
            identifier["period"] = period
        entry["identifier"] = identifier
    return entry


def payload_medication_request_identifier(i: MedicationRequestIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use.value
    coding = _coding_list(i.type_coding)
    if coding or i.type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period = _period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    if i.assigner:
        assigner: dict = {"reference": i.assigner}
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        entry["assigner"] = assigner
    return entry


def payload_medication_request_codeable_concept(cc: MedicationRequestCodeableConceptInput) -> dict:
    entry: dict = {}
    coding = _coding_list(cc.coding)
    if coding:
        entry["coding"] = coding
    if cc.text:
        entry["text"] = cc.text
    return entry


def payload_medication_request_note(n: MedicationRequestNoteInput) -> dict:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference:
        ref: dict = {"reference": n.author_reference}
        if n.author_reference_display:
            ref["display"] = n.author_reference_display
        entry["authorReference"] = ref
    if n.time:
        entry["time"] = n.time.isoformat()
    if n.text:
        entry["text"] = n.text
    return entry


def payload_medication_request_dosage_instruction(d: MedicationRequestDosageInstructionInput) -> dict:
    entry: dict = {}
    if d.sequence is not None:
        entry["sequence"] = d.sequence
    if d.text:
        entry["text"] = d.text
    if d.additional_instruction:
        entry["additionalInstruction"] = [
            payload_medication_request_codeable_concept(ai) for ai in d.additional_instruction
        ]
    if d.patient_instruction:
        entry["patientInstruction"] = d.patient_instruction
    if d.timing:
        entry["timing"] = dict(d.timing)

    if d.as_needed_boolean is not None:
        entry["asNeededBoolean"] = d.as_needed_boolean
    elif d.as_needed_codeable_concept:
        cc = payload_medication_request_codeable_concept(d.as_needed_codeable_concept)
        if cc:
            entry["asNeededCodeableConcept"] = cc

    if d.site:
        site = payload_medication_request_codeable_concept(d.site)
        if site:
            entry["site"] = site
    if d.route:
        route = payload_medication_request_codeable_concept(d.route)
        if route:
            entry["route"] = route
    if d.method:
        method = payload_medication_request_codeable_concept(d.method)
        if method:
            entry["method"] = method

    if d.dose_and_rate:
        entry["doseAndRate"] = list(d.dose_and_rate)
    if d.max_dose_per_period:
        entry["maxDosePerPeriod"] = dict(d.max_dose_per_period)

    max_dose_per_administration = {
        k: v
        for k, v in {
            "value": d.max_dose_per_administration_value,
            "unit": d.max_dose_per_administration_unit,
            "system": d.max_dose_per_administration_system,
            "code": d.max_dose_per_administration_code,
        }.items()
        if v is not None
    }
    if max_dose_per_administration:
        entry["maxDosePerAdministration"] = max_dose_per_administration

    max_dose_per_lifetime = {
        k: v
        for k, v in {
            "value": d.max_dose_per_lifetime_value,
            "unit": d.max_dose_per_lifetime_unit,
            "system": d.max_dose_per_lifetime_system,
            "code": d.max_dose_per_lifetime_code,
        }.items()
        if v is not None
    }
    if max_dose_per_lifetime:
        entry["maxDosePerLifetime"] = max_dose_per_lifetime

    return entry


def _dispense_request_choice(payload) -> dict | None:
    entry: dict = {}
    initial_fill: dict = {}
    qty = {
        k: v
        for k, v in {
            "value": payload.dispense_request_initial_fill_quantity_value,
            "comparator": payload.dispense_request_initial_fill_quantity_comparator.value
            if payload.dispense_request_initial_fill_quantity_comparator
            else None,
            "unit": payload.dispense_request_initial_fill_quantity_unit,
            "system": payload.dispense_request_initial_fill_quantity_system,
            "code": payload.dispense_request_initial_fill_quantity_code,
        }.items()
        if v is not None
    }
    if qty:
        initial_fill["quantity"] = qty
    dur = {
        k: v
        for k, v in {
            "value": payload.dispense_request_initial_fill_duration_value,
            "unit": payload.dispense_request_initial_fill_duration_unit,
            "system": payload.dispense_request_initial_fill_duration_system,
            "code": payload.dispense_request_initial_fill_duration_code,
        }.items()
        if v is not None
    }
    if dur:
        initial_fill["duration"] = dur
    if initial_fill:
        entry["initialFill"] = initial_fill

    dispense_interval = {
        k: v
        for k, v in {
            "value": payload.dispense_request_dispense_interval_value,
            "unit": payload.dispense_request_dispense_interval_unit,
            "system": payload.dispense_request_dispense_interval_system,
            "code": payload.dispense_request_dispense_interval_code,
        }.items()
        if v is not None
    }
    if dispense_interval:
        entry["dispenseInterval"] = dispense_interval

    period = _period(payload.dispense_request_validity_period_start, payload.dispense_request_validity_period_end)
    if period:
        entry["validityPeriod"] = period
    if payload.dispense_request_number_of_repeats_allowed is not None:
        entry["numberOfRepeatsAllowed"] = payload.dispense_request_number_of_repeats_allowed

    quantity = {
        k: v
        for k, v in {
            "value": payload.dispense_request_quantity_value,
            "unit": payload.dispense_request_quantity_unit,
            "system": payload.dispense_request_quantity_system,
            "code": payload.dispense_request_quantity_code,
        }.items()
        if v is not None
    }
    if quantity:
        entry["quantity"] = quantity

    expected_supply_duration = {
        k: v
        for k, v in {
            "value": payload.dispense_request_expected_supply_duration_value,
            "unit": payload.dispense_request_expected_supply_duration_unit,
            "system": payload.dispense_request_expected_supply_duration_system,
            "code": payload.dispense_request_expected_supply_duration_code,
        }.items()
        if v is not None
    }
    if expected_supply_duration:
        entry["expectedSupplyDuration"] = expected_supply_duration

    if payload.dispense_request_performer:
        performer = _reference_with_identifier_fallback_from_payload(payload.dispense_request_performer)
        if performer:
            entry["performer"] = performer

    return entry or None


def _substitution_choice(payload) -> dict | None:
    entry: dict = {}
    if payload.substitution_allowed_boolean is not None:
        entry["allowedBoolean"] = payload.substitution_allowed_boolean
    elif payload.substitution_allowed_codeable_concept:
        cc = payload_medication_request_codeable_concept(payload.substitution_allowed_codeable_concept)
        if cc:
            entry["allowedCodeableConcept"] = cc
    if payload.substitution_reason:
        reason = payload_medication_request_codeable_concept(payload.substitution_reason)
        if reason:
            entry["reason"] = reason
    return entry or None


# field -> (fhir key, builder) for every plain 0..* list on this resource.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_medication_request_identifier),
    "category": ("category", payload_medication_request_codeable_concept),
    "reason_code": ("reasonCode", payload_medication_request_codeable_concept),
    "reason_reference": ("reasonReference", _reference_with_identifier_fallback_from_payload),
    "based_on": ("basedOn", _reference_with_identifier_fallback_from_payload),
    "insurance": ("insurance", _reference_with_identifier_fallback_from_payload),
    "supporting_information": ("supportingInformation", _reference_with_identifier_fallback_from_payload),
    "note": ("note", payload_medication_request_note),
    "dosage_instruction": ("dosageInstruction", payload_medication_request_dosage_instruction),
    "detected_issue": ("detectedIssue", _reference_with_identifier_fallback_from_payload),
    "event_history": ("eventHistory", _reference_with_identifier_fallback_from_payload),
}

_SINGLE_REFERENCE_FIELDS = {
    "subject": "subject",
    "encounter": "encounter",
    "requester": "requester",
    "performer": "performer",
    "recorder": "recorder",
    "prior_prescription": "priorPrescription",
}
_SINGLE_CC_FIELDS = {
    "status_reason": "statusReason",
    "performer_type": "performerType",
    "course_of_therapy_type": "courseOfTherapyType",
}

_DISPENSE_REQUEST_FIELDS = {
    "dispense_request_initial_fill_quantity_value", "dispense_request_initial_fill_quantity_comparator",
    "dispense_request_initial_fill_quantity_unit", "dispense_request_initial_fill_quantity_system",
    "dispense_request_initial_fill_quantity_code", "dispense_request_initial_fill_duration_value",
    "dispense_request_initial_fill_duration_unit", "dispense_request_initial_fill_duration_system",
    "dispense_request_initial_fill_duration_code", "dispense_request_dispense_interval_value",
    "dispense_request_dispense_interval_unit", "dispense_request_dispense_interval_system",
    "dispense_request_dispense_interval_code", "dispense_request_validity_period_start",
    "dispense_request_validity_period_end", "dispense_request_number_of_repeats_allowed",
    "dispense_request_quantity_value", "dispense_request_quantity_unit", "dispense_request_quantity_system",
    "dispense_request_quantity_code", "dispense_request_expected_supply_duration_value",
    "dispense_request_expected_supply_duration_unit", "dispense_request_expected_supply_duration_system",
    "dispense_request_expected_supply_duration_code", "dispense_request_performer",
}
_SUBSTITUTION_FIELDS = {"substitution_allowed_boolean", "substitution_allowed_codeable_concept", "substitution_reason"}


def payload_to_fhir_medication_request(payload: MedicationRequestCreateSchema) -> dict:
    """Full-resource conversion for CREATE: every field is considered present."""
    result: dict = {"resourceType": "MedicationRequest"}

    if payload.extension:
        result["extension"] = list(payload.extension)

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [i for i in items if i]
        if items:
            result[fhir_key] = items

    if payload.status:
        result["status"] = payload.status.value
    if payload.intent:
        result["intent"] = payload.intent.value
    if payload.priority:
        result["priority"] = payload.priority.value
    if payload.do_not_perform is not None:
        result["doNotPerform"] = payload.do_not_perform

    if payload.reported_boolean is not None:
        result["reportedBoolean"] = payload.reported_boolean
    elif payload.reported_reference:
        ref = _reference_with_identifier_fallback_from_payload(payload.reported_reference)
        if ref:
            result["reportedReference"] = ref

    if payload.medication_codeable_concept:
        cc = payload_medication_request_codeable_concept(payload.medication_codeable_concept)
        if cc:
            result["medicationCodeableConcept"] = cc
    elif payload.medication_reference:
        ref = _reference_with_identifier_fallback_from_payload(payload.medication_reference)
        if ref:
            result["medicationReference"] = ref

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            ref = _reference_with_identifier_fallback_from_payload(obj)
            if ref:
                result[fhir_key] = ref

    for field, fhir_key in _SINGLE_CC_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            cc = payload_medication_request_codeable_concept(obj)
            if cc:
                result[fhir_key] = cc

    if payload.instantiates_canonical:
        result["instantiatesCanonical"] = list(payload.instantiates_canonical)
    if payload.instantiates_uri:
        result["instantiatesUri"] = list(payload.instantiates_uri)
    if payload.group_identifier:
        gi = payload_medication_request_identifier(payload.group_identifier)
        if gi:
            result["groupIdentifier"] = gi

    if payload.authored_on:
        result["authoredOn"] = payload.authored_on.isoformat()

    dispense_request = _dispense_request_choice(payload)
    if dispense_request:
        result["dispenseRequest"] = dispense_request

    substitution = _substitution_choice(payload)
    if substitution:
        result["substitution"] = substitution

    return result


def patch_fragment_to_fhir_medication_request(payload: MedicationRequestPatchSchema) -> tuple[dict, set[str]]:
    """Tri-state conversion for PATCH."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [i for i in items if i]
            if items:
                fragment[fhir_key] = items

    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = payload.status.value
    if "intent" in provided:
        touched.add("intent")
        if payload.intent:
            fragment["intent"] = payload.intent.value
    if "priority" in provided:
        touched.add("priority")
        if payload.priority:
            fragment["priority"] = payload.priority.value
    if "do_not_perform" in provided:
        touched.add("doNotPerform")
        if payload.do_not_perform is not None:
            fragment["doNotPerform"] = payload.do_not_perform

    if provided & {"reported_boolean", "reported_reference"}:
        touched.add("reportedBoolean")
        touched.add("reportedReference")
        if payload.reported_boolean is not None:
            fragment["reportedBoolean"] = payload.reported_boolean
        elif payload.reported_reference:
            ref = _reference_with_identifier_fallback_from_payload(payload.reported_reference)
            if ref:
                fragment["reportedReference"] = ref

    if provided & {"medication_codeable_concept", "medication_reference"}:
        touched.add("medicationCodeableConcept")
        touched.add("medicationReference")
        if payload.medication_codeable_concept:
            cc = payload_medication_request_codeable_concept(payload.medication_codeable_concept)
            if cc:
                fragment["medicationCodeableConcept"] = cc
        elif payload.medication_reference:
            ref = _reference_with_identifier_fallback_from_payload(payload.medication_reference)
            if ref:
                fragment["medicationReference"] = ref

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                ref = _reference_with_identifier_fallback_from_payload(obj)
                if ref:
                    fragment[fhir_key] = ref

    for field, fhir_key in _SINGLE_CC_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                cc = payload_medication_request_codeable_concept(obj)
                if cc:
                    fragment[fhir_key] = cc

    if "instantiates_canonical" in provided:
        touched.add("instantiatesCanonical")
        if payload.instantiates_canonical:
            fragment["instantiatesCanonical"] = list(payload.instantiates_canonical)
    if "instantiates_uri" in provided:
        touched.add("instantiatesUri")
        if payload.instantiates_uri:
            fragment["instantiatesUri"] = list(payload.instantiates_uri)
    if "group_identifier" in provided:
        touched.add("groupIdentifier")
        if payload.group_identifier:
            gi = payload_medication_request_identifier(payload.group_identifier)
            if gi:
                fragment["groupIdentifier"] = gi

    if "authored_on" in provided:
        touched.add("authoredOn")
        if payload.authored_on:
            fragment["authoredOn"] = payload.authored_on.isoformat()

    if provided & _DISPENSE_REQUEST_FIELDS:
        touched.add("dispenseRequest")
        dispense_request = _dispense_request_choice(payload)
        if dispense_request:
            fragment["dispenseRequest"] = dispense_request

    if provided & _SUBSTITUTION_FIELDS:
        touched.add("substitution")
        substitution = _substitution_choice(payload)
        if substitution:
            fragment["substitution"] = substitution

    return fragment, touched
