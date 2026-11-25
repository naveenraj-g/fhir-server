"""FHIR R4 conformance for `to_fhir_immunization()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Immunization is stored Medplum-style (like Patient, Appointment, Encounter,
Condition, Procedure, DiagnosticReport and the other content-based resources):
the resource lives whole in ImmunizationModel.content, and to_fhir_immunization()
only stamps `id` and `meta` onto it. So what can go wrong on the read side is that
stamping (e.g. a malformed meta extension) or a stored document the server returns
that isn't valid R4 — each case below is a `content` document as the write path
would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.immunization import to_fhir_immunization
from app.models.immunization import ImmunizationModel

from .support import assert_valid, fhir_json_text

immunization_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.immunization_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
PATIENT = {"reference": "Patient/10001"}
VACCINE = {
    "coding": [
        {"system": "http://hl7.org/fhir/sid/cvx", "code": "140", "display": "Influenza"}
    ]
}
SCT = "http://snomed.info/sct"
OCCURRED = "2023-01-15T09:30:00Z"


def _immunization(content: dict, **overrides) -> ImmunizationModel:
    fields = {
        "immunization_id": 330001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ImmunizationModel(**fields)


def _with(**elements) -> ImmunizationModel:
    return _immunization(
        {
            "status": "completed",
            "vaccineCode": VACCINE,
            "patient": PATIENT,
            "occurrenceDateTime": OCCURRED,
            **elements,
        }
    )


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _immunization(
        {
            "status": "completed",
            "vaccineCode": VACCINE,
            "patient": PATIENT,
            "occurrenceDateTime": OCCURRED,
        },
        updated_by="u-other",
        updated_at=D,
    ),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "FILL",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/immunization-id",
                "value": "IM-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _immunization(
            {
                "status": s,
                "vaccineCode": VACCINE,
                "patient": PATIENT,
                "occurrenceDateTime": OCCURRED,
            }
        )
        for s in ("completed", "entered-in-error", "not-done")
    },
    "status_reason": _immunization(
        {
            "status": "not-done",
            "statusReason": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "PATOBJ",
                    }
                ],
                "text": "Objected",
            },
            "vaccineCode": VACCINE,
            "patient": PATIENT,
            "occurrenceDateTime": OCCURRED,
        }
    ),
    "vaccine_code_text_only": _immunization(
        {
            "status": "completed",
            "vaccineCode": {"text": "Tetanus"},
            "patient": PATIENT,
            "occurrenceDateTime": OCCURRED,
        }
    ),
    "patient_with_display": _with(
        patient={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "patient_logical": _immunization(
        {
            "status": "completed",
            "vaccineCode": VACCINE,
            "occurrenceDateTime": OCCURRED,
            "patient": {"identifier": {"system": "urn:pts", "value": "P-9"}},
        }
    ),
    "patient_absolute_url": _immunization(
        {
            "status": "completed",
            "vaccineCode": VACCINE,
            "occurrenceDateTime": OCCURRED,
            "patient": {"reference": "https://other.example.org/fhir/Patient/9"},
        }
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "occurrence_date_time_partial": _immunization(
        {
            "status": "completed",
            "vaccineCode": VACCINE,
            "patient": PATIENT,
            "occurrenceDateTime": "2023-01",
        }
    ),
    "occurrence_string": _immunization(
        {
            "status": "completed",
            "vaccineCode": VACCINE,
            "patient": PATIENT,
            "occurrenceString": "last spring",
        }
    ),
    "recorded": _with(recorded="2023-01-15T10:00:00Z"),
    "primary_source_true": _with(primarySource=True),
    "primary_source_false": _with(
        primarySource=False,
        reportOrigin={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-origin",
                    "code": "record",
                }
            ]
        },
    ),
    "location": _with(location={"reference": "Location/230001"}),
    "manufacturer": _with(manufacturer={"reference": "Organization/190001"}),
    "lot_number_and_expiration": _with(
        lotNumber="AAJN11K", expirationDate="2025-02-15"
    ),
    "site_and_route": _with(
        site={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                    "code": "LA",
                    "display": "left arm",
                }
            ]
        },
        route={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                    "code": "IM",
                }
            ]
        },
    ),
    "dose_quantity": _with(
        doseQuantity={
            "value": 5,
            "unit": "mg",
            "system": "http://unitsofmeasure.org",
            "code": "mg",
        }
    ),
    "performer_with_function": _with(
        performer=[
            {
                "function": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                            "code": "AP",
                        }
                    ]
                },
                "actor": {"reference": "Practitioner/30001"},
            }
        ]
    ),
    **{
        f"performer_{t}": _with(performer=[{"actor": {"reference": f"{t}/1"}}])
        for t in ("Practitioner", "PractitionerRole", "Organization")
    },
    "performer_logical": _with(
        performer=[{"actor": {"identifier": {"system": "urn:who", "value": "W-1"}}}]
    ),
    "note_author_string": _with(
        note=[
            {
                "text": "Given in left arm",
                "time": "2023-01-15T10:05:00Z",
                "authorString": "Nurse Joy",
            }
        ]
    ),
    "note_author_reference": _with(
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/30001"}}]
    ),
    "reason_code": _with(
        reasonCode=[
            {"coding": [{"system": SCT, "code": "429060002"}]},
            {"text": "Other"},
        ]
    ),
    **{
        f"reason_reference_{t}": _with(reasonReference=[{"reference": f"{t}/1"}])
        for t in ("Condition", "Observation", "DiagnosticReport")
    },
    "is_subpotent": _with(
        isSubpotent=True,
        subpotentReason=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-subpotent-reason",
                        "code": "partial",
                    }
                ]
            }
        ],
    ),
    "education": _with(
        education=[
            {
                "documentType": "flu-fact-sheet",
                "reference": "https://example.org/flu",
                "publicationDate": "2022-10-01",
                "presentationDate": "2023-01-15",
            },
            {"reference": "https://example.org/other"},
        ]
    ),
    "program_eligibility_and_funding": _with(
        programEligibility=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-program-eligibility",
                        "code": "ineligible",
                    }
                ]
            }
        ],
        fundingSource={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-funding-source",
                    "code": "private",
                }
            ]
        },
    ),
    "reaction": _with(
        reaction=[
            {
                "date": "2023-01-16T08:00:00Z",
                "detail": {"reference": "Observation/160001"},
                "reported": True,
            },
            {"reported": False},
        ]
    ),
    "protocol_applied_positive_int": _with(
        protocolApplied=[
            {
                "series": "2-dose",
                "authority": {"reference": "Organization/190001"},
                "targetDisease": [{"coding": [{"system": SCT, "code": "6142004"}]}],
                "doseNumberPositiveInt": 1,
                "seriesDosesPositiveInt": 2,
            }
        ]
    ),
    "protocol_applied_string": _with(
        protocolApplied=[{"doseNumberString": "booster", "seriesDosesString": "many"}]
    ),
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:im", "value": "IM-1"}],
        encounter={"reference": "Encounter/20001"},
        recorded="2023-01-15T10:00:00Z",
        primarySource=True,
        location={"reference": "Location/230001"},
        manufacturer={"reference": "Organization/190001"},
        lotNumber="AAJN11K",
        expirationDate="2025-02-15",
        site={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                    "code": "LA",
                }
            ]
        },
        route={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                    "code": "IM",
                }
            ]
        },
        doseQuantity={"value": 5, "system": "http://unitsofmeasure.org", "code": "mg"},
        performer=[{"actor": {"reference": "Practitioner/30001"}}],
        note=[{"text": "n"}],
        reasonCode=[{"coding": [{"system": SCT, "code": "429060002"}]}],
        reasonReference=[{"reference": "Condition/120001"}],
        isSubpotent=False,
        reaction=[
            {"date": "2023-01-16", "detail": {"reference": "Observation/160001"}}
        ],
        protocolApplied=[{"series": "2-dose", "doseNumberPositiveInt": 1}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_immunization_mapper_emits_valid_fhir_r4(case):
    assert_valid(immunization_pb2.Immunization, to_fhir_immunization(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {
        "status": "completed",
        "vaccineCode": VACCINE,
        "patient": PATIENT,
        "occurrenceDateTime": OCCURRED,
        "lotNumber": "X1",
    }
    out = to_fhir_immunization(_immunization(content))
    assert out["resourceType"] == "Immunization"
    assert out["id"] == "330001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `patient` or `vaccineCode` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("vaccineCode as string not a CodeableConcept", {"vaccineCode": "140"}),
        ("occurrenceDateTime not a dateTime", {"occurrenceDateTime": "yesterday"}),
        ("recorded not a dateTime", {"recorded": "recently"}),
        ("expirationDate not a date", {"expirationDate": "soon"}),
        ("primarySource as string", {"primarySource": "yes"}),
        ("isSubpotent as string", {"isSubpotent": "no"}),
        ("lotNumber as number", {"lotNumber": 5}),
        (
            "performer as object not a list",
            {"performer": {"actor": {"reference": "Practitioner/1"}}},
        ),
        ("performer actor as string", {"performer": [{"actor": "Practitioner/1"}]}),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("note author as number", {"note": [{"text": "x", "authorString": 5}]}),
        ("reasonCode as object not a list", {"reasonCode": {"text": "x"}}),
        (
            "reasonReference as object not a list",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        ("reaction as object not a list", {"reaction": {"reported": True}}),
        ("reaction detail as string", {"reaction": [{"detail": "Observation/1"}]}),
        ("doseQuantity as string", {"doseQuantity": "5 mg"}),
        ("protocolApplied as object not a list", {"protocolApplied": {"series": "x"}}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Immunization",
        "id": "330001",
        "status": "completed",
        "vaccineCode": VACCINE,
        "patient": PATIENT,
        "occurrenceDateTime": OCCURRED,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), immunization_pb2.Immunization, validate=True
        )
