"""Payload -> FHIR JSON conversion, the mirror image of fhir.py — see that
module's docstring pattern (e.g. app.fhir.mappers.organization.payload) for
the full reasoning. Reads the validated Pydantic input schema
(ServiceRequestCreateSchema / ServiceRequestPatchSchema and their nested
sub-schemas) rather than the persisted ORM model, before anything is
written to the DB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.service_request.input import (
        ServiceRequestCreateSchema,
        ServiceRequestIdentifierInput,
        ServiceRequestNoteInput,
        ServiceRequestPatchSchema,
    )
    from app.schemas.service_request.input.codeable_concept import ServiceRequestCodeableConceptInput


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


def _quantity_from_payload(obj, prefix: str) -> dict:
    value = getattr(obj, f"{prefix}_value", None)
    comparator = getattr(obj, f"{prefix}_comparator", None)
    return {
        k: v
        for k, v in {
            "value": value,
            "comparator": comparator.value if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }


def payload_service_request_identifier(i: ServiceRequestIdentifierInput) -> dict:
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


def payload_service_request_codeable_concept(cc: ServiceRequestCodeableConceptInput) -> dict:
    entry: dict = {}
    coding = _coding_list(cc.coding)
    if coding:
        entry["coding"] = coding
    if cc.text:
        entry["text"] = cc.text
    return entry


def payload_service_request_note(n: ServiceRequestNoteInput) -> dict:
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


def _quantity_choice(payload) -> dict | None:
    q = _quantity_from_payload(payload, "quantity_quantity")
    if q:
        return {"quantityQuantity": q}
    num = _quantity_from_payload(payload, "quantity_ratio_numerator")
    den = _quantity_from_payload(payload, "quantity_ratio_denominator")
    if num or den:
        ratio: dict = {}
        if num:
            ratio["numerator"] = num
        if den:
            ratio["denominator"] = den
        return {"quantityRatio": ratio}
    low = _quantity_from_payload(payload, "quantity_range_low")
    high = _quantity_from_payload(payload, "quantity_range_high")
    if low or high:
        rng: dict = {}
        if low:
            rng["low"] = low
        if high:
            rng["high"] = high
        return {"quantityRange": rng}
    return None


def _occurrence_choice(payload) -> dict | None:
    if payload.occurrence_date_time:
        return {"occurrenceDateTime": payload.occurrence_date_time.isoformat()}
    period = _period(payload.occurrence_period_start, payload.occurrence_period_end)
    if period:
        return {"occurrencePeriod": period}
    if payload.occurrence_timing:
        return {"occurrenceTiming": dict(payload.occurrence_timing)}
    return None


def _as_needed_choice(payload) -> dict | None:
    if payload.as_needed_boolean is not None:
        return {"asNeededBoolean": payload.as_needed_boolean}
    if payload.as_needed_codeable_concept:
        cc = payload_service_request_codeable_concept(payload.as_needed_codeable_concept)
        if cc:
            return {"asNeededCodeableConcept": cc}
    return None


# field -> (fhir key, builder) for every plain 0..* list on this resource.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_service_request_identifier),
    "based_on": ("basedOn", _reference_with_identifier_fallback_from_payload),
    "replaces": ("replaces", _reference_with_identifier_fallback_from_payload),
    "category": ("category", payload_service_request_codeable_concept),
    "order_detail": ("orderDetail", payload_service_request_codeable_concept),
    "performer": ("performer", _reference_with_identifier_fallback_from_payload),
    "location_code": ("locationCode", payload_service_request_codeable_concept),
    "location_reference": ("locationReference", _reference_with_identifier_fallback_from_payload),
    "reason_code": ("reasonCode", payload_service_request_codeable_concept),
    "reason_reference": ("reasonReference", _reference_with_identifier_fallback_from_payload),
    "insurance": ("insurance", _reference_with_identifier_fallback_from_payload),
    "supporting_info": ("supportingInfo", _reference_with_identifier_fallback_from_payload),
    "specimen": ("specimen", _reference_with_identifier_fallback_from_payload),
    "body_site": ("bodySite", payload_service_request_codeable_concept),
    "note": ("note", payload_service_request_note),
    "relevant_history": ("relevantHistory", _reference_with_identifier_fallback_from_payload),
}

# field -> fhir key for every single 0..1 nested-object field.
_SINGLE_REFERENCE_FIELDS = {"subject": "subject", "encounter": "encounter", "requester": "requester"}
_SINGLE_CC_FIELDS = {"code": "code", "performer_type": "performerType"}


def payload_to_fhir_service_request(payload: ServiceRequestCreateSchema) -> dict:
    """Full-resource conversion for CREATE: every field is considered present."""
    result: dict = {"resourceType": "ServiceRequest"}

    if payload.extension:
        result["extension"] = list(payload.extension)

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [i for i in items if i]
        if items:
            result[fhir_key] = items

    if payload.instantiates_canonical:
        result["instantiatesCanonical"] = list(payload.instantiates_canonical)
    if payload.instantiates_uri:
        result["instantiatesUri"] = list(payload.instantiates_uri)
    if payload.requisition:
        requisition = payload_service_request_identifier(payload.requisition)
        if requisition:
            result["requisition"] = requisition

    if payload.status:
        result["status"] = payload.status.value
    if payload.intent:
        result["intent"] = payload.intent.value
    if payload.priority:
        result["priority"] = payload.priority.value
    if payload.do_not_perform is not None:
        result["doNotPerform"] = payload.do_not_perform
    if payload.code:
        code = payload_service_request_codeable_concept(payload.code)
        if code:
            result["code"] = code

    quantity = _quantity_choice(payload)
    if quantity:
        result.update(quantity)

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            ref = _reference_with_identifier_fallback_from_payload(obj)
            if ref:
                result[fhir_key] = ref

    occurrence = _occurrence_choice(payload)
    if occurrence:
        result.update(occurrence)

    as_needed = _as_needed_choice(payload)
    if as_needed:
        result.update(as_needed)

    if payload.authored_on:
        result["authoredOn"] = payload.authored_on.isoformat()

    for field, fhir_key in _SINGLE_CC_FIELDS.items():
        obj = getattr(payload, field, None)
        if obj:
            cc = payload_service_request_codeable_concept(obj)
            if cc:
                result[fhir_key] = cc

    if payload.patient_instruction:
        result["patientInstruction"] = payload.patient_instruction

    return result


def patch_fragment_to_fhir_service_request(payload: ServiceRequestPatchSchema) -> tuple[dict, set[str]]:
    """Tri-state conversion for PATCH — see
    app.fhir.mappers.organization.payload.patch_fragment_to_fhir_organization's
    docstring for the full reasoning."""
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

    if "instantiates_canonical" in provided:
        touched.add("instantiatesCanonical")
        if payload.instantiates_canonical:
            fragment["instantiatesCanonical"] = list(payload.instantiates_canonical)
    if "instantiates_uri" in provided:
        touched.add("instantiatesUri")
        if payload.instantiates_uri:
            fragment["instantiatesUri"] = list(payload.instantiates_uri)
    if "requisition" in provided:
        touched.add("requisition")
        if payload.requisition:
            requisition = payload_service_request_identifier(payload.requisition)
            if requisition:
                fragment["requisition"] = requisition

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
    if "code" in provided:
        touched.add("code")
        if payload.code:
            code = payload_service_request_codeable_concept(payload.code)
            if code:
                fragment["code"] = code

    if provided & {
        "quantity_quantity_value", "quantity_quantity_comparator", "quantity_quantity_unit",
        "quantity_quantity_system", "quantity_quantity_code",
        "quantity_ratio_numerator_value", "quantity_ratio_numerator_comparator", "quantity_ratio_numerator_unit",
        "quantity_ratio_numerator_system", "quantity_ratio_numerator_code",
        "quantity_ratio_denominator_value", "quantity_ratio_denominator_comparator", "quantity_ratio_denominator_unit",
        "quantity_ratio_denominator_system", "quantity_ratio_denominator_code",
        "quantity_range_low_value", "quantity_range_low_unit", "quantity_range_low_system", "quantity_range_low_code",
        "quantity_range_high_value", "quantity_range_high_unit", "quantity_range_high_system", "quantity_range_high_code",
    }:
        touched.add("quantityQuantity")
        touched.add("quantityRatio")
        touched.add("quantityRange")
        quantity = _quantity_choice(payload)
        if quantity:
            fragment.update(quantity)

    for field, fhir_key in _SINGLE_REFERENCE_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                ref = _reference_with_identifier_fallback_from_payload(obj)
                if ref:
                    fragment[fhir_key] = ref

    if provided & {"occurrence_date_time", "occurrence_period_start", "occurrence_period_end", "occurrence_timing"}:
        touched.add("occurrenceDateTime")
        touched.add("occurrencePeriod")
        touched.add("occurrenceTiming")
        occurrence = _occurrence_choice(payload)
        if occurrence:
            fragment.update(occurrence)

    if provided & {"as_needed_boolean", "as_needed_codeable_concept"}:
        touched.add("asNeededBoolean")
        touched.add("asNeededCodeableConcept")
        as_needed = _as_needed_choice(payload)
        if as_needed:
            fragment.update(as_needed)

    if "authored_on" in provided:
        touched.add("authoredOn")
        if payload.authored_on:
            fragment["authoredOn"] = payload.authored_on.isoformat()

    for field, fhir_key in _SINGLE_CC_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            obj = getattr(payload, field, None)
            if obj:
                cc = payload_service_request_codeable_concept(obj)
                if cc:
                    fragment[fhir_key] = cc

    if "patient_instruction" in provided:
        touched.add("patientInstruction")
        if payload.patient_instruction:
            fragment["patientInstruction"] = payload.patient_instruction

    return fragment, touched
