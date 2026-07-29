from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split

if TYPE_CHECKING:
    from app.models.patient.patient import (
        PatientAddress,
        PatientCommunication,
        PatientContact,
        PatientGeneralPractitioner,
        PatientIdentifier,
        PatientLink,
        PatientModel,
        PatientName,
        PatientPhoto,
        PatientTelecom,
    )


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Patient sub-resource
    row now carries these; not shared with other resources' equivalent mapper
    helpers since their sub-resource tables don't have these columns."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    """Flat `{prefix}_type`/`{prefix}_id`/`{prefix}_display` + `{prefix}_identifier_*`
    fallback fields for a resolved-or-logical Reference. Shared by every
    flattened Reference field on Patient (managingOrganization,
    contact.organization, generalPractitioner, link.other, identifier.assigner)."""
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    return {
        f"{prefix}_type": fhir_enum(getattr(obj, f"{prefix}_type", None)),
        f"{prefix}_id": getattr(obj, f"{prefix}_id", None),
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
        f"{prefix}_identifier_use": fhir_enum(
            getattr(obj, f"{prefix}_identifier_use", None)
        ),
        f"{prefix}_identifier_type_system": getattr(
            obj, f"{prefix}_identifier_type_system", None
        ),
        f"{prefix}_identifier_type_version": getattr(
            obj, f"{prefix}_identifier_type_version", None
        ),
        f"{prefix}_identifier_type_code": getattr(
            obj, f"{prefix}_identifier_type_code", None
        ),
        f"{prefix}_identifier_type_display": getattr(
            obj, f"{prefix}_identifier_type_display", None
        ),
        f"{prefix}_identifier_type_text": getattr(
            obj, f"{prefix}_identifier_type_text", None
        ),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_system": getattr(
            obj, f"{prefix}_identifier_system", None
        ),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": id_period_start.isoformat()
        if id_period_start
        else None,
        f"{prefix}_identifier_period_end": id_period_end.isoformat()
        if id_period_end
        else None,
    }


def plain_name(n: "PatientName") -> dict:
    """Patient.name (HumanName) → plain snake_case dict. Resource-specific
    (not the shared app.fhir.datatypes.plain_name) because PatientName now
    carries an audit trail that other resources' equivalent tables don't."""
    return {
        "id": n.id,
        "org_id": n.org_id,
        "use": fhir_enum(n.use),
        "text": n.text,
        "family": n.family,
        "given": fhir_split(n.given),
        "prefix": fhir_split(n.prefix),
        "suffix": fhir_split(n.suffix),
        "period_start": n.period_start.isoformat() if n.period_start else None,
        "period_end": n.period_end.isoformat() if n.period_end else None,
        **_audit_fields(n),
    }


def plain_identifier(i: "PatientIdentifier") -> dict:
    """Patient.identifier (Identifier) → plain snake_case dict. Resource-specific
    (not the shared app.fhir.datatypes.plain_identifier) because Patient's
    assigner is a resolved Reference(Organization) with an identifier fallback,
    unlike every other resource's flat assigner display string, and because
    PatientIdentifier now carries an audit trail."""
    return {
        "id": i.id,
        "org_id": i.org_id,
        "use": fhir_enum(i.use),
        "type_system": i.type_system,
        "type_version": i.type_version,
        "type_code": i.type_code,
        "type_display": i.type_display,
        "type_text": i.type_text,
        "type_user_selected": i.type_user_selected,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        **_plain_reference_fields(i, "assigner"),
        **_audit_fields(i),
    }


def plain_telecom(t: "PatientTelecom") -> dict:
    """Patient.telecom (ContactPoint) → plain snake_case dict. Resource-specific
    because PatientTelecom now carries an audit trail."""
    return {
        "id": t.id,
        "org_id": t.org_id,
        "system": fhir_enum(t.system),
        "value": t.value,
        "use": fhir_enum(t.use),
        "rank": t.rank,
        "period_start": t.period_start.isoformat() if t.period_start else None,
        "period_end": t.period_end.isoformat() if t.period_end else None,
        **_audit_fields(t),
    }


def plain_address(a: "PatientAddress") -> dict:
    """Patient.address (Address) → plain snake_case dict. Resource-specific
    because PatientAddress now carries an audit trail."""
    return {
        "id": a.id,
        "org_id": a.org_id,
        "use": fhir_enum(a.use),
        "type": fhir_enum(a.type),
        "text": a.text,
        "line": fhir_split(a.line),
        "city": a.city,
        "district": a.district,
        "state": a.state,
        "postal_code": a.postal_code,
        "country": a.country,
        "period_start": a.period_start.isoformat() if a.period_start else None,
        "period_end": a.period_end.isoformat() if a.period_end else None,
        **_audit_fields(a),
    }


def plain_photo(p: "PatientPhoto") -> dict:
    """Patient.photo (Attachment) → plain snake_case dict. Resource-specific
    because PatientPhoto now carries an audit trail."""
    return {
        "id": p.id,
        "org_id": p.org_id,
        "content_type": p.content_type,
        "language": p.language,
        "data": p.data,
        "url": p.url,
        "size": p.size,
        "hash": p.hash,
        "title": p.title,
        "creation": p.creation.isoformat() if p.creation else None,
        **_audit_fields(p),
    }


def plain_communication(cm: "PatientCommunication") -> dict:
    """Patient.communication BackboneElement → plain snake_case dict.
    Resource-specific because PatientCommunication now carries an audit trail."""
    return {
        "id": cm.id,
        "org_id": cm.org_id,
        "language_system": cm.language_system,
        "language_version": cm.language_version,
        "language_code": cm.language_code,
        "language_display": cm.language_display,
        "language_text": cm.language_text,
        "language_user_selected": cm.language_user_selected,
        "preferred": cm.preferred,
        **_audit_fields(cm),
    }


def plain_contact(c: "PatientContact") -> dict:
    """Patient.contact BackboneElement → plain snake_case dict, including the
    relationship[] and telecom[] grandchildren inline."""
    return {
        "id": c.id,
        "org_id": c.org_id,
        "relationship": [
            {
                "id": r.id,
                "org_id": r.org_id,
                "coding_system": r.coding_system,
                "coding_version": r.coding_version,
                "coding_code": r.coding_code,
                "coding_display": r.coding_display,
                "text": r.text,
                "coding_user_selected": r.coding_user_selected,
                **_audit_fields(r),
            }
            for r in c.relationships
        ]
        if c.relationships
        else None,
        "name_use": fhir_enum(c.name_use),
        "name_text": c.name_text,
        "name_family": c.name_family,
        "name_given": fhir_split(c.name_given),
        "name_prefix": fhir_split(c.name_prefix),
        "name_suffix": fhir_split(c.name_suffix),
        "name_period_start": c.name_period_start.isoformat()
        if c.name_period_start
        else None,
        "name_period_end": c.name_period_end.isoformat()
        if c.name_period_end
        else None,
        "telecom": [
            {
                "id": t.id,
                "org_id": t.org_id,
                "system": fhir_enum(t.system),
                "value": t.value,
                "use": fhir_enum(t.use),
                "rank": t.rank,
                "period_start": t.period_start.isoformat() if t.period_start else None,
                "period_end": t.period_end.isoformat() if t.period_end else None,
                **_audit_fields(t),
            }
            for t in c.telecoms
        ]
        if c.telecoms
        else None,
        "address_use": fhir_enum(c.address_use),
        "address_type": fhir_enum(c.address_type),
        "address_text": c.address_text,
        "address_line": fhir_split(c.address_line),
        "address_city": c.address_city,
        "address_district": c.address_district,
        "address_state": c.address_state,
        "address_postal_code": c.address_postal_code,
        "address_country": c.address_country,
        "address_period_start": c.address_period_start.isoformat()
        if c.address_period_start
        else None,
        "address_period_end": c.address_period_end.isoformat()
        if c.address_period_end
        else None,
        "gender": fhir_enum(c.gender),
        **_plain_reference_fields(c, "organization"),
        "period_start": c.period_start.isoformat() if c.period_start else None,
        "period_end": c.period_end.isoformat() if c.period_end else None,
        **_audit_fields(c),
    }


def plain_general_practitioner(gp: "PatientGeneralPractitioner") -> dict:
    """Patient.generalPractitioner (Reference) → plain snake_case dict."""
    return {
        "id": gp.id,
        "org_id": gp.org_id,
        **_plain_reference_fields(gp, "reference"),
        **_audit_fields(gp),
    }


def plain_link(lk: "PatientLink") -> dict:
    """Patient.link BackboneElement → plain snake_case dict."""
    return {
        "id": lk.id,
        "org_id": lk.org_id,
        **_plain_reference_fields(lk, "other"),
        "type": fhir_enum(lk.type),
        **_audit_fields(lk),
    }


def _core_fields(patient: "PatientModel") -> dict:
    """
    Scalar-column-only fields shared by to_plain_patient() and
    to_plain_patient_core() — deliberately never touches a relationship
    attribute (patient.names, patient.identifiers, ...), so it's safe to call
    on a PatientModel fetched without the selectinload options (see
    PatientRepository.get_core_by_patient_id()): touching an unloaded
    relationship on an async session raises rather than lazy-loading.
    """
    return {
        "id": patient.patient_id,
        "user_id": patient.user_id,
        "org_id": patient.org_id,
        "active": patient.active,
        "gender": fhir_enum(patient.gender) if patient.gender else None,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "deceased_boolean": patient.deceased_boolean,
        "deceased_datetime": patient.deceased_datetime.isoformat()
        if patient.deceased_datetime
        else None,
        "marital_status_system": patient.marital_status_system,
        "marital_status_version": patient.marital_status_version,
        "marital_status_code": patient.marital_status_code,
        "marital_status_display": patient.marital_status_display,
        "marital_status_text": patient.marital_status_text,
        "marital_status_user_selected": patient.marital_status_user_selected,
        "multiple_birth_boolean": patient.multiple_birth_boolean,
        "multiple_birth_integer": patient.multiple_birth_integer,
        **_plain_reference_fields(patient, "managing_organization"),
        "created_at": patient.created_at.isoformat() if patient.created_at else None,
        "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
        "created_by": patient.created_by,
        "updated_by": patient.updated_by,
    }


def to_plain_patient_core(patient: "PatientModel") -> dict:
    """Patient table scalars only — no sub-resource arrays. Backs GET /{patient_id}/core."""
    return {k: v for k, v in _core_fields(patient).items() if v is not None}


def to_plain_patient(patient: "PatientModel") -> dict:
    """Full plain snake_case Patient representation, including every
    populated sub-resource array. Backs GET /{patient_id} and the
    create/patch routes."""
    result: dict = _core_fields(patient)

    if patient.names:
        result["name"] = [plain_name(n) for n in patient.names]
    if patient.identifiers:
        result["identifier"] = [plain_identifier(i) for i in patient.identifiers]
    if patient.telecoms:
        result["telecom"] = [plain_telecom(t) for t in patient.telecoms]
    if patient.addresses:
        result["address"] = [plain_address(a) for a in patient.addresses]
    if patient.photos:
        result["photo"] = [plain_photo(p) for p in patient.photos]
    if patient.contacts:
        result["contact"] = [plain_contact(c) for c in patient.contacts]
    if patient.communications:
        result["communication"] = [
            plain_communication(cm) for cm in patient.communications
        ]
    if patient.general_practitioners:
        result["general_practitioner"] = [
            plain_general_practitioner(gp) for gp in patient.general_practitioners
        ]
    if patient.links:
        result["link"] = [plain_link(lk) for lk in patient.links]

    return {k: v for k, v in result.items() if v is not None}
