from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.immunization import (
        ImmunizationEducationModel,
        ImmunizationIdentifierModel,
        ImmunizationModel,
        ImmunizationNoteModel,
        ImmunizationPerformerModel,
        ImmunizationProtocolAppliedModel,
        ImmunizationReactionModel,
        ImmunizationReasonCodeModel,
        ImmunizationSubpotentReasonModel,
    )

_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


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


def fhir_immunization_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
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

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

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
            identifier["use"] = fhir_enum(id_use)
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
                    "start": fhir_instant(id_period_start) if id_period_start else None,
                    "end": fhir_instant(id_period_end) if id_period_end else None,
                }.items()
                if v is not None
            }
        entry["identifier"] = identifier

    return entry


def _fhir_simple_quantity(obj, prefix: str = "dose_quantity") -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    if val is None:
        return None
    res = {"value": float(val)}
    unit = getattr(obj, f"{prefix}_unit", None)
    system = getattr(obj, f"{prefix}_system", None)
    code = getattr(obj, f"{prefix}_code", None)
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def _fhir_meta(model: ImmunizationModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif model.created_at:
        meta["lastUpdated"] = fhir_instant(model.created_at)

    exts: list[dict] = []
    if model.created_at:
        exts.append({"url": f"{_EXT_BASE}/created-at", "valueInstant": fhir_instant(model.created_at)})
    if model.created_by:
        exts.append({"url": f"{_EXT_BASE}/created-by", "valueString": model.created_by})
    if model.updated_by:
        exts.append({"url": f"{_EXT_BASE}/updated-by", "valueString": model.updated_by})
    if model.tenant_id:
        exts.append({"url": f"{_EXT_BASE}/tenant-id", "valueString": model.tenant_id})
    if exts:
        meta["extension"] = exts
    return meta


def fhir_immunization_identifier(i: ImmunizationIdentifierModel) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = fhir_immunization_codeable_concept(i.type_codings, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start) if i.period_start else None,
                "end": fhir_instant(i.period_end) if i.period_end else None,
            }.items()
            if v is not None
        }
    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_immunization_performer(p: ImmunizationPerformerModel) -> dict:
    entry: dict = {}
    fn_cc = fhir_immunization_codeable_concept(p.function_codings, p.function_text)
    if fn_cc:
        entry["function"] = fn_cc
    actor = _fhir_reference_with_identifier_fallback(p, "actor")
    if actor:
        entry["actor"] = actor
    return entry


def fhir_immunization_note(n: ImmunizationNoteModel) -> dict:
    entry: dict = {"text": n.text}
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        author_ref = _fhir_reference_with_identifier_fallback(n, "author")
        if author_ref:
            entry["authorReference"] = author_ref
    return entry


def fhir_immunization_education(e: ImmunizationEducationModel) -> dict:
    entry: dict = {}
    if e.document_type:
        entry["documentType"] = e.document_type
    if e.reference:
        entry["reference"] = e.reference
    if e.publication_date:
        entry["publicationDate"] = (
            e.publication_date.isoformat()
            if hasattr(e.publication_date, "isoformat")
            else str(e.publication_date)
        )
    if e.presentation_date:
        entry["presentationDate"] = (
            e.presentation_date.isoformat()
            if hasattr(e.presentation_date, "isoformat")
            else str(e.presentation_date)
        )
    return entry


def fhir_immunization_reaction(r: ImmunizationReactionModel) -> dict:
    entry: dict = {}
    if r.date:
        entry["date"] = fhir_instant(r.date)
    detail = _fhir_reference_with_identifier_fallback(r, "detail")
    if detail:
        entry["detail"] = detail
    if r.reported is not None:
        entry["reported"] = r.reported
    return entry


def fhir_immunization_protocol_applied(pa: ImmunizationProtocolAppliedModel) -> dict:
    entry: dict = {}
    if pa.series:
        entry["series"] = pa.series
    authority = _fhir_reference_with_identifier_fallback(pa, "authority")
    if authority:
        entry["authority"] = authority
    if pa.target_diseases:
        td_list = [
            fhir_immunization_codeable_concept(td.codings, td.text)
            for td in pa.target_diseases
        ]
        entry["targetDisease"] = [td for td in td_list if td]
    if pa.dose_number_positive_int is not None:
        entry["doseNumberPositiveInt"] = pa.dose_number_positive_int
    elif pa.dose_number_string:
        entry["doseNumberString"] = pa.dose_number_string
    if pa.series_doses_positive_int is not None:
        entry["seriesDosesPositiveInt"] = pa.series_doses_positive_int
    elif pa.series_doses_string:
        entry["seriesDosesString"] = pa.series_doses_string
    return entry


def to_fhir_immunization(model: ImmunizationModel) -> dict:
    """Serialize ImmunizationModel to standard FHIR R4 JSON."""
    resource: dict = {
        "resourceType": "Immunization",
        "id": str(model.immunization_id),
    }

    meta = _fhir_meta(model)
    if meta:
        resource["meta"] = meta

    if model.extension:
        resource["extension"] = model.extension

    if model.identifiers:
        resource["identifier"] = [
            fhir_immunization_identifier(i) for i in model.identifiers
        ]

    resource["status"] = fhir_enum(model.status)

    status_reason = fhir_immunization_codeable_concept(
        model.status_reason_codings, model.status_reason_text
    )
    if status_reason:
        resource["statusReason"] = status_reason

    vaccine_code = fhir_immunization_codeable_concept(
        model.vaccine_codings, model.vaccine_code_text
    )
    if vaccine_code:
        resource["vaccineCode"] = vaccine_code

    patient = _fhir_reference_with_identifier_fallback(model, "patient")
    if patient:
        resource["patient"] = patient

    encounter = _fhir_reference_with_identifier_fallback(model, "encounter")
    if encounter:
        resource["encounter"] = encounter

    if model.occurrence_date_time:
        resource["occurrenceDateTime"] = fhir_instant(model.occurrence_date_time)
    elif model.occurrence_string:
        resource["occurrenceString"] = model.occurrence_string

    if model.recorded:
        resource["recorded"] = fhir_instant(model.recorded)

    if model.primary_source is not None:
        resource["primarySource"] = model.primary_source

    report_origin = fhir_immunization_codeable_concept(
        model.report_origin_codings, model.report_origin_text
    )
    if report_origin:
        resource["reportOrigin"] = report_origin

    location = _fhir_reference_with_identifier_fallback(model, "location")
    if location:
        resource["location"] = location

    manufacturer = _fhir_reference_with_identifier_fallback(model, "manufacturer")
    if manufacturer:
        resource["manufacturer"] = manufacturer

    if model.lot_number:
        resource["lotNumber"] = model.lot_number

    if model.expiration_date:
        resource["expirationDate"] = model.expiration_date.isoformat()

    site = fhir_immunization_codeable_concept(model.site_codings, model.site_text)
    if site:
        resource["site"] = site

    route = fhir_immunization_codeable_concept(model.route_codings, model.route_text)
    if route:
        resource["route"] = route

    dose_qty = _fhir_simple_quantity(model, "dose_quantity")
    if dose_qty:
        resource["doseQuantity"] = dose_qty

    if model.performers:
        resource["performer"] = [
            fhir_immunization_performer(p) for p in model.performers
        ]

    if model.notes:
        resource["note"] = [fhir_immunization_note(n) for n in model.notes]

    if model.reason_codes:
        rc_list = [
            fhir_immunization_codeable_concept(rc.codings, rc.text)
            for rc in model.reason_codes
        ]
        resource["reasonCode"] = [rc for rc in rc_list if rc]

    if model.reason_references:
        resource["reasonReference"] = [
            _fhir_reference_with_identifier_fallback(rr, "reference")
            for rr in model.reason_references
        ]

    if model.is_subpotent is not None:
        resource["isSubpotent"] = model.is_subpotent

    if model.subpotent_reasons:
        sr_list = [
            fhir_immunization_codeable_concept(sr.codings, sr.text)
            for sr in model.subpotent_reasons
        ]
        resource["subpotentReason"] = [sr for sr in sr_list if sr]

    if model.education_items:
        resource["education"] = [
            fhir_immunization_education(e) for e in model.education_items
        ]

    if model.program_eligibilities:
        pe_list = [
            fhir_immunization_codeable_concept(pe.codings, pe.text)
            for pe in model.program_eligibilities
        ]
        resource["programEligibility"] = [pe for pe in pe_list if pe]

    funding_source = fhir_immunization_codeable_concept(
        model.funding_source_codings, model.funding_source_text
    )
    if funding_source:
        resource["fundingSource"] = funding_source

    if model.reactions:
        resource["reaction"] = [
            fhir_immunization_reaction(r) for r in model.reactions
        ]

    if model.protocol_applied_items:
        resource["protocolApplied"] = [
            fhir_immunization_protocol_applied(pa) for pa in model.protocol_applied_items
        ]

    return {k: v for k, v in resource.items() if v is not None}
