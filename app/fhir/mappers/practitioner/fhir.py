from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import (
    fhir_address,
    fhir_enum,
    fhir_human_name,
    fhir_photo,
    fhir_telecom,
)

if TYPE_CHECKING:
    from app.models.practitioner import (
        PractitionerCommunication,
        PractitionerIdentifier,
        PractitionerModel,
        PractitionerQualification,
        PractitionerQualificationIdentifier,
    )


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on Practitioner (identifier.assigner, qualification.issuer)
    — mirrors app.fhir.mappers.patient.fhir._fhir_reference."""
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
                    "start": id_period_start.isoformat() if id_period_start else None,
                    "end": id_period_end.isoformat() if id_period_end else None,
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def fhir_identifier(
    i: PractitionerIdentifier | PractitionerQualificationIdentifier,
) -> dict:
    """Practitioner.identifier / qualification.identifier (Identifier) → FHIR
    camelCase dict. Resource-specific (not the shared
    app.fhir.datatypes.fhir_identifier) because assigner is a resolved
    Reference(Organization) with an identifier fallback, unlike a flat
    display string."""
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


def fhir_practitioner_communication(cm: PractitionerCommunication) -> dict:
    """communication[] (0..*) CodeableConcept — R4 Practitioner has no `.preferred` (Patient/RelatedPerson-only)."""
    coding = {
        k: v
        for k, v in {
            "system": cm.language_system,
            "version": cm.language_version,
            "code": cm.language_code,
            "display": cm.language_display,
            "userSelected": cm.language_user_selected,
        }.items()
        if v is not None
    }
    entry: dict = {}
    if coding:
        entry["coding"] = [coding]
    if cm.language_text:
        entry["text"] = cm.language_text
    return entry


def fhir_qualification(q: PractitionerQualification) -> dict:
    entry: dict = {}
    if q.identifiers:
        entry["identifier"] = [fhir_identifier(qi) for qi in q.identifiers]
    code_cc: dict = {}
    if q.code_system or q.code_code:
        code_cc["coding"] = [
            {
                k: v
                for k, v in {
                    "system": q.code_system,
                    "code": q.code_code,
                    "display": q.code_display,
                }.items()
                if v
            }
        ]
    if q.code_text:
        code_cc["text"] = q.code_text
    if code_cc:
        entry["code"] = code_cc
    if q.period_start or q.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": q.period_start.isoformat() if q.period_start else None,
                "end": q.period_end.isoformat() if q.period_end else None,
            }.items()
            if v
        }
    issuer = _fhir_reference(q, "issuer")
    if issuer:
        entry["issuer"] = issuer
    return entry


def to_fhir_practitioner(practitioner: PractitionerModel) -> dict:
    result: dict = {
        "resourceType": "Practitioner",
        "id": str(practitioner.practitioner_id),
        "active": practitioner.active,
        "gender": fhir_enum(practitioner.gender) if practitioner.gender else None,
        "birthDate": practitioner.birth_date.isoformat()
        if practitioner.birth_date
        else None,
    }

    if practitioner.names:
        result["name"] = [fhir_human_name(n) for n in practitioner.names]
    if practitioner.identifiers:
        result["identifier"] = [fhir_identifier(i) for i in practitioner.identifiers]
    if practitioner.telecoms:
        result["telecom"] = [fhir_telecom(t) for t in practitioner.telecoms]
    if practitioner.addresses:
        result["address"] = [fhir_address(a) for a in practitioner.addresses]
    if practitioner.photos:
        result["photo"] = [fhir_photo(p) for p in practitioner.photos]
    if practitioner.qualifications:
        result["qualification"] = [
            fhir_qualification(q) for q in practitioner.qualifications
        ]
    if practitioner.communications:
        result["communication"] = [
            cc
            for c in practitioner.communications
            if (cc := fhir_practitioner_communication(c))
        ]

    return {k: v for k, v in result.items() if v is not None}
