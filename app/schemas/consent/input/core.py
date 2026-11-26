"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.consent import Consent, ConsentPatch

_CREATE_EXAMPLE = {
    "resourceType": "Consent",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/consent-id",
            "value": "C-1",
        }
    ],
    "status": "active",
    "scope": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                "code": "patient-privacy",
            }
        ]
    },
    "category": [{"coding": [{"system": "http://loinc.org", "code": "59284-0"}]}],
    "patient": {"type": "Patient", "display": "Example patient"},
    "dateTime": "2026-01-15T09:00:00Z",
    "performer": [{"type": "Patient", "display": "Example patient"}],
    "organization": [{"type": "Organization", "display": "Example organization"}],
    "policyRule": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "OPTIN",
            }
        ]
    },
    "provision": {
        "type": "permit",
        "period": {"start": "2026-01-15", "end": "2027-01-14"},
        "actor": [
            {
                "role": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                            "code": "IRCP",
                        }
                    ]
                },
                "reference": {
                    "type": "Practitioner",
                    "display": "Example practitioner",
                },
            }
        ],
        "action": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/consentaction",
                        "code": "access",
                    }
                ]
            }
        ],
    },
}

_PATCH_EXAMPLE = {
    "status": "inactive",
    "provision": {"type": "deny", "period": {"start": "2026-06-01"}},
}


class ConsentCreateSchema(Consent):
    "POST body - a FHIR R4 Consent resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ConsentPatchSchema(ConsentPatch):
    "PATCH body - a partial FHIR R4 Consent (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
