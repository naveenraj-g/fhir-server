from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.patient.input import (
        PatientAddressInput,
        PatientCommunicationInput,
        PatientContactInput,
        PatientCreateSchema,
        PatientGeneralPractitionerInput,
        PatientIdentifierInput,
        PatientLinkInput,
        PatientNameInput,
        PatientPatchSchema,
        PatientPhotoInput,
        PatientTelecomInput,
    )


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
        for k, v in {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        }.items()
        if v
    }
    return period or None


def _reference_from_payload(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, prefix, None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(
        obj, f"{prefix}_identifier_type_user_selected", None
    )
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_code
        or id_type_text
        or id_system
        or id_value
    ):
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
        period = _period(id_period_start, id_period_end)
        if period:
            identifier["period"] = period
        entry["identifier"] = identifier
    return entry


def payload_identifier(i: PatientIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
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
    assigner = _reference_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def payload_name(n: PatientNameInput) -> dict:
    entry: dict = {}
    if n.use:
        entry["use"] = fhir_enum(n.use)
    if n.text:
        entry["text"] = n.text
    if n.family:
        entry["family"] = n.family
    if n.given:
        entry["given"] = list(n.given)
    if n.prefix:
        entry["prefix"] = list(n.prefix)
    if n.suffix:
        entry["suffix"] = list(n.suffix)
    period = _period(n.period_start, n.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_telecom(t: PatientTelecomInput) -> dict:
    entry: dict = {}
    if t.system:
        entry["system"] = fhir_enum(t.system)
    if t.value:
        entry["value"] = t.value
    if t.use:
        entry["use"] = fhir_enum(t.use)
    if t.rank is not None:
        entry["rank"] = t.rank
    period = _period(t.period_start, t.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_address(a: PatientAddressInput) -> dict:
    entry: dict = {}
    if a.use:
        entry["use"] = fhir_enum(a.use)
    if a.type:
        entry["type"] = fhir_enum(a.type)
    if a.text:
        entry["text"] = a.text
    if a.line:
        entry["line"] = list(a.line)
    if a.city:
        entry["city"] = a.city
    if a.district:
        entry["district"] = a.district
    if a.state:
        entry["state"] = a.state
    if a.postal_code:
        entry["postalCode"] = a.postal_code
    if a.country:
        entry["country"] = a.country
    period = _period(a.period_start, a.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_photo(ph: PatientPhotoInput) -> dict:
    entry: dict = {}
    if ph.content_type:
        entry["contentType"] = ph.content_type
    if ph.language:
        entry["language"] = ph.language
    if ph.data:
        entry["data"] = ph.data
    if ph.url:
        entry["url"] = ph.url
    if ph.size is not None:
        entry["size"] = ph.size
    if ph.hash:
        entry["hash"] = ph.hash
    if ph.title:
        entry["title"] = ph.title
    if ph.creation:
        entry["creation"] = ph.creation.isoformat()
    return entry


def payload_contact(c: PatientContactInput) -> dict:
    entry: dict = {}
    relationships = []
    for r in c.relationship or []:
        coding = _coding_list(r.coding)
        if coding or r.text:
            rel: dict = {}
            if coding:
                rel["coding"] = coding
            if r.text:
                rel["text"] = r.text
            relationships.append(rel)
    if relationships:
        entry["relationship"] = relationships

    name_dict: dict = {}
    if c.name_use:
        name_dict["use"] = fhir_enum(c.name_use)
    if c.name_text:
        name_dict["text"] = c.name_text
    if c.name_family:
        name_dict["family"] = c.name_family
    if c.name_given:
        name_dict["given"] = list(c.name_given)
    if c.name_prefix:
        name_dict["prefix"] = list(c.name_prefix)
    if c.name_suffix:
        name_dict["suffix"] = list(c.name_suffix)
    period = _period(c.name_period_start, c.name_period_end)
    if period:
        name_dict["period"] = period
    if name_dict:
        entry["name"] = name_dict

    telecoms = [payload_telecom(t) for t in (c.telecom or [])]
    telecoms = [t for t in telecoms if t]
    if telecoms:
        entry["telecom"] = telecoms

    address_dict: dict = {}
    if c.address_use:
        address_dict["use"] = fhir_enum(c.address_use)
    if c.address_type:
        address_dict["type"] = fhir_enum(c.address_type)
    if c.address_text:
        address_dict["text"] = c.address_text
    if c.address_line:
        address_dict["line"] = list(c.address_line)
    if c.address_city:
        address_dict["city"] = c.address_city
    if c.address_district:
        address_dict["district"] = c.address_district
    if c.address_state:
        address_dict["state"] = c.address_state
    if c.address_postal_code:
        address_dict["postalCode"] = c.address_postal_code
    if c.address_country:
        address_dict["country"] = c.address_country
    addr_period = _period(c.address_period_start, c.address_period_end)
    if addr_period:
        address_dict["period"] = addr_period
    if address_dict:
        entry["address"] = address_dict

    if c.gender:
        entry["gender"] = fhir_enum(c.gender)

    org = _reference_from_payload(c, "organization")
    if org:
        entry["organization"] = org

    contact_period = _period(c.period_start, c.period_end)
    if contact_period:
        entry["period"] = contact_period

    return entry


def payload_communication(c: PatientCommunicationInput) -> dict:
    entry: dict = {}
    coding = _coding_list(c.language_coding)
    if coding or c.language_text:
        lang: dict = {}
        if coding:
            lang["coding"] = coding
        if c.language_text:
            lang["text"] = c.language_text
        entry["language"] = lang
    if c.preferred is not None:
        entry["preferred"] = c.preferred
    return entry


def payload_general_practitioner(gp: PatientGeneralPractitionerInput) -> dict:
    return _reference_from_payload(gp, "reference")


def payload_link(l: PatientLinkInput) -> dict:
    entry: dict = {}
    other = _reference_from_payload(l, "other")
    if other:
        entry["other"] = other
    if l.type:
        raw_type = fhir_enum(l.type)
        entry["type"] = raw_type.replace("_", "-") if raw_type else None
    return entry


_LIST_FIELDS = {
    "identifier": payload_identifier,
    "name": payload_name,
    "telecom": payload_telecom,
    "address": payload_address,
    "photo": payload_photo,
    "contact": payload_contact,
    "communication": payload_communication,
    "general_practitioner": payload_general_practitioner,
    "link": payload_link,
}

_FHIR_KEY_FOR_LIST = {
    "identifier": "identifier",
    "name": "name",
    "telecom": "telecom",
    "address": "address",
    "photo": "photo",
    "contact": "contact",
    "communication": "communication",
    "general_practitioner": "generalPractitioner",
    "link": "link",
}


def payload_to_fhir_patient(payload: PatientCreateSchema) -> dict:
    result: dict = {"resourceType": "Patient"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    if payload.active is not None:
        result["active"] = payload.active
    if payload.gender:
        result["gender"] = fhir_enum(payload.gender)
    if payload.birth_date:
        result["birthDate"] = payload.birth_date.isoformat()
    if payload.deceased_boolean is not None:
        result["deceasedBoolean"] = payload.deceased_boolean
    if payload.deceased_date_time:
        result["deceasedDateTime"] = payload.deceased_date_time.isoformat()

    marital_codings = _coding_list(payload.marital_status_coding)
    if marital_codings or payload.marital_status_text:
        ms: dict = {}
        if marital_codings:
            ms["coding"] = marital_codings
        if payload.marital_status_text:
            ms["text"] = payload.marital_status_text
        result["maritalStatus"] = ms

    if payload.multiple_birth_boolean is not None:
        result["multipleBirthBoolean"] = payload.multiple_birth_boolean
    if payload.multiple_birth_integer is not None:
        result["multipleBirthInteger"] = payload.multiple_birth_integer

    managing_org = _reference_from_payload(payload, "managing_organization")
    if managing_org:
        result["managingOrganization"] = managing_org

    for field, builder in _LIST_FIELDS.items():
        fhir_key = _FHIR_KEY_FOR_LIST[field]
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [item for item in items if item]
        if items:
            result[fhir_key] = items

    return result


def patch_fragment_to_fhir_patient(
    payload: PatientPatchSchema,
) -> tuple[dict, set[str]]:
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)
    if "active" in provided:
        touched.add("active")
        if payload.active is not None:
            fragment["active"] = payload.active
    if "gender" in provided:
        touched.add("gender")
        if payload.gender:
            fragment["gender"] = fhir_enum(payload.gender)
    if "birth_date" in provided:
        touched.add("birthDate")
        if payload.birth_date:
            fragment["birthDate"] = payload.birth_date.isoformat()
    if "deceased_boolean" in provided:
        touched.add("deceasedBoolean")
        if payload.deceased_boolean is not None:
            fragment["deceasedBoolean"] = payload.deceased_boolean
    if "deceased_date_time" in provided:
        touched.add("deceasedDateTime")
        if payload.deceased_date_time:
            fragment["deceasedDateTime"] = payload.deceased_date_time.isoformat()

    if "marital_status_text" in provided or "marital_status_coding" in provided:
        touched.add("maritalStatus")
        marital_codings = _coding_list(payload.marital_status_coding)
        if marital_codings or payload.marital_status_text:
            ms: dict = {}
            if marital_codings:
                ms["coding"] = marital_codings
            if payload.marital_status_text:
                ms["text"] = payload.marital_status_text
            fragment["maritalStatus"] = ms

    if "multiple_birth_boolean" in provided:
        touched.add("multipleBirthBoolean")
        if payload.multiple_birth_boolean is not None:
            fragment["multipleBirthBoolean"] = payload.multiple_birth_boolean
    if "multiple_birth_integer" in provided:
        touched.add("multipleBirthInteger")
        if payload.multiple_birth_integer is not None:
            fragment["multipleBirthInteger"] = payload.multiple_birth_integer

    managing_org_fields = {
        "managing_organization",
        "managing_organization_display",
        "managing_organization_identifier_system",
        "managing_organization_identifier_value",
        "managing_organization_identifier_use",
        "managing_organization_identifier_type_text",
    }
    if any(f in provided for f in managing_org_fields):
        touched.add("managingOrganization")
        managing_org = _reference_from_payload(payload, "managing_organization")
        if managing_org:
            fragment["managingOrganization"] = managing_org

    for field, builder in _LIST_FIELDS.items():
        if field in provided:
            fhir_key = _FHIR_KEY_FOR_LIST[field]
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [item for item in items if item]
            if items:
                fragment[fhir_key] = items

    return fragment, touched
