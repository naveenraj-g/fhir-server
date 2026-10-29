from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.service_request import ServiceRequestModel

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


def fhir_service_request_identifier(obj, prefix: str = "") -> dict:
    """Renders either a full ServiceRequestIdentifier child row (prefix="")
    or the main row's flattened `requisition_*` columns (prefix=
    "requisition_") into a FHIR Identifier dict — same shape either way.
    The type.coding[] relationship is named `type_codings` on the child
    row, `requisition_type_codings` on the main row."""
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


def fhir_service_request_codeable_concept(codings, text: str | None) -> dict:
    """Generic CodeableConcept renderer — reused for every plain {coding[],
    text} field on this resource (category/orderDetail/locationCode/
    reasonCode/bodySite list items, and code/performerType/
    asNeededCodeableConcept's own single fields)."""
    entry: dict = {}
    coding = _fhir_coding_list(codings)
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def fhir_service_request_note(n) -> dict:
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


_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(sr: ServiceRequestModel) -> dict:
    meta: dict = {}
    if sr.updated_at:
        meta["lastUpdated"] = fhir_instant(sr.updated_at)
    extensions = []
    if sr.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": sr.tenant_id})
    if sr.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": sr.created_by})
    if sr.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": sr.updated_by})
    if sr.created_at:
        extensions.append({"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(sr.created_at)})
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_service_request(sr: ServiceRequestModel) -> dict:
    result: dict = {"resourceType": "ServiceRequest", "id": str(sr.service_request_id)}

    meta = _fhir_meta(sr)
    if meta:
        result["meta"] = meta
    if sr.extension:
        result["extension"] = list(sr.extension)

    identifiers = [fhir_service_request_identifier(i) for i in (sr.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers
    if sr.instantiates_canonical:
        result["instantiatesCanonical"] = list(sr.instantiates_canonical)
    if sr.instantiates_uri:
        result["instantiatesUri"] = list(sr.instantiates_uri)

    based_ons = [_fhir_reference_with_identifier_fallback(b, "reference") for b in (sr.based_ons or [])]
    based_ons = [b for b in based_ons if b]
    if based_ons:
        result["basedOn"] = based_ons

    replaces = [_fhir_reference_with_identifier_fallback(r, "reference") for r in (sr.replaces or [])]
    replaces = [r for r in replaces if r]
    if replaces:
        result["replaces"] = replaces

    requisition = fhir_service_request_identifier(sr, "requisition_")
    if requisition:
        result["requisition"] = requisition

    if sr.status:
        result["status"] = fhir_enum(sr.status).replace("_", "-")
    if sr.intent:
        result["intent"] = fhir_enum(sr.intent).replace("_", "-")

    categories = [fhir_service_request_codeable_concept(c.codings, c.text) for c in (sr.categories or [])]
    categories = [c for c in categories if c]
    if categories:
        result["category"] = categories

    if sr.priority:
        result["priority"] = fhir_enum(sr.priority)
    if sr.do_not_perform is not None:
        result["doNotPerform"] = sr.do_not_perform

    code = fhir_service_request_codeable_concept(sr.code_codings, sr.code_text)
    if code:
        result["code"] = code

    order_details = [fhir_service_request_codeable_concept(o.codings, o.text) for o in (sr.order_details or [])]
    order_details = [o for o in order_details if o]
    if order_details:
        result["orderDetail"] = order_details

    quantity_quantity = _fhir_quantity(sr, "quantity_quantity")
    quantity_ratio_num = _fhir_quantity(sr, "quantity_ratio_numerator")
    quantity_ratio_den = _fhir_quantity(sr, "quantity_ratio_denominator")
    quantity_range_low = _fhir_quantity(sr, "quantity_range_low")
    quantity_range_high = _fhir_quantity(sr, "quantity_range_high")
    if quantity_quantity:
        result["quantityQuantity"] = quantity_quantity
    elif quantity_ratio_num or quantity_ratio_den:
        ratio: dict = {}
        if quantity_ratio_num:
            ratio["numerator"] = quantity_ratio_num
        if quantity_ratio_den:
            ratio["denominator"] = quantity_ratio_den
        result["quantityRatio"] = ratio
    elif quantity_range_low or quantity_range_high:
        rng: dict = {}
        if quantity_range_low:
            rng["low"] = quantity_range_low
        if quantity_range_high:
            rng["high"] = quantity_range_high
        result["quantityRange"] = rng

    subject = _fhir_reference_with_identifier_fallback(sr, "subject")
    if subject:
        result["subject"] = subject

    encounter = _fhir_reference_with_identifier_fallback(sr, "encounter")
    if encounter:
        result["encounter"] = encounter

    if sr.occurrence_date_time:
        result["occurrenceDateTime"] = fhir_instant(sr.occurrence_date_time)
    elif sr.occurrence_period_start or sr.occurrence_period_end:
        result["occurrencePeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(sr.occurrence_period_start),
                "end": fhir_instant(sr.occurrence_period_end),
            }.items()
            if v
        }
    elif sr.occurrence_timing:
        result["occurrenceTiming"] = dict(sr.occurrence_timing)

    if sr.as_needed_boolean is not None:
        result["asNeededBoolean"] = sr.as_needed_boolean
    else:
        as_needed_cc = fhir_service_request_codeable_concept(sr.as_needed_codings, sr.as_needed_codeable_concept_text)
        if as_needed_cc:
            result["asNeededCodeableConcept"] = as_needed_cc

    if sr.authored_on:
        result["authoredOn"] = fhir_instant(sr.authored_on)

    requester = _fhir_reference_with_identifier_fallback(sr, "requester")
    if requester:
        result["requester"] = requester

    performer_type = fhir_service_request_codeable_concept(sr.performer_type_codings, sr.performer_type_text)
    if performer_type:
        result["performerType"] = performer_type

    performers = [_fhir_reference_with_identifier_fallback(p, "reference") for p in (sr.performers or [])]
    performers = [p for p in performers if p]
    if performers:
        result["performer"] = performers

    location_codes = [fhir_service_request_codeable_concept(lc.codings, lc.text) for lc in (sr.location_codes or [])]
    location_codes = [lc for lc in location_codes if lc]
    if location_codes:
        result["locationCode"] = location_codes

    location_refs = [_fhir_reference_with_identifier_fallback(lr, "reference") for lr in (sr.location_references or [])]
    location_refs = [lr for lr in location_refs if lr]
    if location_refs:
        result["locationReference"] = location_refs

    reason_codes = [fhir_service_request_codeable_concept(rc.codings, rc.text) for rc in (sr.reason_codes or [])]
    reason_codes = [rc for rc in reason_codes if rc]
    if reason_codes:
        result["reasonCode"] = reason_codes

    reason_refs = [_fhir_reference_with_identifier_fallback(rr, "reference") for rr in (sr.reason_references or [])]
    reason_refs = [rr for rr in reason_refs if rr]
    if reason_refs:
        result["reasonReference"] = reason_refs

    insurances = [_fhir_reference_with_identifier_fallback(ins, "reference") for ins in (sr.insurances or [])]
    insurances = [ins for ins in insurances if ins]
    if insurances:
        result["insurance"] = insurances

    supporting_infos = [_fhir_reference_with_identifier_fallback(si, "reference") for si in (sr.supporting_infos or [])]
    supporting_infos = [si for si in supporting_infos if si]
    if supporting_infos:
        result["supportingInfo"] = supporting_infos

    specimens = [_fhir_reference_with_identifier_fallback(sp, "reference") for sp in (sr.specimens or [])]
    specimens = [sp for sp in specimens if sp]
    if specimens:
        result["specimen"] = specimens

    body_sites = [fhir_service_request_codeable_concept(bs.codings, bs.text) for bs in (sr.body_sites or [])]
    body_sites = [bs for bs in body_sites if bs]
    if body_sites:
        result["bodySite"] = body_sites

    notes = [fhir_service_request_note(n) for n in (sr.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        result["note"] = notes

    if sr.patient_instruction:
        result["patientInstruction"] = sr.patient_instruction

    relevant_histories = [
        _fhir_reference_with_identifier_fallback(rh, "reference") for rh in (sr.relevant_histories or [])
    ]
    relevant_histories = [rh for rh in relevant_histories if rh]
    if relevant_histories:
        result["relevantHistory"] = relevant_histories

    return {k: v for k, v in result.items() if v is not None}
