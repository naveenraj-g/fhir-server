from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.medication_request import MedicationRequestModel

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


def _fhir_coding_list(codings) -> list[dict]:
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


def _fhir_reference(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    entry = _fhir_reference(obj, prefix)

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": id_type_version,
                            "code": id_type_code,
                            "display": id_type_display,
                            "userSelected": id_type_user_selected,
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
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {"start": fhir_instant(id_period_start), "end": fhir_instant(id_period_end)}.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def _fhir_quantity(obj, prefix: str) -> dict:
    value = getattr(obj, f"{prefix}_value", None)
    comparator = getattr(obj, f"{prefix}_comparator", None)
    return {
        k: v
        for k, v in {
            "value": float(value) if value is not None else None,
            "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(comparator)) if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }


def fhir_medication_request_identifier(obj, prefix: str = "") -> dict:
    """Renders either a full MedicationRequestIdentifier child row
    (prefix="") or the main row's flattened `group_identifier_*` columns
    (prefix="group_identifier_") into a FHIR Identifier dict."""
    p = prefix
    entry: dict = {}
    use = getattr(obj, f"{p}use", None)
    if use:
        entry["use"] = fhir_enum(use)
    codings_attr = f"{p}type_codings" if p else "type_codings"
    coding = _fhir_coding_list(getattr(obj, codings_attr, None))
    type_text = getattr(obj, f"{p}type_text", None)
    if coding or type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if type_text:
            type_cc["text"] = type_text
        entry["type"] = type_cc
    system = getattr(obj, f"{p}system", None)
    if system:
        entry["system"] = system
    value = getattr(obj, f"{p}value", None)
    if value:
        entry["value"] = value
    period_start = getattr(obj, f"{p}period_start", None)
    period_end = getattr(obj, f"{p}period_end", None)
    if period_start or period_end:
        entry["period"] = {
            k: v for k, v in {"start": fhir_instant(period_start), "end": fhir_instant(period_end)}.items() if v
        }
    assigner = _fhir_reference_with_identifier_fallback(obj, f"{p}assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_medication_request_codeable_concept(codings, text: str | None) -> dict:
    """Generic CodeableConcept renderer — reused for every plain {coding[],
    text} field on this resource."""
    entry: dict = {}
    coding = _fhir_coding_list(codings)
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def fhir_medication_request_note(n) -> dict:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        ref = _fhir_reference(n, "author")
        if ref:
            entry["authorReference"] = ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry


def fhir_medication_request_dosage_instruction(d) -> dict:
    entry: dict = {}
    if d.sequence is not None:
        entry["sequence"] = d.sequence
    if d.text:
        entry["text"] = d.text
    additional_instructions = [
        fhir_medication_request_codeable_concept(ai.codings, ai.text) for ai in (d.additional_instructions or [])
    ]
    additional_instructions = [ai for ai in additional_instructions if ai]
    if additional_instructions:
        entry["additionalInstruction"] = additional_instructions
    if d.patient_instruction:
        entry["patientInstruction"] = d.patient_instruction
    if d.timing:
        entry["timing"] = dict(d.timing)

    if d.as_needed_boolean is not None:
        entry["asNeededBoolean"] = d.as_needed_boolean
    else:
        as_needed_cc = fhir_medication_request_codeable_concept(d.as_needed_codings, d.as_needed_codeable_concept_text)
        if as_needed_cc:
            entry["asNeededCodeableConcept"] = as_needed_cc

    site = fhir_medication_request_codeable_concept(d.site_codings, d.site_text)
    if site:
        entry["site"] = site
    route = fhir_medication_request_codeable_concept(d.route_codings, d.route_text)
    if route:
        entry["route"] = route
    method = fhir_medication_request_codeable_concept(d.method_codings, d.method_text)
    if method:
        entry["method"] = method

    if d.dose_and_rate:
        entry["doseAndRate"] = list(d.dose_and_rate)
    if d.max_dose_per_period:
        entry["maxDosePerPeriod"] = dict(d.max_dose_per_period)

    max_dose_per_administration = _fhir_quantity(d, "max_dose_per_administration")
    if max_dose_per_administration:
        entry["maxDosePerAdministration"] = max_dose_per_administration
    max_dose_per_lifetime = _fhir_quantity(d, "max_dose_per_lifetime")
    if max_dose_per_lifetime:
        entry["maxDosePerLifetime"] = max_dose_per_lifetime

    return entry


_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(mr: MedicationRequestModel) -> dict:
    meta: dict = {}
    if mr.updated_at:
        meta["lastUpdated"] = fhir_instant(mr.updated_at)
    extensions = []
    if mr.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": mr.tenant_id})
    if mr.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": mr.created_by})
    if mr.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": mr.updated_by})
    if mr.created_at:
        extensions.append({"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(mr.created_at)})
    if extensions:
        meta["extension"] = extensions
    return meta


def _fhir_dispense_request(mr: MedicationRequestModel) -> dict:
    entry: dict = {}
    initial_fill: dict = {}
    qty = _fhir_quantity(mr, "dispense_request_initial_fill_quantity")
    if qty:
        initial_fill["quantity"] = qty
    dur = _fhir_quantity(mr, "dispense_request_initial_fill_duration")
    if dur:
        initial_fill["duration"] = dur
    if initial_fill:
        entry["initialFill"] = initial_fill

    dispense_interval = _fhir_quantity(mr, "dispense_request_dispense_interval")
    if dispense_interval:
        entry["dispenseInterval"] = dispense_interval

    if mr.dispense_request_validity_period_start or mr.dispense_request_validity_period_end:
        entry["validityPeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(mr.dispense_request_validity_period_start),
                "end": fhir_instant(mr.dispense_request_validity_period_end),
            }.items()
            if v
        }
    if mr.dispense_request_number_of_repeats_allowed is not None:
        entry["numberOfRepeatsAllowed"] = mr.dispense_request_number_of_repeats_allowed

    quantity = _fhir_quantity(mr, "dispense_request_quantity")
    if quantity:
        entry["quantity"] = quantity

    expected_supply_duration = _fhir_quantity(mr, "dispense_request_expected_supply_duration")
    if expected_supply_duration:
        entry["expectedSupplyDuration"] = expected_supply_duration

    performer = _fhir_reference_with_identifier_fallback(mr, "dispense_request_performer")
    if performer:
        entry["performer"] = performer

    return entry


def _fhir_substitution(mr: MedicationRequestModel) -> dict:
    entry: dict = {}
    if mr.substitution_allowed_boolean is not None:
        entry["allowedBoolean"] = mr.substitution_allowed_boolean
    else:
        allowed_cc = fhir_medication_request_codeable_concept(
            mr.substitution_allowed_codings, mr.substitution_allowed_codeable_concept_text
        )
        if allowed_cc:
            entry["allowedCodeableConcept"] = allowed_cc
    reason = fhir_medication_request_codeable_concept(mr.substitution_reason_codings, mr.substitution_reason_text)
    if reason:
        entry["reason"] = reason
    return entry


def to_fhir_medication_request(mr: MedicationRequestModel) -> dict:
    result: dict = {"resourceType": "MedicationRequest", "id": str(mr.medication_request_id)}

    meta = _fhir_meta(mr)
    if meta:
        result["meta"] = meta
    if mr.extension:
        result["extension"] = list(mr.extension)

    identifiers = [fhir_medication_request_identifier(i) for i in (mr.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if mr.status:
        result["status"] = fhir_enum(mr.status).replace("_", "-")

    status_reason = fhir_medication_request_codeable_concept(mr.status_reason_codings, mr.status_reason_text)
    if status_reason:
        result["statusReason"] = status_reason

    if mr.intent:
        result["intent"] = fhir_enum(mr.intent).replace("_", "-")

    categories = [fhir_medication_request_codeable_concept(c.codings, c.text) for c in (mr.categories or [])]
    categories = [c for c in categories if c]
    if categories:
        result["category"] = categories

    if mr.priority:
        result["priority"] = fhir_enum(mr.priority)
    if mr.do_not_perform is not None:
        result["doNotPerform"] = mr.do_not_perform

    if mr.reported_boolean is not None:
        result["reportedBoolean"] = mr.reported_boolean
    else:
        reported_ref = _fhir_reference_with_identifier_fallback(mr, "reported_reference")
        if reported_ref:
            result["reportedReference"] = reported_ref

    medication_cc = fhir_medication_request_codeable_concept(mr.medication_codings, mr.medication_codeable_concept_text)
    if medication_cc:
        result["medicationCodeableConcept"] = medication_cc
    else:
        medication_ref = _fhir_reference_with_identifier_fallback(mr, "medication_reference")
        if medication_ref:
            result["medicationReference"] = medication_ref

    subject = _fhir_reference_with_identifier_fallback(mr, "subject")
    if subject:
        result["subject"] = subject

    encounter = _fhir_reference_with_identifier_fallback(mr, "encounter")
    if encounter:
        result["encounter"] = encounter

    supporting_infos = [
        _fhir_reference_with_identifier_fallback(si, "reference") for si in (mr.supporting_informations or [])
    ]
    supporting_infos = [si for si in supporting_infos if si]
    if supporting_infos:
        result["supportingInformation"] = supporting_infos

    if mr.authored_on:
        result["authoredOn"] = fhir_instant(mr.authored_on)

    requester = _fhir_reference_with_identifier_fallback(mr, "requester")
    if requester:
        result["requester"] = requester

    performer = _fhir_reference_with_identifier_fallback(mr, "performer")
    if performer:
        result["performer"] = performer

    performer_type = fhir_medication_request_codeable_concept(mr.performer_type_codings, mr.performer_type_text)
    if performer_type:
        result["performerType"] = performer_type

    recorder = _fhir_reference_with_identifier_fallback(mr, "recorder")
    if recorder:
        result["recorder"] = recorder

    reason_codes = [fhir_medication_request_codeable_concept(rc.codings, rc.text) for rc in (mr.reason_codes or [])]
    reason_codes = [rc for rc in reason_codes if rc]
    if reason_codes:
        result["reasonCode"] = reason_codes

    reason_refs = [
        _fhir_reference_with_identifier_fallback(rr, "reference") for rr in (mr.reason_references or [])
    ]
    reason_refs = [rr for rr in reason_refs if rr]
    if reason_refs:
        result["reasonReference"] = reason_refs

    if mr.instantiates_canonical:
        result["instantiatesCanonical"] = list(mr.instantiates_canonical)
    if mr.instantiates_uri:
        result["instantiatesUri"] = list(mr.instantiates_uri)

    based_ons = [_fhir_reference_with_identifier_fallback(b, "reference") for b in (mr.based_ons or [])]
    based_ons = [b for b in based_ons if b]
    if based_ons:
        result["basedOn"] = based_ons

    group_identifier = fhir_medication_request_identifier(mr, "group_identifier_")
    if group_identifier:
        result["groupIdentifier"] = group_identifier

    course_of_therapy_type = fhir_medication_request_codeable_concept(
        mr.course_of_therapy_type_codings, mr.course_of_therapy_type_text
    )
    if course_of_therapy_type:
        result["courseOfTherapyType"] = course_of_therapy_type

    insurances = [_fhir_reference_with_identifier_fallback(ins, "reference") for ins in (mr.insurances or [])]
    insurances = [ins for ins in insurances if ins]
    if insurances:
        result["insurance"] = insurances

    notes = [fhir_medication_request_note(n) for n in (mr.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        result["note"] = notes

    dosage_instructions = [fhir_medication_request_dosage_instruction(d) for d in (mr.dosage_instructions or [])]
    dosage_instructions = [d for d in dosage_instructions if d]
    if dosage_instructions:
        result["dosageInstruction"] = dosage_instructions

    dispense_request = _fhir_dispense_request(mr)
    if dispense_request:
        result["dispenseRequest"] = dispense_request

    substitution = _fhir_substitution(mr)
    if substitution:
        result["substitution"] = substitution

    prior_prescription = _fhir_reference_with_identifier_fallback(mr, "prior_prescription")
    if prior_prescription:
        result["priorPrescription"] = prior_prescription

    detected_issues = [_fhir_reference_with_identifier_fallback(di, "reference") for di in (mr.detected_issues or [])]
    detected_issues = [di for di in detected_issues if di]
    if detected_issues:
        result["detectedIssue"] = detected_issues

    event_histories = [_fhir_reference_with_identifier_fallback(eh, "reference") for eh in (mr.event_histories or [])]
    event_histories = [eh for eh in event_histories if eh]
    if event_histories:
        result["eventHistory"] = event_histories

    return {k: v for k, v in result.items() if v is not None}
