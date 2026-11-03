"""Payload -> FHIR JSON conversion for MedicationDispense.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(MedicationDispenseCreateSchema / MedicationDispensePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.medication_dispense.input import (
        MedicationDispenseAuthorizingPrescriptionInput,
        MedicationDispenseCodeableConceptInput,
        MedicationDispenseCreateSchema,
        MedicationDispenseDetectedIssueInput,
        MedicationDispenseDosageInstructionInput,
        MedicationDispenseEventHistoryInput,
        MedicationDispenseIdentifierInput,
        MedicationDispenseNoteInput,
        MedicationDispensePartOfInput,
        MedicationDispensePatchSchema,
        MedicationDispensePerformerInput,
        MedicationDispenseReceiverInput,
        MedicationDispenseSubstitutionInput,
        MedicationDispenseSupportingInfoInput,
    )

_STATUS_REASON_FIELDS = {
    "status_reason_codeable_concept",
    "status_reason_reference",
    "status_reason_reference_display",
    "status_reason_reference_identifier_use",
    "status_reason_reference_identifier_type_system",
    "status_reason_reference_identifier_type_version",
    "status_reason_reference_identifier_type_code",
    "status_reason_reference_identifier_type_display",
    "status_reason_reference_identifier_type_user_selected",
    "status_reason_reference_identifier_type_text",
    "status_reason_reference_identifier_system",
    "status_reason_reference_identifier_value",
    "status_reason_reference_identifier_period_start",
    "status_reason_reference_identifier_period_end",
}
_STATUS_REASON_FHIR_KEYS = {"statusReasonCodeableConcept", "statusReasonReference"}

_MEDICATION_FIELDS = {
    "medication_codeable_concept",
    "medication_reference",
    "medication_display",
    "medication_identifier_use",
    "medication_identifier_type_system",
    "medication_identifier_type_version",
    "medication_identifier_type_code",
    "medication_identifier_type_display",
    "medication_identifier_type_user_selected",
    "medication_identifier_type_text",
    "medication_identifier_system",
    "medication_identifier_value",
    "medication_identifier_period_start",
    "medication_identifier_period_end",
}
_MEDICATION_FHIR_KEYS = {"medicationCodeableConcept", "medicationReference"}

_SUBJECT_FIELDS = {
    "subject",
    "subject_display",
    "subject_identifier_use",
    "subject_identifier_type_system",
    "subject_identifier_type_version",
    "subject_identifier_type_code",
    "subject_identifier_type_display",
    "subject_identifier_type_user_selected",
    "subject_identifier_type_text",
    "subject_identifier_system",
    "subject_identifier_value",
    "subject_identifier_period_start",
    "subject_identifier_period_end",
}
_SUBJECT_FHIR_KEYS = {"subject"}

_CONTEXT_FIELDS = {
    "context",
    "context_display",
    "context_identifier_use",
    "context_identifier_type_system",
    "context_identifier_type_version",
    "context_identifier_type_code",
    "context_identifier_type_display",
    "context_identifier_type_user_selected",
    "context_identifier_type_text",
    "context_identifier_system",
    "context_identifier_value",
    "context_identifier_period_start",
    "context_identifier_period_end",
}
_CONTEXT_FHIR_KEYS = {"context"}

_LOCATION_FIELDS = {
    "location",
    "location_display",
    "location_identifier_use",
    "location_identifier_type_system",
    "location_identifier_type_version",
    "location_identifier_type_code",
    "location_identifier_type_display",
    "location_identifier_type_user_selected",
    "location_identifier_type_text",
    "location_identifier_system",
    "location_identifier_value",
    "location_identifier_period_start",
    "location_identifier_period_end",
}
_LOCATION_FHIR_KEYS = {"location"}

_DESTINATION_FIELDS = {
    "destination",
    "destination_display",
    "destination_identifier_use",
    "destination_identifier_type_system",
    "destination_identifier_type_version",
    "destination_identifier_type_code",
    "destination_identifier_type_display",
    "destination_identifier_type_user_selected",
    "destination_identifier_type_text",
    "destination_identifier_system",
    "destination_identifier_value",
    "destination_identifier_period_start",
    "destination_identifier_period_end",
}
_DESTINATION_FHIR_KEYS = {"destination"}

_QUANTITY_FIELDS = {"quantity_value", "quantity_unit", "quantity_system", "quantity_code"}
_QUANTITY_FHIR_KEYS = {"quantity"}

_DAYS_SUPPLY_FIELDS = {"days_supply_value", "days_supply_unit", "days_supply_system", "days_supply_code"}
_DAYS_SUPPLY_FHIR_KEYS = {"daysSupply"}


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _payload_coding_list(codings: list | None) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": _val(c, "system"),
                "version": _val(c, "version"),
                "code": _val(c, "code"),
                "display": _val(c, "display"),
                "userSelected": _val(c, "user_selected"),
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def payload_medication_dispense_codeable_concept(
    cc: MedicationDispenseCodeableConceptInput | dict | None,
) -> dict | None:
    if not cc:
        return None
    coding_list = _payload_coding_list(_val(cc, "coding"))
    text = _val(cc, "text")
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _reference_with_prefix_from_payload(obj: Any, prefix: str) -> dict | None:
    if not obj:
        return None
    ref = _val(obj, prefix) or _val(obj, f"{prefix}_reference")
    display = _val(obj, f"{prefix}_display")

    id_use = _val(obj, f"{prefix}_identifier_use")
    id_type_system = _val(obj, f"{prefix}_identifier_type_system")
    id_type_version = _val(obj, f"{prefix}_identifier_type_version")
    id_type_code = _val(obj, f"{prefix}_identifier_type_code")
    id_type_display = _val(obj, f"{prefix}_identifier_type_display")
    id_type_user_selected = _val(obj, f"{prefix}_identifier_type_user_selected")
    id_type_text = _val(obj, f"{prefix}_identifier_type_text")
    id_system = _val(obj, f"{prefix}_identifier_system")
    id_value = _val(obj, f"{prefix}_identifier_value")
    id_period_start = _val(obj, f"{prefix}_identifier_period_start")
    id_period_end = _val(obj, f"{prefix}_identifier_period_end")

    entry: dict = {}
    if ref:
        entry["reference"] = ref
    if display:
        entry["display"] = display

    if (
        id_use
        or id_type_system
        or id_type_version
        or id_type_code
        or id_type_display
        or id_type_user_selected
        or id_type_text
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = id_use.value if hasattr(id_use, "value") else str(id_use)
        if (
            id_type_system
            or id_type_code
            or id_type_text
            or id_type_display
            or id_type_version
            or id_type_user_selected
        ):
            type_coding: dict = {}
            if id_type_system:
                type_coding["system"] = id_type_system
            if id_type_code:
                type_coding["code"] = id_type_code
            if id_type_display:
                type_coding["display"] = id_type_display
            if id_type_version:
                type_coding["version"] = id_type_version
            if id_type_user_selected is not None:
                type_coding["userSelected"] = id_type_user_selected
            t: dict = {}
            if type_coding:
                t["coding"] = [type_coding]
            if id_type_text:
                t["text"] = id_type_text
            if t:
                identifier["type"] = t
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        period: dict = {}
        if id_period_start:
            period["start"] = (
                id_period_start.isoformat()
                if hasattr(id_period_start, "isoformat")
                else str(id_period_start)
            )
        if id_period_end:
            period["end"] = (
                id_period_end.isoformat()
                if hasattr(id_period_end, "isoformat")
                else str(id_period_end)
            )
        if period:
            identifier["period"] = period
        if identifier:
            entry["identifier"] = identifier

    return entry or None


def _reference_from_child_payload(child: Any) -> dict | None:
    return _reference_with_prefix_from_payload(child, "reference")


def payload_medication_dispense_identifier(i: MedicationDispenseIdentifierInput) -> dict:
    entry: dict = {}
    use = _val(i, "use")
    if use:
        entry["use"] = use.value if hasattr(use, "value") else str(use)
    type_cc = payload_medication_dispense_codeable_concept(_val(i, "type"))
    if type_cc:
        entry["type"] = type_cc
    system = _val(i, "system")
    if system:
        entry["system"] = system
    value = _val(i, "value")
    if value:
        entry["value"] = value
    period_start = _val(i, "period_start")
    period_end = _val(i, "period_end")
    period: dict = {}
    if period_start:
        period["start"] = (
            period_start.isoformat()
            if hasattr(period_start, "isoformat")
            else str(period_start)
        )
    if period_end:
        period["end"] = (
            period_end.isoformat()
            if hasattr(period_end, "isoformat")
            else str(period_end)
        )
    if period:
        entry["period"] = period
    assigner = _reference_with_prefix_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def _payload_quantity(obj: Any, prefix: str) -> dict | None:
    val = _val(obj, f"{prefix}_value")
    unit = _val(obj, f"{prefix}_unit")
    system = _val(obj, f"{prefix}_system")
    code = _val(obj, f"{prefix}_code")
    if val is None and not unit and not system and not code:
        return None
    res: dict = {}
    if val is not None:
        res["value"] = float(val)
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def payload_medication_dispense_performer(p: MedicationDispensePerformerInput) -> dict:
    entry: dict = {}
    func = payload_medication_dispense_codeable_concept(_val(p, "function"))
    if func:
        entry["function"] = func
    actor = _reference_with_prefix_from_payload(p, "actor")
    if actor:
        entry["actor"] = actor
    return entry


def payload_medication_dispense_note(n: MedicationDispenseNoteInput) -> dict:
    entry: dict = {}
    author_ref = _reference_with_prefix_from_payload(n, "author")
    author_str = _val(n, "author_string")
    if author_ref:
        entry["authorReference"] = author_ref
    elif author_str:
        entry["authorString"] = author_str
    time_val = _val(n, "time")
    if time_val:
        entry["time"] = (
            time_val.isoformat() if hasattr(time_val, "isoformat") else str(time_val)
        )
    text = _val(n, "text")
    if text:
        entry["text"] = text
    return entry


def payload_medication_dispense_dosage_instruction(
    d: MedicationDispenseDosageInstructionInput,
) -> dict:
    entry: dict = {}
    seq = _val(d, "sequence")
    if seq is not None:
        entry["sequence"] = seq
    text = _val(d, "text")
    if text:
        entry["text"] = text
    additional_instructions = [
        payload_medication_dispense_codeable_concept(ai)
        for ai in (_val(d, "additional_instruction") or [])
    ]
    additional_instructions = [ai for ai in additional_instructions if ai]
    if additional_instructions:
        entry["additionalInstruction"] = additional_instructions
    patient_inst = _val(d, "patient_instruction")
    if patient_inst:
        entry["patientInstruction"] = patient_inst
    timing = _val(d, "timing")
    if timing:
        entry["timing"] = dict(timing)

    as_needed_bool = _val(d, "as_needed_boolean")
    if as_needed_bool is not None:
        entry["asNeededBoolean"] = as_needed_bool
    else:
        as_needed_cc = payload_medication_dispense_codeable_concept(
            _val(d, "as_needed_codeable_concept")
        )
        if as_needed_cc:
            entry["asNeededCodeableConcept"] = as_needed_cc

    site = payload_medication_dispense_codeable_concept(_val(d, "site"))
    if site:
        entry["site"] = site
    route = payload_medication_dispense_codeable_concept(_val(d, "route"))
    if route:
        entry["route"] = route
    method = payload_medication_dispense_codeable_concept(_val(d, "method"))
    if method:
        entry["method"] = method

    dose_and_rate = _val(d, "dose_and_rate")
    if dose_and_rate:
        entry["doseAndRate"] = list(dose_and_rate)
    max_dose_period = _val(d, "max_dose_per_period")
    if max_dose_period:
        entry["maxDosePerPeriod"] = dict(max_dose_period)

    max_dose_admin = _payload_quantity(d, "max_dose_per_administration")
    if max_dose_admin:
        entry["maxDosePerAdministration"] = max_dose_admin
    max_dose_life = _payload_quantity(d, "max_dose_per_lifetime")
    if max_dose_life:
        entry["maxDosePerLifetime"] = max_dose_life

    return entry


def payload_medication_dispense_substitution(
    sub: MedicationDispenseSubstitutionInput | None,
) -> dict | None:
    if not sub:
        return None
    entry: dict = {
        "wasSubstituted": bool(_val(sub, "was_substituted"))
        if _val(sub, "was_substituted") is not None
        else False
    }
    type_cc = payload_medication_dispense_codeable_concept(_val(sub, "type"))
    if type_cc:
        entry["type"] = type_cc
    reasons = [
        payload_medication_dispense_codeable_concept(r)
        for r in (_val(sub, "reason") or [])
    ]
    reasons = [r for r in reasons if r]
    if reasons:
        entry["reason"] = reasons

    parties = [
        _reference_from_child_payload(rp)
        for rp in (_val(sub, "responsible_party") or [])
    ]
    parties = [p for p in parties if p]
    if parties:
        entry["responsibleParty"] = parties

    return entry


def payload_to_fhir_medication_dispense(payload: MedicationDispenseCreateSchema) -> dict:
    """Format a validated MedicationDispenseCreateSchema as a FHIR R4 JSON dict."""
    out: dict = {
        "resourceType": "MedicationDispense",
    }

    if payload.extension:
        out["extension"] = list(payload.extension)

    identifiers = [
        payload_medication_dispense_identifier(i)
        for i in (payload.identifier or [])
    ]
    if identifiers:
        out["identifier"] = identifiers

    part_of = [
        _reference_from_child_payload(p) for p in (payload.part_of or [])
    ]
    part_of = [p for p in part_of if p]
    if part_of:
        out["partOf"] = part_of

    out["status"] = (
        payload.status.value
        if hasattr(payload.status, "value")
        else str(payload.status)
    )

    status_reason_cc = payload_medication_dispense_codeable_concept(
        payload.status_reason_codeable_concept
    )
    if status_reason_cc:
        out["statusReasonCodeableConcept"] = status_reason_cc
    status_reason_ref = _reference_with_prefix_from_payload(
        payload, "status_reason_reference"
    )
    if status_reason_ref:
        out["statusReasonReference"] = status_reason_ref

    category = payload_medication_dispense_codeable_concept(payload.category)
    if category:
        out["category"] = category

    medication_cc = payload_medication_dispense_codeable_concept(
        payload.medication_codeable_concept
    )
    if medication_cc:
        out["medicationCodeableConcept"] = medication_cc
    medication_ref = _reference_with_prefix_from_payload(payload, "medication")
    if medication_ref:
        out["medicationReference"] = medication_ref

    subject = _reference_with_prefix_from_payload(payload, "subject")
    if subject:
        out["subject"] = subject

    context = _reference_with_prefix_from_payload(payload, "context")
    if context:
        out["context"] = context

    supporting_infos = [
        _reference_from_child_payload(s)
        for s in (payload.supporting_information or [])
    ]
    supporting_infos = [s for s in supporting_infos if s]
    if supporting_infos:
        out["supportingInformation"] = supporting_infos

    performers = [
        payload_medication_dispense_performer(p)
        for p in (payload.performer or [])
    ]
    if performers:
        out["performer"] = performers

    location = _reference_with_prefix_from_payload(payload, "location")
    if location:
        out["location"] = location

    authorizing_prescriptions = [
        _reference_from_child_payload(a)
        for a in (payload.authorizing_prescription or [])
    ]
    authorizing_prescriptions = [a for a in authorizing_prescriptions if a]
    if authorizing_prescriptions:
        out["authorizingPrescription"] = authorizing_prescriptions

    dispense_type = payload_medication_dispense_codeable_concept(payload.type)
    if dispense_type:
        out["type"] = dispense_type

    quantity = _payload_quantity(payload, "quantity")
    if quantity:
        out["quantity"] = quantity

    days_supply = _payload_quantity(payload, "days_supply")
    if days_supply:
        out["daysSupply"] = days_supply

    if payload.when_prepared:
        out["whenPrepared"] = (
            payload.when_prepared.isoformat()
            if hasattr(payload.when_prepared, "isoformat")
            else str(payload.when_prepared)
        )

    if payload.when_handed_over:
        out["whenHandedOver"] = (
            payload.when_handed_over.isoformat()
            if hasattr(payload.when_handed_over, "isoformat")
            else str(payload.when_handed_over)
        )

    destination = _reference_with_prefix_from_payload(payload, "destination")
    if destination:
        out["destination"] = destination

    receivers = [
        _reference_from_child_payload(r) for r in (payload.receiver or [])
    ]
    receivers = [r for r in receivers if r]
    if receivers:
        out["receiver"] = receivers

    notes = [
        payload_medication_dispense_note(n) for n in (payload.note or [])
    ]
    if notes:
        out["note"] = notes

    dosages = [
        payload_medication_dispense_dosage_instruction(d)
        for d in (payload.dosage_instruction or [])
    ]
    if dosages:
        out["dosageInstruction"] = dosages

    substitution = payload_medication_dispense_substitution(payload.substitution)
    if substitution:
        out["substitution"] = substitution

    detected_issues = [
        _reference_from_child_payload(d)
        for d in (payload.detected_issue or [])
    ]
    detected_issues = [d for d in detected_issues if d]
    if detected_issues:
        out["detectedIssue"] = detected_issues

    event_history = [
        _reference_from_child_payload(e)
        for e in (payload.event_history or [])
    ]
    event_history = [e for e in event_history if e]
    if event_history:
        out["eventHistory"] = event_history

    return {k: v for k, v in out.items() if v is not None}


def patch_fragment_to_fhir_medication_dispense(
    payload: MedicationDispensePatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    """Convert only the explicitly-set fields on a MedicationDispensePatchSchema into FHIR keys."""
    provided = payload.model_fields_set
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "status" in provided:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = (
                payload.status.value
                if hasattr(payload.status, "value")
                else str(payload.status)
            )

    if provided & _STATUS_REASON_FIELDS:
        touched |= _STATUS_REASON_FHIR_KEYS
        if payload.status_reason_codeable_concept:
            sr_cc = payload_medication_dispense_codeable_concept(
                payload.status_reason_codeable_concept
            )
            if sr_cc:
                fragment["statusReasonCodeableConcept"] = sr_cc
        sr_ref = _reference_with_prefix_from_payload(
            payload, "status_reason_reference"
        )
        if sr_ref:
            fragment["statusReasonReference"] = sr_ref

    if "category" in provided:
        touched.add("category")
        if payload.category:
            cat = payload_medication_dispense_codeable_concept(payload.category)
            if cat:
                fragment["category"] = cat

    if provided & _MEDICATION_FIELDS:
        touched |= _MEDICATION_FHIR_KEYS
        if payload.medication_codeable_concept:
            med_cc = payload_medication_dispense_codeable_concept(
                payload.medication_codeable_concept
            )
            if med_cc:
                fragment["medicationCodeableConcept"] = med_cc
        med_ref = _reference_with_prefix_from_payload(payload, "medication")
        if med_ref:
            fragment["medicationReference"] = med_ref

    if provided & _SUBJECT_FIELDS:
        touched |= _SUBJECT_FHIR_KEYS
        subj = _reference_with_prefix_from_payload(payload, "subject")
        if subj:
            fragment["subject"] = subj

    if provided & _CONTEXT_FIELDS:
        touched |= _CONTEXT_FHIR_KEYS
        ctx = _reference_with_prefix_from_payload(payload, "context")
        if ctx:
            fragment["context"] = ctx

    if provided & _LOCATION_FIELDS:
        touched |= _LOCATION_FHIR_KEYS
        loc = _reference_with_prefix_from_payload(payload, "location")
        if loc:
            fragment["location"] = loc

    if "type" in provided:
        touched.add("type")
        if payload.type:
            dt = payload_medication_dispense_codeable_concept(payload.type)
            if dt:
                fragment["type"] = dt

    if provided & _QUANTITY_FIELDS:
        touched |= _QUANTITY_FHIR_KEYS
        q = _payload_quantity(payload, "quantity")
        if q:
            fragment["quantity"] = q

    if provided & _DAYS_SUPPLY_FIELDS:
        touched |= _DAYS_SUPPLY_FHIR_KEYS
        ds = _payload_quantity(payload, "days_supply")
        if ds:
            fragment["daysSupply"] = ds

    if "when_prepared" in provided:
        touched.add("whenPrepared")
        if payload.when_prepared is not None:
            fragment["whenPrepared"] = (
                payload.when_prepared.isoformat()
                if hasattr(payload.when_prepared, "isoformat")
                else str(payload.when_prepared)
            )

    if "when_handed_over" in provided:
        touched.add("whenHandedOver")
        if payload.when_handed_over is not None:
            fragment["whenHandedOver"] = (
                payload.when_handed_over.isoformat()
                if hasattr(payload.when_handed_over, "isoformat")
                else str(payload.when_handed_over)
            )

    if provided & _DESTINATION_FIELDS:
        touched |= _DESTINATION_FHIR_KEYS
        dest = _reference_with_prefix_from_payload(payload, "destination")
        if dest:
            fragment["destination"] = dest

    if "substitution" in provided:
        touched.add("substitution")
        sub = payload_medication_dispense_substitution(payload.substitution)
        if sub:
            fragment["substitution"] = sub

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier:
            fragment["identifier"] = [
                payload_medication_dispense_identifier(i)
                for i in payload.identifier
            ]

    if "part_of" in provided:
        touched.add("partOf")
        if payload.part_of:
            po = [_reference_from_child_payload(p) for p in payload.part_of]
            fragment["partOf"] = [p for p in po if p]

    if "supporting_information" in provided:
        touched.add("supportingInformation")
        if payload.supporting_information:
            si = [
                _reference_from_child_payload(s)
                for s in payload.supporting_information
            ]
            fragment["supportingInformation"] = [s for s in si if s]

    if "performer" in provided:
        touched.add("performer")
        if payload.performer:
            fragment["performer"] = [
                payload_medication_dispense_performer(p)
                for p in payload.performer
            ]

    if "authorizing_prescription" in provided:
        touched.add("authorizingPrescription")
        if payload.authorizing_prescription:
            ap = [
                _reference_from_child_payload(a)
                for a in payload.authorizing_prescription
            ]
            fragment["authorizingPrescription"] = [a for a in ap if a]

    if "receiver" in provided:
        touched.add("receiver")
        if payload.receiver:
            rc = [_reference_from_child_payload(r) for r in payload.receiver]
            fragment["receiver"] = [r for r in rc if r]

    if "note" in provided:
        touched.add("note")
        if payload.note:
            fragment["note"] = [
                payload_medication_dispense_note(n) for n in payload.note
            ]

    if "dosage_instruction" in provided:
        touched.add("dosageInstruction")
        if payload.dosage_instruction:
            fragment["dosageInstruction"] = [
                payload_medication_dispense_dosage_instruction(d)
                for d in payload.dosage_instruction
            ]

    if "detected_issue" in provided:
        touched.add("detectedIssue")
        if payload.detected_issue:
            di = [_reference_from_child_payload(d) for d in payload.detected_issue]
            fragment["detectedIssue"] = [d for d in di if d]

    if "event_history" in provided:
        touched.add("eventHistory")
        if payload.event_history:
            eh = [_reference_from_child_payload(e) for e in payload.event_history]
            fragment["eventHistory"] = [e for e in eh if e]

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)

    return fragment, touched
