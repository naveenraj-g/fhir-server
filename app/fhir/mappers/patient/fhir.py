from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.patient import (
        PatientContact,
        PatientIdentifier,
        PatientModel,
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
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def fhir_patient_identifier(i: PatientIdentifier) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    coding = _fhir_coding_list(i.type_codings)
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
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start),
                "end": fhir_instant(i.period_end),
            }.items()
            if v
        }
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_patient_name(n) -> dict:
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
    if n.period_start or n.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(n.period_start),
                "end": fhir_instant(n.period_end),
            }.items()
            if v
        }
    return entry


def fhir_patient_telecom(t) -> dict:
    entry: dict = {}
    if t.system:
        entry["system"] = fhir_enum(t.system)
    if t.value:
        entry["value"] = t.value
    if t.use:
        entry["use"] = fhir_enum(t.use)
    if t.rank is not None:
        entry["rank"] = t.rank
    if t.period_start or t.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(t.period_start),
                "end": fhir_instant(t.period_end),
            }.items()
            if v
        }
    return entry


def fhir_patient_address(a) -> dict:
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
    if a.period_start or a.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(a.period_start),
                "end": fhir_instant(a.period_end),
            }.items()
            if v
        }
    return entry


def fhir_patient_photo(ph) -> dict:
    entry: dict = {}
    if ph.content_type:
        entry["contentType"] = ph.content_type
    if ph.language:
        entry["language"] = ph.language
    if ph.data:
        import base64
        entry["data"] = base64.b64encode(ph.data).decode("ascii")
    if ph.url:
        entry["url"] = ph.url
    if ph.size is not None:
        entry["size"] = ph.size
    if ph.hash:
        import base64
        entry["hash"] = base64.b64encode(ph.hash).decode("ascii")
    if ph.title:
        entry["title"] = ph.title
    if ph.creation:
        entry["creation"] = fhir_instant(ph.creation)
    return entry


def fhir_patient_contact(c: PatientContact) -> dict:
    entry: dict = {}
    relationships = []
    for r in c.relationships or []:
        coding = _fhir_coding_list(r.codings)
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
    if c.name_period_start or c.name_period_end:
        name_dict["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(c.name_period_start),
                "end": fhir_instant(c.name_period_end),
            }.items()
            if v
        }
    if name_dict:
        entry["name"] = name_dict

    telecoms = [fhir_patient_telecom(t) for t in (c.telecoms or [])]
    if telecoms:
        entry["telecom"] = telecoms

    address_dict: dict = {}
    if c.use:
        address_dict["use"] = fhir_enum(c.use)
    if c.type:
        address_dict["type"] = fhir_enum(c.type)
    if c.text:
        address_dict["text"] = c.text
    if c.line:
        address_dict["line"] = list(c.line)
    if c.city:
        address_dict["city"] = c.city
    if c.district:
        address_dict["district"] = c.district
    if c.state:
        address_dict["state"] = c.state
    if c.postal_code:
        address_dict["postalCode"] = c.postal_code
    if c.country:
        address_dict["country"] = c.country
    if c.period_start or c.period_end:
        address_dict["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(c.period_start),
                "end": fhir_instant(c.period_end),
            }.items()
            if v
        }
    if address_dict:
        entry["address"] = address_dict

    if c.gender:
        entry["gender"] = fhir_enum(c.gender)

    org = _fhir_reference(c, "organization")
    if org:
        entry["organization"] = org

    if c.period_start or c.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(c.period_start),
                "end": fhir_instant(c.period_end),
            }.items()
            if v
        }
    return entry


def fhir_patient_communication(c) -> dict:
    entry: dict = {}
    coding = _fhir_coding_list(c.language_codings)
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


def fhir_patient_general_practitioner(gp) -> dict:
    return _fhir_reference(gp, "reference")


def fhir_patient_link(l) -> dict:
    entry: dict = {}
    other = _fhir_reference(l, "other")
    if other:
        entry["other"] = other
    if l.type:
        raw_type = fhir_enum(l.type)
        entry["type"] = raw_type.replace("_", "-") if raw_type else None
    return entry


def _fhir_meta(patient: PatientModel) -> dict:
    meta: dict = {}
    if patient.updated_at:
        meta["lastUpdated"] = fhir_instant(patient.updated_at)

    extensions = []
    if patient.tenant_id:
        extensions.append(
            {"url": f"{_EXT_BASE}/org-id", "valueString": patient.tenant_id}
        )
    if patient.created_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-by", "valueString": patient.created_by}
        )
    if patient.updated_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/updated-by", "valueString": patient.updated_by}
        )
    if patient.created_at:
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-at",
                "valueDateTime": fhir_instant(patient.created_at),
            }
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_patient(p: PatientModel) -> dict:
    result: dict = {
        "resourceType": "Patient",
        "id": str(p.patient_id),
    }

    meta = _fhir_meta(p)
    if meta:
        result["meta"] = meta

    if p.extension:
        result["extension"] = list(p.extension)

    identifiers = [fhir_patient_identifier(i) for i in (p.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if p.active is not None:
        result["active"] = p.active

    names = [fhir_patient_name(n) for n in (p.names or [])]
    if names:
        result["name"] = names

    telecoms = [fhir_patient_telecom(t) for t in (p.telecoms or [])]
    if telecoms:
        result["telecom"] = telecoms

    if p.gender:
        result["gender"] = fhir_enum(p.gender)
    if p.birth_date:
        result["birthDate"] = p.birth_date.isoformat()

    if p.deceased_boolean is not None:
        result["deceasedBoolean"] = p.deceased_boolean
    if p.deceased_date_time:
        result["deceasedDateTime"] = fhir_instant(p.deceased_date_time)

    addresses = [fhir_patient_address(a) for a in (p.addresses or [])]
    if addresses:
        result["address"] = addresses

    marital_codings = _fhir_coding_list(p.marital_status_codings)
    if marital_codings or p.marital_status_text:
        ms: dict = {}
        if marital_codings:
            ms["coding"] = marital_codings
        if p.marital_status_text:
            ms["text"] = p.marital_status_text
        result["maritalStatus"] = ms

    if p.multiple_birth_boolean is not None:
        result["multipleBirthBoolean"] = p.multiple_birth_boolean
    if p.multiple_birth_integer is not None:
        result["multipleBirthInteger"] = p.multiple_birth_integer

    photos = [fhir_patient_photo(ph) for ph in (p.photos or [])]
    if photos:
        result["photo"] = photos

    contacts = [fhir_patient_contact(c) for c in (p.contacts or [])]
    if contacts:
        result["contact"] = contacts

    communications = [
        fhir_patient_communication(c) for c in (p.communications or [])
    ]
    if communications:
        result["communication"] = communications

    gps = [
        fhir_patient_general_practitioner(gp) for gp in (p.general_practitioners or [])
    ]
    if gps:
        result["generalPractitioner"] = gps

    managing_org = _fhir_reference(p, "managing_organization")
    if managing_org:
        result["managingOrganization"] = managing_org

    links = [fhir_patient_link(l) for l in (p.links or [])]
    if links:
        result["link"] = links

    return {k: v for k, v in result.items() if v is not None}
