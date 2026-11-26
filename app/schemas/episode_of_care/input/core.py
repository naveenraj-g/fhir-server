"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.episode_of_care import EpisodeOfCare, EpisodeOfCarePatch

_CREATE_EXAMPLE = {
    "resourceType": "EpisodeOfCare",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/episode-of-care-id",
            "value": "EOC-1001",
        }
    ],
    "status": "active",
    "statusHistory": [
        {"status": "planned", "period": {"start": "2025-12-01", "end": "2025-12-31"}},
        {"status": "active", "period": {"start": "2026-01-01"}},
    ],
    "type": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
                    "code": "cacp",
                    "display": "Community-based aged care",
                }
            ]
        }
    ],
    "diagnosis": [
        {"condition": {"type": "Condition", "display": "Example condition"}, "rank": 1}
    ],
    "patient": {"type": "Patient", "display": "Example patient"},
    "managingOrganization": {"type": "Organization", "display": "Example organization"},
    "period": {"start": "2026-01-01"},
    "careManager": {"type": "Practitioner", "display": "Example practitioner"},
}

_PATCH_EXAMPLE = {
    "status": "finished",
    "period": {"start": "2026-01-01", "end": "2026-06-30"},
}


class EpisodeOfCareCreateSchema(EpisodeOfCare):
    "POST body - a FHIR R4 EpisodeOfCare resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class EpisodeOfCarePatchSchema(EpisodeOfCarePatch):
    "PATCH body - a partial FHIR R4 EpisodeOfCare (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
