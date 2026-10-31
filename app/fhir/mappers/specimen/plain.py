from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.specimen import SpecimenModel


def _audit_fields(obj) -> dict:
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        **_audit_fields(c),
    }


def _plain_reference(obj, prefix: str) -> dict | None:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    if not (raw_reference or ref_type or ref_id or display):
        return None

    return {
        "reference": raw_reference or (f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None),
        "id": ref_id,
        "type": fhir_enum(ref_type) if ref_type else None,
        "display": display,
    }


def plain_specimen_identifier(i) -> dict:
    ref_type = i.assigner_type
    ref_id = i.assigner_id
    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type_text": i.type_text,
        "type_codings": [plain_coding(c) for c in (i.type_codings or [])],
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        "assigner_reference": i.assigner_reference,
        "assigner_id": ref_id,
        "assigner_type": fhir_enum(ref_type) if ref_type else None,
        "assigner_display": i.assigner_display,
        **_audit_fields(i),
    }


def plain_specimen_accession_identifier(model: SpecimenModel) -> dict | None:
    if not (
        model.accession_identifier_use
        or model.accession_identifier_type_text
        or model.accession_identifier_system
        or model.accession_identifier_value
        or model.accession_identifier_type_codings
        or model.accession_identifier_assigner_reference
        or model.accession_identifier_assigner_id
    ):
        return None

    return {
        "use": fhir_enum(model.accession_identifier_use) if model.accession_identifier_use else None,
        "type_text": model.accession_identifier_type_text,
        "type_codings": [plain_coding(c) for c in (model.accession_identifier_type_codings or [])],
        "system": model.accession_identifier_system,
        "value": model.accession_identifier_value,
        "period_start": model.accession_identifier_period_start.isoformat() if model.accession_identifier_period_start else None,
        "period_end": model.accession_identifier_period_end.isoformat() if model.accession_identifier_period_end else None,
        "assigner_reference": model.accession_identifier_assigner_reference,
        "assigner_id": model.accession_identifier_assigner_id,
        "assigner_type": fhir_enum(model.accession_identifier_assigner_type) if model.accession_identifier_assigner_type else None,
        "assigner_display": model.accession_identifier_assigner_display,
    }


def plain_specimen_collection(model: SpecimenModel) -> dict | None:
    collector = _plain_reference(model, "collection_collector")
    method_codings = [plain_coding(c) for c in (model.collection_method_codings or [])]
    body_site_codings = [plain_coding(c) for c in (model.collection_body_site_codings or [])]
    fasting_codings = [plain_coding(c) for c in (model.collection_fasting_status_codings or [])]

    has_data = any([
        collector,
        model.collection_collected_date_time,
        model.collection_collected_period_start,
        model.collection_collected_period_end,
        model.collection_duration_value is not None,
        model.collection_quantity_value is not None,
        model.collection_method_text,
        method_codings,
        model.collection_body_site_text,
        body_site_codings,
        model.collection_fasting_status_text,
        fasting_codings,
        model.collection_fasting_status_duration_value is not None,
    ])
    if not has_data:
        return None

    method = None
    if model.collection_method_text or method_codings:
        method = {
            "text": model.collection_method_text,
            "codings": method_codings,
        }

    body_site = None
    if model.collection_body_site_text or body_site_codings:
        body_site = {
            "text": model.collection_body_site_text,
            "codings": body_site_codings,
        }

    fasting_status = None
    if model.collection_fasting_status_text or fasting_codings:
        fasting_status = {
            "text": model.collection_fasting_status_text,
            "codings": fasting_codings,
        }

    return {
        "collector": collector,
        "collected_date_time": model.collection_collected_date_time.isoformat() if model.collection_collected_date_time else None,
        "collected_period_start": model.collection_collected_period_start.isoformat() if model.collection_collected_period_start else None,
        "collected_period_end": model.collection_collected_period_end.isoformat() if model.collection_collected_period_end else None,
        "duration_value": float(model.collection_duration_value) if model.collection_duration_value is not None else None,
        "duration_comparator": fhir_enum(model.collection_duration_comparator) if model.collection_duration_comparator else None,
        "duration_unit": model.collection_duration_unit,
        "duration_system": model.collection_duration_system,
        "duration_code": model.collection_duration_code,
        "quantity_value": float(model.collection_quantity_value) if model.collection_quantity_value is not None else None,
        "quantity_unit": model.collection_quantity_unit,
        "quantity_system": model.collection_quantity_system,
        "quantity_code": model.collection_quantity_code,
        "method": method,
        "body_site": body_site,
        "fasting_status_codeable_concept": fasting_status,
        "fasting_status_duration_value": float(model.collection_fasting_status_duration_value) if model.collection_fasting_status_duration_value is not None else None,
        "fasting_status_duration_comparator": fhir_enum(model.collection_fasting_status_duration_comparator) if model.collection_fasting_status_duration_comparator else None,
        "fasting_status_duration_unit": model.collection_fasting_status_duration_unit,
        "fasting_status_duration_system": model.collection_fasting_status_duration_system,
        "fasting_status_duration_code": model.collection_fasting_status_duration_code,
    }


def plain_specimen_processing(p) -> dict:
    procedure_codings = [plain_coding(c) for c in (p.procedure_codings or [])]
    procedure = None
    if p.procedure_text or procedure_codings:
        procedure = {
            "text": p.procedure_text,
            "codings": procedure_codings,
        }

    return {
        "id": p.id,
        "description": p.description,
        "procedure": procedure,
        "additive": [
            _plain_reference(a, "reference")
            for a in (p.additives or [])
            if _plain_reference(a, "reference") is not None
        ],
        "time_date_time": p.time_date_time.isoformat() if p.time_date_time else None,
        "time_period_start": p.time_period_start.isoformat() if p.time_period_start else None,
        "time_period_end": p.time_period_end.isoformat() if p.time_period_end else None,
        **_audit_fields(p),
    }


def plain_specimen_container(c) -> dict:
    type_codings = [plain_coding(tc) for tc in (c.type_codings or [])]
    ctype = None
    if c.type_text or type_codings:
        ctype = {
            "text": c.type_text,
            "codings": type_codings,
        }

    additive_codings = [plain_coding(ac) for ac in (c.additive_codings or [])]
    additive_concept = None
    if c.additive_codeable_concept_text or additive_codings:
        additive_concept = {
            "text": c.additive_codeable_concept_text,
            "codings": additive_codings,
        }

    additive_ref = _plain_reference(c, "additive_reference")

    return {
        "id": c.id,
        "identifier": [plain_specimen_identifier(i) for i in (c.identifiers or [])],
        "description": c.description,
        "type": ctype,
        "capacity_value": float(c.capacity_value) if c.capacity_value is not None else None,
        "capacity_unit": c.capacity_unit,
        "capacity_system": c.capacity_system,
        "capacity_code": c.capacity_code,
        "specimen_quantity_value": float(c.specimen_quantity_value) if c.specimen_quantity_value is not None else None,
        "specimen_quantity_unit": c.specimen_quantity_unit,
        "specimen_quantity_system": c.specimen_quantity_system,
        "specimen_quantity_code": c.specimen_quantity_code,
        "additive_codeable_concept": additive_concept,
        "additive_reference": additive_ref,
        **_audit_fields(c),
    }


def plain_specimen_condition(cond) -> dict:
    return {
        "id": cond.id,
        "text": cond.text,
        "codings": [plain_coding(c) for c in (cond.codings or [])],
        **_audit_fields(cond),
    }


def plain_specimen_note(n) -> dict:
    ref = _plain_reference(n, "author")
    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": ref["reference"] if ref else None,
        "author_id": ref["id"] if ref else None,
        "author_type": ref["type"] if ref else None,
        "author_display": ref["display"] if ref else None,
        "time": n.time.isoformat() if n.time else None,
        "text": n.text,
        **_audit_fields(n),
    }


def to_plain_specimen(specimen: SpecimenModel) -> dict:
    """Transform SpecimenModel to plain snake_case dictionary."""
    type_codings = [plain_coding(c) for c in (specimen.type_codings or [])]
    type_concept = None
    if specimen.type_text or type_codings:
        type_concept = {
            "text": specimen.type_text,
            "codings": type_codings,
        }

    return {
        "id": specimen.specimen_id,
        "identifier": [plain_specimen_identifier(i) for i in (specimen.identifiers or [])],
        "accession_identifier": plain_specimen_accession_identifier(specimen),
        "status": fhir_enum(specimen.status) if specimen.status else None,
        "type": type_concept,
        "subject": _plain_reference(specimen, "subject"),
        "received_time": specimen.received_time.isoformat() if specimen.received_time else None,
        "parent": [
            _plain_reference(p, "reference")
            for p in (specimen.parents or [])
            if _plain_reference(p, "reference") is not None
        ],
        "request": [
            _plain_reference(r, "reference")
            for r in (specimen.requests or [])
            if _plain_reference(r, "reference") is not None
        ],
        "collection": plain_specimen_collection(specimen),
        "processing": [plain_specimen_processing(p) for p in (specimen.processings or [])],
        "container": [plain_specimen_container(c) for c in (specimen.containers or [])],
        "condition": [plain_specimen_condition(cond) for cond in (specimen.conditions or [])],
        "note": [plain_specimen_note(n) for n in (specimen.notes or [])],
        "extension": specimen.extension or [],
        **_audit_fields(specimen),
    }
