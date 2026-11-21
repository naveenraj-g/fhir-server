"""Shared helpers and payloads for practitioner integration tests.

Request bodies are genuine FHIR R4 Practitioner JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

BASE = "/api/fhir/v1/practitioners"

MINIMAL = {
    "active": True,
    "name": [{"family": "Careful", "given": ["Adam"]}],
}

FULL = {
    "resourceType": "Practitioner",
    "active": True,
    "gender": "male",
    "birthDate": "1980-05-15",
    "identifier": [
        {
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": "9941339108",
            "use": "official",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "NPI",
                    }
                ]
            },
        }
    ],
    "name": [
        {"use": "official", "family": "Careful", "given": ["Adam"], "prefix": ["Dr"]}
    ],
    "telecom": [
        {"system": "phone", "value": "555-9988", "use": "work"},
        {"system": "email", "value": "adam@example.org"},
    ],
    "address": [
        {
            "use": "work",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postalCode": "3999",
        }
    ],
    # No `contentType` here deliberately — Attachment.contentType is bound
    # against the full IANA MimeType ValueSet and the java validator sidecar
    # tries a remote lookup for it; it is 0..1, so omitting it is valid.
    "photo": [{"url": "https://fhir-server.dev/fhir/assets/photo.png"}],
    # No `system` on codings below deliberately — an external-terminology
    # system can trigger a slow remote lookup in the sidecar.
    "qualification": [
        {
            "code": {
                "coding": [{"code": "BS", "display": "Bachelor of Science"}],
                "text": "Bachelor of Science",
            }
        }
    ],
    "communication": [{"coding": [{"code": "en", "display": "English"}]}],
}


async def link_user(client, practitioner_id: int, user_id: str = "u-test"):
    """Link an end-user to a practitioner (needs practitioner:link)."""
    return await client.put(f"{BASE}/{practitioner_id}/user", json={"user_id": user_id})


async def create_practitioner(client, payload=None) -> int:
    """Create a practitioner and return the public practitioner id (int)."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
