"""Shared helpers and payloads for MeasureReport integration tests."""

BASE = "/api/fhir/v1/measure-reports"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"active": True, "name": "Quality Health Organization"},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "gender": "male"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_measure_report() -> dict:
    return {
        "status": "complete",
        "type": "summary",
        "measure": "http://example.org/fhir/Measure/exclusive-breastfeeding-measure",
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-01-31T23:59:59Z",
    }


async def create_measure_report(client) -> int:
    """Create a minimal measure report and return its public ID."""
    resp = await client.post(
        f"{BASE}/",
        json=minimal_measure_report(),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def full_measure_report(
    organization_id: int | None = None,
    patient_id: int | None = None,
    practitioner_id: int | None = None,
) -> dict:
    assigner_ref = f"Organization/{organization_id}" if organization_id else None
    subj_ref = f"Patient/{patient_id}" if patient_id else None
    rep_ref = f"Practitioner/{practitioner_id}" if practitioner_id else None
    return {
        "status": "complete",
        "type": "summary",
        "measure": "http://example.org/fhir/Measure/exclusive-breastfeeding-measure",
        "subject": subj_ref,
        "subject_display": "Test Patient",
        "date": "2026-02-01T10:00:00Z",
        "reporter": rep_ref,
        "reporter_display": "Dr. Reporter",
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-01-31T23:59:59Z",
        "improvement_notation_text": "Increased score indicates improvement",
        "improvement_notation_coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                "code": "increase",
                "display": "Increased score indicates improvement",
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/fhir/measurereport",
                "value": "mr-full-001",
                "type_text": "Filler Identifier",
                "type_coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "FILL",
                        "display": "Filler Identifier",
                    }
                ],
                "period_start": "2026-02-01T10:00:00Z",
                "period_end": "2026-02-01T10:00:00Z",
                "assigner": assigner_ref,
            }
        ],
        "group": [
            {
                "code_text": "Primary Group",
                "code_coding": [
                    {
                        "system": "http://example.org/group-codes",
                        "code": "grp-1",
                        "display": "Primary Group",
                    }
                ],
                "population": [
                    {
                        "code_text": "Initial Population",
                        "code_coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                "code": "initial-population",
                                "display": "Initial Population",
                            }
                        ],
                        "count": 100,
                    }
                ],
                "measure_score_value": 0.8,
                "measure_score_comparator": ">=",
                "measure_score_unit": "%",
                "measure_score_system": "http://unitsofmeasure.org",
                "measure_score_code": "%",
                "stratifier": [
                    {
                        "code": [
                            {
                                "text": "Gender",
                                "coding": [
                                    {
                                        "system": "http://example.org/stratifier-code",
                                        "code": "gender",
                                        "display": "Gender Stratifier",
                                    }
                                ],
                            }
                        ],
                        "stratum": [
                            {
                                "value_text": "Male",
                                "value_coding": [
                                    {
                                        "system": "http://hl7.org/fhir/administrative-gender",
                                        "code": "male",
                                        "display": "Male",
                                    }
                                ],
                                "component": [
                                    {
                                        "code_text": "Age Group",
                                        "code_coding": [
                                            {
                                                "system": "http://example.org/comp-code",
                                                "code": "age-group",
                                                "display": "Age Group",
                                            }
                                        ],
                                        "value_text": "Newborn",
                                        "value_coding": [
                                            {
                                                "system": "http://example.org/age-ranges",
                                                "code": "newborn",
                                                "display": "Newborn",
                                            }
                                        ],
                                    }
                                ],
                                "population": [
                                    {
                                        "code_text": "Initial Population",
                                        "count": 50,
                                    }
                                ],
                                "measure_score_value": 0.85,
                            }
                        ],
                    }
                ],
            }
        ],
    }
