"""Payload -> FHIR JSON conversion for MedicationAdministration.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(MedicationAdministrationCreateSchema / MedicationAdministrationPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.medication_administration.input import (
        MedicationAdministrationCodeableConceptInput,
        MedicationAdministrationCreateSchema,
        MedicationAdministrationDosageInput,
        MedicationAdministrationIdentifierInput,
        MedicationAdministrationNoteInput,
        MedicationAdministrationPatchSchema,
        MedicationAdministrationPerformerInput,
        RatioInput,
        SimpleQuantityInput,
    )

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

_EFFECTIVE_FIELDS = {"effective_date_time", "effective_period_start", "effective_period_end"}
_EFFECTIVE_FHIR_KEYS = {"effectiveDateTime", "effectivePeriod"}

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

_REQUEST_FIELDS = {
    "request",
    "request_display",
    "request_identifier_use",
    "request_identifier_type_system",
    "request_identifier_type_version",
    "request_identifier_type_code",
    "request_identifier_type_display",
    "request_identifier_type_user_selected",
    "request_identifier_type_text",
    "request_identifier_system",
    "request_identifier_value",
    "request_identifier_period_start",
    "request_identifier_period_end",
}
_REQUEST_FHIR_KEYS = {"request"}


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected"),
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


def payload_medication_administration_codeable_concept(
    cc: MedicationAdministrationCodeableConceptInput | dict | None,
) -> dict | None:
    if not cc:
        return None
    coding_raw = _val(cc, "coding")
    codings = [_coding_from_payload(c) for c in (coding_raw or [])]
    codings = [c for c in codings if c]
    text = _val(cc, "text")

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _reference_with_prefix_from_payload(obj: Any, prefix: str) -> dict:
    if not obj:
        return {}
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
            type_cc: dict = {}
            if id_type_system or id_type_code or id_type_display or id_type_version or id_type_user_selected:
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
                for k, v in {
                    "start": id_period_start.isoformat() if hasattr(id_period_start, "isoformat") else (str(id_period_start) if id_period_start else None),
                    "end": id_period_end.isoformat() if hasattr(id_period_end, "isoformat") else (str(id_period_end) if id_period_end else None),
                }.items()
                if v is not None
            }
        if identifier:
            entry["identifier"] = identifier

    return entry


def _reference_from_child_payload(obj: Any) -> dict:
    if not obj:
        return {}
    ref = _val(obj, "reference")
    display = _val(obj, "display")

    id_use = _val(obj, "identifier_use")
    id_type_system = _val(obj, "identifier_type_system")
    id_type_version = _val(obj, "identifier_type_version")
    id_type_code = _val(obj, "identifier_type_code")
    id_type_display = _val(obj, "identifier_type_display")
    id_type_user_selected = _val(obj, "identifier_type_user_selected")
    id_type_text = _val(obj, "identifier_type_text")
    id_system = _val(obj, "identifier_system")
    id_value = _val(obj, "identifier_value")
    id_period_start = _val(obj, "identifier_period_start")
    id_period_end = _val(obj, "identifier_period_end")

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
            type_cc: dict = {}
            if id_type_system or id_type_code or id_type_display or id_type_version or id_type_user_selected:
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
                for k, v in {
                    "start": id_period_start.isoformat() if hasattr(id_period_start, "isoformat") else (str(id_period_start) if id_period_start else None),
                    "end": id_period_end.isoformat() if hasattr(id_period_end, "isoformat") else (str(id_period_end) if id_period_end else None),
                }.items()
                if v is not None
            }
        if identifier:
            entry["identifier"] = identifier

    return entry


def payload_medication_administration_identifier(i: MedicationAdministrationIdentifierInput | dict) -> dict:
    res: dict = {}
    use = _val(i, "use")
    if use:
        res["use"] = use.value if hasattr(use, "value") else str(use)
    t = _val(i, "type")
    if t:
        type_cc = payload_medication_administration_codeable_concept(t)
        if type_cc:
            res["type"] = type_cc
    sys = _val(i, "system")
    if sys:
        res["system"] = sys
    val = _val(i, "value")
    if val:
        res["value"] = val
    start = _val(i, "period_start")
    end = _val(i, "period_end")
    if start or end:
        res["period"] = {
            k: v
            for k, v in {
                "start": start.isoformat() if hasattr(start, "isoformat") else (str(start) if start else None),
                "end": end.isoformat() if hasattr(end, "isoformat") else (str(end) if end else None),
            }.items()
            if v is not None
        }

    assigner = _reference_with_prefix_from_payload(i, "assigner")
    if assigner:
        res["assigner"] = assigner

    return res


def payload_medication_administration_performer(p: MedicationAdministrationPerformerInput | dict) -> dict:
    res: dict = {}
    func = _val(p, "function")
    if func:
        func_cc = payload_medication_administration_codeable_concept(func)
        if func_cc:
            res["function"] = func_cc
    actor = _reference_with_prefix_from_payload(p, "actor")
    if actor:
        res["actor"] = actor
    return res


def payload_medication_administration_note(n: MedicationAdministrationNoteInput | dict) -> dict:
    res: dict = {"text": _val(n, "text")}
    time = _val(n, "time")
    if time:
        res["time"] = time.isoformat() if hasattr(time, "isoformat") else str(time)
    author_str = _val(n, "author_string")
    if author_str:
        res["authorString"] = author_str
    else:
        author_ref = _reference_with_prefix_from_payload(n, "author")
        if author_ref:
            res["authorReference"] = author_ref
    return res


def _quantity_from_payload(q: SimpleQuantityInput | dict | None) -> dict | None:
    if not q:
        return None
    val = _val(q, "value")
    unit = _val(q, "unit")
    system = _val(q, "system")
    code = _val(q, "code")
    res = {
        k: v
        for k, v in {
            "value": float(val) if val is not None else None,
            "unit": unit,
            "system": system,
            "code": code,
        }.items()
        if v is not None
    }
    return res or None


def payload_medication_administration_dosage(d: MedicationAdministrationDosageInput | dict | None) -> dict | None:
    if not d:
        return None
    res: dict = {}
    text = _val(d, "text")
    if text:
        res["text"] = text
    site = _val(d, "site")
    if site:
        site_cc = payload_medication_administration_codeable_concept(site)
        if site_cc:
            res["site"] = site_cc
    route = _val(d, "route")
    if route:
        route_cc = payload_medication_administration_codeable_concept(route)
        if route_cc:
            res["route"] = route_cc
    method = _val(d, "method")
    if method:
        method_cc = payload_medication_administration_codeable_concept(method)
        if method_cc:
            res["method"] = method_cc
    dose = _quantity_from_payload(_val(d, "dose"))
    if dose:
        res["dose"] = dose
    rate_ratio = _val(d, "rate_ratio")
    if rate_ratio:
        num = _quantity_from_payload(_val(rate_ratio, "numerator"))
        den = _quantity_from_payload(_val(rate_ratio, "denominator"))
        ratio = {}
        if num:
            ratio["numerator"] = num
        if den:
            ratio["denominator"] = den
        if ratio:
            res["rateRatio"] = ratio
    else:
        rate_qty = _quantity_from_payload(_val(d, "rate_quantity"))
        if rate_qty:
            res["rateQuantity"] = rate_qty
    return res or None


def payload_to_fhir_medication_administration(payload: MedicationAdministrationCreateSchema) -> dict:
    res: dict = {
        "resourceType": "MedicationAdministration",
    }
    if payload.status:
        res["status"] = payload.status.value if hasattr(payload.status, "value") else str(payload.status)

    if payload.category:
        cat = payload_medication_administration_codeable_concept(payload.category)
        if cat:
            res["category"] = cat

    # medication[x]
    if payload.medication_codeable_concept:
        med_cc = payload_medication_administration_codeable_concept(payload.medication_codeable_concept)
        if med_cc:
            res["medicationCodeableConcept"] = med_cc
    elif payload.medication_reference:
        med_ref = _reference_with_prefix_from_payload(payload, "medication")
        if med_ref:
            res["medicationReference"] = med_ref

    # subject
    subj = _reference_with_prefix_from_payload(payload, "subject")
    if subj:
        res["subject"] = subj

    # context
    ctx = _reference_with_prefix_from_payload(payload, "context")
    if ctx:
        res["context"] = ctx

    # effective[x]
    if payload.effective_date_time:
        res["effectiveDateTime"] = (
            payload.effective_date_time.isoformat()
            if hasattr(payload.effective_date_time, "isoformat")
            else str(payload.effective_date_time)
        )
    elif payload.effective_period_start or payload.effective_period_end:
        res["effectivePeriod"] = {
            k: v
            for k, v in {
                "start": (
                    payload.effective_period_start.isoformat()
                    if hasattr(payload.effective_period_start, "isoformat")
                    else str(payload.effective_period_start)
                )
                if payload.effective_period_start
                else None,
                "end": (
                    payload.effective_period_end.isoformat()
                    if hasattr(payload.effective_period_end, "isoformat")
                    else str(payload.effective_period_end)
                )
                if payload.effective_period_end
                else None,
            }.items()
            if v is not None
        }

    # request
    req = _reference_with_prefix_from_payload(payload, "request")
    if req:
        res["request"] = req

    # instantiates
    if payload.instantiates:
        res["instantiates"] = list(payload.instantiates)

    # part_of
    if payload.part_of:
        po_list = [_reference_from_child_payload(p) for p in payload.part_of]
        po_list = [p for p in po_list if p]
        if po_list:
            res["partOf"] = po_list

    # status_reason
    if payload.status_reason:
        sr_list = [payload_medication_administration_codeable_concept(sr) for sr in payload.status_reason]
        sr_list = [sr for sr in sr_list if sr]
        if sr_list:
            res["statusReason"] = sr_list

    # supporting_information
    if payload.supporting_information:
        si_list = [_reference_from_child_payload(si) for si in payload.supporting_information]
        si_list = [si for si in si_list if si]
        if si_list:
            res["supportingInformation"] = si_list

    # performer
    if payload.performer:
        perf_list = [payload_medication_administration_performer(p) for p in payload.performer]
        perf_list = [p for p in perf_list if p]
        if perf_list:
            res["performer"] = perf_list

    # reason_code
    if payload.reason_code:
        rc_list = [payload_medication_administration_codeable_concept(rc) for rc in payload.reason_code]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            res["reasonCode"] = rc_list

    # reason_reference
    if payload.reason_reference:
        rr_list = [_reference_from_child_payload(rr) for rr in payload.reason_reference]
        rr_list = [rr for rr in rr_list if rr]
        if rr_list:
            res["reasonReference"] = rr_list

    # device
    if payload.device:
        dev_list = [_reference_from_child_payload(d) for d in payload.device]
        dev_list = [d for d in dev_list if d]
        if dev_list:
            res["device"] = dev_list

    # note
    if payload.note:
        notes = [payload_medication_administration_note(n) for n in payload.note]
        notes = [n for n in notes if n]
        if notes:
            res["note"] = notes

    # dosage
    if payload.dosage:
        dosage = payload_medication_administration_dosage(payload.dosage)
        if dosage:
            res["dosage"] = dosage

    # event_history
    if payload.event_history:
        eh_list = [_reference_from_child_payload(eh) for eh in payload.event_history]
        eh_list = [eh for eh in eh_list if eh]
        if eh_list:
            res["eventHistory"] = eh_list

    # identifier
    if payload.identifier:
        identifiers = [payload_medication_administration_identifier(i) for i in payload.identifier]
        identifiers = [i for i in identifiers if i]
        if identifiers:
            res["identifier"] = identifiers

    if payload.extension:
        res["extension"] = list(payload.extension)

    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_medication_administration(
    payload: MedicationAdministrationPatchSchema,
) -> tuple[dict, set[str]]:
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = payload.status.value if hasattr(payload.status, "value") else str(payload.status)

    if "category" in provided:
        touched.add("category")
        if payload.category:
            fragment["category"] = payload_medication_administration_codeable_concept(payload.category)

    if provided & _MEDICATION_FIELDS:
        touched |= _MEDICATION_FHIR_KEYS
        if payload.medication_codeable_concept:
            fragment["medicationCodeableConcept"] = payload_medication_administration_codeable_concept(
                payload.medication_codeable_concept
            )
        elif payload.medication_reference:
            fragment["medicationReference"] = _reference_with_prefix_from_payload(payload, "medication")

    if provided & _SUBJECT_FIELDS:
        touched |= _SUBJECT_FHIR_KEYS
        if payload.subject:
            fragment["subject"] = _reference_with_prefix_from_payload(payload, "subject")

    if provided & _CONTEXT_FIELDS:
        touched |= _CONTEXT_FHIR_KEYS
        if payload.context:
            fragment["context"] = _reference_with_prefix_from_payload(payload, "context")

    if provided & _EFFECTIVE_FIELDS:
        touched |= _EFFECTIVE_FHIR_KEYS
        if payload.effective_date_time:
            fragment["effectiveDateTime"] = (
                payload.effective_date_time.isoformat()
                if hasattr(payload.effective_date_time, "isoformat")
                else str(payload.effective_date_time)
            )
        elif payload.effective_period_start or payload.effective_period_end:
            fragment["effectivePeriod"] = {
                k: v
                for k, v in {
                    "start": (
                        payload.effective_period_start.isoformat()
                        if hasattr(payload.effective_period_start, "isoformat")
                        else str(payload.effective_period_start)
                    )
                    if payload.effective_period_start
                    else None,
                    "end": (
                        payload.effective_period_end.isoformat()
                        if hasattr(payload.effective_period_end, "isoformat")
                        else str(payload.effective_period_end)
                    )
                    if payload.effective_period_end
                    else None,
                }.items()
                if v is not None
            }

    if provided & _REQUEST_FIELDS:
        touched |= _REQUEST_FHIR_KEYS
        if payload.request:
            fragment["request"] = _reference_with_prefix_from_payload(payload, "request")

    if "instantiates" in provided:
        touched.add("instantiates")
        if payload.instantiates:
            fragment["instantiates"] = list(payload.instantiates)

    if "part_of" in provided:
        touched.add("partOf")
        if payload.part_of:
            po_list = [_reference_from_child_payload(p) for p in payload.part_of]
            fragment["partOf"] = [p for p in po_list if p]

    if "status_reason" in provided:
        touched.add("statusReason")
        if payload.status_reason:
            sr_list = [payload_medication_administration_codeable_concept(sr) for sr in payload.status_reason]
            fragment["statusReason"] = [sr for sr in sr_list if sr]

    if "supporting_information" in provided:
        touched.add("supportingInformation")
        if payload.supporting_information:
            si_list = [_reference_from_child_payload(si) for si in payload.supporting_information]
            fragment["supportingInformation"] = [si for si in si_list if si]

    if "performer" in provided:
        touched.add("performer")
        if payload.performer:
            perf_list = [payload_medication_administration_performer(p) for p in payload.performer]
            fragment["performer"] = [p for p in perf_list if p]

    if "reason_code" in provided:
        touched.add("reasonCode")
        if payload.reason_code:
            rc_list = [payload_medication_administration_codeable_concept(rc) for rc in payload.reason_code]
            fragment["reasonCode"] = [rc for rc in rc_list if rc]

    if "reason_reference" in provided:
        touched.add("reasonReference")
        if payload.reason_reference:
            rr_list = [_reference_from_child_payload(rr) for rr in payload.reason_reference]
            fragment["reasonReference"] = [rr for rr in rr_list if rr]

    if "device" in provided:
        touched.add("device")
        if payload.device:
            dev_list = [_reference_from_child_payload(d) for d in payload.device]
            fragment["device"] = [d for d in dev_list if d]

    if "note" in provided:
        touched.add("note")
        if payload.note:
            notes = [payload_medication_administration_note(n) for n in payload.note]
            fragment["note"] = [n for n in notes if n]

    if "dosage" in provided:
        touched.add("dosage")
        if payload.dosage:
            fragment["dosage"] = payload_medication_administration_dosage(payload.dosage)

    if "event_history" in provided:
        touched.add("eventHistory")
        if payload.event_history:
            eh_list = [_reference_from_child_payload(eh) for eh in payload.event_history]
            fragment["eventHistory"] = [eh for eh in eh_list if eh]

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier:
            identifiers = [payload_medication_administration_identifier(i) for i in payload.identifier]
            fragment["identifier"] = [i for i in identifiers if i]

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)

    return fragment, touched
