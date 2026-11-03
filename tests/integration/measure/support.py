"""Shared helpers and payloads for Measure integration tests."""

BASE = "/api/fhir/v1/measures"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"active": True, "name": "Quality Health Organization"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_group(client) -> int:
    """Create a minimal group and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/groups/",
        json={"type": "person", "actual": True, "name": "Test Group Cohort"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_measure() -> dict:
    return {
        "status": "draft",
    }


async def create_measure(client) -> int:
    """Create a minimal measure and return its public ID."""
    resp = await client.post(
        f"{BASE}/",
        json=minimal_measure(),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def full_measure(organization_id: int | None = None) -> dict:
    assigner_ref = f"Organization/{organization_id}" if organization_id else None
    return {
        "url": "http://example.org/fhir/Measure/exclusive-breastfeeding-measure",
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/fhir/measure",
                "value": "meas-full-001",
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
        "version": "1.0.0",
        "name": "ExclusiveBreastfeedingMeasure",
        "title": "Exclusive Breastfeeding Measure",
        "subtitle": "Birth Stay Measure",
        "status": "draft",
        "experimental": True,
        "subject_codeable_concept": {
            "text": "Patient",
            "coding": [
                {
                    "system": "http://hl7.org/fhir/resource-types",
                    "code": "Patient",
                    "display": "Patient",
                }
            ],
        },
        "date": "2026-02-01T10:00:00Z",
        "publisher": "National Quality Agency",
        "contact": [
            {
                "name": "Quality Lead",
                "telecom": [
                    {
                        "system": "phone",
                        "value": "555-1234",
                        "use": "work",
                        "rank": 1,
                    }
                ],
            }
        ],
        "description": "Exclusive breastfeeding measure for newborns during birth stay.",
        "use_context": [
            {
                "code_system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
                "code_code": "focus",
                "code_display": "Clinical Focus",
                "value_codeable_concept_text": "Cardiology",
                "value_codeable_concept_coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "394579002",
                        "display": "Cardiology",
                    }
                ],
            }
        ],
        "jurisdiction": [
            {
                "text": "US",
                "coding": [
                    {
                        "system": "urn:iso:std:iso:3166",
                        "code": "US",
                        "display": "United States of America",
                    }
                ],
            }
        ],
        "purpose": "Improve infant nutrition and health outcomes.",
        "usage": "Use annually across hospital maternal wards.",
        "copyright": "Copyright 2026 National Quality Agency.",
        "approval_date": "2026-01-15",
        "last_review_date": "2026-01-20",
        "effective_period_start": "2026-01-01T00:00:00Z",
        "effective_period_end": "2026-12-31T23:59:59Z",
        "topic": [
            {
                "text": "Pediatrics",
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "394537008",
                        "display": "Pediatrics",
                    }
                ],
            }
        ],
        "author": [{"name": "Dr. Author"}],
        "editor": [{"name": "Dr. Editor"}],
        "reviewer": [{"name": "Dr. Reviewer"}],
        "endorser": [{"name": "Endorsement Board"}],
        "related_artifact": [
            {
                "type": "depends-on",
                "label": "CQM Logic",
                "display": "Clinical Quality Measure Logic Library",
                "url": "http://example.org/fhir/Library/breastfeeding-logic",
            }
        ],
        "library": ["http://example.org/fhir/Library/breastfeeding-logic"],
        "disclaimer": "Informational purpose only.",
        "scoring": {
            "text": "Proportion",
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/measure-scoring",
                    "code": "proportion",
                    "display": "Proportion",
                }
            ],
        },
        "composite_scoring": {
            "text": "Linear",
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/composite-measure-scoring",
                    "code": "linear",
                    "display": "Linear",
                }
            ],
        },
        "type": [
            {
                "text": "Process",
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/measure-type",
                        "code": "process",
                        "display": "Process",
                    }
                ],
            }
        ],
        "risk_adjustment": "None",
        "rate_aggregation": "None",
        "rationale": "Breastfeeding promotes vital early infant immune response.",
        "clinical_recommendation_statement": "Infants should be breastfed exclusively.",
        "improvement_notation": {
            "text": "Increase",
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                    "code": "increase",
                    "display": "Increased score indicates improvement",
                }
            ],
        },
        "definition": ["Exclusively breastfed: receiving only breast milk."],
        "guidance": "Follow WHO recommendations.",
        "group": [
            {
                "description": "Initial Population and Denominator",
                "code": {
                    "text": "Primary Group",
                    "coding": [
                        {
                            "system": "http://example.org/fhir/measure-group",
                            "code": "primary",
                            "display": "Primary Group",
                        }
                    ],
                },
                "population": [
                    {
                        "description": "Initial Population",
                        "code": {
                            "text": "Initial Population",
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                    "code": "initial-population",
                                    "display": "Initial Population",
                                }
                            ],
                        },
                        "criteria": {
                            "language": "text/cql",
                            "expression": "Initial Population",
                        },
                    }
                ],
                "stratifier": [
                    {
                        "description": "Gestational Age Stratifier",
                        "code": {
                            "text": "Gestational Age",
                            "coding": [
                                {
                                    "system": "http://example.org/stratifier",
                                    "code": "gestational-age",
                                    "display": "Gestational Age",
                                }
                            ],
                        },
                        "criteria": {
                            "language": "text/cql",
                            "expression": "Gestational Age Stratifier",
                        },
                    }
                ],
            }
        ],
        "supplemental_data": [
            {
                "description": "Payer Information",
                "code": {
                    "text": "Payer",
                    "coding": [
                        {
                            "system": "http://example.org/supplemental-data",
                            "code": "payer",
                            "display": "Payer",
                        }
                    ],
                },
                "usage": [
                    {
                        "text": "Risk Adjustment",
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/measure-data-usage",
                                "code": "risk-adjustment-factor",
                                "display": "Risk Adjustment Factor",
                            }
                        ],
                    }
                ],
                "criteria": {
                    "language": "text/cql",
                    "expression": "Coverage.payer",
                },
            }
        ],
    }
