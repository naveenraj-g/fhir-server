"""Shared helpers and payloads for consent integration tests."""

BASE = "/api/fhir/v1/consents"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True, "name": [{"family": "Smith", "given": ["Alice"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"active": True, "name": "General Hospital"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_consent(patient_id: int | None = None) -> dict:
    payload = {
        "status": "active",
        "scope": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                    "code": "patient-privacy",
                    "display": "Privacy Consent",
                }
            ],
            "text": "Privacy Consent",
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "INFA",
                        "display": "information access",
                    }
                ],
                "text": "Information Access",
            }
        ],
    }
    if patient_id:
        payload["patient"] = f"Patient/{patient_id}"
        payload["patient_display"] = "Jane Doe"
    return payload


def full_consent(
    patient_id: int,
    practitioner_id: int,
    org_id: int,
) -> dict:
    return {
        "status": "active",
        "scope": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                    "code": "patient-privacy",
                    "display": "Privacy Consent",
                }
            ],
            "text": "Privacy Consent",
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "INFA",
                        "display": "information access",
                    }
                ],
                "text": "Information Access",
            }
        ],
        "patient": f"Patient/{patient_id}",
        "patient_display": "Jane Doe",
        "date_time": "2026-01-01T10:00:00Z",
        "performer": [
            {
                "reference": f"Practitioner/{practitioner_id}",
                "display": "Dr. Alice Smith",
            }
        ],
        "organization": [
            {
                "reference": f"Organization/{org_id}",
                "display": "General Hospital",
            }
        ],
        "policy": [
            {
                "authority": "http://example.org/fhir/ConsentPolicy",
                "uri": "http://example.org/fhir/ConsentPolicy/1",
            }
        ],
        "policy_rule": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "OPTIN",
                    "display": "opt-in",
                }
            ],
            "text": "opt-in",
        },
        "verification": [
            {
                "verified": True,
                "verified_with": f"Patient/{patient_id}",
                "verified_with_display": "Jane Doe",
                "verification_date": "2026-01-01T10:00:00Z",
            }
        ],
        "provision": {
            "type": "permit",
            "period_start": "2026-01-01T00:00:00Z",
            "period_end": "2026-12-31T23:59:59Z",
            "actor": [
                {
                    "role": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "PRCP",
                                "display": "primary recipient",
                            }
                        ],
                        "text": "Primary Recipient",
                    },
                    "reference": f"Practitioner/{practitioner_id}",
                    "reference_display": "Dr. Alice Smith",
                }
            ],
            "action": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/consentaction",
                            "code": "access",
                            "display": "Access",
                        }
                    ],
                    "text": "Access",
                }
            ],
            "security_label": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "N",
                    "display": "normal",
                }
            ],
            "purpose": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                    "code": "TREAT",
                    "display": "treatment",
                }
            ],
        },
        "identifier": [
            {
                "system": "http://example.org/consents",
                "value": "CONSENT-001",
            }
        ],
    }


async def create_consent(
    client,
    payload: dict | None = None,
    patient_id: int | None = None,
) -> int:
    if payload is None:
        if patient_id is None:
            patient_id = await create_test_patient(client)
        payload = minimal_consent(patient_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
