"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.patient import Patient, PatientPatch

_CREATE_EXAMPLE = {
    "resourceType": "Patient",
    "active": True,
    "gender": "male",
    "birthDate": "1974-12-25",
    "deceasedBoolean": False,
    "identifier": [
        {
            "use": "official",
            "system": "http://hospital.example.org/mrn",
            "value": "MRN-12345",
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Chalmers",
            "given": ["Peter", "James"],
            "prefix": ["Mr"],
        }
    ],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "home"}],
    "address": [
        {
            "use": "home",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postalCode": "3999",
            "country": "AU",
        }
    ],
    "maritalStatus": {"coding": [{"code": "M", "display": "Married"}]},
    "contact": [
        {
            "relationship": [{"coding": [{"code": "N", "display": "Next-of-Kin"}]}],
            "name": {"family": "Chalmers", "given": ["Sarah"]},
            "telecom": [{"system": "phone", "value": "555-9876"}],
        }
    ],
    "communication": [
        {
            "language": {"coding": [{"code": "en", "display": "English"}]},
            "preferred": True,
        }
    ],
    "generalPractitioner": [{"reference": "Practitioner/30001"}],
    "managingOrganization": {"reference": "Organization/190001"},
}

_PATCH_EXAMPLE = {
    "telecom": [{"system": "phone", "value": "555-0000", "use": "mobile"}],
    "active": False,
}


class PatientCreateSchema(Patient):
    "POST body - a FHIR R4 Patient resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class PatientPatchSchema(PatientPatch):
    "PATCH body - a partial FHIR R4 Patient (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
