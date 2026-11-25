"""FHIR R4 conformance for `to_fhir_specimen()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Specimen is stored Medplum-style (like Patient, Appointment, Encounter, Condition, Procedure,
DiagnosticReport, Observation and the other content-based resources): the resource lives whole in
SpecimenModel.content, and to_fhir_specimen() only stamps `id` and `meta` onto it. So what can go
wrong on the read side is that stamping (e.g. a malformed meta extension) or a stored document the
server returns that isn't valid R4 — each case below is a `content` document as the write path
would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.specimen import to_fhir_specimen
from app.models.specimen import SpecimenModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.specimen_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
BLD = {
    "coding": [
        {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
            "code": "BLD",
            "display": "Whole blood",
        }
    ]
}


def _qty(value, unit="mL", code="mL"):
    return {"value": value, "unit": unit, "system": UCUM, "code": code}


def _specimen(content: dict, **overrides) -> SpecimenModel:
    fields = {
        "specimen_id": 310001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return SpecimenModel(**fields)


CASES = {
    "empty": _specimen({}),
    "updated_by_and_updated_at": _specimen({}, updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _specimen(
        {
            "identifier": [
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
                    "system": "https://fhir-server.dev/fhir/identifier-system/specimen-id",
                    "value": "SP-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    "accession_identifier": _specimen(
        {
            "accessionIdentifier": {
                "system": "http://lab.example.org/accessions",
                "value": "ACC-1",
            }
        }
    ),
    **{
        f"status_{s}": _specimen({"status": s})
        for s in ("available", "unavailable", "unsatisfactory", "entered-in-error")
    },
    "type": _specimen({"type": BLD}),
    **{
        f"subject_{t}": _specimen({"subject": {"reference": f"{t}/1"}})
        for t in ("Patient", "Group", "Device", "Substance", "Location")
    },
    "subject_with_display": _specimen(
        {"subject": {"reference": "Patient/10001", "display": "A. Patient"}}
    ),
    "subject_logical": _specimen(
        {"subject": {"identifier": {"system": "urn:pts", "value": "P-9"}}}
    ),
    "subject_absolute_url": _specimen(
        {"subject": {"reference": "https://other.example.org/fhir/Patient/9"}}
    ),
    "received_time": _specimen({"receivedTime": "2023-01-15T11:00:00Z"}),
    "received_time_partial": _specimen({"receivedTime": "2023-01"}),
    "parent": _specimen(
        {"parent": [{"reference": "Specimen/310000"}, {"reference": "Specimen/310002"}]}
    ),
    "request": _specimen({"request": [{"reference": "ServiceRequest/80001"}]}),
    "collection_empty": _specimen({"collection": {}}),
    **{
        f"collector_{t}": _specimen(
            {"collection": {"collector": {"reference": f"{t}/1"}}}
        )
        for t in ("Practitioner", "PractitionerRole")
    },
    "collected_date_time": _specimen(
        {"collection": {"collectedDateTime": "2023-01-15T09:30:00Z"}}
    ),
    "collected_date_time_partial": _specimen(
        {"collection": {"collectedDateTime": "2023-01"}}
    ),
    "collected_period": _specimen(
        {
            "collection": {
                "collectedPeriod": {"start": "2023-01-01", "end": "2023-01-02"}
            }
        }
    ),
    "collection_duration_and_quantity": _specimen(
        {"collection": {"duration": _qty(5, "min", "min"), "quantity": _qty(6)}}
    ),
    "collection_method_and_body_site": _specimen(
        {
            "collection": {
                "method": {"coding": [{"system": SCT, "code": "82078001"}]},
                "bodySite": {
                    "coding": [{"system": SCT, "code": "368208006"}],
                    "text": "arm",
                },
            }
        }
    ),
    "fasting_status_codeable_concept": _specimen(
        {
            "collection": {
                "fastingStatusCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0916",
                            "code": "F",
                        }
                    ]
                }
            }
        }
    ),
    "fasting_status_duration": _specimen(
        {"collection": {"fastingStatusDuration": _qty(8, "h", "h")}}
    ),
    "processing_empty": _specimen({"processing": [{}]}),
    "processing_full": _specimen(
        {
            "processing": [
                {
                    "description": "Centrifuged",
                    "procedure": {"coding": [{"system": SCT, "code": "9265001"}]},
                    "additive": [{"reference": "Substance/1"}],
                    "timeDateTime": "2023-01-15T11:30:00Z",
                }
            ]
        }
    ),
    "processing_time_period": _specimen(
        {"processing": [{"timePeriod": {"start": "2023-01-15T11:30:00Z"}}]}
    ),
    "container_empty": _specimen({"container": [{}]}),
    "container_full": _specimen(
        {
            "container": [
                {
                    "identifier": [{"system": "urn:containers", "value": "C-1"}],
                    "description": "Red top tube",
                    "type": {"coding": [{"system": SCT, "code": "434746001"}]},
                    "capacity": _qty(10),
                    "specimenQuantity": _qty(6),
                    "additiveCodeableConcept": {
                        "coding": [{"system": SCT, "code": "118424005"}]
                    },
                }
            ]
        }
    ),
    "container_additive_reference": _specimen(
        {"container": [{"additiveReference": {"reference": "Substance/1"}}]}
    ),
    "condition": _specimen(
        {
            "condition": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0493",
                            "code": "HEM",
                        }
                    ]
                },
                {"text": "Clotted"},
            ]
        }
    ),
    "note_author_string": _specimen(
        {
            "note": [
                {
                    "text": "Fasting.",
                    "time": "2023-01-15T10:00:00Z",
                    "authorString": "Nurse Joy",
                }
            ]
        }
    ),
    "note_author_reference": _specimen(
        {
            "note": [
                {"text": "n", "authorReference": {"reference": "Practitioner/30001"}}
            ]
        }
    ),
    "extension": _specimen(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
    "full": _specimen(
        {
            "identifier": [{"system": "urn:sp", "value": "SP-1"}],
            "accessionIdentifier": {"system": "urn:acc", "value": "ACC-1"},
            "status": "available",
            "type": BLD,
            "subject": {"reference": "Patient/10001"},
            "receivedTime": "2023-01-15T11:00:00Z",
            "parent": [{"reference": "Specimen/310000"}],
            "request": [{"reference": "ServiceRequest/80001"}],
            "collection": {
                "collector": {"reference": "Practitioner/30001"},
                "collectedDateTime": "2023-01-15T09:30:00Z",
                "quantity": _qty(6),
                "bodySite": {"text": "arm"},
            },
            "processing": [{"description": "Centrifuged"}],
            "container": [{"type": {"text": "tube"}, "capacity": _qty(10)}],
            "condition": [{"text": "OK"}],
            "note": [{"text": "n"}],
        }
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_specimen_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Specimen, to_fhir_specimen(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"status": "available", "collection": {"collectedDateTime": "2023-01-15"}}
    out = to_fhir_specimen(_specimen(content))
    assert out["resourceType"] == "Specimen"
    assert out["id"] == "310001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `type`, `subject` or `collection` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("type as string not a CodeableConcept", {"type": "x"}),
        ("receivedTime not a dateTime", {"receivedTime": "yesterday"}),
        ("accessionIdentifier as string", {"accessionIdentifier": "ACC-1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("parent as object not a list", {"parent": {"reference": "Specimen/1"}}),
        (
            "request as object not a list",
            {"request": {"reference": "ServiceRequest/1"}},
        ),
        ("collection as string", {"collection": "x"}),
        (
            "collection collector as string",
            {"collection": {"collector": "Practitioner/1"}},
        ),
        (
            "collectedDateTime not a dateTime",
            {"collection": {"collectedDateTime": "yesterday"}},
        ),
        ("collectedPeriod as string", {"collection": {"collectedPeriod": "2023"}}),
        ("collection quantity as string", {"collection": {"quantity": "5"}}),
        ("collection bodySite as string", {"collection": {"bodySite": "arm"}}),
        (
            "fastingStatusCodeableConcept as string",
            {"collection": {"fastingStatusCodeableConcept": "F"}},
        ),
        ("processing as object not a list", {"processing": {"description": "x"}}),
        ("processing procedure as string", {"processing": [{"procedure": "x"}]}),
        (
            "processing timeDateTime not a dateTime",
            {"processing": [{"timeDateTime": "noon"}]},
        ),
        ("container as object not a list", {"container": {"description": "x"}}),
        ("container type as string", {"container": [{"type": "x"}]}),
        ("container capacity as string", {"container": [{"capacity": "10"}]}),
        (
            "container identifier as object",
            {"container": [{"identifier": {"value": "x"}}]},
        ),
        ("condition as string", {"condition": "x"}),
        ("note as object not a list", {"note": {"text": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Specimen", "id": "310001", **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Specimen, validate=True
        )
