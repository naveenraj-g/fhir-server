"""Payload -> FHIR JSON conversion for Immunization.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ImmunizationCreateSchema / ImmunizationPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.immunization.input import (
        ImmunizationCodeableConceptInput,
        ImmunizationCreateSchema,
        ImmunizationEducationInput,
        ImmunizationIdentifierInput,
        ImmunizationNoteInput,
        ImmunizationPatchSchema,
        ImmunizationPerformerInput,
        ImmunizationProtocolAppliedInput,
        ImmunizationReactionInput,
    )

_OCCURRENCE_FIELDS = {"occurrence_date_time", "occurrence_string"}
_OCCURRENCE_FHIR_KEYS = {"occurrenceDateTime", "occurrenceString"}


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _format_datetime(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


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


def payload_immunization_codeable_concept(
    cc: ImmunizationCodeableConceptInput | dict | None,
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


def _reference_with_identifier_from_payload(obj: Any) -> dict:
    if not obj:
        return {}
    ref = _val(obj, "reference")
    display = _val(obj, "reference_display") or _val(obj, "display")

    id_use = _val(obj, "reference_identifier_use") or _val(obj, "identifier_use")
    id_type_system = _val(obj, "reference_identifier_type_system") or _val(obj, "identifier_type_system")
    id_type_version = _val(obj, "reference_identifier_type_version") or _val(obj, "identifier_type_version")
    id_type_code = _val(obj, "reference_identifier_type_code") or _val(obj, "identifier_type_code")
    id_type_display = _val(obj, "reference_identifier_type_display") or _val(obj, "identifier_type_display")
    id_type_user_selected = _val(obj, "reference_identifier_type_user_selected") or _val(obj, "identifier_type_user_selected")
    id_type_text = _val(obj, "reference_identifier_type_text") or _val(obj, "identifier_type_text")
    id_system = _val(obj, "reference_identifier_system") or _val(obj, "identifier_system")
    id_value = _val(obj, "reference_identifier_value") or _val(obj, "identifier_value")
    id_period_start = _val(obj, "reference_identifier_period_start") or _val(obj, "identifier_period_start")
    id_period_end = _val(obj, "reference_identifier_period_end") or _val(obj, "identifier_period_end")

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
                    "start": _format_datetime(id_period_start),
                    "end": _format_datetime(id_period_end),
                }.items()
                if v is not None
            }
        entry["identifier"] = identifier

    return entry


def _simple_quantity_from_payload(obj: Any) -> dict | None:
    if not obj:
        return None
    val = _val(obj, "value")
    if val is None:
        return None
    res = {"value": float(val)}
    unit = _val(obj, "unit")
    system = _val(obj, "system")
    code = _val(obj, "code")
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def payload_immunization_identifier(i: ImmunizationIdentifierInput | dict) -> dict:
    entry: dict = {}
    use = _val(i, "use")
    if use:
        entry["use"] = use.value if hasattr(use, "value") else str(use)
    type_cc = payload_immunization_codeable_concept(_val(i, "type"))
    if type_cc:
        entry["type"] = type_cc
    system = _val(i, "system")
    if system:
        entry["system"] = system
    value = _val(i, "value")
    if value:
        entry["value"] = value
    p_start = _val(i, "period_start")
    p_end = _val(i, "period_end")
    if p_start or p_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": _format_datetime(p_start),
                "end": _format_datetime(p_end),
            }.items()
            if v is not None
        }
    assigner = _val(i, "assigner")
    assigner_display = _val(i, "assigner_display")
    if assigner or assigner_display:
        assigner_dict: dict = {}
        if assigner:
            assigner_dict["reference"] = assigner
        if assigner_display:
            assigner_dict["display"] = assigner_display
        entry["assigner"] = assigner_dict
    return entry


def payload_immunization_performer(p: ImmunizationPerformerInput | dict) -> dict:
    entry: dict = {}
    fn_cc = payload_immunization_codeable_concept(_val(p, "function"))
    if fn_cc:
        entry["function"] = fn_cc
    actor = _reference_with_identifier_from_payload(_val(p, "actor"))
    if actor:
        entry["actor"] = actor
    return entry


def payload_immunization_note(n: ImmunizationNoteInput | dict) -> dict:
    entry: dict = {"text": _val(n, "text")}
    time = _val(n, "time")
    if time:
        entry["time"] = _format_datetime(time)
    author_string = _val(n, "author_string")
    if author_string:
        entry["authorString"] = author_string
    else:
        author_ref = _val(n, "author_reference")
        author_disp = _val(n, "author_display")
        if author_ref or author_disp:
            ref_dict: dict = {}
            if author_ref:
                ref_dict["reference"] = author_ref
            if author_disp:
                ref_dict["display"] = author_disp
            entry["authorReference"] = ref_dict
    return entry


def payload_immunization_education(e: ImmunizationEducationInput | dict) -> dict:
    entry: dict = {}
    doc_type = _val(e, "document_type")
    if doc_type:
        entry["documentType"] = doc_type
    ref = _val(e, "reference")
    if ref:
        entry["reference"] = ref
    pub_date = _val(e, "publication_date")
    if pub_date:
        entry["publicationDate"] = _format_datetime(pub_date)
    pres_date = _val(e, "presentation_date")
    if pres_date:
        entry["presentationDate"] = _format_datetime(pres_date)
    return entry


def payload_immunization_reaction(r: ImmunizationReactionInput | dict) -> dict:
    entry: dict = {}
    date_val = _val(r, "date")
    if date_val:
        entry["date"] = _format_datetime(date_val)
    detail = _reference_with_identifier_from_payload(_val(r, "detail"))
    if detail:
        entry["detail"] = detail
    reported = _val(r, "reported")
    if reported is not None:
        entry["reported"] = reported
    return entry


def payload_immunization_protocol_applied(pa: ImmunizationProtocolAppliedInput | dict) -> dict:
    entry: dict = {}
    series = _val(pa, "series")
    if series:
        entry["series"] = series
    authority = _reference_with_identifier_from_payload(_val(pa, "authority"))
    if authority:
        entry["authority"] = authority
    target_disease_raw = _val(pa, "target_disease")
    if target_disease_raw:
        td_list = [
            payload_immunization_codeable_concept(td)
            for td in target_disease_raw
        ]
        entry["targetDisease"] = [td for td in td_list if td]
    dose_int = _val(pa, "dose_number_positive_int")
    dose_str = _val(pa, "dose_number_string")
    if dose_int is not None:
        entry["doseNumberPositiveInt"] = dose_int
    elif dose_str:
        entry["doseNumberString"] = dose_str
    series_int = _val(pa, "series_doses_positive_int")
    series_str = _val(pa, "series_doses_string")
    if series_int is not None:
        entry["seriesDosesPositiveInt"] = series_int
    elif series_str:
        entry["seriesDosesString"] = series_str
    return entry


def payload_to_fhir_immunization(payload: ImmunizationCreateSchema) -> dict:
    """Full conversion: ImmunizationCreateSchema -> true FHIR R4 dict."""
    resource: dict = {"resourceType": "Immunization"}

    status = _val(payload, "status")
    if status:
        resource["status"] = status.value if hasattr(status, "value") else str(status)

    status_reason = payload_immunization_codeable_concept(_val(payload, "status_reason"))
    if status_reason:
        resource["statusReason"] = status_reason

    vaccine_code = payload_immunization_codeable_concept(_val(payload, "vaccine_code"))
    if vaccine_code:
        resource["vaccineCode"] = vaccine_code

    patient = _reference_with_identifier_from_payload(_val(payload, "patient"))
    if patient:
        resource["patient"] = patient

    encounter = _reference_with_identifier_from_payload(_val(payload, "encounter"))
    if encounter:
        resource["encounter"] = encounter

    occ_dt = _val(payload, "occurrence_date_time")
    occ_str = _val(payload, "occurrence_string")
    if occ_dt:
        resource["occurrenceDateTime"] = _format_datetime(occ_dt)
    elif occ_str:
        resource["occurrenceString"] = occ_str

    recorded = _val(payload, "recorded")
    if recorded:
        resource["recorded"] = _format_datetime(recorded)

    primary_source = _val(payload, "primary_source")
    if primary_source is not None:
        resource["primarySource"] = primary_source

    report_origin = payload_immunization_codeable_concept(_val(payload, "report_origin"))
    if report_origin:
        resource["reportOrigin"] = report_origin

    location = _reference_with_identifier_from_payload(_val(payload, "location"))
    if location:
        resource["location"] = location

    manufacturer = _reference_with_identifier_from_payload(_val(payload, "manufacturer"))
    if manufacturer:
        resource["manufacturer"] = manufacturer

    lot_number = _val(payload, "lot_number")
    if lot_number:
        resource["lotNumber"] = lot_number

    exp_date = _val(payload, "expiration_date")
    if exp_date:
        resource["expirationDate"] = exp_date.isoformat() if hasattr(exp_date, "isoformat") else str(exp_date)

    site = payload_immunization_codeable_concept(_val(payload, "site"))
    if site:
        resource["site"] = site

    route = payload_immunization_codeable_concept(_val(payload, "route"))
    if route:
        resource["route"] = route

    dose_qty = _simple_quantity_from_payload(_val(payload, "dose_quantity"))
    if dose_qty:
        resource["doseQuantity"] = dose_qty

    is_subpotent = _val(payload, "is_subpotent")
    if is_subpotent is not None:
        resource["isSubpotent"] = is_subpotent

    funding_source = payload_immunization_codeable_concept(_val(payload, "funding_source"))
    if funding_source:
        resource["fundingSource"] = funding_source

    identifiers = _val(payload, "identifier")
    if identifiers:
        resource["identifier"] = [payload_immunization_identifier(i) for i in identifiers]

    performers = _val(payload, "performer")
    if performers:
        resource["performer"] = [payload_immunization_performer(p) for p in performers]

    notes = _val(payload, "note")
    if notes:
        resource["note"] = [payload_immunization_note(n) for n in notes]

    reason_codes = _val(payload, "reason_code")
    if reason_codes:
        rc_list = [payload_immunization_codeable_concept(rc) for rc in reason_codes]
        resource["reasonCode"] = [rc for rc in rc_list if rc]

    reason_refs = _val(payload, "reason_reference")
    if reason_refs:
        resource["reasonReference"] = [
            _reference_with_identifier_from_payload(rr) for rr in reason_refs
        ]

    subpotent_reasons = _val(payload, "subpotent_reason")
    if subpotent_reasons:
        sr_list = [payload_immunization_codeable_concept(sr) for sr in subpotent_reasons]
        resource["subpotentReason"] = [sr for sr in sr_list if sr]

    education_items = _val(payload, "education")
    if education_items:
        resource["education"] = [payload_immunization_education(e) for e in education_items]

    program_eligibilities = _val(payload, "program_eligibility")
    if program_eligibilities:
        pe_list = [payload_immunization_codeable_concept(pe) for pe in program_eligibilities]
        resource["programEligibility"] = [pe for pe in pe_list if pe]

    reactions = _val(payload, "reaction")
    if reactions:
        resource["reaction"] = [payload_immunization_reaction(r) for r in reactions]

    protocol_applied_items = _val(payload, "protocol_applied")
    if protocol_applied_items:
        resource["protocolApplied"] = [
            payload_immunization_protocol_applied(pa) for pa in protocol_applied_items
        ]

    return {k: v for k, v in resource.items() if v is not None}


def patch_fragment_to_fhir_immunization(
    payload: ImmunizationPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert an ImmunizationPatchSchema to a partial FHIR R4 dict."""
    fragment: dict = {}
    touched: set[str] = set()

    for field in payload.model_fields_set:
        val = getattr(payload, field)

        if field == "status":
            touched.add("status")
            if val is not None:
                fragment["status"] = val.value if hasattr(val, "value") else str(val)

        elif field == "status_reason":
            touched.add("statusReason")
            cc = payload_immunization_codeable_concept(val)
            if cc:
                fragment["statusReason"] = cc

        elif field == "vaccine_code":
            touched.add("vaccineCode")
            cc = payload_immunization_codeable_concept(val)
            if cc:
                fragment["vaccineCode"] = cc

        elif field == "patient":
            touched.add("patient")
            ref = _reference_with_identifier_from_payload(val)
            if ref:
                fragment["patient"] = ref

        elif field == "encounter":
            touched.add("encounter")
            ref = _reference_with_identifier_from_payload(val)
            if ref:
                fragment["encounter"] = ref

        elif field in _OCCURRENCE_FIELDS:
            touched.update(_OCCURRENCE_FHIR_KEYS)
            occ_dt = getattr(payload, "occurrence_date_time", None)
            occ_str = getattr(payload, "occurrence_string", None)
            if occ_dt:
                fragment["occurrenceDateTime"] = _format_datetime(occ_dt)
            elif occ_str:
                fragment["occurrenceString"] = occ_str

        elif field == "recorded":
            touched.add("recorded")
            if val is not None:
                fragment["recorded"] = _format_datetime(val)

        elif field == "primary_source":
            touched.add("primarySource")
            if val is not None:
                fragment["primarySource"] = val

        elif field == "report_origin":
            touched.add("reportOrigin")
            cc = payload_immunization_codeable_concept(val)
            if cc:
                fragment["reportOrigin"] = cc

        elif field == "location":
            touched.add("location")
            ref = _reference_with_identifier_from_payload(val)
            if ref:
                fragment["location"] = ref

        elif field == "manufacturer":
            touched.add("manufacturer")
            ref = _reference_with_identifier_from_payload(val)
            if ref:
                fragment["manufacturer"] = ref

        elif field == "lot_number":
            touched.add("lotNumber")
            if val is not None:
                fragment["lotNumber"] = val

        elif field == "expiration_date":
            touched.add("expirationDate")
            if val is not None:
                fragment["expirationDate"] = val.isoformat() if hasattr(val, "isoformat") else str(val)

        elif field == "site":
            touched.add("site")
            cc = payload_immunization_codeable_concept(val)
            if cc:
                fragment["site"] = cc

        elif field == "route":
            touched.add("route")
            cc = payload_immunization_codeable_concept(val)
            if cc:
                fragment["route"] = cc

        elif field == "dose_quantity":
            touched.add("doseQuantity")
            dq = _simple_quantity_from_payload(val)
            if dq:
                fragment["doseQuantity"] = dq

        elif field == "is_subpotent":
            touched.add("isSubpotent")
            if val is not None:
                fragment["isSubpotent"] = val

        elif field == "funding_source":
            touched.add("fundingSource")
            cc = payload_immunization_codeable_concept(val)
            if cc:
                fragment["fundingSource"] = cc

        elif field == "identifier":
            touched.add("identifier")
            if val is not None:
                fragment["identifier"] = [payload_immunization_identifier(i) for i in val]

        elif field == "performer":
            touched.add("performer")
            if val is not None:
                fragment["performer"] = [payload_immunization_performer(p) for p in val]

        elif field == "note":
            touched.add("note")
            if val is not None:
                fragment["note"] = [payload_immunization_note(n) for n in val]

        elif field == "reason_code":
            touched.add("reasonCode")
            if val is not None:
                rc_list = [payload_immunization_codeable_concept(rc) for rc in val]
                fragment["reasonCode"] = [rc for rc in rc_list if rc]

        elif field == "reason_reference":
            touched.add("reasonReference")
            if val is not None:
                fragment["reasonReference"] = [
                    _reference_with_identifier_from_payload(rr) for rr in val
                ]

        elif field == "subpotent_reason":
            touched.add("subpotentReason")
            if val is not None:
                sr_list = [payload_immunization_codeable_concept(sr) for sr in val]
                fragment["subpotentReason"] = [sr for sr in sr_list if sr]

        elif field == "education":
            touched.add("education")
            if val is not None:
                fragment["education"] = [payload_immunization_education(e) for e in val]

        elif field == "program_eligibility":
            touched.add("programEligibility")
            if val is not None:
                pe_list = [payload_immunization_codeable_concept(pe) for pe in val]
                fragment["programEligibility"] = [pe for pe in pe_list if pe]

        elif field == "reaction":
            touched.add("reaction")
            if val is not None:
                fragment["reaction"] = [payload_immunization_reaction(r) for r in val]

        elif field == "protocol_applied":
            touched.add("protocolApplied")
            if val is not None:
                fragment["protocolApplied"] = [
                    payload_immunization_protocol_applied(pa) for pa in val
                ]

    return fragment, touched
