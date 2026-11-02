from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.immunization import (
        ImmunizationEducationModel,
        ImmunizationIdentifierModel,
        ImmunizationModel,
        ImmunizationNoteModel,
        ImmunizationPerformerModel,
        ImmunizationProtocolAppliedModel,
        ImmunizationReactionModel,
    )


def plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        if any(v is not None for v in entry.values()):
            result.append(entry)
    return result


def plain_immunization_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = plain_coding_list(codings)
    if not coding_list and not text:
        return None
    return {
        "coding": coding_list if coding_list else None,
        "text": text,
    }


def plain_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    ref_str = raw_reference
    if not ref_str and ref_type and ref_id:
        ref_str = f"{fhir_enum(ref_type)}/{ref_id}"

    id_use = getattr(obj, f"{prefix}_identifier_use", None)

    return {
        "id": getattr(obj, "id", None),
        "reference": ref_str,
        "reference_display": display,
        "reference_identifier_use": fhir_enum(id_use) if id_use else None,
        "reference_identifier_type_system": getattr(obj, f"{prefix}_identifier_type_system", None),
        "reference_identifier_type_version": getattr(obj, f"{prefix}_identifier_type_version", None),
        "reference_identifier_type_code": getattr(obj, f"{prefix}_identifier_type_code", None),
        "reference_identifier_type_display": getattr(obj, f"{prefix}_identifier_type_display", None),
        "reference_identifier_type_user_selected": getattr(obj, f"{prefix}_identifier_type_user_selected", None),
        "reference_identifier_type_text": getattr(obj, f"{prefix}_identifier_type_text", None),
        "reference_identifier_system": getattr(obj, f"{prefix}_identifier_system", None),
        "reference_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        "reference_identifier_period_start": getattr(obj, f"{prefix}_identifier_period_start", None),
        "reference_identifier_period_end": getattr(obj, f"{prefix}_identifier_period_end", None),
    }


def plain_simple_quantity(obj, prefix: str = "dose_quantity") -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    if val is None:
        return None
    return {
        "value": float(val),
        "unit": getattr(obj, f"{prefix}_unit", None),
        "system": getattr(obj, f"{prefix}_system", None),
        "code": getattr(obj, f"{prefix}_code", None),
    }


def plain_immunization_identifier(i: ImmunizationIdentifierModel) -> dict:
    assigner_raw = getattr(i, "assigner_reference", None)
    assigner_id = getattr(i, "assigner_id", None)
    assigner_type = getattr(i, "assigner_type", None)
    assigner_str = assigner_raw
    if not assigner_str and assigner_type and assigner_id:
        assigner_str = f"{fhir_enum(assigner_type)}/{assigner_id}"

    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": plain_immunization_codeable_concept(i.type_codings, i.type_text),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": assigner_str,
        "assigner_display": i.assigner_display,
        "assigner_identifier_use": fhir_enum(i.assigner_identifier_use) if i.assigner_identifier_use else None,
        "assigner_identifier_type_system": i.assigner_identifier_type_system,
        "assigner_identifier_type_version": i.assigner_identifier_type_version,
        "assigner_identifier_type_code": i.assigner_identifier_type_code,
        "assigner_identifier_type_display": i.assigner_identifier_type_display,
        "assigner_identifier_type_user_selected": i.assigner_identifier_type_user_selected,
        "assigner_identifier_type_text": i.assigner_identifier_type_text,
        "assigner_identifier_system": i.assigner_identifier_system,
        "assigner_identifier_value": i.assigner_identifier_value,
        "assigner_identifier_period_start": i.assigner_identifier_period_start,
        "assigner_identifier_period_end": i.assigner_identifier_period_end,
    }


def plain_immunization_performer(p: ImmunizationPerformerModel) -> dict:
    actor_data = plain_reference_with_identifier_fallback(p, "actor")
    return {
        "id": p.id,
        "function": plain_immunization_codeable_concept(p.function_codings, p.function_text),
        "actor": actor_data,
    }


def plain_immunization_note(n: ImmunizationNoteModel) -> dict:
    author_raw = n.author_reference
    author_id = n.author_id
    author_type = n.author_type
    author_str = author_raw
    if not author_str and author_type and author_id:
        author_str = f"{fhir_enum(author_type)}/{author_id}"

    return {
        "id": n.id,
        "text": n.text,
        "time": n.time,
        "author_string": n.author_string,
        "author_reference": author_str,
        "author_display": n.author_display,
        "author_identifier_use": fhir_enum(n.author_identifier_use) if n.author_identifier_use else None,
        "author_identifier_type_system": n.author_identifier_type_system,
        "author_identifier_type_version": n.author_identifier_type_version,
        "author_identifier_type_code": n.author_identifier_type_code,
        "author_identifier_type_display": n.author_identifier_type_display,
        "author_identifier_type_user_selected": n.author_identifier_type_user_selected,
        "author_identifier_type_text": n.author_identifier_type_text,
        "author_identifier_system": n.author_identifier_system,
        "author_identifier_value": n.author_identifier_value,
        "author_identifier_period_start": n.author_identifier_period_start,
        "author_identifier_period_end": n.author_identifier_period_end,
    }


def plain_immunization_education(e: ImmunizationEducationModel) -> dict:
    return {
        "id": e.id,
        "document_type": e.document_type,
        "reference": e.reference,
        "publication_date": e.publication_date,
        "presentation_date": e.presentation_date,
    }


def plain_immunization_reaction(r: ImmunizationReactionModel) -> dict:
    detail_data = plain_reference_with_identifier_fallback(r, "detail")
    return {
        "id": r.id,
        "date": r.date,
        "detail": detail_data if (detail_data.get("reference") or detail_data.get("reference_display")) else None,
        "reported": r.reported,
    }


def plain_immunization_protocol_applied(pa: ImmunizationProtocolAppliedModel) -> dict:
    auth_data = plain_reference_with_identifier_fallback(pa, "authority")
    target_diseases = []
    if pa.target_diseases:
        for td in pa.target_diseases:
            cc = plain_immunization_codeable_concept(td.codings, td.text)
            if cc:
                target_diseases.append(cc)

    return {
        "id": pa.id,
        "series": pa.series,
        "authority": auth_data if (auth_data.get("reference") or auth_data.get("reference_display")) else None,
        "target_disease": target_diseases if target_diseases else None,
        "dose_number_positive_int": pa.dose_number_positive_int,
        "dose_number_string": pa.dose_number_string,
        "series_doses_positive_int": pa.series_doses_positive_int,
        "series_doses_string": pa.series_doses_string,
    }


def to_plain_immunization(model: ImmunizationModel) -> dict:
    """Serialize ImmunizationModel to snake_case plain JSON response."""
    return {
        "id": model.immunization_id,
        "status": fhir_enum(model.status),
        "status_reason": plain_immunization_codeable_concept(
            model.status_reason_codings, model.status_reason_text
        ),
        "vaccine_code": plain_immunization_codeable_concept(
            model.vaccine_codings, model.vaccine_code_text
        ),
        "patient": plain_reference_with_identifier_fallback(model, "patient"),
        "encounter": (
            plain_reference_with_identifier_fallback(model, "encounter")
            if (model.encounter_reference or model.encounter_id or model.encounter_display)
            else None
        ),
        "occurrence_date_time": model.occurrence_date_time,
        "occurrence_string": model.occurrence_string,
        "recorded": model.recorded,
        "primary_source": model.primary_source,
        "report_origin": plain_immunization_codeable_concept(
            model.report_origin_codings, model.report_origin_text
        ),
        "location": (
            plain_reference_with_identifier_fallback(model, "location")
            if (model.location_reference or model.location_id or model.location_display)
            else None
        ),
        "manufacturer": (
            plain_reference_with_identifier_fallback(model, "manufacturer")
            if (model.manufacturer_reference or model.manufacturer_id or model.manufacturer_display)
            else None
        ),
        "lot_number": model.lot_number,
        "expiration_date": model.expiration_date,
        "site": plain_immunization_codeable_concept(model.site_codings, model.site_text),
        "route": plain_immunization_codeable_concept(model.route_codings, model.route_text),
        "dose_quantity": plain_simple_quantity(model, "dose_quantity"),
        "is_subpotent": model.is_subpotent,
        "funding_source": plain_immunization_codeable_concept(
            model.funding_source_codings, model.funding_source_text
        ),
        "identifier": (
            [plain_immunization_identifier(i) for i in model.identifiers]
            if model.identifiers
            else None
        ),
        "performer": (
            [plain_immunization_performer(p) for p in model.performers]
            if model.performers
            else None
        ),
        "note": (
            [plain_immunization_note(n) for n in model.notes]
            if model.notes
            else None
        ),
        "reason_code": (
            [
                plain_immunization_codeable_concept(rc.codings, rc.text)
                for rc in model.reason_codes
            ]
            if model.reason_codes
            else None
        ),
        "reason_reference": (
            [
                plain_reference_with_identifier_fallback(rr, "reference")
                for rr in model.reason_references
            ]
            if model.reason_references
            else None
        ),
        "subpotent_reason": (
            [
                plain_immunization_codeable_concept(sr.codings, sr.text)
                for sr in model.subpotent_reasons
            ]
            if model.subpotent_reasons
            else None
        ),
        "education": (
            [plain_immunization_education(e) for e in model.education_items]
            if model.education_items
            else None
        ),
        "program_eligibility": (
            [
                plain_immunization_codeable_concept(pe.codings, pe.text)
                for pe in model.program_eligibilities
            ]
            if model.program_eligibilities
            else None
        ),
        "reaction": (
            [plain_immunization_reaction(r) for r in model.reactions]
            if model.reactions
            else None
        ),
        "protocol_applied": (
            [plain_immunization_protocol_applied(pa) for pa in model.protocol_applied_items]
            if model.protocol_applied_items
            else None
        ),
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
