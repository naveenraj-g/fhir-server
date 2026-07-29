from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import (
    fhir_address,
    fhir_communication,
    fhir_enum,
    fhir_human_name,
    fhir_photo,
    fhir_split,
    fhir_telecom,
)

if TYPE_CHECKING:
    from app.models.patient.patient import (
        PatientContact,
        PatientGeneralPractitioner,
        PatientIdentifier,
        PatientLink,
        PatientModel,
    )


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on Patient (managingOrganization, contact.organization,
    generalPractitioner, link.other, identifier.assigner)."""
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

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
                for k, v in {
                    "start": id_period_start.isoformat() if id_period_start else None,
                    "end": id_period_end.isoformat() if id_period_end else None,
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def fhir_identifier(i: PatientIdentifier) -> dict:
    """Patient.identifier (Identifier) → FHIR camelCase dict. Resource-specific
    (not the shared app.fhir.datatypes.fhir_identifier) because Patient's
    assigner is a resolved Reference(Organization) with an identifier fallback,
    unlike every other resource's flat assigner display string."""
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.type_system or i.type_code or i.type_text:
        type_cc: dict = {}
        if i.type_system or i.type_code:
            type_cc["coding"] = [
                {
                    k: v
                    for k, v in {
                        "system": i.type_system,
                        "version": i.type_version,
                        "code": i.type_code,
                        "display": i.type_display,
                        "userSelected": i.type_user_selected,
                    }.items()
                    if v is not None
                }
            ]
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": i.period_start.isoformat() if i.period_start else None,
                "end": i.period_end.isoformat() if i.period_end else None,
            }.items()
            if v
        }
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_contact(c: PatientContact) -> dict:
    """Patient.contact BackboneElement → FHIR camelCase dict. Builds
    relationship/name/address/organization/period sub-structures, each
    included only if at least one of its fields is set."""
    entry: dict = {}
    if c.relationships:
        entry["relationship"] = [
            {
                k: v
                for k, v in {
                    "coding": [
                        {
                            k2: v2
                            for k2, v2 in {
                                "system": r.coding_system,
                                "version": r.coding_version,
                                "code": r.coding_code,
                                "display": r.coding_display,
                                "userSelected": r.coding_user_selected,
                            }.items()
                            if v2 is not None
                        }
                    ],
                    "text": r.text,
                }.items()
                if v
            }
            for r in c.relationships
        ]
    name_entry: dict = {}
    if c.name_use:
        name_entry["use"] = fhir_enum(c.name_use)
    if c.name_text:
        name_entry["text"] = c.name_text
    if c.name_family:
        name_entry["family"] = c.name_family
    given = fhir_split(c.name_given)
    if given:
        name_entry["given"] = given
    prefix = fhir_split(c.name_prefix)
    if prefix:
        name_entry["prefix"] = prefix
    suffix = fhir_split(c.name_suffix)
    if suffix:
        name_entry["suffix"] = suffix
    if c.name_period_start or c.name_period_end:
        name_entry["period"] = {
            k: v
            for k, v in {
                "start": c.name_period_start.isoformat()
                if c.name_period_start
                else None,
                "end": c.name_period_end.isoformat() if c.name_period_end else None,
            }.items()
            if v
        }
    if name_entry:
        entry["name"] = name_entry
    if c.telecoms:
        entry["telecom"] = [fhir_telecom(t) for t in c.telecoms]
    addr_entry: dict = {}
    if c.address_use:
        addr_entry["use"] = fhir_enum(c.address_use)
    if c.address_type:
        addr_entry["type"] = fhir_enum(c.address_type)
    if c.address_text:
        addr_entry["text"] = c.address_text
    addr_lines = fhir_split(c.address_line)
    if addr_lines:
        addr_entry["line"] = addr_lines
    if c.address_city:
        addr_entry["city"] = c.address_city
    if c.address_district:
        addr_entry["district"] = c.address_district
    if c.address_state:
        addr_entry["state"] = c.address_state
    if c.address_postal_code:
        addr_entry["postalCode"] = c.address_postal_code
    if c.address_country:
        addr_entry["country"] = c.address_country
    if c.address_period_start or c.address_period_end:
        addr_entry["period"] = {
            k: v
            for k, v in {
                "start": c.address_period_start.isoformat()
                if c.address_period_start
                else None,
                "end": c.address_period_end.isoformat()
                if c.address_period_end
                else None,
            }.items()
            if v
        }
    if addr_entry:
        entry["address"] = addr_entry
    if c.gender:
        entry["gender"] = fhir_enum(c.gender)
    organization = _fhir_reference(c, "organization")
    if organization:
        entry["organization"] = organization
    if c.period_start or c.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": c.period_start.isoformat() if c.period_start else None,
                "end": c.period_end.isoformat() if c.period_end else None,
            }.items()
            if v
        }
    return entry


def fhir_general_practitioner(gp: PatientGeneralPractitioner) -> dict:
    """Patient.generalPractitioner (Reference) → FHIR camelCase dict."""
    return _fhir_reference(gp, "reference")


def fhir_link(lk: PatientLink) -> dict:
    """Patient.link BackboneElement → FHIR camelCase dict."""
    other = _fhir_reference(lk, "other")
    entry: dict = {"other": other}
    if lk.type:
        entry["type"] = fhir_enum(lk.type)
    return entry


def _core_fields(patient: PatientModel) -> dict:
    """
    Scalar-column-only fields shared by to_fhir_patient() and
    to_fhir_patient_core() — deliberately never touches a relationship
    attribute (patient.names, patient.identifiers, ...), so it's safe to call
    on a PatientModel fetched without the selectinload options (see
    PatientRepository.get_core_by_patient_id()): touching an unloaded
    relationship on an async session raises rather than lazy-loading.
    """
    result: dict = {
        "resourceType": "Patient",
        "id": str(patient.patient_id),
        "active": patient.active,
        "gender": fhir_enum(patient.gender) if patient.gender else None,
        "birthDate": patient.birth_date.isoformat() if patient.birth_date else None,
        "deceasedBoolean": patient.deceased_boolean,
        "deceasedDateTime": patient.deceased_datetime.isoformat()
        if patient.deceased_datetime
        else None,
    }

    if patient.marital_status_code or patient.marital_status_text:
        cc: dict = {}
        if patient.marital_status_system or patient.marital_status_code:
            cc["coding"] = [
                {
                    k: v
                    for k, v in {
                        "system": patient.marital_status_system,
                        "version": patient.marital_status_version,
                        "code": patient.marital_status_code,
                        "display": patient.marital_status_display,
                        "userSelected": patient.marital_status_user_selected,
                    }.items()
                    if v is not None
                }
            ]
        if patient.marital_status_text:
            cc["text"] = patient.marital_status_text
        result["maritalStatus"] = cc

    if patient.multiple_birth_integer is not None:
        result["multipleBirthInteger"] = patient.multiple_birth_integer
    elif patient.multiple_birth_boolean is not None:
        result["multipleBirthBoolean"] = patient.multiple_birth_boolean

    managing_organization = _fhir_reference(patient, "managing_organization")
    if managing_organization:
        result["managingOrganization"] = managing_organization

    return result


def to_fhir_patient_core(patient: PatientModel) -> dict:
    """Patient table scalars only — no sub-resource arrays. Backs GET /{patient_id}/core."""
    return {k: v for k, v in _core_fields(patient).items() if v is not None}


def to_fhir_patient(patient: PatientModel) -> dict:
    """Full FHIR R4 Patient representation, including every populated
    sub-resource array. Backs GET /{patient_id} and the create/patch routes."""
    result: dict = _core_fields(patient)

    if patient.names:
        result["name"] = [fhir_human_name(n) for n in patient.names]
    if patient.identifiers:
        result["identifier"] = [fhir_identifier(i) for i in patient.identifiers]
    if patient.telecoms:
        result["telecom"] = [fhir_telecom(t) for t in patient.telecoms]
    if patient.addresses:
        result["address"] = [fhir_address(a) for a in patient.addresses]
    if patient.photos:
        result["photo"] = [fhir_photo(p) for p in patient.photos]
    if patient.contacts:
        result["contact"] = [fhir_contact(c) for c in patient.contacts]
    if patient.communications:
        result["communication"] = [
            fhir_communication(cm) for cm in patient.communications
        ]
    if patient.general_practitioners:
        result["generalPractitioner"] = [
            fhir_general_practitioner(gp) for gp in patient.general_practitioners
        ]
    if patient.links:
        result["link"] = [fhir_link(lk) for lk in patient.links]

    return {k: v for k, v in result.items() if v is not None}
