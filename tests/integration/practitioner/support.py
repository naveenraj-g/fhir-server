"""Shared helpers and payloads for practitioner integration tests."""

BASE = "/api/fhir/v1/practitioners"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

MINIMAL = {
    "active": True,
    "name": [{"family": "Careful", "given": ["Adam"]}],
}

FULL = {
    "user_id": "end-user-1",
    "active": True,
    "gender": "male",
    "birth_date": "1980-05-15",
    "identifier": [
        {
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": "9941339108",
            "use": "official",
            "type_coding": [
                {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "NPI"}
            ],
        }
    ],
    "name": [
        {"use": "official", "family": "Careful", "given": ["Adam"], "prefix": ["Dr"]}
    ],
    "telecom": [{"system": "phone", "value": "555-9988", "use": "work"}],
    "address": [
        {
            "use": "work",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postal_code": "3999",
        }
    ],
    "photo": [
        # No `content_type` here deliberately — Attachment.contentType is
        # bound against the full IANA MimeType ValueSet
        # (http://hl7.org/fhir/ValueSet/mimetypes), and the java validator
        # sidecar tries to verify it via a remote tx.fhir.org cache lookup
        # that this sandboxed environment can't complete ("the cache was
        # never issued by this server"). contentType is 0..1, so omitting
        # it keeps the Attachment structurally valid without triggering
        # that lookup.
        {"url": "https://fhir-server.dev/fhir/assets/photo.png"}
    ],
    "qualification": [
        {
            # No `system` on the coding here deliberately — same reasoning
            # as `communication` above: an external-terminology system can
            # trigger a remote lookup this sandboxed environment can't
            # complete reliably (confirmed flaky for
            # http://terminology.hl7.org/CodeSystem/v2-0360/2.7 specifically).
            "code_coding": [{"code": "BS", "display": "Bachelor of Science"}],
            "code_text": "Bachelor of Science",
        }
    ],
    "communication": [
        # No `system` here deliberately — `urn:ietf:bcp:47` triggers the java
        # validator sidecar's preferred-binding check against the full "All
        # Languages" ValueSet, which this sandboxed environment can't
        # resolve quickly (confirmed via the sidecar's own logs — 180s+).
        {"coding": [{"code": "en", "display": "English"}]}
    ],
}


async def create_practitioner(client, payload=None) -> int:
    """Create a practitioner and return the public practitioner id."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
